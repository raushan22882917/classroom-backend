"""Virtual Labs service for managing interactive science experiments"""

import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from supabase import create_client, Client

from app.config import settings
from app.models.virtual_labs import (
    VirtualLabCreate,
    VirtualLabUpdate,
    VirtualLabResponse,
    VirtualLabSessionCreate,
    VirtualLabSessionUpdate,
    VirtualLabSessionResponse,
    VirtualLabInteractionCreate,
    VirtualLabInteractionResponse,
    VirtualLabAIAssistanceCreate,
    VirtualLabAIAssistanceResponse,
    PerformanceMetrics,
    ConceptMastery,
    CompletionStatus,
    DifficultyLevel
)
from app.models.base import Subject
from app.utils.exceptions import APIException

logger = logging.getLogger(__name__)


class VirtualLabsService:
    """Service for Virtual Labs operations"""
    
    def __init__(self):
        """Initialize Virtual Labs service with Supabase client"""
        self.supabase: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
    
    # Virtual Labs Management
    async def create_virtual_lab(
        self,
        lab_data: VirtualLabCreate,
        created_by: str
    ) -> VirtualLabResponse:
        """Create a new virtual lab"""
        try:
            lab_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            
            lab_record = {
                "id": lab_id,
                "title": lab_data.title,
                "description": lab_data.description,
                "subject": lab_data.subject.value,
                "class_grade": lab_data.class_grade,
                "topic": lab_data.topic,
                "html_content": lab_data.html_content,
                "css_content": lab_data.css_content,
                "js_content": lab_data.js_content,
                "thumbnail_url": lab_data.thumbnail_url,
                "difficulty_level": lab_data.difficulty_level.value,
                "estimated_duration": lab_data.estimated_duration,
                "learning_objectives": lab_data.learning_objectives,
                "prerequisites": lab_data.prerequisites,
                "tags": lab_data.tags,
                "is_active": True,
                "created_by": created_by,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat()
            }
            
            response = self.supabase.table("virtual_labs").insert(lab_record).execute()
            
            if not response.data:
                raise APIException(
                    code="LAB_CREATION_FAILED",
                    message="Failed to create virtual lab",
                    status_code=500
                )
            
            return VirtualLabResponse(**response.data[0])
            
        except APIException:
            raise
        except Exception as e:
            logger.error(f"Error creating virtual lab: {str(e)}")
            raise APIException(
                code="LAB_CREATION_ERROR",
                message=f"Failed to create virtual lab: {str(e)}",
                status_code=500
            )
    
    async def get_virtual_labs(
        self,
        subject: Optional[Subject] = None,
        class_grade: Optional[int] = None,
        difficulty_level: Optional[DifficultyLevel] = None,
        is_active: bool = True,
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get list of virtual labs with filtering"""
        try:
            query = self.supabase.table("virtual_labs").select("*")
            
            # Apply filters
            query = query.eq("is_active", is_active)
            
            if subject:
                query = query.eq("subject", subject.value)
            
            if class_grade:
                query = query.eq("class_grade", class_grade)
            
            if difficulty_level:
                query = query.eq("difficulty_level", difficulty_level.value)
            
            # Get total count
            count_response = query.execute()
            total = len(count_response.data) if count_response.data else 0
            
            # Apply pagination
            query = query.range(offset, offset + limit - 1)
            query = query.order("created_at", desc=True)
            
            response = query.execute()
            
            labs = []
            if response.data:
                for lab_data in response.data:
                    labs.append(VirtualLabResponse(**lab_data))
            
            return {
                "labs": labs,
                "total": total,
                "page": (offset // limit) + 1,
                "limit": limit
            }
            
        except Exception as e:
            logger.error(f"Error fetching virtual labs: {str(e)}")
            
            # Check if it's a table not found error
            error_str = str(e).lower()
            if "relation" in error_str and "does not exist" in error_str:
                logger.warning("Virtual Labs tables not found. Please run the database migration.")
                raise APIException(
                    code="TABLES_NOT_FOUND",
                    message="Virtual Labs database tables not found. Please run the migration script to create the required tables.",
                    status_code=503
                )
            
            raise APIException(
                code="LAB_FETCH_ERROR",
                message=f"Failed to fetch virtual labs: {str(e)}",
                status_code=500
            )
    
    async def get_virtual_lab(self, lab_id: str) -> VirtualLabResponse:
        """Get a specific virtual lab by ID"""
        try:
            response = self.supabase.table("virtual_labs")\
                .select("*")\
                .eq("id", lab_id)\
                .eq("is_active", True)\
                .execute()
            
            if not response.data:
                raise APIException(
                    code="LAB_NOT_FOUND",
                    message="Virtual lab not found",
                    status_code=404
                )
            
            return VirtualLabResponse(**response.data[0])
            
        except APIException:
            raise
        except Exception as e:
            logger.error(f"Error fetching virtual lab {lab_id}: {str(e)}")
            raise APIException(
                code="LAB_FETCH_ERROR",
                message=f"Failed to fetch virtual lab: {str(e)}",
                status_code=500
            )
    
    async def update_virtual_lab(
        self,
        lab_id: str,
        lab_data: VirtualLabUpdate,
        user_id: str
    ) -> VirtualLabResponse:
        """Update a virtual lab"""
        try:
            # Check if lab exists and user has permission
            existing_lab = await self.get_virtual_lab(lab_id)
            
            # For now, allow any authenticated user to update
            # In production, check if user is creator or admin
            
            update_data = {}
            if lab_data.title is not None:
                update_data["title"] = lab_data.title
            if lab_data.description is not None:
                update_data["description"] = lab_data.description
            if lab_data.subject is not None:
                update_data["subject"] = lab_data.subject.value
            if lab_data.class_grade is not None:
                update_data["class_grade"] = lab_data.class_grade
            if lab_data.topic is not None:
                update_data["topic"] = lab_data.topic
            if lab_data.html_content is not None:
                update_data["html_content"] = lab_data.html_content
            if lab_data.css_content is not None:
                update_data["css_content"] = lab_data.css_content
            if lab_data.js_content is not None:
                update_data["js_content"] = lab_data.js_content
            if lab_data.thumbnail_url is not None:
                update_data["thumbnail_url"] = lab_data.thumbnail_url
            if lab_data.difficulty_level is not None:
                update_data["difficulty_level"] = lab_data.difficulty_level.value
            if lab_data.estimated_duration is not None:
                update_data["estimated_duration"] = lab_data.estimated_duration
            if lab_data.learning_objectives is not None:
                update_data["learning_objectives"] = lab_data.learning_objectives
            if lab_data.prerequisites is not None:
                update_data["prerequisites"] = lab_data.prerequisites
            if lab_data.tags is not None:
                update_data["tags"] = lab_data.tags
            if lab_data.is_active is not None:
                update_data["is_active"] = lab_data.is_active
            
            update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            response = self.supabase.table("virtual_labs")\
                .update(update_data)\
                .eq("id", lab_id)\
                .execute()
            
            if not response.data:
                raise APIException(
                    code="LAB_UPDATE_FAILED",
                    message="Failed to update virtual lab",
                    status_code=500
                )
            
            return VirtualLabResponse(**response.data[0])
            
        except APIException:
            raise
        except Exception as e:
            logger.error(f"Error updating virtual lab {lab_id}: {str(e)}")
            raise APIException(
                code="LAB_UPDATE_ERROR",
                message=f"Failed to update virtual lab: {str(e)}",
                status_code=500
            )
    
    async def delete_virtual_lab(self, lab_id: str, user_id: str) -> Dict[str, Any]:
        """Soft delete a virtual lab"""
        try:
            # Check if lab exists
            await self.get_virtual_lab(lab_id)
            
            # Soft delete by setting is_active to False
            response = self.supabase.table("virtual_labs")\
                .update({
                    "is_active": False,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                })\
                .eq("id", lab_id)\
                .execute()
            
            if not response.data:
                raise APIException(
                    code="LAB_DELETE_FAILED",
                    message="Failed to delete virtual lab",
                    status_code=500
                )
            
            return {"success": True, "message": "Virtual lab deleted successfully"}
            
        except APIException:
            raise
        except Exception as e:
            logger.error(f"Error deleting virtual lab {lab_id}: {str(e)}")
            raise APIException(
                code="LAB_DELETE_ERROR",
                message=f"Failed to delete virtual lab: {str(e)}",
                status_code=500
            )
    
    # Session Management
    async def create_session(
        self,
        session_data: VirtualLabSessionCreate
    ) -> VirtualLabSessionResponse:
        """Create a new lab session"""
        try:
            # Verify lab exists
            await self.get_virtual_lab(session_data.lab_id)
            
            session_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            
            session_record = {
                "id": session_id,
                "user_id": session_data.user_id,
                "lab_id": session_data.lab_id,
                "session_name": session_data.session_name,
                "started_at": now.isoformat(),
                "completion_status": CompletionStatus.IN_PROGRESS.value,
                "interactions_count": 0,
                "gesture_commands_used": 0,
                "ai_assistance_requests": 0,
                "created_at": now.isoformat(),
                "updated_at": now.isoformat()
            }
            
            response = self.supabase.table("virtual_lab_sessions")\
                .insert(session_record)\
                .execute()
            
            if not response.data:
                raise APIException(
                    code="SESSION_CREATION_FAILED",
                    message="Failed to create lab session",
                    status_code=500
                )
            
            return VirtualLabSessionResponse(**response.data[0])
            
        except APIException:
            raise
        except Exception as e:
            logger.error(f"Error creating lab session: {str(e)}")
            raise APIException(
                code="SESSION_CREATION_ERROR",
                message=f"Failed to create lab session: {str(e)}",
                status_code=500
            )
    
    async def get_user_sessions(
        self,
        user_id: str,
        lab_id: Optional[str] = None,
        completion_status: Optional[CompletionStatus] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[VirtualLabSessionResponse]:
        """Get user's lab sessions"""
        try:
            query = self.supabase.table("virtual_lab_sessions")\
                .select("*")\
                .eq("user_id", user_id)
            
            if lab_id:
                query = query.eq("lab_id", lab_id)
            
            if completion_status:
                query = query.eq("completion_status", completion_status.value)
            
            query = query.order("created_at", desc=True)\
                .range(offset, offset + limit - 1)
            
            response = query.execute()
            
            sessions = []
            if response.data:
                for session_data in response.data:
                    sessions.append(VirtualLabSessionResponse(**session_data))
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error fetching user sessions: {str(e)}")
            
            # Check if it's a table not found error
            error_str = str(e).lower()
            if "relation" in error_str and "does not exist" in error_str:
                logger.warning("Virtual Labs tables not found. Please run the database migration.")
                raise APIException(
                    code="TABLES_NOT_FOUND",
                    message="Virtual Labs database tables not found. Please run the migration script to create the required tables.",
                    status_code=503
                )
            
            raise APIException(
                code="SESSION_FETCH_ERROR",
                message=f"Failed to fetch user sessions: {str(e)}",
                status_code=500
            )
    
    async def update_session(
        self,
        session_id: str,
        session_data: VirtualLabSessionUpdate,
        user_id: str
    ) -> VirtualLabSessionResponse:
        """Update a lab session"""
        try:
            update_data = {}
            
            if session_data.completed_at is not None:
                update_data["completed_at"] = session_data.completed_at.isoformat()
            if session_data.duration_minutes is not None:
                update_data["duration_minutes"] = session_data.duration_minutes
            if session_data.completion_status is not None:
                update_data["completion_status"] = session_data.completion_status.value
            if session_data.performance_score is not None:
                update_data["performance_score"] = session_data.performance_score
            if session_data.feedback is not None:
                update_data["feedback"] = session_data.feedback
            
            update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            response = self.supabase.table("virtual_lab_sessions")\
                .update(update_data)\
                .eq("id", session_id)\
                .eq("user_id", user_id)\
                .execute()
            
            if not response.data:
                raise APIException(
                    code="SESSION_UPDATE_FAILED",
                    message="Failed to update session or session not found",
                    status_code=404
                )
            
            return VirtualLabSessionResponse(**response.data[0])
            
        except APIException:
            raise
        except Exception as e:
            logger.error(f"Error updating session {session_id}: {str(e)}")
            raise APIException(
                code="SESSION_UPDATE_ERROR",
                message=f"Failed to update session: {str(e)}",
                status_code=500
            )
    
    # Interaction Tracking
    async def record_interaction(
        self,
        interaction_data: VirtualLabInteractionCreate
    ) -> VirtualLabInteractionResponse:
        """Record a user interaction"""
        try:
            interaction_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            
            interaction_record = {
                "id": interaction_id,
                "session_id": interaction_data.session_id,
                "interaction_type": interaction_data.interaction_type.value,
                "interaction_data": interaction_data.interaction_data,
                "element_id": interaction_data.element_id,
                "gesture_type": interaction_data.gesture_type,
                "performance_impact": interaction_data.performance_impact,
                "timestamp": now.isoformat()
            }
            
            response = self.supabase.table("virtual_lab_interactions")\
                .insert(interaction_record)\
                .execute()
            
            if not response.data:
                raise APIException(
                    code="INTERACTION_RECORD_FAILED",
                    message="Failed to record interaction",
                    status_code=500
                )
            
            # Update session interaction count
            await self._update_session_counters(interaction_data.session_id, "interactions")
            
            return VirtualLabInteractionResponse(**response.data[0])
            
        except APIException:
            raise
        except Exception as e:
            logger.error(f"Error recording interaction: {str(e)}")
            raise APIException(
                code="INTERACTION_RECORD_ERROR",
                message=f"Failed to record interaction: {str(e)}",
                status_code=500
            )
    
    async def get_session_interactions(
        self,
        session_id: str,
        user_id: str
    ) -> List[VirtualLabInteractionResponse]:
        """Get all interactions for a session"""
        try:
            # Verify user owns the session
            session_response = self.supabase.table("virtual_lab_sessions")\
                .select("id")\
                .eq("id", session_id)\
                .eq("user_id", user_id)\
                .execute()
            
            if not session_response.data:
                raise APIException(
                    code="SESSION_NOT_FOUND",
                    message="Session not found or access denied",
                    status_code=404
                )
            
            response = self.supabase.table("virtual_lab_interactions")\
                .select("*")\
                .eq("session_id", session_id)\
                .order("timestamp", desc=False)\
                .execute()
            
            interactions = []
            if response.data:
                for interaction_data in response.data:
                    interactions.append(VirtualLabInteractionResponse(**interaction_data))
            
            return interactions
            
        except APIException:
            raise
        except Exception as e:
            logger.error(f"Error fetching session interactions: {str(e)}")
            raise APIException(
                code="INTERACTION_FETCH_ERROR",
                message=f"Failed to fetch session interactions: {str(e)}",
                status_code=500
            )
    
    async def _update_session_counters(self, session_id: str, counter_type: str):
        """Update session counters (interactions, gestures, ai_requests)"""
        try:
            if counter_type == "interactions":
                field = "interactions_count"
            elif counter_type == "gestures":
                field = "gesture_commands_used"
            elif counter_type == "ai_requests":
                field = "ai_assistance_requests"
            else:
                return
            
            # Get current count
            response = self.supabase.table("virtual_lab_sessions")\
                .select(field)\
                .eq("id", session_id)\
                .execute()
            
            if response.data:
                current_count = response.data[0].get(field, 0)
                new_count = current_count + 1
                
                self.supabase.table("virtual_lab_sessions")\
                    .update({field: new_count})\
                    .eq("id", session_id)\
                    .execute()
                    
        except Exception as e:
            logger.warning(f"Failed to update session counter {counter_type}: {str(e)}")


# Create global instance
virtual_labs_service = VirtualLabsService()