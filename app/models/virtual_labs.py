"""Virtual Labs models for interactive science experiments"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from app.models.base import Subject


class DifficultyLevel(str, Enum):
    """Difficulty levels for virtual labs"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class CompletionStatus(str, Enum):
    """Session completion status"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class InteractionType(str, Enum):
    """Types of user interactions in virtual labs"""
    CLICK = "click"
    DRAG = "drag"
    GESTURE = "gesture"
    INPUT = "input"
    SELECTION = "selection"
    MEASUREMENT = "measurement"
    CALCULATION = "calculation"


class ResponseType(str, Enum):
    """Types of AI assistance responses"""
    EXPLANATION = "explanation"
    HINT = "hint"
    CORRECTION = "correction"
    ENCOURAGEMENT = "encouragement"
    GUIDANCE = "guidance"


# Base Models
class VirtualLabBase(BaseModel):
    """Base model for Virtual Lab"""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    subject: Subject
    class_grade: int = Field(..., ge=1, le=12)
    topic: str = Field(..., min_length=1, max_length=100)
    difficulty_level: DifficultyLevel
    estimated_duration: int = Field(..., ge=5, le=300, description="Duration in minutes")
    learning_objectives: List[str] = Field(..., min_items=1)
    prerequisites: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class VirtualLabCreate(VirtualLabBase):
    """Model for creating a new Virtual Lab"""
    html_content: str = Field(..., min_length=1)
    css_content: str = Field(default="")
    js_content: str = Field(default="")
    thumbnail_url: Optional[str] = None


class VirtualLabUpdate(BaseModel):
    """Model for updating a Virtual Lab"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=1000)
    subject: Optional[Subject] = None
    class_grade: Optional[int] = Field(None, ge=1, le=12)
    topic: Optional[str] = Field(None, min_length=1, max_length=100)
    html_content: Optional[str] = None
    css_content: Optional[str] = None
    js_content: Optional[str] = None
    thumbnail_url: Optional[str] = None
    difficulty_level: Optional[DifficultyLevel] = None
    estimated_duration: Optional[int] = Field(None, ge=5, le=300)
    learning_objectives: Optional[List[str]] = None
    prerequisites: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class VirtualLabResponse(VirtualLabBase):
    """Model for Virtual Lab response"""
    id: str
    html_content: str
    css_content: str
    js_content: str
    thumbnail_url: Optional[str] = None
    is_active: bool
    created_by: str
    created_at: datetime
    updated_at: datetime


class VirtualLabListResponse(BaseModel):
    """Model for Virtual Lab list response"""
    labs: List[VirtualLabResponse]
    total: int
    page: int
    limit: int


# Session Models
class VirtualLabSessionBase(BaseModel):
    """Base model for Virtual Lab Session"""
    user_id: str
    lab_id: str
    session_name: Optional[str] = None


class VirtualLabSessionCreate(VirtualLabSessionBase):
    """Model for creating a new lab session"""
    pass


class VirtualLabSessionUpdate(BaseModel):
    """Model for updating a lab session"""
    completed_at: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=0)
    completion_status: Optional[CompletionStatus] = None
    performance_score: Optional[float] = Field(None, ge=0, le=100)
    feedback: Optional[str] = None


class VirtualLabSessionResponse(VirtualLabSessionBase):
    """Model for Virtual Lab Session response"""
    id: str
    session_name: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    completion_status: CompletionStatus
    performance_score: Optional[float] = None
    feedback: Optional[str] = None
    interactions_count: int = 0
    gesture_commands_used: int = 0
    ai_assistance_requests: int = 0
    created_at: datetime
    updated_at: datetime


# Interaction Models
class VirtualLabInteractionBase(BaseModel):
    """Base model for Virtual Lab Interaction"""
    session_id: str
    interaction_type: InteractionType
    interaction_data: Dict[str, Any]
    element_id: Optional[str] = None
    gesture_type: Optional[str] = None
    performance_impact: Optional[float] = Field(None, ge=-1, le=1)


class VirtualLabInteractionCreate(VirtualLabInteractionBase):
    """Model for creating a new interaction"""
    pass


class VirtualLabInteractionResponse(VirtualLabInteractionBase):
    """Model for Virtual Lab Interaction response"""
    id: str
    timestamp: datetime


# AI Assistance Models
class VirtualLabAIAssistanceBase(BaseModel):
    """Base model for Virtual Lab AI Assistance"""
    session_id: str
    user_query: str
    context_data: Optional[Dict[str, Any]] = None
    response_type: ResponseType = ResponseType.EXPLANATION


class VirtualLabAIAssistanceCreate(VirtualLabAIAssistanceBase):
    """Model for creating AI assistance request"""
    pass


class VirtualLabAIAssistanceResponse(VirtualLabAIAssistanceBase):
    """Model for Virtual Lab AI Assistance response"""
    id: str
    ai_response: str
    created_at: datetime


# Performance Analytics Models
class ConceptMastery(BaseModel):
    """Model for concept mastery scores"""
    concept_name: str
    mastery_score: float = Field(..., ge=0, le=1)


class PerformanceMetrics(BaseModel):
    """Model for detailed performance metrics"""
    session_duration: int  # seconds
    interactions_count: int
    completion_percentage: float = Field(..., ge=0, le=100)
    accuracy_score: float = Field(..., ge=0, le=100)
    help_requests: int
    time_on_task: int  # seconds
    gesture_efficiency: float = Field(..., ge=0, le=1)
    concept_mastery: List[ConceptMastery]


class SessionPerformanceResponse(BaseModel):
    """Model for session performance response"""
    session_id: str
    metrics: PerformanceMetrics


# Aggregated Models
class VirtualLabStats(BaseModel):
    """Model for Virtual Lab statistics"""
    total_labs: int
    active_labs: int
    total_sessions: int
    active_sessions: int
    total_interactions: int
    average_completion_rate: float
    average_performance_score: float


class UserLabProgress(BaseModel):
    """Model for user's progress across labs"""
    user_id: str
    completed_labs: int
    in_progress_labs: int
    total_time_spent: int  # minutes
    average_score: float
    favorite_subjects: List[str]
    recent_sessions: List[VirtualLabSessionResponse]