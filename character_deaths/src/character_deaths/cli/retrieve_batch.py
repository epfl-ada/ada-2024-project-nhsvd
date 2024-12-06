import argparse
import logging
import json
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

from character_deaths.models import ProcessingStatus, Characters
from character_deaths.database import DatabaseHandler
from character_deaths.utils.common import get_batch_ids

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

def retrieve_batch_results(batch_id: str, db: DatabaseHandler, 
                         client: OpenAI) -> None:
    """Retrieve and process results from a completed batch"""
    try:
        status = client.batches.retrieve(batch_id)
        if status.status != "completed":
            logging.info(f"Batch {batch_id} not completed (status: {status.status})")
            return
        
        output_file = client.files.content(status.output_file_id)
        content = output_file.text
        
        for line in content.splitlines():
            try:
                data = json.loads(line)
                movie_id = data['custom_id']
                response = json.loads(data['response']['body']['choices'][0]['message']['content'])
                
                characters = Characters(**response)
                db.add_character_deaths(movie_id, characters.characters)
                db.update_movie_status(movie_id, ProcessingStatus.COMPLETED)
                
            except Exception as e:
                logging.error(f"Error processing result for movie {movie_id}: {e}")
                db.update_movie_status(movie_id, ProcessingStatus.FAILED)
        
        logging.info(f"Processed results for batch {batch_id}")
        
    except Exception as e:
        logging.error(f"Error retrieving batch {batch_id}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Retrieve batch results")
    parser.add_argument("--db-path", type=Path, required=True)
    parser.add_argument("--batch-num", type=int, required=True, help="Batch number to retrieve (indexed from 1)")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    
    batch_ids = get_batch_ids(args.output_dir)
    if args.batch_num > len(batch_ids) or not batch_ids[args.batch_num - 1]:
        logging.error(f"No batch ID found for batch {args.batch_num}")
        return
    
    batch_id = batch_ids[args.batch_num - 1]
    db = DatabaseHandler(args.db_path)
    client = OpenAI()
    
    retrieve_batch_results(batch_id, db, client)

if __name__ == "__main__":
    main()
