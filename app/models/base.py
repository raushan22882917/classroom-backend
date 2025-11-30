"""Base models and enums"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class Subject(str, Enum):
    """Subject types"""
    MATHEMATICS = "mathematics"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"


class BaseResponse(BaseModel):
    """Base response model"""
    success: bool
    message: str
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    detail: Optional[str] = None
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class Message(BaseModel):
    """Message model"""
    id: str
    conversation_id: str
    sender_id: str
    receiver_id: str
    content: str
    is_read: bool = False
    read_at: Optional[datetime] = None
    metadata: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Conversation(BaseModel):
    """Conversation model"""
    id: str
    participant1_id: str
    participant2_id: str
    last_message_at: Optional[datetime] = None
    last_message_content: Optional[str] = None
    unread_count_participant1: int = 0
    unread_count_participant2: int = 0
    metadata: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    """Message creation request"""
    conversation_id: str
    sender_id: str
    receiver_id: str
    content: str
    metadata: Optional[dict] = None


class MessageImproveRequest(BaseModel):
    """Message improvement request"""
    text: str
    tone: Optional[str] = "professional"  # professional, friendly, formal, casual
    context: Optional[str] = None


class ConversationCreateRequest(BaseModel):
    """Conversation creation request"""
    participant1_id: str
    participant2_id: str


class MessageSuggestionsRequest(BaseModel):
    """Message suggestions request"""
    context: str
    recipient_role: Optional[str] = None
