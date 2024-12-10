import argparse
import json
import logging
from pathlib import Path
from typing import List

from character_deaths.models import ProcessingMethod
from character_deaths.database import DatabaseHandler
from character_deaths.utils import (
    SYSTEM_PROMPT, 
    construct_user_prompt, 
    get_plot_summary,
    get_character_names,
    get_batch_ids,
    save_batch_ids
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
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

class BatchCreator:
    def __init__(
        self,
        db: DatabaseHandler,
        input_dir: Path,
        batch_dir: Path,
        num_batches: int,
        batch_token_target: int
    ):
        self.db = db
        self.input_dir = input_dir
        self.batch_dir = batch_dir
        self.num_batches = num_batches
        self.batch_token_target = batch_token_target
        self.batch_count = self.db.get_batch_count()

    def create_batches(self) -> None:
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
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt}
                        ],
                        "response_format": RESPONSE_FORMAT
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
    parser = argparse.ArgumentParser(description="Create new batches from pending movies")
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

    db = DatabaseHandler(args.db_path)
    creator = BatchCreator(db, args.input_dir, args.batch_dir, args.num_batches, args.batch_token_target)
    creator.create_batches()
    logging.info("Batch creation complete.")


if __name__ == "__main__":
    main()
