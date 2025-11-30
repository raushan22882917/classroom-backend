"""AI Tutoring endpoints for enhanced feedback and study planning"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, Query
from app.models.ai_features import (
    FeedbackRequest, StudyPlanRequest, QuestionAnswerRequest,
    CreateSessionRequest, SendMessageRequest, GenerateLessonPlanRequest
)
from app.services.ai_tutoring_service import AITutoringService
from app.services.enhanced_ai_tutor_service import EnhancedAITutorService
from app.utils.exceptions import APIException
from supabase import create_client
from app.config import settings

router = APIRouter(prefix="/ai-tutoring", tags=["AI Tutoring"])

# Initialize Supabase client
supabase_client = create_client(
    settings.supabase_url,
    settings.supabase_service_key
)

# Initialize services
ai_tutoring_service = AITutoringService(supabase_client)
enhanced_ai_tutor_service = EnhancedAITutorService(supabase_client)


@router.post("/feedback")
async def get_personalized_feedback(request: FeedbackRequest):
    """
    Get personalized feedback for student work
    
    Args:
        request: Feedback request with content and performance data
    
    Returns:
        Personalized feedback with suggestions
    """
    try:
        feedback = await ai_tutoring_service.get_personalized_feedback(
            user_id=request.user_id,
            content=request.content,
            subject=request.subject,
            performance_data=request.performance_data
        )
        return {
            "success": True,
            **feedback
        }
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate feedback: {str(e)}"
        )


@router.post("/study-plan")
async def generate_study_plan(request: StudyPlanRequest):
    """
    Generate personalized study plan
    
    Args:
        request: Study plan request with subject and duration
    
    Returns:
        Detailed study plan
    """
    try:
        study_plan = await ai_tutoring_service.generate_study_plan(
            user_id=request.user_id,
            subject=request.subject,
            days=request.days,
            hours_per_day=request.hours_per_day
        )
        return {
            "success": True,
            **study_plan
        }
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate study plan: {str(e)}"
        )


@router.post("/answer")
async def answer_question(request: QuestionAnswerRequest):
    """
    Answer student questions with explanations
    
    Args:
        request: Question answer request
    
    Returns:
        Answer with explanation and resources
    """
    try:
        answer = await ai_tutoring_service.answer_question(
            user_id=request.user_id,
            question=request.question,
            subject=request.subject,
            context=request.context
        )
        return {
            "success": True,
            **answer
        }
    except APIException as e:
        print(f"APIException in answer_question: {e.message} (code: {e.code})")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Unexpected error in answer_question endpoint: {str(e)}")
        print(f"Traceback: {error_trace}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to answer question: {str(e)}"
        )


# Enhanced AI Tutor Endpoints (Conversational Interface)

@router.post("/sessions")
async def create_session(request: CreateSessionRequest):
    """
    Create a new AI tutor session
    
    Args:
        request: Session creation request
    
    Returns:
        Created session with welcome message
    """
    try:
        session = await enhanced_ai_tutor_service.create_session(
            user_id=request.user_id,
            session_name=request.session_name,
            subject=request.subject
        )
        return {
            "success": True,
            "session": session
        }
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@router.get("/sessions")
async def get_sessions(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Get all sessions for a user
    
    Args:
        user_id: User ID
        limit: Maximum number of sessions to return
        offset: Offset for pagination
    
    Returns:
        List of sessions
    """
    try:
        sessions = await enhanced_ai_tutor_service.get_user_sessions(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        return {
            "success": True,
            "sessions": sessions,
            "count": len(sessions)
        }
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch sessions: {str(e)}"
        )


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    limit: int = Query(50, ge=1, le=100)
):
    """
    Get all messages in a session
    
    Args:
        session_id: Session ID
        limit: Maximum number of messages to return
    
    Returns:
        List of messages
    """
    try:
        messages = await enhanced_ai_tutor_service.get_session_messages(
            session_id=session_id,
            limit=limit
        )
        return {
            "success": True,
            "messages": messages,
            "count": len(messages)
        }
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch messages: {str(e)}"
        )


@router.post("/sessions/message")
async def send_message(request: SendMessageRequest):
    """
    Send a message in a session and get AI response
    
    Args:
        request: Message request
    
    Returns:
        User message and AI response
    """
    try:
        result = await enhanced_ai_tutor_service.send_message(
            session_id=request.session_id,
            user_id=request.user_id,
            content=request.content,
            subject=request.subject,
            message_type=request.message_type
        )
        return {
            "success": True,
            **result
        }
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )


@router.post("/lesson-plans/generate")
async def generate_lesson_plan(request: GenerateLessonPlanRequest):
    """
    Generate a personalized lesson plan based on student performance
    
    Args:
        request: Lesson plan generation request
    
    Returns:
        Generated lesson plan
    """
    try:
        lesson_plan = await enhanced_ai_tutor_service.generate_performance_based_lesson_plan(
            user_id=request.user_id,
            subject=request.subject,
            days=request.days,
            hours_per_day=request.hours_per_day
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


@router.get("/lesson-plans")
async def get_lesson_plans(
    user_id: str = Query(..., description="User ID"),
    subject: Optional[str] = Query(None, description="Subject filter"),
    is_active: Optional[bool] = Query(True, description="Filter by active status")
):
    """
    Get lesson plans for a user
    
    Args:
        user_id: User ID
        subject: Optional subject filter
        is_active: Filter by active status
    
    Returns:
        List of lesson plans
    """
    try:
        from app.models.base import Subject as SubjectEnum
        
        subject_enum = None
        if subject:
            try:
                subject_enum = SubjectEnum(subject)
            except ValueError:
                pass
        
        lesson_plans = await enhanced_ai_tutor_service.get_lesson_plans(
            user_id=user_id,
            subject=subject_enum,
            is_active=is_active
        )
        return {
            "success": True,
            "lesson_plans": lesson_plans,
            "count": len(lesson_plans)
        }
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch lesson plans: {str(e)}"
        )


@router.get("/teacher/student-sessions")
async def get_teacher_student_sessions(
    teacher_id: str = Query(..., description="Teacher ID"),
    student_id: Optional[str] = Query(None, description="Optional student ID filter"),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Get AI tutor sessions for students in teacher's school (limited access)
    
    Args:
        teacher_id: Teacher ID
        student_id: Optional specific student ID
        limit: Maximum number of sessions to return
    
    Returns:
        List of student sessions
    """
    try:
        sessions = await enhanced_ai_tutor_service.get_teacher_student_sessions(
            teacher_id=teacher_id,
            student_id=student_id,
            limit=limit
        )
        return {
            "success": True,
            "sessions": sessions,
            "count": len(sessions)
        }
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch student sessions: {str(e)}"
        )

