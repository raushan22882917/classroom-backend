"""Notification endpoints"""

from fastapi import APIRouter, HTTPException, Query, Request
from typing import Optional, List
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.notification import (
    Notification,
    NotificationCreate,
    NotificationResponse,
    NotificationType
)
from app.services.notification_service import notification_service
from app.utils.exceptions import APIException

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/notifications", response_model=NotificationResponse)
@limiter.limit("100/minute")
async def get_notifications(
    request: Request,
    user_id: str = Query(..., description="User ID"),
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    notification_type: Optional[NotificationType] = Query(None, description="Filter by type"),
    limit: int = Query(100, description="Maximum number of results", ge=1, le=500),
    offset: int = Query(0, description="Pagination offset", ge=0)
):
    """
    Get notifications for a user
    
    Query Parameters:
    - user_id: User ID
    - is_read: Filter by read status (optional)
    - notification_type: Filter by notification type (optional)
    - limit: Maximum number of results (default: 100, max: 500)
    - offset: Pagination offset (default: 0)
    
    Returns:
    - NotificationResponse with notifications, unread count, and total count
    """
    try:
        notifications = await notification_service.get_user_notifications(
            user_id=user_id,
            is_read=is_read,
            notification_type=notification_type,
            limit=limit,
            offset=offset
        )
        
        unread_count = await notification_service.get_unread_count(user_id)
        
        return NotificationResponse(
            notifications=notifications,
            unread_count=unread_count,
            total_count=len(notifications)
        )
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notifications/teacher", response_model=List[Notification])
@limiter.limit("100/minute")
async def get_teacher_notifications(
    request: Request,
    user_id: str = Query(..., description="User ID")
):
    """
    Get notifications created by teachers
    
    Query Parameters:
    - user_id: User ID
    
    Returns:
    - List of notifications from teachers
    """
    try:
        notifications = await notification_service.get_notifications_by_creator_role(
            user_id=user_id,
            creator_role="teacher"
        )
        return notifications
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notifications/admin", response_model=List[Notification])
@limiter.limit("100/minute")
async def get_admin_notifications(
    request: Request,
    user_id: str = Query(..., description="User ID")
):
    """
    Get notifications created by admins
    
    Query Parameters:
    - user_id: User ID
    
    Returns:
    - List of notifications from admins
    """
    try:
        notifications = await notification_service.get_notifications_by_creator_role(
            user_id=user_id,
            creator_role="admin"
        )
        return notifications
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications", response_model=Notification, status_code=201)
@limiter.limit("50/minute")
async def create_notification(
    request: Request,
    notification: NotificationCreate
):
    """
    Create a new notification (admin or teacher only)
    
    Request Body:
    - user_id: Target user ID
    - title: Notification title
    - message: Notification message
    - type: Notification type (optional)
    - priority: Notification priority (optional)
    - action_url: Optional action URL
    - metadata: Optional metadata
    - created_by: Creator user ID (optional, will be set from notification if provided)
    
    Returns:
    - Created Notification object
    """
    try:
        created = await notification_service.create_notification(
            notification, 
            created_by=notification.created_by
        )
        return created
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/notifications/{notification_id}/read", response_model=Notification)
@limiter.limit("100/minute")
async def mark_notification_read(
    request: Request,
    notification_id: str,
    user_id: str = Query(..., description="User ID")
):
    """
    Mark a notification as read
    
    Path Parameters:
    - notification_id: Notification ID
    
    Query Parameters:
    - user_id: User ID (for verification)
    
    Returns:
    - Updated Notification object
    """
    try:
        updated = await notification_service.mark_as_read(notification_id, user_id)
        return updated
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/notifications/read-all", response_model=dict)
@limiter.limit("20/minute")
async def mark_all_notifications_read(
    request: Request,
    user_id: str = Query(..., description="User ID")
):
    """
    Mark all notifications as read for a user
    
    Query Parameters:
    - user_id: User ID
    
    Returns:
    - Dictionary with count of notifications marked as read
    """
    try:
        count = await notification_service.mark_all_as_read(user_id)
        return {"marked_count": count}
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notifications/unread-count", response_model=dict)
@limiter.limit("100/minute")
async def get_unread_count(
    request: Request,
    user_id: str = Query(..., description="User ID")
):
    """
    Get unread notification count for a user
    
    Query Parameters:
    - user_id: User ID
    
    Returns:
    - Dictionary with unread_count
    """
    try:
        count = await notification_service.get_unread_count(user_id)
        return {"unread_count": count}
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

