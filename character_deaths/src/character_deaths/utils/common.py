from typing import Optional, List
from pathlib import Path
import json
import logging

import pandas as pd

SYSTEM_PROMPT = (
    "Given a list of character names and a plot summary, extract the information about character deaths."
)

def get_plot_summary(input_dir: Path, movie_id: str) -> str:
    """Get plot summary for a movie"""
    try:
        plot_file = input_dir / f'plot_summaries_{movie_id}.txt'
        return plot_file.read_text().strip()
    except Exception as e:
        logging.error(f"Error reading plot summary for {movie_id}: {e}")
        return None

def get_character_names(input_dir: Path, movie_id: str) -> List[str]:
    """Get character names if available"""
    try:
        char_file = input_dir / f'character.metadata_{movie_id}.csv'
        if not char_file.exists():
            return []
        df = pd.read_csv(char_file, usecols=['character_name'])
        return df['character_name'].dropna().astype(str).tolist()
    except Exception as e:
        logging.error(f"Error reading characters for {movie_id}: {e}")
        return None

def construct_user_prompt(plot_summary: str, character_names: Optional[List[str]]) -> str:
    if character_names:
        names_str = ', '.join(character_names)
        return f"<summary>{plot_summary}</summary>\n<names>{names_str}</names>"
    return f"<summary>{plot_summary}</summary>"

def get_batch_ids(output_dir: Path) -> List[Optional[str]]:
    """Read batch IDs from JSON file"""
    batch_file = output_dir / "batch_ids.json"
    if not batch_file.exists():
        return []
    return json.loads(batch_file.read_text())

def save_batch_ids(output_dir: Path, batch_ids: List[Optional[str]]) -> None:
    """Save batch IDs to JSON file"""
    batch_file = output_dir / "batch_ids.json"
    batch_file.write_text(json.dumps(batch_ids))
