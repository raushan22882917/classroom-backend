"""Content management service for admin operations"""

from typing import Optional, List, Dict
from datetime import datetime
import uuid
import re
import logging
from supabase import create_client, Client
from io import BytesIO

# Try to import PyPDF2, fall back to text extraction if not available
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    logger.warning("PyPDF2 not available, PDF processing will be limited")

from app.config import settings

logger = logging.getLogger(__name__)
from app.models.content import (
    ContentItem,
    ContentItemCreate,
    PYQ,
    PYQCreate,
    HOTSQuestion,
    HOTSQuestionCreate,
    ContentType,
    DifficultyLevel
)
from app.models.admin import ContentUploadRequest, ContentUploadResponse, ContentPreview
from app.models.base import Subject
from app.services.content_indexer import content_indexer
from app.utils.exceptions import APIException


class ContentService:
    """Service for content management operations"""
    
    def __init__(self):
        """Initialize content service with Supabase client"""
        self.supabase: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
    
    async def upload_content(
        self,
        content_request: ContentUploadRequest,
        trigger_indexing: bool = True
    ) -> ContentUploadResponse:
        """
        Upload and tag content (NCERT/PYQ/HOTS)
        
        Args:
            content_request: Content upload request with metadata
            trigger_indexing: Whether to trigger embedding generation
        
        Returns:
            ContentUploadResponse with content ID and indexing status
        """
        try:
            content_id = str(uuid.uuid4())
            embedding_id = None
            indexed = False
            
            # Handle different content types
            if content_request.type == "pyq":
                # Insert into pyqs table
                pyq_data = {
                    "id": content_id,
                    "subject": content_request.subject.value,
                    "year": content_request.year,
                    "question": content_request.content_text,
                    "solution": content_request.solution or "",
                    "marks": content_request.marks or 1,
                    "topic_ids": content_request.topic_ids,
                    "difficulty": content_request.difficulty,
                    "metadata": content_request.metadata,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                
                response = self.supabase.table("pyqs").insert(pyq_data).execute()
                
                if not response.data:
                    raise APIException(
                        code="DATABASE_ERROR",
                        message="Failed to insert PYQ into database",
                        status_code=500
                    )
                
                # Create content item for indexing
                if trigger_indexing:
                    try:
                        content_item = ContentItem(
                            id=content_id,
                            type=ContentType.PYQ,
                            subject=content_request.subject,
                            chapter=content_request.chapter,
                            topic_id=content_request.topic_id,
                            difficulty=DifficultyLevel(content_request.difficulty) if content_request.difficulty else None,
                            title=content_request.title,
                            content_text=f"Question: {content_request.content_text}\nSolution: {content_request.solution}",
                            metadata=content_request.metadata,
                            embedding_id=None,
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )
                        
                        # Index content (don't fail if indexing fails)
                        try:
                            logger.info(f"Starting indexing for PYQ content: {content_id}")
                            index_result = await content_indexer.index_content_item(content_item)
                            indexed = index_result.get("success", False)
                            embedding_id = content_id  # Use content_id as embedding_id
                            logger.info(f"Indexing completed for PYQ content: {content_id}, success: {indexed}")
                            
                            if not indexed:
                                error_msg = index_result.get("message", "Unknown indexing error")
                                logger.warning(f"PYQ indexing failed for {content_id}: {error_msg}")
                        except Exception as index_error:
                            # Log indexing error but don't fail the upload
                            logger.error(f"PYQ content indexing failed for {content_id}: {str(index_error)}", exc_info=True)
                            indexed = False
                            embedding_id = None
                    except Exception as item_error:
                        logger.error(f"Failed to create PYQ content item for indexing: {str(item_error)}", exc_info=True)
                        indexed = False
                        embedding_id = None
            
            elif content_request.type == "hots":
                # Insert into hots_questions table
                hots_data = {
                    "id": content_id,
                    "subject": content_request.subject.value,
                    "topic_id": content_request.topic_id,
                    "question": content_request.content_text,
                    "solution": content_request.solution or "",
                    "difficulty": content_request.difficulty or "hard",
                    "question_type": content_request.question_type or "case_based",
                    "metadata": content_request.metadata,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                
                response = self.supabase.table("hots_questions").insert(hots_data).execute()
                
                if not response.data:
                    raise APIException(
                        code="DATABASE_ERROR",
                        message="Failed to insert HOTS question into database",
                        status_code=500
                    )
                
                # Create content item for indexing
                if trigger_indexing:
                    try:
                        content_item = ContentItem(
                            id=content_id,
                            type=ContentType.HOTS,
                            subject=content_request.subject,
                            chapter=content_request.chapter,
                            topic_id=content_request.topic_id,
                            difficulty=DifficultyLevel(content_request.difficulty) if content_request.difficulty else DifficultyLevel.HARD,
                            title=content_request.title,
                            content_text=f"Question: {content_request.content_text}\nSolution: {content_request.solution}",
                            metadata=content_request.metadata,
                            embedding_id=None,
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )
                        
                        # Index content (don't fail if indexing fails)
                        try:
                            logger.info(f"Starting indexing for HOTS content: {content_id}")
                            index_result = await content_indexer.index_content_item(content_item)
                            indexed = index_result.get("success", False)
                            embedding_id = content_id
                            logger.info(f"Indexing completed for HOTS content: {content_id}, success: {indexed}")
                            
                            if not indexed:
                                error_msg = index_result.get("message", "Unknown indexing error")
                                logger.warning(f"HOTS indexing failed for {content_id}: {error_msg}")
                        except Exception as index_error:
                            # Log indexing error but don't fail the upload
                            logger.error(f"HOTS content indexing failed for {content_id}: {str(index_error)}", exc_info=True)
                            indexed = False
                            embedding_id = None
                    except Exception as item_error:
                        logger.error(f"Failed to create HOTS content item for indexing: {str(item_error)}", exc_info=True)
                        indexed = False
                        embedding_id = None
            
            else:  # ncert or other content types
                # Validate topic_id if provided (must be UUID format)
                topic_id = None
                if content_request.topic_id:
                    # Check if it's a valid UUID format
                    try:
                        uuid.UUID(content_request.topic_id)
                        topic_id = content_request.topic_id
                    except (ValueError, AttributeError):
                        # Not a valid UUID, try to look up by name or skip
                        logger.warning(f"Invalid topic_id format: {content_request.topic_id}. Skipping topic_id.")
                        # Optionally, you could look up topic by name here
                        # For now, we'll just skip it
                        topic_id = None
                
                # Insert into content table
                content_data = {
                    "id": content_id,
                    "type": content_request.type,
                    "subject": content_request.subject.value,
                    "chapter": content_request.chapter,
                    "topic_id": topic_id,
                    "difficulty": content_request.difficulty,
                    "title": content_request.title,
                    "content_text": content_request.content_text,
                    "metadata": content_request.metadata,
                    "embedding_id": None,
                    "processing_status": "pending",  # Will be updated after indexing
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                
                response = self.supabase.table("content").insert(content_data).execute()
                
                if not response.data:
                    raise APIException(
                        code="DATABASE_ERROR",
                        message="Failed to insert content into database",
                        status_code=500
                    )
                
                # Create content item for indexing
                if trigger_indexing:
                    try:
                        content_item = ContentItem(
                            id=content_id,
                            type=ContentType(content_request.type),
                            subject=content_request.subject,
                            chapter=content_request.chapter,
                            topic_id=content_request.topic_id,
                            difficulty=DifficultyLevel(content_request.difficulty) if content_request.difficulty else None,
                            title=content_request.title,
                            content_text=content_request.content_text,
                            metadata=content_request.metadata,
                            embedding_id=None,
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )
                        
                        # Index content (don't fail if indexing fails)
                        try:
                            # Progress callback to update database
                            async def update_progress(cid: str, progress: int):
                                try:
                                    # Store progress in metadata
                                    current_content = self.supabase.table("content").select("metadata").eq("id", cid).execute()
                                    current_metadata = current_content.data[0].get("metadata", {}) if current_content.data else {}
                                    current_metadata["indexing_progress"] = progress
                                    
                                    # Update processing status based on progress
                                    if progress < 100:
                                        status = "processing"
                                    else:
                                        status = "completed"
                                    
                                    update_dict = {
                                        "metadata": current_metadata,
                                        "processing_status": status
                                    }
                                    
                                    # Set processing_started_at only on first progress update
                                    if progress == 10:
                                        update_dict["processing_started_at"] = datetime.now().isoformat()
                                    
                                    self.supabase.table("content").update(update_dict).eq("id", cid).execute()
                                    
                                    logger.info(f"Updated indexing progress for {cid}: {progress}% (status: {status})")
                                except Exception as e:
                                    logger.warning(f"Failed to update progress for {cid}: {str(e)}")
                            
                            logger.info(f"Starting indexing for content: {content_id}")
                            index_result = await content_indexer.index_content_item(
                                content_item,
                                update_progress_callback=update_progress
                            )
                            indexed = index_result.get("success", False)
                            embedding_id = content_id
                            logger.info(f"Indexing completed for content: {content_id}, success: {indexed}")
                            
                            # Update embedding_id and processing status in database
                            if indexed:
                                update_data = {
                                    "embedding_id": embedding_id,
                                    "processing_status": "completed",
                                    "processing_started_at": datetime.now().isoformat(),
                                    "processing_completed_at": datetime.now().isoformat(),
                                    "indexed_at": datetime.now().isoformat()
                                }
                                self.supabase.table("content")\
                                    .update(update_data)\
                                    .eq("id", content_id)\
                                    .execute()
                            else:
                                # Mark as failed if indexing didn't succeed
                                self.supabase.table("content")\
                                    .update({
                                        "processing_status": "failed",
                                        "processing_started_at": datetime.now().isoformat(),
                                        "processing_completed_at": datetime.now().isoformat()
                                    })\
                                    .eq("id", content_id)\
                                    .execute()
                        except Exception as index_error:
                            # Log indexing error but don't fail the upload
                            logger.error(f"Content indexing failed for {content_id}: {str(index_error)}", exc_info=True)
                            indexed = False
                            embedding_id = None
                            
                            # Update database status to failed
                            try:
                                self.supabase.table("content")\
                                    .update({
                                        "processing_status": "failed",
                                        "processing_started_at": datetime.now().isoformat(),
                                        "processing_completed_at": datetime.now().isoformat()
                                    })\
                                    .eq("id", content_id)\
                                    .execute()
                            except Exception as db_error:
                                logger.warning(f"Failed to update processing status for {content_id}: {str(db_error)}")
                    except Exception as item_error:
                        logger.error(f"Failed to create content item for indexing: {str(item_error)}", exc_info=True)
                        indexed = False
                        embedding_id = None
            
            # Create informative message based on indexing status
            if indexed:
                message = f"Content uploaded and indexed successfully."
            else:
                message = f"Content uploaded successfully, but indexing failed. Please check logs for details. You can try reindexing this content later."
            
            return ContentUploadResponse(
                id=content_id,
                type=content_request.type,
                subject=content_request.subject,
                embedding_id=embedding_id,
                indexed=indexed,
                message=message
            )
            
        except APIException:
            raise
        except Exception as e:
            raise APIException(
                code="UPLOAD_ERROR",
                message=f"Failed to upload content: {str(e)}",
                status_code=500
            )
    
    async def upload_file(
        self,
        file_content: bytes,
        file_type: str,
        subject: Subject,
        chapter: Optional[str] = None,
        topic_id: Optional[str] = None,
        difficulty: Optional[str] = None,
        metadata: Optional[Dict] = None,
        filename: Optional[str] = None,
        class_grade: Optional[int] = None
    ) -> ContentUploadResponse:
        """
        Upload content from file (PDF or text)
        
        Args:
            file_content: File content as bytes
            file_type: File MIME type
            subject: Subject
            chapter: Chapter name
            topic_id: Topic ID (must be UUID format)
            difficulty: Difficulty level
            metadata: Additional metadata
        
        Returns:
            ContentUploadResponse
        """
        try:
            # Validate topic_id format if provided (must be UUID)
            validated_topic_id = None
            if topic_id:
                try:
                    # Try to parse as UUID
                    uuid.UUID(topic_id)
                    validated_topic_id = topic_id
                except (ValueError, AttributeError, TypeError):
                    # Not a valid UUID format - log warning and skip
                    logger.warning(f"Invalid topic_id format (not a UUID): {topic_id}. Skipping topic_id.")
                    # Set to None to avoid database error
                    validated_topic_id = None
            
            # Extract text from file
            logger.info(f"Extracting text from file: {filename}, type: {file_type}")
            if file_type == "application/pdf":
                text = self._extract_text_from_pdf(file_content)
                logger.info(f"Extracted {len(text)} characters from PDF: {filename}")
            elif file_type.startswith("text/"):
                text = file_content.decode("utf-8")
                logger.info(f"Read {len(text)} characters from text file: {filename}")
            else:
                raise APIException(
                    code="UNSUPPORTED_FILE_TYPE",
                    message=f"Unsupported file type: {file_type}",
                    status_code=400
                )
            
            # Upload file to Supabase Storage
            file_url = None
            storage_path = None
            if filename:
                try:
                    # Determine class name (use class_grade if provided, otherwise default to "general")
                    class_name = f"class_{class_grade}" if class_grade else "general"
                    subject_name = subject.value.lower()
                    
                    # Sanitize filename
                    safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
                    
                    # Create storage path: class_name/subject_name/filename
                    storage_path = f"{class_name}/{subject_name}/{safe_filename}"
                    
                    # Upload to Supabase Storage bucket "content"
                    storage_response = self.supabase.storage.from_("content").upload(
                        path=storage_path,
                        file=file_content,
                        file_options={"content-type": file_type, "upsert": "true"}
                    )
                    
                    if storage_response:
                        # Get public URL
                        url_response = self.supabase.storage.from_("content").get_public_url(storage_path)
                        if isinstance(url_response, str):
                            file_url = url_response
                        elif isinstance(url_response, dict):
                            file_url = url_response.get("publicUrl")
                        else:
                            # Try to get URL from response data
                            file_url = getattr(url_response, 'publicUrl', None) if hasattr(url_response, 'publicUrl') else None
                        
                        logger.info(f"File uploaded to storage: {storage_path}, URL: {file_url}")
                except Exception as e:
                    # Log error but don't fail the upload
                    logger.warning(f"Failed to upload file to storage: {str(e)}. Continuing with text extraction only.")
            
            # Prepare metadata with file URL
            content_metadata = metadata or {}
            if file_url:
                content_metadata["pdf_url"] = file_url
                content_metadata["file_url"] = file_url
                content_metadata["storage_path"] = storage_path
                content_metadata["original_filename"] = filename
            
            # Create upload request
            upload_request = ContentUploadRequest(
                type="ncert",
                subject=subject,
                chapter=chapter,
                topic_id=validated_topic_id,
                difficulty=difficulty,
                content_text=text,
                metadata=content_metadata
            )
            
            # Upload content with file metadata
            logger.info(f"Uploading content from file: {filename}, subject: {subject.value}")
            response = await self.upload_content(upload_request)
            logger.info(f"Content uploaded successfully: {response.id}, indexed: {response.indexed}")
            
            # Update content record with file information
            if response.id:
                # Get current metadata to preserve indexing_progress if it exists
                current_content = self.supabase.table("content").select("metadata, processing_status").eq("id", response.id).execute()
                current_metadata = current_content.data[0].get("metadata", {}) if current_content.data else {}
                current_status = current_content.data[0].get("processing_status", "pending") if current_content.data else "pending"
                
                update_data = {
                    "file_url": file_url,
                    "file_type": "pdf" if file_type == "application/pdf" else "text",
                    "file_size_bytes": len(file_content),
                    "class_grade": class_grade,
                    "folder_path": storage_path.rsplit('/', 1)[0] if storage_path else None,
                    "updated_at": datetime.now().isoformat(),
                    "metadata": current_metadata  # Preserve existing metadata including indexing_progress
                }
                
                # Only update processing status if it's not already being processed
                # This preserves the progress tracking from the indexing callback
                if current_status not in ["processing", "completed"]:
                    if file_type == "application/pdf":
                        if response.indexed:
                            # If indexing succeeded, mark as completed
                            update_data["processing_status"] = "completed"
                            update_data["processing_started_at"] = datetime.now().isoformat()
                            update_data["processing_completed_at"] = datetime.now().isoformat()
                        else:
                            # If indexing failed, mark as failed
                            update_data["processing_status"] = "failed"
                            update_data["processing_started_at"] = datetime.now().isoformat()
                            update_data["processing_completed_at"] = datetime.now().isoformat()
                    else:
                        # For non-PDF files, mark as completed immediately
                        update_data["processing_status"] = "completed"
                        update_data["processing_started_at"] = datetime.now().isoformat()
                        update_data["processing_completed_at"] = datetime.now().isoformat()
                else:
                    # Preserve existing status if already processing
                    logger.debug(f"Preserving existing processing status: {current_status} for content: {response.id}")
                
                # Ensure folder exists
                if storage_path and class_grade:
                    folder_path = storage_path.rsplit('/', 1)[0]
                    folder_name = folder_path.split('/')[-1] if '/' in folder_path else folder_path
                    try:
                        folder_id = await self._ensure_folder_exists(
                            folder_path=folder_path,
                            name=folder_name,
                            subject=subject,
                            class_grade=class_grade,
                            chapter=chapter
                        )
                        if folder_id:
                            update_data["parent_folder_id"] = folder_id
                    except Exception as e:
                        logger.warning(f"Failed to create folder: {str(e)}")
                
                self.supabase.table("content")\
                    .update(update_data)\
                    .eq("id", response.id)\
                    .execute()
            
            return response
            
        except APIException:
            raise
        except Exception as e:
            raise APIException(
                code="FILE_UPLOAD_ERROR",
                message=f"Failed to upload file: {str(e)}",
                status_code=500
            )
    
    def _extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """
        Extract text from PDF file
        
        Args:
            pdf_content: PDF file content as bytes
        
        Returns:
            Extracted text
        """
        try:
            if not PDF_AVAILABLE:
                raise APIException(
                    code="PDF_LIBRARY_UNAVAILABLE",
                    message="PDF processing library not available. Please upload text files instead.",
                    status_code=400
                )
            
            pdf_file = BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_parts = []
            for page in pdf_reader.pages:
                text_parts.append(page.extract_text())
            
            return "\n\n".join(text_parts)
            
        except APIException:
            raise
        except Exception as e:
            raise APIException(
                code="PDF_EXTRACTION_ERROR",
                message=f"Failed to extract text from PDF: {str(e)}",
                status_code=500
            )
    
    async def reindex_all_content(self, filter_indexed: bool = False) -> Dict:
        """
        Re-index all content in the database
        
        Args:
            filter_indexed: If True, only index content that hasn't been indexed yet
        
        Returns:
            Dictionary with reindexing results
        """
        try:
            # Get all content from content table
            query = self.supabase.table("content").select("*")
            
            # Filter out already indexed content if requested
            if filter_indexed:
                query = query.is_("indexed_at", "null")
            
            content_response = query.execute()
            
            if not content_response.data:
                return {
                    "success": True,
                    "total_items": 0,
                    "successful_items": 0,
                    "failed_items": 0,
                    "total_chunks": 0,
                    "total_embeddings": 0,
                    "message": "No content found to index"
                }
            
            content_items = []
            skipped_items = []
            
            for row in content_response.data:
                # Skip content with no text or empty text
                content_text = row.get("content_text", "").strip()
                if not content_text:
                    skipped_items.append({
                        "id": row["id"],
                        "reason": "Empty content_text"
                    })
                    continue
                
                # Build metadata with all database fields
                metadata = row.get("metadata", {}) or {}
                metadata.update({
                    "class_grade": row.get("class_grade"),
                    "chapter_number": row.get("chapter_number"),
                    "folder_path": row.get("folder_path"),
                    "file_url": row.get("file_url"),
                    "file_type": row.get("file_type"),
                    "processing_status": row.get("processing_status")
                })
                
                content_items.append(ContentItem(
                    id=row["id"],
                    type=ContentType(row["type"]),
                    subject=Subject(row["subject"]),
                    chapter=row.get("chapter"),
                    topic_id=row.get("topic_id"),
                    difficulty=DifficultyLevel(row["difficulty"]) if row.get("difficulty") else None,
                    title=row.get("title"),
                    content_text=content_text,
                    metadata=metadata,
                    embedding_id=row.get("embedding_id"),
                    created_at=datetime.fromisoformat(row["created_at"].replace("Z", "+00:00") if "Z" in row["created_at"] else row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"].replace("Z", "+00:00") if "Z" in row["updated_at"] else row["updated_at"])
                ))
            
            if not content_items:
                return {
                    "success": True,
                    "total_items": len(content_response.data),
                    "successful_items": 0,
                    "failed_items": 0,
                    "skipped_items": len(skipped_items),
                    "total_chunks": 0,
                    "total_embeddings": 0,
                    "message": f"No valid content to index. Skipped {len(skipped_items)} items.",
                    "skipped": skipped_items
                }
            
            # Index all content
            result = await content_indexer.index_content_batch(content_items)
            
            # Update indexed_at timestamp for successfully indexed items
            # We'll track which items were successfully indexed by comparing with failed_items
            if result.get("successful_items", 0) > 0:
                failed_ids = {f.get("content_id") for f in result.get("failures", []) if f.get("content_id")}
                successful_ids = [
                    item.id for item in content_items 
                    if item.id not in failed_ids
                ]
                
                if successful_ids:
                    # Update indexed_at in batches
                    indexed_at = datetime.now().isoformat()
                    for content_id in successful_ids:
                        try:
                            self.supabase.table("content")\
                                .update({"indexed_at": indexed_at})\
                                .eq("id", content_id)\
                                .execute()
                        except Exception as e:
                            logger.warning(f"Failed to update indexed_at for {content_id}: {str(e)}")
            
            return {
                "success": result["success"],
                "total_items": len(content_response.data),
                "successful_items": result["successful_items"],
                "failed_items": result["failed_items"],
                "skipped_items": len(skipped_items),
                "total_chunks": result["total_chunks"],
                "total_embeddings": result["total_embeddings"],
                "message": f"Reindexed {result['successful_items']} out of {len(content_response.data)} content items. Skipped {len(skipped_items)} items.",
                "skipped": skipped_items[:10] if skipped_items else []  # Return first 10 skipped items
            }
            
        except Exception as e:
            raise APIException(
                code="REINDEX_ERROR",
                message=f"Failed to reindex content: {str(e)}",
                status_code=500
            )
    
    async def preview_content(self, content_id: str) -> ContentPreview:
        """
        Preview how content appears in RAG pipeline
        
        Args:
            content_id: Content item ID
        
        Returns:
            ContentPreview with chunks and similar content
        """
        try:
            # Get content from database
            content_response = self.supabase.table("content")\
                .select("*")\
                .eq("id", content_id)\
                .execute()
            
            if not content_response.data:
                raise APIException(
                    code="CONTENT_NOT_FOUND",
                    message=f"Content {content_id} not found",
                    status_code=404
                )
            
            row = content_response.data[0]
            
            # Create content item
            content_item = ContentItem(
                id=row["id"],
                type=ContentType(row["type"]),
                subject=Subject(row["subject"]),
                chapter=row.get("chapter"),
                topic_id=row.get("topic_id"),
                difficulty=DifficultyLevel(row["difficulty"]) if row.get("difficulty") else None,
                title=row.get("title"),
                content_text=row["content_text"],
                metadata=row.get("metadata", {}),
                embedding_id=row.get("embedding_id"),
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"])
            )
            
            # Get chunks (would need to query vector DB or recreate)
            from app.services.chunking_service import chunking_service
            chunks = chunking_service.chunk_content_item(content_item)
            
            chunk_previews = [
                {
                    "id": chunk["id"],
                    "text": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"],
                    "metadata": chunk["metadata"]
                }
                for chunk in chunks[:5]  # Show first 5 chunks
            ]
            
            return ContentPreview(
                content_id=content_id,
                content_text=content_item.content_text[:500] + "..." if len(content_item.content_text) > 500 else content_item.content_text,
                embedding_id=content_item.embedding_id,
                chunks=chunk_previews,
                similar_content=[],  # Would need to query vector DB
                metadata=content_item.metadata
            )
            
        except APIException:
            raise
        except Exception as e:
            raise APIException(
                code="PREVIEW_ERROR",
                message=f"Failed to preview content: {str(e)}",
                status_code=500
            )
    
    async def _ensure_folder_exists(
        self,
        folder_path: str,
        name: str,
        subject: Optional[Subject] = None,
        class_grade: Optional[int] = None,
        chapter: Optional[str] = None
    ) -> Optional[str]:
        """Ensure content folder exists, create if not"""
        try:
            # Check if folder exists
            folder_response = self.supabase.table("content_folders")\
                .select("id")\
                .eq("folder_path", folder_path)\
                .execute()
            
            if folder_response.data:
                return folder_response.data[0]["id"]
            
            # Create folder
            folder_data = {
                "name": name,
                "folder_path": folder_path,
                "subject": subject.value if subject else None,
                "class_grade": class_grade,
                "chapter": chapter
            }
            
            create_response = self.supabase.table("content_folders")\
                .insert(folder_data)\
                .execute()
            
            if create_response.data:
                return create_response.data[0]["id"]
            
            return None
        except Exception as e:
            logger.warning(f"Failed to ensure folder exists: {str(e)}")
            return None
    
    async def open_content_with_rag(
        self,
        content_id: str,
        user_id: str,
        trigger_processing: bool = True
    ) -> Dict:
        """
        Open content (especially PDFs) and trigger real-time RAG processing
        
        Args:
            content_id: Content item ID
            user_id: User ID accessing the content
            trigger_processing: Whether to trigger RAG processing if not already done
        
        Returns:
            Dictionary with content details and processing status
        """
        try:
            # Get content from database
            content_response = self.supabase.table("content")\
                .select("*")\
                .eq("id", content_id)\
                .execute()
            
            if not content_response.data:
                raise APIException(
                    code="CONTENT_NOT_FOUND",
                    message=f"Content {content_id} not found",
                    status_code=404
                )
            
            content_row = content_response.data[0]
            
            # Log access
            try:
                self.supabase.table("content_access_log").insert({
                    "content_id": content_id,
                    "user_id": user_id,
                    "access_type": "view",
                    "processing_triggered": trigger_processing
                }).execute()
            except Exception as e:
                logger.warning(f"Failed to log content access: {str(e)}")
            
            # Check if content needs processing
            processing_status = content_row.get("processing_status", "pending")
            file_url = content_row.get("file_url") or content_row.get("metadata", {}).get("file_url")
            file_type = content_row.get("file_type") or content_row.get("metadata", {}).get("file_type", "text")
            
            # If PDF and not processed, trigger processing
            if trigger_processing and file_type == "pdf" and processing_status != "completed":
                # Update status to processing
                self.supabase.table("content")\
                    .update({
                        "processing_status": "processing",
                        "processing_started_at": datetime.now().isoformat()
                    })\
                    .eq("id", content_id)\
                    .execute()
                
                # Trigger background processing
                try:
                    await self._process_pdf_content(content_id, content_row)
                except Exception as e:
                    logger.error(f"Failed to process PDF content {content_id}: {str(e)}")
                    # Update status to failed
                    self.supabase.table("content")\
                        .update({
                            "processing_status": "failed",
                            "processing_completed_at": datetime.now().isoformat()
                        })\
                        .eq("id", content_id)\
                        .execute()
                    processing_status = "failed"
            
            # Get RAG insights if content is indexed
            rag_insights = None
            if content_row.get("embedding_id") or processing_status == "completed":
                try:
                    # Get content summary using RAG
                    from app.services.rag_service import rag_service
                    from app.models.rag import RAGQuery
                    from app.models.base import Subject
                    
                    # Use the content text directly for summarization
                    content_text_preview = content_row.get("content_text", "")[:2000]  # First 2000 chars
                    
                    # Create a query to get content summary
                    summary_query = RAGQuery(
                        query=f"Summarize the key concepts and important points from this {content_row.get('subject', 'content')} content: {content_text_preview}",
                        subject=Subject(content_row["subject"]) if content_row.get("subject") else None,
                        top_k=5,
                        confidence_threshold=0.3  # Lower threshold for content-specific queries
                    )
                    
                    rag_response = await rag_service.query(summary_query)
                    
                    # Filter results to prioritize this content
                    content_sources = [
                        s for s in rag_response.sources 
                        if s.get("id") == content_id
                    ]
                    
                    if rag_response.confidence > 0.3:
                        rag_insights = {
                            "summary": rag_response.generated_text,
                            "confidence": rag_response.confidence,
                            "sources_count": len(content_sources) if content_sources else len(rag_response.sources),
                            "from_this_content": len(content_sources) > 0
                        }
                except Exception as e:
                    logger.warning(f"Failed to get RAG insights: {str(e)}")
            
            return {
                "content": content_row,
                "file_url": file_url,
                "file_type": file_type,
                "processing_status": processing_status,
                "rag_insights": rag_insights,
                "indexed": bool(content_row.get("embedding_id"))
            }
            
        except APIException:
            raise
        except Exception as e:
            raise APIException(
                code="CONTENT_ACCESS_ERROR",
                message=f"Failed to open content: {str(e)}",
                status_code=500
            )
    
    async def _process_pdf_content(self, content_id: str, content_row: Dict) -> None:
        """
        Process PDF content in real-time: extract text, chunk, and index
        
        Args:
            content_id: Content item ID
            content_row: Content row from database
        """
        try:
            file_url = content_row.get("file_url") or content_row.get("metadata", {}).get("file_url")
            
            if not file_url:
                raise ValueError("No file URL found for content")
            
            # Download file from storage
            storage_path = content_row.get("metadata", {}).get("storage_path")
            if not storage_path:
                # Try to extract from file_url
                if "storage" in file_url:
                    storage_path = file_url.split("/storage/v1/object/public/content/")[-1]
                else:
                    raise ValueError("Cannot determine storage path")
            
            # Download file
            file_response = self.supabase.storage.from_("content").download(storage_path)
            
            if not file_response:
                raise ValueError("Failed to download file from storage")
            
            # Extract text from PDF
            text = self._extract_text_from_pdf(file_response)
            
            if not text or len(text.strip()) < 50:
                raise ValueError("Extracted text is too short or empty")
            
            # Update content with extracted text
            self.supabase.table("content")\
                .update({
                    "content_text": text,
                    "updated_at": datetime.now().isoformat()
                })\
                .eq("id", content_id)\
                .execute()
            
            # Create content item for indexing
            content_item = ContentItem(
                id=content_id,
                type=ContentType(content_row["type"]),
                subject=Subject(content_row["subject"]),
                chapter=content_row.get("chapter"),
                topic_id=content_row.get("topic_id"),
                difficulty=DifficultyLevel(content_row["difficulty"]) if content_row.get("difficulty") else None,
                title=content_row.get("title") or content_row.get("metadata", {}).get("original_filename", "PDF Content"),
                content_text=text,
                metadata=content_row.get("metadata", {}),
                embedding_id=None,
                created_at=datetime.fromisoformat(content_row["created_at"]),
                updated_at=datetime.now()
            )
            
            # Index content
            index_result = await content_indexer.index_content_item(content_item)
            
            if index_result.get("success"):
                # Update content with indexing status
                self.supabase.table("content")\
                    .update({
                        "embedding_id": content_id,
                        "processing_status": "completed",
                        "processing_completed_at": datetime.now().isoformat(),
                        "indexed_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    })\
                    .eq("id", content_id)\
                    .execute()
            else:
                raise ValueError(f"Indexing failed: {index_result.get('message', 'Unknown error')}")
            
        except Exception as e:
            logger.error(f"Error processing PDF content {content_id}: {str(e)}")
            raise
    
    async def get_content_folders(
        self,
        class_grade: Optional[int] = None,
        subject: Optional[Subject] = None,
        parent_folder_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Get content folders for hierarchical organization
        
        Args:
            class_grade: Filter by class grade
            subject: Filter by subject
            parent_folder_id: Filter by parent folder ID
        
        Returns:
            List of folder dictionaries
        """
        try:
            query = self.supabase.table("content_folders").select("*")
            
            if class_grade:
                query = query.eq("class_grade", class_grade)
            if subject:
                query = query.eq("subject", subject.value)
            if parent_folder_id:
                query = query.eq("parent_folder_id", parent_folder_id)
            else:
                # If no parent_folder_id specified, get root folders (null parent)
                query = query.is_("parent_folder_id", "null")
            
            query = query.order("folder_path")
            
            response = query.execute()
            return response.data or []
            
        except Exception as e:
            logger.error(f"Failed to get content folders: {str(e)}")
            return []
    
    async def get_content_by_folder(
        self,
        folder_path: Optional[str] = None,
        class_grade: Optional[int] = None,
        subject: Optional[Subject] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict:
        """
        Get content items organized by folder hierarchy
        
        Args:
            folder_path: Filter by folder path
            class_grade: Filter by class grade
            subject: Filter by subject
            limit: Maximum number of results
            offset: Pagination offset
        
        Returns:
            Dictionary with folders and content items
        """
        try:
            # Get folders
            folders_query = self.supabase.table("content_folders").select("*")
            if class_grade:
                folders_query = folders_query.eq("class_grade", class_grade)
            if subject:
                folders_query = folders_query.eq("subject", subject.value)
            if folder_path:
                folders_query = folders_query.like("folder_path", f"{folder_path}%")
            
            folders_response = folders_query.order("folder_path").execute()
            folders = folders_response.data or []
            
            # Get content items
            content_query = self.supabase.table("content").select("*")
            if folder_path:
                content_query = content_query.like("folder_path", f"{folder_path}%")
            if class_grade:
                content_query = content_query.eq("class_grade", class_grade)
            if subject:
                content_query = content_query.eq("subject", subject.value)
            
            content_query = content_query.order("created_at", desc=True).limit(limit).offset(offset)
            content_response = content_query.execute()
            content_items = content_response.data or []
            
            return {
                "folders": folders,
                "content": content_items,
                "total": len(content_items),
                "limit": limit,
                "offset": offset
            }
            
        except Exception as e:
            logger.error(f"Failed to get content by folder: {str(e)}")
            return {
                "folders": [],
                "content": [],
                "total": 0,
                "limit": limit,
                "offset": offset
            }
    
    async def list_all_content(
        self,
        subject: Optional[Subject] = None,
        content_type: Optional[str] = None,
        processing_status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """
        List all content items with filters
        
        Args:
            subject: Filter by subject
            content_type: Filter by content type
            processing_status: Filter by processing status
            limit: Maximum number of results
            offset: Pagination offset
        
        Returns:
            List of content items
        """
        try:
            query = self.supabase.table("content").select("*")
            
            if subject:
                query = query.eq("subject", subject.value)
            if content_type:
                query = query.eq("type", content_type)
            if processing_status:
                query = query.eq("processing_status", processing_status)
            
            query = query.order("created_at", desc=True).limit(limit).offset(offset)
            
            response = query.execute()
            return response.data or []
            
        except Exception as e:
            logger.error(f"Failed to list content: {str(e)}")
            return []
    
    async def update_content(
        self,
        content_id: str,
        title: Optional[str] = None,
        chapter: Optional[str] = None,
        difficulty: Optional[str] = None,
        class_grade: Optional[int] = None,
        chapter_number: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Update content metadata
        
        Args:
            content_id: Content item ID
            title: New title
            chapter: New chapter name
            difficulty: New difficulty level
            class_grade: Class/Grade level (1-12)
            chapter_number: Chapter number
            metadata: Additional metadata
        
        Returns:
            Updated content item
        """
        try:
            update_data = {
                "updated_at": datetime.now().isoformat()
            }
            
            if title is not None:
                update_data["title"] = title
            if chapter is not None:
                update_data["chapter"] = chapter
            if difficulty is not None:
                update_data["difficulty"] = difficulty
            if class_grade is not None:
                update_data["class_grade"] = class_grade
            if chapter_number is not None:
                update_data["chapter_number"] = chapter_number
            if metadata is not None:
                # Merge with existing metadata
                current_response = self.supabase.table("content")\
                    .select("metadata")\
                    .eq("id", content_id)\
                    .single()\
                    .execute()
                
                current_metadata = current_response.data.get("metadata", {}) if current_response.data else {}
                # Remove title from metadata if title column is being updated
                # Title should be in the title column, not in metadata
                merged_metadata = {**current_metadata, **metadata}
                if title is not None and "title" in merged_metadata:
                    del merged_metadata["title"]
                update_data["metadata"] = merged_metadata
            
            response = self.supabase.table("content")\
                .update(update_data)\
                .eq("id", content_id)\
                .execute()
            
            if not response.data:
                raise APIException(
                    code="CONTENT_NOT_FOUND",
                    message=f"Content {content_id} not found",
                    status_code=404
                )
            
            return response.data[0]
            
        except APIException:
            raise
        except Exception as e:
            raise APIException(
                code="UPDATE_ERROR",
                message=f"Failed to update content: {str(e)}",
                status_code=500
            )
    
    async def delete_content(self, content_id: str) -> Dict:
        """
        Delete content item
        
        Args:
            content_id: Content item ID
        
        Returns:
            Success message
        """
        try:
            # Delete from vector database first
            try:
                await content_indexer.delete_content_index(content_id)
            except Exception as e:
                logger.warning(f"Failed to delete content index: {str(e)}")
            
            # Delete from database
            response = self.supabase.table("content")\
                .delete()\
                .eq("id", content_id)\
                .execute()
            
            if not response.data:
                raise APIException(
                    code="CONTENT_NOT_FOUND",
                    message=f"Content {content_id} not found",
                    status_code=404
                )
            
            return {
                "success": True,
                "message": f"Content {content_id} deleted successfully"
            }
            
        except APIException:
            raise
        except Exception as e:
            raise APIException(
                code="DELETE_ERROR",
                message=f"Failed to delete content: {str(e)}",
                status_code=500
            )


# Global content service instance
content_service = ContentService()
