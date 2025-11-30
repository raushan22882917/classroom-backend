"""Quiz session models"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, List
from decimal import Decimal
from .base import Subject


class QuizSession(BaseModel):
    """Quiz session model"""
    id: str
    user_id: str
    microplan_id: Optional[str] = None
    quiz_data: dict = Field(default_factory=dict)
    subject: Subject
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    total_marks: Optional[int] = None
    score: Optional[Decimal] = Field(None, decimal_places=2)
    answers: Dict[str, str] = Field(default_factory=dict)
    is_completed: bool = False
    metadata: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QuizSessionCreate(BaseModel):
    """Quiz session creation model"""
    user_id: str
    microplan_id: Optional[str] = None
    quiz_data: dict = Field(default_factory=dict)
    subject: Subject
    duration_minutes: Optional[int] = None
    total_marks: Optional[int] = None


class QuizAnswerSubmission(BaseModel):
    """Quiz answer submission model"""
    question_id: str
    answer: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class QuizResult(BaseModel):
    """Quiz result model"""
    session_id: str
    score: Decimal = Field(decimal_places=2)
    total_marks: int
    percentage: Decimal = Field(decimal_places=2)
    time_taken_minutes: int
    correct_answers: int
    total_questions: int
    question_results: list = Field(default_factory=list)

    class Config:
        from_attributes = True


class QuizTemplate(BaseModel):
    """Quiz template model for teacher-created quizzes"""
    id: str
    teacher_id: str
    title: str
    subject: Subject
    description: Optional[str] = None
    quiz_data: dict = Field(default_factory=dict)
    duration_minutes: Optional[int] = None
    total_marks: Optional[int] = None
    class_grade: Optional[int] = None
    topic_ids: List[str] = Field(default_factory=list)
    is_active: bool = True
    metadata: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QuizTemplateCreate(BaseModel):
    """Quiz template creation model"""
    teacher_id: str
    title: str
    subject: Subject
    description: Optional[str] = None
    quiz_data: dict = Field(default_factory=dict)
    duration_minutes: Optional[int] = None
    total_marks: Optional[int] = None
    class_grade: Optional[int] = None
    topic_ids: List[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)






