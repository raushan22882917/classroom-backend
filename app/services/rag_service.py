"""RAG (Retrieval-Augmented Generation) service using Google's RAG engine"""

from typing import List, Optional, Dict
import google.generativeai as genai
from app.config import settings
from app.models.rag import RAGQuery, RAGResponse, RAGContext
from app.services.google_rag_service import google_rag_service
from app.utils.exceptions import RAGPipelineError
import logging

logger = logging.getLogger(__name__)


class RAGService:
    """Service for RAG pipeline operations using Google's RAG engine"""
    
    def __init__(self):
        """Initialize RAG service"""
        self.google_rag_service = google_rag_service
        self._initialized = False
    
    async def initialize(self):
        """Initialize the Google RAG service"""
        if not self._initialized:
            await self.google_rag_service.initialize()
            self._initialized = True
            logger.info("RAG service initialized with Google RAG engine")
    
    async def query(
        self,
        query: RAGQuery
    ) -> RAGResponse:
        """
        Process a RAG query using Google's RAG engine
        
        Args:
            query: RAG query object
            
        Returns:
            RAG response with generated text and sources
        """
        try:
            # Initialize if needed
            if not self._initialized:
                await self.initialize()
            
            # Use Google RAG service for processing
            logger.info(f"Processing RAG query with Google RAG engine: {query.query[:50]}...")
            response = await self.google_rag_service.query(query)
            logger.info("Successfully processed query with Google RAG engine")
            return response
            
        except RAGPipelineError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in RAG query: {e}")
            import traceback
            traceback.print_exc()
            raise RAGPipelineError(f"Failed to process RAG query: {str(e)}")
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a text (legacy method - now uses Google services)
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
        """
        try:
            # This method is kept for backward compatibility
            # In the new Google RAG implementation, embeddings are handled internally
            logger.warning("generate_embedding called on new Google RAG service - this is a legacy method")
            raise RAGPipelineError("Direct embedding generation not supported in Google RAG mode. Use query() method instead.")
        except Exception as e:
            raise RAGPipelineError(f"Failed to generate embedding: {str(e)}")
    
    async def find_similar_content(
        self,
        text: str,
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Find similar content (legacy method - now uses Google RAG)
        
        Args:
            text: Input text to find similar content for
            top_k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            List of similar content items
        """
        try:
            # This method is kept for backward compatibility
            # In the new Google RAG implementation, search is handled internally
            logger.warning("find_similar_content called on new Google RAG service - this is a legacy method")
            raise RAGPipelineError("Direct similarity search not supported in Google RAG mode. Use query() method instead.")
        except Exception as e:
            raise RAGPipelineError(f"Failed to find similar content: {str(e)}")


# Global instance
rag_service = RAGService()
