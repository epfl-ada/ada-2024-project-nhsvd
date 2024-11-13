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

### Abstract

The goal of this project is to investigate and examine the mortality of movie characters to identify which types (like heroes, villains, mentors) are most prone to dying in films. By employing a mix of text mining methods and statistical evaluation, we will create a "mortality index" that showcases death patterns among character tropes in different film genres. Moreover, we intend to explore whether specific actors, especially those recognized for significant on-screen deaths, maintain a consistently high mortality rate throughout their body of work. This examination will turn tragic on-screen deaths into a lighthearted investigation, uncovering which characters, stereotypes, and performers "perish the most."

## Research Questions

1. Which character types or tropes (e.g., villains, mentors) are most likely to meet their demise in movies?
2. How does character mortality vary across different movie genres, such as action, horror, and drama?
3. Do specific actors, known for high on-screen death rates, have a statistically higher chance of dying in films?
4. Are there additional attributes (such as character age, gender) that correlate with a higher mortality rate?
## Proposed Additional Datasets
At this stage, we are focusing on the datasets provided:
   - `movie.metadata.tsv`: Metadata for movies, including genres, release dates, and runtime.
   - `character.metadata.tsv`: Information on movie characters and their associated metadata, including actor details and character descriptions.
   - `tvtropes.clusters.txt`: Character trope classifications, which allow us to associate characters with specific types (e.g., heroes, villains).

Currently, no additional datasets are required; however, we may consider further resources if necessary to enhance character or actor profiles. We will ensure that any additional data aligns in format and structure with the existing datasets to facilitate analysis.

## Methods

### Data Preprocessing
Our initial examination of the data revealed the following:
   - The plot summaries contain HTML tags, references, and unclosed or mismatched tags that may interfere with text mining.
   - Some summaries are not actual descriptions of plot events but rather cast lists, reviews, or descriptions with irrelevant information. We will need to filter these out or preprocess them to retain meaningful text.
   - We plan to implement regular expressions and NLP libraries to remove extraneous characters and identify summaries that do not describe plot events.

### Death Term Extraction
   - **Death-Related Keywords**: We developed a comprehensive list of death-related keywords (e.g., "die," "kill," "murder") and phrases (e.g., "pass away," "meet their end") to identify character mortality in plot summaries.
   - **Text Mining Approach**: Using spaCy and its PhraseMatcher tool, we detect phrases and terms related to death. We also account for negations (e.g., "did not die") to prevent false positives in death detection.
   - **Initial Results**: In our initial analysis, we identified that out of a subset of movies, 21,452 summaries contained death terms or phrases, while 20,851 did not. These results indicate that about half of the summaries involve character death, suggesting a sufficient amount of data for mortality analysis.

### DUUUUUUUUUUUUC

### Mortality Index Calculation
   - We propose calculating a mortality index as the proportion of characters within each trope, genre, or actor’s filmography that die.
   - **Genre-Specific Analysis**: We will examine mortality rates across genres, hypothesizing that certain genres like horror or war may exhibit higher mortality.
   - **Character Tropes and Attributes**: We will investigate if certain character types (e.g., mentors, villains) are more prone to death than others.
   - **Actor-Specific Analysis**: By calculating mortality rates for certain actors, we can identify those with high on-screen death frequencies (e.g., Sean Bean).

## Proposed Timeline

1. **1->15th November**: Data preprocessing and initial analysis (cleaning summaries, identifying and filtering irrelevant text).
2. **15->30th Nobember**: Implement text mining for mortality detection; calculate initial mortality rates by trope and genre.
3. **1 ->10th December**: Finalize in-depth analysis and begin creating visualizations.
4. **10->20th December**: Review results, prepare final presentation, and refine documentation.

## Organization within the Team
Each team member has an assigned role to ensure efficient progress:
   - **Project Manager**: Oversees task assignments, progress tracking, and ensures deadlines are met.
   - **Data Collection & Preparation Specialist**: Manages data loading, cleaning, and merging across files.
   - **NLP/Text Mining Specialist**: Develops functions for mortality detection, including keyword and phrase matching.
   - **Data Analysis & Mortality Index Calculation**: Calculates and analyzes mortality rates by genre, trope, and actor.
   - **Visualization & Presentation Specialist**: Creates visual representations of findings and structures the final presentation.

## Initial Questions for TAs
```
Our current methodology reveals some limitations in accurately detecting character deaths due to the complexity of natural language nuances and metadata inconsistencies:

False Positive Detection: In a sentence like “Two-Face then attacks the party and nearly kills Batman,” the term “kills” is identified by our model as an indication of death. However, it cannot distinguish between “nearly kills” and “kills,” resulting in a false positive where Batman is inaccurately classified as deceased.
Missed Detection Due to Metadata Limitations: Conversely, the only actual character death in this movie—Two-Face—is not detected because the name “Two-Face” does not appear in the character metadata for this film. This discrepancy between plot text and metadata leads to a failure to identify genuine character deaths.
```
   - How can we handle and quanitify  errors like this ?
   - Are there any recommended approaches for efficiently filtering non-relevant summaries (e.g., cast lists, reviews)?
   - Are we on the right track with our mortality index calculation approach, or would you suggest additional considerations for calculating mortality rates by actor and trope?
