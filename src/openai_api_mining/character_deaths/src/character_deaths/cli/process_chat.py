import argparse
import logging
from pathlib import Path

from openai import OpenAI, RateLimitError
from tqdm import tqdm
from dotenv import load_dotenv
load_dotenv()

from character_deaths.models import Movie, ProcessingStatus, Characters
from character_deaths.database import DatabaseHandler
from character_deaths.utils import (
    SYSTEM_PROMPT, 
    construct_user_prompt,
    get_plot_summary, 
    get_character_names
)

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

class ChatProcessor:
    def __init__(self, client: OpenAI, db: DatabaseHandler, input_dir: Path):
        self.client = client
        self.db = db
        self.input_dir = input_dir

    def process_movie(self, movie: Movie) -> bool:
        try:
            character_names = get_character_names(self.input_dir, movie.id)
            plot_summary = get_plot_summary(self.input_dir, movie.id)
            
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
        except KeyboardInterrupt:
            logging.error("Keyboard interrupt - stopping processing")
            self.db.update_movie(
                movie_id=movie.id,
                status=ProcessingStatus.PENDING
            )
            return False
        except Exception as e:
            logging.error(f"Error processing movie {movie.id}: {e}")
            self.db.update_movie(
                movie_id=movie.id,
                status=ProcessingStatus.FAILED
            )
            return True

    def process_pending_movies(self) -> None:
        with self.db.get_session() as session:
            pending_movies = self.db.get_pending_chat_movies()
        
            if not pending_movies:
                logging.info("No pending movies to process")
                return
                
            for movie in tqdm(pending_movies, desc="Processing movies"):
                session.add(movie)
                if not self.process_movie(movie):
                    break

def main():
    parser = argparse.ArgumentParser(description="Process movies using chat (real-time) API")
    parser.add_argument("--db-path", type=Path, required=True, 
                        help="Path to the database")
    parser.add_argument("--input-dir", type=Path, default=Path("./data/interim"), 
                        help="Path to the input directory (default: ./data/interim)")
    args = parser.parse_args()
    
    db = DatabaseHandler(args.db_path)
    client = OpenAI()
    processor = ChatProcessor(client, db, input_dir=args.input_dir)
    processor.process_pending_movies()

if __name__ == "__main__":
    main()
