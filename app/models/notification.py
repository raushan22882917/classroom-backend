"""Notification models"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict
from enum import Enum


class NotificationType(str, Enum):
    """Notification type enum"""
    ASSIGNMENT = "assignment"
    GRADE = "grade"
    ANNOUNCEMENT = "announcement"
    HOMEWORK = "homework"
    EXAM = "exam"
    QUIZ = "quiz"
    MESSAGE = "message"
    SYSTEM = "system"


class NotificationPriority(str, Enum):
    """Notification priority enum"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Notification(BaseModel):
    """Notification model"""
    id: str
    user_id: str
    title: str
    message: str
    type: NotificationType
    priority: NotificationPriority
    is_read: bool = False
    read_at: Optional[datetime] = None
    action_url: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationCreate(BaseModel):
    """Notification creation model"""
    user_id: str
    title: str
    message: str
    type: NotificationType = NotificationType.SYSTEM
    priority: NotificationPriority = NotificationPriority.MEDIUM
    action_url: Optional[str] = None
    metadata: Dict = Field(default_factory=dict)
    created_by: Optional[str] = None


class NotificationUpdate(BaseModel):
    """Notification update model"""
    is_read: Optional[bool] = None


class NotificationResponse(BaseModel):
    """Notification response model"""
    notifications: list[Notification]
    unread_count: int
    total_count: int
