from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel
from sqlmodel import Field, SQLModel

class DataType(str, Enum):
    DEATHS = "deaths"
    TROPES = "tropes"

class ProcessingStatus(str, Enum):
    """Processing status of a movie"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ProcessingMethod(str, Enum):
    """Processing method of a movie"""
    BATCH = "batch"
    CHAT = "chat"

class MetadataStatus(str, Enum):
    """Status of movie character metadata"""
    COMPLETE = "complete"
    MISSING_METADATA = "missing_metadata"
    EMPTY_CHARACTERS = "empty_characters"

class Character(BaseModel):
    """Base model for a character"""
    name: str

class MovieBase(SQLModel):
    """Base model for movie data with processing metadata"""
    id: str = Field(primary_key=True)
    metadata_status: MetadataStatus
    processed_status: ProcessingStatus = Field(default=ProcessingStatus.PENDING)
    processing_method: Optional[ProcessingMethod] = None
    batch_id: Optional[str] = None
    batch_index: Optional[int] = None
    token_count: int = Field(default=0)
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class DatabaseMetadata(SQLModel, table=True):
    """Metadata for database type and creation time"""
    id: str = Field(default="metadata", primary_key=True)
    data_type: DataType
    created_at: datetime = Field(default_factory=datetime.utcnow)
