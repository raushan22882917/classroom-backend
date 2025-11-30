"""Microplan generation endpoints"""

from fastapi import APIRouter, HTTPException, Query, status
from datetime import date
from typing import Optional

from app.models.progress import MicroPlan
from app.models.base import Subject
from app.services.microplan_service import microplan_service
from app.utils.exceptions import APIException

router = APIRouter(prefix="/microplan", tags=["Microplan"])


@router.post("/generate", response_model=MicroPlan)
async def generate_microplan(
    user_id: str = Query(..., description="User ID for the student"),
    plan_date: Optional[date] = Query(None, description="Date for the micro-plan (defaults to today)"),
    subject: Optional[Subject] = Query(None, description="Specific subject to focus on (optional)")
):
    """
    Generate a personalized daily micro-plan for a student
    
    The micro-plan includes:
    - 1 concept summary (NCERT content)
    - 2 PYQs (Previous Year Questions)
    - 1 HOTS question
    - 1 quiz (3-5 quick questions)
    
    Selection is adaptive based on:
    - Student's mastery scores (prioritizes weak areas)
    - Spaced repetition scheduling (reviews topics at optimal intervals)
    - Recent activity (avoids repetition)
    
    The algorithm uses the SM-2 spaced repetition algorithm to determine
    which topics are due for review, ensuring efficient long-term retention.
    
    Args:
        user_id: Student user ID (required)
        plan_date: Date for the micro-plan (optional, defaults to today)
        subject: Specific subject to focus on (optional, auto-selected if not provided)
        
    Returns:
        MicroPlan object with selected content
        
    Raises:
        400: Invalid user_id or parameters
        500: Failed to generate micro-plan
    """
    try:
        if not user_id or not user_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID is required"
            )
        
        microplan = await microplan_service.generate_microplan(
            user_id=user_id,
            plan_date=plan_date,
            subject=subject
        )
        
        return microplan
        
    except APIException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate micro-plan: {str(e)}"
        )


@router.get("/today", response_model=Optional[MicroPlan])
async def get_today_microplan(
    user_id: str = Query(..., description="User ID for the student")
):
    """
    Get today's micro-plan for a student
    
    If no micro-plan exists for today, returns None.
    Use the /generate endpoint to create a new micro-plan.
    
    Args:
        user_id: Student user ID (required)
        
    Returns:
        MicroPlan object if exists, None otherwise
        
    Raises:
        400: Invalid user_id
        500: Failed to fetch micro-plan
    """
    try:
        if not user_id or not user_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID is required"
            )
        
        microplan = await microplan_service.get_microplan(
            user_id=user_id,
            plan_date=date.today()
        )
        
        return microplan
        
    except APIException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch micro-plan: {str(e)}"
        )


@router.get("/{plan_date}", response_model=Optional[MicroPlan])
async def get_microplan_by_date(
    plan_date: date,
    user_id: str = Query(..., description="User ID for the student")
):
    """
    Get micro-plan for a specific date
    
    Args:
        plan_date: Date for the micro-plan (YYYY-MM-DD format)
        user_id: Student user ID (required)
        
    Returns:
        MicroPlan object if exists, None otherwise
        
    Raises:
        400: Invalid user_id or date
        500: Failed to fetch micro-plan
    """
    try:
        if not user_id or not user_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID is required"
            )
        
        microplan = await microplan_service.get_microplan(
            user_id=user_id,
            plan_date=plan_date
        )
        
        return microplan
        
    except APIException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch micro-plan: {str(e)}"
        )


@router.get("/{microplan_id}", response_model=MicroPlan)
async def get_microplan_by_id(
    microplan_id: str
):
    """
    Get micro-plan by ID
    
    Args:
        microplan_id: Micro-plan ID
        
    Returns:
        MicroPlan object
        
    Raises:
        404: Micro-plan not found
        500: Failed to fetch micro-plan
    """
    try:
        if not microplan_id or not microplan_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Microplan ID is required"
            )
        
        microplan = await microplan_service.get_microplan_by_id(microplan_id)
        
        return microplan
        
    except APIException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch micro-plan: {str(e)}"
        )


@router.post("/{microplan_id}/complete", response_model=MicroPlan)
async def mark_microplan_completed(
    microplan_id: str,
    user_id: str = Query(..., description="User ID for the student")
):
    """
    Mark a micro-plan as completed
    
    This updates the completion status and timestamp, which is used
    for tracking streaks and progress.
    
    Args:
        microplan_id: Micro-plan ID
        user_id: Student user ID (required)
        
    Returns:
        Updated MicroPlan object
        
    Raises:
        400: Invalid microplan_id or user_id
        404: Micro-plan not found
        500: Failed to update micro-plan
    """
    try:
        if not microplan_id or not microplan_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Microplan ID is required"
            )
        
        if not user_id or not user_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID is required"
            )
        
        microplan = await microplan_service.mark_completed(
            microplan_id=microplan_id,
            user_id=user_id
        )
        
        return microplan
        
    except APIException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark micro-plan as completed: {str(e)}"
        )
