"""Doubt solver models"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum
from .base import Subject
from .content import ContentItem, PYQ, HOTSQuestion


class DoubtType(str, Enum):
    """Doubt input type enumeration"""
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"


class DoubtQuery(BaseModel):
    """Doubt query model"""
    id: str
    user_id: str
    type: DoubtType
    content: str
    subject: Optional[Subject] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict)

    class Config:
        from_attributes = True


class DoubtQueryCreate(BaseModel):
    """Doubt query creation model"""
    user_id: str
    type: DoubtType
    content: str
    subject: Optional[Subject] = None
    metadata: dict = Field(default_factory=dict)


class WolframStep(BaseModel):
    """Wolfram solution step model"""
    step_number: int
    description: str
    expression: str
    explanation: Optional[str] = None


class Source(BaseModel):
    """Content source citation model"""
    content_id: str
    type: str
    title: str
    confidence: float = Field(ge=0, le=1)
    excerpt: Optional[str] = None


class DoubtResponse(BaseModel):
    """Doubt response model"""
    query_id: str
    ncert_summary: str
    solved_example: Optional[ContentItem] = None
    related_pyq: Optional[PYQ] = None
    hots_question: Optional[HOTSQuestion] = None
    wolfram_steps: Optional[List[WolframStep]] = None
    sources: List[Source] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    metadata: dict = Field(default_factory=dict)

    class Config:
        from_attributes = True


class HomeworkSession(BaseModel):
    """Homework session model"""
    id: str
    user_id: str
    question_id: str
    question: str
    subject: str
    hints_revealed: int = 0
    attempts: List[dict] = Field(default_factory=list)
    is_complete: bool = False
    solution_revealed: bool = False
    correct_answer: Optional[str] = None
    metadata: Optional[dict] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HomeworkAttempt(BaseModel):
    """Homework attempt model"""
    answer: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_correct: bool
    feedback: str


class HintRequest(BaseModel):
    """Hint request model"""
    session_id: str
    hint_level: int = Field(ge=1, le=3)


class HintResponse(BaseModel):
    """Hint response model"""
    session_id: str
    hint_level: int
    hint_text: str
    is_final_hint: bool


class HomeworkStartRequest(BaseModel):
    """Homework session start request"""
    user_id: str
    question: str
    subject: Subject
    question_id: Optional[str] = None
    correct_answer: Optional[str] = None
    metadata: Optional[dict] = Field(default_factory=dict)


class HomeworkStartResponse(BaseModel):
    """Homework session start response"""
    session_id: str
    question: str
    subject: Subject
    message: str


class HomeworkAttemptRequest(BaseModel):
    """Homework attempt submission request"""
    session_id: str
    answer: str


class HomeworkAttemptResponse(BaseModel):
    """Homework attempt submission response"""
    session_id: str
    is_correct: bool
    feedback: str
    attempts_count: int
    solution_revealed: bool
    solution: Optional[str] = None
