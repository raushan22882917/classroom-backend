"""Well-being and focus endpoints"""

from fastapi import APIRouter, HTTPException, status
from app.models.ai_features import FocusSessionRequest, FocusSessionEndRequest
from app.services.wellbeing_service import WellbeingService
from app.utils.exceptions import APIException
from supabase import create_client
from app.config import settings

router = APIRouter(prefix="/wellbeing", tags=["Well-being & Focus"])

# Initialize Supabase client
supabase_client = create_client(
    settings.supabase_url,
    settings.supabase_service_key
)

# Initialize service
wellbeing_service = WellbeingService(supabase_client)


@router.post("/focus/start")
async def start_focus_session(request: FocusSessionRequest):
    """
    Start a focused study session with time-boxing
    
    Args:
        request: Focus session request
    
    Returns:
        Focus session details
    """
    try:
        session = await wellbeing_service.start_focus_session(
            user_id=request.user_id,
            duration_minutes=request.duration_minutes,
            subject=request.subject,
            goal=request.goal
        )
        return {
            "success": True,
            **session
        }
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start focus session: {str(e)}"
        )


@router.post("/focus/end")
async def end_focus_session(request: FocusSessionEndRequest):
    """
    End a focus session and get summary
    
    Args:
        request: Focus session end request
    
    Returns:
        Session summary with achievements
    """
    try:
        summary = await wellbeing_service.end_focus_session(
            session_id=request.session_id,
            user_id=request.user_id,
            distractions_count=request.distractions_count,
            completed=request.completed
        )
        return {
            "success": True,
            **summary
        }
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to end focus session: {str(e)}"
        )


@router.get("/motivation/{user_id}")
async def get_motivation(user_id: str, context: str = None):
    """
    Get personalized motivation message
    
    Args:
        user_id: Student user ID
        context: Optional context (struggling, achievement, daily_checkin)
    
    Returns:
        Motivational message and tips
    """
    try:
        motivation = await wellbeing_service.get_motivation_message(
            user_id=user_id,
            context=context
        )
        return {
            "success": True,
            **motivation
        }
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get motivation: {str(e)}"
        )


@router.get("/distraction-guard/{user_id}")
async def get_distraction_guard_settings(user_id: str):
    """
    Get distraction guard settings
    
    Args:
        user_id: Student user ID
    
    Returns:
        Distraction guard settings
    """
    try:
        settings = await wellbeing_service.get_distraction_guard_settings(user_id)
        return {
            "success": True,
            "user_id": user_id,
            "settings": settings
        }
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get settings: {str(e)}"
        )


@router.put("/distraction-guard/{user_id}")
async def update_distraction_guard_settings(user_id: str, settings: dict):
    """
    Update distraction guard settings
    
    Args:
        user_id: Student user ID
        settings: Settings to update
    
    Returns:
        Updated settings
    """
    try:
        updated_settings = await wellbeing_service.update_distraction_guard_settings(
            user_id=user_id,
            settings=settings
        )
        return {
            "success": True,
            **updated_settings
        }
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update settings: {str(e)}"
        )


