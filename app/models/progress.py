"""Progress and mastery tracking models"""

from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal
from .base import Subject


class MasteryScore(BaseModel):
    """Mastery score model"""
    topic_id: str
    score: Decimal = Field(ge=0, le=100, decimal_places=2)
    last_updated: datetime
    questions_attempted: int = 0
    correct_answers: int = 0

    class Config:
        from_attributes = True


class Progress(BaseModel):
    """Student progress model"""
    id: str
    user_id: str
    topic_id: str
    subject: Subject
    mastery_score: Decimal = Field(ge=0, le=100, decimal_places=2, default=Decimal("0.00"))
    questions_attempted: int = 0
    correct_answers: int = 0
    total_time_minutes: int = 0
    last_practiced_at: Optional[datetime] = None
    streak_days: int = 0
    last_streak_date: Optional[date] = None
    achievements: List[dict] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProgressCreate(BaseModel):
    """Progress creation model"""
    user_id: str
    topic_id: str
    subject: Subject
    mastery_score: Decimal = Field(ge=0, le=100, decimal_places=2, default=Decimal("0.00"))
    questions_attempted: int = 0
    correct_answers: int = 0


class ProgressUpdate(BaseModel):
    """Progress update model"""
    mastery_score: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)
    questions_attempted: Optional[int] = None
    correct_answers: Optional[int] = None
    total_time_minutes: Optional[int] = None
    last_practiced_at: Optional[datetime] = None
    streak_days: Optional[int] = None
    last_streak_date: Optional[date] = None
    achievements: Optional[List[dict]] = None


class Achievement(BaseModel):
    """Achievement model"""
    id: str
    name: str
    description: str
    icon: str
    earned_at: datetime
    metadata: dict = Field(default_factory=dict)


class MicroPlan(BaseModel):
    """Daily micro-plan model"""
    id: str
    user_id: str
    plan_date: date
    subject: Subject
    concept_summary_id: Optional[str] = None
    pyq_ids: List[str] = Field(default_factory=list)
    hots_question_id: Optional[str] = None
    quiz_data: dict = Field(default_factory=dict)
    estimated_minutes: int = 15
    is_completed: bool = False
    completed_at: Optional[datetime] = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MicroPlanCreate(BaseModel):
    """Micro-plan creation model"""
    user_id: str
    plan_date: date
    subject: Subject
    concept_summary_id: Optional[str] = None
    pyq_ids: List[str] = Field(default_factory=list)
    hots_question_id: Optional[str] = None
    quiz_data: dict = Field(default_factory=dict)
    estimated_minutes: int = 15


class MicroPlanUpdate(BaseModel):
    """Micro-plan update model"""
    is_completed: Optional[bool] = None
    completed_at: Optional[datetime] = None
    metadata: Optional[dict] = None


class Quiz(BaseModel):
    """Quiz model"""
    id: str
    questions: List[dict]
    total_marks: int
    duration_minutes: int
    metadata: dict = Field(default_factory=dict)
