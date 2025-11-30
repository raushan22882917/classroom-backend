"""Teacher time-savers endpoints"""

from fastapi import APIRouter, HTTPException, status
from app.models.ai_features import LessonPlanRequest, AssessmentRequest, ParentMessageRequest
from app.services.teacher_service import TeacherService
from app.utils.exceptions import APIException
from supabase import create_client
from app.config import settings

router = APIRouter(prefix="/teacher", tags=["Teacher Tools"])

# Initialize Supabase client
supabase_client = create_client(
    settings.supabase_url,
    settings.supabase_service_key
)

# Initialize service
teacher_service = TeacherService(supabase_client)


@router.post("/lesson-plan")
async def generate_lesson_plan(request: LessonPlanRequest):
    """
    Generate lesson plan for a topic
    
    Args:
        request: Lesson plan request
    
    Returns:
        Complete lesson plan
    """
    try:
        lesson_plan = await teacher_service.generate_lesson_plan(
            teacher_id=request.teacher_id,
            subject=request.subject,
            topic=request.topic,
            duration_minutes=request.duration_minutes,
            class_grade=request.class_grade,
            learning_objectives=request.learning_objectives
        )
        return {
            "success": True,
            **lesson_plan
        }
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate lesson plan: {str(e)}"
        )


@router.post("/assessment")
async def create_formative_assessment(request: AssessmentRequest):
    """
    Generate formative assessment questions
    
    Args:
        request: Assessment request
    
    Returns:
        Assessment with questions and rubrics
    """
    try:
        assessment = await teacher_service.create_formative_assessment(
            teacher_id=request.teacher_id,
            subject=request.subject,
            topic=request.topic,
            question_count=request.question_count,
            difficulty_levels=request.difficulty_levels
        )
        return {
            "success": True,
            **assessment
        }
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create assessment: {str(e)}"
        )


@router.post("/parent-message")
async def generate_parent_message(request: ParentMessageRequest):
    """
    Generate parent communication message
    
    Args:
        request: Parent message request
    
    Returns:
        Formatted message ready to send
    """
    try:
        message = await teacher_service.generate_parent_message(
            teacher_id=request.teacher_id,
            student_id=request.student_id,
            message_type=request.message_type,
            subject=request.subject,
            custom_content=request.custom_content
        )
        return {
            "success": True,
            **message
        }
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate parent message: {str(e)}"
        )


