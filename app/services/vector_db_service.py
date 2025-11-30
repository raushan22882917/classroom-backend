"""Vector database service using Vertex AI Vector Search"""

from typing import List, Dict, Optional
import os
import numpy as np
from app.config import settings
from app.models.rag import SimilaritySearchResult
from app.utils.exceptions import VectorDBError


class VectorDBService:
    """Service for managing vector database operations with Vertex AI Vector Search"""
    
    def __init__(self):
        """Initialize Vertex AI Vector Search client"""
        self.project_id = settings.google_cloud_project
        self.location = settings.vertex_ai_location
        self.index_name = settings.pinecone_index_name  # Reusing this config key
        self.index_endpoint = None
        self.index = None
        self._initialized = False
        
        # For development: use in-memory storage if Vertex AI Vector Search is not configured
        self._use_memory_store = False
        self._memory_vectors: Dict[str, tuple] = {}  # id -> (vector, metadata)
    
    def _setup_authentication(self):
        """Set up Google Cloud authentication"""
        try:
            if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
                creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                if os.path.exists(creds_path):
                    return
                else:
                    print(f"Warning: GOOGLE_APPLICATION_CREDENTIALS points to non-existent file: {creds_path}")
            
            creds_path = settings.google_application_credentials
            if not os.path.isabs(creds_path):
                backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                creds_path = os.path.join(backend_dir, creds_path)
                creds_path = os.path.normpath(creds_path)
            
            if os.path.exists(creds_path):
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
                print(f"✓ Google Cloud authentication configured from: {creds_path}")
            else:
                print(f"Warning: Service account file not found at: {creds_path}")
                print("Falling back to in-memory vector store for development")
                self._use_memory_store = True
        except Exception as e:
            print(f"Warning: Could not set up Google Cloud authentication: {e}")
            print("Falling back to in-memory vector store for development")
            self._use_memory_store = True
    
    async def initialize(self):
        """Initialize or connect to Vertex AI Vector Search index"""
        if not self._initialized:
            try:
                self._setup_authentication()
                
                # Always use in-memory store for development (Vertex AI Vector Search requires setup)
                self._use_memory_store = True
                print("✓ Using in-memory vector store (Vertex AI Vector Search not configured)")
                print("⚠ This is suitable for development only. For production, set up Vertex AI Vector Search.")
                print("⚠ See backend/VERTEX_AI_VECTOR_SEARCH_SETUP.md for instructions")
                self._initialized = True
            except Exception as e:
                print(f"Warning: Could not initialize Vertex AI Vector Search: {e}")
                print("Falling back to in-memory vector store")
                self._use_memory_store = True
                self._initialized = True
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(dot_product / (norm1 * norm2))
    
    async def upsert_vectors(
        self,
        vectors: List[tuple],  # List of (id, vector, metadata)
        namespace: str = ""
    ) -> Dict:
        """
        Upsert vectors into the index
        
        Args:
            vectors: List of tuples (id, vector, metadata)
            namespace: Optional namespace for organizing vectors (not used in memory store)
            
        Returns:
            Upsert response
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Always use memory store for development
            if not self._use_memory_store:
                self._use_memory_store = True
            
            # Store in memory
            for vector_id, vector, metadata in vectors:
                self._memory_vectors[vector_id] = (vector, metadata)
            
            return {
                "upserted_count": len(vectors),
                "namespace": namespace
            }
        except Exception as e:
            raise VectorDBError(f"Failed to upsert vectors: {str(e)}")
    
    async def query_similar(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict] = None,
        namespace: str = ""
    ) -> List[SimilaritySearchResult]:
        """
        Query for similar vectors
        
        Args:
            query_vector: Query embedding vector
            top_k: Number of results to return
            filters: Optional metadata filters
            namespace: Optional namespace to query (not used in memory store)
            
        Returns:
            List of similarity search results
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            # Always use memory store for development
            if not self._use_memory_store:
                self._use_memory_store = True
            
            # Check if we have any vectors
            if not self._memory_vectors:
                return []
            
            # Calculate similarity for all vectors
            similarities = []
            for vector_id, (vector, metadata) in self._memory_vectors.items():
                # Apply filters if provided
                if filters:
                    match = True
                    for key, value in filters.items():
                        if metadata.get(key) != value:
                            match = False
                            break
                    if not match:
                        continue
                
                similarity = self._cosine_similarity(query_vector, vector)
                similarities.append({
                    "id": vector_id,
                    "score": similarity,
                    "metadata": metadata
                })
            
            # Sort by similarity and take top_k
            similarities.sort(key=lambda x: x["score"], reverse=True)
            top_results = similarities[:top_k]
            
            # Convert to SimilaritySearchResult objects
            results = []
            for result in top_results:
                metadata = result["metadata"] or {}
                results.append(
                    SimilaritySearchResult(
                        content_id=metadata.get("content_id", ""),
                        chunk_id=result["id"],
                        similarity_score=result["score"],
                        text=metadata.get("text", ""),
                        metadata=metadata
                    )
                )
            
            return results
        except Exception as e:
            raise VectorDBError(f"Failed to query similar vectors: {str(e)}")
    
    async def delete_vectors(
        self,
        ids: List[str],
        namespace: str = ""
    ) -> Dict:
        """
        Delete vectors by IDs
        
        Args:
            ids: List of vector IDs to delete
            namespace: Optional namespace
            
        Returns:
            Delete response
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            deleted_count = 0
            for vector_id in ids:
                if vector_id in self._memory_vectors:
                    del self._memory_vectors[vector_id]
                    deleted_count += 1
            
            return {
                "deleted_count": deleted_count,
                "namespace": namespace
            }
        except Exception as e:
            raise VectorDBError(f"Failed to delete vectors: {str(e)}")
    
    async def delete_by_filter(
        self,
        filters: Dict,
        namespace: str = ""
    ) -> Dict:
        """
        Delete vectors by metadata filter
        
        Args:
            filters: Metadata filters
            namespace: Optional namespace
            
        Returns:
            Delete response
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            deleted_ids = []
            for vector_id, (vector, metadata) in list(self._memory_vectors.items()):
                match = True
                for key, value in filters.items():
                    if metadata.get(key) != value:
                        match = False
                        break
                if match:
                    deleted_ids.append(vector_id)
            
            for vector_id in deleted_ids:
                del self._memory_vectors[vector_id]
            
            return {
                "deleted_count": len(deleted_ids),
                "namespace": namespace
            }
        except Exception as e:
            raise VectorDBError(f"Failed to delete by filter: {str(e)}")
    
    async def get_index_stats(self) -> Dict:
        """Get index statistics"""
        if not self._initialized:
            await self.initialize()
        
        try:
            if self._use_memory_store or len(self._memory_vectors) > 0:
                return {
                    "total_vector_count": len(self._memory_vectors),
                    "storage_type": "in-memory"
                }
            else:
                return {
                    "total_vector_count": 0,
                    "storage_type": "vertex-ai-vector-search"
                }
        except Exception as e:
            raise VectorDBError(f"Failed to get index stats: {str(e)}")


# Global instance
vector_db_service = VectorDBService()
