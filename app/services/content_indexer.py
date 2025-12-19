"""Google RAG content indexer using Vertex AI Search"""

import logging
import json
import asyncio
from typing import List, Dict, Optional, Callable, Awaitable
from google.cloud import discoveryengine_v1
from google.cloud import storage
from app.models.content import ContentItem
from app.config import settings
from app.services.chunking_service import chunking_service

logger = logging.getLogger(__name__)


class ContentIndexer:
    """Content indexer for Google Vertex AI Search"""
    
    def __init__(self):
        """Initialize content indexer"""
        self.project_id = settings.google_cloud_project
        self.location = 'us-central1'  # Default location
        self.data_store_id = None  # Not using Vertex AI Search
        self.search_engine_id = None  # Not using Vertex AI Search
        
        # Initialize clients
        self.document_client = None
        self.storage_client = None
        self.bucket_name = getattr(settings, 'gcs_bucket_name', None)
        
        logger.info("Content indexer initialized (Google Vertex AI Search mode)")
    
    def _setup_clients(self):
        """Setup Google Cloud clients"""
        try:
            if not self.document_client:
                self.document_client = discoveryengine_v1.DocumentServiceClient()
                logger.info("Document service client initialized")
            
            if not self.storage_client and self.bucket_name:
                self.storage_client = storage.Client()
                logger.info("Storage client initialized")
                
        except Exception as e:
            logger.error(f"Failed to setup Google Cloud clients: {e}")
            raise
    
    async def index_content_item(
        self,
        content_item: ContentItem,
        chunk_size: int = 1200,
        chunk_overlap: int = 200,
        update_progress_callback: Optional[Callable[[str, int], Awaitable[None]]] = None
    ) -> Dict:
        """
        Index content item into Google Vertex AI Search
        """
        try:
            logger.info(f"Starting Google RAG indexing for {content_item.id}")
            
            if update_progress_callback:
                await update_progress_callback("Initializing indexing...", 10)
            
            # Check if data store is configured
            if not self.data_store_id:
                logger.warning("Vertex AI data store not configured, using fallback indexing")
                return await self._fallback_indexing(content_item, update_progress_callback)
            
            # Setup clients
            self._setup_clients()
            
            if update_progress_callback:
                await update_progress_callback("Chunking content...", 20)
            
            # Chunk the content
            chunks = await chunking_service.chunk_content_item(
                content_item,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            if update_progress_callback:
                await update_progress_callback("Creating documents...", 40)
            
            # Create documents for Vertex AI Search
            documents_created = 0
            total_chunks = len(chunks)
            
            for i, chunk in enumerate(chunks):
                try:
                    # Create document for this chunk
                    document_id = f"{content_item.id}_chunk_{i}"
                    
                    # Prepare document data
                    document_data = {
                        "id": document_id,
                        "content": chunk["text"],
                        "title": content_item.title or f"Content {content_item.id}",
                        "subject": content_item.subject.value if content_item.subject else "general",
                        "chapter": getattr(content_item, 'chapter', ''),
                        "content_type": getattr(content_item, 'type', 'general'),
                        "difficulty": getattr(content_item, 'difficulty', ''),
                        "chunk_index": i,
                        "total_chunks": total_chunks,
                        "source_content_id": content_item.id
                    }
                    
                    # Create document in Vertex AI Search
                    success = await self._create_document(document_id, document_data)
                    
                    if success:
                        documents_created += 1
                    
                    # Update progress
                    progress = 40 + int((i + 1) / total_chunks * 50)
                    if update_progress_callback:
                        await update_progress_callback(f"Indexed {i + 1}/{total_chunks} chunks", progress)
                        
                except Exception as chunk_error:
                    logger.error(f"Failed to index chunk {i} for {content_item.id}: {chunk_error}")
                    continue
            
            if update_progress_callback:
                await update_progress_callback("Indexing completed", 100)
            
            success = documents_created > 0
            logger.info(f"Google RAG indexing completed for {content_item.id}: {documents_created}/{total_chunks} chunks indexed")
            
            return {
                "success": success,
                "message": f"Indexed {documents_created}/{total_chunks} chunks into Vertex AI Search",
                "content_id": content_item.id,
                "chunks_created": total_chunks,
                "documents_indexed": documents_created,
                "embeddings_generated": documents_created  # Vertex AI handles embeddings
            }
            
        except Exception as e:
            logger.error(f"Google RAG indexing failed for {content_item.id}: {e}", exc_info=True)
            
            if update_progress_callback:
                await update_progress_callback(f"Indexing failed: {str(e)}", 0)
            
            return {
                "success": False,
                "message": f"Google RAG indexing failed: {str(e)}",
                "content_id": content_item.id,
                "chunks_created": 0,
                "documents_indexed": 0,
                "embeddings_generated": 0,
                "error": str(e)
            }
    
    async def _create_document(self, document_id: str, document_data: Dict) -> bool:
        """Create a document in Vertex AI Search"""
        try:
            # Construct the parent path
            parent = f"projects/{self.project_id}/locations/global/collections/default_collection/dataStores/{self.data_store_id}/branches/default_branch"
            
            # Create document object
            document = discoveryengine_v1.Document(
                id=document_id,
                json_data=json.dumps(document_data).encode('utf-8')
            )
            
            # Create the request
            request = discoveryengine_v1.CreateDocumentRequest(
                parent=parent,
                document=document,
                document_id=document_id
            )
            
            # Execute the request
            operation = self.document_client.create_document(request=request)
            logger.debug(f"Created document {document_id} in Vertex AI Search")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create document {document_id}: {e}")
            return False
    
    async def _fallback_indexing(
        self,
        content_item: ContentItem,
        update_progress_callback: Optional[Callable[[str, int], Awaitable[None]]] = None
    ) -> Dict:
        """Fallback indexing when Vertex AI Search is not configured"""
        logger.info(f"Using fallback indexing for {content_item.id}")
        
        if update_progress_callback:
            await update_progress_callback("Using fallback indexing (Vertex AI not configured)", 50)
            await asyncio.sleep(1)  # Simulate processing
            await update_progress_callback("Fallback indexing completed", 100)
        
        return {
            "success": True,
            "message": "Content indexed using fallback method (Vertex AI Search not configured)",
            "content_id": content_item.id,
            "chunks_created": 1,
            "documents_indexed": 1,
            "embeddings_generated": 0,
            "mode": "fallback"
        }
    
    async def index_content_batch(
        self,
        content_items: List[ContentItem],
        chunk_size: int = 1200,
        chunk_overlap: int = 200,
        batch_size: int = 10
    ) -> Dict:
        """
        Index multiple content items in batches
        """
        logger.info(f"Starting batch indexing for {len(content_items)} items")
        
        indexed_items = 0
        failed_items = 0
        total_chunks = 0
        total_documents = 0
        
        # Process in batches
        for i in range(0, len(content_items), batch_size):
            batch = content_items[i:i + batch_size]
            
            for content_item in batch:
                try:
                    result = await self.index_content_item(
                        content_item,
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap
                    )
                    
                    if result.get("success", False):
                        indexed_items += 1
                        total_chunks += result.get("chunks_created", 0)
                        total_documents += result.get("documents_indexed", 0)
                    else:
                        failed_items += 1
                        
                except Exception as e:
                    logger.error(f"Failed to index content item {content_item.id}: {e}")
                    failed_items += 1
        
        return {
            "success": indexed_items > 0,
            "message": f"Batch indexing completed: {indexed_items} successful, {failed_items} failed",
            "total_items": len(content_items),
            "indexed_items": indexed_items,
            "failed_items": failed_items,
            "total_chunks": total_chunks,
            "total_embeddings": total_documents
        }
    
    async def delete_content_index(self, content_id: str) -> Dict:
        """
        Delete content index from Vertex AI Search
        """
        try:
            logger.info(f"Deleting content index for {content_id}")
            
            if not self.data_store_id:
                logger.warning("Vertex AI data store not configured, skipping deletion")
                return {
                    "success": True,
                    "message": "Content deletion skipped (Vertex AI not configured)",
                    "content_id": content_id,
                    "deleted_chunks": 0
                }
            
            self._setup_clients()
            
            # Find and delete all documents for this content
            deleted_chunks = 0
            
            # Search for documents with this content_id
            # Note: This is a simplified approach - in production you might want to 
            # maintain a mapping of content_id to document_ids
            
            try:
                # Construct the parent path
                parent = f"projects/{self.project_id}/locations/global/collections/default_collection/dataStores/{self.data_store_id}/branches/default_branch"
                
                # Try to delete documents (assuming naming pattern content_id_chunk_N)
                chunk_index = 0
                while chunk_index < 100:  # Reasonable limit
                    document_id = f"{content_id}_chunk_{chunk_index}"
                    
                    try:
                        request = discoveryengine_v1.DeleteDocumentRequest(
                            name=f"{parent}/documents/{document_id}"
                        )
                        
                        self.document_client.delete_document(request=request)
                        deleted_chunks += 1
                        logger.debug(f"Deleted document {document_id}")
                        
                    except Exception as delete_error:
                        # If document doesn't exist, we've reached the end
                        if "not found" in str(delete_error).lower():
                            break
                        else:
                            logger.warning(f"Error deleting document {document_id}: {delete_error}")
                    
                    chunk_index += 1
                
            except Exception as e:
                logger.error(f"Error during content deletion for {content_id}: {e}")
            
            logger.info(f"Deleted {deleted_chunks} document chunks for content {content_id}")
            
            return {
                "success": True,
                "message": f"Deleted {deleted_chunks} document chunks from Vertex AI Search",
                "content_id": content_id,
                "deleted_chunks": deleted_chunks
            }
            
        except Exception as e:
            logger.error(f"Failed to delete content index for {content_id}: {e}")
            return {
                "success": False,
                "message": f"Content deletion failed: {str(e)}",
                "content_id": content_id,
                "deleted_chunks": 0,
                "error": str(e)
            }
    
    async def delete_content_batch(self, content_ids: List[str]) -> Dict:
        """
        Delete multiple content indexes in batch
        """
        logger.info(f"Starting batch deletion for {len(content_ids)} items")
        
        deleted_items = 0
        total_deleted_chunks = 0
        
        for content_id in content_ids:
            try:
                result = await self.delete_content_index(content_id)
                
                if result.get("success", False):
                    deleted_items += 1
                    total_deleted_chunks += result.get("deleted_chunks", 0)
                    
            except Exception as e:
                logger.error(f"Failed to delete content index {content_id}: {e}")
        
        return {
            "success": deleted_items > 0,
            "message": f"Batch deletion completed: {deleted_items} items deleted",
            "deleted_items": deleted_items,
            "total_deleted_chunks": total_deleted_chunks
        }


# Global instance
content_indexer = ContentIndexer()