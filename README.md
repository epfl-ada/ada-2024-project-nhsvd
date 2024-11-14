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
all the preprocessing scripts take `input_dir` and `output_dir` from the CLI.

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
A member(Samuli Näppi) wrote a faster Rust version of the XML parser.

--------

### Abstract

The goal of this project is to investigate and examine the mortality of movie characters to identify which types (like heroes, villains, mentors) are most prone to dying in films. By employing a mix of text mining methods and statistical evaluation, we will create a "mortality index" that showcases death patterns among character tropes in different film genres. Moreover, we intend to explore whether specific actors, especially those recognized for significant on-screen deaths, maintain a consistently high mortality rate throughout their body of work. This examination will turn tragic on-screen deaths into a lighthearted investigation, uncovering which characters, stereotypes, and performers "perish the most."

## Research Questions

1. Which character types or tropes (e.g., villains, mentors) are most likely to meet their demise in movies?
2. How does character mortality vary across different movie genres, such as action, horror, and drama?
3. Do specific actors, known for high on-screen death rates, have a statistically higher chance of dying in films?
4. Are there additional attributes (such as character age, gender) that correlate with a higher mortality rate?
## Datasets
At this stage, we are focusing on the datasets provided:
   - `movie.metadata.tsv`: Metadata of movies.
   - `character.metadata.tsv`: Metadata of characters.
   - `plot_summaries.txt`: Plot summaries of the movies.
   - `corenlp_plot_summaries.tar`: The plot summaries run through Stanford CoreNLP pipeline (tagging, parsing, NER and coref).

Currently, no additional datasets are required; however, we may consider further resources if necessary to enhance character or actor profiles. We will ensure that any additional data aligns in format and structure with the existing datasets to facilitate analysis.

## Methods
### 1. Data preprocessing to generate character's bag-of-words:
For each `.xml` file in `corenlp_plot_summaries.tar`, we parse the file to generate the following:

- Characters mentioned in the summary.
- Agent Verbs: Actions characters perform.
- Patient Verbs: Actions done to characters.

We then attempt to match them with a character in `character.metadata.tsv`. Some characters like "Two-Faced" appear in the summary but not in the metadata table.

The preprocessing is documented at the start of this `README.md`.

### 2. Determining which characters died
To classify whether a given character has died, we implemented the two methods below.

#### A. Bag-of-words matching:

- Feature: The character's bag-of-words
- Approach:
    1. Check if the character's Agent Verbs contain: died, perished, ...
    2. Check if the character's Patient Verbs contain: killed, assassinated, ...
- Limitation: The model is incapable of accounting for language nuances
    + One summary contained the following "Two-Face then attacks the party and nearly kills Batman".
    + Batman is considered dead since the model can not differentiate between "nearly kills" and "kills".

This complete method is presented in `bags_analysis.ipynb`.

#### B. LLM:

- Feature: Movie's summary tagged with character mentions
- Approach:
    1. Create document-character pairs as input.
    2. Use the LLM associates the pair with a binary label: dead or alive.
- Limitation:
    1. LLM API costs.
    2. The result's accuracy is dependent on the prompt.

This partially completed method is presented in `extract_char_deaths_with_llm.ipynb`.

### 3. Creating complete tropes clusters
`tvtropes.clusters.txt` is only an incomplete test file with extremely limited sample size. Therefore, we intend to perform our own tropes clustering using one of the methods below.

#### A. Dirichlet Persona Model (DPM):

This is the original model used to generate `tvtropes.clusters.txt` proposed by Bamman, O’Connor, & Smith in their paper: "Learning latent personas of film characters". It is a latent variable model based on Latent Dirichlet Allocation (LDA)

- Feature: The character's bag-of-words
- Approach: 
    1. Associates each character with a latent persona using DPM.
    2. Soften the persona clusters to extract latent topics.
- Limitation:
    1. Manual alignment with well-established tropes is required.
    2. Loss of structure as movie's summary is treated as a bag-of-words.
        
#### B. LLM:

Another way to tackle this problem is simply using a LLM to decide the tropes.

- Feature: Movie's summary tagged with character mentions
- Approach: 
    1. Create document-character pairs as input.
    2. Use the LLM associates the pair with a trope label among the well-established tropes.
- Limitation: Same limitations as the LLM method in previous section

### 4. Mortality Index Calculation
   - We propose calculating a mortality index as the proportion of characters within each trope, genre, or actor’s filmography that die.
   - **Genre-Specific Analysis**: We will examine mortality rates across genres, hypothesizing that certain genres like horror or war may exhibit higher mortality.
   - **Character Tropes and Attributes**: We will investigate if certain character types (e.g., mentors, villains) are more prone to death than others.
   - **Actor-Specific Analysis**: By calculating mortality rates for certain actors, we can identify those with high on-screen death frequencies (e.g., Sean Bean).

## Proposed Timeline

1. **1->15th November**: Data preprocessing and initial analysis.
2. **15->30th Nobember**: Homework 2 and tropes clustering.
3. **1 ->10th December**: Finalize analysis and begin creating visualizations.
4. **10->20th December**: Review results, refine documentation and presentation.

## Organization within the Team
Each team member has an assigned role to ensure efficient progress:
   - Samuli Näppi: Data preprocessing and code reviewing.
   - Vsevolod Malevannyi: Character death classifcation.
   - Duc-Anh Do: Tropes clustering and team coordinating.
   - Hamza Karime & Nizar Ben Mohamed: Analysis, visualization and presentation.

## Questions for TAs
   - How can we handle and quantify the errors of dead classification?
   - Are we on the right track with our mortality index calculation approach, or would you suggest additional considerations for calculating mortality rates by actor and trope?
