"""Main FastAPI application"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings

# Set up Google Cloud authentication early (before any services initialize)
def setup_google_cloud_auth():
    """
    Set up Google Cloud authentication from service account.
    Supports multiple methods:
    1. GOOGLE_APPLICATION_CREDENTIALS environment variable (explicit file path)
    2. Service account JSON file path from config
    3. Application Default Credentials (ADC) - automatic on Cloud Run
    """
    try:
        # Check if already set in environment
        if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
            creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            if os.path.exists(creds_path):
                print(f"✓ Using GOOGLE_APPLICATION_CREDENTIALS from environment: {creds_path}")
                return
            else:
                print(f"⚠ Warning: GOOGLE_APPLICATION_CREDENTIALS points to non-existent file: {creds_path}")
        
        # Get the credentials path from settings (if provided)
        creds_path = settings.google_application_credentials
        
        # If no path configured, try to find service-account.json in common locations
        if not creds_path:
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            alternative_paths = [
                os.path.join(backend_dir, "service-account.json"),
                "./service-account.json",
                "service-account.json"
            ]
            
            for alt_path in alternative_paths:
                alt_path = os.path.normpath(alt_path)
                if os.path.exists(alt_path):
                    creds_path = alt_path
                    break
        
        # If path is relative and found, make it absolute
        if creds_path and os.path.exists(creds_path):
            if not os.path.isabs(creds_path):
                backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                creds_path = os.path.join(backend_dir, creds_path)
                creds_path = os.path.normpath(creds_path)
            
            # Set environment variable for Google Cloud libraries
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
            print(f"✓ Google Cloud authentication configured from: {creds_path}")
        else:
            # No service account file found - will use Application Default Credentials (ADC)
            # This is expected and works automatically on Google Cloud Run
            # Don't verify ADC here - it will be available when services need it
            # Verification would block startup unnecessarily
            print(f"✓ Will use Application Default Credentials (ADC) for Google Cloud when needed")
            print(f"   On Cloud Run, the service account attached to the service will be used automatically.")
        
    except Exception as e:
        # Don't block startup - authentication will be handled when services initialize
        print(f"⚠ Warning: Failed to set up Google Cloud authentication: {str(e)}")
        print(f"   On Cloud Run, authentication will use the service account attached to the service.")
        print(f"   Application will continue to start - authentication will be retried when services need it.")

# Initialize authentication at module load (non-blocking)
# On Cloud Run, ADC will work automatically when services need credentials
try:
    setup_google_cloud_auth()
except Exception as e:
    # Don't fail startup if auth setup has issues - services will handle it
    print(f"⚠ Warning: Auth setup failed during module load: {str(e)}")
    print("   Application will continue - authentication will be handled per-service.")
from app.routers import health, rag, doubt, homework, microplan, exam, quiz, videos, hots, admin, progress, analytics, translation, ai_tutoring, teacher_tools, wellbeing, teacher, messages, notification
from app.utils.exceptions import (
    APIException,
    api_exception_handler,
    validation_exception_handler,
    generic_exception_handler
)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="Class 12 Learning Platform API",
    description="Backend API for intelligent Class 12 learning platform with RAG, LLM, and adaptive learning",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add exception handlers
app.add_exception_handler(APIException, api_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(rag.router, prefix="/api", tags=["rag"])
app.include_router(doubt.router, prefix="/api", tags=["doubt"])
app.include_router(homework.router, prefix="/api", tags=["homework"])
app.include_router(microplan.router, prefix="/api", tags=["microplan"])
app.include_router(exam.router, prefix="/api", tags=["exam"])
app.include_router(quiz.router, prefix="/api", tags=["quiz"])
app.include_router(videos.router, prefix="/api/videos", tags=["videos"])
app.include_router(hots.router, prefix="/api/hots", tags=["hots"])
app.include_router(admin.router, prefix="/api", tags=["admin"])
app.include_router(progress.router, prefix="/api", tags=["progress"])
app.include_router(analytics.router, prefix="/api", tags=["analytics"])
app.include_router(translation.router, prefix="/api", tags=["translation"])
app.include_router(ai_tutoring.router, prefix="/api", tags=["ai-tutoring"])
app.include_router(teacher_tools.router, prefix="/api", tags=["teacher-tools"])
app.include_router(teacher.router, prefix="/api", tags=["teacher"])
app.include_router(wellbeing.router, prefix="/api", tags=["wellbeing"])
app.include_router(messages.router, prefix="/api", tags=["messages"])
app.include_router(notification.router, prefix="/api", tags=["notifications"])

# Placeholder routers for future implementation
# app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
# app.include_router(packs.router, prefix="/api/packs", tags=["packs"])


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    port = os.getenv("PORT", str(settings.app_port))
    print(f"Starting Class 12 Learning Platform API in {settings.app_env} mode")
    print(f"Listening on port: {port}")
    print(f"CORS enabled for origins: {settings.cors_origins_list}")
    # Services will initialize lazily when needed - don't block startup


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("Shutting down Class 12 Learning Platform API")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", settings.app_port))
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=port,
        reload=settings.app_env == "development"
    )
