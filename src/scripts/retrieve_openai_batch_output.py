import json
import argparse
import logging
import csv
from pathlib import Path
from typing import List, Tuple

from dotenv import load_dotenv
from openai import OpenAI


logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
load_dotenv()
client = OpenAI()


def get_batch_ids(args) -> List[str]:
    batch_ids = set()

    if args.id:
        batch_ids.update(args.id)
        logging.info(f"Using {len(args.id)} batch ID(s) from command-line arguments.")

    if args.file:
        try:
            file_ids = [line.strip() for line in args.file.read_text().splitlines() if line.strip()]
            batch_ids.update(file_ids)
            logging.info(f"Using {len(file_ids)} batch ID(s) from file: {args.file}")
        except FileNotFoundError:
            logging.error(f"Batch ID file '{args.file}' not found.")
            if not batch_ids:
                raise
            else:
                logging.warning("Proceeding with batch IDs from command-line arguments.")

    if not batch_ids:
        raise ValueError("No batch IDs provided. Please specify batch IDs via --id or provide a batch ID file.")

    return list(batch_ids)


def process_response(response_jsonl: str) -> Tuple[List[dict], List[str], List[Tuple[str, str]]]:
    data_rows = []
    no_characters = []
    refusals = []

    for line in response_jsonl.splitlines():
        try:
            data = json.loads(line)
            movie_id = data['custom_id']
            message = data['response']['body']['choices'][0]['message']

            if refusal := message.get('refusal'):
                refusals.append((movie_id, refusal))
                logging.debug(f"Request refused for movie ID: {movie_id}")
                continue

            content = json.loads(message['content'])

            if not content.get('characters'):
                no_characters.append(movie_id)
                logging.debug(f"No characters found in response for movie ID: {movie_id}")
                continue

            for character in content.get('characters', []):
                data_rows.append({
                    "movie_id": movie_id,
                    "character_name": character.get('name', 'N/A'),
                    "dies": character.get('dies', False)
                })
        except (KeyError, json.JSONDecodeError) as e:
            logging.error(f"Error processing line: {e}")
            continue

    return data_rows, no_characters, refusals


def process_batch(batch_id: str) -> Tuple[List[dict], List[str], List[Tuple[str, str]]]:
    try:
        status = client.batches.retrieve(batch_id)
        if status.status == "completed":
            logging.info(f"Processing batch ID: {batch_id}")
            output_file_id = status.output_file_id
            response_jsonl = client.files.content(output_file_id).text
            return process_response(response_jsonl)
        else:
            logging.warning(f"Batch job '{batch_id}' is in status: '{status.status}'. Skipping.")
            return [], [], []
    except Exception as e:
        logging.error(f"Failed to process batch ID '{batch_id}': {e}")
        return [], [], []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", type=Path, help="Path to the batch ID file (one ID per line).")
    parser.add_argument("--id", type=str, nargs='*', 
                        help="One or more batch IDs. You can specify multiple IDs separated by space.")
    parser.add_argument("-o", "--output", type=Path, default="./data/processed/character_deaths.csv", 
                        help="Output CSV file path (default: ./data/processed/character_deaths.csv)")
    parser.add_argument("--no-characters", type=Path, default="./no_characters.txt", 
                        help="Path to save movie IDs with no characters (default: ./no_characters.txt)")
    parser.add_argument("--refused", type=Path, default="./refused_ids.txt", 
                        help="Path to save refused IDs (default: ./refused_ids.txt)")
    parser.add_argument("-y", action='store_true', help="Overwrite output files without prompting.")
    args = parser.parse_args()
    output_file = args.output
    no_characters_file = args.no_characters
    refusal_file = args.refused

    if not args.id and not args.file:
        parser.error("No batch IDs provided. Use --id or --file to specify batch IDs.")

    try:
        batch_ids = get_batch_ids(args)
        logging.info(f"Total batch IDs to process: {len(batch_ids)}")
    except (FileNotFoundError, ValueError) as e:
        logging.error(e)
        return

    output_file.parent.mkdir(parents=True, exist_ok=True)
    refusal_file.parent.mkdir(parents=True, exist_ok=True)

    if output_file.exists() and not args.y:
        logging.warning(f"Output file '{output_file}' already exists.")
        response = input("Do you want to overwrite the output file? (y/n) ").lower().strip()
        if response != "y":
            logging.info("Operation cancelled by user.")
            return

    all_data_rows = []
    all_no_characters = []
    all_refusals = []

    for batch_id in batch_ids:
        data_rows, no_characters, refusals = process_batch(batch_id)
        all_data_rows.extend(data_rows)
        all_no_characters.extend(no_characters)
        all_refusals.extend(refusals)

    if all_data_rows:
        with output_file.open('w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["movie_id", "character_name", "dies"])
            writer.writeheader()
            writer.writerows(all_data_rows)
        logging.info(f"Processed character data saved to '{output_file}'")
    else:
        logging.info("No data to write. Skipping writing to output file.")

    if all_no_characters:
        with no_characters_file.open('w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["movie_id"])
            writer.writeheader()
            for movie_id in all_no_characters:
                writer.writerow({"movie_id": movie_id})
        logging.info(f"Saved {len(all_no_characters)} movie IDs with no characters to '{no_characters_file}'")
    else:
        logging.info("No movie IDs with no characters.")

    if all_refusals:
        with refusal_file.open('w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=["movie_id", "refusal"])
            writer.writeheader()
            for movie_id, refusal_reason in all_refusals:
                writer.writerow({"movie_id": movie_id, "refusal": refusal_reason})
        logging.info(f"Saved {len(all_refusals)} refusals to '{refusal_file}'")
    else:
        logging.info("No requests were refused.")


if __name__ == "__main__":
    main()
