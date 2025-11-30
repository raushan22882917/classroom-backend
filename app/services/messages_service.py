"""Messages service for student-teacher communication with AI assistance"""

import json
from typing import List, Optional
from datetime import datetime
import google.generativeai as genai
from supabase import create_client, Client

from app.config import settings
from app.models.base import Message, Conversation, MessageCreate
from app.utils.exceptions import APIException


class MessagesService:
    """Service for managing messages and conversations"""
    
    def __init__(self):
        """Initialize messages service"""
        self._gemini_initialized = False
        self._supabase_client: Optional[Client] = None
    
    def _initialize_gemini(self):
        """Initialize Gemini API"""
        if not self._gemini_initialized:
            if not settings.gemini_api_key or not settings.gemini_api_key.strip():
                raise Exception("Gemini API key is not configured")
            genai.configure(api_key=settings.gemini_api_key)
            self._gemini_initialized = True
    
    def _get_supabase_client(self) -> Client:
        """Get or create Supabase client"""
        if self._supabase_client is None:
            self._supabase_client = create_client(
                settings.supabase_url,
                settings.supabase_service_key
            )
        return self._supabase_client
    
    async def get_conversations(self, user_id: str) -> List[Conversation]:
        """Get all conversations for a user"""
        try:
            supabase = self._get_supabase_client()
            
            # Get conversations where user is participant1 or participant2
            response1 = supabase.table("conversations")\
                .select("*")\
                .eq("participant1_id", user_id)\
                .order("last_message_at", desc=True)\
                .execute()
            
            response2 = supabase.table("conversations")\
                .select("*")\
                .eq("participant2_id", user_id)\
                .order("last_message_at", desc=True)\
                .execute()
            
            conversations = []
            for conv_data in (response1.data or []) + (response2.data or []):
                conversations.append(Conversation(
                    id=conv_data["id"],
                    participant1_id=conv_data["participant1_id"],
                    participant2_id=conv_data["participant2_id"],
                    last_message_at=datetime.fromisoformat(conv_data["last_message_at"].replace("Z", "+00:00")) if conv_data.get("last_message_at") else None,
                    last_message_content=conv_data.get("last_message_content"),
                    unread_count_participant1=conv_data.get("unread_count_participant1", 0),
                    unread_count_participant2=conv_data.get("unread_count_participant2", 0),
                    metadata=conv_data.get("metadata", {}),
                    created_at=datetime.fromisoformat(conv_data["created_at"].replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat(conv_data["updated_at"].replace("Z", "+00:00"))
                ))
            
            return conversations
            
        except Exception as e:
            raise APIException(
                status_code=500,
                detail=f"Failed to get conversations: {str(e)}"
            )
    
    async def get_messages(
        self,
        conversation_id: str,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Message]:
        """Get messages for a conversation"""
        try:
            supabase = self._get_supabase_client()
            
            # Verify user has access to this conversation
            conv_response = supabase.table("conversations")\
                .select("*")\
                .eq("id", conversation_id)\
                .execute()
            
            if not conv_response.data:
                raise APIException(
                    code="CONVERSATION_NOT_FOUND",
                    message="Conversation not found",
                    status_code=404
                )
            
            conv = conv_response.data[0]
            if conv["participant1_id"] != user_id and conv["participant2_id"] != user_id:
                raise APIException(
                    code="ACCESS_DENIED",
                    message="Access denied",
                    status_code=403
                )
            
            # Get messages
            response = supabase.table("messages")\
                .select("*")\
                .eq("conversation_id", conversation_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .offset(offset)\
                .execute()
            
            messages = []
            for msg_data in response.data:
                messages.append(Message(
                    id=msg_data["id"],
                    conversation_id=msg_data["conversation_id"],
                    sender_id=msg_data["sender_id"],
                    receiver_id=msg_data["receiver_id"],
                    content=msg_data["content"],
                    is_read=msg_data.get("is_read", False),
                    read_at=datetime.fromisoformat(msg_data["read_at"].replace("Z", "+00:00")) if msg_data.get("read_at") else None,
                    metadata=msg_data.get("metadata", {}),
                    created_at=datetime.fromisoformat(msg_data["created_at"].replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat(msg_data["updated_at"].replace("Z", "+00:00"))
                ))
            
            return list(reversed(messages))  # Return in chronological order
            
        except APIException:
            raise
        except Exception as e:
            raise APIException(
                code="GET_MESSAGES_ERROR",
                message=f"Failed to get messages: {str(e)}",
                status_code=500
            )
    
    async def create_or_get_conversation(
        self,
        participant1_id: str,
        participant2_id: str
    ) -> Conversation:
        """Create or get existing conversation"""
        try:
            supabase = self._get_supabase_client()
            
            # Try to find existing conversation (order doesn't matter)
            response1 = supabase.table("conversations")\
                .select("*")\
                .eq("participant1_id", participant1_id)\
                .eq("participant2_id", participant2_id)\
                .execute()
            
            response2 = supabase.table("conversations")\
                .select("*")\
                .eq("participant1_id", participant2_id)\
                .eq("participant2_id", participant1_id)\
                .execute()
            
            if response1.data:
                conv_data = response1.data[0]
            elif response2.data:
                conv_data = response2.data[0]
            else:
                # Create new conversation
                insert_response = supabase.table("conversations")\
                    .insert({
                        "participant1_id": participant1_id,
                        "participant2_id": participant2_id
                    })\
                    .execute()
                conv_data = insert_response.data[0]
            
            return Conversation(
                id=conv_data["id"],
                participant1_id=conv_data["participant1_id"],
                participant2_id=conv_data["participant2_id"],
                last_message_at=datetime.fromisoformat(conv_data["last_message_at"].replace("Z", "+00:00")) if conv_data.get("last_message_at") else None,
                last_message_content=conv_data.get("last_message_content"),
                unread_count_participant1=conv_data.get("unread_count_participant1", 0),
                unread_count_participant2=conv_data.get("unread_count_participant2", 0),
                metadata=conv_data.get("metadata", {}),
                created_at=datetime.fromisoformat(conv_data["created_at"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(conv_data["updated_at"].replace("Z", "+00:00"))
            )
            
        except Exception as e:
            raise APIException(
                code="CREATE_CONVERSATION_ERROR",
                message=f"Failed to create conversation: {str(e)}",
                status_code=500
            )
    
    async def send_message(self, request: MessageCreate) -> Message:
        """Send a message"""
        try:
            supabase = self._get_supabase_client()
            
            # Verify conversation exists and user is participant
            conv_response = supabase.table("conversations")\
                .select("*")\
                .eq("id", request.conversation_id)\
                .execute()
            
            if not conv_response.data:
                raise APIException(
                    code="CONVERSATION_NOT_FOUND",
                    message="Conversation not found",
                    status_code=404
                )
            
            conv = conv_response.data[0]
            if conv["participant1_id"] != request.sender_id and conv["participant2_id"] != request.sender_id:
                raise APIException(
                    code="ACCESS_DENIED",
                    message="Access denied",
                    status_code=403
                )
            
            # Determine receiver
            receiver_id = conv["participant2_id"] if conv["participant1_id"] == request.sender_id else conv["participant1_id"]
            
            if request.receiver_id != receiver_id:
                raise APIException(
                    code="RECEIVER_ID_MISMATCH",
                    message="Receiver ID mismatch",
                    status_code=400
                )
            
            # Insert message
            insert_response = supabase.table("messages")\
                .insert({
                    "conversation_id": request.conversation_id,
                    "sender_id": request.sender_id,
                    "receiver_id": request.receiver_id,
                    "content": request.content,
                    "metadata": request.metadata or {}
                })\
                .execute()
            
            msg_data = insert_response.data[0]
            
            return Message(
                id=msg_data["id"],
                conversation_id=msg_data["conversation_id"],
                sender_id=msg_data["sender_id"],
                receiver_id=msg_data["receiver_id"],
                content=msg_data["content"],
                is_read=msg_data.get("is_read", False),
                read_at=datetime.fromisoformat(msg_data["read_at"].replace("Z", "+00:00")) if msg_data.get("read_at") else None,
                metadata=msg_data.get("metadata", {}),
                created_at=datetime.fromisoformat(msg_data["created_at"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(msg_data["updated_at"].replace("Z", "+00:00"))
            )
            
        except APIException:
            raise
        except Exception as e:
            raise APIException(
                status_code=500,
                detail=f"Failed to send message: {str(e)}"
            )
    
    async def improve_message(
        self,
        text: str,
        tone: str = "professional",
        context: Optional[str] = None
    ) -> str:
        """Improve message using AI"""
        try:
            self._initialize_gemini()
            
            tone_descriptions = {
                "professional": "professional, clear, and respectful",
                "friendly": "friendly, warm, and approachable",
                "formal": "formal, polite, and structured",
                "casual": "casual, relaxed, and conversational"
            }
            
            tone_desc = tone_descriptions.get(tone, "professional, clear, and respectful")
            
            prompt = f"""Rewrite the following message to make it more {tone_desc}. 
Keep the original meaning and intent, but improve:
- Grammar and spelling
- Clarity and conciseness
- Professional tone
- Politeness and respect

{f"Context: {context}" if context else ""}

Original message:
{text}

Provide only the improved message, no additional explanation:"""
            
            # Use faster model for better response times
            model_name = getattr(settings, 'gemini_model_fast', 'gemini-1.5-flash')
            try:
                model = genai.GenerativeModel(model_name)
            except:
                # Fallback to standard if fast model not available
                model_name = getattr(settings, 'gemini_model_standard', 'gemini-1.5-flash')
                try:
                    model = genai.GenerativeModel(model_name)
                except:
                    model = genai.GenerativeModel('gemini-3-pro-preview')
            
            response = model.generate_content(prompt)
            
            if hasattr(response, 'text') and response.text:
                return response.text.strip()
            elif hasattr(response, 'candidates') and response.candidates:
                return response.candidates[0].content.parts[0].text.strip()
            else:
                return text  # Fallback to original
            
        except Exception as e:
            print(f"[MessagesService] Error improving message: {str(e)}")
            return text  # Fallback to original
    
    async def get_message_suggestions(
        self,
        context: str,
        recipient_role: Optional[str] = None
    ) -> List[str]:
        """Get AI-powered message suggestions"""
        try:
            self._initialize_gemini()
            
            role_context = f" The recipient is a {recipient_role}." if recipient_role else ""
            
            prompt = f"""Generate 3 professional message suggestions based on the following context.{role_context}

Context: {context}

Provide 3 different message options that are:
- Professional and respectful
- Clear and concise
- Appropriate for the context
- Varied in approach (one can be more formal, one more friendly, etc.)

Format as a JSON array of strings:
["message 1", "message 2", "message 3"]

Only return the JSON array, no additional text:"""
            
            # Use faster model for better response times
            model_name = getattr(settings, 'gemini_model_fast', 'gemini-1.5-flash')
            try:
                model = genai.GenerativeModel(model_name)
            except:
                # Fallback to standard if fast model not available
                model_name = getattr(settings, 'gemini_model_standard', 'gemini-1.5-flash')
                try:
                    model = genai.GenerativeModel(model_name)
                except:
                    model = genai.GenerativeModel('gemini-3-pro-preview')
            
            response = model.generate_content(prompt)
            
            response_text = response.text.strip() if hasattr(response, 'text') else ""
            if not response_text and hasattr(response, 'candidates') and response.candidates:
                response_text = response.candidates[0].content.parts[0].text.strip()
            
            # Extract JSON
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            suggestions = json.loads(response_text)
            return suggestions if isinstance(suggestions, list) else []
            
        except Exception as e:
            print(f"[MessagesService] Error getting suggestions: {str(e)}")
            return []
    
    async def mark_as_read(self, message_id: str, user_id: str) -> Message:
        """Mark a message as read"""
        try:
            supabase = self._get_supabase_client()
            
            # Verify user is receiver
            msg_response = supabase.table("messages")\
                .select("*")\
                .eq("id", message_id)\
                .execute()
            
            if not msg_response.data:
                raise APIException(
                    code="MESSAGE_NOT_FOUND",
                    message="Message not found",
                    status_code=404
                )
            
            msg = msg_response.data[0]
            if msg["receiver_id"] != user_id:
                raise APIException(
                    code="ACCESS_DENIED",
                    message="Access denied",
                    status_code=403
                )
            
            # Update message
            update_response = supabase.table("messages")\
                .update({
                    "is_read": True,
                    "read_at": datetime.utcnow().isoformat()
                })\
                .eq("id", message_id)\
                .execute()
            
            msg_data = update_response.data[0]
            
            return Message(
                id=msg_data["id"],
                conversation_id=msg_data["conversation_id"],
                sender_id=msg_data["sender_id"],
                receiver_id=msg_data["receiver_id"],
                content=msg_data["content"],
                is_read=msg_data.get("is_read", False),
                read_at=datetime.fromisoformat(msg_data["read_at"].replace("Z", "+00:00")) if msg_data.get("read_at") else None,
                metadata=msg_data.get("metadata", {}),
                created_at=datetime.fromisoformat(msg_data["created_at"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(msg_data["updated_at"].replace("Z", "+00:00"))
            )
            
        except APIException:
            raise
        except Exception as e:
            raise APIException(
                status_code=500,
                detail=f"Failed to mark message as read: {str(e)}"
            )


# Global instance
messages_service = MessagesService()


