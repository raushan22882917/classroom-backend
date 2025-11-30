"""Messages endpoints for student-teacher communication"""

from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from app.models.base import Message, Conversation, MessageCreate, MessageImproveRequest, ConversationCreateRequest, MessageSuggestionsRequest
from app.services.messages_service import messages_service
from app.utils.exceptions import APIException

router = APIRouter(prefix="/messages", tags=["Messages"])


@router.get("/conversations", response_model=List[Conversation])
async def get_conversations(user_id: str = Query(..., description="User ID")):
    """
    Get all conversations for a user
    
    Args:
        user_id: User ID
        
    Returns:
        List of Conversation objects
    """
    try:
        if not user_id or not user_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID is required"
            )
        
        conversations = await messages_service.get_conversations(user_id)
        return conversations
        
    except APIException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversations: {str(e)}"
        )


@router.get("/conversations/{conversation_id}/messages", response_model=List[Message])
async def get_messages(
    conversation_id: str,
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Get messages for a conversation
    
    Args:
        conversation_id: Conversation ID
        user_id: User ID (for authorization)
        limit: Number of messages to fetch
        offset: Offset for pagination
        
    Returns:
        List of Message objects
    """
    try:
        if not conversation_id or not conversation_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Conversation ID is required"
            )
        
        messages = await messages_service.get_messages(
            conversation_id=conversation_id,
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        return messages
        
    except APIException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get messages: {str(e)}"
        )


@router.post("/conversations", response_model=Conversation)
async def create_or_get_conversation(request: ConversationCreateRequest):
    """
    Create or get existing conversation between two users
    
    Args:
        request: Conversation creation request with participant IDs
        
    Returns:
        Conversation object
    """
    try:
        if not request.participant1_id or not request.participant1_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Participant 1 ID is required"
            )
        
        if not request.participant2_id or not request.participant2_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Participant 2 ID is required"
            )
        
        conversation = await messages_service.create_or_get_conversation(
            participant1_id=request.participant1_id,
            participant2_id=request.participant2_id
        )
        return conversation
        
    except APIException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create conversation: {str(e)}"
        )


@router.post("/send", response_model=Message)
async def send_message(request: MessageCreate):
    """
    Send a message
    
    Args:
        request: Message creation request
        
    Returns:
        Created Message object
    """
    try:
        if not request.conversation_id or not request.conversation_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Conversation ID is required"
            )
        
        if not request.sender_id or not request.sender_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sender ID is required"
            )
        
        if not request.content or not request.content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message content is required"
            )
        
        message = await messages_service.send_message(request)
        return message
        
    except APIException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )


@router.post("/improve", response_model=dict)
async def improve_message(request: MessageImproveRequest):
    """
    Improve a message using AI to make it more professional
    
    Args:
        request: Message improvement request with original text and tone
        
    Returns:
        Improved message text
    """
    try:
        if not request.text or not request.text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message text is required"
            )
        
        improved = await messages_service.improve_message(
            text=request.text,
            tone=request.tone or "professional",
            context=request.context
        )
        return {"original": request.text, "improved": improved}
        
    except APIException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to improve message: {str(e)}"
        )


@router.post("/suggestions", response_model=List[str])
async def get_message_suggestions(request: MessageSuggestionsRequest):
    """
    Get AI-powered message suggestions based on context
    
    Args:
        request: Message suggestions request with context and recipient role
        
    Returns:
        List of suggested message texts
    """
    try:
        if not request.context or not request.context.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Context is required"
            )
        
        suggestions = await messages_service.get_message_suggestions(
            context=request.context,
            recipient_role=request.recipient_role
        )
        return suggestions
        
    except APIException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get suggestions: {str(e)}"
        )


@router.put("/messages/{message_id}/read", response_model=Message)
async def mark_message_read(
    message_id: str,
    user_id: str = Query(..., description="User ID")
):
    """
    Mark a message as read
    
    Args:
        message_id: Message ID
        user_id: User ID (for authorization)
        
    Returns:
        Updated Message object
    """
    try:
        if not message_id or not message_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message ID is required"
            )
        
        message = await messages_service.mark_as_read(message_id, user_id)
        return message
        
    except APIException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.detail
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark message as read: {str(e)}"
        )

