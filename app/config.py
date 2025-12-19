"""Application configuration management"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Supabase Configuration
    supabase_url: str = ""  # Allow empty for graceful degradation
    supabase_key: str = ""  # Allow empty for graceful degradation
    supabase_service_key: str = ""  # Allow empty for graceful degradation
    
    # Google Cloud Configuration
    google_cloud_project: str = ""  # Allow empty for graceful degradation
    google_application_credentials: str = ""  # Optional - if not set, will use Application Default Credentials (ADC) on Cloud Run
    
    # Gemini API
    gemini_api_key: str = ""  # Allow empty for graceful degradation
    
    # Optional Services (can be empty)
    wolfram_app_id: str = ""
    youtube_api_key: str = ""
    
    # Gemini Model Configuration - Production-ready
    gemini_model: str = "gemini-2.5-flash"  # Only available production model
    
    # RAG Configuration
    rag_chunk_size: int = 1000
    rag_chunk_overlap: int = 200
    rag_max_context_chunks: int = 6
    

    
    # Application Configuration
    app_env: str = "production"  # Default to production for Cloud Run
    app_host: str = "0.0.0.0"
    app_port: int = 8080  # Cloud Run default port
    cors_origins: str = ""  # Not used - see cors_origins_list property
    
    # Rate Limiting
    rate_limit_per_minute: int = 100
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Hardcoded CORS origins for production"""
        return [
            "http://localhost:5173",  # Vite dev server
            "http://localhost:3000",  # React dev server
            "http://localhost:8080",  # Local frontend
            "https://eduverse-dashboard-iota.vercel.app",  # Production frontend
            "http://127.0.0.1:5173",  # Alternative localhost
            "http://127.0.0.1:3000",  # Alternative localhost
            "http://127.0.0.1:8080"   # Alternative localhost
        ]
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env file


# Global settings instance with error handling
# Make settings loading more resilient - allow app to start even if some vars are missing
try:
    settings = Settings()
except Exception as e:
    import os
    import sys
    
    # Print detailed error message
    error_msg = f"""
{'=' * 80}
ERROR: Failed to load required environment variables!
{'=' * 80}
Error: {str(e)}

Required environment variables that are missing:
"""
    # Check which specific variables are missing
    required_vars = [
        "SUPABASE_URL", "SUPABASE_KEY", "SUPABASE_SERVICE_KEY",
        "GEMINI_API_KEY"
    ]
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            error_msg += f"  ❌ {var}\n"
            missing_vars.append(var)
    
    error_msg += f"""
{'=' * 80}
The application may start but features requiring these variables will fail.
Please set these in Cloud Run service configuration.
{'=' * 80}
"""
    print(error_msg, file=sys.stderr)
    
    # Create a minimal settings object with defaults so app can at least start
    # This allows the startup probe to succeed
    from typing import Optional
    from pydantic import BaseModel
    
    class MinimalSettings:
        """Minimal settings when full Settings() fails"""
        supabase_url: str = ""
        supabase_key: str = ""
        supabase_service_key: str = ""
        google_cloud_project: str = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        google_application_credentials: str = ""
        gemini_api_key: str = ""
        wolfram_app_id: str = ""
        youtube_api_key: str = ""
        gemini_model: str = "gemini-2.5-flash"
        rag_chunk_size: int = 1000
        rag_chunk_overlap: int = 200
        rag_max_context_chunks: int = 6
        app_env: str = "production"
        app_host: str = "0.0.0.0"
        app_port: int = 8080
        cors_origins: str = ""
        rate_limit_per_minute: int = 100
        
        @property
        def cors_origins_list(self):
            """Hardcoded CORS origins for production"""
            return [
                "http://localhost:5173",
                "http://localhost:3000", 
                "http://localhost:8080",
                "https://eduverse-dashboard-iota.vercel.app",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8080"
            ]
    
    settings = MinimalSettings()
    print("⚠ Using minimal settings - application will start but some features may not work", file=sys.stderr)
