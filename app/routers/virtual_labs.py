"""Virtual Labs API endpoints for interactive science experiments"""

from fastapi import APIRouter, Query, HTTPException, Request, Depends
from typing import Optional, List
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.virtual_labs import (
    VirtualLabCreate,
    VirtualLabUpdate,
    VirtualLabResponse,
    VirtualLabListResponse,
    VirtualLabSessionCreate,
    VirtualLabSessionUpdate,
    VirtualLabSessionResponse,
    VirtualLabInteractionCreate,
    VirtualLabInteractionResponse,
    VirtualLabAIAssistanceCreate,
    VirtualLabAIAssistanceResponse,
    PerformanceMetrics,
    SessionPerformanceResponse,
    DifficultyLevel,
    CompletionStatus
)
from app.models.base import Subject
from app.utils.exceptions import APIException

# Import services lazily to avoid startup issues
virtual_labs_service = None
virtual_labs_ai_service = None

def get_virtual_labs_service():
    global virtual_labs_service
    if virtual_labs_service is None:
        from app.services.virtual_labs_service import virtual_labs_service as vls
        virtual_labs_service = vls
    return virtual_labs_service

def get_virtual_labs_ai_service():
    global virtual_labs_ai_service
    if virtual_labs_ai_service is None:
        from app.services.virtual_labs_ai_service import virtual_labs_ai_service as vlas
        virtual_labs_ai_service = vlas
    return virtual_labs_ai_service

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


# Virtual Labs Management Endpoints

@router.get("/virtual-labs", response_model=VirtualLabListResponse)
@limiter.limit("100/minute")
async def list_virtual_labs(
    request: Request,
    subject: Optional[Subject] = Query(None, description="Filter by subject"),
    class_grade: Optional[int] = Query(None, description="Filter by grade level", ge=1, le=12),
    difficulty_level: Optional[DifficultyLevel] = Query(None, description="Filter by difficulty"),
    is_active: bool = Query(True, description="Filter active labs"),
    limit: int = Query(10, description="Maximum number of results", ge=1, le=100),
    offset: int = Query(0, description="Pagination offset", ge=0)
):
    """
    List all virtual labs with filtering options
    
    Query Parameters:
    - subject: Filter by subject (mathematics, physics, chemistry, biology)
    - class_grade: Filter by grade level (1-12)
    - difficulty_level: Filter by difficulty (beginner, intermediate, advanced)
    - is_active: Filter active labs (default: true)
    - limit: Maximum number of results (default: 10, max: 100)
    - offset: Pagination offset (default: 0)
    
    Returns:
    - VirtualLabListResponse with labs, total count, and pagination info
    """
    try:
        vls = get_virtual_labs_service()
        result = await vls.get_virtual_labs(
            subject=subject,
            class_grade=class_grade,
            difficulty_level=difficulty_level,
            is_active=is_active,
            limit=limit,
            offset=offset
        )
        
        return VirtualLabListResponse(**result)
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/virtual-labs", response_model=VirtualLabResponse, status_code=201)
@limiter.limit("20/minute")
async def create_virtual_lab(
    request: Request,
    lab_data: VirtualLabCreate,
    # TODO: Add authentication dependency
    # current_user: User = Depends(get_current_user)
):
    """
    Create a new virtual lab
    
    Authentication: Required (Teacher/Admin only)
    
    Request Body:
    - VirtualLabCreate with all lab details including HTML/CSS/JS content
    
    Returns:
    - VirtualLabResponse with created lab details
    
    Notes:
    - Only teachers and admins can create virtual labs
    - HTML/CSS/JS content is validated for security
    - Automatically sets created_by to current user
    """
    try:
        # TODO: Get user ID from authentication
        created_by = "temp-user-id"  # Replace with actual user ID from auth
        
        vls = get_virtual_labs_service()
        lab = await vls.create_virtual_lab(
            lab_data=lab_data,
            created_by=created_by
        )
        
        return lab
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/virtual-labs/{lab_id}", response_model=VirtualLabResponse)
@limiter.limit("100/minute")
async def get_virtual_lab(
    request: Request,
    lab_id: str
):
    """
    Get specific virtual lab details
    
    Path Parameters:
    - lab_id: Virtual lab ID (UUID)
    
    Returns:
    - VirtualLabResponse with complete lab details
    
    Raises:
    - 404: Lab not found or inactive
    """
    try:
        vls = get_virtual_labs_service()
        lab = await vls.get_virtual_lab(lab_id)
        return lab
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/virtual-labs/{lab_id}", response_model=VirtualLabResponse)
@limiter.limit("30/minute")
async def update_virtual_lab(
    request: Request,
    lab_id: str,
    lab_data: VirtualLabUpdate,
    # TODO: Add authentication dependency
    # current_user: User = Depends(get_current_user)
):
    """
    Update virtual lab
    
    Authentication: Required (Creator/Admin only)
    
    Path Parameters:
    - lab_id: Virtual lab ID (UUID)
    
    Request Body:
    - VirtualLabUpdate with fields to update (partial updates allowed)
    
    Returns:
    - VirtualLabResponse with updated lab details
    
    Notes:
    - Only lab creator or admin can update
    - Partial updates are supported
    """
    try:
        # TODO: Get user ID from authentication
        user_id = "temp-user-id"  # Replace with actual user ID from auth
        
        vls = get_virtual_labs_service()
        lab = await vls.update_virtual_lab(
            lab_id=lab_id,
            lab_data=lab_data,
            user_id=user_id
        )
        
        return lab
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/virtual-labs/{lab_id}")
@limiter.limit("20/minute")
async def delete_virtual_lab(
    request: Request,
    lab_id: str,
    # TODO: Add authentication dependency
    # current_user: User = Depends(get_current_user)
):
    """
    Delete virtual lab (soft delete)
    
    Authentication: Required (Creator/Admin only)
    
    Path Parameters:
    - lab_id: Virtual lab ID (UUID)
    
    Returns:
    - Success message
    
    Notes:
    - Performs soft delete by setting is_active=false
    - Only lab creator or admin can delete
    """
    try:
        # TODO: Get user ID from authentication
        user_id = "temp-user-id"  # Replace with actual user ID from auth
        
        vls = get_virtual_labs_service()
        result = await vls.delete_virtual_lab(
            lab_id=lab_id,
            user_id=user_id
        )
        
        return result
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Lab Sessions Management Endpoints

@router.post("/virtual-labs/sessions", response_model=VirtualLabSessionResponse, status_code=201)
@limiter.limit("50/minute")
async def create_lab_session(
    request: Request,
    session_data: VirtualLabSessionCreate,
    # TODO: Add authentication dependency
    # current_user: User = Depends(get_current_user)
):
    """
    Start a new lab session
    
    Authentication: Required (Student)
    
    Request Body:
    - VirtualLabSessionCreate with user_id, lab_id, and optional session_name
    
    Returns:
    - VirtualLabSessionResponse with session details
    
    Notes:
    - Creates a new session for the user to work on the lab
    - Session starts in 'in_progress' status
    - Tracks session start time and counters
    """
    try:
        vls = get_virtual_labs_service()
        session = await vls.create_session(session_data)
        return session
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/virtual-labs/sessions", response_model=List[VirtualLabSessionResponse])
@limiter.limit("100/minute")
async def get_user_sessions(
    request: Request,
    user_id: str = Query(..., description="User ID"),
    lab_id: Optional[str] = Query(None, description="Filter by specific lab"),
    completion_status: Optional[CompletionStatus] = Query(None, description="Filter by status"),
    limit: int = Query(10, description="Maximum number of results", ge=1, le=100),
    offset: int = Query(0, description="Pagination offset", ge=0)
):
    """
    Get user's lab sessions
    
    Query Parameters:
    - user_id: User ID (required)
    - lab_id: Filter by specific lab (optional)
    - completion_status: Filter by status (optional)
    - limit: Maximum number of results (default: 10, max: 100)
    - offset: Pagination offset (default: 0)
    
    Returns:
    - List of VirtualLabSessionResponse objects
    """
    try:
        vls = get_virtual_labs_service()
        sessions = await vls.get_user_sessions(
            user_id=user_id,
            lab_id=lab_id,
            completion_status=completion_status,
            limit=limit,
            offset=offset
        )
        
        return sessions
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/virtual-labs/sessions/{session_id}", response_model=VirtualLabSessionResponse)
@limiter.limit("50/minute")
async def update_lab_session(
    request: Request,
    session_id: str,
    session_data: VirtualLabSessionUpdate,
    user_id: str = Query(..., description="User ID for authorization")
):
    """
    Update lab session (completion, feedback, etc.)
    
    Path Parameters:
    - session_id: Session ID (UUID)
    
    Query Parameters:
    - user_id: User ID for authorization
    
    Request Body:
    - VirtualLabSessionUpdate with fields to update
    
    Returns:
    - VirtualLabSessionResponse with updated session details
    
    Notes:
    - Only session owner can update
    - Used to mark completion, add feedback, update scores
    """
    try:
        vls = get_virtual_labs_service()
        session = await vls.update_session(
            session_id=session_id,
            session_data=session_data,
            user_id=user_id
        )
        
        return session
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Interaction Tracking Endpoints

@router.post("/virtual-labs/interactions", response_model=VirtualLabInteractionResponse, status_code=201)
@limiter.limit("200/minute")
async def record_interaction(
    request: Request,
    interaction_data: VirtualLabInteractionCreate
):
    """
    Record user interaction in virtual lab
    
    Request Body:
    - VirtualLabInteractionCreate with interaction details
    
    Returns:
    - VirtualLabInteractionResponse with recorded interaction
    
    Notes:
    - High rate limit for frequent interactions
    - Automatically updates session interaction counters
    - Used for analytics and performance tracking
    """
    try:
        vls = get_virtual_labs_service()
        interaction = await vls.record_interaction(interaction_data)
        return interaction
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/virtual-labs/sessions/{session_id}/interactions", response_model=List[VirtualLabInteractionResponse])
@limiter.limit("100/minute")
async def get_session_interactions(
    request: Request,
    session_id: str,
    user_id: str = Query(..., description="User ID for authorization")
):
    """
    Get all interactions for a session
    
    Path Parameters:
    - session_id: Session ID (UUID)
    
    Query Parameters:
    - user_id: User ID for authorization
    
    Returns:
    - List of VirtualLabInteractionResponse objects
    
    Notes:
    - Only session owner can view interactions
    - Ordered by timestamp (oldest first)
    """
    try:
        vls = get_virtual_labs_service()
        interactions = await vls.get_session_interactions(
            session_id=session_id,
            user_id=user_id
        )
        
        return interactions
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# AI Assistance Endpoints

@router.post("/virtual-labs/ai-assistance", response_model=VirtualLabAIAssistanceResponse, status_code=201)
@limiter.limit("30/minute")
async def request_ai_assistance(
    request: Request,
    assistance_data: VirtualLabAIAssistanceCreate
):
    """
    Request AI help for virtual lab
    
    Request Body:
    - VirtualLabAIAssistanceCreate with query and context
    
    Returns:
    - VirtualLabAIAssistanceResponse with AI response
    
    Notes:
    - Uses Gemini AI for context-aware assistance
    - Automatically updates session AI request counter
    - Provides educational guidance, not direct answers
    """
    try:
        vlas = get_virtual_labs_ai_service()
        assistance = await vlas.create_ai_assistance(assistance_data)
        return assistance
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/virtual-labs/sessions/{session_id}/ai-assistance", response_model=List[VirtualLabAIAssistanceResponse])
@limiter.limit("100/minute")
async def get_session_ai_assistance(
    request: Request,
    session_id: str,
    user_id: str = Query(..., description="User ID for authorization")
):
    """
    Get AI assistance history for session
    
    Path Parameters:
    - session_id: Session ID (UUID)
    
    Query Parameters:
    - user_id: User ID for authorization
    
    Returns:
    - List of VirtualLabAIAssistanceResponse objects
    
    Notes:
    - Only session owner can view AI assistance history
    - Ordered by timestamp (oldest first)
    """
    try:
        vlas = get_virtual_labs_ai_service()
        assistance_history = await vlas.get_session_ai_assistance(
            session_id=session_id,
            user_id=user_id
        )
        
        return assistance_history
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Performance Analytics Endpoints

@router.get("/virtual-labs/sessions/{session_id}/performance", response_model=SessionPerformanceResponse)
@limiter.limit("50/minute")
async def get_session_performance(
    request: Request,
    session_id: str,
    user_id: str = Query(..., description="User ID for authorization")
):
    """
    Get detailed performance metrics for session
    
    Path Parameters:
    - session_id: Session ID (UUID)
    
    Query Parameters:
    - user_id: User ID for authorization
    
    Returns:
    - SessionPerformanceResponse with detailed metrics
    
    Notes:
    - Calculates performance metrics from interactions
    - Includes concept mastery analysis
    - Only session owner can view performance
    """
    try:
        # TODO: Implement performance calculation logic
        # This is a placeholder implementation
        
        # Verify session ownership
        vls = get_virtual_labs_service()
        interactions = await vls.get_session_interactions(session_id, user_id)
        
        # Calculate basic metrics (placeholder)
        metrics = PerformanceMetrics(
            session_duration=1800,  # 30 minutes
            interactions_count=len(interactions),
            completion_percentage=85.0,
            accuracy_score=78.5,
            help_requests=3,
            time_on_task=1650,
            gesture_efficiency=0.85,
            concept_mastery=[
                ConceptMastery(concept_name="basic_setup", mastery_score=0.9),
                ConceptMastery(concept_name="parameter_adjustment", mastery_score=0.7),
                ConceptMastery(concept_name="result_analysis", mastery_score=0.8)
            ]
        )
        
        return SessionPerformanceResponse(
            session_id=session_id,
            metrics=metrics
        )
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Health Check Endpoint

@router.get("/virtual-labs/health")
@limiter.limit("100/minute")
async def virtual_labs_health(request: Request):
    """
    Health check for Virtual Labs service
    
    Returns:
    - Service status and basic statistics
    """
    try:
        vls = get_virtual_labs_service()
        
        # Test if tables exist by trying to query them
        try:
            labs_response = vls.supabase.table("virtual_labs")\
                .select("id", count="exact")\
                .limit(1)\
                .execute()
            
            sessions_response = vls.supabase.table("virtual_lab_sessions")\
                .select("id", count="exact")\
                .limit(1)\
                .execute()
            
            total_labs = labs_response.count if hasattr(labs_response, 'count') else 0
            total_sessions = sessions_response.count if hasattr(sessions_response, 'count') else 0
            
            return {
                "status": "healthy",
                "service": "Virtual Labs",
                "version": "1.0.0",
                "database_status": "connected",
                "tables_status": "ready",
                "stats": {
                    "total_labs": total_labs,
                    "total_sessions": total_sessions
                },
                "features": [
                    "Interactive Lab Creation",
                    "Real-time Interaction Tracking", 
                    "AI-Powered Assistance",
                    "Performance Analytics"
                ]
            }
            
        except Exception as db_error:
            # Tables don't exist
            error_str = str(db_error).lower()
            if "relation" in error_str and "does not exist" in error_str:
                return {
                    "status": "setup_required",
                    "service": "Virtual Labs",
                    "version": "1.0.0",
                    "database_status": "connected",
                    "tables_status": "missing",
                    "message": "Virtual Labs database tables need to be created",
                    "setup_instructions": {
                        "step_1": "Go to your Supabase dashboard",
                        "step_2": "Navigate to SQL Editor",
                        "step_3": "Run the contents of 'supabase_migration_virtual_labs.sql'",
                        "step_4": "Refresh this endpoint to verify setup"
                    },
                    "migration_file": "supabase_migration_virtual_labs.sql",
                    "error": str(db_error)
                }
            else:
                raise db_error
        
    except Exception as e:
        return {
            "status": "error",
            "service": "Virtual Labs",
            "error": str(e),
            "message": "Service unavailable - check database connection"
        }