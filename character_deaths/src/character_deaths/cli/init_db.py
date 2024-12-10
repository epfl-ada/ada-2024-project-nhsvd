import argparse
import logging
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from character_deaths.models import (
    MetadataStatus, 
    ProcessingStatus, 
    ProcessingMethod
)
from character_deaths.database import DatabaseHandler
from character_deaths.utils import (
    TokenCounter,
    get_plot_summary,
    get_character_names,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class DBInitializer:
    def __init__(self, db: DatabaseHandler, input_dir: Path):
        self.db = db
        self.input_dir = input_dir
        self.token_counter = TokenCounter()

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
    
    def process_all_movies(self):
        plot_files = list(self.input_dir.glob('plot_summaries_*.txt'))
        
        for plot_file in tqdm(plot_files, desc="Processing movies"):
            movie_id = plot_file.stem.split('_')[2]
            plot_summary = get_plot_summary(self.input_dir, movie_id)
            
            if not plot_summary:
                continue

            metadata_status = self.check_character_metadata(movie_id)
            character_names = (
                get_character_names(self.input_dir, movie_id) 
                if metadata_status == MetadataStatus.COMPLETE 
                else None
            )
            
            token_count = self.token_counter.estimate_request_tokens(
                plot_summary=plot_summary,
                character_names=character_names
            )

            self.db.add_movie(
                movie_id=movie_id,
                metadata_status=metadata_status,
                status=ProcessingStatus.PENDING,
                method=ProcessingMethod.CHAT,
                token_count=token_count
            )


def main():
    parser = argparse.ArgumentParser(description="Initialize database with all movies")
    parser.add_argument("--db-path", type=Path, required=True, 
                        help="Path to the database")
    parser.add_argument("--input-dir", type=Path, default=Path("./data/interim"), 
                        help="Path to the input directory (default: ./data/interim)")
    args = parser.parse_args()

    args.db_path.parent.mkdir(parents=True, exist_ok=True)
    if args.db_path.exists():
        logging.warning(f"Database file already exists at {args.db_path}. Exiting.")
        return

    db = DatabaseHandler(args.db_path) 
    initializer = DBInitializer(db, args.input_dir)
    initializer.process_all_movies()
    logging.info("Database initialization complete.")


if __name__ == "__main__":
    main()
