import json
import argparse
import logging
import csv
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from openai import OpenAI


logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
load_dotenv()
client = OpenAI()


def get_batch_ids(args) -> List[str]:
    batch_ids = set()

    if args.id:
        if isinstance(args.id, list):
            batch_ids.update(args.id)
            logging.info(f"Using {len(args.id)} batch ID(s) from command-line arguments.")
        else:
            batch_ids.add(args.id)
            logging.info("Using batch ID from command-line argument.")

    if args.file:
        try:
            file_content = args.file.read_text().strip()
            file_ids = [line.strip() for line in file_content.splitlines() if line.strip()]
            batch_ids.update(file_ids)
            logging.info(f"Using {len(file_ids)} batch ID(s) from file: {args.file}")
        except FileNotFoundError:
            if not batch_ids:
                raise FileNotFoundError(f"Batch ID file '{args.file}' not found and no batch IDs provided via command line.")
            else:
                logging.warning(f"Batch ID file '{args.file}' not found. Proceeding with command-line batch IDs.")

    if not batch_ids:
        raise ValueError("No batch IDs provided. Please specify batch IDs via --id or provide a batch ID file.")

    return list(batch_ids)


def process_response(response_jsonl: str, csv_writer: csv.DictWriter, refusals: List[str]) -> None:
    for line in response_jsonl.splitlines():
        data = json.loads(line)
        movie_id = data['custom_id']
        message = data['response']['body']['choices'][0]['message']

        if refusal := message.get('refusal'):
            refusals.append((movie_id, refusal))
            logging.debug(f"Request refused for movie ID: {movie_id}")
            continue

        content = json.loads(message['content'])

        for character in content.get('characters', []):
            csv_writer.writerow({
                "movie_id": movie_id,
                "character_name": character.get('name', 'N/A'),
                "dies": character.get('dies', False)
            })


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", type=Path, help="Path to the batch ID file (one ID per line).")
    parser.add_argument("--id", type=str, nargs='*', 
                        help="One or more batch IDs. You can specify multiple IDs separated by space.")
    parser.add_argument("-o", "--output", type=Path, default="./data/processed/character_deaths.csv", 
                        help="Output CSV file path (default: ./data/processed/character_deaths.csv)")
    parser.add_argument("-r", "--refused", type=Path, default=Path("./refused_ids.txt"), 
                        help="Path to save refused IDs (default: ./refused_ids.txt)")
    args = parser.parse_args()

    if not args.id and not args.file:
        parser.error("No batch IDs provided. Use --id or --file to specify batch IDs.")

    try:
        batch_ids = get_batch_ids(args)
        logging.info(f"Total batch IDs to process: {len(batch_ids)}")
    except (FileNotFoundError, ValueError) as e:
        logging.error(e)
        return

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.refused.parent.mkdir(parents=True, exist_ok=True)


    with args.output.open(mode='w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ["movie_id", "character_name", "dies"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        refusals = []

        for batch_id in batch_ids:
            try:
                status = client.batches.retrieve(batch_id)
                if status.status == "completed":
                    logging.info(f"Processing batch ID: {batch_id}")
                    output_file_id = status.output_file_id
                    response_jsonl = client.files.content(output_file_id).text
                    process_response(response_jsonl, writer, refusals)
                else:
                    logging.warning(f"Batch job '{batch_id}' is in status: '{status.status}'. Skipping.")
            except Exception as e:
                logging.error(f"Failed to process batch ID '{batch_id}': {e}")

    if refusals:
        with args.refused.open(mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["movie_id", "refusal"])
            writer.writeheader()
            for movie_id, refusal_reason in refusals:
                writer.writerow({"movie_id": movie_id, "refusal": refusal_reason})

        logging.info(f"Saved {len(refusals)} refusals to '{args.refused}'")
    else:
        logging.info("No requests were refused.")

    logging.info(f"Processed character data saved to '{args.output}'")


if __name__ == "__main__":
    main()
