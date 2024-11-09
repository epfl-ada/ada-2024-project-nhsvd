# CMU Movie Summary Corpus Analysis by NHSVD

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
all the preprocessing scripts take `input_dir` and `output_dir` from the CLI so you can use any structure you like.

### Usage

1. Parse XML to CSV files:
   ```
   python parse_corenlp_xml.py
   ```
2. Split `character.metadata.tsv` by movie ID to enable parallel processing
    ```
    python split_char_metadata.py
    ```
3. Build bags of words for each character in each movie following the methodology of *Learning Latent Personas*.
   ```
   python build_char_word_bags.py
   ```

Total runtime: 15-20 minutes

I (Sam) wrote a Rust version of the XML parser but this is probably fast enough.

--------