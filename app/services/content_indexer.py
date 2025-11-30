"""Content indexing service for RAG pipeline"""

import logging
from typing import List, Dict, Optional, Callable, Awaitable
from app.models.content import ContentItem
from app.services.embedding_service import embedding_service
from app.services.vector_db_service import vector_db_service
from app.services.chunking_service import chunking_service
from app.utils.exceptions import RAGPipelineError

logger = logging.getLogger(__name__)


class ContentIndexer:
    """Service for indexing content into the RAG pipeline"""
    
    def __init__(self):
        """Initialize content indexer"""
        self.embedding_service = embedding_service
        self.vector_db_service = vector_db_service
        self.chunking_service = chunking_service
    
    async def index_content_item(
        self,
        content_item: ContentItem,
        chunk_size: int = 1200,
        chunk_overlap: int = 200,
        update_progress_callback: Optional[Callable[[str, int], Awaitable[None]]] = None
    ) -> Dict:
        """
        Index a single content item into the RAG pipeline
        
        Args:
            content_item: Content item to index
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            update_progress_callback: Optional callback to update progress (content_id, progress_percent)
            
        Returns:
            Dictionary with indexing results
        """
        try:
            logger.info(f"Starting indexing for content item: {content_item.id}")
            
            # Step 1: Chunk the content (10% progress)
            if update_progress_callback:
                await update_progress_callback(str(content_item.id), 10)
            logger.debug(f"Chunking content: {content_item.id}")
            
            chunks = self.chunking_service.chunk_content_item(
                content_item,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            if not chunks:
                logger.warning(f"No chunks created from content: {content_item.id}")
                return {
                    "content_id": content_item.id,
                    "chunks_created": 0,
                    "embeddings_generated": 0,
                    "success": False,
                    "message": "No chunks created from content"
                }
            
            logger.info(f"Created {len(chunks)} chunks for content: {content_item.id}")
            
            # Step 2: Generate embeddings for all chunks (30-70% progress)
            chunk_texts = [chunk["text"] for chunk in chunks]
            total_chunks = len(chunk_texts)
            
            embeddings = []
            # The embedding service now handles token-aware batching automatically
            # It will respect the 20,000 token limit per request
            # We just pass all chunks and let it handle batching intelligently
            logger.info(f"Generating embeddings for {total_chunks} chunks (token-aware batching will be applied)")
            
            # Generate all embeddings - the service will handle token-aware batching
            all_embeddings = await self.embedding_service.generate_embeddings_batch(
                chunk_texts,
                batch_size=None  # Let the service determine optimal batching based on token limits
            )
            embeddings.extend(all_embeddings)
            
            # Update progress to 70% after all embeddings are generated
            if update_progress_callback:
                await update_progress_callback(str(content_item.id), 70)
            
            logger.info(f"Generated {len(embeddings)} embeddings for content: {content_item.id}")
            
            logger.info(f"Generated {len(embeddings)} embeddings for content: {content_item.id}")
            
            # Step 3: Prepare vectors (80% progress)
            if update_progress_callback:
                await update_progress_callback(str(content_item.id), 80)
            
            vectors = []
            for chunk, embedding in zip(chunks, embeddings):
                vectors.append((
                    chunk["id"],  # vector ID
                    embedding,    # embedding vector
                    chunk["metadata"]  # metadata
                ))
            
            # Step 4: Upsert to vector database (90% progress)
            if update_progress_callback:
                await update_progress_callback(str(content_item.id), 90)
            
            logger.debug(f"Upserting {len(vectors)} vectors to database")
            await self.vector_db_service.upsert_vectors(vectors)
            
            # Complete (100% progress)
            if update_progress_callback:
                await update_progress_callback(str(content_item.id), 100)
            
            logger.info(f"Successfully indexed content: {content_item.id} ({len(chunks)} chunks)")
            
            return {
                "content_id": content_item.id,
                "chunks_created": len(chunks),
                "embeddings_generated": len(embeddings),
                "success": True,
                "message": f"Successfully indexed {len(chunks)} chunks"
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to index content item {content_item.id}: {error_msg}", exc_info=True)
            
            # Return detailed error information instead of raising
            return {
                "content_id": content_item.id,
                "chunks_created": 0,
                "embeddings_generated": 0,
                "success": False,
                "message": f"Indexing failed: {error_msg}",
                "error": error_msg
            }
    
    async def index_content_batch(
        self,
        content_items: List[ContentItem],
        chunk_size: int = 1200,
        chunk_overlap: int = 200
    ) -> Dict:
        """
        Index multiple content items in batch
        
        Args:
            content_items: List of content items to index
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            
        Returns:
            Dictionary with batch indexing results
        """
        try:
            results = []
            total_chunks = 0
            total_embeddings = 0
            failed_items = []
            
            for content_item in content_items:
                try:
                    result = await self.index_content_item(
                        content_item,
                        chunk_size=chunk_size,
                        chunk_overlap=chunk_overlap
                    )
                    results.append(result)
                    total_chunks += result["chunks_created"]
                    total_embeddings += result["embeddings_generated"]
                except Exception as e:
                    failed_items.append({
                        "content_id": content_item.id,
                        "error": str(e)
                    })
            
            return {
                "total_items": len(content_items),
                "successful_items": len(results),
                "failed_items": len(failed_items),
                "total_chunks": total_chunks,
                "total_embeddings": total_embeddings,
                "failures": failed_items,
                "success": len(failed_items) == 0
            }
            
        except Exception as e:
            raise RAGPipelineError(f"Failed to index content batch: {str(e)}")
    
    async def reindex_content(
        self,
        content_id: str,
        content_item: ContentItem,
        chunk_size: int = 1200,
        chunk_overlap: int = 200
    ) -> Dict:
        """
        Reindex existing content (delete old chunks and create new ones)
        
        Args:
            content_id: ID of content to reindex
            content_item: Updated content item
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            
        Returns:
            Dictionary with reindexing results
        """
        try:
            # Step 1: Delete existing chunks for this content
            await self.vector_db_service.delete_by_filter(
                filters={"content_id": content_id}
            )
            
            # Step 2: Index the new content
            result = await self.index_content_item(
                content_item,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            result["reindexed"] = True
            return result
            
        except Exception as e:
            raise RAGPipelineError(f"Failed to reindex content: {str(e)}")
    
    async def delete_content_index(self, content_id: str) -> Dict:
        """
        Delete all indexed chunks for a content item
        
        Args:
            content_id: ID of content to delete from index
            
        Returns:
            Dictionary with deletion results
        """
        try:
            result = await self.vector_db_service.delete_by_filter(
                filters={"content_id": content_id}
            )
            
            return {
                "content_id": content_id,
                "success": True,
                "message": "Content deleted from index"
            }
            
        except Exception as e:
            raise RAGPipelineError(f"Failed to delete content index: {str(e)}")


# Global instance
content_indexer = ContentIndexer()
