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
# Only import essential routers at startup for faster boot time
_router_imports = {}
_router_errors = []

# Essential routers - import immediately
essential_routers = ['health']
for router_name in essential_routers:
    try:
        module = __import__(f"app.routers.{router_name}", fromlist=[router_name])
        _router_imports[router_name] = module
        print(f"✓ Imported essential router: {router_name}")
    except Exception as e:
        _router_errors.append(f"{router_name}: {str(e)}")
        print(f"⚠ Warning: Failed to import essential router {router_name}: {e}")

# Non-essential routers - defer import to startup event for faster boot
_deferred_routers = [
    'rag', 'doubt', 'homework', 'microplan', 'exam', 'quiz', 'videos', 
    'hots', 'admin', 'progress', 'analytics', 'translation', 'ai_tutoring',
    'teacher_tools', 'wellbeing', 'teacher', 'messages', 'notification', 
    'memory_intelligence'
]

# Magic learn router removed

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
    # Ensure critical origins are always included
    required_origins = [
        "https://eduverse-dashboard-iota.vercel.app",
        "http://localhost:8080",  # Frontend
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000"   # React dev server
    ]
    
    for origin in required_origins:
        if origin not in cors_origins:
            cors_origins.append(origin)
            
except Exception:
    # Default CORS origins if settings fail (must be explicit when allow_credentials=True)
    cors_origins = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8080",
        "https://eduverse-dashboard-iota.vercel.app"
    ]

# Log CORS configuration for debugging
print(f"✓ CORS configured for origins: {cors_origins}")

# Always allow localhost origins for development and testing
localhost_origins = [
    "http://localhost:8080",
    "http://localhost:8081", 
    "http://localhost:8082",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:8081",
    "http://127.0.0.1:8082"
]

cors_origins.extend(localhost_origins)
# Remove duplicates
cors_origins = list(set(cors_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Add additional CORS handling for all endpoints
@app.middleware("http")
async def add_cors_headers(request, call_next):
    """Add CORS headers for all requests"""
    
    # Get the origin from the request
    origin = request.headers.get("origin")
    
    # Log CORS requests for debugging
    if origin:
        print(f"🌐 CORS request from origin: {origin}")
        print(f"🌐 Request method: {request.method}")
        print(f"🌐 Request path: {request.url.path}")
    
    response = await call_next(request)
    
    # Allow localhost origins for development and configured origins
    if origin and (
        origin.startswith("http://localhost:") or 
        origin.startswith("https://localhost:") or
        origin in cors_origins
    ):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Expose-Headers"] = "*"
        print(f"✅ CORS headers added for origin: {origin}")
    elif origin:
        print(f"❌ CORS blocked for origin: {origin}")
    
    return response

# Add a minimal root endpoint that responds immediately (for startup probe)
@app.get("/")
async def root():
    """Root endpoint - responds immediately for startup probe"""
    return {"status": "ok", "message": "Classroom Backend API"}

# Add a simple readiness probe
@app.get("/ready")
async def readiness_probe():
    """Readiness probe - indicates when app is ready to serve traffic"""
    return {"status": "ready", "timestamp": __import__('time').time()}

# Core API info endpoint
@app.get("/info")
async def api_info():
    """API service information"""
    return {
        "service": "Educational Platform API",
        "status": "running",
        "version": "1.0.0",
        "features": ["AI Tutoring", "Content Management", "Assessment"]
    }

# Add alias routes for backward compatibility (proxy /ai-tutoring/* to /api/ai-tutoring/*)
# This allows frontend to call /ai-tutoring/sessions instead of /api/ai-tutoring/sessions
from fastapi import Request, Query
from fastapi.responses import JSONResponse

async def _handle_ai_tutoring_sessions(user_id: str, limit: int, offset: int):
    """Helper function to handle AI tutoring sessions requests"""
    # Try to import and call the actual handler, even if router import failed
    try:
        from app.routers.ai_tutoring import get_sessions
        # Call the actual handler function
        return await get_sessions(user_id=user_id, limit=limit, offset=offset)
    except ImportError as e:
        # Router module import failed - return empty sessions list as fallback
        return {
            "success": True,
            "sessions": [],
            "count": 0,
            "message": "AI Tutoring service is initializing. Please try again in a moment."
        }
    except Exception as e:
        # Other errors - log and return error response
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in AI tutoring sessions: {str(e)}")
        print(f"Traceback: {error_trace}")
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

async def _handle_ai_tutoring_create_session(request_data: dict):
    """Helper function to handle AI tutoring session creation"""
    try:
        from app.routers.ai_tutoring import create_session
        from app.models.ai_features import CreateSessionRequest
        
        session_request = CreateSessionRequest(**request_data)
        return await create_session(session_request)
    except ImportError as e:
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "error": "AI Tutoring service is initializing. Please try again in a moment."
            }
        )
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error creating AI tutoring session: {str(e)}")
        print(f"Traceback: {error_trace}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to create session: {str(e)}"
            }
        )

async def _handle_ai_tutoring_session_messages(session_id: str, limit: int):
    """Helper function to handle session messages requests"""
    try:
        from app.routers.ai_tutoring import get_session_messages
        # Call the actual handler function
        return await get_session_messages(session_id=session_id, limit=limit)
    except ImportError as e:
        # Router module import failed - return empty messages list as fallback
        return {
            "success": True,
            "messages": [],
            "count": 0,
            "message": "AI Tutoring service is initializing. Please try again in a moment."
        }
    except Exception as e:
        # Other errors - log and return error response
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in AI tutoring session messages: {str(e)}")
        print(f"Traceback: {error_trace}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": f"Failed to fetch session messages: {str(e)}",
                    "retryable": True
                }
            }
        )

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
    return await _handle_ai_tutoring_sessions(user_id, limit, offset)

@app.get("/api/ai-tutoring/sessions")
async def ai_tutoring_sessions_api(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Direct route for /api/ai-tutoring/sessions
    This ensures the endpoint works even if router import fails
    """
    return await _handle_ai_tutoring_sessions(user_id, limit, offset)

@app.get("/api/api/ai-tutoring/sessions")
async def ai_tutoring_sessions_api_double(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Route for /api/api/ai-tutoring/sessions (handles double /api prefix from frontend)
    This is a workaround for frontend API client adding /api prefix to already-prefixed URLs
    """
    return await _handle_ai_tutoring_sessions(user_id, limit, offset)

@app.post("/api/ai-tutoring/sessions")
async def ai_tutoring_create_session_api(request: Request):
    """
    Direct route for POST /api/ai-tutoring/sessions
    This ensures the endpoint works even if router import fails
    """
    # Try to import and call the actual handler
    try:
        from app.routers.ai_tutoring import create_session
        from app.models.ai_features import CreateSessionRequest
        # Parse request body
        body = await request.json()
        session_request = CreateSessionRequest(**body)
        return await create_session(session_request)
    except ImportError as e:
        # Router module import failed
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "AI Tutoring service is initializing. Please try again in a moment.",
                    "retryable": True
                }
            }
        )
    except Exception as e:
        # Other errors
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error creating AI tutoring session: {str(e)}")
        print(f"Traceback: {error_trace}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": f"Failed to create session: {str(e)}",
                    "retryable": True
                }
            }
        )

@app.post("/api/api/ai-tutoring/sessions")
async def ai_tutoring_create_session_api_double(request: Request):
    """
    Route for POST /api/api/ai-tutoring/sessions (handles double /api prefix from frontend)
    This is a workaround for frontend API client adding /api prefix to already-prefixed URLs
    """
    # Try to import and call the actual handler
    try:
        from app.routers.ai_tutoring import create_session
        from app.models.ai_features import CreateSessionRequest
        # Parse request body
        body = await request.json()
        session_request = CreateSessionRequest(**body)
        return await create_session(session_request)
    except ImportError as e:
        # Router module import failed
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "AI Tutoring service is initializing. Please try again in a moment.",
                    "retryable": True
                }
            }
        )
    except Exception as e:
        # Other errors
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error creating AI tutoring session: {str(e)}")
        print(f"Traceback: {error_trace}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": f"Failed to create session: {str(e)}",
                    "retryable": True
                }
            }
        )

# Add direct Wolfram chat endpoint to handle frontend calls
@app.post("/api/doubt/wolfram/chat")
async def wolfram_chat_direct(request: Request):
    """
    Direct route for Wolfram Alpha chat
    This ensures the endpoint works even if router import fails
    """
    try:
        from app.routers.doubt import wolfram_chat
        from fastapi import Query
        
        # Get query parameters
        query_params = request.query_params
        query = query_params.get("query", "")
        include_steps = query_params.get("include_steps", "true").lower() == "true"
        
        print(f"🔍 Direct Wolfram request: query='{query}', include_steps={include_steps}")
        
        if not query:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "Query parameter is required",
                    "query": query
                }
            )
        
        # Call the actual handler
        return await wolfram_chat(query=query, include_steps=include_steps)
        
    except ImportError as e:
        print(f"❌ Failed to import wolfram_chat: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "error": "Wolfram Alpha service is initializing. Please try again in a moment.",
                "query": query if 'query' in locals() else ""
            }
        )
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Error in direct Wolfram chat: {str(e)}")
        print(f"Traceback: {error_trace}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to process Wolfram query: {str(e)}",
                "query": query if 'query' in locals() else ""
            }
        )

# Add direct AI tutoring message endpoint
@app.post("/api/ai-tutoring/sessions/message")
async def ai_tutoring_send_message_direct(request: Request):
    """
    Direct route for AI tutoring send message
    This ensures the endpoint works even if router import fails
    """
    try:
        from app.routers.ai_tutoring import send_message
        from app.models.ai_features import SendMessageRequest
        
        # Parse request body
        body = await request.json()
        print(f"💬 AI tutoring message request: {body}")
        
        message_request = SendMessageRequest(**body)
        return await send_message(message_request)
        
    except ImportError as e:
        print(f"❌ Failed to import send_message: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "error": "AI Tutoring service is initializing. Please try again in a moment."
            }
        )
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ Error in AI tutoring send message: {str(e)}")
        print(f"Traceback: {error_trace}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Failed to send message: {str(e)}"
            }
        )

# Include essential routers immediately (only health for fast startup)
if 'health' in _router_imports:
    app.include_router(_router_imports['health'].router, prefix="/api", tags=["health"])
    print("✓ Health router included")

# Function to load deferred routers
def load_deferred_routers():
    """Load non-essential routers after startup"""
    router_configs = [
        ('rag', '/api', ['rag']),
        ('doubt', '/api', ['doubt']),
        ('homework', '/api', ['homework']),
        ('microplan', '/api', ['microplan']),
        ('exam', '/api', ['exam']),
        ('quiz', '/api', ['quiz']),
        ('videos', '/api/videos', ['videos']),
        ('hots', '/api/hots', ['hots']),
        ('admin', '/api', ['admin']),
        ('progress', '/api', ['progress']),
        ('analytics', '/api', ['analytics']),
        ('translation', '/api', ['translation']),
        ('ai_tutoring', '/api', ['ai-tutoring']),
        ('teacher_tools', '/api', ['teacher-tools']),
        ('teacher', '/api', ['teacher']),
        ('wellbeing', '/api', ['wellbeing']),
        ('messages', '/api', ['messages']),
        ('notification', '/api', ['notifications']),
        ('memory_intelligence', '/api', ['memory-intelligence'])
    ]
    
    loaded_count = 0
    for router_name, prefix, tags in router_configs:
        try:
            if router_name not in _router_imports:
                module = __import__(f"app.routers.{router_name}", fromlist=[router_name])
                _router_imports[router_name] = module
                app.include_router(module.router, prefix=prefix, tags=tags)
                loaded_count += 1
                print(f"✓ Loaded deferred router: {router_name}")
        except Exception as e:
            _router_errors.append(f"{router_name}: {str(e)}")
            print(f"⚠ Warning: Failed to load deferred router {router_name}: {e}")
    
    print(f"✓ Loaded {loaded_count} deferred routers")
    return loaded_count

# Log initial router status
print(f"✓ {len(_router_imports)} essential routers loaded, {len(_deferred_routers)} deferred")

# Placeholder routers for future implementation
# app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
# app.include_router(packs.router, prefix="/api/packs", tags=["packs"])


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    port = os.getenv("PORT", str(settings.app_port))
    print(f"🚀 Starting Class 12 Learning Platform API in {settings.app_env} mode")
    print(f"🌐 Listening on port: {port}")
    print(f"🔒 CORS enabled for origins: {settings.cors_origins_list}")
    
    # Load deferred routers in background (don't block startup)
    import asyncio
    asyncio.create_task(asyncio.to_thread(load_deferred_routers))
    print("✓ Deferred router loading started in background")


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
