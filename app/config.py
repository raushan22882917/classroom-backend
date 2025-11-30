"""Application configuration management"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Supabase Configuration
    supabase_url: str
    supabase_key: str
    supabase_service_key: str
    
    # Google Cloud Configuration
    google_cloud_project: str
    google_application_credentials: str = ""  # Optional - if not set, will use Application Default Credentials (ADC) on Cloud Run
    
    # Gemini API
    gemini_api_key: str
    
    # Wolfram Alpha API
    wolfram_app_id: str
    
    # YouTube Data API
    youtube_api_key: str
    
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
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
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


# Global settings instance with error handling
# Note: Settings validation errors will be caught and displayed by startup script
try:
    settings = Settings()
except Exception as e:
    import os
    # On Cloud Run, provide detailed error but don't exit immediately
    # This allows health checks to still work and better error messages
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
    for var in required_vars:
        if not os.getenv(var):
            error_msg += f"  ❌ {var}\n"
    
    error_msg += f"""
{'=' * 80}
Please set these in Cloud Run service configuration:
  gcloud run services update classroom-backend \\
    --set-env-vars "SUPABASE_URL=...,SUPABASE_KEY=..." \\
    --region us-central1
{'=' * 80}
"""
    print(error_msg)
    # Re-raise so we can see the exact validation error
    raise
