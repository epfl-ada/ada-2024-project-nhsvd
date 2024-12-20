from abc import ABC, abstractmethod
from enum import Enum
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Generator, Type, TypeVar, Generic

from pydantic import BaseModel
from sqlmodel import Session, select, create_engine, SQLModel, func

from api_mining.models.core import (
    DatabaseMetadata,
    DataType,
    ProcessingMethod,
    ProcessingStatus,
    MetadataStatus,
    MovieBase,
    Character
)

from api_mining.models.char_deaths import (
    DeathCharacter,
    DeathCharacters,
    DeathCharacterDB,
    DeathMovie
)

from api_mining.models.tropes import (
    TropeCharacter,
    TropeCharacters,
    TropeCharacterDB,
    TropeMovie
)

M = TypeVar('M', bound=MovieBase)
C = TypeVar('C', bound=Character)
CDB = TypeVar('CDB', bound=SQLModel)

class DatabaseHandler(ABC, Generic[M, C, CDB]):
    """Abstract base class for managing database operations for movies and characters."""
    def __init__(self, db_path: Path):
        """Initialize the database handler with the given database path."""
        self.engine = create_engine(f"sqlite:///{db_path}")

        SQLModel.metadata.create_all(
            self.engine, 
            tables=[DatabaseMetadata.__table__, self.Movie.__table__, self.CharacterDB.__table__]
        )

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Provide a session for database operations."""
        session = Session(self.engine)
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @abstractmethod
    def add_character_data(self, movie_id: str, characters: List[C]) -> None:
        """Add character data to the database."""
        pass

    @property
    @abstractmethod
    def Movie(self) -> Type[M]:
        """Movie model for this handler"""
        pass

    @property
    @abstractmethod
    def Character(self) -> Type[C]:
        """Character model for this handler"""
        pass

    @property
    @abstractmethod
    def Characters(self) -> Type[BaseModel]:
        """Characters container model for this handler"""
        pass

    @property
    @abstractmethod
    def CharacterDB(self) -> Type[CDB]:
        """Database Character model for this handler"""
        pass

    @property
    @abstractmethod
    def data_type(self) -> DataType:
        """Data type for this handler"""
        pass

    def add_movie(
        self,
        movie_id: str,
        metadata_status: MetadataStatus,
        status: ProcessingStatus = ProcessingStatus.PENDING,
        method: ProcessingMethod = ProcessingMethod.CHAT,
        token_count: int = 0
    ) -> None:
        """Add a movie to the database."""
        with self.get_session() as session:
            movie = self.Movie(
                id=movie_id, 
                metadata_status=metadata_status,
                processed_status=status,
                processing_method=method,
                token_count=token_count,
                last_updated=datetime.utcnow()
            )
            session.add(movie)

    def get_pending_chat_movies(self, limit: Optional[int] = None) -> List[M]:
        """Retrieve pending movies for chat processing."""
        with self.get_session() as session:
            statement = select(self.Movie).where(
                self.Movie.processed_status == ProcessingStatus.PENDING,
                self.Movie.processing_method == ProcessingMethod.CHAT
            )
            if limit:
                statement = statement.limit(limit)
            return list(session.exec(statement))

    def get_next_chat_movie(self) -> Optional[M]:
        """Retrieve the next movie pending chat processing."""
        with self.get_session() as session:
            statement = select(self.Movie).where(
                self.Movie.processed_status == ProcessingStatus.PENDING,
                self.Movie.processing_method == ProcessingMethod.CHAT
            ).order_by(self.Movie.last_updated).limit(1)
            return session.exec(statement).first()

    def update_movie(
        self, 
        movie_id: str,
        status: Optional[ProcessingStatus] = None,
        method: Optional[ProcessingMethod] = None,
        batch_id: Optional[str] = None,
        batch_index: Optional[int] = None,
        token_count: Optional[int] = None
    ) -> None:
        """Update the details of a movie in the database."""
        with self.get_session() as session:
            movie = session.get(self.Movie, movie_id)
            if not movie:
                raise ValueError(f"Movie {movie_id} not found")

            if status is not None:
                movie.processed_status = status
            if method is not None:
                movie.processing_method = method
                if method == ProcessingMethod.BATCH:
                    if batch_index is None:
                        raise ValueError("Batch index is required for batch processing")
                    movie.batch_index = batch_index
            if batch_id is not None:
                movie.batch_id = batch_id
            if token_count is not None:
                movie.token_count = token_count

            movie.last_updated = datetime.utcnow()

    def update_batch_movies_status(
        self,
        batch_num: int,
        batch_id: str,
        status: ProcessingStatus
    ) -> None:
        """Update the processing status of all movies in a batch."""
        with self.get_session() as session:
            statement = select(self.Movie).where(
                self.Movie.batch_index == batch_num
            )
            movies = session.exec(statement)
            for movie in movies:
                movie.batch_id = batch_id
                movie.processed_status = status
                movie.last_updated = datetime.utcnow()

    def get_batch_count(self) -> int:
        """Get the total number of batches in the database."""
        with self.get_session() as session:
            statement = select(func.max(self.Movie.batch_index))
            result = session.exec(statement).first()
            return result or 0

class DeathsDatabaseHandler(DatabaseHandler[DeathMovie, DeathCharacter, DeathCharacterDB]):
    """Database handler for managing character death information."""
    @property
    def Movie(self) -> Type[DeathMovie]:
        return DeathMovie

    @property
    def Character(self) -> Type[DeathCharacter]:
        return DeathCharacter

    @property
    def Characters(self) -> Type[DeathCharacters]:
        return DeathCharacters

    @property
    def CharacterDB(self) -> Type[DeathCharacterDB]:
        return DeathCharacterDB
    
    @property
    def data_type(self) -> DataType:
        return DataType.DEATHS

    def add_character_data(self, movie_id: str, characters: List[DeathCharacter]) -> None:
        """Add character death data to the database."""
        with self.get_session() as session:
            movie = session.get(self.Movie, movie_id)
            if not movie:
                raise ValueError(f"Movie {movie_id} not found")
            
            for char in characters:
                character_db = DeathCharacterDB(
                    movie_id=movie_id,
                    name=char.name,
                    dies=char.dies
                )
                session.add(character_db)
            
            movie.processed_status = ProcessingStatus.COMPLETED
            movie.last_updated = datetime.utcnow()

class TropesDatabaseHandler(DatabaseHandler[TropeMovie, TropeCharacter, TropeCharacterDB]):
    """Database handler for managing character trope information."""
    @property
    def Movie(self) -> Type[TropeMovie]:
        return TropeMovie

    @property
    def Character(self) -> Type[TropeCharacter]:
        return TropeCharacter

    @property
    def Characters(self) -> Type[TropeCharacters]:
        return TropeCharacters

    @property
    def CharacterDB(self) -> Type[TropeCharacterDB]:
        return TropeCharacterDB
    
    @property
    def data_type(self) -> DataType:
        return DataType.TROPES

    def add_character_data(self, movie_id: str, characters: List[TropeCharacter]) -> None:
        """Add character trope data to the database."""
        with self.get_session() as session:
            movie = session.get(self.Movie, movie_id)
            if not movie:
                raise ValueError(f"Movie {movie_id} not found")
            
            for char in characters:
                character_db = TropeCharacterDB(
                    movie_id=movie_id,
                    name=char.name,
                    trope=char.trope
                )
                session.add(character_db)
            
            movie.processed_status = ProcessingStatus.COMPLETED
            movie.last_updated = datetime.utcnow()

def create_database_handler(db_path: Path) -> DatabaseHandler:
    """Create appropriate database handler based on database metadata"""
    engine = create_engine(f"sqlite:///{db_path}")
    
    with Session(engine) as session:
        metadata = session.get(DatabaseMetadata, "metadata")
        if metadata is None:
            raise ValueError("Database not initialized with a data type")
        
        handlers = {
            DataType.DEATHS: DeathsDatabaseHandler,
            DataType.TROPES: TropesDatabaseHandler
        }
        handler_class = handlers.get(metadata.data_type)
        if not handler_class:
            raise ValueError(f"Unknown data type in database: {metadata.data_type}")
        
        return handler_class(db_path)
