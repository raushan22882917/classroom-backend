"""Embedding generation service using Vertex AI"""

import asyncio
import os
import logging
from typing import List, Optional
from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingModel
from google.oauth2 import service_account
import numpy as np
from app.config import settings
from app.utils.exceptions import EmbeddingGenerationError

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings using Vertex AI"""
    
    def __init__(self):
        """Initialize Vertex AI and embedding model"""
        # Set up authentication
        self._setup_authentication()
        
        # Initialize Vertex AI
        aiplatform.init(
            project=settings.google_cloud_project,
            location=settings.vertex_ai_location
        )
        self.model_name = settings.vertex_ai_embedding_model
        self.model = None
        self._initialized = False
    
    def _setup_authentication(self):
        """
        Set up Google Cloud authentication.
        Supports: explicit file path, config file path, or Application Default Credentials (ADC)
        """
        try:
            # Check if already set in environment
            if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
                creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
                if os.path.exists(creds_path):
                    print(f"✓ Using GOOGLE_APPLICATION_CREDENTIALS from environment: {creds_path}")
                    return
                else:
                    print(f"Warning: GOOGLE_APPLICATION_CREDENTIALS points to non-existent file: {creds_path}")
            
            # Get the credentials path from settings (if provided)
            creds_path = settings.google_application_credentials
            
            # If no path configured, try to find service-account.json in common locations
            if not creds_path:
                backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                alternative_paths = [
                    os.path.join(backend_dir, "service-account.json"),
                    "./service-account.json",
                    "service-account.json"
                ]
                
                for alt_path in alternative_paths:
                    alt_path = os.path.normpath(alt_path)
                    if os.path.exists(alt_path):
                        creds_path = alt_path
                        break
            
            # If we found a file path, use it
            if creds_path:
                # If path is relative, make it absolute from backend directory
                if not os.path.isabs(creds_path):
                    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    creds_path = os.path.join(backend_dir, creds_path)
                    creds_path = os.path.normpath(creds_path)
                
                if os.path.exists(creds_path):
                    # Set environment variable for Google Cloud libraries
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
                    
                    # Verify credentials can be loaded
                    credentials = service_account.Credentials.from_service_account_file(creds_path)
                    if not credentials:
                        raise EmbeddingGenerationError("Failed to load service account credentials")
                    
                    print(f"✓ Google Cloud authentication configured from: {creds_path}")
                    return
            
            # No file found - try Application Default Credentials (ADC)
            # This works automatically on Google Cloud Run
            import google.auth
            try:
                credentials, project = google.auth.default()
                print(f"✓ Using Application Default Credentials (ADC) for Google Cloud")
                print(f"  Project: {project}")
            except Exception as adc_error:
                raise EmbeddingGenerationError(
                    f"No Google Cloud credentials found. "
                    f"On Cloud Run, ensure the service has a service account attached. "
                    f"For local development, set GOOGLE_APPLICATION_CREDENTIALS in .env or place service-account.json in the project root. "
                    f"ADC error: {str(adc_error)}"
                )
            
        except EmbeddingGenerationError:
            raise
        except Exception as e:
            raise EmbeddingGenerationError(
                f"Failed to set up Google Cloud authentication: {str(e)}. "
                f"Please check your GOOGLE_APPLICATION_CREDENTIALS setting in .env file."
            )
    
    async def initialize(self):
        """Initialize the embedding model"""
        if not self._initialized:
            try:
                self.model = TextEmbeddingModel.from_pretrained(self.model_name)
                self._initialized = True
                print(f"✓ Vertex AI embedding model initialized: {self.model_name}")
            except Exception as e:
                error_msg = str(e)
                if "PERMISSION_DENIED" in error_msg or "IAM_PERMISSION_DENIED" in error_msg:
                    raise EmbeddingGenerationError(
                        f"Permission denied for Vertex AI. The service account needs the 'Vertex AI User' role. "
                        f"Please grant the role 'roles/aiplatform.user' to the service account: "
                        f"classroom@buiseness-417505.iam.gserviceaccount.com. "
                        f"Error details: {error_msg}"
                    )
                raise EmbeddingGenerationError(f"Failed to initialize embedding model: {str(e)}")
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            embeddings = self.model.get_embeddings([text])
            return embeddings[0].values
        except Exception as e:
            error_msg = str(e)
            if "PERMISSION_DENIED" in error_msg or "IAM_PERMISSION_DENIED" in error_msg:
                raise EmbeddingGenerationError(
                    f"Permission denied: The service account needs 'Vertex AI User' role (roles/aiplatform.user). "
                    f"Please grant this role to: classroom@buiseness-417505.iam.gserviceaccount.com. "
                    f"See GOOGLE_CLOUD_AUTH_SETUP.md for instructions. Error: {error_msg}"
                )
            error_msg = str(e)
            # Provide more user-friendly error messages
            if "503" in error_msg or "no route to host" in error_msg.lower() or "connection" in error_msg.lower():
                raise EmbeddingGenerationError(
                    f"Failed to generate embedding: Network connectivity issue with embedding service. "
                    f"This may be a temporary network problem. Please try again."
                )
            raise EmbeddingGenerationError(f"Failed to generate embedding: {error_msg}")
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for a text string.
        Rough estimate: 1 token ≈ 4 characters for English text.
        For math/formulas, it might be slightly different, but this is a safe estimate.
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        # Rough estimate: 1 token ≈ 4 characters
        # This is conservative to ensure we stay under the 20,000 token limit
        return len(text) // 4
    
    def _create_token_aware_batches(self, texts: List[str], max_tokens_per_batch: int = 18000) -> List[List[str]]:
        """
        Create batches that respect the token limit.
        Vertex AI embedding models have a 20,000 token limit per request.
        We use 18,000 as a safe margin.
        
        Args:
            texts: List of texts to batch
            max_tokens_per_batch: Maximum tokens per batch (default 18,000 for safety)
            
        Returns:
            List of batches, each respecting the token limit
        """
        batches = []
        current_batch = []
        current_tokens = 0
        
        for text in texts:
            text_tokens = self._estimate_tokens(text)
            
            # If adding this text would exceed the limit, start a new batch
            if current_tokens + text_tokens > max_tokens_per_batch and current_batch:
                batches.append(current_batch)
                current_batch = [text]
                current_tokens = text_tokens
            else:
                current_batch.append(text)
                current_tokens += text_tokens
        
        # Add the last batch if it has items
        if current_batch:
            batches.append(current_batch)
        
        return batches
    
    async def generate_embeddings_batch(
        self, 
        texts: List[str], 
        batch_size: int = None  # Will use configured batch size if None (but token limit takes precedence)
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.
        Automatically respects the 20,000 token limit per request.
        
        Args:
            texts: List of input texts to embed
            batch_size: Suggested number of texts per batch (token limit takes precedence)
            
        Returns:
            List of embedding vectors
        """
        if not self._initialized:
            await self.initialize()
        
        all_embeddings = []
        
        try:
            # Create token-aware batches (respects 20,000 token limit)
            # Use 18,000 as safe margin to avoid hitting the limit
            token_aware_batches = self._create_token_aware_batches(texts, max_tokens_per_batch=18000)
            
            logger.info(f"Created {len(token_aware_batches)} token-aware batches from {len(texts)} texts")
            
            # Process each batch
            for batch_idx, batch in enumerate(token_aware_batches):
                try:
                    batch_tokens = sum(self._estimate_tokens(text) for text in batch)
                    logger.debug(f"Processing batch {batch_idx + 1}/{len(token_aware_batches)} with {len(batch)} texts (~{batch_tokens} tokens)")
                    
                    embeddings = self.model.get_embeddings(batch)
                    all_embeddings.extend([emb.values for emb in embeddings])
                    
                    # Small delay to avoid rate limiting
                    if batch_idx < len(token_aware_batches) - 1:
                        await asyncio.sleep(0.05)
                except Exception as batch_error:
                    error_msg = str(batch_error)
                    # If we hit token limit error, try splitting this batch further
                    if "token count" in error_msg.lower() or "20000" in error_msg:
                        logger.warning(f"Batch exceeded token limit, splitting further: {error_msg}")
                        # Split this batch in half and retry
                        mid = len(batch) // 2
                        if mid > 0:
                            first_half = batch[:mid]
                            second_half = batch[mid:]
                            for sub_batch in [first_half, second_half]:
                                if sub_batch:
                                    sub_embeddings = self.model.get_embeddings(sub_batch)
                                    all_embeddings.extend([emb.values for emb in sub_embeddings])
                        else:
                            # If batch is already 1 item, it's too large - log error
                            logger.error(f"Single text exceeds token limit: {len(batch[0])} chars")
                            raise EmbeddingGenerationError(f"Text too large for embedding model: {error_msg}")
                    else:
                        raise
            
            return all_embeddings
        except EmbeddingGenerationError:
            raise
        except Exception as e:
            raise EmbeddingGenerationError(f"Failed to generate batch embeddings: {str(e)}")
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings from this model"""
        # text-embedding-005 produces 768-dimensional embeddings
        # text-embedding-004 also produces 768-dimensional embeddings
        # Both models are compatible
        return 768
    
    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        dot_product = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        
        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0
        
        similarity = dot_product / (norm_v1 * norm_v2)
        return float(similarity)


# Global instance
embedding_service = EmbeddingService()
