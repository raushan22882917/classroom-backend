"""Analytics endpoints"""

from fastapi import APIRouter, Depends, Query, BackgroundTasks
from typing import Optional
from supabase import Client

from app.models.base import Subject
from app.services.analytics_service import AnalyticsService
from app.config import settings
from supabase import create_client

router = APIRouter()


def get_supabase_client() -> Client:
    """Get Supabase client"""
    return create_client(settings.supabase_url, settings.supabase_service_key)


def get_analytics_service(supabase: Client = Depends(get_supabase_client)) -> AnalyticsService:
    """Get analytics service instance"""
    return AnalyticsService(supabase)


@router.get("/analytics/dashboard")
async def get_admin_dashboard(
    service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Get aggregate metrics for admin dashboard
    
    Returns:
        Dashboard metrics including active students, avg mastery, completion rate, and flagged students
    """
    return await service.get_admin_dashboard_metrics()


@router.get("/analytics/student/{student_id}")
async def get_student_analytics(
    student_id: str,
    service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Get detailed analytics for a specific student
    
    Args:
        student_id: Student user ID
        
    Returns:
        Student analytics including progress, test performance, and subject breakdown
    """
    return await service.get_student_analytics(student_id)


@router.get("/analytics/trends")
async def get_performance_trends(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    subject: Optional[str] = Query(None, description="Filter by subject"),
    days: int = Query(30, description="Number of days to look back", ge=1, le=365),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Get performance trends over time
    
    Args:
        user_id: Optional user ID filter
        subject: Optional subject filter
        days: Number of days to look back (1-365)
        
    Returns:
        Performance trends with daily aggregates
    """
    return await service.get_performance_trends(user_id, subject, days)


@router.post("/analytics/event")
async def log_event(
    background_tasks: BackgroundTasks,
    user_id: str = Query(..., description="User ID"),
    event_type: str = Query(..., description="Event type"),
    subject: Optional[str] = Query(None, description="Subject"),
    topic_id: Optional[str] = Query(None, description="Topic ID"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Log a user event to BigQuery (background task)
    
    Args:
        user_id: User ID
        event_type: Type of event
        subject: Optional subject
        topic_id: Optional topic ID
        
    Returns:
        Success message
    """
    background_tasks.add_task(
        service.log_event,
        user_id=user_id,
        event_type=event_type,
        subject=subject,
        topic_id=topic_id
    )
    
    return {
        "message": "Event logged successfully",
        "event_type": event_type
    }


@router.post("/analytics/test-result")
async def log_test_result(
    background_tasks: BackgroundTasks,
    test_id: str = Query(..., description="Test session ID"),
    user_id: str = Query(..., description="User ID"),
    subject: str = Query(..., description="Subject"),
    exam_set_id: Optional[str] = Query(None, description="Exam set ID"),
    score: float = Query(..., description="Score achieved"),
    total_marks: int = Query(..., description="Total marks"),
    duration_minutes: int = Query(..., description="Duration in minutes"),
    questions_attempted: int = Query(..., description="Questions attempted"),
    correct_answers: int = Query(..., description="Correct answers"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Log a test result to BigQuery (background task)
    
    Args:
        test_id: Test session ID
        user_id: User ID
        subject: Subject
        exam_set_id: Exam set ID
        score: Score achieved
        total_marks: Total marks
        duration_minutes: Duration in minutes
        questions_attempted: Questions attempted
        correct_answers: Correct answers
        
    Returns:
        Success message
    """
    background_tasks.add_task(
        service.log_test_result,
        test_id=test_id,
        user_id=user_id,
        subject=subject,
        exam_set_id=exam_set_id,
        score=score,
        total_marks=total_marks,
        duration_minutes=duration_minutes,
        questions_attempted=questions_attempted,
        correct_answers=correct_answers
    )
    
    return {
        "message": "Test result logged successfully",
        "test_id": test_id
    }


@router.post("/analytics/progress-snapshot")
async def log_progress_snapshot(
    background_tasks: BackgroundTasks,
    user_id: str = Query(..., description="User ID"),
    subject: str = Query(..., description="Subject"),
    topic_id: str = Query(..., description="Topic ID"),
    mastery_score: float = Query(..., description="Mastery score"),
    questions_attempted: int = Query(..., description="Questions attempted"),
    correct_answers: int = Query(..., description="Correct answers"),
    total_time_minutes: int = Query(..., description="Total time in minutes"),
    streak_days: int = Query(..., description="Streak days"),
    service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Log a progress snapshot to BigQuery (background task)
    
    Args:
        user_id: User ID
        subject: Subject
        topic_id: Topic ID
        mastery_score: Mastery score
        questions_attempted: Questions attempted
        correct_answers: Correct answers
        total_time_minutes: Total time in minutes
        streak_days: Streak days
        
    Returns:
        Success message
    """
    background_tasks.add_task(
        service.log_progress_snapshot,
        user_id=user_id,
        subject=subject,
        topic_id=topic_id,
        mastery_score=mastery_score,
        questions_attempted=questions_attempted,
        correct_answers=correct_answers,
        total_time_minutes=total_time_minutes,
        streak_days=streak_days
    )
    
    return {
        "message": "Progress snapshot logged successfully",
        "user_id": user_id,
        "topic_id": topic_id
    }
