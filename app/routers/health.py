"""Health check endpoints"""

from fastapi import APIRouter, HTTPException
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
    # Always return a response - never raise exceptions that could trigger generic handler
    try:
        from app.config import settings
    except ImportError:
        # If settings can't be imported, return minimal config
        return {
            "app_env": "unknown",
            "vertex_ai_location": "unknown",
            "vertex_ai_embedding_model": "unknown",
            "google_rag_engine": "vertex_ai_search",
            "vertex_search_engine_id": "not_configured",
            "rate_limit_per_minute": 100,
            "cors_origins": ["*"],
            "error": "Settings module not available"
        }
    except Exception:
        # If any other import error, return minimal config
        return {
            "app_env": "unknown",
            "vertex_ai_location": "unknown",
            "vertex_ai_embedding_model": "unknown",
            "google_rag_engine": "vertex_ai_search",
            "vertex_search_engine_id": "not_configured",
            "rate_limit_per_minute": 100,
            "cors_origins": ["*"],
            "error": "Failed to load settings"
        }
    
    # Safely access settings with fallback values
    try:
        cors_origins = settings.cors_origins_list
    except (AttributeError, Exception):
        # Fallback if property access fails
        try:
            cors_origins_str = getattr(settings, "cors_origins", "*")
            if cors_origins_str and isinstance(cors_origins_str, str):
                cors_origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]
            else:
                cors_origins = ["*"]
        except Exception:
            cors_origins = ["*"]
    
    # Build response with safe attribute access
    try:
        return {
            "app_env": getattr(settings, "app_env", "unknown"),
            "vertex_ai_location": getattr(settings, "vertex_ai_location", "unknown"),
            "vertex_ai_embedding_model": getattr(settings, "vertex_ai_embedding_model", "unknown"),
            "google_rag_engine": "vertex_ai_search",
            "vertex_search_engine_id": getattr(settings, "vertex_search_engine_id", "not_configured"),
            "rate_limit_per_minute": getattr(settings, "rate_limit_per_minute", 100),
            "cors_origins": cors_origins
        }
    except Exception as e:
        # Last resort - return minimal response instead of raising exception
        return {
            "app_env": "unknown",
            "vertex_ai_location": "unknown",
            "vertex_ai_embedding_model": "unknown",
            "google_rag_engine": "vertex_ai_search",
            "vertex_search_engine_id": "not_configured",
            "rate_limit_per_minute": 100,
            "cors_origins": ["*"],
            "error": f"Partial config load: {str(e)}"
        }
