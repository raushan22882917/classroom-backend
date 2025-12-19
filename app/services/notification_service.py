"""Notification service"""

from typing import List, Optional
from datetime import datetime
from supabase import create_client, Client

from app.config import settings
from app.models.notification import (
    Notification,
    NotificationCreate,
    NotificationType,
    NotificationPriority
)
from app.utils.exceptions import APIException


class NotificationService:
    """Service for managing notifications"""
    
    def __init__(self):
        """Initialize notification service with Supabase client"""
        self.supabase: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
    
    async def get_user_notifications(
        self,
        user_id: str,
        is_read: Optional[bool] = None,
        notification_type: Optional[NotificationType] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Notification]:
        """
        Get notifications for a user
        
        Args:
            user_id: User ID
            is_read: Filter by read status (optional)
            notification_type: Filter by type (optional)
            limit: Maximum number of results
            offset: Pagination offset
            
        Returns:
            List of Notification objects
        """
        try:
            query = self.supabase.table("notifications").select("*").eq("user_id", user_id)
            
            if is_read is not None:
                query = query.eq("is_read", is_read)
            
            if notification_type:
                query = query.eq("type", notification_type.value)
            
            query = query.order("created_at", desc=True).limit(limit).offset(offset)
            
            result = query.execute()
            
            if not result.data:
                return []
            
            return [Notification(**item) for item in result.data]
            
        except Exception as e:
            raise APIException(
                code="GET_NOTIFICATIONS_ERROR",
                message=f"Failed to get notifications: {str(e)}",
                status_code=500
            )
    
    async def get_unread_count(self, user_id: str) -> int:
        """
        Get unread notification count for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Unread count
        """
        try:
            result = self.supabase.table("notifications").select("id", count="exact").eq(
                "user_id", user_id
            ).eq("is_read", False).execute()
            
            return result.count or 0
            
        except Exception as e:
            raise APIException(
                code="GET_UNREAD_COUNT_ERROR",
                message=f"Failed to get unread count: {str(e)}",
                status_code=500
            )
    
    async def create_notification(self, notification: NotificationCreate, created_by: Optional[str] = None) -> Notification:
        """
        Create a new notification
        
        Args:
            notification: Notification creation data
            created_by: User ID of the creator (optional, will use notification.created_by if not provided)
            
        Returns:
            Created Notification object
        """
        try:
            notification_data = {
                "user_id": notification.user_id,
                "title": notification.title,
                "message": notification.message,
                "type": notification.type.value,
                "priority": notification.priority.value,
                "action_url": notification.action_url,
                "metadata": notification.metadata
            }
            
            # Use created_by from notification if provided, otherwise use parameter
            creator_id = notification.created_by or created_by
            if creator_id:
                notification_data["created_by"] = creator_id
            
            result = self.supabase.table("notifications").insert(notification_data).execute()
            
            if not result.data or len(result.data) == 0:
                raise APIException(
                    code="NOTIFICATION_CREATION_FAILED",
                    message="Failed to create notification",
                    status_code=500
                )
            
            return Notification(**result.data[0])
            
        except APIException:
            raise
        except Exception as e:
            raise APIException(
                code="CREATE_NOTIFICATION_ERROR",
                message=f"Failed to create notification: {str(e)}",
                status_code=500
            )
    
    async def mark_as_read(self, notification_id: str, user_id: str) -> Notification:
        """
        Mark a notification as read
        
        Args:
            notification_id: Notification ID
            user_id: User ID (for verification)
            
        Returns:
            Updated Notification object
        """
        try:
            update_data = {
                "is_read": True,
                "read_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table("notifications").update(update_data).eq(
                "id", notification_id
            ).eq("user_id", user_id).execute()
            
            if not result.data or len(result.data) == 0:
                raise APIException(
                    code="NOTIFICATION_NOT_FOUND",
                    message="Notification not found",
                    status_code=404
                )
            
            return Notification(**result.data[0])
            
        except APIException:
            raise
        except Exception as e:
            raise APIException(
                code="MARK_READ_ERROR",
                message=f"Failed to mark notification as read: {str(e)}",
                status_code=500
            )
    
    async def mark_all_as_read(self, user_id: str) -> int:
        """
        Mark all notifications as read for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Number of notifications marked as read
        """
        try:
            # Get count of unread before marking
            unread_count = await self.get_unread_count(user_id)
            
            if unread_count == 0:
                return 0
            
            # Mark them as read
            update_data = {
                "is_read": True,
                "read_at": datetime.utcnow().isoformat()
            }
            
            self.supabase.table("notifications").update(update_data).eq(
                "user_id", user_id
            ).eq("is_read", False).execute()
            
            return unread_count
            
        except Exception as e:
            raise APIException(
                code="MARK_ALL_READ_ERROR",
                message=f"Failed to mark all notifications as read: {str(e)}",
                status_code=500
            )
    
    async def get_notifications_by_creator_role(
        self,
        user_id: str,
        creator_role: str  # "teacher" or "admin"
    ) -> List[Notification]:
        """
        Get notifications created by teachers or admins
        
        Args:
            user_id: User ID receiving notifications
            creator_role: Role of the creator ("teacher" or "admin")
            
        Returns:
            List of Notification objects
        """
        try:
            # Get user IDs with the specified role
            role_result = self.supabase.table("user_roles").select("user_id").eq(
                "role", creator_role
            ).execute()
            
            creator_ids = {item["user_id"] for item in (role_result.data or [])}
            
            if not creator_ids:
                return []
            
            # Get notifications for the user created by users with the specified role
            query = self.supabase.table("notifications").select("*").eq("user_id", user_id)
            
            # Filter by creator IDs - need to use .in_() for multiple IDs
            # Since Supabase doesn't support .in_() directly on created_by, we'll filter in Python
            result = query.order("created_at", desc=True).limit(500).execute()
            
            if not result.data:
                return []
            
            # Filter notifications by creator role
            filtered = [
                Notification(**item) for item in result.data
                if item.get("created_by") and item["created_by"] in creator_ids
            ]
            
            return filtered
            
        except Exception as e:
            raise APIException(
                code="GET_NOTIFICATIONS_BY_ROLE_ERROR",
                message=f"Failed to get notifications by creator role: {str(e)}",
                status_code=500
            )
    
    async def dismiss_notification(
        self,
        notification_id: str,
        user_id: str
    ) -> bool:
        """
        Dismiss (delete) a notification
        
        Args:
            notification_id: Notification ID to dismiss
            user_id: User ID (for security verification)
            
        Returns:
            True if successful
        """
        try:
            # First verify the notification belongs to the user
            check_result = self.supabase.table("notifications").select("id").eq(
                "id", notification_id
            ).eq("user_id", user_id).execute()
            
            if not check_result.data:
                raise APIException(
                    code="NOTIFICATION_NOT_FOUND",
                    message="Notification not found or does not belong to user",
                    status_code=404
                )
            
            # Delete the notification
            delete_result = self.supabase.table("notifications").delete().eq(
                "id", notification_id
            ).eq("user_id", user_id).execute()
            
            return True
            
        except APIException:
            raise
        except Exception as e:
            raise APIException(
                code="DISMISS_NOTIFICATION_ERROR",
                message=f"Failed to dismiss notification: {str(e)}",
                status_code=500
            )


# Global service instance
notification_service = NotificationService()
