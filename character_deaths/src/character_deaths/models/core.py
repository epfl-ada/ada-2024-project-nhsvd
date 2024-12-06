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

class Character(BaseModel):
    name: str
    dies: bool

class Characters(BaseModel):
    characters: List[Character]

class MovieBase(SQLModel):
    id: str = Field(primary_key=True)
    plot_summary: str
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
    dies: bool
    movie: Movie = Relationship(back_populates="characters")
