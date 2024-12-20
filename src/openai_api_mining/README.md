# Character data mining with OpenAI API

A collection of scripts and utilities for extracting character deaths and tropes from plot summaries using OpenAI API structured output via batch and real-time APIs. 

## Installation

```bash
cd openai_api_mining
pip install -e .
```

## Usage

Due to the low rate limit of the OpenAI batch API for usage tier 1, we cannot process the entire dataset (~18M tokens for plot summaries alone) in a single batch.

You can choose one of the following strategies:

1. **Batch-only:** Process the dataset using ~10 batches of ~1.8M tokens (+extra for system prompt and formatting), keeping under the 2M token limit. This is the cheapest option but could take up to 10 days. Our experience is that the batches take substantially less than the completion window of 24h suggests.
2. **Real-time-only:** Process the dataset using the real-time API (500 requests per minute, 10k requests per day). This option costs double compared to option 1 but takes only ~4.2 days for ~42k movies.
3. **Hybrid:** Submit 4 batches of 1.9M tokens each, prioritizing shorter plot summaries (~30k movies). Process the remaining ~12k movies using the real-time API in parallel. This costs ~60% more than option 1 and took ~2 days in testing.

(Numbers for gpt-4o-mini (11-12.2024) processing character deaths. The system prompt is substantially longer for tropes.)

### Initialize database

```bash
api-mining-init-db
```

Arguments:

- `--data-type`: Type of data to store (character deaths or tropes, one DB is designed to be used for only one type of data).
- `--db-path`: Path where the database will be saved.
- `--input-dir`: Path to the directory containing the *split* plot summaries and character metadata (one file per movie, created by `src/preprocessing/split_plot_summaries.py` and `src/preprocessing/split_char_metadata.py`).

### Create batches

```bash
api-mining-create-batches
```

Arguments:

- `--db-path`: Path where the database will be saved.
- `--input-dir`: Path to the directory containing the *split* plot summaries and character metadata.
- `--batch-dir`: Path to the directory to save the batch files and the batch ID log.
- `--num-batches`: Number of batches to create (default: 4).
- `--batch-token-target`: Target number of tokens per batch  (default: 1.9M).

New batches can be created at any time by running `api-mining-create-batches` again with the same or different arguments.


### Submit a batch

```bash
api-mining-submit-batch
```

Arguments:

- `--db-path`: Path to the database file.
- `--batch-num`: The number of the batch to submit (indexed from 1).
- `--batch-dir`: Path to the directory containing the batch files (`--batch-dir` from `api-mining-create-batches`) and the batch ID log.
- `--force`: If the batch is already submitted, submit it again anyway (useful if the batch was cancelled due to rate limiting).

### Retrieve results

```bash
api-mining-retrieve-batch
```

Arguments:

- `--db-path`: Path to the database file.
- `--batch-num`: The number of the batch to retrieve (indexed from 1).
- `--batch-dir`: Path to the directory containing the batch IDs (created by `api-mining-submit-batch`).

### Process movies via real-time API

```bash
api-mining-process-chat
```

Arguments:

- `--db-path`: Path to the database file.
- `--input-dir`: Path to the directory containing the *split* plot summaries and character metadata.