import argparse
import json
import logging
from pathlib import Path
from typing import List, Optional

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


SYSTEM_PROMPT = (
    "Given a list of character names and a plot summary, extract the information about character deaths."
)

RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "character_deaths",
        "schema": {
            "type": "object",
            "properties": {
                "characters": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "dies": {"type": "boolean"},
                        },
                        "required": ["name", "dies"],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["characters"],
            "additionalProperties": False,
        },
        "strict": True,
    },
}


def get_movie_ids(input_dir: Path) -> List[str]:
    """Retrieves a list of movie IDs that have plot summaries"""
    summary_files = list(input_dir.glob('plot_summaries_*.txt'))
    movie_ids = [f.stem.split('_')[2] for f in summary_files]
    logging.info(f"Found {len(movie_ids)} movies with plot summaries.")
    return movie_ids


def get_character_names(movie_id: str, input_dir: Path) -> Optional[List[str]]:
    character_metadata_file = input_dir / f'character.metadata_{movie_id}.csv'
    if not character_metadata_file.exists():
        logging.debug(f"Metadata file not found for movie ID: {movie_id}")
        return None
    
    try:
        character_df = pd.read_csv(character_metadata_file, usecols=['character_name'])
        character_names = character_df['character_name'].dropna().astype(str).tolist()
        if not character_names:
            logging.debug(f"No valid character names found for movie ID: {movie_id}")
            return None
        return character_names
    except Exception as e:
        logging.error(f"Error reading character metadata for movie ID {movie_id}: {e}")
        return None
    

def get_plot_summary(movie_id: str, input_dir: Path) -> str:
    plot_summary_file = input_dir / f'plot_summaries_{movie_id}.txt'
    try:
        plot_summary = plot_summary_file.read_text().strip()
        if not plot_summary:
            logging.warning(f"Empty plot summary for movie ID: {movie_id}")
            return None
        return plot_summary
    except Exception as e:
        logging.error(f"Error reading plot summary for movie ID {movie_id}: {e}")
        return None


def construct_user_prompt(character_names: Optional[List[str]], plot_summary: str) -> str:
    if character_names:
        names_str = ', '.join(character_names)
        prompt = (
            f"<summary>{plot_summary}</summary>\n"
            f"<names>{names_str}</names>"
        )
    else:
        prompt = f"<summary>{plot_summary}</summary>"
    return prompt


def get_user_prompt(movie_id: str, input_dir: Path) -> str:
    """For use in notebooks where API requests is created with the SDK"""
    character_names = get_character_names(movie_id, input_dir)
    plot_summary = get_plot_summary(movie_id, input_dir)
    return construct_user_prompt(character_names, plot_summary)


def create_api_request(movie_id: str, input_dir: Path, missing_ids: List[str]) -> Optional[dict]:
    character_names = get_character_names(movie_id, input_dir)
    plot_summary = get_plot_summary(movie_id, input_dir)

    if not character_names:
        logging.debug(f"No character names for movie ID {movie_id}. Logging to missing IDs.")
        missing_ids.append(movie_id)

    user_prompt = construct_user_prompt(character_names, plot_summary)

    request = {
        "custom_id": movie_id,
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": RESPONSE_FORMAT
        }
    }

    return request


def create_batch_requests(movie_ids: List[str], input_dir: Path, batch_file: Path, missing_ids_file: Path):
    total = len(movie_ids)
    missing_ids = []

    with batch_file.open('w', encoding='utf-8') as batch_f:
        for movie_id in tqdm(movie_ids, desc="Creating batch requests"):
            request = create_api_request(movie_id, input_dir, missing_ids)
            if request:
                batch_f.write(json.dumps(request) + '\n')

    if missing_ids:
        with missing_ids_file.open('w', encoding='utf-8') as missing_f:
            for mid in missing_ids:
                missing_f.write(f"{mid}\n")
        logging.info(f"Logged {len(missing_ids)} movie IDs with missing metadata or character names to {missing_ids_file}")
    else:
        logging.info("No missing metadata or character names found.")

    logging.info(f"Batch input saved to {batch_file}")
    logging.info(f"Total movies processed: {total}")
    logging.info(f"Total movies with missing metadata/character names: {len(missing_ids)}")


def submit_batch_job(batch_file: Path) -> Optional[str]:
    try:
        client = OpenAI()
        with batch_file.open("rb") as f:
            batch_input_file = client.files.create(
                file=f,
                purpose="batch"
            )

        batch_input_file_id = batch_input_file.id

        batch_metadata = client.batches.create(
            input_file_id=batch_input_file_id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
            metadata={
                "description": "Extract character deaths from plot summaries",
            }
        )

        logging.info(f"Submitted batch job with ID: {batch_metadata.id}")
        return batch_metadata.id

    except Exception as e:
        logging.error(f"Failed to submit batch job: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Create and submit a batch of OpenAI API requests.")
    parser.add_argument("-i", "--input-dir", type=Path, default="./data/interim/", 
                        help="Directory containing split plot summaries and character metadata (default: ./data/interim/)")
    parser.add_argument("--batch-file", type=Path, default="./batchinput.jsonl", 
                        help="Path to save batch input file (default: ./batchinput.jsonl)")
    parser.add_argument("--missing-ids-file", type=Path, default="./missing_metadata_movie_ids.txt", 
                        help="Path to save list of movie IDs with missing metadata or character names (default: ./missing_metadata_movie_ids.txt)")
    parser.add_argument("--movie-ids", nargs='*', help="List of specific movie IDs to process")
    parser.add_argument("--debug", action="store_true", help="Do not submit the batch job, only create the input file.")

    args = parser.parse_args()
    input_dir = args.input_dir
    batch_file = args.batch_file
    missing_ids_file = args.missing_ids_file
    movie_ids = args.movie_ids
    debug_mode = args.debug

    if movie_ids:
        logging.info(f"Processing {len(movie_ids)} specified movies: {movie_ids}")
    else:
        movie_ids = get_movie_ids(input_dir)
        logging.info(f"Processing {len(movie_ids)} movies found in the input directory: {input_dir}")

    create_batch_requests(movie_ids, input_dir, batch_file, missing_ids_file)

    logging.info(f"Saved batch input to {batch_file}")

    if debug_mode:
        logging.info("Debug mode enabled. Skipping batch job submission.")
        return

    batch_id = submit_batch_job(batch_file)
    if batch_id:
        batch_id_file = Path("./batch_id.txt")
        with batch_id_file.open(mode='a', encoding='utf-8') as f:
            f.write(batch_id + "\n")

        logging.info(f"Batch ID {batch_id} written to {batch_id_file}")


if __name__ == "__main__":
    main()
