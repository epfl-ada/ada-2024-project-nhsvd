import argparse
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", type=Path, required=False, default="./batch_id.txt", 
                        help="Batch ID file output by `submit_openai_batch_job.py` (default: ./batch_id.txt)")
    parser.add_argument("--id", type=str, required=False)

    args = parser.parse_args()

    if args.id:
        batch_id = args.id
    else:
        batch_id = args.file.read_text().strip()

    status = client.batches.retrieve(batch_id)
    print(status)


if __name__ == "__main__":
    main()