from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ProcessingMethod(str, Enum):
    BATCH = "batch"
    CHAT = "chat"

class MetadataStatus(str, Enum):
    COMPLETE = "complete"
    MISSING_METADATA = "missing_metadata"
    EMPTY_CHARACTERS = "empty_characters"

class Trope(str, Enum):
    CHOSEN_ONE = "Chosen One"
    RELUCTANT_HERO = "Reluctant Hero"
    ANTIHERO = "Antihero"
    MENTOR = "Mentor"
    COMIC_RELIEF = "Comic Relief"
    FEMME_FATALE = "Femme Fatale"
    BROODING_LONER = "Brooding Loner"
    INGENUE = "Ingenue"
    EVIL_OVERLORD = "Evil Overlord"
    LOVABLE_ROGUE = "Lovable Rogue"
    SIDEKICK = "Sidekick"
    MAD_SCIENTIST = "Mad Scientist"
    TRAGIC_HERO = "Tragic Hero"
    EVERYMAN = "Everyman"
    JADED_VETERAN = "Jaded Veteran"
    NOBLE_SAVAGE = "Noble Savage"
    DAMSEL_IN_DISTRESS = "Damsel in Distress"
    BYRONIC_HERO = "Byronic Hero"
    ETERNAL_OPTIMIST = "Eternal Optimist"
    CYNICAL_REALIST = "Cynical Realist"
    UNDERDOG = "Underdog"
    CLASS_CLOWN = "Class Clown"
    VILLAIN_WITH_A_HEART = "Villain with a Heart"
    WARRIOR_POET = "Warrior Poet"
    REBEL_LEADER = "Rebel Leader"
    PROTECTIVE_PARENT = "Protective Parent"
    SCHEMING_MANIPULATOR = "Scheming Manipulator"
    INNOCENT_CHILD = "Innocent Child"
    LOYAL_BUTLER = "Loyal Butler"
    BRASH_ROOKIE = "Brash Rookie"
    OVERBEARING_BOSS = "Overbearing Boss"
    COWARDLY_LION = "Cowardly Lion"
    TORTURED_ARTIST = "Tortured Artist"
    GOLDEN_BOY_GIRL = "Golden Boy/Girl"
    SEDUCTIVE_VILLAIN = "Seductive Villain"
    TECH_GENIUS = "Tech Genius"
    WILD_CARD = "Wild Card"
    CRUSADER = "Crusader"
    REFORMED_CRIMINAL = "Reformed Criminal"
    ECCENTRIC_MILLIONAIRE = "Eccentric Millionaire"
    TRICKSTER = "Trickster"
    DUTIFUL_SOLDIER = "Dutiful Soldier"
    GENTLE_GIANT = "Gentle Giant"
    OUTCAST = "Outcast"
    VENGEFUL_SPIRIT = "Vengeful Spirit"
    OBSESSIVE_DETECTIVE = "Obsessive Detective"
    HAPPY_GO_LUCKY_ADVENTURER = "Happy-Go-Lucky Adventurer"
    SCHEMER = "Schemer"
    MENTOR_TURNED_VILLAIN = "Mentor Turned Villain"
    HOT_HEADED_FIGHTER = "Hot-Headed Fighter"
    RELUCTANT_ROYAL = "Reluctant Royal"
    BLIND_SEER = "Blind Seer"
    TRAGIC_LOVER = "Tragic Lover"
    STOIC_WARRIOR = "Stoic Warrior"
    CAREFREE_DRIFTER = "Carefree Drifter"
    QUIRKY_NEIGHBOR = "Quirky Neighbor"
    SOCIAL_CLIMBER = "Social Climber"
    DEVOUT_BELIEVER = "Devout Believer"
    UNSCRUPULOUS_BUSINESSPERSON = "Unscrupulous Businessperson"
    QUIET_GENIUS = "Quiet Genius"
    BATTLE_HARDENED_LEADER = "Battle-Hardened Leader"
    OVERCONFIDENT_ROOKIE = "Overconfident Rookie"
    MISUNDERSTOOD_MONSTER = "Misunderstood Monster"
    CUNNING_SURVIVOR = "Cunning Survivor"
    ROMANTIC_DREAMER = "Romantic Dreamer"
    CHARISMATIC_CULT_LEADER = "Charismatic Cult Leader"
    HARDBOILED_DETECTIVE = "Hardboiled Detective"
    NURTURING_HEALER = "Nurturing Healer"
    VISIONARY_INVENTOR = "Visionary Inventor"
    RESERVED_SCHOLAR = "Reserved Scholar"
    VAIN_NARCISSIST = "Vain Narcissist"
    ELDER_STATESMAN = "Elder Statesman"
    BUMBLING_FOOL = "Bumbling Fool"
    SARCASTIC_SNARKER = "Sarcastic Snarker"
    HEROIC_SACRIFICE = "Heroic Sacrifice"
    IDEALISTIC_YOUTH = "Idealistic Youth"
    CALCULATING_STRATEGIST = "Calculating Strategist"
    PARANOID_CONSPIRACY_THEORIST = "Paranoid Conspiracy Theorist"
    STRONG_SILENT_TYPE = "Strong Silent Type"
    HOPELESS_ROMANTIC = "Hopeless Romantic"
    MANIPULATIVE_POLITICIAN = "Manipulative Politician"
    DARK_MESSIAH = "Dark Messiah"
    WILD_CHILD = "Wild Child"
    UNASSUMING_HERO = "Unassuming Hero"
    SINISTER_BUTLER = "Sinister Butler"
    THRILL_SEEKING_DAREDEVIL = "Thrill-Seeking Daredevil"
    STARRY_EYED_PRODIGY = "Starry-Eyed Prodigy"
    BITTER_RIVAL = "Bitter Rival"
    LOST_SOUL = "Lost Soul"
    PEACEFUL_PACIFIST = "Peaceful Pacifist"
    OBSESSED_FAN = "Obsessed Fan"
    MANIPULATIVE_LOVER = "Manipulative Lover"
    GUARDIAN_ANGEL = "Guardian Angel"
    ABSENT_MINDED_PROFESSOR = "Absent-Minded Professor"
    BEAST_WITHIN = "Beast Within"
    CHARMER = "Charmer"
    WISE_ELDER = "Wise Elder"
    DREAMER = "Dreamer"
    NO_TROPE = "No Trope"

class Character(BaseModel):
    name: str
    trope: Trope

class Characters(BaseModel):
    characters: List[Character]

class MovieBase(SQLModel):
    id: str = Field(primary_key=True)
    metadata_status: MetadataStatus
    processed_status: ProcessingStatus = Field(default=ProcessingStatus.PENDING)
    processing_method: Optional[ProcessingMethod] = None
    batch_id: Optional[str] = None
    batch_index: Optional[int] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class Movie(MovieBase, table=True):
    characters: Optional[List["CharacterDB"]] = Relationship(
        back_populates="movie",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

class CharacterDB(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    movie_id: str = Field(foreign_key="movie.id", index=True)
    name: str
    trope: Trope
    movie: Movie = Relationship(back_populates="characters")
