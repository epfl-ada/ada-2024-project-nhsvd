from argparse import ArgumentParser
import json
import logging
from pathlib import Path
from typing import Type, Dict, Any, List
from pydantic import BaseModel

from api_mining.utils.common import (
    read_system_prompt,
    construct_user_prompt,
    get_plot_summary,
    get_character_names,
    get_batch_ids,
    save_batch_ids
)
from api_mining.models.core import ProcessingMethod
from api_mining.database.db import create_database_handler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def remove_title(d):
    """Remove 'title' keys recursively from a dictionary."""
    return {k: remove_title(v) if isinstance(v, dict) else v 
            for k, v in d.items() if k != "title"}

def create_response_format(characters_model: Type[BaseModel], name: str) -> Dict[str, Any]:
    """Generate a response format JSON schema for character models."""
    schema = characters_model.model_json_schema()

    schema = remove_title(schema)
    schema["additionalProperties"] = False

    defs = schema.pop("$defs", None)

    response_format = {
        "type": "json_schema",
        "json_schema": {
            "name": name,
            "schema": {
                "type": "object",
                "properties": {
                    "characters": {
                        "type": "array",
                        "items": schema
                    }
                },
                "required": ["characters"],
                "additionalProperties": False,
            },
            "strict": True,
        },
    }

    if defs:
        response_format["json_schema"]["schema"]["$defs"] = defs

    return response_format

class BatchCreator:
    """Manages the creation of movie processing batches for the OpenAI batch API."""
    def __init__(
        self,
        db_path: Path,
        input_dir: Path,
        batch_dir: Path,
        num_batches: int,
        batch_token_target: int
    ):
        self.db = create_database_handler(db_path)
        self.input_dir = input_dir
        self.batch_dir = batch_dir
        self.num_batches = num_batches
        self.batch_token_target = batch_token_target
        self.batch_count = self.db.get_batch_count()
        self.system_prompt = read_system_prompt(self.db.data_type)
        self.response_format = create_response_format(
            characters_model=self.db.Character, 
            name=f"character_{self.db.data_type.value}"
        )

    def create_batches(self) -> None:
        """Create batches of movies for processing based on token count limits."""
        with self.db.get_session() as session:
            movies = self.db.get_pending_chat_movies()
            if not movies:
                logging.info("No pending movies available for batching.")
                return
            
            logging.info(f"Found {len(movies)} pending movies not assigned to a batch")

            for movie in movies:
                session.add(movie)
            # Sort by token count to process the shortest summaries first (least tokens per request)
            movies.sort(key=lambda x: x.token_count)
            
            current_batch = 1
            current_tokens = 0
            batch_movies = []
            batch_ids = get_batch_ids(self.batch_dir)

            for movie in movies:
                if current_batch > self.num_batches:
                    break
                    
                if current_tokens + movie.token_count > self.batch_token_target:
                    self.create_batch_file(current_batch, batch_movies, current_tokens)
                    current_batch += 1
                    batch_movies = [movie.id]
                    current_tokens = movie.token_count
                    batch_ids.append(None)
                else:
                    batch_movies.append(movie.id)
                    current_tokens += movie.token_count
            
            if batch_movies and current_batch <= self.num_batches:
                self.create_batch_file(current_batch, batch_movies, current_tokens)
                batch_ids.append(None)
            
            save_batch_ids(self.batch_dir, batch_ids)
    
    def create_batch_file(self, batch_num: int, movie_ids: List[str], token_count: int) -> None:
        """Create a batch input file for the specified movies and update their database records."""
        batch_index = self.batch_count + batch_num

        batch_file = self.batch_dir / f"batch_{batch_index}.jsonl"
        
        with batch_file.open('w') as f:
            for movie_id in movie_ids:
                plot_summary = get_plot_summary(self.input_dir, movie_id)
                character_names = get_character_names(self.input_dir, movie_id)
                user_prompt = construct_user_prompt(
                    plot_summary=plot_summary,
                    character_names=character_names
                )
                
                request = {
                    "custom_id": movie_id,
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": {
                        "model": "gpt-4o-mini",
                        "messages": [
                            {"role": "system", "content": self.system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "response_format": self.response_format
                    }
                }
                f.write(json.dumps(request) + '\n')
                
                self.db.update_movie(
                    movie_id=movie_id,
                    method=ProcessingMethod.BATCH,
                    batch_index=batch_index,
                    token_count=token_count
                )
        
        logging.info(f"Created batch {batch_index} with {len(movie_ids)} movies and estimated {token_count} tokens")

def main():
    parser = ArgumentParser(description="Create new batches from pending movies")
    parser.add_argument("--db-path", type=Path, required=True, help="Path to the database")
    parser.add_argument("--input-dir", type=Path, default=Path("./data/interim"), 
                        help="Path to the input directory (default: ./data/interim)")
    parser.add_argument("--batch-dir", type=Path, required=True,
                        help="Path to the batch directory")
    parser.add_argument("--num-batches", type=int, default=4, 
                        help="Number of batches to create (default: 4)")
    parser.add_argument("--batch-token-target", type=int, default=1_900_000, 
                        help="Target token count for each batch (default: 1_900_000)")
    args = parser.parse_args()

    args.batch_dir.mkdir(parents=True, exist_ok=True)

    creator = BatchCreator(args.db_path, args.input_dir, args.batch_dir, args.num_batches, args.batch_token_target)
    creator.create_batches()
    logging.info("Batch creation complete.")


if __name__ == "__main__":
    main()
