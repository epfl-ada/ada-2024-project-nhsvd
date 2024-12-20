from typing import List, Optional

from pydantic import BaseModel
from sqlmodel import Relationship, SQLModel, Field

from api_mining.models.core import MovieBase, Character

class DeathCharacter(Character):
    """Represents a character and their death status."""
    dies: bool

class DeathCharacters(BaseModel):
    """Contains a list of characters and their death statuses."""
    characters: List[DeathCharacter]

class DeathMovie(MovieBase, table=True):
    """Represents a movie with associated characters and their death statuses."""
    characters: Optional[List["DeathCharacterDB"]] = Relationship(
        back_populates="movie",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

class DeathCharacterDB(SQLModel, table=True):
    """Database model for character death information."""
    __tablename__ = "character_deaths"
    id: Optional[int] = Field(default=None, primary_key=True)
    movie_id: str = Field(foreign_key="deathmovie.id", index=True)
    name: str
    dies: bool
    movie: DeathMovie = Relationship(back_populates="characters")
