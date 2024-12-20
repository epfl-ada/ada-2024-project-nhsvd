from argparse import ArgumentParser
import logging
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

from api_mining.models.core import ProcessingStatus
from api_mining.database.db import create_database_handler
from api_mining.utils.common import get_batch_ids, save_batch_ids

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def submit_batch(
    batch_file: Path, 
    batch_num: int, 
    db_path: Path,
    batch_dir: Path, 
    force: bool = False
) -> None:
    """Submit a batch file for processing and update its status in the database."""
    db = create_database_handler(db_path)
    batch_ids = get_batch_ids(batch_dir)
    
    while len(batch_ids) < batch_num:
        batch_ids.append(None)

    if batch_ids[batch_num - 1] is not None and not force:
        logging.info(f"Batch {batch_num} already submitted")
        return

    try:
        client = OpenAI()
        
        with batch_file.open("rb") as f:
            batch_input_file = client.files.create(
                file=f,
                purpose="batch"
            )

        batch = client.batches.create(
            input_file_id=batch_input_file.id,
            endpoint="/v1/chat/completions",
            completion_window="24h"
        )

        batch_ids[batch_num - 1] = batch.id
        save_batch_ids(batch_dir, batch_ids)
        
        db.update_batch_movies_status(batch_num, batch.id, ProcessingStatus.PROCESSING)
        
        logging.info(f"Submitted batch {batch_num} with ID: {batch.id}")

    except Exception as e:
        logging.error(f"Failed to submit batch {batch_num}: {e}")
        raise

def main():
    parser = ArgumentParser(description="Submit a batch for processing")
    parser.add_argument("--db-path", type=Path, required=True, 
                        help="Path to the database")
    parser.add_argument("--batch-num", type=int, required=True, 
                        help="Batch number to submit (indexed from 1)")
    parser.add_argument("--batch-dir", type=Path, required=True, 
                        help="Path to the batch directory")
    parser.add_argument("-f", "--force", action="store_true", 
                        help="Force submission even if the batch is already submitted")
    args = parser.parse_args()
    
    batch_file = args.batch_dir / f"batch_{args.batch_num}.jsonl"
    if not batch_file.exists():
        raise FileNotFoundError(f"Batch file not found: {batch_file}")

    submit_batch(batch_file, args.batch_num, args.db_path, args.batch_dir, args.force)

if __name__ == "__main__":
    main()
