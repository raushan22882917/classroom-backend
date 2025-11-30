"""Homework assistant endpoints"""

from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from app.models.doubt import (
    HomeworkSession,
    HintRequest,
    HintResponse,
    HomeworkStartRequest,
    HomeworkStartResponse,
    HomeworkAttemptRequest,
    HomeworkAttemptResponse
)
from app.services.homework_service import homework_service
from app.utils.exceptions import APIException

router = APIRouter(prefix="/homework", tags=["Homework Assistant"])


@router.post("/start", response_model=HomeworkStartResponse)
async def start_homework_session(request: HomeworkStartRequest):
    """
    Start a new homework session
    
    Args:
        request: Homework start request with question and user details
        
    Returns:
        HomeworkStartResponse with session ID and instructions
    """
    try:
        if not request.user_id or not request.user_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID is required"
            )
        
        if not request.question or not request.question.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question is required"
            )
        
        response = await homework_service.start_homework_session(request)
        return response
        
    except APIException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start homework session: {str(e)}"
        )


@router.post("/hint", response_model=HintResponse)
async def get_hint(request: HintRequest):
    """
    Get a hint for the homework problem
    
    Hints are graduated in 3 levels:
    - Level 1: Basic hint pointing in the right direction
    - Level 2: Detailed hint with approach and method
    - Level 3: Complete solution with step-by-step explanation
    
    Args:
        request: Hint request with session ID and optional hint level
        
    Returns:
        HintResponse with hint text
    """
    try:
        if not request.session_id or not request.session_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session ID is required"
            )
        
        # Validate hint level if provided
        if request.hint_level < 1 or request.hint_level > 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hint level must be between 1 and 3"
            )
        
        response = await homework_service.get_hint(
            session_id=request.session_id,
            hint_level=request.hint_level
        )
        return response
        
    except APIException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    except Exception as e:
        import traceback
        error_detail = str(e)
        print(f"[HomeworkRouter] ERROR in get_hint endpoint: {error_detail}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get hint: {error_detail}"
        )


@router.post("/attempt", response_model=HomeworkAttemptResponse)
async def submit_attempt(request: HomeworkAttemptRequest):
    """
    Submit an answer attempt for homework
    
    The system will:
    - Evaluate the answer using Gemini (and Wolfram for numerical questions)
    - Provide constructive feedback
    - Track the number of attempts
    - Reveal the solution after 3 attempts or correct answer
    
    Args:
        request: Homework attempt request with session ID and answer
        
    Returns:
        HomeworkAttemptResponse with evaluation feedback
    """
    try:
        if not request.session_id or not request.session_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session ID is required"
            )
        
        if not request.answer or not request.answer.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Answer is required"
            )
        
        response = await homework_service.submit_attempt(request)
        return response
        
    except APIException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit attempt: {str(e)}"
        )


@router.get("/session/{session_id}", response_model=HomeworkSession)
async def get_session(session_id: str):
    """
    Get homework session details
    
    Args:
        session_id: Homework session ID
        
    Returns:
        HomeworkSession with all session details
    """
    try:
        if not session_id or not session_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session ID is required"
            )
        
        session = await homework_service.get_session(session_id)
        return session
        
    except APIException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session: {str(e)}"
        )


@router.get("/sessions", response_model=List[HomeworkSession])
async def get_user_sessions(
    user_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Get homework sessions - all sessions if user_id is not provided, or filtered by user_id
    
    Args:
        user_id: Optional User ID (if not provided, returns all sessions)
        limit: Number of records to fetch (default: 100)
        offset: Offset for pagination (default: 0)
        
    Returns:
        List of HomeworkSession objects
    """
    try:
        if limit < 1 or limit > 1000:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 1000"
            )
        
        # If user_id is provided, filter by user, otherwise get all
        if user_id and user_id.strip():
            sessions = await homework_service.get_user_sessions(
                user_id=user_id,
                limit=limit,
                offset=offset
            )
        else:
            sessions = await homework_service.get_all_sessions(
                limit=limit,
                offset=offset
            )
        
        return sessions
        
    except APIException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sessions: {str(e)}"
        )
