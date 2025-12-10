"""Magic Learn router for AI-powered learning tools"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from typing import Optional, List
import logging
import traceback
import time

from app.models.magic_learn import (
    ImageAnalysisRequest, ImageAnalysisResponse,
    GestureRecognitionRequest, GestureRecognitionResponse,
    PlotCrafterRequest, PlotCrafterResponse,
    MagicLearnAnalytics, AnalysisType
)
from app.services.magic_learn_service import (
    image_reader_service,
    draw_in_air_service,
    plot_crafter_service,
    analytics_service
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/magic-learn/health")
async def health_check():
    """Health check endpoint for Magic Learn services"""
    return {
        "status": "healthy",
        "services": {
            "image_reader": "active",
            "draw_in_air": "active", 
            "plot_crafter": "active"
        },
        "timestamp": time.time()
    }


@router.post("/magic-learn/image-reader/analyze", response_model=ImageAnalysisResponse)
async def analyze_image(request: ImageAnalysisRequest):
    """
    Analyze uploaded images and sketches with AI vision models
    
    This endpoint processes hand-drawn sketches, diagrams, mathematical equations,
    scientific content, and general educational material.
    """
    try:
        # Create session for tracking
        session_id = await analytics_service.create_session(
            user_id=request.user_id,
            tool_used="image_reader"
        )
        
        # Perform image analysis
        result = await image_reader_service.analyze_image(request)
        
        # Update session with results
        await analytics_service.update_session(session_id, {
            "analysis_type": request.analysis_type.value,
            "success": result.success,
            "processing_time": result.processing_time,
            "confidence_score": result.confidence_score,
            "detected_elements_count": len(result.detected_elements)
        })
        
        logger.info(f"Image analysis completed - Session: {session_id}, Success: {result.success}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in image analysis: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return ImageAnalysisResponse(
            success=False,
            analysis="",
            detected_elements=[],
            confidence_score=0.0,
            processing_time=0.0,
            analysis_type=request.analysis_type,
            error=f"Analysis failed: {str(e)}"
        )


@router.post("/magic-learn/image-reader/upload", response_model=ImageAnalysisResponse)
async def upload_and_analyze_image(
    file: UploadFile = File(...),
    analysis_type: AnalysisType = Form(AnalysisType.GENERAL),
    custom_instructions: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None)
):
    """
    Upload and analyze image files directly
    
    Supports JPG, PNG, and WEBP formats up to 10MB.
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read file content
        file_content = await file.read()
        
        # Convert to base64
        import base64
        image_data = base64.b64encode(file_content).decode('utf-8')
        
        # Create analysis request
        request = ImageAnalysisRequest(
            image_data=image_data,
            analysis_type=analysis_type,
            custom_instructions=custom_instructions,
            user_id=user_id
        )
        
        # Analyze image
        return await analyze_image(request)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in file upload and analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/magic-learn/draw-in-air/recognize", response_model=GestureRecognitionResponse)
async def recognize_gestures(request: GestureRecognitionRequest):
    """
    Recognize shapes and patterns from hand gesture points
    
    Processes gesture coordinates to identify geometric shapes, mathematical
    concepts, and provide educational insights.
    """
    try:
        # Create session for tracking
        session_id = await analytics_service.create_session(
            user_id=request.user_id,
            tool_used="draw_in_air"
        )
        
        # Perform gesture recognition
        result = await draw_in_air_service.recognize_gestures(request)
        
        # Update session with results
        await analytics_service.update_session(session_id, {
            "gesture_points_count": len(request.gesture_points),
            "canvas_size": f"{request.canvas_width}x{request.canvas_height}",
            "success": result.success,
            "recognized_shapes_count": len(result.recognized_shapes),
            "shapes_detected": [shape.shape_type for shape in result.recognized_shapes]
        })
        
        logger.info(f"Gesture recognition completed - Session: {session_id}, Success: {result.success}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in gesture recognition: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return GestureRecognitionResponse(
            success=False,
            recognized_shapes=[],
            interpretation="",
            suggestions=[],
            error=f"Recognition failed: {str(e)}"
        )


@router.post("/magic-learn/plot-crafter/generate", response_model=PlotCrafterResponse)
async def generate_story(request: PlotCrafterRequest):
    """
    Generate educational stories with AI-powered visualizations
    
    Creates interactive learning experiences through story-based content
    with educational objectives and visual elements.
    """
    try:
        # Create session for tracking
        session_id = await analytics_service.create_session(
            user_id=request.user_id,
            tool_used="plot_crafter"
        )
        
        # Generate story
        result = await plot_crafter_service.generate_story(request)
        
        # Update session with results
        await analytics_service.update_session(session_id, {
            "story_prompt": request.story_prompt[:100],  # First 100 chars
            "educational_topic": request.educational_topic,
            "target_age_group": request.target_age_group,
            "story_length": request.story_length,
            "success": result.success,
            "story_title": result.story.title if result.success else None,
            "characters_count": len(result.story.characters) if result.success else 0,
            "educational_elements_count": len(result.story.educational_elements) if result.success else 0
        })
        
        logger.info(f"Story generation completed - Session: {session_id}, Success: {result.success}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in story generation: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return PlotCrafterResponse(
            success=False,
            story=None,
            visualization_prompts=[],
            interactive_elements=[],
            error=f"Story generation failed: {str(e)}"
        )


@router.get("/magic-learn/analytics", response_model=MagicLearnAnalytics)
async def get_analytics():
    """
    Get usage analytics for Magic Learn platform
    
    Returns statistics about tool usage, success rates, and popular features.
    """
    try:
        analytics = await analytics_service.get_analytics()
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analytics retrieval failed: {str(e)}")


@router.get("/magic-learn/analysis-types")
async def get_analysis_types():
    """Get available analysis types for image reader"""
    return {
        "analysis_types": [
            {
                "value": "mathematical",
                "label": "Mathematical Content",
                "description": "Analyze equations, formulas, and mathematical diagrams"
            },
            {
                "value": "scientific", 
                "label": "Scientific Diagrams",
                "description": "Analyze scientific charts, diagrams, and illustrations"
            },
            {
                "value": "text_extraction",
                "label": "Text Extraction",
                "description": "Extract and analyze text content from images"
            },
            {
                "value": "object_identification",
                "label": "Object Identification", 
                "description": "Identify objects, shapes, and visual elements"
            },
            {
                "value": "general",
                "label": "General Analysis",
                "description": "Comprehensive analysis of educational content"
            }
        ]
    }


@router.get("/magic-learn/examples")
async def get_examples():
    """Get example use cases and sample content for Magic Learn tools"""
    return {
        "image_reader_examples": [
            {
                "title": "Mathematical Equations",
                "description": "Upload sketches of quadratic equations, calculus problems, or geometric proofs",
                "sample_instructions": "Explain the mathematical concepts shown and provide step-by-step solutions"
            },
            {
                "title": "Scientific Diagrams", 
                "description": "Analyze cell structures, physics diagrams, or chemistry molecular drawings",
                "sample_instructions": "Identify the scientific components and explain their functions"
            },
            {
                "title": "Hand-drawn Charts",
                "description": "Process graphs, flowcharts, or data visualizations",
                "sample_instructions": "Interpret the data and explain the relationships shown"
            }
        ],
        "draw_in_air_examples": [
            {
                "title": "Geometric Shapes",
                "description": "Draw circles, triangles, rectangles in the air to learn about their properties",
                "learning_outcome": "Understanding geometric properties and calculations"
            },
            {
                "title": "Mathematical Functions",
                "description": "Trace function curves to explore mathematical relationships",
                "learning_outcome": "Visualizing mathematical concepts through gesture"
            },
            {
                "title": "Scientific Processes",
                "description": "Draw molecular structures or process flows",
                "learning_outcome": "Interactive learning of scientific concepts"
            }
        ],
        "plot_crafter_examples": [
            {
                "title": "Mathematical Adventure",
                "prompt": "A student discovers the golden ratio in nature",
                "educational_topic": "Mathematics - Golden Ratio and Fibonacci Sequence"
            },
            {
                "title": "Science Mystery",
                "prompt": "Solving a mystery using chemistry knowledge",
                "educational_topic": "Chemistry - Chemical Reactions and Analysis"
            },
            {
                "title": "Historical Journey",
                "prompt": "Time travel to learn about ancient civilizations",
                "educational_topic": "History - Ancient Civilizations and Culture"
            }
        ]
    }


@router.post("/magic-learn/feedback")
async def submit_feedback(
    session_id: str,
    rating: int,
    feedback_text: Optional[str] = None,
    user_id: Optional[str] = None
):
    """Submit feedback for a Magic Learn session"""
    try:
        # Validate rating
        if not 1 <= rating <= 5:
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
        
        # Update session with feedback
        await analytics_service.update_session(session_id, {
            "feedback_rating": rating,
            "feedback_text": feedback_text,
            "feedback_submitted_at": time.time()
        })
        
        return {
            "success": True,
            "message": "Feedback submitted successfully",
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting feedback: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Feedback submission failed: {str(e)}")


# Error handlers
@router.exception_handler(Exception)
async def magic_learn_exception_handler(request, exc):
    """Global exception handler for Magic Learn endpoints"""
    logger.error(f"Unhandled exception in Magic Learn: {str(exc)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "MAGIC_LEARN_ERROR",
                "message": "An error occurred in Magic Learn services",
                "details": str(exc)
            }
        }
    )