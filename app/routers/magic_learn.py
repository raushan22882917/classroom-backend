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
    plot_crafter_service,
    analytics_service
)
from app.services.draw_in_air_service import draw_in_air_service

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


@router.get("/magic-learn/cors-test")
async def cors_test():
    """Simple CORS test endpoint"""
    return {
        "message": "CORS test successful",
        "timestamp": time.time(),
        "status": "ok"
    }


@router.options("/magic-learn/{path:path}")
async def magic_learn_options_handler(path: str):
    """Handle OPTIONS requests for Magic Learn endpoints"""
    from fastapi import Response
    
    response = Response()
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Accept, Origin, X-Requested-With"
    response.headers["Access-Control-Max-Age"] = "3600"
    
    return response


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


# DrawInAir endpoints with MediaPipe integration

@router.post("/magic-learn/draw-in-air/start")
async def start_draw_in_air():
    """Start DrawInAir session with MediaPipe hand tracking"""
    try:
        result = await draw_in_air_service.start_session()
        
        if result['success']:
            # Create session for tracking
            session_id = await analytics_service.create_session(
                user_id=None,
                tool_used="draw_in_air"
            )
            result['session_id'] = session_id
        
        return result
        
    except Exception as e:
        logger.error(f"Error starting DrawInAir: {str(e)}")
        return {"success": False, "error": str(e)}


@router.post("/magic-learn/draw-in-air/process-frame")
async def process_draw_in_air_frame(request: dict):
    """Process video frame with hand tracking and gesture recognition"""
    try:
        frame_data = request.get('frame')
        if not frame_data:
            return {"success": False, "error": "No frame data provided"}
        
        result = await draw_in_air_service.process_frame(frame_data)
        return result
        
    except Exception as e:
        logger.error(f"Error processing DrawInAir frame: {str(e)}")
        return {"success": False, "error": str(e)}


@router.post("/magic-learn/draw-in-air/analyze")
async def analyze_draw_in_air_drawing(request: dict):
    """Analyze drawn content with Gemini AI"""
    try:
        image_data = request.get('image')
        if not image_data:
            return {"success": False, "error": "No image data provided"}
        
        # Create session for tracking
        session_id = await analytics_service.create_session(
            user_id=request.get('user_id'),
            tool_used="draw_in_air_analysis"
        )
        
        result = await draw_in_air_service.analyze_drawing(image_data)
        
        # Update session with results
        await analytics_service.update_session(session_id, {
            "analysis_success": result['success'],
            "has_content": bool(image_data)
        })
        
        logger.info(f"DrawInAir analysis completed - Session: {session_id}, Success: {result['success']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing DrawInAir drawing: {str(e)}")
        return {"success": False, "error": str(e)}


@router.post("/magic-learn/draw-in-air/clear")
async def clear_draw_in_air_canvas():
    """Clear DrawInAir canvas"""
    try:
        result = await draw_in_air_service.clear_canvas()
        return result
        
    except Exception as e:
        logger.error(f"Error clearing DrawInAir canvas: {str(e)}")
        return {"success": False, "error": str(e)}


@router.post("/magic-learn/draw-in-air/stop")
async def stop_draw_in_air():
    """Stop DrawInAir session and cleanup resources"""
    try:
        result = await draw_in_air_service.stop_session()
        return result
        
    except Exception as e:
        logger.error(f"Error stopping DrawInAir: {str(e)}")
        return {"success": False, "error": str(e)}


@router.get("/magic-learn/draw-in-air/gesture")
async def get_current_gesture():
    """Get current hand gesture"""
    try:
        return {
            "success": True,
            "gesture": draw_in_air_service.current_gesture
        }
    except Exception as e:
        logger.error(f"Error getting current gesture: {str(e)}")
        return {"success": False, "error": str(e)}


# Legacy gesture recognition endpoint (for backward compatibility)
@router.post("/magic-learn/draw-in-air/recognize", response_model=GestureRecognitionResponse)
async def recognize_gestures(request: GestureRecognitionRequest):
    """
    Legacy endpoint for gesture recognition from coordinate points
    
    Note: The new DrawInAir service uses real-time MediaPipe processing.
    This endpoint is maintained for backward compatibility.
    """
    try:
        # Create session for tracking
        session_id = await analytics_service.create_session(
            user_id=request.user_id,
            tool_used="draw_in_air_legacy"
        )
        
        # Use the original gesture recognition service for coordinate-based analysis
        from app.services.magic_learn_service import draw_in_air_service as legacy_service
        result = await legacy_service.recognize_gestures(request)
        
        # Update session with results
        await analytics_service.update_session(session_id, {
            "gesture_points_count": len(request.gesture_points),
            "canvas_size": f"{request.canvas_width}x{request.canvas_height}",
            "success": result.success,
            "recognized_shapes_count": len(result.recognized_shapes),
            "shapes_detected": [shape.shape_type for shape in result.recognized_shapes]
        })
        
        logger.info(f"Legacy gesture recognition completed - Session: {session_id}, Success: {result.success}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in legacy gesture recognition: {str(e)}")
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
    Generate educational stories with AI-powered visualizations using Gemini API
    
    Creates interactive learning experiences through story-based content
    with educational objectives and visual elements.
    """
    try:
        # Create session for tracking
        session_id = await analytics_service.create_session(
            user_id=request.user_id,
            tool_used="plot_crafter"
        )
        
        # Generate story with Gemini API
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
            story=GeneratedStory(
                title="Error",
                content="Story generation failed",
                characters=[],
                settings=[],
                educational_elements=[],
                learning_objectives=[]
            ),
            visualization_prompts=[],
            interactive_elements=[],
            error=f"Story generation failed: {str(e)}"
        )


@router.post("/magic-learn/plot-crafter/generate-simple")
async def generate_simple_explanation(request: dict):
    """
    Generate concise real-life example explanation using Gemini API
    
    This endpoint matches the Flask app's approach of providing short,
    interactive real-life examples for educational concepts.
    """
    try:
        theme = request.get('theme')
        if not theme:
            return {"success": False, "error": "No theme provided"}
        
        # Create session for tracking
        session_id = await analytics_service.create_session(
            user_id=request.get('user_id'),
            tool_used="plot_crafter_simple"
        )
        
        # Use Gemini API for simple explanation
        import google.generativeai as genai
        import os
        
        GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
        if not GEMINI_API_KEY:
            return {"success": False, "error": "Gemini API key not configured"}
        
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        
        prompt = f"""Explain the concept "{theme}" using a SINGLE real-life example in simple, interactive language.

CRITICAL REQUIREMENTS:
- Use ONLY ONE PARAGRAPH (maximum 4-5 sentences)
- Explain with a relatable, everyday real-life scenario
- Use simple, conversational language that anyone can understand
- Make it interactive and engaging
- DO NOT write a long story - just one clear, concise example
- Focus on helping the user understand the concept quickly

Example format: "Imagine you're [everyday scenario]. This is exactly how [concept] works because [simple explanation]."

Topic: {theme}

Provide your ONE PARAGRAPH real-life example explanation:"""

        response = model.generate_content([prompt])
        
        # Update session with results
        await analytics_service.update_session(session_id, {
            "theme": theme,
            "success": True,
            "response_length": len(response.text)
        })
        
        return {
            "success": True,
            "result": response.text
        }
        
    except Exception as e:
        logger.error(f"Error in simple explanation generation: {str(e)}")
        return {"success": False, "error": str(e)}


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
                "title": "Hand Gesture Drawing",
                "description": "Use MediaPipe hand tracking to draw in the air with natural gestures",
                "gestures": {
                    "Drawing": "Thumb + Index finger extended",
                    "Moving": "Thumb + Index + Middle finger extended", 
                    "Erasing": "Thumb + Middle finger extended",
                    "Clearing": "Thumb + Pinky finger extended",
                    "Analyzing": "Index + Middle finger extended (no thumb)"
                },
                "learning_outcome": "Interactive gesture-based learning with real-time feedback"
            },
            {
                "title": "Mathematical Equations",
                "description": "Draw equations in the air and get AI analysis with step-by-step solutions",
                "example": "Draw 'x² + 5x + 6 = 0' and get factoring explanation",
                "learning_outcome": "Visual mathematics with immediate AI feedback"
            },
            {
                "title": "Geometric Shapes",
                "description": "Draw shapes and get instant property calculations",
                "example": "Draw a triangle and learn about area, perimeter, and angles",
                "learning_outcome": "Interactive geometry with real-time analysis"
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


# Advanced Magic Learn Endpoints

@router.post("/magic-learn/batch-analysis")
async def batch_analyze_images(request: dict):
    """Analyze multiple images in batch with parallel processing"""
    try:
        from app.services.advanced_magic_learn_service import advanced_image_service
        from app.models.magic_learn import BatchAnalysisRequest
        
        batch_request = BatchAnalysisRequest(**request)
        result = await advanced_image_service.analyze_batch(batch_request)
        
        logger.info(f"Batch analysis completed - Batch ID: {result.batch_id}, Success: {result.success}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in batch analysis: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return {
            "success": False,
            "batch_id": "",
            "results": [],
            "summary": "Batch analysis failed",
            "total_processing_time": 0.0,
            "error": str(e)
        }


@router.post("/magic-learn/realtime/start")
async def start_realtime_analysis(stream_id: str):
    """Start a real-time analysis stream"""
    try:
        from app.services.advanced_magic_learn_service import realtime_service
        
        result = await realtime_service.start_stream(stream_id)
        return result
        
    except Exception as e:
        logger.error(f"Error starting real-time analysis: {str(e)}")
        return {"success": False, "error": str(e)}


@router.post("/magic-learn/realtime/process")
async def process_realtime_frame(request: dict):
    """Process a frame in real-time analysis stream"""
    try:
        from app.services.advanced_magic_learn_service import realtime_service
        from app.models.magic_learn import RealTimeAnalysisRequest
        
        rt_request = RealTimeAnalysisRequest(**request)
        result = await realtime_service.process_frame(rt_request)
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing real-time frame: {str(e)}")
        return {
            "success": False,
            "stream_id": request.get("stream_id", ""),
            "frame_number": 0,
            "analysis": f"Processing failed: {str(e)}",
            "confidence": 0.0,
            "detected_objects": [],
            "timestamp": time.time()
        }


@router.post("/magic-learn/realtime/stop")
async def stop_realtime_analysis(stream_id: str):
    """Stop a real-time analysis stream"""
    try:
        from app.services.advanced_magic_learn_service import realtime_service
        
        result = await realtime_service.stop_stream(stream_id)
        return result
        
    except Exception as e:
        logger.error(f"Error stopping real-time analysis: {str(e)}")
        return {"success": False, "error": str(e)}


# Collaborative Learning Endpoints

@router.post("/magic-learn/collaborate/create")
async def create_collaborative_session(request: dict):
    """Create a new collaborative learning session"""
    try:
        from app.services.collaborative_learning_service import collaborative_service
        from app.models.magic_learn import CollaborativeSessionRequest
        
        collab_request = CollaborativeSessionRequest(**request)
        result = await collaborative_service.create_session(collab_request)
        
        logger.info(f"Collaborative session created - Session ID: {result.session_id}, Success: {result.success}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error creating collaborative session: {str(e)}")
        return {
            "success": False,
            "session_id": "",
            "join_code": "",
            "session_url": "",
            "expires_at": time.time()
        }


@router.post("/magic-learn/collaborate/join")
async def join_collaborative_session(session_id: str, user_id: str, join_code: str):
    """Join an existing collaborative session"""
    try:
        from app.services.collaborative_learning_service import collaborative_service
        
        result = await collaborative_service.join_session(session_id, user_id, join_code)
        return result
        
    except Exception as e:
        logger.error(f"Error joining collaborative session: {str(e)}")
        return {"success": False, "error": str(e)}


@router.post("/magic-learn/collaborate/leave")
async def leave_collaborative_session(session_id: str, user_id: str):
    """Leave a collaborative session"""
    try:
        from app.services.collaborative_learning_service import collaborative_service
        
        result = await collaborative_service.leave_session(session_id, user_id)
        return result
        
    except Exception as e:
        logger.error(f"Error leaving collaborative session: {str(e)}")
        return {"success": False, "error": str(e)}


@router.post("/magic-learn/collaborate/update-state")
async def update_participant_state(session_id: str, user_id: str, state_update: dict):
    """Update participant state in collaborative session"""
    try:
        from app.services.collaborative_learning_service import collaborative_service
        
        result = await collaborative_service.update_participant_state(session_id, user_id, state_update)
        return result
        
    except Exception as e:
        logger.error(f"Error updating participant state: {str(e)}")
        return {"success": False, "error": str(e)}


@router.post("/magic-learn/collaborate/chat")
async def send_chat_message(session_id: str, user_id: str, message: str):
    """Send a chat message in collaborative session"""
    try:
        from app.services.collaborative_learning_service import collaborative_service
        
        result = await collaborative_service.send_chat_message(session_id, user_id, message)
        return result
        
    except Exception as e:
        logger.error(f"Error sending chat message: {str(e)}")
        return {"success": False, "error": str(e)}


@router.get("/magic-learn/collaborate/state")
async def get_session_state(session_id: str, user_id: str):
    """Get current session state for a participant"""
    try:
        from app.services.collaborative_learning_service import collaborative_service
        
        result = await collaborative_service.get_session_state(session_id, user_id)
        return result
        
    except Exception as e:
        logger.error(f"Error getting session state: {str(e)}")
        return {"success": False, "error": str(e)}


# AI Tutor Endpoints

@router.post("/magic-learn/ai-tutor/chat")
async def chat_with_ai_tutor(request: dict):
    """Have a conversation with the AI tutor"""
    try:
        from app.services.collaborative_learning_service import ai_tutor_service
        from app.models.magic_learn import AITutorRequest
        
        tutor_request = AITutorRequest(**request)
        result = await ai_tutor_service.chat_with_tutor(tutor_request)
        
        logger.info(f"AI tutor interaction - User: {tutor_request.user_id}, Success: {result.success}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in AI tutor chat: {str(e)}")
        return {
            "success": False,
            "response": f"I apologize, but I encountered an error: {str(e)}",
            "explanation_type": "error",
            "follow_up_questions": [],
            "related_concepts": [],
            "practice_problems": [],
            "confidence_score": 0.0
        }


# Learning Path Endpoints

@router.post("/magic-learn/learning-path/generate")
async def generate_learning_path(request: dict):
    """Generate a personalized learning path"""
    try:
        from app.services.learning_path_service import learning_path_service
        from app.models.magic_learn import LearningPathRequest
        
        path_request = LearningPathRequest(**request)
        result = await learning_path_service.generate_learning_path(path_request)
        
        logger.info(f"Learning path generated - Path ID: {result.path_id}, Success: {result.success}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating learning path: {str(e)}")
        return {
            "success": False,
            "path_id": "",
            "milestones": [],
            "estimated_duration": 0,
            "recommended_activities": [],
            "progress_tracking": {}
        }


@router.get("/magic-learn/learning-path/{path_id}")
async def get_learning_path(path_id: str):
    """Get a learning path by ID"""
    try:
        from app.services.learning_path_service import learning_path_service
        
        path = await learning_path_service.get_learning_path(path_id)
        
        if path:
            return {"success": True, "learning_path": path}
        else:
            return {"success": False, "error": "Learning path not found"}
        
    except Exception as e:
        logger.error(f"Error getting learning path: {str(e)}")
        return {"success": False, "error": str(e)}


# Progress Tracking Endpoints

@router.post("/magic-learn/progress/track")
async def track_progress(request: dict):
    """Track user learning progress"""
    try:
        from app.services.learning_path_service import progress_tracking_service
        from app.models.magic_learn import ProgressTrackingRequest
        
        progress_request = ProgressTrackingRequest(**request)
        result = await progress_tracking_service.track_progress(progress_request)
        
        logger.info(f"Progress tracked - User: {progress_request.user_id}, Success: {result.success}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error tracking progress: {str(e)}")
        return {
            "success": False,
            "user_id": request.get("user_id", ""),
            "current_level": "unknown",
            "progress_percentage": 0.0,
            "achievements": [],
            "next_recommendations": [],
            "streak_count": 0
        }


@router.get("/magic-learn/progress/{user_id}")
async def get_user_progress(user_id: str):
    """Get user progress data"""
    try:
        from app.services.learning_path_service import progress_tracking_service
        
        progress = await progress_tracking_service.get_user_progress(user_id)
        
        if progress:
            return {"success": True, "progress": progress.__dict__}
        else:
            return {"success": False, "error": "User progress not found"}
        
    except Exception as e:
        logger.error(f"Error getting user progress: {str(e)}")
        return {"success": False, "error": str(e)}


@router.get("/magic-learn/progress/{user_id}/analytics")
async def get_progress_analytics(user_id: str):
    """Get detailed progress analytics"""
    try:
        from app.services.learning_path_service import progress_tracking_service
        
        analytics = await progress_tracking_service.get_progress_analytics(user_id)
        return {"success": True, "analytics": analytics}
        
    except Exception as e:
        logger.error(f"Error getting progress analytics: {str(e)}")
        return {"success": False, "error": str(e)}


# Assessment Endpoints

@router.post("/magic-learn/assessment/generate")
async def generate_assessment(request: dict):
    """Generate a comprehensive assessment"""
    try:
        from app.services.assessment_service import assessment_service
        from app.models.magic_learn import AssessmentRequest
        
        assessment_request = AssessmentRequest(**request)
        result = await assessment_service.generate_assessment(assessment_request)
        
        logger.info(f"Assessment generated - Assessment ID: {result.assessment_id}, Success: {result.success}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating assessment: {str(e)}")
        return {
            "success": False,
            "assessment_id": "",
            "questions": [],
            "time_limit": 0,
            "scoring_rubric": {},
            "learning_objectives": []
        }


@router.post("/magic-learn/assessment/{assessment_id}/submit")
async def submit_assessment(assessment_id: str, user_id: str, answers: dict):
    """Submit and grade an assessment"""
    try:
        from app.services.assessment_service import assessment_service
        
        result = await assessment_service.submit_assessment(assessment_id, user_id, answers)
        
        logger.info(f"Assessment submitted - Assessment ID: {assessment_id}, User: {user_id}, Success: {result['success']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error submitting assessment: {str(e)}")
        return {"success": False, "error": str(e)}


@router.get("/magic-learn/assessment/{assessment_id}")
async def get_assessment(assessment_id: str):
    """Get an assessment by ID"""
    try:
        from app.services.assessment_service import assessment_service
        
        assessment = await assessment_service.get_assessment(assessment_id)
        
        if assessment:
            return {"success": True, "assessment": assessment.__dict__}
        else:
            return {"success": False, "error": "Assessment not found"}
        
    except Exception as e:
        logger.error(f"Error getting assessment: {str(e)}")
        return {"success": False, "error": str(e)}


# Content Generation Endpoints

@router.post("/magic-learn/content/generate")
async def generate_educational_content(request: dict):
    """Generate educational content"""
    try:
        from app.services.assessment_service import content_generation_service
        from app.models.magic_learn import ContentGenerationRequest
        
        content_request = ContentGenerationRequest(**request)
        result = await content_generation_service.generate_content(content_request)
        
        logger.info(f"Content generated - Content ID: {result.content_id}, Success: {result.success}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating content: {str(e)}")
        return {
            "success": False,
            "content_id": "",
            "title": "Content Generation Failed",
            "content": f"Failed to generate content: {str(e)}",
            "metadata": {},
            "interactive_elements": [],
            "assessment_questions": []
        }


@router.get("/magic-learn/content/{content_id}")
async def get_generated_content(content_id: str):
    """Get generated content by ID"""
    try:
        from app.services.assessment_service import content_generation_service
        
        content = await content_generation_service.get_generated_content(content_id)
        
        if content:
            return {"success": True, "content": content}
        else:
            return {"success": False, "error": "Content not found"}
        
    except Exception as e:
        logger.error(f"Error getting generated content: {str(e)}")
        return {"success": False, "error": str(e)}


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