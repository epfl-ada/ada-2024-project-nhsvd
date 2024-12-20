from argparse import ArgumentParser
import logging
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from api_mining.models.core import (
    DataType,
    MetadataStatus, 
    ProcessingStatus, 
    ProcessingMethod,
    DatabaseMetadata
)
from api_mining.database.db import DeathsDatabaseHandler, TropesDatabaseHandler
from api_mining.utils.common import (
    get_plot_summary,
    get_character_names,
)
from api_mining.utils.token_counter import TokenCounter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class DBInitializer:
    """Initializes and processes a database with movie and character data."""
    def __init__(self, db_path: Path, data_type: DataType, input_dir: Path):
        handlers = {
            DataType.DEATHS: DeathsDatabaseHandler,
            DataType.TROPES: TropesDatabaseHandler
        }
        handler_class = handlers.get(data_type)
        if not handler_class:
            raise ValueError(f"Unknown data type: {data_type}")
        
        self.db = handler_class(db_path)
        with self.db.get_session() as session:
            metadata = DatabaseMetadata(data_type=data_type)
            session.add(metadata)

        self.input_dir = input_dir
        self.token_counter = TokenCounter(data_type)

    def check_character_metadata(self, movie_id: str) -> MetadataStatus:
        """Check the availability and completeness of character metadata for a movie."""
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
        """Process all movies by reading plot summaries and character metadata."""
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
    parser = ArgumentParser(description="Initialize database with all movies")
    parser.add_argument("--db-path", type=Path, required=True, 
                        help="Path to the database")
    parser.add_argument("--data-type", type=DataType, choices=[d.value for d in DataType],
                       required=True, help="Type of data to store")
    parser.add_argument("--input-dir", type=Path, default=Path("./data/interim"), 
                        help="Path to the input directory (default: ./data/interim)")
    args = parser.parse_args()

    args.db_path.parent.mkdir(parents=True, exist_ok=True)
    if args.db_path.exists():
        logging.warning(f"Database file already exists at {args.db_path}. Exiting.")
        return

    initializer = DBInitializer(args.db_path, args.data_type, args.input_dir)
    initializer.process_all_movies()
    logging.info("Database initialization complete.")


if __name__ == "__main__":
    main()
