from typing import Optional, List
from pathlib import Path
import json

import pandas as pd


SYSTEM_PROMPT = (
"""<tropes>
Chosen One: A character destined for greatness, often with a unique power or lineage.
Reluctant Hero: Someone forced into heroism despite their initial hesitation.
Antihero: A protagonist with questionable morals or unconventional methods.
Mentor: A wise figure who guides the hero, often older and experienced.
Comic Relief: Provides humor to lighten the story's tone.
Femme Fatale: A seductive and mysterious woman who leads others into danger.
Brooding Loner: A solitary character, often with a tragic past.
Ingenue: A naive and innocent character, often young.
Evil Overlord: A powerful antagonist with ambitions of domination.
Lovable Rogue: A charming, morally ambiguous character with a heart of gold.
Sidekick: A loyal companion who supports the hero.
Mad Scientist: An eccentric genius with dangerous experiments.
Tragic Hero: A noble character doomed by a fatal flaw.
Everyman: A relatable, ordinary character thrust into extraordinary situations.
Jaded Veteran: A battle-weary character who’s seen too much.
Noble Savage: A character untarnished by civilization, with a pure moral compass.
Damsel in Distress: A character needing rescue, traditionally a woman.
Byronic Hero: Dark, charismatic, and deeply flawed.
Eternal Optimist: Always positive, no matter how dire the situation.
Cynical Realist: A pragmatist who often clashes with idealists.
Underdog: Overcomes great odds despite being underestimated.
Class Clown: Makes jokes to hide insecurities or defuse tension.
Villain with a Heart: An antagonist with redeeming qualities.
Warrior Poet: Combines physical prowess with intellectual depth.
Rebel Leader: Fights against oppressive systems or regimes.
Protective Parent: Driven by love for their child.
Scheming Manipulator: A master of deception and plotting.
Innocent Child: A beacon of purity and hope.
Loyal Butler: A steadfast servant with hidden wisdom or skills.
Brash Rookie: Overconfident but inexperienced.
Overbearing Boss: Demanding, often humorous authority figure.
Cowardly Lion: Afraid of danger but capable of bravery.
Tortured Artist: Fueled by inner turmoil to create masterpieces.
Golden Boy/Girl: Excels at everything and loved by all.
Seductive Villain: Uses allure to achieve nefarious goals.
Tech Genius: Solves problems with technological savvy.
Wild Card: Unpredictable, with motives and actions that keep everyone guessing.
Crusader: Fights tirelessly for a cause they believe in.
Reformed Criminal: A former villain seeking redemption.
Eccentric Millionaire: Wealthy and unconventional.
Trickster: Loves causing chaos, often to teach lessons or reveal truths.
Dutiful Soldier: Obeys orders and adheres to strict codes of conduct.
Gentle Giant: Big and intimidating, but kind and tender-hearted.
Outcast: Shunned by society but finds strength in their uniqueness.
Vengeful Spirit: Motivated by revenge for a wrong done to them.
Obsessive Detective: Relentless in pursuit of justice or the truth.
Happy-Go-Lucky Adventurer: Lives for the thrill of the journey.
Schemer: Always plotting, often for personal gain.
Mentor Turned Villain: A guide who becomes corrupted or misguided.
Hot-Headed Fighter: Quick to anger and action, often impulsive.
Reluctant Royal: A noble figure who doesn't want their throne.
Blind Seer: A character who lacks sight but sees beyond the physical world.
Tragic Lover: Doomed to heartbreak or loss in romance.
Stoic Warrior: Emotionally reserved but incredibly dependable.
Carefree Drifter: A wanderer with no ties, living in the moment.
Quirky Neighbor: An odd but endearing presence in the protagonist’s life.
Social Climber: Obsessed with status and willing to do anything to achieve it.
Devout Believer: Motivated by faith or ideology.
Unscrupulous Businessperson: Greedy and willing to cross any line for profit.
Quiet Genius: Underestimated due to their reserved nature.
Battle-Hardened Leader: Commands respect through their experience.
Overconfident Rookie: Bold but often naive.
Misunderstood Monster: Feared due to appearance or abilities, but kind at heart.
Cunning Survivor: Does whatever it takes to stay alive.
Romantic Dreamer: Longs for love and beauty in the world.
Charismatic Cult Leader: Inspires fanatic devotion.
Hardboiled Detective: Cynical, street-smart investigator.
Nurturing Healer: Devoted to caring for others.
Visionary Inventor: Dreams big, often ahead of their time.
Reserved Scholar: A thinker, not a fighter.
Vain Narcissist: Obsessed with their own appearance and status.
Elder Statesman: Wise, respected, and often a peacemaker.
Bumbling Fool: Always making mistakes but with a good heart.
Sarcastic Snarker: Quick-witted with biting humor.
Heroic Sacrifice: Gives their life for the greater good.
Idealistic Youth: Sees the world as it could be, not as it is.
Calculating Strategist: Always thinking several steps ahead.
Paranoid Conspiracy Theorist: Sees hidden plots everywhere.
Strong Silent Type: Speaks little but acts decisively.
Hopeless Romantic: Constantly seeking love, often to their detriment.
Manipulative Politician: Skilled at bending people to their will.
Dark Messiah: A savior figure with questionable methods or morals.
Wild Child: Untamed, free-spirited, and unpredictable.
Unassuming Hero: An ordinary person who rises to extraordinary circumstances.
Sinister Butler: A servant with hidden motives or a dark past.
Thrill-Seeking Daredevil: Lives for danger and excitement.
Starry-Eyed Prodigy: Talented and ambitious but inexperienced.
Bitter Rival: Obsessed with outdoing or defeating the protagonist.
Lost Soul: Searching for meaning, often plagued by inner demons.
Peaceful Pacifist: Avoids violence at all costs.
Obsessed Fan: Takes admiration to dangerous extremes.
Manipulative Lover: Uses romance as a tool for control.
Guardian Angel: Protects others, often at great personal cost.
Absent-Minded Professor: Brilliant but scatterbrained.
Beast Within: Struggles to control a literal or metaphorical monster inside.
Charmer: Wins others over with wit and charisma.
Wise Elder: A sage figure, often dispensing advice in riddles.
Dreamer: Lives in their imagination, often disconnected from reality.
No Trope: A character that doesn't align with any of the tropes above or not enough information.
</tropes>
<task>Given a plot summary (and a list of character names), assign a trope from the ones above to each character."</task>"""
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
