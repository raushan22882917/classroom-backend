"""Exam mode endpoints for timed tests and exam sets"""

from fastapi import APIRouter, Query, HTTPException, Depends, Request
from typing import Optional, List
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.exam import (
    ExamSet,
    ExamSetCreate,
    TestSession,
    TestSessionCreate,
    AnswerSubmission,
    TestResult,
    PerformanceTrend
)
from app.models.base import Subject
from app.services.exam_service import exam_service
from app.utils.exceptions import APIException

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/exam/sets", response_model=List[ExamSet])
@limiter.limit("100/minute")
async def get_exam_sets(
    request: Request,
    subject: Optional[Subject] = Query(None, description="Filter by subject"),
    year: Optional[int] = Query(None, description="Filter by year", ge=2000, le=2100),
    limit: int = Query(50, description="Maximum number of results", ge=1, le=100),
    offset: int = Query(0, description="Pagination offset", ge=0)
):
    """
    Get available exam sets with optional filtering
    
    Returns exam sets organized by subject and year, containing PYQ questions.
    Each exam set includes duration, total marks, and questions.
    
    Query Parameters:
    - subject: Filter by specific subject (mathematics, physics, chemistry, biology)
    - year: Filter by specific year (2000-2100)
    - limit: Maximum number of exam sets to return (default: 50, max: 100)
    - offset: Pagination offset (default: 0)
    
    Returns:
    - List of exam sets with questions, duration, and marks
    """
    try:
        exam_sets = await exam_service.get_exam_sets(
            subject=subject,
            year=year,
            limit=limit,
            offset=offset
        )
        
        return exam_sets
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exam/sets/{exam_set_id}", response_model=ExamSet)
@limiter.limit("100/minute")
async def get_exam_set(request: Request, exam_set_id: str):
    """
    Get a specific exam set by ID
    
    Path Parameters:
    - exam_set_id: Exam set identifier (format: subject_year, e.g., mathematics_2023)
    
    Returns:
    - Exam set with all questions and details
    """
    try:
        exam_set = await exam_service.get_exam_set_by_id(exam_set_id)
        
        if not exam_set:
            raise HTTPException(
                status_code=404,
                detail=f"Exam set {exam_set_id} not found"
            )
        
        return exam_set
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/exam/sets", response_model=ExamSet, status_code=201)
@limiter.limit("10/minute")
async def create_exam_set(request: Request, exam_set_create: ExamSetCreate):
    """
    Create a new exam set (admin or teacher)
    
    Request Body:
    - subject: Subject for the exam set
    - year: Year of the exam
    - duration_minutes: Duration in minutes
    - total_marks: Total marks for the exam
    - questions: List of questions with solutions
    - metadata: Additional metadata
    
    Returns:
    - Created exam set
    """
    try:
        exam_set = await exam_service.create_exam_set(exam_set_create)
        return exam_set
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/exam/start", response_model=TestSession, status_code=201)
@limiter.limit("20/minute")
async def start_test_session(request: Request, session_create: TestSessionCreate):
    """
    Start a new timed test session
    
    Request Body:
    - user_id: Student user ID
    - exam_set_id: Optional exam set ID to use
    - subject: Subject for the test
    - duration_minutes: Optional custom duration
    - total_marks: Optional custom total marks
    
    Returns:
    - Created test session with start time and session ID
    """
    try:
        session = await exam_service.start_test_session(session_create)
        return session
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        import traceback
        error_detail = str(e)
        traceback.print_exc()
        print(f"Error in start_test_session endpoint: {error_detail}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {error_detail}")


@router.put("/exam/answer", response_model=TestSession)
@limiter.limit("100/minute")
async def save_answer(
    request: Request,
    session_id: str = Query(..., description="Test session ID"),
    user_id: str = Query(..., description="User ID"),
    answer_submission: AnswerSubmission = ...
):
    """
    Save an answer during a test session
    
    Query Parameters:
    - session_id: Test session ID
    - user_id: User ID for verification
    
    Request Body:
    - question_id: ID of the question being answered
    - answer: Student's answer text
    - timestamp: Time of submission
    
    Returns:
    - Updated test session
    
    Notes:
    - Automatically submits test if time limit is exceeded
    - Cannot save answers after test is completed
    """
    try:
        session = await exam_service.save_answer(
            session_id=session_id,
            user_id=user_id,
            answer_submission=answer_submission
        )
        return session
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        import traceback
        error_detail = str(e)
        traceback.print_exc()
        print(f"Error in save_answer endpoint: {error_detail}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {error_detail}")


@router.post("/exam/submit", response_model=TestSession)
@limiter.limit("20/minute")
async def submit_test(
    request: Request,
    session_id: str = Query(..., description="Test session ID"),
    user_id: str = Query(..., description="User ID")
):
    """
    Submit a test session for evaluation
    
    Query Parameters:
    - session_id: Test session ID
    - user_id: User ID for verification
    
    Returns:
    - Completed test session with calculated score
    
    Notes:
    - Uses Gemini AI to evaluate subjective answers
    - Calculates total score based on marking rubric
    - Marks session as completed
    """
    try:
        session = await exam_service.submit_test(
            session_id=session_id,
            user_id=user_id
        )
        return session
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exam/results/{session_id}", response_model=TestResult)
@limiter.limit("50/minute")
async def get_test_results(
    request: Request,
    session_id: str,
    user_id: str = Query(..., description="User ID")
):
    """
    Get detailed test results with model answers and marking breakdown
    
    Path Parameters:
    - session_id: Test session ID
    
    Query Parameters:
    - user_id: User ID for verification
    
    Returns:
    - Detailed test results including:
      - Score and percentage
      - Time taken
      - Question-by-question breakdown
      - Model answers
      - Marking rubric
    """
    try:
        results = await exam_service.get_test_results(
            session_id=session_id,
            user_id=user_id
        )
        return results
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exam/history", response_model=PerformanceTrend)
@limiter.limit("50/minute")
async def get_test_history(
    request: Request,
    user_id: str = Query(..., description="User ID"),
    subject: Optional[Subject] = Query(None, description="Filter by subject"),
    limit: int = Query(20, description="Maximum number of sessions", ge=1, le=100)
):
    """
    Get test history and performance trends
    
    Query Parameters:
    - user_id: User ID
    - subject: Optional subject filter
    - limit: Maximum number of test sessions to retrieve (default: 20, max: 100)
    
    Returns:
    - Performance trend data including:
      - Historical test sessions
      - Average score
      - Improvement rate
      - Identified strengths and weaknesses
    """
    try:
        trend = await exam_service.get_test_history(
            user_id=user_id,
            subject=subject,
            limit=limit
        )
        return trend
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
