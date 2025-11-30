"""Custom exception handlers"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Union


class APIException(Exception):
    """Base API exception"""
    def __init__(
        self,
        code: str,
        message: str,
        details: Union[dict, None] = None,
        retryable: bool = False,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        self.retryable = retryable
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(APIException):
    """Authentication failed"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            code="AUTHENTICATION_ERROR",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class AuthorizationError(APIException):
    """Insufficient permissions"""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            code="AUTHORIZATION_ERROR",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )


class ValidationError(APIException):
    """Validation error"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class NotFoundError(APIException):
    """Resource not found"""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            code="NOT_FOUND",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND
        )


class ExternalAPIError(APIException):
    """External API error"""
    def __init__(self, service: str, message: str):
        super().__init__(
            code="EXTERNAL_API_ERROR",
            message=f"{service} API error: {message}",
            retryable=True,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


class RateLimitError(APIException):
    """Rate limit exceeded"""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            code="RATE_LIMIT_ERROR",
            message=message,
            retryable=True,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )


async def api_exception_handler(request: Request, exc: APIException):
    """Handle custom API exceptions"""
    from app.config import settings
    
    response = JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "retryable": exc.retryable
            }
        }
    )
    # Ensure CORS headers are included
    origin = request.headers.get("origin")
    if origin and origin in settings.cors_origins_list:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid input provided",
                "details": exc.errors(),
                "retryable": False
            }
        }
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    import logging
    from app.config import settings
    
    logger = logging.getLogger(__name__)
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "details": {"error": str(exc)} if settings.app_env == "development" else {},
                "retryable": True
            }
        }
    )
    # Ensure CORS headers are included
    origin = request.headers.get("origin")
    if origin and origin in settings.cors_origins_list:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


class EmbeddingGenerationError(APIException):
    """Embedding generation error"""
    def __init__(self, message: str = "Failed to generate embeddings"):
        super().__init__(
            code="EMBEDDING_GENERATION_ERROR",
            message=message,
            retryable=True,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class VectorDBError(APIException):
    """Vector database error"""
    def __init__(self, message: str = "Vector database operation failed"):
        super().__init__(
            code="VECTOR_DB_ERROR",
            message=message,
            retryable=True,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class ChunkingError(APIException):
    """Content chunking error"""
    def __init__(self, message: str = "Failed to chunk content"):
        super().__init__(
            code="CHUNKING_ERROR",
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class RAGPipelineError(APIException):
    """RAG pipeline error"""
    def __init__(self, message: str = "RAG pipeline operation failed"):
        super().__init__(
            code="RAG_PIPELINE_ERROR",
            message=message,
            retryable=True,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
