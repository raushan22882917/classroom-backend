"""Admin panel endpoints for content management and student oversight"""

from fastapi import APIRouter, Query, HTTPException, UploadFile, File, BackgroundTasks, Request, Depends
from typing import Optional, List
from slowapi import Limiter
from slowapi.util import get_remote_address
from io import StringIO
import pandas as pd

from app.models.admin import (
    AdminDashboardMetrics,
    StudentOverview,
    StudentDetailedProfile,
    ContentUploadRequest,
    ContentUploadResponse,
    ContentPreview,
    SchoolCreateRequest,
    SchoolUpdateRequest,
    UserCreateRequest
)
from app.models.base import Subject
from app.services.admin_service import admin_service
from app.services.content_service import content_service
from app.services.school_service import school_service
from app.utils.exceptions import APIException

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.get("/admin/dashboard", response_model=AdminDashboardMetrics)
@limiter.limit("50/minute")
async def get_admin_dashboard(request: Request):
    """
    Get admin dashboard with aggregate metrics
    
    Returns comprehensive metrics including:
    - Active students count (active in last 7 days)
    - Total students count
    - Average mastery score across all students and topics
    - Completion rate (topics with mastery >= 80%)
    - Flagged students list (mastery < 50%)
    - Total content items
    - Total test sessions
    
    Returns:
    - AdminDashboardMetrics with all aggregate data
    """
    try:
        metrics = await admin_service.get_dashboard_metrics()
        return metrics
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/students", response_model=List[StudentOverview])
@limiter.limit("50/minute")
async def get_students(
    request: Request,
    subject: Optional[Subject] = Query(None, description="Filter by subject"),
    min_mastery: Optional[float] = Query(None, description="Minimum mastery score", ge=0, le=100),
    max_mastery: Optional[float] = Query(None, description="Maximum mastery score", ge=0, le=100),
    active_days: Optional[int] = Query(None, description="Filter students active in last N days", ge=1),
    limit: int = Query(50, description="Maximum number of results", ge=1, le=200),
    offset: int = Query(0, description="Pagination offset", ge=0)
):
    """
    Get list of students with optional filters
    
    Query Parameters:
    - subject: Filter by specific subject (mathematics, physics, chemistry, biology)
    - min_mastery: Minimum average mastery score (0-100)
    - max_mastery: Maximum average mastery score (0-100)
    - active_days: Show only students active in last N days
    - limit: Maximum number of students to return (default: 50, max: 200)
    - offset: Pagination offset (default: 0)
    
    Returns:
    - List of StudentOverview objects with aggregated metrics
    
    Notes:
    - Students are sorted by average mastery score (ascending) to show struggling students first
    - Flagged students (mastery < 50%) are marked with is_flagged=True
    """
    try:
        students = await admin_service.get_students(
            subject=subject,
            min_mastery=min_mastery,
            max_mastery=max_mastery,
            active_days=active_days,
            limit=limit,
            offset=offset
        )
        
        return students
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/students/{student_id}", response_model=StudentDetailedProfile)
@limiter.limit("50/minute")
async def get_student_profile(request: Request, student_id: str):
    """
    Get detailed profile for a specific student
    
    Path Parameters:
    - student_id: Student user ID (UUID)
    
    Returns:
    - StudentDetailedProfile with comprehensive data including:
      - Progress by subject with completion rates
      - List of completed topics
      - Total time spent learning
      - Test session history (last 20 sessions)
      - Average test score
      - Activity metrics (last active, streak days)
      - Achievements earned
    
    Raises:
    - 404: Student not found
    """
    try:
        profile = await admin_service.get_student_profile(student_id)
        return profile
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
        response = await content_service.upload_content(
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
        response = await content_service.upload_file(
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
            result = loop.run_until_complete(content_service.reindex_all_content())
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
        from app.services.vector_db_service import vector_db_service
        
        # Get vector DB stats
        await vector_db_service.initialize()
        vector_stats = await vector_db_service.get_index_stats()
        
        # Get content counts from database
        content_response = content_service.supabase.table("content")\
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
        from app.services.content_service import content_service
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
        preview = await content_service.preview_content(content_id)
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
        result = await content_service.open_content_with_rag(
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
        folders = await content_service.get_content_folders(
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
        content_items = await content_service.get_content_by_folder(
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
        content_items = await content_service.list_all_content(
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
        updated_content = await content_service.update_content(
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
        result = await content_service.delete_content(content_id)
        return result
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/export")
@limiter.limit("10/minute")
async def export_students(
    request: Request,
    subject: Optional[Subject] = Query(None, description="Filter by subject"),
    min_mastery: Optional[float] = Query(None, description="Minimum mastery score", ge=0, le=100),
    max_mastery: Optional[float] = Query(None, description="Maximum mastery score", ge=0, le=100),
    active_days: Optional[int] = Query(None, description="Filter students active in last N days", ge=1)
):
    """
    Export student data as CSV
    
    Query Parameters:
    - subject: Filter by specific subject
    - min_mastery: Minimum average mastery score (0-100)
    - max_mastery: Maximum average mastery score (0-100)
    - active_days: Show only students active in last N days
    
    Returns:
    - CSV file with student data including:
      - User ID, name, email
      - Subjects (comma-separated)
      - Average mastery score
      - Topics completed
      - Total time spent (minutes)
      - Test sessions count
      - Average test score
      - Last active date
      - Streak days
      - Flagged status
      - Created date
    
    Notes:
    - Exports up to 1000 students
    - CSV is returned as downloadable file
    - Use filters to narrow down export scope
    """
    try:
        # Get student data for export
        export_data = await admin_service.export_students_data(
            subject=subject,
            min_mastery=min_mastery,
            max_mastery=max_mastery,
            active_days=active_days
        )
        
        if not export_data:
            raise HTTPException(
                status_code=404,
                detail="No students found matching the criteria"
            )
        
        # Convert to pandas DataFrame
        df = pd.DataFrame(export_data)
        
        # Generate CSV
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_content = csv_buffer.getvalue()
        
        # Return CSV as response
        from fastapi.responses import Response
        
        filename = f"students_export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except HTTPException:
        raise
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# School Management Endpoints

@router.post("/admin/schools", status_code=201)
@limiter.limit("30/minute")
async def create_school(
    request: Request,
    school_data: SchoolCreateRequest
):
    """Create a new school"""
    try:
        school = await school_service.create_school(
            name=school_data.name,
            address=school_data.address,
            city=school_data.city,
            state=school_data.state,
            pincode=school_data.pincode,
            phone=school_data.phone,
            email=school_data.email,
            principal_name=school_data.principal_name
        )
        return school
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/schools")
@limiter.limit("50/minute")
async def get_schools(
    request: Request,
    city: Optional[str] = None,
    state: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0
):
    """Get list of schools"""
    try:
        schools = await school_service.get_schools(
            city=city,
            state=state,
            is_active=is_active,
            limit=limit,
            offset=offset
        )
        return schools
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/schools/{school_id}")
@limiter.limit("50/minute")
async def get_school(request: Request, school_id: str):
    """Get a specific school"""
    try:
        school = await school_service.get_school(school_id)
        return school
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/admin/schools/{school_id}")
@limiter.limit("30/minute")
async def update_school(
    request: Request,
    school_id: str,
    school_data: SchoolUpdateRequest
):
    """Update a school"""
    try:
        school = await school_service.update_school(
            school_id=school_id,
            name=school_data.name,
            address=school_data.address,
            city=school_data.city,
            state=school_data.state,
            pincode=school_data.pincode,
            phone=school_data.phone,
            email=school_data.email,
            principal_name=school_data.principal_name,
            is_active=school_data.is_active
        )
        return school
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/admin/schools/{school_id}")
@limiter.limit("20/minute")
async def delete_school(request: Request, school_id: str):
    """Delete a school"""
    try:
        result = await school_service.delete_school(school_id)
        return result
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/schools/{school_id}/teachers/{teacher_id}")
@limiter.limit("30/minute")
async def assign_teacher_to_school(request: Request, school_id: str, teacher_id: str):
    """Assign a teacher to a school"""
    try:
        result = await school_service.assign_teacher_to_school(school_id, teacher_id)
        return result
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/admin/schools/{school_id}/teachers/{teacher_id}")
@limiter.limit("30/minute")
async def remove_teacher_from_school(request: Request, school_id: str, teacher_id: str):
    """Remove a teacher from a school"""
    try:
        result = await school_service.remove_teacher_from_school(school_id, teacher_id)
        return result
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/schools/{school_id}/teachers")
@limiter.limit("50/minute")
async def get_school_teachers(request: Request, school_id: str):
    """Get all teachers assigned to a school"""
    try:
        teachers = await school_service.get_school_teachers(school_id)
        return teachers
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/schools/{school_id}/students")
@limiter.limit("50/minute")
async def get_school_students(
    request: Request,
    school_id: str,
    limit: int = 100,
    offset: int = 0
):
    """Get all students in a school"""
    try:
        students = await school_service.get_school_students(school_id, limit=limit, offset=offset)
        return students
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/schools/{school_id}/students/{student_id}")
@limiter.limit("30/minute")
async def assign_student_to_school(request: Request, school_id: str, student_id: str):
    """Assign a student to a school"""
    try:
        result = await school_service.assign_student_to_school(school_id, student_id)
        return result
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/teachers")
@limiter.limit("50/minute")
async def get_all_teachers(request: Request):
    """Get all teachers in the system"""
    try:
        teachers = await school_service.get_all_teachers()
        return teachers
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/admin/users")
@limiter.limit("50/minute")
async def get_all_users(request: Request):
    """Get all users in the system with their roles"""
    try:
        users = await school_service.get_all_users()
        return users
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/admin/users", status_code=201)
@limiter.limit("30/minute")
async def create_user(
    request: Request,
    user_data: UserCreateRequest
):
    """Create a new user (student or teacher)"""
    try:
        if user_data.role not in ["student", "teacher"]:
            raise HTTPException(status_code=400, detail="Role must be 'student' or 'teacher'")
        
        if user_data.role == "student" and not user_data.class_grade:
            raise HTTPException(status_code=400, detail="class_grade is required for students")
        
        user = await school_service.create_user(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            role=user_data.role,
            class_grade=user_data.class_grade,
            phone=user_data.phone,
            subject_specializations=user_data.subject_specializations
        )
        return user
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
