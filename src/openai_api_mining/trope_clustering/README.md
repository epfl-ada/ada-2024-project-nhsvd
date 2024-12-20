# Installation

```bash
cd trope_clustering
pip install -e .
```

# Usage

Due to the low rate limit of the OpenAI batch API for usage tier 1, we cannot process the entire dataset (~18M tokens) in a single batch.

We could either:

1. Process the entire dataset using 10 batches of ~1.8M tokens each (under the 2M token limit). This is the cheapest option but could take up to 10 days.
2. Process the entire dataset using the real-time API (500 requests per minute, 10k requests per day). This is double the cost of option 1 and would take 4.2 days (42k movies, 1 request per movie).
3. Submit 4 batches of 1.9M tokens, selecting the shortest plot summaries first. These contain ~30k movies. In parallel, process the remaining ~12k movies using the real time API. This costs 60% more than option 1 and could take up to 4 days, but took around 2 days in our testing.

### Create batches and initialize database

```bash
trope-clustering-create-batches
```

Arguments:

- `--db-path`: Path where the database will be saved.
- `--input-dir`: Path to the directory containing the *split* plot summaries and character metadata (one file per movie, created by `src/preprocessing/split_plot_summaries.py` and `src/preprocessing/split_char_metadata.py`).
- `--batch-dir`: Path to the directory to save the batch files.
- `--num-batches`: Number of batches to create.
- `--batch-token-target`: Target number of tokens per batch.

The default number of batches is 4 and the default batch token target is 1.9 million. 

These numbers were chosen because the OpenAI batch API at usage tier 1 allows at most 2 million tokens to be in the processing queue at any given time for gpt-4o-mini.
Since the completion window is 24 hours (cannot be changed), 4 batches allows the batches to be processed in at most 4 days. 

In reality, the batches completed in less than 12 hours, so 4 batches could be processed in 48 hours. This was a reasonable tradeoff between the increased cost of the real-time API and the time it takes to process the data.

### Process data via real-time API

```bash
trope-clustering-process-chat
```

Arguments:

- `--db-path`: Path to the database file.
- `--input-dir`: Path to the directory containing the *split* plot summaries and character metadata (one file per movie, created by `src/preprocessing/split_plot_summaries.py` and `src/preprocessing/split_char_metadata.py`).