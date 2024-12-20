import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from pathlib import Path
from matplotlib.ticker import MaxNLocator


def plot_popular_genres(df_movies):
    genres_freq = df_movies.genres_list.explode().value_counts().reset_index(name='count')
    genres_freq = genres_freq.sort_values('count', ascending=False)

    print(f"In total we have {len(df_movies)} movies.")
    print(f"Movies are classified into one or multiple genres, out of a total of {len(genres_freq)} genres.")

    threshold=20

    plt.figure(figsize=(20, 12))

    sns.barplot(
        data=genres_freq[:threshold],
        x='genres_list',
        y='count',
        palette='Greys_r'
    )

    plt.title(f'The top {threshold} most frequent genres', pad=20, fontsize=14)
    plt.xlabel('Genre', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.xticks(rotation=45, ha='right')

    for i, v in enumerate(genres_freq[:threshold]['count']):
        plt.text(i, v, f'{v}', ha='center', va='bottom')

    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

    threshold=10
    print(f'\nTop {threshold} most common genres:')
    print(genres_freq.head(threshold).to_string(index=False))


def plot_popular_tropes(df_characters, df_tropes):
    trope_freq = df_characters.dropna(subset=['died']).groupby('trope_id').size().reset_index(name='count')
    trope_freq = trope_freq.sort_values('count', ascending=False)

    print(f"In total we have {trope_freq['count'].sum()} characters whose trope we identified while also knowing if they died in the movie.")
    print(f"Tropes classified into {len(df_tropes)} tropes (1 of them being the \"NO TROPE\" trope).")

    threshold=20

    plt.figure(figsize=(20, 12))

    sns.barplot(
        data=trope_freq[:threshold],
        x='trope_id',
        y='count',
        palette='Greys_r'
    )

    plt.title(f'The top {threshold} most frequent tropes (where we could identify whether or not the character died)', pad=20, fontsize=14)
    plt.xlabel('Trope', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.xticks(rotation=45, ha='right')

    for i, v in enumerate(trope_freq[:threshold]['count']):
        plt.text(i, v, f'{v}', ha='center', va='bottom')

    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

    threshold=10
    print(f'\nTop {threshold} most common tropes:')
    print(trope_freq.head(threshold).to_string(index=False))


def plot_popular_genres_tropes(df_movies, df_characters):
    genres_freq = df_movies.genres_list.explode().value_counts().reset_index(name='count')
    genres_freq = genres_freq.sort_values('count', ascending=False)

    df_trope_genre = pd.merge(df_movies, df_characters, on='wikipedia_movie_id', how='inner')[['trope_id', 'genres_list']].explode('genres_list')
    df_trope_genre = df_trope_genre[df_trope_genre.trope_id != 'NO_TROPE']
    df_trope_genre = df_trope_genre[df_trope_genre.genres_list.isin(genres_freq.head(4).genres_list)]

    fig, axes = plt.subplots(2, 2, figsize=(21, 25))
    axes = axes.flatten()

    dfs = []

    genre_count=4
    threshold=10

    for idx, genre in enumerate(genres_freq.head(genre_count).genres_list):
        genre_tropes = df_trope_genre[df_trope_genre['genres_list'] == genre]
        genre_freq = genre_tropes.groupby('trope_id').size().reset_index(name='count')
        genre_freq = genre_freq.sort_values('count', ascending=False)[:threshold]

        dfs.append(genre_freq)

        sns.barplot(
            data=genre_freq,
            x='count',
            y='trope_id',
            ax=axes[idx],
            palette='Greys_r'
        )
        
        axes[idx].grid(axis='y', linestyle='--', alpha=0.7)
        
        axes[idx].set_title(f'{genre}', pad=10, fontsize=16)
        axes[idx].set_xlabel('Frequency')
        axes[idx].set_ylabel('Tropes')
        
        # Add text on the bars (adjust text position to work with horizontal bars)
        for i, v in enumerate(genre_freq['count']):
            axes[idx].text(v, i, f'{v}', va='center')

    # Add a title for the whole figure
    plt.suptitle(f'Trope distribution in the {genre_count} most frequent genres in the dataset\n({threshold} most common for each genre with NO_TROPE excluded)', 
                fontsize=16, y=1.02)
    plt.tight_layout()
    plt.show()

    for idx, genre in enumerate(genres_freq.head(genre_count).genres_list):
        print(f'\nTop {threshold} most common tropes in {genre}:')
        print(dfs[idx].head(threshold).to_string(index=False))


def plot_tropes_death_rates(df_characters):
    mortality_by_trope = df_characters.groupby('trope_id').agg({
        'died': ['count', 'sum', 'mean']
    }).round(3)
    mortality_by_trope.columns = ['total_characters', 'total_deaths', 'death_rate']

    trope_threshold = 200
    significant_character_mortality = mortality_by_trope[mortality_by_trope['total_characters'] >= trope_threshold]
    significant_character_mortality = significant_character_mortality.sort_values('death_rate', ascending=False)

    shown_number = 10
    top_ = significant_character_mortality.head(shown_number).reset_index()
    bottom_ = significant_character_mortality.tail(shown_number).reset_index()

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

    mean_death_rate = significant_character_mortality['death_rate'].mean()
    plt.axhline(y=mean_death_rate, color='black', linestyle='--', label=f'Mean death rate by character: {mean_death_rate:.3f}')

    all_labels = list(top_['trope_id']) + [''] * 5 + list(bottom_['trope_id'])
    plt.xticks(np.arange(len(all_labels)), all_labels, rotation=45, ha='right')


    for i, v in enumerate(top_['death_rate']):
        plt.text(positions[i], v, f'{v:.3f}', ha='center', va='bottom')    
    for i, v in enumerate(bottom_['death_rate']):
        plt.text(positions[i + shown_number], v, f'{v:.3f}', ha='center', va='bottom')

    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend(title='Category', fontsize=16, title_fontsize=16)
    plt.tight_layout()
    plt.show()

    print(f'\nOverall mortality rate: {mean_death_rate:.3f}')
    print(f'\nTop {shown_number} deadliest character tropes:')
    print(significant_character_mortality.head(shown_number).to_string())
    print(f'\nTop {shown_number} safest character tropes:')
    print(significant_character_mortality.tail(shown_number).to_string())


def plot_genres_death_rates(df_movies, df_characters):
    df_merged = df_characters.merge(df_movies[['wikipedia_movie_id', 'genres_list']], 
                                    on='wikipedia_movie_id')

    df_exploded = df_merged.explode('genres_list')
    mortality_by_genre = df_exploded.groupby('genres_list').agg({
        'died': ['count', 'sum', 'mean']
    }).round(3)
    mortality_by_genre.columns = ['total_characters', 'total_deaths', 'death_rate']

    genre_threshold = 200
    significant_genres_mortality = mortality_by_genre[mortality_by_genre['total_characters'] >= genre_threshold]
    significant_genres_mortality = significant_genres_mortality.sort_values('death_rate', ascending=False)

    shown_number = 10
    top_ = significant_genres_mortality.head(shown_number).reset_index()
    bottom_ = significant_genres_mortality.tail(shown_number).reset_index()

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

    mean_death_rate = significant_genres_mortality['death_rate'].mean()
    plt.axhline(y=mean_death_rate, color='black', linestyle='--', label=f'Mean death rate by genre: {mean_death_rate:.3f}')

    all_labels = list(top_['genres_list']) + [''] * 5 + list(bottom_['genres_list'])
    plt.xticks(np.arange(len(all_labels)), all_labels, rotation=45, ha='right')

    for i, v in enumerate(top_['death_rate']):
        plt.text(positions[i], v, f'{v:.3f}', ha='center', va='bottom')    
    for i, v in enumerate(bottom_['death_rate']):
        plt.text(positions[i + shown_number], v, f'{v:.3f}', ha='center', va='bottom')

    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend(title='Category', fontsize=16, title_fontsize=16)
    plt.tight_layout()
    plt.show()

    print(f'\nOverall mortality rate: {mean_death_rate:.3f}')
    print(f'\nTop {shown_number} deadliest genres:')
    print(significant_genres_mortality.head(shown_number).to_string())
    print(f'\nTop {shown_number} safest genres:')
    print(significant_genres_mortality.tail(shown_number).to_string())


def plot_top_genres_tropes_deaths(df_movies, df_characters):
    df_merged = df_characters.merge(df_movies[['wikipedia_movie_id', 'genres_list']], 
                                    on='wikipedia_movie_id')

    df_exploded = df_merged.explode('genres_list')
    mortality_by_genre = df_exploded.groupby('genres_list').agg({
        'died': ['count', 'sum', 'mean']
    }).round(3)
    mortality_by_genre.columns = ['total_characters', 'total_deaths', 'death_rate']

    genre_threshold = 200
    significant_genres_mortality = mortality_by_genre[mortality_by_genre['total_characters'] >= genre_threshold]
    significant_genres_mortality = significant_genres_mortality.sort_values('death_rate', ascending=False)

    top_deadly_genres = significant_genres_mortality.head(10).index

    fig, axes = plt.subplots(5, 2, figsize=(21, 25), dpi=300)
    axes = axes.flatten()

    for idx, genre in enumerate(top_deadly_genres):
        genre_chars = df_exploded[df_exploded['genres_list'] == genre]
        total_chars = len(genre_chars)

        genre_deaths = df_exploded[
            (df_exploded['genres_list'] == genre) & 
            (df_exploded['died'] == 1.0)
        ]
        
        trope_deaths = genre_deaths['trope_id'].value_counts().head(10)
        
        total_deaths = genre_deaths['trope_id'].count()
        trope_death_pcts = (trope_deaths / total_deaths * 100).round(1)
        
        sns.barplot(
            x=trope_death_pcts.values,
            y=trope_deaths.index,
            ax=axes[idx],
            palette='Reds_r'
        )
        axes[idx].grid(axis='x', linestyle='--', alpha=0.7)
        
        axes[idx].set_title(f'{genre}\nTotals: number of characters = {total_chars}, number of deaths = {total_deaths}', pad=10, fontsize=16)
        axes[idx].set_xlabel('% of deaths in genre')
        axes[idx].set_ylabel('Character Trope')
        
        for i, v in enumerate(trope_death_pcts):
            axes[idx].text(v, i, f'{v}%', va='center')

    plt.suptitle('Top-10 most frequent dying character tropes in deadliest movie genres', 
                fontsize=16, y=1.02)
    plt.tight_layout()
    plt.show()

    print('\nDetailed breakdown of deaths by trope in deadliest movie genres:')
    for genre in top_deadly_genres:
        print(f'\n{genre}:')
        genre_chars = df_exploded[df_exploded['genres_list'] == genre]
        total_chars = len(genre_chars)
        
        genre_deaths = genre_chars[genre_chars['died'] == 1.0]
        
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
    df_actors = df_characters.dropna(subset=['actor_name'])

    mortality_by_actor = df_actors.groupby('actor_name').agg({
        'died': ['count', 'sum', 'mean']
    }).round(3)
    mortality_by_actor.columns = ['total_characters', 'total_deaths', 'death_rate']

    roles_threshold = 20
    significant_actor_mortality = mortality_by_actor[mortality_by_actor['total_characters'] >= roles_threshold]
    significant_actor_mortality = significant_actor_mortality.sort_values('death_rate', ascending=False)

    shown_number = 10
    top_ = significant_actor_mortality.head(shown_number).reset_index()
    bottom_ = significant_actor_mortality.tail(shown_number).reset_index()

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

    mean_death_rate = significant_actor_mortality['death_rate'].mean()
    plt.axhline(y=mean_death_rate, color='black', linestyle='--', 
                label=f'Mean death rate by actor: {mean_death_rate:.3f}')

    all_labels = list(top_['actor_name']) + [''] * 5 + list(bottom_['actor_name'])
    plt.xticks(np.arange(len(all_labels)), all_labels, rotation=45, ha='right')

    for i, v in enumerate(top_['death_rate']):
        plt.text(positions[i], v, f'{v:.3f}', ha='center', va='bottom')    
    for i, v in enumerate(bottom_['death_rate']):
        plt.text(positions[i + shown_number], v, f'{v:.3f}', ha='center', va='bottom')

    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend(title='Category', fontsize=16, title_fontsize=16)
    plt.tight_layout()
    plt.show()

    print(f'\nOverall mortality rate: {mean_death_rate:.3f}')
    print(f'\nTop {shown_number} most dying actors:')
    print(significant_actor_mortality.head(shown_number).to_string())
    print(f'\nTop {shown_number} least dying actors:')
    print(significant_actor_mortality.tail(shown_number).to_string())


def plot_top_actors_tropes_deaths(df_characters):
    df_actors = df_characters.dropna(subset=['actor_name'])

    mortality_by_actor = df_actors.groupby('actor_name').agg({
        'died': ['count', 'sum', 'mean']
    }).round(3)
    mortality_by_actor.columns = ['total_characters', 'total_deaths', 'death_rate']

    roles_threshold = 20
    significant_actor_mortality = mortality_by_actor[mortality_by_actor['total_characters'] >= roles_threshold]
    significant_actor_mortality = significant_actor_mortality.sort_values('death_rate', ascending=False)

    top_dying_actors = significant_actor_mortality.head(10).index

    fig, axes = plt.subplots(5, 2, figsize=(21, 25), dpi=300)
    axes = axes.flatten()

    for idx, actor in enumerate(top_dying_actors):
        actor_chars = df_actors[df_actors['actor_name'] == actor]
        total_chars = len(actor_chars)

        actor_deaths = df_actors[
            (df_actors['actor_name'] == actor) & 
            (df_actors['died'] == 1.0)
        ]
        
        trope_deaths = actor_deaths['trope_id'].value_counts().head(10)
        total_deaths = actor_deaths['trope_id'].count()
        
        sns.barplot(
            x=trope_deaths.values,
            y=trope_deaths.index,
            ax=axes[idx],
            palette='Reds_r'
        )
        axes[idx].grid(axis='x', linestyle='--', alpha=0.7)
        axes[idx].xaxis.set_major_locator(MaxNLocator(integer=True))
        axes[idx].set_title(f'{actor}\nTotals: number of roles = {total_chars}, number of deaths = {total_deaths}', 
                        pad=10, fontsize=16)
        axes[idx].set_xlabel('Number of deaths')
        axes[idx].set_ylabel('Character Trope')

    plt.suptitle(f'The most frequent dying character tropes for actors with highest death rates \n actors with {roles_threshold}+ roles', 
                fontsize=16, y=1.02)
    plt.tight_layout()
    plt.show()

    print('\nDetailed breakdown of deaths by trope for actors with highest death rates:')
    for actor in top_dying_actors:
        print(f'\n{actor}:')
        actor_chars = df_actors[df_actors['actor_name'] == actor]
        total_chars = len(actor_chars)
        
        actor_deaths = actor_chars[actor_chars['died'] == 1.0]
        
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