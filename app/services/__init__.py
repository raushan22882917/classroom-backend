"""Services module"""

# Don't import services at module level - import them on-demand
# This prevents import-time initialization failures that block router imports
# Services will be imported when actually needed by routers

__all__ = [
    "chunking_service",
    "content_indexer",
    "rag_service",
    "google_rag_service",
    "hots_service"
]

# Lazy import functions - import services only when needed
# Note: embedding_service and vector_db_service removed - now using Google RAG service

def get_chunking_service():
    from app.services.chunking_service import chunking_service
    return chunking_service

def get_content_indexer():
    from app.services.content_indexer import content_indexer
    return content_indexer

def get_rag_service():
    from app.services.rag_service import rag_service
    return rag_service

def get_hots_service():
    from app.services.hots_service import hots_service
    return hots_service
