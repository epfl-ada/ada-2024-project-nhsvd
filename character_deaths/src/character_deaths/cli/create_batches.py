import argparse
import json
import logging
from pathlib import Path
from typing import List, Tuple, Optional

import pandas as pd
from tqdm import tqdm

from character_deaths.models import ProcessingMethod, ProcessingStatus, MetadataStatus
from character_deaths.database import DatabaseHandler
from character_deaths.utils import (
    TokenCounter, 
    SYSTEM_PROMPT, 
    construct_user_prompt, 
    get_summary, 
    get_char_names,
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
        output_dir: Path,
        num_batches: int,
        batch_token_target: int
    ):
        self.db = db
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.token_counter = TokenCounter()
        self.num_batches = num_batches
        self.batch_token_target = batch_token_target

    def check_character_metadata(self, movie_id: str) -> MetadataStatus:
        char_file = self.input_dir / f'character.metadata_{movie_id}.csv'
        
        if not char_file.exists():
            return MetadataStatus.MISSING_METADATA
            
        try:
            df = pd.read_csv(char_file, usecols=['character_name'])
            valid_names = df['character_name'].dropna().astype(str).tolist()
            
            if not valid_names:
                return MetadataStatus.EMPTY_CHARACTERS
                
            return MetadataStatus.COMPLETE
            
        except Exception as e:
            logging.error(f"Error reading character metadata for {movie_id}: {e}")
            return MetadataStatus.MISSING_METADATA
    
    def get_plot_summary(self, movie_id: str) -> Optional[str]:
        try:
            return get_summary(self.input_dir, movie_id)
        except Exception as e:
            logging.error(f"Error reading plot summary for {movie_id}: {e}")
            return None
    
    def get_character_names(self, movie_id: str) -> Optional[List[str]]:
        try:
            return get_char_names(self.input_dir, movie_id)
        except Exception as e:
            logging.error(f"Error reading characters for {movie_id}: {e}")
            return None
    
    def process_all_movies(self) -> List[Tuple[str, int]]:
        """Process all movies and return list of (movie_id, token_count)"""
        all_movies = []
        
        plot_files = list(self.input_dir.glob('plot_summaries_*.txt'))
        
        for plot_file in tqdm(plot_files, desc="Processing movies"):
            movie_id = plot_file.stem.split('_')[2]
            plot_summary = self.get_plot_summary(movie_id)
            
            if not plot_summary:
                continue
                
            metadata_status = self.check_character_metadata(movie_id)
            character_names = self.get_character_names(movie_id) if metadata_status == MetadataStatus.COMPLETE else None
            
            self.db.add_movie(
                movie_id=movie_id,
                plot_summary=plot_summary,
                metadata_status=metadata_status
            )
            
            token_count = self.token_counter.estimate_request_tokens(
                plot_summary=plot_summary,
                character_names=character_names
            )
            all_movies.append((movie_id, token_count))
        
        return all_movies
    
    def create_batches(self, movies: List[Tuple[str, int]]) -> None:
        """Create batch files and update database"""
        # Sort by token count to process smallest in batches
        movies.sort(key=lambda x: x[1])
        
        current_batch = 1
        current_tokens = 0
        batch_movies = []
        batch_ids = []

        for movie_id, token_count in movies:
            if current_batch > self.num_batches:
                for remaining_id, _ in movies[len(batch_movies):]:
                    self.db.update_movie_method(
                        movie_id=remaining_id,
                        method=ProcessingMethod.CHAT
                    )
                break
                
            if current_tokens + token_count > self.batch_token_target:
                self.create_batch_file(current_batch, batch_movies, current_tokens)
                current_batch += 1
                batch_movies = [(movie_id, token_count)]
                current_tokens = token_count
                batch_ids.append(None)
            else:
                batch_movies.append((movie_id, token_count))
                current_tokens += token_count
        
        if batch_movies and current_batch <= self.num_batches:
            self.create_batch_file(current_batch, batch_movies, current_tokens)
            batch_ids.append(None)
        
        save_batch_ids(self.output_dir, batch_ids)
    
    def create_batch_file(self, batch_num: int, movies: List[Tuple[str, int]], token_count: int) -> None:
        """Create batch file and update database records"""
        batch_file = self.output_dir / f"batch_{batch_num}.jsonl"
        
        with batch_file.open('w') as f:
            for movie_id, _ in movies:
                plot_summary = self.get_plot_summary(movie_id)
                character_names = self.get_character_names(movie_id)
                
                request = {
                    "custom_id": movie_id,
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": {
                        "model": "gpt-4o-mini",
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": construct_user_prompt(plot_summary=plot_summary, character_names=character_names)}
                        ],
                        "response_format": RESPONSE_FORMAT
                    }
                }
                f.write(json.dumps(request) + '\n')
                
                self.db.update_movie_method(
                    movie_id=movie_id,
                    method=ProcessingMethod.BATCH,
                    batch_index=batch_num
                )
                self.db.update_movie_status(
                    movie_id=movie_id,
                    status=ProcessingStatus.PENDING,
                )
        
        logging.info(f"Created batch {batch_num} with {len(movies)} movies and estimated {token_count} tokens")

def main():
    parser = argparse.ArgumentParser(description="Initialize database and create batch files")
    parser.add_argument("--db-path", type=Path, required=True)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--num-batches", type=int, default=4)
    parser.add_argument("--batch-token-target", type=int, default=1_900_000)
    args = parser.parse_args()

    args.db_path.parent.mkdir(parents=True, exist_ok=True)
    if args.db_path.exists():
        logging.warning(f"Database file already exists at {args.db_path}. Exiting.")
        return

    args.output_dir.mkdir(parents=True, exist_ok=True)

    db = DatabaseHandler(args.db_path) 
    creator = BatchCreator(db, args.input_dir, args.output_dir, args.num_batches, args.batch_token_target)
    movies = creator.process_all_movies()
    creator.create_batches(movies)

if __name__ == "__main__":
    main()
