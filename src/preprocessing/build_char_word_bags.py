import argparse
import json
import pickle
from collections import defaultdict
from pathlib import Path
import multiprocessing as mp
from functools import partial

from tqdm import tqdm
import pandas as pd


def read_character_metadata(movie_id, input_dir):
    character_metadata_file = input_dir / f'character.metadata_{movie_id}.csv'
    character_df = pd.read_csv(character_metadata_file, usecols=['character_name', 'freebase_character_id'])
    return character_df


def read_tokens(movie_id, input_dir):
    tokens_file = input_dir / f'corenlp_plot_summaries/tokens_{movie_id}.csv'
    tokens_df = pd.read_csv(tokens_file)
    return tokens_df


def read_dependencies(movie_id, input_dir):
    dependencies_file = input_dir / f'corenlp_plot_summaries/dependencies_{movie_id}.csv'
    dependencies_df = pd.read_csv(dependencies_file)
    return dependencies_df


def read_coreferences(movie_id, input_dir):
    coref_file = input_dir / f'corenlp_plot_summaries/coreferences_{movie_id}.csv'
    coref_df = pd.read_csv(coref_file)
    return coref_df


def generate_name_tuples(character_df):
    """
    For each character, generate all possible unambiguous ordered name part tuples.
    """
    name_parts_dict = defaultdict(set)
    for _, row in character_df.iterrows():
        character_id = row['freebase_character_id']
        character_name = str(row['character_name'])
        name_parts = character_name.split()

        # create a map for different length name part combinations
        n = len(name_parts)
        for l in range(n, 0, -1):
            for i in range(n - l + 1):
                name_tuple = tuple(name_parts[i:i+l])
                name_parts_dict[name_tuple].add((character_name, character_id))

    # reduce the character_map to only include unambiguous entries
    unique_character_map = {}
    for name_tuple, char_tuple in name_parts_dict.items():
        if len(char_tuple) == 1:
            unique_character_map[name_tuple] = next(iter(char_tuple))

    return unique_character_map


def get_max_name_length(name_parts_dict):
    max_length = max(len(name_tuple) for name_tuple in name_parts_dict.keys())
    return max_length


def match_name_parts_in_tokens(tokens_df, name_parts_dict):
    """
    Matches character name parts in the tokens and records occurrences.
    """
    # map sentence_id to list of tokens
    sentence_tokens = {}
    for sentence_id, group in tokens_df.groupby('sentence_id'):
        word_list = list(group['word'])
        token_ids = list(group['token_id'])
        sentence_tokens[sentence_id] = {'words': word_list, 'token_ids': token_ids}
    
    # for each sentence, try to match name parts
    name_occurrences = []
    max_name_length = get_max_name_length(name_parts_dict)
    for sentence_id, data in sentence_tokens.items():
        words = data['words']
        token_ids = data['token_ids']
        n = len(words)
        matched_indices = set()
        for window_size in range(max_name_length, 0, -1):
            if window_size > n:
                continue
            for i in range(n - window_size + 1):
                if any(idx in matched_indices for idx in range(i, i+window_size)):
                    continue  # skip if tokens are already matched
                token_sequence = tuple(words[i:i+window_size])
                if token_sequence in name_parts_dict:
                    name, freebase_id = name_parts_dict[token_sequence]
                    start_token_id = token_ids[i]
                    end_token_id = token_ids[i+window_size -1]
                    name_occurrences.append({
                        'sentence_id': sentence_id,
                        'start_token_id': start_token_id,
                        'end_token_id': end_token_id,
                        'name': name,
                        'freebase_character_id': freebase_id
                    })
                    matched_indices.update(range(i, i+window_size))

    return name_occurrences


def map_tokens_to_characters(name_occurrences, coref_df):
    """
    Maps tokens to characters and their coreference mentions.
    """
    # map (sentence_id, token_id) to (character_name, freebase_character_id)
    token_to_character = {}
    for occ in name_occurrences:
        sentence_id = occ['sentence_id']
        start_token_id = occ['start_token_id']
        end_token_id = occ['end_token_id']
        name = occ['name']
        freebase_id = occ['freebase_character_id']
        token_range = range(start_token_id, end_token_id + 1)
        for token_id in token_range:
            token_to_character[(sentence_id, token_id)] = (name, freebase_id)

    # find coreference chains of characters
    character_chain = False
    name, freebase_id = None, None

    for _, row in coref_df.iterrows():
        if row['representative']: # each chain starts with a representative
            sentence_id = row['sentence_id']
            head_token_id = row['head']
            if (sentence_id, head_token_id) in token_to_character: 
                # if the representative is a character, we need to add the whole chain to character_corefs
                character_chain = True
                name, freebase_id = token_to_character[(sentence_id, head_token_id)]
                # the representative is already stored in token_to_character
            else:
                character_chain = False

        elif character_chain: 
            token_to_character[(row['sentence_id'], row['head'])] = (name, freebase_id)
        
        # else: if the representative is not a character, we can ignore the whole chain
    
    return token_to_character


def get_dep_label(dep_type, governor: bool):
    """
    Helper function to determine the label for the (r, w) = (label, lemma) tuple.
    """
    agent_verb_types = ['nsubj', 'agent']
    patient_verb_types = ['dobj', 'nsubjpass', 'iobj'] # + all types starting with "prep_"
    attribute_types_dep = ['nsubj', 'appos']
    attribute_types_gov = ['nsubj', 'appos', 'amod', 'nn']

    # governor flag determines whether the character is the governor or dependent
    if dep_type in agent_verb_types:
        return 'agent verb'
    elif dep_type in patient_verb_types or dep_type.startswith('prep_'):
        return 'patient verb'
    elif dep_type in attribute_types_gov and governor:
        return 'attribute'
    elif dep_type in attribute_types_dep and not governor:
        return 'attribute'
    else:
        return None


def build_character_bags_of_words(token_character_map, dependencies_df, tokens_df):
    """
    Builds the bag of words for each character based on dependencies.
    """
    # map (sentence_id, token_id) to lemma
    token_lemma = {
        (row['sentence_id'], row['token_id']): str(row['lemma']).lower()
        for _, row in tokens_df.iterrows()
    }

    character_bags = defaultdict(set)

    for _, dep in dependencies_df.iterrows():
        sentence_id = dep['sentence_id']
        dep_type = dep['type']
        governor_idx = dep['governor_idx']
        dependent_idx = dep['dependent_idx']

        if (sentence_id, governor_idx) in token_character_map:
            # governor is a character
            label = get_dep_label(dep_type, governor=True)
            if label is not None:
                char = token_character_map[(sentence_id, governor_idx)]
                lemma = token_lemma.get((sentence_id, dependent_idx), '')
                if lemma:
                    character_bags[char].add((label, lemma))

        if (sentence_id, dependent_idx) in token_character_map:
            # dependent is a character
            label = get_dep_label(dep_type, governor=False)
            if label is not None:
                char = token_character_map[(sentence_id, dependent_idx)]
                lemma = token_lemma.get((sentence_id, governor_idx), '')
                if lemma:
                    character_bags[char].add((label, lemma))

    return character_bags


def process_movie(movie_id, input_dir):
    """Builds character bags of words for a single movie

    Returns:
        tuple: (character_bags, ok) where ok is a boolean indicating whether the processing was successful
    """


    # Step 1: Read character metadata and generate name tuples
    character_df = read_character_metadata(movie_id, input_dir)
    name_parts_dict = generate_name_tuples(character_df)

    if not name_parts_dict:
        return {}, False
    
    # Step 2: Read tokens and match name parts
    tokens_df = read_tokens(movie_id, input_dir)
    name_occurrences = match_name_parts_in_tokens(tokens_df, name_parts_dict)

    if not name_occurrences:
        return {}, False
    
    # Steps 3 and 4: Read coreferences and map characters to coreference mentions
    # Build a map from (sentence_id, token_id) to (name, freebase_id)
    coref_df = read_coreferences(movie_id, input_dir)
    token_character_map = map_tokens_to_characters(name_occurrences, coref_df)

    # token_character_map is nonempty if name_occurrences was, no need to check it
    
    # Step 5: Read dependencies and build character bags of words
    dependencies_df = read_dependencies(movie_id, input_dir)
    character_bags = build_character_bags_of_words(token_character_map, dependencies_df, tokens_df)

    if not character_bags:
        return {}, False

    return character_bags, True


def process_movie_pickle(movie_id, input_dir, output_dir):
    character_bags, ok = process_movie(movie_id, input_dir)
    if not ok:
        return

    character_bags_file = output_dir / f'character_bags_{movie_id}.pkl'
    with character_bags_file.open('wb') as f:
        pickle.dump(character_bags, f)


def process_movie_json(movie_id, input_dir, output_dir):
    character_bags, ok = process_movie(movie_id, input_dir)
    if not ok:
        return

    json_compatible_data = [
        {"name": name, "id": char_id, "bag": list(v)} for (name, char_id), v in character_bags.items()
    ]

    json_file = output_dir / f'character_bags_{movie_id}.json'
    with json_file.open('w') as f:
        json.dump(json_compatible_data, f)


def process_movies(movie_ids, input_dir, output_dir, save_format):
    if save_format == 'json':
        process_and_save = partial(process_movie_json, input_dir=input_dir, output_dir=output_dir)
    elif save_format == 'pickle':
        process_and_save = partial(process_movie_pickle, input_dir=input_dir, output_dir=output_dir)

    with mp.Pool(mp.cpu_count()) as pool:
        list(tqdm(pool.imap_unordered(process_and_save, movie_ids), total=len(movie_ids)))


def main():
    parser = argparse.ArgumentParser(description="Build character bags of words.")
    parser.add_argument("-i", "--input-dir", type=Path, required=False, default="./data/interim/", 
                        help="Directory containing CSV files created by `parse_corenlp_xml.py` and `split_char_metadata` (default: ./data/interim/)")
    parser.add_argument("-o", "--output-dir", type=Path, required=False, default="./data/processed/", help="Directory to save character bags of words files (default: ./data/processed/)")
    parser.add_argument("--save-format", type=str, default='json', choices=['json', 'pickle'], help="Format to save character bags of words (default: json)")
    parser.add_argument("-n", "--num-files", type=int, default=None, help="Number of files to process")
    parser.add_argument("--movie-ids", required=False, nargs='*', help="List of movie IDs to process")
    
    args = parser.parse_args()
    input_dir = args.input_dir
    output_dir = args.output_dir
    save_format = args.save_format
    num_files = args.num_files
    movie_ids = args.movie_ids


    if movie_ids:
        print(f"Processing {len(movie_ids)} movies:", movie_ids)
    else:
        # not all movie IDs in the character.metadata files are present in the plot summaries
        # and not all movie IDs in the plot summaries are present in the character.metadata files
        # so we need to take the intersection of the movie IDs in the plot summaries and the character.metadata files

        token_files = input_dir.glob('corenlp_plot_summaries/tokens_*.csv') # token, depencency, and coreference files have the same movie IDs
        metadata_files = input_dir.glob('character.metadata_*.csv')

        token_movie_ids = [f.stem.split('_')[1] for f in token_files]
        metadata_movie_ids = [f.stem.split('_')[1] for f in metadata_files]
        movie_ids = list(set(metadata_movie_ids) & set(token_movie_ids))

        if num_files:
            movie_ids = movie_ids[:num_files]

        print(f"Processing {len(movie_ids)} movies")

    output_dir.mkdir(parents=True, exist_ok=True)

    process_movies(movie_ids, input_dir, output_dir, save_format)

    processed_movie_ids = set()
    for movie_id in movie_ids:
        character_bags_file = output_dir / f'character_bags_{movie_id}.{save_format}'
        if character_bags_file.exists():
            processed_movie_ids.add(movie_id)

    print(f"Successfully built character bags of words for {len(processed_movie_ids)}/{len(movie_ids)} movies")


if __name__ == "__main__":
    main()
