"""RAG (Retrieval-Augmented Generation) service"""

from typing import List, Optional, Dict
import google.generativeai as genai
from langchain_core.prompts import PromptTemplate
from app.config import settings
from app.models.rag import RAGQuery, RAGResponse, RAGContext
from app.services.embedding_service import embedding_service
from app.services.vector_db_service import vector_db_service
from app.utils.exceptions import RAGPipelineError


class RAGService:
    """Service for RAG pipeline operations"""
    
    def __init__(self):
        """Initialize RAG service"""
        self.embedding_service = embedding_service
        self.vector_db_service = vector_db_service
        self._gemini_initialized = False
        
        # Prompt template for RAG - STRICT: Only use provided context, no external knowledge
        self.prompt_template = PromptTemplate(
            input_variables=["context", "query"],
            template="""You are an expert tutor for Class 12 students in India. You MUST ONLY use the information provided in the context below. DO NOT use any external knowledge or information not present in the context.

Context from curriculum materials:
{context}

Student's Question: {query}

CRITICAL INSTRUCTIONS:
1. Answer ONLY using information from the context provided above
2. DO NOT add any information that is not in the context
3. If the context doesn't contain enough information to answer the question, say "The available content doesn't contain enough information to fully answer this question. Here's what I found: [summarize what is available]"
4. Paraphrase and explain the context in simple language appropriate for Class 12 students
5. If you need to explain concepts, only use examples that are mentioned in the context
6. Clearly indicate which source each piece of information comes from
7. If the question cannot be answered from the context, acknowledge this clearly

Answer (ONLY from context, no external knowledge):"""
        )
    
    def _initialize_gemini(self):
        """Initialize Gemini API"""
        if not self._gemini_initialized:
            genai.configure(api_key=settings.gemini_api_key)
            self._gemini_initialized = True
    
    async def query(
        self,
        query: RAGQuery
    ) -> RAGResponse:
        """
        Process a RAG query
        
        Args:
            query: RAG query object
            
        Returns:
            RAG response with generated text and sources
        """
        try:
            # Initialize services if needed
            if not self.embedding_service._initialized:
                await self.embedding_service.initialize()
            if not self.vector_db_service._initialized:
                await self.vector_db_service.initialize()
            
            # Step 1: Generate query embedding
            try:
                query_embedding = await self.embedding_service.generate_embedding(
                    query.query
                )
            except Exception as e:
                error_msg = str(e)
                print(f"Error generating embedding: {e}")
                import traceback
                traceback.print_exc()
                
                # Check for authentication errors
                if "Unable to authenticate" in error_msg or "authentication" in error_msg.lower():
                    raise RAGPipelineError(
                        f"Google Cloud authentication failed. "
                        f"On Cloud Run, ensure the service account attached to the service has Vertex AI permissions. "
                        f"For local development, set GOOGLE_APPLICATION_CREDENTIALS environment variable. "
                        f"Error: {error_msg}"
                    )
                raise RAGPipelineError(f"Failed to generate embedding: {error_msg}")
            
            # Step 2: Build filters if subject is specified
            filters = query.filters.copy() if query.filters else {}
            if query.subject:
                filters["subject"] = query.subject.value
            
            # Step 3: Retrieve similar content chunks
            try:
                search_results = await self.vector_db_service.query_similar(
                    query_vector=query_embedding,
                    top_k=query.top_k,
                    filters=filters if filters else None
                )
            except Exception as e:
                print(f"Error querying vector database: {e}")
                import traceback
                traceback.print_exc()
                raise RAGPipelineError(f"Failed to query vector database: {str(e)}")
            
            # Step 4: Check if we have search results
            if not search_results:
                # Try a broader search without subject filter if subject was specified
                if query.subject:
                    print(f"No results with subject filter, trying without subject...")
                    filters_no_subject = query.filters.copy() if query.filters else {}
                    # Remove subject filter
                    search_results = await self.vector_db_service.query_similar(
                        query_vector=query_embedding,
                        top_k=query.top_k,
                        filters=filters_no_subject if filters_no_subject else None
                    )
                
                # If still no results, return empty response
                if not search_results:
                    return RAGResponse(
                        query=query.query,
                        generated_text="I couldn't find relevant information in the available content. Please try rephrasing your question or ask about a different topic.",
                        contexts=[],
                        confidence=0.0,
                        sources=[],
                        metadata={"reason": "no_results"}
                    )
            
            # Calculate average confidence
            avg_confidence = sum(r.similarity_score for r in search_results) / len(search_results)
            
            # Step 5: Check confidence threshold - but still return context if available
            # We'll use a lower threshold and let the user see what we found
            use_lower_threshold = avg_confidence < query.confidence_threshold
            
            # Step 6: Build context from retrieved chunks
            contexts = []
            context_text_parts = []
            sources = []
            
            for idx, result in enumerate(search_results):
                # Create RAGContext object
                rag_context = RAGContext(
                    chunk_id=result.chunk_id,
                    content_id=result.content_id,
                    text=result.text,
                    similarity_score=result.similarity_score,
                    metadata=result.metadata,
                    source_type=result.metadata.get("type", "unknown"),
                    subject=query.subject
                )
                contexts.append(rag_context)
                
                # Build context text
                context_text_parts.append(
                    f"[Source {idx + 1}] ({result.metadata.get('type', 'content')} - "
                    f"{result.metadata.get('chapter', 'N/A')})\n{result.text}"
                )
                
                # Build sources list
                sources.append({
                    "id": result.content_id,
                    "type": result.metadata.get("type", "unknown"),
                    "subject": result.metadata.get("subject", ""),
                    "chapter": result.metadata.get("chapter", ""),
                    "similarity": result.similarity_score
                })
            
            context_text = "\n\n".join(context_text_parts)
            
            # Step 7: Generate response using Gemini - STRICT: Only from context
            self._initialize_gemini()
            
            prompt = self.prompt_template.format(
                context=context_text,
                query=query.query
            )
            
            try:
                # Use faster model for better response times
                model_name = getattr(settings, 'gemini_model_fast', 'gemini-2.5-flash')
                try:
                    model = genai.GenerativeModel(model_name)
                except Exception as model_error:
                    print(f"Error creating Gemini model {model_name}: {model_error}")
                    # Try fallback models
                    fallback_models = ['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-pro']
                    model = None
                    for fallback_name in fallback_models:
                        if fallback_name == model_name:
                            continue
                        try:
                            model = genai.GenerativeModel(fallback_name)
                            model_name = fallback_name
                            print(f"Using fallback model: {fallback_name}")
                            break
                        except Exception:
                            continue
                    
                    if model is None:
                        raise RAGPipelineError(f"Failed to create any Gemini model: {str(model_error)}")
                
                response = model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": 0.1,  # Low temperature for more factual responses
                        "top_p": 0.8,
                        "top_k": 40
                    }
                )
                
                # Handle response safely
                if not response:
                    generated_text = "I couldn't generate a response. Please try again."
                elif hasattr(response, 'text') and response.text:
                    generated_text = response.text
                elif hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                        generated_text = candidate.content.parts[0].text if candidate.content.parts else "I couldn't generate a response. Please try again."
                    else:
                        generated_text = "I couldn't generate a response. Please try again."
                else:
                    generated_text = "I couldn't generate a response. Please try again."
                
                # If confidence is low, add a disclaimer
                if use_lower_threshold:
                    generated_text = f"*Note: The confidence in this answer is {avg_confidence:.1%}. Here's what I found in the available content:*\n\n{generated_text}"
                    
            except Exception as e:
                # Fallback: return raw context if generation fails
                print(f"Error generating RAG response: {e}")
                import traceback
                traceback.print_exc()
                generated_text = f"Here's the relevant content I found:\n\n{context_text}\n\n*This is direct content from the curriculum materials.*"
            
            # Step 8: Return RAG response
            return RAGResponse(
                query=query.query,
                generated_text=generated_text,
                contexts=contexts,
                confidence=avg_confidence,
                sources=sources,
                metadata={
                    "model": model_name,
                    "chunks_retrieved": len(search_results)
                }
            )
            
        except RAGPipelineError:
            raise
        except Exception as e:
            print(f"Unexpected error in RAG query: {e}")
            import traceback
            traceback.print_exc()
            raise RAGPipelineError(f"Failed to process RAG query: {str(e)}")
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a text
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
        """
        try:
            return await self.embedding_service.generate_embedding(text)
        except Exception as e:
            raise RAGPipelineError(f"Failed to generate embedding: {str(e)}")
    
    async def find_similar_content(
        self,
        text: str,
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Find similar content to given text
        
        Args:
            text: Input text to find similar content for
            top_k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            List of similar content items
        """
        try:
            # Generate embedding for input text
            embedding = await self.embedding_service.generate_embedding(text)
            
            # Search for similar vectors
            results = await self.vector_db_service.query_similar(
                query_vector=embedding,
                top_k=top_k,
                filters=filters
            )
            
            # Convert to dict format
            return [
                {
                    "content_id": r.content_id,
                    "chunk_id": r.chunk_id,
                    "text": r.text,
                    "similarity_score": r.similarity_score,
                    "metadata": r.metadata
                }
                for r in results
            ]
            
        except Exception as e:
            raise RAGPipelineError(f"Failed to find similar content: {str(e)}")


# Global instance
rag_service = RAGService()
