"""Admin-related Pydantic models"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from .base import Subject


class StudentAlert(BaseModel):
    """Student alert model for flagged students"""
    user_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    subject: Subject
    mastery_score: Decimal = Field(ge=0, le=100, decimal_places=2)
    last_active: Optional[datetime] = None
    alert_reason: str
    alert_severity: str = "medium"  # low, medium, high


class AdminDashboardMetrics(BaseModel):
    """Admin dashboard aggregate metrics"""
    active_students: int = 0
    total_students: int = 0
    average_mastery_score: Decimal = Field(default=Decimal("0.00"), ge=0, le=100, decimal_places=2)
    completion_rate: Decimal = Field(default=Decimal("0.00"), ge=0, le=100, decimal_places=2)
    flagged_students: List[StudentAlert] = Field(default_factory=list)
    total_content_items: int = 0
    total_test_sessions: int = 0
    metadata: dict = Field(default_factory=dict)


class ContentUploadRequest(BaseModel):
    """Content upload request model"""
    type: str  # 'ncert', 'pyq', 'hots'
    subject: Subject
    chapter: Optional[str] = None
    topic_id: Optional[str] = None
    difficulty: Optional[str] = None  # 'easy', 'medium', 'hard'
    title: Optional[str] = None
    content_text: str
    metadata: dict = Field(default_factory=dict)
    
    # PYQ-specific fields
    year: Optional[int] = Field(None, ge=2000, le=2100)
    marks: Optional[int] = Field(None, gt=0)
    solution: Optional[str] = None
    topic_ids: List[str] = Field(default_factory=list)
    
    # HOTS-specific fields
    question_type: Optional[str] = None


class ContentUploadResponse(BaseModel):
    """Content upload response model"""
    id: str
    type: str
    subject: Subject
    embedding_id: Optional[str] = None
    indexed: bool = False
    message: str


class StudentOverview(BaseModel):
    """Student overview model for admin"""
    user_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    subjects: List[Subject] = Field(default_factory=list)
    average_mastery_score: Decimal = Field(ge=0, le=100, decimal_places=2)
    total_topics_completed: int = 0
    total_time_minutes: int = 0
    total_test_sessions: int = 0
    average_test_score: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)
    last_active: Optional[datetime] = None
    streak_days: int = 0
    is_flagged: bool = False
    created_at: datetime


class StudentDetailedProfile(BaseModel):
    """Detailed student profile for admin"""
    user_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    subjects: List[Subject] = Field(default_factory=list)
    
    # Progress metrics
    progress_by_subject: dict = Field(default_factory=dict)
    topics_completed: List[dict] = Field(default_factory=list)
    total_time_minutes: int = 0
    
    # Test performance
    test_sessions: List[dict] = Field(default_factory=list)
    average_test_score: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)
    
    # Activity
    last_active: Optional[datetime] = None
    streak_days: int = 0
    achievements: List[dict] = Field(default_factory=list)
    
    # Metadata
    created_at: datetime
    metadata: dict = Field(default_factory=dict)


class StudentExportData(BaseModel):
    """Student data for CSV export"""
    user_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    subjects: str  # Comma-separated
    average_mastery_score: Decimal
    topics_completed: int
    total_time_minutes: int
    total_test_sessions: int
    average_test_score: Optional[Decimal] = None
    last_active: Optional[str] = None
    streak_days: int
    created_at: str


class ContentPreview(BaseModel):
    """Content preview in RAG pipeline"""
    content_id: str
    content_text: str
    embedding_id: Optional[str] = None
    chunks: List[dict] = Field(default_factory=list)
    similar_content: List[dict] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class SchoolCreateRequest(BaseModel):
    """School creation request model"""
    name: str = Field(..., description="School name")
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    principal_name: Optional[str] = None


class SchoolUpdateRequest(BaseModel):
    """School update request model"""
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    principal_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserCreateRequest(BaseModel):
    """User creation request model"""
    email: str = Field(..., description="User email")
    password: str = Field(..., min_length=6, description="User password")
    full_name: str = Field(..., description="User full name")
    role: str = Field(..., description="User role: student or teacher")
    class_grade: Optional[int] = Field(None, ge=6, le=12, description="Class grade for students")
    phone: Optional[str] = None
    subject_specializations: Optional[List[str]] = Field(default_factory=list, description="Subject specializations for teachers")
