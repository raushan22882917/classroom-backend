"""
Pydantic models for Memory Intelligence features
Supports MemMachine and Neo4j integration
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum

class ContextType(str, Enum):
    """Types of contexts that can be stored"""
    GENERAL = "general"
    LEARNING = "learning"
    INTERACTION = "interaction"
    PERFORMANCE = "performance"
    PREFERENCE = "preference"
    SESSION = "session"
    NAVIGATION = "navigation"
    ERROR = "error"
    FEEDBACK = "feedback"

class SuggestionType(str, Enum):
    """Types of suggestions that can be requested"""
    NEXT_ACTION = "next_action"
    CONTENT_RECOMMENDATION = "content_recommendation"
    STUDY_SCHEDULE = "study_schedule"
    REVIEW_SUGGESTION = "review_suggestion"
    LEARNING_PATH = "learning_path"

class ContextData(BaseModel):
    """Model for storing context data"""
    type: ContextType = Field(default=ContextType.GENERAL, description="Type of context")
    content: Dict[str, Any] = Field(description="The actual context content")
    subject: Optional[str] = Field(None, description="Subject related to this context")
    topic: Optional[str] = Field(None, description="Specific topic")
    importance: float = Field(default=0.5, ge=0.0, le=1.0, description="Importance score")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    source: Optional[str] = Field(None, description="Source of the context (component, page, etc.)")
    session_id: Optional[str] = Field(None, description="Session ID if applicable")
    page_url: Optional[str] = Field(None, description="URL where context was generated")
    component: Optional[str] = Field(None, description="Frontend component that generated this")
    batch_id: Optional[str] = Field(None, description="Batch ID for bulk operations")

class PerformanceData(BaseModel):
    """Model for performance data within contexts"""
    accuracy: Optional[float] = Field(None, ge=0.0, le=1.0, description="Accuracy score")
    completion_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="Completion rate")
    duration: Optional[int] = Field(None, description="Duration in seconds")
    engagement_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Engagement score")
    attempts: Optional[int] = Field(None, description="Number of attempts")
    hints_used: Optional[int] = Field(None, description="Number of hints used")
    errors_made: Optional[int] = Field(None, description="Number of errors made")

class ContextResponse(BaseModel):
    """Response model for stored context"""
    memory_id: str = Field(description="Unique memory ID")
    content: Dict[str, Any] = Field(description="Stored content")
    metadata: Dict[str, Any] = Field(description="Context metadata")
    timestamp: str = Field(description="When context was stored")
    importance_score: float = Field(description="Importance score")
    access_count: int = Field(description="Number of times accessed")
    last_accessed: Optional[str] = Field(None, description="Last access time")
    tags: List[str] = Field(description="Associated tags")
    context_type: str = Field(description="Type of context")
    subject: Optional[str] = Field(None, description="Subject")
    topic: Optional[str] = Field(None, description="Topic")
    source: Optional[str] = Field(None, description="Source")

class SmartSuggestion(BaseModel):
    """Model for intelligent suggestions"""
    type: str = Field(description="Type of suggestion")
    action: str = Field(description="Suggested action")
    reason: str = Field(description="Reason for suggestion")
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in minutes")
    difficulty: Optional[int] = Field(None, description="Difficulty level")
    confidence: float = Field(description="Confidence in suggestion")
    priority: Optional[str] = Field(None, description="Priority level")

class UserInsights(BaseModel):
    """Model for user insights"""
    most_studied_subject: Optional[str] = Field(None, description="Most studied subject")
    most_studied_topic: Optional[str] = Field(None, description="Most studied topic")
    peak_activity_hour: Optional[int] = Field(None, description="Hour of peak activity")
    total_contexts: int = Field(description="Total number of contexts")
    learning_velocity: float = Field(description="Learning velocity score")
    mastery_rate: float = Field(description="Overall mastery rate")

class TimelineEvent(BaseModel):
    """Model for timeline events"""
    timestamp: str = Field(description="Event timestamp")
    type: str = Field(description="Event type")
    event_type: str = Field(description="Specific event type")
    title: str = Field(description="Event title")
    description: str = Field(description="Event description")
    subject: Optional[str] = Field(None, description="Related subject")
    topic: Optional[str] = Field(None, description="Related topic")
    importance: float = Field(description="Event importance")
    source: Optional[str] = Field(None, description="Event source")
    data: Dict[str, Any] = Field(description="Additional event data")

class TimelineSummary(BaseModel):
    """Model for timeline summary statistics"""
    total_events: int = Field(description="Total number of events")
    learning_sessions: int = Field(description="Number of learning sessions")
    interactions: int = Field(description="Number of interactions")
    subjects_studied: int = Field(description="Number of different subjects studied")
    most_active_day: Optional[str] = Field(None, description="Most active day")
    average_daily_activity: float = Field(description="Average daily activity")

class BulkContextRequest(BaseModel):
    """Model for bulk context storage request"""
    contexts: List[ContextData] = Field(description="List of contexts to store")

class ContextFilters(BaseModel):
    """Model for context filtering parameters"""
    context_type: Optional[ContextType] = Field(None, description="Filter by context type")
    subject: Optional[str] = Field(None, description="Filter by subject")
    topic: Optional[str] = Field(None, description="Filter by topic")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    limit: int = Field(default=20, description="Maximum number of results")
    days_back: int = Field(default=30, description="Days to look back")
    min_importance: float = Field(default=0.0, description="Minimum importance score")

class LearningContextData(BaseModel):
    """Extended context data specifically for learning activities"""
    type: ContextType = Field(default=ContextType.LEARNING, description="Context type")
    content: Dict[str, Any] = Field(description="Learning content")
    subject: str = Field(description="Subject being learned")
    topic: str = Field(description="Specific topic")
    difficulty_level: int = Field(default=1, ge=1, le=5, description="Difficulty level")
    learning_objectives: List[str] = Field(default_factory=list, description="Learning objectives")
    performance_data: Optional[PerformanceData] = Field(None, description="Performance metrics")
    session_duration: Optional[int] = Field(None, description="Session duration in minutes")
    completion_status: Optional[str] = Field(None, description="Completion status")
    mistakes_made: Optional[List[str]] = Field(None, description="Common mistakes")
    concepts_mastered: Optional[List[str]] = Field(None, description="Concepts mastered")
    next_steps: Optional[List[str]] = Field(None, description="Suggested next steps")

class InteractionContextData(BaseModel):
    """Extended context data for user interactions"""
    type: ContextType = Field(default=ContextType.INTERACTION, description="Context type")
    content: Dict[str, Any] = Field(description="Interaction content")
    component: str = Field(description="Component that was interacted with")
    action: str = Field(description="Type of action performed")
    page_url: str = Field(description="URL where interaction occurred")
    interaction_duration: Optional[int] = Field(None, description="Duration of interaction")
    success: bool = Field(default=True, description="Whether interaction was successful")
    error_message: Optional[str] = Field(None, description="Error message if any")
    user_feedback: Optional[str] = Field(None, description="User feedback")

class PreferenceContextData(BaseModel):
    """Extended context data for user preferences"""
    type: ContextType = Field(default=ContextType.PREFERENCE, description="Context type")
    content: Dict[str, Any] = Field(description="Preference content")
    preference_category: str = Field(description="Category of preference")
    old_value: Optional[Any] = Field(None, description="Previous value")
    new_value: Any = Field(description="New preference value")
    reason: Optional[str] = Field(None, description="Reason for change")
    auto_detected: bool = Field(default=False, description="Whether preference was auto-detected")

# Response Models
class RememberContextResponse(BaseModel):
    """Response for remember context endpoint"""
    success: bool = Field(description="Whether operation was successful")
    memory_id: str = Field(description="Unique memory ID")
    message: str = Field(description="Success message")
    stored_at: str = Field(description="Storage timestamp")
    tags: List[str] = Field(description="Applied tags")

class RecallContextResponse(BaseModel):
    """Response for recall context endpoint"""
    success: bool = Field(description="Whether operation was successful")
    user_id: str = Field(description="User ID")
    total_contexts: int = Field(description="Total number of contexts found")
    contexts: List[ContextResponse] = Field(description="Retrieved contexts")
    filters_applied: Dict[str, Any] = Field(description="Filters that were applied")

class SmartSuggestionsResponse(BaseModel):
    """Response for smart suggestions endpoint"""
    success: bool = Field(description="Whether operation was successful")
    user_id: str = Field(description="User ID")
    suggestion_type: str = Field(description="Type of suggestions")
    suggestions: List[SmartSuggestion] = Field(description="Generated suggestions")
    insights: UserInsights = Field(description="User insights")
    generated_at: str = Field(description="Generation timestamp")

class BulkRememberResponse(BaseModel):
    """Response for bulk remember endpoint"""
    success: bool = Field(description="Whether operation was successful")
    user_id: str = Field(description="User ID")
    total_stored: int = Field(description="Total contexts stored")
    stored_contexts: List[Dict[str, Any]] = Field(description="Summary of stored contexts")
    learning_updates: int = Field(description="Number of learning updates made")
    stored_at: str = Field(description="Storage timestamp")

class UserTimelineResponse(BaseModel):
    """Response for user timeline endpoint"""
    success: bool = Field(description="Whether operation was successful")
    user_id: str = Field(description="User ID")
    timeline_period: Dict[str, Any] = Field(description="Timeline period information")
    summary: TimelineSummary = Field(description="Timeline summary statistics")
    timeline: List[TimelineEvent] = Field(description="Timeline events")

# Request Models for specific endpoints
class SmartSuggestionsRequest(BaseModel):
    """Request model for smart suggestions"""
    current_context: Dict[str, Any] = Field(default_factory=dict, description="Current user context")
    suggestion_type: SuggestionType = Field(default=SuggestionType.NEXT_ACTION, description="Type of suggestions needed")

class TimelineRequest(BaseModel):
    """Request model for user timeline"""
    days_back: int = Field(default=7, description="Days to look back")
    include_learning: bool = Field(default=True, description="Include learning progress")
    include_interactions: bool = Field(default=True, description="Include user interactions")