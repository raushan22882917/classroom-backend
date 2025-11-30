"""Models for AI features: tutoring, teacher tools, and well-being"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from app.models.base import Subject


class FeedbackRequest(BaseModel):
    """Request model for personalized feedback"""
    user_id: str
    content: str
    subject: Subject
    performance_data: Optional[Dict[str, Any]] = None


class StudyPlanRequest(BaseModel):
    """Request model for study plan generation"""
    user_id: str
    subject: Subject
    days: int = Field(default=7, ge=1, le=30)
    hours_per_day: float = Field(default=2.0, ge=0.5, le=8.0)


class QuestionAnswerRequest(BaseModel):
    """Request model for question answering"""
    user_id: str
    question: str
    subject: Subject
    context: Optional[str] = None


class LessonPlanRequest(BaseModel):
    """Request model for lesson plan generation"""
    teacher_id: str
    subject: Subject
    topic: str
    duration_minutes: int = Field(default=45, ge=15, le=120)
    class_grade: int = Field(default=12, ge=6, le=12)
    learning_objectives: Optional[List[str]] = None


class AssessmentRequest(BaseModel):
    """Request model for formative assessment"""
    teacher_id: str
    subject: Subject
    topic: str
    question_count: int = Field(default=5, ge=1, le=20)
    difficulty_levels: Optional[List[str]] = None


class ParentMessageRequest(BaseModel):
    """Request model for parent communication"""
    teacher_id: str
    student_id: str
    message_type: str = Field(..., pattern="^(progress_update|concern|achievement|general)$")
    subject: Optional[Subject] = None
    custom_content: Optional[str] = None


class FocusSessionRequest(BaseModel):
    """Request model for focus session"""
    user_id: str
    duration_minutes: int = Field(..., ge=5, le=180)
    subject: Optional[Subject] = None
    goal: Optional[str] = None


class FocusSessionEndRequest(BaseModel):
    """Request model for ending focus session"""
    session_id: str
    user_id: str
    distractions_count: int = Field(default=0, ge=0)
    completed: bool = True


class TranslationRequest(BaseModel):
    """Request model for translation"""
    text: str
    target_language: str = Field(default="en", min_length=2, max_length=5)
    source_language: Optional[str] = Field(default=None, min_length=2, max_length=5)


class BatchTranslationRequest(BaseModel):
    """Request model for batch translation"""
    texts: List[str]
    target_language: str = Field(default="en", min_length=2, max_length=5)
    source_language: Optional[str] = Field(default=None, min_length=2, max_length=5)


class LanguageDetectionRequest(BaseModel):
    """Request model for language detection"""
    text: str = Field(..., min_length=1)


class CreateSessionRequest(BaseModel):
    """Request model for creating AI tutor session"""
    user_id: str
    session_name: Optional[str] = None
    subject: Optional[Subject] = None


class SendMessageRequest(BaseModel):
    """Request model for sending message in session"""
    session_id: str
    user_id: str
    content: str
    subject: Optional[Subject] = None
    message_type: str = Field(default="text", pattern="^(text|question|homework_help|lesson_plan)$")


class GenerateLessonPlanRequest(BaseModel):
    """Request model for generating performance-based lesson plan"""
    user_id: str
    subject: Subject
    days: int = Field(default=7, ge=1, le=30)
    hours_per_day: float = Field(default=2.0, ge=0.5, le=8.0)


