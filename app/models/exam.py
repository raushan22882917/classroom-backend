"""Exam and test session models"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict
from decimal import Decimal
from .base import Subject


class ExamQuestion(BaseModel):
    """Exam question model"""
    id: str
    question: str
    marks: int
    question_type: str  # 'mcq', 'short_answer', 'long_answer', 'numerical'
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class ExamSet(BaseModel):
    """Exam set model"""
    id: str
    subject: Subject
    year: int
    duration_minutes: int
    total_marks: int
    questions: List[ExamQuestion]
    metadata: dict = Field(default_factory=dict)

    class Config:
        from_attributes = True


class ExamSetCreate(BaseModel):
    """Exam set creation model"""
    subject: Subject
    year: int
    duration_minutes: int
    total_marks: int
    questions: List[dict]
    metadata: dict = Field(default_factory=dict)


class TestSession(BaseModel):
    """Test session model"""
    id: str
    user_id: str
    exam_set_id: Optional[str] = None
    subject: Subject
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    total_marks: Optional[int] = None
    score: Optional[Decimal] = Field(None, decimal_places=2)
    answers: Dict[str, Dict[str, str]] = Field(default_factory=dict)
    is_completed: bool = False
    metadata: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TestSessionCreate(BaseModel):
    """Test session creation model"""
    user_id: str
    exam_set_id: Optional[str] = None
    subject: Subject
    duration_minutes: Optional[int] = None
    total_marks: Optional[int] = None


class TestSessionUpdate(BaseModel):
    """Test session update model"""
    end_time: Optional[datetime] = None
    score: Optional[Decimal] = Field(None, decimal_places=2)
    answers: Optional[Dict[str, Dict[str, str]]] = None
    is_completed: Optional[bool] = None


class AnswerSubmission(BaseModel):
    """Answer submission model"""
    question_id: str
    answer: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TestResult(BaseModel):
    """Test result model"""
    session_id: str
    score: Decimal = Field(decimal_places=2)
    total_marks: int
    percentage: Decimal = Field(decimal_places=2)
    time_taken_minutes: int
    correct_answers: int
    total_questions: int
    question_results: List[dict]
    model_answers: List[dict]
    marking_rubric: dict = Field(default_factory=dict)

    class Config:
        from_attributes = True


class PerformanceTrend(BaseModel):
    """Performance trend model"""
    user_id: str
    subject: Subject
    test_sessions: List[dict]
    average_score: Decimal = Field(decimal_places=2)
    improvement_rate: Decimal = Field(decimal_places=2)
    strengths: List[str]
    weaknesses: List[str]
    metadata: dict = Field(default_factory=dict)
