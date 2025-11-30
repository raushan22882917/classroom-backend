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
    
    # Wolfram Alpha API
    wolfram_app_id: str = ""  # Allow empty for graceful degradation
    
    # YouTube Data API
    youtube_api_key: str = ""  # Allow empty for graceful degradation
    
    # Vertex AI Configuration
    vertex_ai_location: str = "us-central1"
    vertex_ai_embedding_model: str = "text-embedding-005"  # Faster and better than text-embedding-004
    
    # Gemini Model Configuration - Use faster models for better response times
    # Latest models from Gemini API (as of 2024)
    gemini_model_fast: str = "gemini-2.5-flash"  # Fast model for most tasks
    gemini_model_standard: str = "gemini-2.5-flash"  # Balanced speed/quality
    gemini_model_quality: str = "gemini-3.0-pro"  # Highest quality - most intelligent model
    
    # All available Gemini models (for fallback chains)
    gemini_models_fast_chain: str = "gemini-2.5-flash,gemini-2.5-flash-lite,gemini-2.0-flash,gemini-2.0-flash-lite,gemini-1.5-flash"
    gemini_models_quality_chain: str = "gemini-3.0-pro,gemini-2.5-pro,gemini-1.5-pro"
    
    # Embedding batch configuration for better throughput
    embedding_batch_size: int = 50  # Increased from 10 for faster processing
    
    # Vector Database Configuration (using Google Cloud - Pinecone is optional)
    pinecone_api_key: str = ""  # Optional - only needed if using Pinecone instead of Vertex AI
    pinecone_environment: str = ""  # Optional - only needed if using Pinecone
    pinecone_index_name: str = "class12-learning"  # Used as index name for both Pinecone and Vertex AI
    
    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    
    # Application Configuration
    app_env: str = "production"  # Default to production for Cloud Run
    app_host: str = "0.0.0.0"
    app_port: int = 8080  # Cloud Run default port
    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://localhost:8080"
    
    # Rate Limiting
    rate_limit_per_minute: int = 100
    
    # Wolfram Alpha API Timeout (in seconds)
    wolfram_timeout: int = 60  # Default 60 seconds for complex queries
    wolfram_connect_timeout: int = 10  # Connection timeout in seconds
    wolfram_read_timeout: int = 60  # Read timeout in seconds
    wolfram_max_retries: int = 2  # Maximum number of retries for failed requests
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
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
        "GOOGLE_CLOUD_PROJECT", "GEMINI_API_KEY",
        "WOLFRAM_APP_ID", "YOUTUBE_API_KEY"
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
        vertex_ai_location: str = "us-central1"
        vertex_ai_embedding_model: str = "text-embedding-005"
        gemini_model_fast: str = "gemini-2.5-flash"
        gemini_model_standard: str = "gemini-2.5-flash"
        gemini_model_quality: str = "gemini-3.0-pro"
        gemini_models_fast_chain: str = "gemini-2.5-flash"
        gemini_models_quality_chain: str = "gemini-3.0-pro"
        embedding_batch_size: int = 50
        pinecone_api_key: str = ""
        pinecone_environment: str = ""
        pinecone_index_name: str = "class12-learning"
        redis_host: str = "localhost"
        redis_port: int = 6379
        redis_password: str = ""
        app_env: str = "production"
        app_host: str = "0.0.0.0"
        app_port: int = 8080
        cors_origins: str = "*"
        rate_limit_per_minute: int = 100
        wolfram_timeout: int = 60
        wolfram_connect_timeout: int = 10
        wolfram_read_timeout: int = 60
        wolfram_max_retries: int = 2
        
        @property
        def cors_origins_list(self):
            return ["*"] if self.cors_origins == "*" else [o.strip() for o in self.cors_origins.split(",")]
    
    settings = MinimalSettings()
    print("⚠ Using minimal settings - application will start but some features may not work", file=sys.stderr)
