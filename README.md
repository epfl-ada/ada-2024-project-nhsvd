# CMU Movie Summary Corpus Analysis by NHSVD

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

Currently, no additional datasets are required; however, we are considering the potential use of IMDb (Internet Movie Database) or TMDb (The Movie Database) to enrich character and actor profiles. These sources offer extensive movie metadata, including cast information, plot details, and character descriptions, which could further enhance our analysis. If we integrate data from these sources, we will ensure it aligns in format and structure with the existing datasets to facilitate seamless analysis.


## Methods
We follow the methods layed out by the following paper: Bamman, D., O’Connor, B., & Smith, N. A. (2013). Learning latent personas of film characters. Proceedings of the 51st Annual Meeting of the Association for Computational Linguistics (ACL), 352–361.

### 1. Data preprocessing to generate character's bag-of-words:
For each `.xml` file in `corenlp_plot_summaries.tar`, we parse the file to generate the following:

- Characters mentioned in the summary.
- Agent Verbs: Actions characters perform.
- Patient Verbs: Actions done to characters.

We then attempt to match them with a character in `character.metadata.tsv`. Some characters like "Two-Faced" is mentioned in the summary but does not appear in the metadata table.

The preprocessing is documented in `data/preprocessing.md`. An example is given in `data/corenlp_example.md`.

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

This complete method is presented in `notebooks/bags_analysis.ipynb`.

#### B. LLM:

- Feature: Movie's summary tagged with character mentions
- Approach:
    1. Create document-character pairs as input.
    2. Use the LLM to associate the pair with a binary label: dead or alive.
- Limitation:
    + LLM API costs.
    + The result's accuracy is dependent on the prompt.

This partially completed method is presented in `notebooks/extract_char_deaths_with_llm.ipynb`.

### 3. Creating complete tropes clusters
`tvtropes.clusters.txt` is only an incomplete test file with extremely limited sample size. Therefore, we intend to perform our own tropes clustering using one of the methods below.

#### A. Dirichlet Persona Model (DPM):

This is the original model used to generate `tvtropes.clusters.txt` proposed in the paper mentioned above. It is a latent variable model based on Latent Dirichlet Allocation (LDA)

- Feature: The character's bag-of-words
- Approach: 
    1. Associates each character with a latent persona using DPM.
    2. Soften the persona clusters to extract latent topics.
- Limitation:
    + Manual alignment with well-established tropes is required.
    + Loss of structure as movie's summary is treated as a bag-of-words.
        
#### B. LLM:

Another way to tackle this problem is simply using a LLM to decide the tropes.

- Feature: Movie's summary tagged with character mentions
- Approach: 
    1. Create document-character pairs as input.
    2. Use the LLM to associate the pair with a trope label among the well-established tropes.
- Limitation: Same limitations as the LLM method in previous section

### 4. Mortality Index Calculation
   - We propose calculating a mortality index as the proportion of characters within each trope, genre, or actor’s filmography that die.
   - **Genre-Specific Analysis**: We will examine mortality rates across genres, hypothesizing that certain genres like horror or war may exhibit higher mortality.
   - **Character Tropes and Attributes**: We will investigate if certain character types (e.g., mentors, villains) are more prone to death than others.
   - **Actor-Specific Analysis**: By calculating mortality rates for certain actors, we can identify those with high on-screen death frequencies (e.g., Sean Bean).

## Proposed Timeline

1. **1->15th November**: Data preprocessing and initial analysis.
2. **15->30th Nobember**: Homework 2, tropes clustering and death classification.
3. **1 ->10th December**: Finalize analysis and begin creating visualizations.
4. **10->20th December**: Review results, refine documentation and presentation.

## Organization within the Team
Each team member has an assigned role to ensure efficient progress:
   - Samuli Näppi: Data preprocessing and code reviewing.
   - Vsevolod Malevannyi: Character death classification.
   - Duc-Anh Do: Tropes clustering and team coordinating.
   - Hamza Karime & Nizar Ben Mohamed: Analysis, visualization and presentation.

## Questions for TAs
   - How can we quantify the errors of death classification?
   - Are we on the right track with our mortality index calculation approach, or would you suggest additional considerations for calculating mortality rates by actor and trope?
