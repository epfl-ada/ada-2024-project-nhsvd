# CMU Movie Summary Corpus Analysis by NHSVD

### Final Website : https://cinematic-fate-analytics.lovable.app

### Abstract

The goal of this project is to investigate and examine the mortality of movie characters to identify which types (like heroes, villains, mentors) are most prone to dying in films. By employing a mix of text mining methods and statistical evaluation, we will create a "mortality index" that showcases death patterns among character tropes in different film genres. Moreover, we intend to explore whether specific actors, especially those recognized for significant on-screen deaths, maintain a consistently high mortality rate throughout their body of work. This examination will turn tragic on-screen deaths into a lighthearted investigation, uncovering which characters, stereotypes, and performers "perish the most."

## Research Questions

1. Which character types or tropes (e.g., villains, mentors) are most likely to meet their demise in movies?
2. How does character mortality vary across different movie genres, such as action, horror, and drama?
3. Do specific actors, known for high on-screen death rates, have a statistically higher chance of dying in films?
4. Are there additional attributes (such as character age, gender) that correlate with a higher mortality rate?
## Datasets
Our project relies heavily on the following files:
   - `movie.metadata.tsv`: Metadata of movies.
   - `character.metadata.tsv`: Metadata of characters.
   - `plot_summaries.txt`: Plot summaries of the movies.
   - `corenlp_plot_summaries.tar`: The plot summaries run through Stanford CoreNLP pipeline (tagging, parsing, NER and coref).


## Methods
Some methods laid out by the following paper: Bamman, D., O’Connor, B., & Smith, N. A. (2013). Learning latent personas of film characters. Proceedings of the 51st Annual Meeting of the Association for Computational Linguistics (ACL), 352–361.

### 1. Data preprocessing to generate character's bag-of-words:
For each `.xml` in `corenlp_plot_summaries.tar`, we parse the file to extract from Named Entity Recognition (NER) the following:

- Characters mentioned in the summary.
- Agent Verbs: Actions characters perform.
- Patient Verbs: Actions done to characters.

We then attempt to match them with a character in `character.metadata.tsv`. Some characters, like "Two-Face", are mentioned in the summary but do not appear in the metadata table.

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

#### B. LLM:

- Feature: Movie's summary tagged with character mentions
- Approach:
    1. Create plot summary-character list pairs as input.
    2. Use the LLM to output for each character a binary label: dead or alive
- Limitation:
    + LLM API costs.
    + The result's accuracy is dependent on the prompt.

#### C. Decision:

The LLM method demonstrates significantly superior performance.


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
    1. Create plot summary-character list pairs as input
    2. Ask the LLM to choose a trope that best represents each character among the well-established tropes.
- Limitation:
    + Same limitations as the LLM method in previous section
    + Increased complexity in comparison to death classification may reduce reliability of results

#### C. Decision:

The LLM method demonstrates significantly superior performance.

### 4. Mortality Index Calculation
   - We propose calculating a mortality index as the proportion of characters within each trope, genre, or actor’s filmography that die.
   - **Genre-Specific Analysis**: We will examine mortality rates across genres, hypothesizing that certain genres like horror or war may exhibit higher mortality.
   - **Character Tropes and Attributes**: We will investigate if certain character types (e.g., mentors, villains) are more prone to death than others.
   - **Actor-Specific Analysis**: By calculating mortality rates for certain actors, we can identify those with high on-screen death frequencies (e.g., Sean Bean).

## Organization within the Team
- Samuli Näppi: Data preprocessing, creating the OpenAI's API framework, LLM death classification, analysis(10%).
- Vsevolod Malevannyi: Bags-of-word death matching, analysis(40%).
- Duc-Anh Do: LLM trope clustering, organizing meetings, merging code.
- Nizar Ben Mohamed: DPM trope clustering, analysis(%10).
- Hamza Karime: Proposing the project idea, analysis(40%), making the data story.
