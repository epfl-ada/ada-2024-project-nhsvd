from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Generator

from sqlmodel import Session, select, create_engine, SQLModel, func

from character_deaths.models import (
    Movie, 
    CharacterDB, 
    ProcessingStatus, 
    ProcessingMethod, 
    Character, 
    MetadataStatus
)

class DatabaseHandler:
    def __init__(self, db_path: Path):
        self.engine = create_engine(f"sqlite:///{db_path}")
        SQLModel.metadata.create_all(self.engine)

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        session = Session(self.engine)
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def add_movie(
        self,
        movie_id: str,
        metadata_status: MetadataStatus,
        status: ProcessingStatus = ProcessingStatus.PENDING,
        method: ProcessingMethod = ProcessingMethod.CHAT,
        token_count: int = 0
    ) -> None:
        with self.get_session() as session:
            movie = Movie(
                id=movie_id, 
                metadata_status=metadata_status,
                processed_status=status,
                processing_method=method,
                token_count=token_count,
                last_updated=datetime.utcnow()
            )
            session.add(movie)

    def add_character_deaths(self, movie_id: str, characters: List[Character]) -> None:
        with self.get_session() as session:
            movie = session.get(Movie, movie_id)
            if not movie:
                raise ValueError(f"Movie {movie_id} not found")
            
            for char in characters:
                character_db = CharacterDB(
                    movie_id=movie_id,
                    name=char.name,
                    dies=char.dies
                )
                session.add(character_db)
            
            movie.processed_status = ProcessingStatus.COMPLETED
            movie.last_updated = datetime.utcnow()

    def get_pending_chat_movies(self, limit: Optional[int] = None) -> List[Movie]:
        with self.get_session() as session:
            statement = select(Movie).where(
                Movie.processed_status == ProcessingStatus.PENDING,
                Movie.processing_method == ProcessingMethod.CHAT
            )
            if limit:
                statement = statement.limit(limit)
            return list(session.exec(statement))

    def get_next_chat_movie(self) -> Optional[Movie]:
        with self.get_session() as session:
            statement = select(Movie).where(
                Movie.processed_status == ProcessingStatus.PENDING,
                Movie.processing_method == ProcessingMethod.CHAT
            ).order_by(Movie.last_updated).limit(1)
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
        with self.get_session() as session:
            movie = session.get(Movie, movie_id)
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
        with self.get_session() as session:
            statement = select(Movie).where(
                Movie.batch_index == batch_num
            )
            movies = session.exec(statement)
            for movie in movies:
                movie.batch_id = batch_id
                movie.processed_status = status
                movie.last_updated = datetime.utcnow()

    def get_batch_count(self) -> int:
        with self.get_session() as session:
            statement = select(func.max(Movie.batch_index))
            result = session.exec(statement).first()
            return result or 0
