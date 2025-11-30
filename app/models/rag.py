"""RAG pipeline models"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from .base import Subject


class EmbeddingVector(BaseModel):
    """Embedding vector model"""
    id: str
    content_id: str
    vector: List[float]
    dimension: int
    model_name: str = "text-embedding-005"  # Updated to faster model
    metadata: dict = Field(default_factory=dict)

    class Config:
        from_attributes = True


class RAGQuery(BaseModel):
    """RAG query model"""
    query: str
    subject: Optional[Subject] = None
    top_k: int = Field(default=5, ge=1, le=20)
    confidence_threshold: float = Field(default=0.7, ge=0, le=1)
    filters: dict = Field(default_factory=dict)


class RAGContext(BaseModel):
    """RAG context model"""
    chunk_id: str
    content_id: str
    text: str
    similarity_score: float = Field(ge=0, le=1)
    metadata: dict = Field(default_factory=dict)
    source_type: str
    subject: Optional[Subject] = None

    class Config:
        from_attributes = True


class RAGResponse(BaseModel):
    """RAG response model"""
    query: str
    generated_text: str
    contexts: List[RAGContext]
    confidence: float = Field(ge=0, le=1)
    sources: List[dict] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


class EmbeddingRequest(BaseModel):
    """Embedding generation request"""
    texts: List[str]
    model_name: str = "text-embedding-005"  # Updated to faster model
    batch_size: int = Field(default=50, ge=1, le=100)  # Updated to use optimized batch size


class EmbeddingResponse(BaseModel):
    """Embedding generation response"""
    embeddings: List[List[float]]
    dimension: int
    model_name: str
    count: int


class SimilaritySearchRequest(BaseModel):
    """Similarity search request"""
    query_vector: List[float]
    top_k: int = Field(default=5, ge=1, le=20)
    filters: Optional[Dict] = None
    subject: Optional[Subject] = None


class SimilaritySearchResult(BaseModel):
    """Similarity search result"""
    content_id: str
    chunk_id: str
    similarity_score: float = Field(ge=0, le=1)
    text: str
    metadata: dict = Field(default_factory=dict)


class ContentIndexRequest(BaseModel):
    """Content indexing request"""
    content_id: str
    text: str
    metadata: dict = Field(default_factory=dict)
    chunk_size: int = Field(default=300, ge=100, le=1000)
    chunk_overlap: int = Field(default=50, ge=0, le=200)


class ContentIndexResponse(BaseModel):
    """Content indexing response"""
    content_id: str
    chunks_created: int
    embeddings_generated: int
    success: bool
    message: Optional[str] = None
