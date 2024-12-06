from typing import Optional, List
from pathlib import Path
import json

import pandas as pd


SYSTEM_PROMPT = (
    "Given a list of character names and a plot summary, extract the information about character deaths."
)

def get_summary(input_dir: Path, movie_id: str) -> str:
    """Get plot summary for a movie"""
    plot_file = input_dir / f'plot_summaries_{movie_id}.txt'
    return plot_file.read_text().strip()

def get_char_names(input_dir: Path, movie_id: str) -> List[str]:
    """Get character names if available"""
    char_file = input_dir / f'character.metadata_{movie_id}.csv'
    if not char_file.exists():
        return []
    df = pd.read_csv(char_file, usecols=['character_name'])
    return df['character_name'].dropna().astype(str).tolist()

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
