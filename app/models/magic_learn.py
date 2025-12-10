"""Magic Learn models for image analysis, gesture recognition, and story visualization"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum
import uuid


class AnalysisType(str, Enum):
    """Types of analysis that can be performed"""
    MATHEMATICAL = "mathematical"
    SCIENTIFIC = "scientific"
    GENERAL = "general"
    TEXT_EXTRACTION = "text_extraction"
    OBJECT_IDENTIFICATION = "object_identification"
    CHEMISTRY = "chemistry"
    PHYSICS = "physics"
    BIOLOGY = "biology"
    GEOMETRY = "geometry"
    ALGEBRA = "algebra"


class DifficultyLevel(str, Enum):
    """Difficulty levels for educational content"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class LanguageCode(str, Enum):
    """Supported languages"""
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    CHINESE = "zh"
    JAPANESE = "ja"
    KOREAN = "ko"
    HINDI = "hi"
    ARABIC = "ar"


class ImageAnalysisRequest(BaseModel):
    """Request model for image analysis"""
    image_data: str = Field(..., description="Base64 encoded image data")
    custom_instructions: Optional[str] = Field(None, description="Custom analysis instructions")
    analysis_type: Optional[AnalysisType] = Field(AnalysisType.GENERAL, description="Type of analysis to perform")
    user_id: Optional[str] = Field(None, description="User ID for tracking")
    difficulty_level: Optional[DifficultyLevel] = Field(DifficultyLevel.INTERMEDIATE, description="Target difficulty level")
    language: Optional[LanguageCode] = Field(LanguageCode.ENGLISH, description="Response language")
    include_step_by_step: bool = Field(True, description="Include step-by-step explanations")
    include_examples: bool = Field(True, description="Include related examples")
    
    @validator('image_data')
    def validate_image_data(cls, v):
        if not v or len(v) < 100:
            raise ValueError("Image data is required and must be valid base64")
        return v


class ImageAnalysisResponse(BaseModel):
    """Response model for image analysis"""
    success: bool = Field(..., description="Whether the analysis was successful")
    analysis: str = Field(..., description="Markdown-formatted analysis result")
    detected_elements: List[str] = Field(default_factory=list, description="List of detected elements")
    confidence_score: float = Field(..., description="Confidence score of the analysis (0-1)")
    processing_time: float = Field(..., description="Processing time in seconds")
    analysis_type: AnalysisType = Field(..., description="Type of analysis performed")
    error: Optional[str] = Field(None, description="Error message if analysis failed")
    session_id: Optional[str] = Field(None, description="Session ID for tracking")
    
    # Enhanced analysis results
    key_concepts: List[str] = Field(default_factory=list, description="Key educational concepts identified")
    difficulty_assessment: Optional[DifficultyLevel] = Field(None, description="Assessed difficulty level")
    suggested_next_steps: List[str] = Field(default_factory=list, description="Suggested learning activities")
    related_topics: List[str] = Field(default_factory=list, description="Related educational topics")
    
    # Structured content for better frontend integration
    structured_content: Optional[Dict[str, Any]] = Field(None, description="Structured analysis content")
    interactive_elements: List[Dict[str, Any]] = Field(default_factory=list, description="Interactive learning elements")


class GesturePoint(BaseModel):
    """A point in gesture recognition"""
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    timestamp: datetime = Field(..., description="Timestamp of the point")


class GestureRecognitionRequest(BaseModel):
    """Request model for gesture recognition"""
    gesture_points: List[GesturePoint] = Field(..., description="List of gesture points")
    canvas_width: int = Field(..., description="Canvas width in pixels")
    canvas_height: int = Field(..., description="Canvas height in pixels")
    user_id: Optional[str] = Field(None, description="User ID for tracking")


class RecognizedShape(BaseModel):
    """A recognized shape from gesture"""
    shape_type: str = Field(..., description="Type of shape (circle, line, rectangle, etc.)")
    confidence: float = Field(..., description="Confidence score (0-1)")
    coordinates: List[GesturePoint] = Field(..., description="Shape coordinates")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Shape properties")


class GestureRecognitionResponse(BaseModel):
    """Response model for gesture recognition"""
    success: bool = Field(..., description="Whether recognition was successful")
    recognized_shapes: List[RecognizedShape] = Field(default_factory=list, description="List of recognized shapes")
    interpretation: str = Field(..., description="Interpretation of the drawn content")
    suggestions: List[str] = Field(default_factory=list, description="Learning suggestions")
    error: Optional[str] = Field(None, description="Error message if recognition failed")


class StoryElement(BaseModel):
    """An element in a story"""
    element_type: str = Field(..., description="Type of element (character, setting, plot_point, etc.)")
    name: str = Field(..., description="Name of the element")
    description: str = Field(..., description="Description of the element")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Element properties")


class PlotCrafterRequest(BaseModel):
    """Request model for plot crafter"""
    story_prompt: str = Field(..., description="Story prompt or theme")
    educational_topic: Optional[str] = Field(None, description="Educational topic to incorporate")
    target_age_group: Optional[str] = Field("12-18", description="Target age group")
    story_length: Optional[str] = Field("medium", description="Story length (short, medium, long)")
    user_id: Optional[str] = Field(None, description="User ID for tracking")


class GeneratedStory(BaseModel):
    """A generated story"""
    title: str = Field(..., description="Story title")
    content: str = Field(..., description="Story content in markdown")
    characters: List[StoryElement] = Field(default_factory=list, description="Story characters")
    settings: List[StoryElement] = Field(default_factory=list, description="Story settings")
    educational_elements: List[str] = Field(default_factory=list, description="Educational concepts covered")
    learning_objectives: List[str] = Field(default_factory=list, description="Learning objectives")


class PlotCrafterResponse(BaseModel):
    """Response model for plot crafter"""
    success: bool = Field(..., description="Whether story generation was successful")
    story: GeneratedStory = Field(..., description="Generated story")
    visualization_prompts: List[str] = Field(default_factory=list, description="Prompts for AI image generation")
    interactive_elements: List[Dict[str, Any]] = Field(default_factory=list, description="Interactive story elements")
    error: Optional[str] = Field(None, description="Error message if generation failed")


class MagicLearnSession(BaseModel):
    """Magic Learn session tracking"""
    session_id: str = Field(..., description="Unique session ID")
    user_id: Optional[str] = Field(None, description="User ID")
    tool_used: str = Field(..., description="Tool used (image_reader, draw_in_air, plot_crafter)")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Session creation time")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update time")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Session metadata")


class MagicLearnAnalytics(BaseModel):
    """Analytics for Magic Learn usage"""
    total_sessions: int = Field(..., description="Total number of sessions")
    image_reader_usage: int = Field(..., description="Image reader usage count")
    draw_in_air_usage: int = Field(..., description="Draw in air usage count")
    plot_crafter_usage: int = Field(..., description="Plot crafter usage count")
    average_processing_time: float = Field(..., description="Average processing time")
    success_rate: float = Field(..., description="Success rate percentage")
    popular_analysis_types: List[Dict[str, Any]] = Field(default_factory=list, description="Popular analysis types")


# New Advanced Models for Enhanced Functionality

class BatchAnalysisRequest(BaseModel):
    """Request model for batch image analysis"""
    images: List[Dict[str, Any]] = Field(..., description="List of images with metadata")
    analysis_type: AnalysisType = Field(AnalysisType.GENERAL, description="Type of analysis to perform")
    user_id: Optional[str] = Field(None, description="User ID for tracking")
    batch_name: Optional[str] = Field(None, description="Name for this batch")
    
    @validator('images')
    def validate_images(cls, v):
        if not v or len(v) == 0:
            raise ValueError("At least one image is required")
        if len(v) > 10:
            raise ValueError("Maximum 10 images per batch")
        return v


class BatchAnalysisResponse(BaseModel):
    """Response model for batch image analysis"""
    success: bool = Field(..., description="Whether the batch analysis was successful")
    batch_id: str = Field(..., description="Unique batch ID")
    results: List[ImageAnalysisResponse] = Field(default_factory=list, description="Individual analysis results")
    summary: str = Field(..., description="Summary of batch analysis")
    total_processing_time: float = Field(..., description="Total processing time")
    error: Optional[str] = Field(None, description="Error message if batch failed")


class RealTimeAnalysisRequest(BaseModel):
    """Request model for real-time analysis streaming"""
    stream_id: str = Field(..., description="Unique stream identifier")
    frame_data: str = Field(..., description="Base64 encoded frame data")
    analysis_type: AnalysisType = Field(AnalysisType.GENERAL, description="Type of analysis")
    user_id: Optional[str] = Field(None, description="User ID for tracking")


class RealTimeAnalysisResponse(BaseModel):
    """Response model for real-time analysis"""
    success: bool = Field(..., description="Whether analysis was successful")
    stream_id: str = Field(..., description="Stream identifier")
    frame_number: int = Field(..., description="Frame sequence number")
    analysis: str = Field(..., description="Quick analysis result")
    confidence: float = Field(..., description="Confidence score")
    detected_objects: List[str] = Field(default_factory=list, description="Detected objects in frame")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")


class CollaborativeSessionRequest(BaseModel):
    """Request model for collaborative learning sessions"""
    session_name: str = Field(..., description="Name of the collaborative session")
    participants: List[str] = Field(..., description="List of participant user IDs")
    session_type: str = Field(..., description="Type of collaborative session")
    max_participants: int = Field(10, description="Maximum number of participants")
    duration_minutes: Optional[int] = Field(60, description="Session duration in minutes")


class CollaborativeSessionResponse(BaseModel):
    """Response model for collaborative sessions"""
    success: bool = Field(..., description="Whether session creation was successful")
    session_id: str = Field(..., description="Unique session ID")
    join_code: str = Field(..., description="Code for participants to join")
    session_url: str = Field(..., description="URL to join the session")
    expires_at: datetime = Field(..., description="Session expiration time")


class LearningPathRequest(BaseModel):
    """Request model for personalized learning path generation"""
    user_id: str = Field(..., description="User ID")
    subject_area: str = Field(..., description="Subject area (math, science, etc.)")
    current_level: DifficultyLevel = Field(..., description="Current skill level")
    learning_goals: List[str] = Field(..., description="Learning objectives")
    time_available: int = Field(..., description="Available study time per week (hours)")
    preferred_learning_style: str = Field(..., description="Visual, auditory, kinesthetic, etc.")


class LearningPathResponse(BaseModel):
    """Response model for learning path generation"""
    success: bool = Field(..., description="Whether path generation was successful")
    path_id: str = Field(..., description="Unique learning path ID")
    milestones: List[Dict[str, Any]] = Field(default_factory=list, description="Learning milestones")
    estimated_duration: int = Field(..., description="Estimated completion time (days)")
    recommended_activities: List[Dict[str, Any]] = Field(default_factory=list, description="Recommended learning activities")
    progress_tracking: Dict[str, Any] = Field(default_factory=dict, description="Progress tracking configuration")


class AITutorRequest(BaseModel):
    """Request model for AI tutor interactions"""
    user_id: str = Field(..., description="User ID")
    question: str = Field(..., description="Student's question")
    context: Optional[str] = Field(None, description="Additional context")
    subject: Optional[str] = Field(None, description="Subject area")
    difficulty_level: DifficultyLevel = Field(DifficultyLevel.INTERMEDIATE, description="Difficulty level")
    learning_style: Optional[str] = Field(None, description="Preferred learning style")


class AITutorResponse(BaseModel):
    """Response model for AI tutor interactions"""
    success: bool = Field(..., description="Whether the interaction was successful")
    response: str = Field(..., description="AI tutor's response")
    explanation_type: str = Field(..., description="Type of explanation provided")
    follow_up_questions: List[str] = Field(default_factory=list, description="Suggested follow-up questions")
    related_concepts: List[str] = Field(default_factory=list, description="Related concepts to explore")
    practice_problems: List[Dict[str, Any]] = Field(default_factory=list, description="Practice problems")
    confidence_score: float = Field(..., description="Confidence in the response")


class AssessmentRequest(BaseModel):
    """Request model for automated assessments"""
    user_id: str = Field(..., description="User ID")
    subject: str = Field(..., description="Subject area")
    topic: str = Field(..., description="Specific topic")
    difficulty_level: DifficultyLevel = Field(..., description="Assessment difficulty")
    question_count: int = Field(10, ge=5, le=50, description="Number of questions")
    question_types: List[str] = Field(default_factory=list, description="Types of questions to include")


class AssessmentResponse(BaseModel):
    """Response model for automated assessments"""
    success: bool = Field(..., description="Whether assessment generation was successful")
    assessment_id: str = Field(..., description="Unique assessment ID")
    questions: List[Dict[str, Any]] = Field(default_factory=list, description="Assessment questions")
    time_limit: int = Field(..., description="Recommended time limit (minutes)")
    scoring_rubric: Dict[str, Any] = Field(default_factory=dict, description="Scoring criteria")
    learning_objectives: List[str] = Field(default_factory=list, description="Learning objectives covered")


class ProgressTrackingRequest(BaseModel):
    """Request model for progress tracking"""
    user_id: str = Field(..., description="User ID")
    activity_type: str = Field(..., description="Type of learning activity")
    activity_data: Dict[str, Any] = Field(..., description="Activity completion data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Activity timestamp")


class ProgressTrackingResponse(BaseModel):
    """Response model for progress tracking"""
    success: bool = Field(..., description="Whether progress was recorded successfully")
    user_id: str = Field(..., description="User ID")
    current_level: str = Field(..., description="Current skill level")
    progress_percentage: float = Field(..., description="Overall progress percentage")
    achievements: List[str] = Field(default_factory=list, description="Recent achievements")
    next_recommendations: List[str] = Field(default_factory=list, description="Next recommended activities")
    streak_count: int = Field(0, description="Current learning streak")


class ContentGenerationRequest(BaseModel):
    """Request model for educational content generation"""
    topic: str = Field(..., description="Educational topic")
    content_type: str = Field(..., description="Type of content (lesson, quiz, exercise, etc.)")
    difficulty_level: DifficultyLevel = Field(..., description="Target difficulty level")
    duration_minutes: int = Field(30, description="Target content duration")
    learning_objectives: List[str] = Field(..., description="Specific learning objectives")
    format_preferences: List[str] = Field(default_factory=list, description="Preferred content formats")


class ContentGenerationResponse(BaseModel):
    """Response model for educational content generation"""
    success: bool = Field(..., description="Whether content generation was successful")
    content_id: str = Field(..., description="Unique content ID")
    title: str = Field(..., description="Content title")
    content: str = Field(..., description="Generated educational content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Content metadata")
    interactive_elements: List[Dict[str, Any]] = Field(default_factory=list, description="Interactive components")
    assessment_questions: List[Dict[str, Any]] = Field(default_factory=list, description="Related assessment questions")