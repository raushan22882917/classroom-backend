"""Content management endpoints"""

from fastapi import APIRouter, Query, HTTPException, UploadFile, File, BackgroundTasks, Request
from typing import Optional, List
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.models.admin import (
    ContentUploadRequest,
    ContentUploadResponse,
    ContentPreview
)
from app.models.base import Subject
from app.utils.exceptions import APIException

# Import content_service lazily to avoid startup issues
content_service = None

def get_content_service():
    global content_service
    if content_service is None:
        from app.services.content_service import content_service as cs
        content_service = cs
    return content_service

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/content/upload", response_model=ContentUploadResponse, status_code=201)
@limiter.limit("20/minute")
async def upload_content(
    request: Request,
    content_request: ContentUploadRequest,
    background_tasks: BackgroundTasks
):
    """
    Upload and tag content (NCERT/PYQ/HOTS)
    
    Request Body:
    - type: Content type ('ncert', 'pyq', 'hots')
    - subject: Subject
    - chapter: Chapter name (optional)
    - topic_id: Topic ID (optional)
    - difficulty: Difficulty level (optional)
    - title: Content title (optional)
    - content_text: Main content text
    - metadata: Additional metadata
    - PYQ-specific: year, marks, solution, topic_ids
    - HOTS-specific: question_type
    
    Returns:
    - ContentUploadResponse with content ID and indexing status
    
    Notes:
    - Automatically triggers embedding generation and indexing
    - Content is immediately available in RAG pipeline after indexing
    """
    try:
        cs = get_content_service()
        response = await cs.upload_content(
            content_request=content_request,
            trigger_indexing=True
        )
        return response
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/content/upload/file", response_model=ContentUploadResponse, status_code=201)
@limiter.limit("10/minute")
async def upload_content_file(
    request: Request,
    file: UploadFile = File(...),
    subject: Subject = Query(..., description="Subject"),
    chapter: Optional[str] = Query(None, description="Chapter name"),
    topic_id: Optional[str] = Query(None, description="Topic ID"),
    difficulty: Optional[str] = Query(None, description="Difficulty level"),
    class_grade: Optional[int] = Query(None, description="Class/Grade number (e.g., 8, 9, 10, 11, 12)")
):
    """
    Upload content from file (PDF or text)
    
    Form Data:
    - file: File to upload (PDF or text file)
    
    Query Parameters:
    - subject: Subject (required)
    - chapter: Chapter name (optional)
    - topic_id: Topic ID (optional)
    - difficulty: Difficulty level (optional)
    
    Returns:
    - ContentUploadResponse with content ID and indexing status
    
    Supported file types:
    - application/pdf
    - text/plain
    - text/markdown
    
    Notes:
    - Extracts text from PDF using PyPDF2
    - Automatically triggers embedding generation and indexing
    """
    try:
        # Read file content
        file_content = await file.read()
        
        # Determine file type if not provided
        file_type = file.content_type
        if not file_type or file_type == "application/octet-stream":
            # Try to infer from filename
            if file.filename:
                filename_lower = file.filename.lower()
                if filename_lower.endswith('.pdf'):
                    file_type = "application/pdf"
                elif filename_lower.endswith(('.txt', '.md')):
                    file_type = "text/plain"
                else:
                    file_type = "text/plain"  # Default to text
        
        # Upload file
        cs = get_content_service()
        response = await cs.upload_file(
            file_content=file_content,
            file_type=file_type,
            subject=subject,
            chapter=chapter,
            topic_id=topic_id,
            difficulty=difficulty,
            filename=file.filename,
            class_grade=class_grade,
            metadata={"original_filename": file.filename}
        )
        
        return response
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        import traceback
        import logging
        logger = logging.getLogger(__name__)
        error_trace = traceback.format_exc()
        logger.error(f"Error uploading file: {str(e)}\n{error_trace}")
        # Return a more user-friendly error message
        error_detail = str(e)
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {error_detail}")


@router.get("/content/list")
@limiter.limit("50/minute")
async def list_all_content(
    request: Request,
    subject: Optional[Subject] = Query(None, description="Filter by subject"),
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    processing_status: Optional[str] = Query(None, description="Filter by processing status"),
    limit: int = Query(100, description="Maximum number of results", ge=1, le=500),
    offset: int = Query(0, description="Pagination offset", ge=0)
):
    """
    List all content items with filters
    
    Query Parameters:
    - subject: Filter by subject
    - content_type: Filter by content type (ncert, pyq, hots)
    - processing_status: Filter by processing status (pending, processing, completed, failed)
    - limit: Maximum number of results
    - offset: Pagination offset
    
    Returns:
    - List of content items
    """
    try:
        cs = get_content_service()
        content_items = await cs.list_all_content(
            subject=subject,
            content_type=content_type,
            processing_status=processing_status,
            limit=limit,
            offset=offset
        )
        return content_items
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/content/reindex", status_code=202)
@limiter.limit("5/minute")
async def reindex_content(request: Request, background_tasks: BackgroundTasks):
    """
    Re-index all content in the RAG pipeline
    
    Returns:
    - 202 Accepted with reindexing results
    
    Notes:
    - This is a potentially long-running operation
    - Regenerates embeddings for all content items
    - Updates vector database with new embeddings
    - Use sparingly as it consumes API quota
    """
    try:
        # Execute reindexing in background
        def reindex_task():
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            cs = get_content_service()
            result = loop.run_until_complete(cs.reindex_all_content())
            loop.close()
            return result
        
        background_tasks.add_task(reindex_task)
        
        return {
            "success": True,
            "message": "Content reindexing started in background",
            "status": "processing"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/content/index-status")
@limiter.limit("20/minute")
async def get_index_status(request: Request):
    """
    Get indexing status and statistics
    
    Returns:
    - Total content count
    - Indexed content count
    - Vector database statistics
    """
    try:
        # Vector DB stats now handled by Google RAG services
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Vector DB stats request - now handled by Google RAG services")
        vector_stats = {
            "total_vector_count": 0,
            "storage_type": "google_rag_services",
            "note": "Vector storage handled by Google RAG services"
        }
        
        # Get content counts from database
        cs = get_content_service()
        content_response = cs.supabase.table("content")\
            .select("id, indexed_at", count="exact")\
            .execute()
        
        total_content = content_response.count if hasattr(content_response, 'count') else len(content_response.data)
        
        indexed_content = sum(1 for row in content_response.data if row.get("indexed_at"))
        not_indexed = total_content - indexed_content
        
        return {
            "success": True,
            "database": {
                "total_content": total_content,
                "indexed_content": indexed_content,
                "not_indexed": not_indexed,
                "indexed_percentage": round((indexed_content / total_content * 100) if total_content > 0 else 0, 2)
            },
            "vector_database": vector_stats,
            "status": "ready" if vector_stats.get("total_vector_count", 0) > 0 else "empty"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/content/status/{content_id}")
@limiter.limit("100/minute")
async def get_content_status(
    request: Request,
    content_id: str
):
    """
    Get content processing status and indexing progress
    
    Path Parameters:
    - content_id: Content item ID (UUID)
    
    Returns:
    - Content status with processing_status and indexing_progress
    """
    try:
        from supabase import create_client
        from app.config import settings
        
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        content_response = supabase.table("content")\
            .select("id, processing_status, metadata, embedding_id, processing_started_at, processing_completed_at")\
            .eq("id", content_id)\
            .execute()
        
        if not content_response.data:
            raise HTTPException(status_code=404, detail="Content not found")
        
        content = content_response.data[0]
        metadata = content.get("metadata", {}) or {}
        indexing_progress = metadata.get("indexing_progress", 0)
        
        # Calculate progress percentage based on status
        if content.get("processing_status") == "completed":
            progress = 100
        elif content.get("processing_status") == "failed":
            progress = 0
        elif content.get("processing_status") == "processing":
            progress = indexing_progress if indexing_progress > 0 else 50  # Default to 50% if processing but no progress tracked
        else:  # pending
            progress = 0
        
        return {
            "content_id": content_id,
            "processing_status": content.get("processing_status", "pending"),
            "indexing_progress": progress,
            "embedding_id": content.get("embedding_id"),
            "processing_started_at": content.get("processing_started_at"),
            "processing_completed_at": content.get("processing_completed_at")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get content status: {str(e)}")


@router.get("/content/preview/{content_id}", response_model=ContentPreview)
@limiter.limit("50/minute")
async def preview_content(request: Request, content_id: str):
    """
    Preview how content appears in RAG pipeline
    
    Path Parameters:
    - content_id: Content item ID (UUID)
    
    Returns:
    - ContentPreview showing:
      - Original content text (truncated to 500 chars)
      - Embedding ID
      - Content chunks (first 5 chunks, truncated to 200 chars each)
      - Metadata
    
    Notes:
    - Useful for verifying content chunking before indexing
    - Shows how content will be split for RAG retrieval
    """
    try:
        cs = get_content_service()
        preview = await cs.preview_content(content_id)
        return preview
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/content/open/{content_id}")
@limiter.limit("100/minute")
async def open_content(
    request: Request,
    content_id: str,
    user_id: str = Query(..., description="User ID accessing the content"),
    trigger_processing: bool = Query(True, description="Trigger RAG processing if not already done")
):
    """
    Open content (especially PDFs) and trigger real-time RAG processing
    
    Path Parameters:
    - content_id: Content item ID (UUID)
    
    Query Parameters:
    - user_id: User ID accessing the content (required)
    - trigger_processing: Whether to trigger RAG processing if not already done (default: True)
    
    Returns:
    - Content details with file URL, processing status, and RAG insights
    
    Notes:
    - When a PDF is opened, this endpoint triggers real-time processing:
      1. Extracts text from PDF
      2. Chunks the content
      3. Generates embeddings
      4. Indexes into vector database
      5. Provides RAG-powered insights
    - Processing happens in the background for better performance
    - Students and teachers can access content immediately while processing completes
    """
    try:
        cs = get_content_service()
        result = await cs.open_content_with_rag(
            content_id=content_id,
            user_id=user_id,
            trigger_processing=trigger_processing
        )
        return result
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/content/folders")
@limiter.limit("50/minute")
async def get_content_folders(
    request: Request,
    class_grade: Optional[int] = Query(None, description="Filter by class grade"),
    subject: Optional[Subject] = Query(None, description="Filter by subject"),
    parent_folder_id: Optional[str] = Query(None, description="Filter by parent folder ID")
):
    """
    Get content folders for hierarchical organization
    
    Query Parameters:
    - class_grade: Filter by class grade (1-12)
    - subject: Filter by subject
    - parent_folder_id: Filter by parent folder ID (for nested folders)
    
    Returns:
    - List of content folders
    """
    try:
        cs = get_content_service()
        folders = await cs.get_content_folders(
            class_grade=class_grade,
            subject=subject,
            parent_folder_id=parent_folder_id
        )
        return folders
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/content/by-folder")
@limiter.limit("50/minute")
async def get_content_by_folder(
    request: Request,
    folder_path: Optional[str] = Query(None, description="Filter by folder path"),
    class_grade: Optional[int] = Query(None, description="Filter by class grade"),
    subject: Optional[Subject] = Query(None, description="Filter by subject"),
    limit: int = Query(50, description="Maximum number of results", ge=1, le=200),
    offset: int = Query(0, description="Pagination offset", ge=0)
):
    """
    Get content items organized by folder hierarchy
    
    Query Parameters:
    - folder_path: Filter by folder path (e.g., "class_12/physics/chapter_1")
    - class_grade: Filter by class grade
    - subject: Filter by subject
    - limit: Maximum number of results
    - offset: Pagination offset
    
    Returns:
    - List of content items with folder information
    """
    try:
        cs = get_content_service()
        content_items = await cs.get_content_by_folder(
            folder_path=folder_path,
            class_grade=class_grade,
            subject=subject,
            limit=limit,
            offset=offset
        )
        return content_items
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/content/{content_id}")
@limiter.limit("30/minute")
async def update_content(
    request: Request,
    content_id: str,
    title: Optional[str] = None,
    chapter: Optional[str] = None,
    difficulty: Optional[str] = None,
    class_grade: Optional[int] = None,
    chapter_number: Optional[int] = None,
    metadata: Optional[dict] = None
):
    """
    Update content metadata
    
    Path Parameters:
    - content_id: Content item ID
    
    Request Body (JSON):
    - title: New title (optional)
    - chapter: New chapter name (optional)
    - difficulty: New difficulty level (optional)
    - class_grade: Class/Grade level 1-12 (optional)
    - chapter_number: Chapter number (optional)
    - metadata: Additional metadata (optional)
    
    Returns:
    - Updated content item
    """
    try:
        cs = get_content_service()
        updated_content = await cs.update_content(
            content_id=content_id,
            title=title,
            chapter=chapter,
            difficulty=difficulty,
            class_grade=class_grade,
            chapter_number=chapter_number,
            metadata=metadata
        )
        return updated_content
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/content/{content_id}")
@limiter.limit("20/minute")
async def delete_content(
    request: Request,
    content_id: str
):
    """
    Delete content item
    
    Path Parameters:
    - content_id: Content item ID
    
    Returns:
    - Success message
    """
    try:
        cs = get_content_service()
        result = await cs.delete_content(content_id)
        return result
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))