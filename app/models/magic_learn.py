"""Magic Learn models for image analysis, gesture recognition, and story visualization"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class AnalysisType(str, Enum):
    """Types of analysis that can be performed"""
    MATHEMATICAL = "mathematical"
    SCIENTIFIC = "scientific"
    GENERAL = "general"
    TEXT_EXTRACTION = "text_extraction"
    OBJECT_IDENTIFICATION = "object_identification"


class ImageAnalysisRequest(BaseModel):
    """Request model for image analysis"""
    image_data: str = Field(..., description="Base64 encoded image data")
    custom_instructions: Optional[str] = Field(None, description="Custom analysis instructions")
    analysis_type: Optional[AnalysisType] = Field(AnalysisType.GENERAL, description="Type of analysis to perform")
    user_id: Optional[str] = Field(None, description="User ID for tracking")


class ImageAnalysisResponse(BaseModel):
    """Response model for image analysis"""
    success: bool = Field(..., description="Whether the analysis was successful")
    analysis: str = Field(..., description="Markdown-formatted analysis result")
    detected_elements: List[str] = Field(default_factory=list, description="List of detected elements")
    confidence_score: float = Field(..., description="Confidence score of the analysis (0-1)")
    processing_time: float = Field(..., description="Processing time in seconds")
    analysis_type: AnalysisType = Field(..., description="Type of analysis performed")
    error: Optional[str] = Field(None, description="Error message if analysis failed")


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