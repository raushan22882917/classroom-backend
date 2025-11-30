"""HOTS (Higher Order Thinking Skills) question endpoints"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel, Field

from app.services.hots_service import hots_service
from app.models.content import HOTSQuestion
from app.utils.exceptions import APIException

router = APIRouter()


class GenerateHOTSRequest(BaseModel):
    """Request model for generating HOTS questions"""
    topic_id: str = Field(..., description="Topic UUID")
    count: int = Field(default=3, ge=1, le=5, description="Number of questions to generate (1-5)")


class GenerateHOTSResponse(BaseModel):
    """Response model for generated HOTS questions"""
    questions: List[HOTSQuestion]
    count: int
    topic_id: str


class SubmitHOTSAttemptRequest(BaseModel):
    """Request model for submitting HOTS attempt"""
    user_id: str = Field(..., description="User UUID")
    question_id: str = Field(..., description="HOTS question UUID")
    answer: str = Field(..., description="Student's answer")
    time_taken_minutes: int = Field(..., ge=0, description="Time taken in minutes")


class SubmitHOTSAttemptResponse(BaseModel):
    """Response model for HOTS attempt submission"""
    question_id: str
    is_correct: bool
    score: int
    feedback: str
    model_solution: str
    mastery_updated: bool


class HOTSPerformanceResponse(BaseModel):
    """Response model for HOTS performance analytics"""
    total_hots_attempted: int
    total_hots_correct: int
    overall_hots_mastery: float
    topics_with_topper_badge: List[dict]
    subject_breakdown: dict


@router.post("/generate", response_model=GenerateHOTSResponse)
async def generate_hots_questions(request: GenerateHOTSRequest):
    """
    Generate HOTS questions for a given topic using Gemini
    
    This endpoint generates 2-3 case-based or application-oriented questions
    that require higher-order thinking skills. Questions are stored in the database
    and associated with the specified topic.
    
    Args:
        request: Generation request with topic_id and count
        
    Returns:
        Generated HOTS questions
        
    Raises:
        404: Topic not found
        500: Generation failed
    """
    try:
        questions = await hots_service.generate_hots_questions(
            topic_id=request.topic_id,
            count=request.count
        )
        
        return GenerateHOTSResponse(
            questions=questions,
            count=len(questions),
            topic_id=request.topic_id
        )
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate HOTS questions: {str(e)}")


@router.get("/topic/{topic_id}", response_model=List[HOTSQuestion])
async def get_hots_by_topic(topic_id: str):
    """
    Fetch HOTS questions for a specific topic
    
    Returns all HOTS questions associated with the given topic,
    ordered by creation date (newest first).
    
    Args:
        topic_id: Topic UUID
        
    Returns:
        List of HOTS questions
        
    Raises:
        500: Fetch failed
    """
    try:
        questions = await hots_service.get_questions_by_topic(topic_id)
        return questions
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch HOTS questions: {str(e)}")


@router.post("/attempt", response_model=SubmitHOTSAttemptResponse)
async def submit_hots_attempt(request: SubmitHOTSAttemptRequest):
    """
    Submit an attempt for a HOTS question
    
    Evaluates the student's answer using Gemini, provides feedback,
    and updates HOTS mastery tracking. Awards topper badge when
    student achieves 80% mastery on HOTS questions.
    
    Args:
        request: Attempt submission with user_id, question_id, answer, and time_taken
        
    Returns:
        Evaluation result with feedback and mastery update
        
    Raises:
        404: Question not found
        500: Submission failed
    """
    try:
        result = await hots_service.submit_attempt(
            user_id=request.user_id,
            question_id=request.question_id,
            answer=request.answer,
            time_taken_minutes=request.time_taken_minutes
        )
        
        return SubmitHOTSAttemptResponse(**result)
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit HOTS attempt: {str(e)}")


@router.get("/performance/{user_id}", response_model=HOTSPerformanceResponse)
async def get_hots_performance(user_id: str):
    """
    Get HOTS performance analytics for a user
    
    Returns comprehensive HOTS performance metrics including:
    - Total questions attempted and correct
    - Overall HOTS mastery score
    - Topics where topper badge was earned
    - Subject-wise breakdown
    
    Args:
        user_id: User UUID
        
    Returns:
        HOTS performance analytics
        
    Raises:
        500: Fetch failed
    """
    try:
        performance = await hots_service.get_hots_performance(user_id)
        return HOTSPerformanceResponse(**performance)
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch HOTS performance: {str(e)}")
