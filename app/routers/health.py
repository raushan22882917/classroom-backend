"""Health check endpoints"""

from fastapi import APIRouter
from app.models.base import BaseResponse

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint - responds immediately even if settings fail"""
    try:
        from app.config import settings
        return BaseResponse(
            success=True,
            message="Class 12 Learning Platform API is running"
        )
    except Exception:
        # Return a simple response even if config fails
        return {"status": "ok", "message": "API is running (config may have issues)"}


@router.get("/health/config", response_model=dict)
async def config_check():
    """Configuration check endpoint (non-sensitive info only)"""
    return {
        "app_env": settings.app_env,
        "vertex_ai_location": settings.vertex_ai_location,
        "vertex_ai_embedding_model": settings.vertex_ai_embedding_model,
        "pinecone_index_name": settings.pinecone_index_name,
        "rate_limit_per_minute": settings.rate_limit_per_minute,
        "cors_origins": settings.cors_origins_list
    }
