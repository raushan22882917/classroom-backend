"""Content-related Pydantic models"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum
from .base import Subject


class ContentType(str, Enum):
    """Content type enumeration"""
    NCERT = "ncert"
    PYQ = "pyq"
    HOTS = "hots"
    VIDEO = "video"


class DifficultyLevel(str, Enum):
    """Difficulty level enumeration"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Topic(BaseModel):
    """Topic model"""
    id: str
    subject: Subject
    chapter: str
    name: str
    order_index: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContentItem(BaseModel):
    """Content item model for NCERT, PYQ, HOTS content"""
    id: str
    type: ContentType
    subject: Subject
    chapter: Optional[str] = None
    topic_id: Optional[str] = None
    difficulty: Optional[DifficultyLevel] = None
    title: Optional[str] = None
    content_text: str
    metadata: dict = Field(default_factory=dict)
    embedding_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContentItemCreate(BaseModel):
    """Content item creation model"""
    type: ContentType
    subject: Subject
    chapter: Optional[str] = None
    topic_id: Optional[str] = None
    difficulty: Optional[DifficultyLevel] = None
    title: Optional[str] = None
    content_text: str
    metadata: dict = Field(default_factory=dict)


class ContentChunk(BaseModel):
    """Content chunk for RAG pipeline"""
    id: str
    content_id: str
    text: str
    embedding: List[float]
    metadata: dict = Field(default_factory=dict)

    class Config:
        from_attributes = True


class PYQ(BaseModel):
    """Previous Year Question model"""
    id: str
    subject: Subject
    year: int = Field(ge=2000, le=2100)
    question: str
    solution: str
    marks: int = Field(gt=0)
    topic_ids: List[str] = Field(default_factory=list)
    difficulty: Optional[DifficultyLevel] = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PYQCreate(BaseModel):
    """PYQ creation model"""
    subject: Subject
    year: int = Field(ge=2000, le=2100)
    question: str
    solution: str
    marks: int = Field(gt=0)
    topic_ids: List[str] = Field(default_factory=list)
    difficulty: Optional[DifficultyLevel] = None
    metadata: dict = Field(default_factory=dict)


class HOTSQuestion(BaseModel):
    """Higher Order Thinking Skills question model"""
    id: str
    subject: Subject
    topic_id: str
    question: str
    solution: str
    difficulty: DifficultyLevel = DifficultyLevel.HARD
    question_type: str = "case_based"
    metadata: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HOTSQuestionCreate(BaseModel):
    """HOTS question creation model"""
    subject: Subject
    topic_id: str
    question: str
    solution: str
    difficulty: DifficultyLevel = DifficultyLevel.HARD
    question_type: str = "case_based"
    metadata: dict = Field(default_factory=dict)


class Video(BaseModel):
    """Video model"""
    id: str
    youtube_id: str
    title: str
    transcript: Optional[str] = None
    timestamps: List[dict] = Field(default_factory=list)
    topic_ids: List[str] = Field(default_factory=list)
    subject: Optional[Subject] = None
    duration_seconds: Optional[int] = None
    channel_name: Optional[str] = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VideoCreate(BaseModel):
    """Video creation model"""
    youtube_id: str
    title: str
    transcript: Optional[str] = None
    timestamps: List[dict] = Field(default_factory=list)
    topic_ids: List[str] = Field(default_factory=list)
    subject: Optional[Subject] = None
    duration_seconds: Optional[int] = None
    channel_name: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class Timestamp(BaseModel):
    """Video timestamp model"""
    time: int  # seconds
    label: str
    topic_id: Optional[str] = None
