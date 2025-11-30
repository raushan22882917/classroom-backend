"""Quiz endpoints for quiz sessions"""

from fastapi import APIRouter, Query, HTTPException, Request
from typing import Optional
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.quiz import (
    QuizSession,
    QuizSessionCreate,
    QuizAnswerSubmission,
    QuizResult
)
from app.services.quiz_service import QuizService
from app.utils.exceptions import APIException

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# Initialize quiz service
quiz_service = QuizService()


@router.post("/quiz/start", response_model=QuizSession, status_code=201)
@limiter.limit("20/minute")
async def start_quiz_session(request: Request, quiz_create: QuizSessionCreate):
    """
    Start a new quiz session
    
    Creates a new quiz session from quiz data (typically from a microplan).
    The quiz session tracks answers, time, and completion status.
    
    Request Body:
    - user_id: User ID starting the quiz
    - microplan_id: Optional microplan ID this quiz belongs to
    - quiz_data: Quiz data containing questions, answers, etc.
    - subject: Subject of the quiz
    - duration_minutes: Optional duration (auto-calculated if not provided)
    - total_marks: Optional total marks (auto-calculated if not provided)
    
    Returns:
    - QuizSession object with session ID and details
    """
    try:
        session = await quiz_service.start_quiz_session(quiz_create)
        return session
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/quiz/answer", response_model=QuizSession)
@limiter.limit("100/minute")
async def save_answer(
    request: Request,
    session_id: str = Query(..., description="Quiz session ID"),
    user_id: str = Query(..., description="User ID"),
    answer_submission: QuizAnswerSubmission = ...
):
    """
    Save an answer during a quiz session
    
    Saves a single answer for a question in the quiz. Answers are saved
    incrementally so users can come back to questions later.
    
    Query Parameters:
    - session_id: Quiz session ID
    - user_id: User ID for verification
    
    Request Body:
    - question_id: ID of the question being answered
    - answer: Student's answer text
    - timestamp: Time of submission
    
    Returns:
    - Updated quiz session
    
    Notes:
    - Automatically submits quiz if time limit is exceeded
    - Cannot save answers after quiz is completed
    """
    try:
        session = await quiz_service.save_answer(
            session_id=session_id,
            user_id=user_id,
            answer_submission=answer_submission
        )
        return session
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quiz/submit", response_model=QuizResult)
@limiter.limit("20/minute")
async def submit_quiz(
    request: Request,
    session_id: str = Query(..., description="Quiz session ID"),
    user_id: str = Query(..., description="User ID")
):
    """
    Submit a quiz session and get results
    
    Submits the quiz, calculates scores, and returns detailed results
    including correct/incorrect answers and feedback.
    
    Query Parameters:
    - session_id: Quiz session ID
    - user_id: User ID for verification
    
    Returns:
    - QuizResult with score, percentage, and question-by-question feedback
    
    Notes:
    - Quiz cannot be submitted twice
    - All answers are evaluated automatically
    """
    try:
        result = await quiz_service.submit_quiz(session_id, user_id)
        return result
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quiz/session/{session_id}", response_model=QuizSession)
@limiter.limit("100/minute")
async def get_quiz_session(
    request: Request,
    session_id: str,
    user_id: str = Query(..., description="User ID")
):
    """
    Get a quiz session by ID
    
    Retrieves quiz session details including current answers and status.
    
    Path Parameters:
    - session_id: Quiz session ID
    
    Query Parameters:
    - user_id: User ID for verification
    
    Returns:
    - QuizSession object
    """
    try:
        session = await quiz_service.get_session(session_id, user_id)
        return session
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))






