import json
import argparse
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()


def retrieve_batch_id(args):
    if args.id:
        return args.id
    elif args.file.is_file():
        return args.file.read_text().strip()
    else:
        raise FileNotFoundError(f"Batch ID file {args.file} not found and no batch ID provided.")


def process_and_save_output(batch_output, output_path, refused_file_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    refusals = []

    with output_path.open("w") as output_file:
        for line in batch_output.splitlines():
            try:
                data = json.loads(line)
                refusal = data["response"]["body"]["choices"][0]["message"]["refusal"]

                if refusal is not None:
                    refusals.append(data["custom_id"])
                    continue

                output_data = {
                    "movie_id": data["custom_id"],
                    "content": data["response"]["body"]["choices"][0]["message"]["content"]
                }
                output_file.write(json.dumps(output_data) + "\n")
            
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON line: {e}")
            except KeyError as e:
                print(f"Missing expected key in data: {e}")

    if refusals:
        refused_file_path.unlink(missing_ok=True)
        refused_file_path.write_text("\n".join(refusals))
        print(f"Saved refused movie IDs to {refused_file_path}")
    else:
        print("No requests were refused")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", type=Path, default="./batch_id.txt", help="Batch ID file path (default: ./batch_id.txt)")
    parser.add_argument("--id", type=str, help="Batch ID")
    parser.add_argument("-o", "--output", type=Path, default="./data/processed/batchoutput.jsonl", help="Output path for processed batch (default: ./data/processed/batchoutput.jsonl)")
    args = parser.parse_args()

    try:
        batch_id = retrieve_batch_id(args)
        status = client.batches.retrieve(batch_id)

        if status.status == "completed":
            output_file_id = status.output_file_id
            batch_output = client.files.content(output_file_id).text
            output_path = args.output
            refused_file_path = Path("./refused_ids.txt")
            process_and_save_output(batch_output, output_path, refused_file_path)
            print(f"Saved processed batch output to {output_path}")
        else:
            print(f"Batch job {batch_id} is currently in status: '{status.status}'.")
            print(status)

    except FileNotFoundError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
