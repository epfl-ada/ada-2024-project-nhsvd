import argparse
import json
from pathlib import Path
from typing import List, Optional

import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator
from openai import OpenAI


load_dotenv()

# we can probably come up with a better prompt
system_prompt = "Given a list of character names and a plot summary, extract the information about character deaths."

response_format = {
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
                        "additionalProperties": False
                    },
                }
            },
            "required": ["characters"],
            "additionalProperties": False
        }
    }, 
    "strict": True 
}

# the above schema corresponds to the following pydantic model
# class Character(BaseModel):
#     name: str
#     dies: bool

# class Characters(BaseModel):
#     characters: List[Character]


def get_movie_character_names(movie_id: str, input_dir: Path) -> Optional[List[str]]:
    character_metadata_file = input_dir / f'character.metadata_{movie_id}.csv'
    character_names = pd.read_csv(character_metadata_file, usecols=['character_name']).character_name.tolist()
    # some movies have character metadata but no character names
    character_names = [name for name in character_names if isinstance(name, str)]
    if character_names:
        return character_names
    return None


def get_movie_plot_summary(movie_id: str, input_dir: Path) -> str:
    plot_summary_file = input_dir / f'plot_summaries_{movie_id}.txt'
    plot_summary = plot_summary_file.read_text()
    return plot_summary


def format_user_prompt(character_names: List, plot_summary: str) -> str:
    character_names = [str(name) for name in character_names]
    return f"Character names: {', '.join(character_names)}\nPlot summary: {str(plot_summary).strip()}"


def get_user_prompt(movie_id: str, input_dir: Path) -> Optional[str]:
    character_names = get_movie_character_names(movie_id, input_dir)
    if not character_names:
        return None

    plot_summary = get_movie_plot_summary(movie_id, input_dir)

    return format_user_prompt(character_names, plot_summary)


def create_api_request(movie_id: str, input_dir: Path) -> Optional[dict]:
    user_prompt = get_user_prompt(movie_id, input_dir)
    if not user_prompt:
        return None
    
    return {
        "custom_id": movie_id,
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": response_format
        }
    }


def create_batch(movie_ids: List[str], input_dir: Path, batch_file: Path):
    count = 0
    with open(batch_file, 'w') as f:
        for movie_id in movie_ids:
            request = create_api_request(movie_id, input_dir)
            if not request:
                count += 1
                continue
            f.write(json.dumps(request) + '\n')
    
    print(f"{count} movies had no character names")

def submit_batch(batch_file: Path):
    client = OpenAI()

    batch_input_file = client.files.create(
        file=open(batch_file, "rb"),
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

    return batch_metadata


def get_movie_ids(input_dir: Path) -> List[str]:
    summary_files = list(input_dir.glob('plot_summaries_*.txt'))
    metadata_files = list(input_dir.glob('character.metadata_*.csv'))

    summary_ids = [f.stem.split('_')[2] for f in summary_files]
    metadata_ids = [f.stem.split('_')[1] for f in metadata_files]
    movie_ids = list(set(metadata_ids) & set(summary_ids))

    return movie_ids


def main():
    parser = argparse.ArgumentParser(description="Create batch of OpenAI API requests.")
    parser.add_argument("-i", "--input-dir", type=Path, required=False, default="./data/interim/", 
                        help="Directory containing split plot summaries and character metadata (default: ./data/interim/)")
    parser.add_argument("--batch-file", type=Path, required=False, default="./batchinput.jsonl", help="Batch input file (default: ./batchinput.jsonl)")
    parser.add_argument("--movie-ids", required=False, nargs='*', help="List of movie IDs to process")

    args = parser.parse_args()
    input_dir = args.input_dir
    batch_file = args.batch_file
    movie_ids = args.movie_ids

    movie_ids = ["2583808"]

    if movie_ids:
        print(f"Processing {len(movie_ids)} movies:", movie_ids)
    else:
        movie_ids = get_movie_ids(input_dir)
        print(f"Processing {len(movie_ids)} movies")

    create_batch(movie_ids, input_dir, batch_file)

    print(f"Saved batch input to {batch_file}")

    # batch_metadata = submit_batch(batch_file)

    # write batch_metadata.id to a file for easier copy-pasting

    # batch_id_file = Path("./batch_id.txt")
    # if batch_id_file.exists():
    #     batch_id_file.unlink()

    # batch_id_file.write_text(batch_metadata.id)

    # print(f"Submitted batch with ID {batch_metadata.id}")
    # print(f"Batch ID written to {batch_id_file}")


if __name__ == "__main__":
    main()
