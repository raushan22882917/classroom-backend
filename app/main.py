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

# Import routers with error handling - app can start even if some routers fail
_router_imports = {}
_router_errors = []

try:
    from app.routers import health
    _router_imports['health'] = health
except Exception as e:
    _router_errors.append(f"health: {str(e)}")
    print(f"⚠ Warning: Failed to import health router: {e}")

try:
    from app.routers import rag
    _router_imports['rag'] = rag
except Exception as e:
    _router_errors.append(f"rag: {str(e)}")
    print(f"⚠ Warning: Failed to import rag router: {e}")

try:
    from app.routers import doubt
    _router_imports['doubt'] = doubt
except Exception as e:
    _router_errors.append(f"doubt: {str(e)}")
    print(f"⚠ Warning: Failed to import doubt router: {e}")

try:
    from app.routers import homework
    _router_imports['homework'] = homework
except Exception as e:
    _router_errors.append(f"homework: {str(e)}")
    print(f"⚠ Warning: Failed to import homework router: {e}")

try:
    from app.routers import microplan
    _router_imports['microplan'] = microplan
except Exception as e:
    _router_errors.append(f"microplan: {str(e)}")
    print(f"⚠ Warning: Failed to import microplan router: {e}")

try:
    from app.routers import exam
    _router_imports['exam'] = exam
except Exception as e:
    _router_errors.append(f"exam: {str(e)}")
    print(f"⚠ Warning: Failed to import exam router: {e}")

try:
    from app.routers import quiz
    _router_imports['quiz'] = quiz
except Exception as e:
    _router_errors.append(f"quiz: {str(e)}")
    print(f"⚠ Warning: Failed to import quiz router: {e}")

try:
    from app.routers import videos
    _router_imports['videos'] = videos
except Exception as e:
    _router_errors.append(f"videos: {str(e)}")
    print(f"⚠ Warning: Failed to import videos router: {e}")

try:
    from app.routers import hots
    _router_imports['hots'] = hots
except Exception as e:
    _router_errors.append(f"hots: {str(e)}")
    print(f"⚠ Warning: Failed to import hots router: {e}")

try:
    from app.routers import admin
    _router_imports['admin'] = admin
except Exception as e:
    _router_errors.append(f"admin: {str(e)}")
    print(f"⚠ Warning: Failed to import admin router: {e}")

try:
    from app.routers import progress
    _router_imports['progress'] = progress
except Exception as e:
    _router_errors.append(f"progress: {str(e)}")
    print(f"⚠ Warning: Failed to import progress router: {e}")

try:
    from app.routers import analytics
    _router_imports['analytics'] = analytics
except Exception as e:
    _router_errors.append(f"analytics: {str(e)}")
    print(f"⚠ Warning: Failed to import analytics router: {e}")

try:
    from app.routers import translation
    _router_imports['translation'] = translation
except Exception as e:
    _router_errors.append(f"translation: {str(e)}")
    print(f"⚠ Warning: Failed to import translation router: {e}")

try:
    from app.routers import ai_tutoring
    _router_imports['ai_tutoring'] = ai_tutoring
except Exception as e:
    _router_errors.append(f"ai_tutoring: {str(e)}")
    print(f"⚠ Warning: Failed to import ai_tutoring router: {e}")

try:
    from app.routers import teacher_tools
    _router_imports['teacher_tools'] = teacher_tools
except Exception as e:
    _router_errors.append(f"teacher_tools: {str(e)}")
    print(f"⚠ Warning: Failed to import teacher_tools router: {e}")

try:
    from app.routers import wellbeing
    _router_imports['wellbeing'] = wellbeing
except Exception as e:
    _router_errors.append(f"wellbeing: {str(e)}")
    print(f"⚠ Warning: Failed to import wellbeing router: {e}")

try:
    from app.routers import teacher
    _router_imports['teacher'] = teacher
except Exception as e:
    _router_errors.append(f"teacher: {str(e)}")
    print(f"⚠ Warning: Failed to import teacher router: {e}")

try:
    from app.routers import messages
    _router_imports['messages'] = messages
except Exception as e:
    _router_errors.append(f"messages: {str(e)}")
    print(f"⚠ Warning: Failed to import messages router: {e}")

try:
    from app.routers import notification
    _router_imports['notification'] = notification
except Exception as e:
    _router_errors.append(f"notification: {str(e)}")
    print(f"⚠ Warning: Failed to import notification router: {e}")

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

# Configure CORS - use defaults if settings fail to load
try:
    cors_origins = settings.cors_origins_list
except Exception:
    # Default CORS origins if settings fail
    cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add a minimal root endpoint that responds immediately (for startup probe)
@app.get("/")
async def root():
    """Root endpoint - responds immediately for startup probe"""
    return {"status": "ok", "message": "Classroom Backend API"}

# Add alias routes for backward compatibility (proxy /ai-tutoring/* to /api/ai-tutoring/*)
# This allows frontend to call /ai-tutoring/sessions instead of /api/ai-tutoring/sessions
from fastapi import Request, Query
from fastapi.responses import JSONResponse

@app.get("/ai-tutoring/sessions")
async def ai_tutoring_sessions_alias(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Alias route for /ai-tutoring/sessions -> /api/ai-tutoring/sessions
    This maintains backward compatibility for frontend calls that omit the /api prefix
    """
    # Check if the router is available
    if 'ai_tutoring' not in _router_imports:
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "AI Tutoring service is not available",
                    "retryable": True
                }
            }
        )
    
    # Import and call the actual handler
    try:
        from app.routers.ai_tutoring import get_sessions
        # Call the actual handler function
        return await get_sessions(user_id=user_id, limit=limit, offset=offset)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": f"Failed to fetch sessions: {str(e)}",
                    "retryable": True
                }
            }
        )

# Include routers (only those that imported successfully)
if 'health' in _router_imports:
    app.include_router(_router_imports['health'].router, prefix="/api", tags=["health"])
if 'rag' in _router_imports:
    app.include_router(_router_imports['rag'].router, prefix="/api", tags=["rag"])
if 'doubt' in _router_imports:
    app.include_router(_router_imports['doubt'].router, prefix="/api", tags=["doubt"])
if 'homework' in _router_imports:
    app.include_router(_router_imports['homework'].router, prefix="/api", tags=["homework"])
if 'microplan' in _router_imports:
    app.include_router(_router_imports['microplan'].router, prefix="/api", tags=["microplan"])
if 'exam' in _router_imports:
    app.include_router(_router_imports['exam'].router, prefix="/api", tags=["exam"])
if 'quiz' in _router_imports:
    app.include_router(_router_imports['quiz'].router, prefix="/api", tags=["quiz"])
if 'videos' in _router_imports:
    app.include_router(_router_imports['videos'].router, prefix="/api/videos", tags=["videos"])
if 'hots' in _router_imports:
    app.include_router(_router_imports['hots'].router, prefix="/api/hots", tags=["hots"])
if 'admin' in _router_imports:
    app.include_router(_router_imports['admin'].router, prefix="/api", tags=["admin"])
if 'progress' in _router_imports:
    app.include_router(_router_imports['progress'].router, prefix="/api", tags=["progress"])
if 'analytics' in _router_imports:
    app.include_router(_router_imports['analytics'].router, prefix="/api", tags=["analytics"])
if 'translation' in _router_imports:
    app.include_router(_router_imports['translation'].router, prefix="/api", tags=["translation"])
if 'ai_tutoring' in _router_imports:
    app.include_router(_router_imports['ai_tutoring'].router, prefix="/api", tags=["ai-tutoring"])
if 'teacher_tools' in _router_imports:
    app.include_router(_router_imports['teacher_tools'].router, prefix="/api", tags=["teacher-tools"])
if 'teacher' in _router_imports:
    app.include_router(_router_imports['teacher'].router, prefix="/api", tags=["teacher"])
if 'wellbeing' in _router_imports:
    app.include_router(_router_imports['wellbeing'].router, prefix="/api", tags=["wellbeing"])
if 'messages' in _router_imports:
    app.include_router(_router_imports['messages'].router, prefix="/api", tags=["messages"])
if 'notification' in _router_imports:
    app.include_router(_router_imports['notification'].router, prefix="/api", tags=["notifications"])

# Log router import status
if _router_errors:
    print(f"⚠ Warning: {len(_router_errors)} router(s) failed to import: {', '.join(_router_errors)}")
else:
    print(f"✓ All {len(_router_imports)} routers imported successfully")

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
