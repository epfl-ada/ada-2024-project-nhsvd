import argparse
import logging
from typing import Optional, List
from pathlib import Path

from openai import OpenAI, RateLimitError
from tqdm import tqdm
from dotenv import load_dotenv
load_dotenv()

from character_deaths.models import Movie, ProcessingStatus, Characters
from character_deaths.database import DatabaseHandler
from character_deaths.utils import (
    SYSTEM_PROMPT, construct_user_prompt, get_summary, get_char_names
)

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s %(levelname)s: %(message)s'
)

class ChatProcessor:
    def __init__(self, client: OpenAI, db: DatabaseHandler, input_dir: Path):
        self.client = client
        self.db = db
        self.input_dir = input_dir

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

    def process_movie(self, movie: Movie) -> bool:
        """Process a single movie, return True if successful"""
        try:
            character_names = self.get_character_names(movie.id)
            plot_summary = self.get_plot_summary(movie.id)
            
            completion = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": construct_user_prompt(
                        plot_summary=plot_summary,
                        character_names=character_names
                    )}
                ],
                response_format=Characters
            )
            
            result = completion.choices[0].message.parsed
            self.db.add_character_deaths(movie.id, result.characters)
            return True

        except RateLimitError:
            logging.error("Rate limit reached - stopping processing")
            return False
        except Exception as e:
            logging.error(f"Error processing movie {movie.id}: {e}")
            self.db.update_movie_status(movie.id, ProcessingStatus.FAILED)
            return True

    def process_pending_movies(self) -> None:
        """Process all pending movies"""

        with self.db.get_session() as session:
            pending_movies = self.db.get_pending_chat_movies(limit=50_000)
        
            if not pending_movies:
                logging.info("No pending movies to process")
                return
                
            for movie in tqdm(pending_movies, desc="Processing movies"):
                session.add(movie)
                if not self.process_movie(movie):
                    break

def main():
    parser = argparse.ArgumentParser(description="Process movies using chat (streaming)API")
    parser.add_argument("--db-path", type=Path, required=True)
    parser.add_argument("--input-dir", type=Path, required=True)
    args = parser.parse_args()
    
    db = DatabaseHandler(args.db_path)
    client = OpenAI()
    processor = ChatProcessor(client, db, input_dir=args.input_dir)
    processor.process_pending_movies()

if __name__ == "__main__":
    main()
