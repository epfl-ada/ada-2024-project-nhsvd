import argparse
from pathlib import Path


def split_plot_summaries(input_dir, output_dir):
    summary_file = input_dir / 'plot_summaries.txt'

    with open(summary_file, 'r', encoding='utf-8') as file:
        for line in file:
            movie_id, summary = line.split('\t', 1)

            output_file = output_dir / f'plot_summaries_{movie_id}.txt'
            with open(output_file, 'w', encoding='utf-8') as output:
                output.write(summary)


def main():
    parser = argparse.ArgumentParser(description="Split plot summaries by movie ID.")
    parser.add_argument("-i", "--input-dir", type=Path, required=False, default="./data/raw/", help="Directory containing plot summary file")
    parser.add_argument("-o", "--output-dir", type=Path, required=False, default="./data/interim/", help="Directory to save split plot summary files")

    args = parser.parse_args()
    input_dir = args.input_dir
    output_dir = args.output_dir

    output_dir.mkdir(parents=True, exist_ok=True)

    split_plot_summaries(input_dir, output_dir)

if __name__ == '__main__':
    main()
