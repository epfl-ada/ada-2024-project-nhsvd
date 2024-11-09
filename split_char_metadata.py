import pandas as pd
import argparse
from pathlib import Path


def split_character_metadata(input_dir, output_dir):
    metadata_file = input_dir / 'character.metadata.tsv'

    characters_metadata_df = pd.read_csv(metadata_file, sep='\t', header=None)

    characters_metadata_df.columns = [
        'movie_id',                         # wikipedia_movie_id
        'freebase_movie_id',
        'movie_release_date',
        'character_name',
        'actor_birth_date',
        'actor_gender',
        'actor_height',
        'actor_ethnicity',
        'actor_name',
        'actor_age_at_movie_release',
        'freebase_character_actor_map_id',
        'freebase_character_id',
        'freebase_actor_id'
    ]

    # split by movie_id and save to separate csv files
    for movie_id in characters_metadata_df['movie_id'].unique():
        df = characters_metadata_df[characters_metadata_df['movie_id'] == movie_id]

        df = df.drop(columns=['movie_id'])

        output_file = output_dir / f'character.metadata_{movie_id}.csv'

        df.to_csv(output_file, index=False)


def main():
    parser = argparse.ArgumentParser(description="Split character metadata by movie ID.")
    parser.add_argument("-i", "--input-dir", type=Path, required=False, default="./data/raw/", help="Directory containing character metadata file")
    parser.add_argument("-o", "--output-dir", type=Path, required=False, default="./data/interim/", help="Directory to save split character metadata files")

    args = parser.parse_args()
    input_dir = args.input_dir
    output_dir = args.output_dir

    output_dir.mkdir(parents=True, exist_ok=True)

    split_character_metadata(input_dir, output_dir)

if __name__ == '__main__':
    main()
