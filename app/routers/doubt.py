"""Doubt solver endpoints"""

from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form, Query
from typing import Optional, List
from app.models.doubt import (
    DoubtResponse,
    DoubtType
)
from app.models.base import Subject, BaseResponse
from app.services.doubt_solver_service import doubt_solver_service
from app.utils.exceptions import APIException

router = APIRouter(prefix="/doubt", tags=["Doubt Solver"])


@router.post("/text", response_model=DoubtResponse)
async def process_text_doubt(
    user_id: str = Query(..., description="User ID submitting the doubt"),
    text: str = Query(..., description="Question text"),
    subject: Optional[Subject] = Query(None, description="Optional subject hint")
):
    """
    Process a text-based doubt query
    
    Args:
        user_id: User ID submitting the doubt
        text: Question text
        subject: Optional subject hint
        
    Returns:
        DoubtResponse with NCERT summary, solved example, PYQ, and HOTS question
    """
    try:
        if not text or not text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question text cannot be empty"
            )
        
        if not user_id or not user_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID is required"
            )
        
        response = await doubt_solver_service.process_text_doubt(
            user_id=user_id,
            text=text,
            subject=subject
        )
        
        return response
        
    except APIException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )
    except Exception as e:
        import logging
        import traceback
        logger = logging.getLogger(__name__)
        logger.error(f"Error processing text doubt: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process text doubt: {str(e)}"
        )


@router.post("/image", response_model=DoubtResponse)
async def process_image_doubt(
    user_id: str = Form(...),
    image: UploadFile = File(...),
    subject: Optional[Subject] = Form(None)
):
    """
    Process an image-based doubt query
    
    Args:
        user_id: User ID submitting the doubt
        image: Image file containing the question
        subject: Optional subject hint
        
    Returns:
        DoubtResponse with NCERT summary, solved example, PYQ, and HOTS question
    """
    try:
        if not user_id or not user_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID is required"
            )
        
        # Validate file type
        allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/webp"]
        if image.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types: {', '.join(allowed_types)}"
            )
        
        # Read image bytes
        image_bytes = await image.read()
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(image_bytes) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image file too large. Maximum size is 10MB"
            )
        
        response = await doubt_solver_service.process_image_doubt(
            user_id=user_id,
            image_bytes=image_bytes,
            subject=subject
        )
        
        return response
        
    except APIException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process image doubt: {str(e)}"
        )


@router.post("/voice", response_model=DoubtResponse)
async def process_voice_doubt(
    user_id: str = Form(...),
    audio: UploadFile = File(...),
    subject: Optional[Subject] = Form(None)
):
    """
    Process a voice-based doubt query
    
    Args:
        user_id: User ID submitting the doubt
        audio: Audio file containing the question
        subject: Optional subject hint
        
    Returns:
        DoubtResponse with NCERT summary, solved example, PYQ, and HOTS question
    """
    try:
        if not user_id or not user_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID is required"
            )
        
        # Validate file type
        allowed_types = ["audio/wav", "audio/wave", "audio/x-wav", "audio/mpeg", "audio/mp3", "audio/webm", "audio/ogg"]
        if audio.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed types: wav, mp3, webm, ogg"
            )
        
        # Read audio bytes
        audio_bytes = await audio.read()
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(audio_bytes) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audio file too large. Maximum size is 10MB"
            )
        
        # Determine audio format from filename
        audio_format = "wav"
        if audio.filename:
            ext = audio.filename.split(".")[-1].lower()
            if ext in ["mp3", "wav", "webm", "ogg", "flac"]:
                audio_format = ext
        
        response = await doubt_solver_service.process_voice_doubt(
            user_id=user_id,
            audio_bytes=audio_bytes,
            audio_format=audio_format,
            subject=subject
        )
        
        return response
        
    except APIException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process voice doubt: {str(e)}"
        )


@router.get("/history", response_model=List[dict])
async def get_doubt_history(
    user_id: str,
    limit: int = 20,
    offset: int = 0
):
    """
    Get doubt history for a user
    
    Args:
        user_id: User ID
        limit: Number of records to fetch (default: 20)
        offset: Offset for pagination (default: 0)
        
    Returns:
        List of doubt records
    """
    try:
        if not user_id or not user_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID is required"
            )
        
        history = await doubt_solver_service.get_doubt_history(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        return history
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch doubt history: {str(e)}"
        )


@router.post("/wolfram/chat")
async def wolfram_chat(
    query: str = Query(..., description="Query for Wolfram Alpha"),
    include_steps: bool = Query(True, description="Include step-by-step solution")
):
    """
    Chat with Wolfram Alpha for mathematical and scientific queries
    
    Args:
        query: Query text for Wolfram Alpha
        include_steps: Whether to include step-by-step solution
        
    Returns:
        Dictionary with solution, steps, and metadata
    """
    try:
        print(f"🔍 Wolfram chat request: query='{query}', include_steps={include_steps}")
        
        if not query or not query.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query cannot be empty"
            )
        
        # Import wolfram service
        try:
            from app.services.wolfram_service import wolfram_service
        except ImportError as e:
            print(f"❌ Failed to import wolfram_service: {e}")
            return {
                "success": False,
                "query": query,
                "error": "Wolfram Alpha service is not available. Please check the service configuration.",
                "result": None
            }
        
        # Check if wolfram service is properly configured
        if not hasattr(wolfram_service, 'solve_math_problem'):
            print("❌ Wolfram service not properly initialized")
            return {
                "success": False,
                "query": query,
                "error": "Wolfram Alpha service is not properly configured.",
                "result": None
            }
        
        result = await wolfram_service.solve_math_problem(
            query=query,
            include_steps=include_steps
        )
        
        print(f"📊 Wolfram result: {result}")
        
        if result is None:
            return {
                "success": False,
                "query": query,
                "error": "Wolfram Alpha service is currently unavailable. Please try again later.",
                "result": None
            }
        
        # Check if result has an error (but not boolean False)
        error_msg = result.get("error")
        if error_msg and error_msg is not False and str(error_msg).strip() and str(error_msg) != "False":
            return {
                "success": False,
                "query": query,
                "result": result,
                "error": str(error_msg) if not isinstance(error_msg, str) else error_msg
            }
        
        # Check if we have an answer/solution
        if not result.get("answer") and not result.get("solution"):
            return {
                "success": False,
                "query": query,
                "result": result,
                "error": "No solution found for this query. Please try rephrasing your question."
            }
        
        return {
            "success": True,
            "query": query,
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Wolfram chat error: {str(e)}")
        print(f"Traceback: {error_trace}")
        
        return {
            "success": False,
            "query": query,
            "error": f"Failed to process Wolfram query: {str(e)}",
            "result": None
        }
