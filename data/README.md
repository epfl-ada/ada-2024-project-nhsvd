### Data directory structure

The default and assumed structure of data is as follows:
```
├── data
    ├── interim        <- Intermediate data that has been transformed.
    ├── processed      <- Final data used for modeling.
    └── raw            <- Original immutable data.
        ├── character.metadata.tsv
        ├── movie.metadata.tsv
        ├── name.clusters.txt
        ├── plot_summaries.txt
        ├── tvtropes.clusters.txt
        └── corenlp_plot_summaries
            └── {movie_id}.xml
```
all the preprocessing scripts take `input_dir` and `output_dir` from the CLI.

### Usage

1. Parse XML to CSV files:
   ```
   python src/preprocessing/parse_corenlp_xml.py
   ```
2. Split `character.metadata.tsv` by movie ID to enable parallel processing
    ```
    python src/preprocessing/split_char_metadata.py
    ```
3. Build bags of words for each character in each movie following the methodology of *Learning Latent Personas*.
   ```
   python src/preprocessing/build_char_word_bags.py
   ```
A member(Samuli Näppi) wrote a faster version of the XML parser in Rust (`src/preprocessing/xml_to_csv`).
