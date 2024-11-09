import argparse
from pathlib import Path
from lxml import etree
import multiprocessing as mp
from functools import partial
from tqdm import tqdm
import csv
import gzip

SENTENCE_XPATH = etree.XPath(".//sentence")
TOKEN_XPATH = etree.XPath("./tokens/token")
DEPENDENCY_XPATH = etree.XPath(f"./collapsed-ccprocessed-dependencies/dep")
COREFERENCE_XPATH = etree.XPath(".//coreference")


def parse_xml_to_csv(file_path, output_dir, compressed=False):
    open_func = gzip.open if compressed else open
    with open_func(file_path, "rb") as file:
        tree = etree.parse(file)
    root = tree.getroot()
    
    base_name = file_path.stem
    
    tokens_file = output_dir / f"tokens_{base_name}.csv"
    dependencies_file = output_dir / f"dependencies_{base_name}.csv"
    coreferences_file = output_dir / f"coreferences_{base_name}.csv"
    
    with open(tokens_file, mode="w", newline="", encoding="utf-8") as tf, \
         open(dependencies_file, mode="w", newline="", encoding="utf-8") as df, \
         open(coreferences_file, mode="w", newline="", encoding="utf-8") as cf:
        
        tokens_writer = csv.writer(tf)
        dependencies_writer = csv.writer(df)
        coreferences_writer = csv.writer(cf)
        
        tokens_writer.writerow([
            "sentence_id", "token_id", "word", "lemma",
            "CharacterOffsetBegin", "CharacterOffsetEnd",
            "POS", "NER"
        ])

        dependencies_writer.writerow([
            "sentence_id", "type",
            "governor", "governor_idx",
            "dependent", "dependent_idx"
        ])

        coreferences_writer.writerow([
            "representative", "sentence_id",
            "start", "end", "head"
        ])

        for sentence in SENTENCE_XPATH(root):
            sentence_id = sentence.get("id")

            for token in TOKEN_XPATH(sentence):
                tokens_writer.writerow([
                    sentence_id,
                    token.get("id"),
                    token.findtext("word"),
                    token.findtext("lemma"),
                    token.findtext("CharacterOffsetBegin"),
                    token.findtext("CharacterOffsetEnd"),
                    token.findtext("POS"),
                    token.findtext("NER")
                ])

            for dep in DEPENDENCY_XPATH(sentence):
                dependencies_writer.writerow([
                    sentence_id,
                    dep.get("type"),
                    dep.findtext("governor"),
                    dep.find("governor").get("idx"),
                    dep.findtext("dependent"),
                    dep.find("dependent").get("idx")
                ])

        for coreference in COREFERENCE_XPATH(root):
            for mention in coreference.xpath("mention"):
                representative = mention.get("representative") == "true"
                coreferences_writer.writerow([
                    representative,
                    mention.findtext("sentence"),
                    mention.findtext("start"),
                    mention.findtext("end"),
                    mention.findtext("head")
                ])


def process_files(file_paths, output_dir, compressed=False):
    process_and_save = partial(parse_xml_to_csv, output_dir=output_dir, compressed=compressed)

    with mp.Pool(mp.cpu_count()) as pool:
        list(tqdm(pool.imap_unordered(process_and_save, file_paths), total=len(file_paths)))


def main():
    parser = argparse.ArgumentParser(description="Parse XML files and save results to CSV.")
    parser.add_argument("-i", "--input-dir", type=Path, required=False, default="./data/raw/corenlp_plot_summaries/", help="Directory containing XML files")
    parser.add_argument("-o", "--output-dir", type=Path, required=False, default="./data/interim/corenlp_plot_summaries/", help="Directory to save CSV files")
    parser.add_argument("-n", "--num-files", type=int, default=None, help="Number of files to process")
    parser.add_argument("--compressed", action="store_true", help="Specify if input files are gz compressed")
    
    args = parser.parse_args()
    input_dir = args.input_dir
    output_dir = args.output_dir
    num_files = args.num_files
    compressed = args.compressed

    output_dir.mkdir(parents=True, exist_ok=True)

    if compressed:
        file_paths = list(input_dir.glob("*.xml.gz"))
    else:
        file_paths = list(input_dir.glob("*.xml"))

    if num_files:
        file_paths = file_paths[:num_files]

    print("Plot summaries:", len(file_paths))

    process_files(file_paths, output_dir, compressed=compressed)


if __name__ == "__main__":
    main()
