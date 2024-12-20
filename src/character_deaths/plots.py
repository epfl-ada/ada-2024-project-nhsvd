import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from pathlib import Path
from matplotlib.ticker import MaxNLocator


def plot_popular_genres(df_movies):
    """
    Plots the most popular genres and print out their counts

    parameters:
    - df_movies: dataframe containing movie data

    displays:
    - bar plots showing the most popular genres
    - counts for the most popular genres
    """
    # calculate the frequency of each genre
    genres_freq = df_movies.genres_list.explode().value_counts().reset_index(name='count')
    genres_freq = genres_freq.sort_values('count', ascending=False)

    print(f"In total we have {len(df_movies)} movies.")
    print(f"Movies are classified into one or multiple genres, out of a total of {len(genres_freq)} genres.")

    # plot the top genres as a bar chart
    threshold = 20
    plt.figure(figsize=(20, 12))
    sns.barplot(data=genres_freq[:threshold], x='genres_list', y='count', palette='Greys_r')
    plt.title(f'The top {threshold} most frequent genres', pad=20, fontsize=14)
    plt.xlabel('Genre', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.xticks(rotation=45, ha='right')

    # annotate bars with values
    for i, v in enumerate(genres_freq[:threshold]['count']):
        plt.text(i, v, f'{v}', ha='center', va='bottom')

    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

    # display the top 10 genres
    threshold = 10
    print(f'\nTop {threshold} most common genres:')
    print(genres_freq.head(threshold).to_string(index=False))


def plot_popular_tropes(df_characters, df_tropes):
    """
    Plots the most frequent character tropes and print out their statistics

    parameters:
    - df_characters: dataframe containing character data with 'trope_id' and 'wikipedia_movie_id'
    - df_tropes: dataframe containing about all possible tropes

    displays:
    - bar plots showing the most popular tropes
    - counts for the most frquent tropes
    """
    # calculate trope frequencies for characters with death info
    trope_freq = df_characters.dropna(subset=['died']).groupby('trope_id').size().reset_index(name='count')
    trope_freq = trope_freq.sort_values('count', ascending=False)

    # print basic statistics
    print(f"In total we have {trope_freq['count'].sum()} characters whose trope we identified while also knowing if they died in the movie.")
    print(f"Tropes classified into {len(df_tropes)} tropes (1 of them being the \"NO TROPE\" trope).")

    # plot the most frequent tropes
    threshold = 20
    plt.figure(figsize=(20, 12))
    sns.barplot(data=trope_freq[:threshold], x='trope_id', y='count', palette='Greys_r')
    plt.title(f'The top {threshold} most frequent tropes (where we could identify whether or not the character died)', pad=20, fontsize=14)
    plt.xlabel('Trope', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.xticks(rotation=45, ha='right')

    # annotate bars with values
    for i, v in enumerate(trope_freq[:threshold]['count']):
        plt.text(i, v, f'{v}', ha='center', va='bottom')

    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

    # display the top 10 tropes
    threshold = 10
    print(f'\nTop {threshold} most common tropes:')
    print(trope_freq.head(threshold).to_string(index=False))



def plot_popular_genres_tropes(df_movies, df_characters):
    """
    plot the distribution of the most common tropes in the top genres.

    this function calculates the frequency of tropes for the top genres
    and generates bar plots for each genre, showing the most frequent tropes.
    
    parameters:
    - df_movies: dataframe containing movie data with a 'genres_list' column
    - df_characters: dataframe containing character data with 'trope_id' and 'wikipedia_movie_id'

    displays:
    - bar plots showing trope distribution for the top genres
    - text output listing the most frequent tropes for each genre
    """

    # calculate genre frequencies
    genres_freq = df_movies.genres_list.explode().value_counts().reset_index(name='count')
    genres_freq = genres_freq.sort_values('count', ascending=False)

    # merge movie and character data to associate tropes with genres
    df_trope_genre = pd.merge(df_movies, df_characters, on='wikipedia_movie_id', how='inner')[
        ['trope_id', 'genres_list']].explode('genres_list')
    df_trope_genre = df_trope_genre[df_trope_genre.trope_id != 'NO_TROPE']  # exclude "no trope"
    df_trope_genre = df_trope_genre[df_trope_genre.genres_list.isin(genres_freq.head(4).genres_list)]

    # create subplots for the top genres
    fig, axes = plt.subplots(2, 2, figsize=(21, 25))
    axes = axes.flatten()

    dfs = []  # store dataframes for later display

    genre_count = 4  # number of genres to include
    threshold = 10  # number of top tropes to show per genre

    # plot tropes for each genre
    for idx, genre in enumerate(genres_freq.head(genre_count).genres_list):
        # filter tropes for the current genre
        genre_tropes = df_trope_genre[df_trope_genre['genres_list'] == genre]
        genre_freq = genre_tropes.groupby('trope_id').size().reset_index(name='count')
        genre_freq = genre_freq.sort_values('count', ascending=False)[:threshold]

        dfs.append(genre_freq)

        # create a bar plot for the genre
        sns.barplot(
            data=genre_freq,
            x='count',
            y='trope_id',
            ax=axes[idx],
            palette='Greys_r'
        )

        # add grid and labels
        axes[idx].grid(axis='y', linestyle='--', alpha=0.7)
        axes[idx].set_title(f'{genre}', pad=10, fontsize=16)
        axes[idx].set_xlabel('Frequency')
        axes[idx].set_ylabel('Tropes')

        # annotate bars with values
        for i, v in enumerate(genre_freq['count']):
            axes[idx].text(v, i, f'{v}', va='center')

    # add a title for the entire plot
    plt.suptitle(
        f'Trope distribution in the {genre_count} most frequent genres in the dataset\n'
        f'({threshold} most common for each genre with NO_TROPE excluded)',
        fontsize=16, y=1.02
    )
    plt.tight_layout()
    plt.show()

    # print the top tropes for each genre
    for idx, genre in enumerate(genres_freq.head(genre_count).genres_list):
        print(f'\nTop {threshold} most common tropes in {genre}:')
        print(dfs[idx].head(threshold).to_string(index=False))


def plot_tropes_death_rates(df_characters):
    """
    plot the death rates of tropes with significant character counts.

    this function calculates the death rate for each trope and identifies the 
    deadliest and safest tropes based on a minimum character threshold. it creates
    a bar plot comparing the top and bottom tropes by death rate.

    parameters:
    - df_characters: dataframe containing character data with 'trope_id' and 'died'

    displays:
    - bar plot comparing the deadliest and safest tropes
    - text output with detailed statistics for the top and bottom tropes
    """

    # calculate total characters, deaths, and death rates for each trope
    mortality_by_trope = df_characters.groupby('trope_id').agg({
        'died': ['count', 'sum', 'mean']
    }).round(3)
    mortality_by_trope.columns = ['total_characters', 'total_deaths', 'death_rate']

    # filter tropes with significant character counts
    trope_threshold = 200
    significant_character_mortality = mortality_by_trope[mortality_by_trope['total_characters'] >= trope_threshold]
    significant_character_mortality = significant_character_mortality.sort_values('death_rate', ascending=False)

    # get the top and bottom tropes by death rate
    shown_number = 10
    top_ = significant_character_mortality.head(shown_number).reset_index()
    bottom_ = significant_character_mortality.tail(shown_number).reset_index()

    # set up the bar plot
    plt.figure(figsize=(20, 10))
    positions = np.concatenate([
        np.arange(shown_number),
        np.arange(shown_number + 5, 2 * shown_number + 5)
    ])
    plt.bar(positions[:shown_number], top_['death_rate'], color='red', label='Deadliest tropes')
    plt.bar(positions[shown_number:], bottom_['death_rate'], color='green', label='Safest tropes')

    plt.title(f'Deadliest vs Safest character tropes \n tropes with {trope_threshold}+ characters', 
              pad=20, fontsize=14)
    plt.xlabel('Trope', fontsize=12)
    plt.ylabel('Death Rate', fontsize=12)

    # plot the mean death rate as a reference line
    mean_death_rate = significant_character_mortality['death_rate'].mean()
    plt.axhline(y=mean_death_rate, color='black', linestyle='--', 
                label=f'Mean death rate by character: {mean_death_rate:.3f}')

    # set x-axis labels with placeholders for spacing
    all_labels = list(top_['trope_id']) + [''] * 5 + list(bottom_['trope_id'])
    plt.xticks(np.arange(len(all_labels)), all_labels, rotation=45, ha='right')

    # annotate bars with death rates
    for i, v in enumerate(top_['death_rate']):
        plt.text(positions[i], v, f'{v:.3f}', ha='center', va='bottom')    
    for i, v in enumerate(bottom_['death_rate']):
        plt.text(positions[i + shown_number], v, f'{v:.3f}', ha='center', va='bottom')

    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend(title='Category', fontsize=16, title_fontsize=16)
    plt.tight_layout()
    plt.show()

    # print summary statistics for the deadliest and safest tropes
    print(f'\nOverall mortality rate: {mean_death_rate:.3f}')
    print(f'\nTop {shown_number} deadliest character tropes:')
    print(significant_character_mortality.head(shown_number).to_string())
    print(f'\nTop {shown_number} safest character tropes:')
    print(significant_character_mortality.tail(shown_number).to_string())



def plot_genres_death_rates(df_movies, df_characters):
    """
    plot the death rates of genres with significant character counts.

    this function calculates the death rate for each genre, filters genres with
    sufficient character counts, and identifies the deadliest and safest genres.
    it creates a bar plot comparing the top and bottom genres by death rate.

    parameters:
    - df_movies: dataframe containing movie data with 'genres_list'
    - df_characters: dataframe containing character data with 'wikipedia_movie_id' and 'died'

    displays:
    - bar plot comparing the deadliest and safest genres
    - text output with detailed statistics for the top and bottom genres
    """

    # merge movies and characters to associate genres with characters
    df_merged = df_characters.merge(df_movies[['wikipedia_movie_id', 'genres_list']], 
                                    on='wikipedia_movie_id')

    # explode genres into separate rows
    df_exploded = df_merged.explode('genres_list')

    # calculate character count, deaths, and death rate for each genre
    mortality_by_genre = df_exploded.groupby('genres_list').agg({
        'died': ['count', 'sum', 'mean']
    }).round(3)
    mortality_by_genre.columns = ['total_characters', 'total_deaths', 'death_rate']

    # filter genres with a significant number of characters
    genre_threshold = 200
    significant_genres_mortality = mortality_by_genre[mortality_by_genre['total_characters'] >= genre_threshold]
    significant_genres_mortality = significant_genres_mortality.sort_values('death_rate', ascending=False)

    # seprate top and bottom genres by death rate
    shown_number = 10
    top_ = significant_genres_mortality.head(shown_number).reset_index()
    bottom_ = significant_genres_mortality.tail(shown_number).reset_index()

    # create a bar plot for deadliest and safest genres
    plt.figure(figsize=(20, 10))
    positions = np.concatenate([
        np.arange(shown_number),
        np.arange(shown_number + 5, 2 * shown_number + 5)
    ])
    plt.bar(positions[:shown_number], top_['death_rate'], color='red', label='Deadliest genres')
    plt.bar(positions[shown_number:], bottom_['death_rate'], color='green', label='Safest genres')

    plt.title(f'Deadliest vs Safest movie genres \n genres with {genre_threshold}+ characters', 
              pad=20, fontsize=14)
    plt.xlabel('Genre', fontsize=12)
    plt.ylabel('Death rate', fontsize=12)

    # plot mean death rate as a reference line
    mean_death_rate = significant_genres_mortality['death_rate'].mean()
    plt.axhline(y=mean_death_rate, color='black', linestyle='--', 
                label=f'Mean death rate by genre: {mean_death_rate:.3f}')

    # set x-axis labels with placeholders for spacing
    all_labels = list(top_['genres_list']) + [''] * 5 + list(bottom_['genres_list'])
    plt.xticks(np.arange(len(all_labels)), all_labels, rotation=45, ha='right')

    # annotate bars with death rates
    for i, v in enumerate(top_['death_rate']):
        plt.text(positions[i], v, f'{v:.3f}', ha='center', va='bottom')    
    for i, v in enumerate(bottom_['death_rate']):
        plt.text(positions[i + shown_number], v, f'{v:.3f}', ha='center', va='bottom')

    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend(title='Category', fontsize=16, title_fontsize=16)
    plt.tight_layout()
    plt.show()

    # print overal mortality rate and details for the top and bottom genres
    print(f'\nOverall mortality rate: {mean_death_rate:.3f}')
    print(f'\nTop {shown_number} deadliest genres:')
    print(significant_genres_mortality.head(shown_number).to_string())
    print(f'\nTop {shown_number} safest genres:')
    print(significant_genres_mortality.tail(shown_number).to_string())


def plot_top_genres_tropes_deaths(df_movies, df_characters):
    """
    plot the top tropes associated with deaths in the deadliest movie genres.

    this function identifies the deadliest genres by death rate and plots the
    most frequent dying character tropes within each genre.

    parameters:
    - df_movies: dataframe containing movie data with 'genres_list'
    - df_characters: dataframe containing character data with 'wikipedia_movie_id' and 'died'

    displays:
    - bar plots for each genre showing the percentage of deaths attributed to top tropes
    - text output with detailed death statistics for tropes in each genre
    """

    # merge movies and characters to associate genres with characters
    df_merged = df_characters.merge(df_movies[['wikipedia_movie_id', 'genres_list']], 
                                    on='wikipedia_movie_id')

    # explode genres into separate rows
    df_exploded = df_merged.explode('genres_list')

    # calculate character count, deaths, and death rate for each genre
    mortality_by_genre = df_exploded.groupby('genres_list').agg({
        'died': ['count', 'sum', 'mean']
    }).round(3)
    mortality_by_genre.columns = ['total_characters', 'total_deaths', 'death_rate']

    # filter genres with a significant number of characters
    genre_threshold = 200
    significant_genres_mortality = mortality_by_genre[mortality_by_genre['total_characters'] >= genre_threshold]
    significant_genres_mortality = significant_genres_mortality.sort_values('death_rate', ascending=False)

    # get the top 10 deadliest genres
    top_deadly_genres = significant_genres_mortality.head(10).index

    # create subplots for each genre
    fig, axes = plt.subplots(5, 2, figsize=(21, 25), dpi=300)
    axes = axes.flatten()

    for idx, genre in enumerate(top_deadly_genres):
        # filter characters in the current genre
        genre_chars = df_exploded[df_exploded['genres_list'] == genre]
        total_chars = len(genre_chars)

        # filter deceased characters in the current genre
        genre_deaths = df_exploded[(df_exploded['genres_list'] == genre) & (df_exploded['died'] == 1.0)]

        # calculate the top dying tropes in the current genre
        trope_deaths = genre_deaths['trope_id'].value_counts().head(10)
        total_deaths = genre_deaths['trope_id'].count()
        trope_death_pcts = (trope_deaths / total_deaths * 100).round(1)

        # create a bar plot for the current genre
        sns.barplot(x=trope_death_pcts.values, y=trope_deaths.index, ax=axes[idx], palette='Reds_r')
        axes[idx].grid(axis='x', linestyle='--', alpha=0.7)
        axes[idx].set_title(
            f'{genre}\nTotals: number of characters = {total_chars}, number of deaths = {total_deaths}', 
            pad=10, fontsize=16
        )
        axes[idx].set_xlabel('% of deaths in genre')
        axes[idx].set_ylabel('Character Trope')

        # annotate bars with death percentages
        for i, v in enumerate(trope_death_pcts):
            axes[idx].text(v, i, f'{v}%', va='center')

    # add a title for the entire figure
    plt.suptitle('Top-10 most frequent dying character tropes in deadliest movie genres', 
                 fontsize=16, y=1.02)
    plt.tight_layout()
    plt.show()

    # print detailed statistics for each genre
    print('\nDetailed breakdown of deaths by trope in deadliest movie genres:')
    for genre in top_deadly_genres:
        print(f'\n{genre}:')
        genre_chars = df_exploded[df_exploded['genres_list'] == genre]
        total_chars = len(genre_chars)
        genre_deaths = genre_chars[genre_chars['died'] == 1.0]

        # calculate detailed trope statistics for the genre
        trope_deaths = genre_deaths['trope_id'].value_counts().head(10)
        total_deaths = genre_deaths['trope_id'].count()
        trope_totals = genre_chars['trope_id'].value_counts()

        stats_df = pd.DataFrame({
            'Total characters': trope_totals[trope_deaths.index],
            'Number of deaths': trope_deaths,
            'Death rate': (trope_deaths / trope_totals[trope_deaths.index] * 100).round(1),
            'Percentage of genre deaths': (trope_deaths / total_deaths * 100).round(1)
        })

        print(f'Totals: number of characters = {total_chars}, number of deaths = {total_deaths}')
        print(stats_df)


def plot_actors_death_rates(df_characters):
    """
    plot the death rates of actors with significant roles.

    this function calculates the death rate for each actor, filters those with
    a sufficient number of roles, and identifies the actors with the highest 
    and lowest death rates. it creates a bar plot comparing the top and bottom actors.

    parameters:
    - df_characters: dataframe containing character data with 'actor_name' and 'died'

    displays:
    - bar plot comparing actors with the highest and lowest death rates
    - text output with detailed statistics for these actors
    """

    # filter out characters without actor names
    df_actors = df_characters.dropna(subset=['actor_name'])

    # calculate total roles, deaths, and death rates for each actor
    mortality_by_actor = df_actors.groupby('actor_name').agg({
        'died': ['count', 'sum', 'mean']
    }).round(3)
    mortality_by_actor.columns = ['total_characters', 'total_deaths', 'death_rate']

    # filter actors with a significant number of roles
    roles_threshold = 20
    significant_actor_mortality = mortality_by_actor[mortality_by_actor['total_characters'] >= roles_threshold]
    significant_actor_mortality = significant_actor_mortality.sort_values('death_rate', ascending=False)

    # separate top and bottom actors by death rate
    shown_number = 10
    top_ = significant_actor_mortality.head(shown_number).reset_index()
    bottom_ = significant_actor_mortality.tail(shown_number).reset_index()

    # create a bar plot for the actors
    plt.figure(figsize=(20, 10))
    positions = np.concatenate([
        np.arange(shown_number),
        np.arange(shown_number + 5, 2 * shown_number + 5)
    ])
    plt.bar(positions[:shown_number], top_['death_rate'], color='red', label='Most dying actors')
    plt.bar(positions[shown_number:], bottom_['death_rate'], color='green', label='Least dying actors')

    plt.title(f'Most vs Least dying actors \n actors with {roles_threshold}+ roles', 
              pad=20, fontsize=14)
    plt.xlabel('Actor', fontsize=12)
    plt.ylabel('Death Rate', fontsize=12)

    # plot mean death rate as a reference line
    mean_death_rate = significant_actor_mortality['death_rate'].mean()
    plt.axhline(y=mean_death_rate, color='black', linestyle='--', 
                label=f'Mean death rate by actor: {mean_death_rate:.3f}')

    # set x-axis labels with placeholders for spacing
    all_labels = list(top_['actor_name']) + [''] * 5 + list(bottom_['actor_name'])
    plt.xticks(np.arange(len(all_labels)), all_labels, rotation=45, ha='right')

    # annotate bars with death rates
    for i, v in enumerate(top_['death_rate']):
        plt.text(positions[i], v, f'{v:.3f}', ha='center', va='bottom')    
    for i, v in enumerate(bottom_['death_rate']):
        plt.text(positions[i + shown_number], v, f'{v:.3f}', ha='center', va='bottom')

    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend(title='Category', fontsize=16, title_fontsize=16)
    plt.tight_layout()
    plt.show()

    # print overall mortality rate and details for the top and bottom actors
    print(f'\nOverall mortality rate: {mean_death_rate:.3f}')
    print(f'\nTop {shown_number} most dying actors:')
    print(significant_actor_mortality.head(shown_number).to_string())
    print(f'\nTop {shown_number} least dying actors:')
    print(significant_actor_mortality.tail(shown_number).to_string())



def plot_top_actors_tropes_deaths(df_characters):
    """
    plot the most frequent dying character tropes for actors with the highest death rates.

    this function identifies the actors with the highest death rates, analyzes their 
    most frequent dying character tropes, and generates bar plots for each actor.

    parameters:
    - df_characters: dataframe containing character data with 'actor_name', 'trope_id', and 'died'

    displays:
    - bar plots for each actor showing their top dying tropes
    - text output with detailed statistics for each actor's tropes and deaths
    """

    # fitler out characters without actor names
    df_actors = df_characters.dropna(subset=['actor_name'])

    # calculate total roles, deaths, and death rates for each actor
    mortality_by_actor = df_actors.groupby('actor_name').agg({
        'died': ['count', 'sum', 'mean']
    }).round(3)
    mortality_by_actor.columns = ['total_characters', 'total_deaths', 'death_rate']

    # filter actros with a significant number of roles
    roles_threshold = 20
    significant_actor_mortality = mortality_by_actor[mortality_by_actor['total_characters'] >= roles_threshold]
    significant_actor_mortality = significant_actor_mortality.sort_values('death_rate', ascending=False)

    # get the top 10 actors with the highest death rates
    top_dying_actors = significant_actor_mortality.head(10).index

    # create subplots for each actor
    fig, axes = plt.subplots(5, 2, figsize=(21, 25), dpi=300)
    axes = axes.flatten()

    for idx, actor in enumerate(top_dying_actors):
        # filter characters for the current actor
        actor_chars = df_actors[df_actors['actor_name'] == actor]
        total_chars = len(actor_chars)

        # filter deceased characters for the current actor
        actor_deaths = df_actors[(df_actors['actor_name'] == actor) & (df_actors['died'] == 1.0)]

        # calculate the top dying tropes for the current actor
        trope_deaths = actor_deaths['trope_id'].value_counts().head(10)
        total_deaths = actor_deaths['trope_id'].count()

        # create a bar plot for the current actor
        sns.barplot(
            x=trope_deaths.values,
            y=trope_deaths.index,
            ax=axes[idx],
            palette='Reds_r'
        )
        axes[idx].grid(axis='x', linestyle='--', alpha=0.7)
        axes[idx].xaxis.set_major_locator(MaxNLocator(integer=True))
        axes[idx].set_title(
            f'{actor}\nTotals: number of roles = {total_chars}, number of deaths = {total_deaths}', 
            pad=10, fontsize=16
        )
        axes[idx].set_xlabel('Number of deaths')
        axes[idx].set_ylabel('Character Trope')

    # add a title for the entire figure
    plt.suptitle(
        f'The most frequent dying character tropes for actors with highest death rates \n actors with {roles_threshold}+ roles', 
        fontsize=16, y=1.02
    )
    plt.tight_layout()
    plt.show()

    # print detailed statistics for each actor
    print('\nDetailed breakdown of deaths by trope for actors with highest death rates:')
    for actor in top_dying_actors:
        print(f'\n{actor}:')
        actor_chars = df_actors[df_actors['actor_name'] == actor]
        total_chars = len(actor_chars)
        actor_deaths = actor_chars[actor_chars['died'] == 1.0]

        # calculate detaied trope statistics for the actor
        trope_deaths = actor_deaths['trope_id'].value_counts().head(10)
        total_deaths = actor_deaths['trope_id'].count()
        trope_totals = actor_chars['trope_id'].value_counts()

        stats_df = pd.DataFrame({
            'Total roles': trope_totals[trope_deaths.index],
            'Number of deaths': trope_deaths,
            'Death rate': (trope_deaths / trope_totals[trope_deaths.index] * 100).round(1),
            'Percentage of actor deaths': (trope_deaths / total_deaths * 100).round(1)
        })

        print(f'Totals: number of roles = {total_chars}, number of deaths = {total_deaths}')
        print(stats_df)
