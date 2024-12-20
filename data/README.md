### Data directory structure

The default and assumed structure of data is as follows:
```
├── data
    ├── databases      <- OpenAI databases and intermediate tables.
    |    ├── char_death.db
    |    ├── char_trope.db
    |    └── .csv files version of databases
    ├── final          <- Data used for final analysis.
    |    ├── characters.csv
    |    ├── movies.csv
    |    └── tropes.csv
    ├── interim        <- Intermediate data that has been transformed.
    ├── processed      <- Final data for naive methods.
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

### Building bag-of-words

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

### Building databases mined with OpenAI's API
