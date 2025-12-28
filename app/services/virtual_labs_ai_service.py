"""AI assistance service for Virtual Labs"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import google.generativeai as genai

from app.config import settings
from app.models.virtual_labs import (
    VirtualLabAIAssistanceCreate,
    VirtualLabAIAssistanceResponse,
    ResponseType
)
from app.services.virtual_labs_service import virtual_labs_service
from app.utils.exceptions import APIException

logger = logging.getLogger(__name__)


class VirtualLabsAIService:
    """AI assistance service for Virtual Labs"""
    
    def __init__(self):
        """Initialize AI service"""
        self.gemini_api_key = settings.gemini_api_key
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        else:
            self.model = None
            logger.warning("Gemini API key not configured, AI assistance will be limited")
    
    async def create_ai_assistance(
        self,
        assistance_data: VirtualLabAIAssistanceCreate
    ) -> VirtualLabAIAssistanceResponse:
        """Create AI assistance response"""
        try:
            # Get session and lab context
            session_context = await self._get_session_context(assistance_data.session_id)
            
            # Generate AI response
            ai_response = await self._generate_ai_response(
                user_query=assistance_data.user_query,
                context_data=assistance_data.context_data,
                response_type=assistance_data.response_type,
                session_context=session_context
            )
            
            # Store in database
            assistance_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            
            assistance_record = {
                "id": assistance_id,
                "session_id": assistance_data.session_id,
                "user_query": assistance_data.user_query,
                "ai_response": ai_response,
                "context_data": assistance_data.context_data,
                "response_type": assistance_data.response_type.value,
                "created_at": now.isoformat()
            }
            
            response = virtual_labs_service.supabase.table("virtual_lab_ai_assistance")\
                .insert(assistance_record)\
                .execute()
            
            if not response.data:
                raise APIException(
                    code="AI_ASSISTANCE_CREATION_FAILED",
                    message="Failed to create AI assistance record",
                    status_code=500
                )
            
            # Update session AI request counter
            await virtual_labs_service._update_session_counters(
                assistance_data.session_id, 
                "ai_requests"
            )
            
            return VirtualLabAIAssistanceResponse(**response.data[0])
            
        except APIException:
            raise
        except Exception as e:
            logger.error(f"Error creating AI assistance: {str(e)}")
            raise APIException(
                code="AI_ASSISTANCE_ERROR",
                message=f"Failed to create AI assistance: {str(e)}",
                status_code=500
            )
    
    async def get_session_ai_assistance(
        self,
        session_id: str,
        user_id: str
    ) -> list[VirtualLabAIAssistanceResponse]:
        """Get AI assistance history for a session"""
        try:
            # Verify user owns the session
            session_response = virtual_labs_service.supabase.table("virtual_lab_sessions")\
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
            
            response = virtual_labs_service.supabase.table("virtual_lab_ai_assistance")\
                .select("*")\
                .eq("session_id", session_id)\
                .order("created_at", desc=False)\
                .execute()
            
            assistance_history = []
            if response.data:
                for assistance_data in response.data:
                    assistance_history.append(VirtualLabAIAssistanceResponse(**assistance_data))
            
            return assistance_history
            
        except APIException:
            raise
        except Exception as e:
            logger.error(f"Error fetching AI assistance history: {str(e)}")
            raise APIException(
                code="AI_ASSISTANCE_FETCH_ERROR",
                message=f"Failed to fetch AI assistance history: {str(e)}",
                status_code=500
            )
    
    async def _get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Get session and lab context for AI assistance"""
        try:
            # Get session details
            session_response = virtual_labs_service.supabase.table("virtual_lab_sessions")\
                .select("*, virtual_labs(*)")\
                .eq("id", session_id)\
                .execute()
            
            if not session_response.data:
                raise APIException(
                    code="SESSION_NOT_FOUND",
                    message="Session not found",
                    status_code=404
                )
            
            session_data = session_response.data[0]
            lab_data = session_data.get("virtual_labs", {})
            
            # Get recent interactions
            interactions_response = virtual_labs_service.supabase.table("virtual_lab_interactions")\
                .select("*")\
                .eq("session_id", session_id)\
                .order("timestamp", desc=True)\
                .limit(10)\
                .execute()
            
            recent_interactions = interactions_response.data if interactions_response.data else []
            
            return {
                "session": session_data,
                "lab": lab_data,
                "recent_interactions": recent_interactions
            }
            
        except APIException:
            raise
        except Exception as e:
            logger.error(f"Error getting session context: {str(e)}")
            return {}
    
    async def _generate_ai_response(
        self,
        user_query: str,
        context_data: Optional[Dict[str, Any]],
        response_type: ResponseType,
        session_context: Dict[str, Any]
    ) -> str:
        """Generate AI response using Gemini"""
        try:
            if not self.model:
                return self._get_fallback_response(user_query, response_type)
            
            # Build context prompt
            lab_info = session_context.get("lab", {})
            session_info = session_context.get("session", {})
            recent_interactions = session_context.get("recent_interactions", [])
            
            system_prompt = self._build_system_prompt(
                lab_info=lab_info,
                session_info=session_info,
                response_type=response_type
            )
            
            user_context = self._build_user_context(
                user_query=user_query,
                context_data=context_data,
                recent_interactions=recent_interactions
            )
            
            full_prompt = f"{system_prompt}\n\n{user_context}"
            
            # Generate response
            response = self.model.generate_content(full_prompt)
            
            if response.text:
                return response.text.strip()
            else:
                return self._get_fallback_response(user_query, response_type)
                
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            return self._get_fallback_response(user_query, response_type)
    
    def _build_system_prompt(
        self,
        lab_info: Dict[str, Any],
        session_info: Dict[str, Any],
        response_type: ResponseType
    ) -> str:
        """Build system prompt for AI"""
        lab_title = lab_info.get("title", "Virtual Lab")
        subject = lab_info.get("subject", "science")
        class_grade = lab_info.get("class_grade", 12)
        topic = lab_info.get("topic", "experiment")
        difficulty = lab_info.get("difficulty_level", "intermediate")
        
        response_guidance = {
            ResponseType.EXPLANATION: "Provide clear, educational explanations that help the student understand the underlying concepts.",
            ResponseType.HINT: "Give subtle hints that guide the student toward the solution without giving away the answer.",
            ResponseType.CORRECTION: "Gently correct misconceptions and guide the student back on track.",
            ResponseType.ENCOURAGEMENT: "Provide positive, motivating feedback to keep the student engaged.",
            ResponseType.GUIDANCE: "Offer step-by-step guidance to help the student progress through the experiment."
        }
        
        return f"""You are an AI tutor for virtual science labs. You are helping a student with the following lab:

Lab: {lab_title}
Subject: {subject.title()}
Grade Level: {class_grade}
Topic: {topic}
Difficulty: {difficulty.title()}

Your role is to provide {response_type.value} responses. {response_guidance.get(response_type, "")}

Guidelines:
- Keep responses concise and age-appropriate for grade {class_grade} students
- Encourage scientific thinking and exploration
- Don't give direct answers - guide students to discover solutions
- Use encouraging and supportive language
- Reference specific lab elements when relevant
- Focus on the learning objectives and concepts
- If the student seems frustrated, provide encouragement and simpler steps

Response Type: {response_type.value}"""
    
    def _build_user_context(
        self,
        user_query: str,
        context_data: Optional[Dict[str, Any]],
        recent_interactions: list
    ) -> str:
        """Build user context for AI"""
        context_parts = [f"Student Question: {user_query}"]
        
        if context_data:
            current_state = context_data.get("current_state", "unknown")
            context_parts.append(f"Current Lab State: {current_state}")
            
            last_actions = context_data.get("last_actions", [])
            if last_actions:
                context_parts.append(f"Recent Actions: {', '.join(last_actions)}")
        
        if recent_interactions:
            interaction_summary = []
            for interaction in recent_interactions[-5:]:  # Last 5 interactions
                interaction_type = interaction.get("interaction_type", "unknown")
                element_id = interaction.get("element_id", "")
                interaction_summary.append(f"{interaction_type} on {element_id}")
            
            if interaction_summary:
                context_parts.append(f"Recent Interactions: {', '.join(interaction_summary)}")
        
        return "\n".join(context_parts)
    
    def _get_fallback_response(self, user_query: str, response_type: ResponseType) -> str:
        """Get fallback response when AI is not available"""
        fallback_responses = {
            ResponseType.EXPLANATION: "I understand you're looking for an explanation. Try exploring the different elements in the lab and observe what happens when you interact with them.",
            ResponseType.HINT: "Here's a hint: Look carefully at the lab setup and try interacting with the main components. What do you think might happen if you change the parameters?",
            ResponseType.CORRECTION: "It looks like you might need to try a different approach. Review the lab instructions and try again with a different method.",
            ResponseType.ENCOURAGEMENT: "You're doing great! Keep experimenting and don't be afraid to try different approaches. Learning comes from exploration!",
            ResponseType.GUIDANCE: "Let's break this down step by step. Start by examining the lab setup, then try interacting with one element at a time to see how it affects the experiment."
        }
        
        return fallback_responses.get(
            response_type,
            "I'm here to help! Try exploring the lab and let me know what specific aspect you'd like help with."
        )


# Create global instance
virtual_labs_ai_service = VirtualLabsAIService()