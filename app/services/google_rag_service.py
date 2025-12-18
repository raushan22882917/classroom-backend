"""Google RAG service using Vertex AI Search and Grounding"""

from typing import List, Optional, Dict, Any
import google.generativeai as genai
from google.cloud import discoveryengine_v1
from google.cloud import aiplatform
from app.config import settings
from app.models.rag import RAGQuery, RAGResponse, RAGContext
from app.utils.exceptions import RAGPipelineError
import logging

logger = logging.getLogger(__name__)


class GoogleRAGService:
    """Service for RAG operations using Google's Vertex AI Search and Grounding"""
    
    def __init__(self):
        """Initialize Google RAG service"""
        self.project_id = settings.google_cloud_project
        self.location = settings.vertex_ai_location
        self.search_engine_id = getattr(settings, 'vertex_search_engine_id', None)
        self.data_store_id = getattr(settings, 'vertex_data_store_id', None)
        
        # Discovery Engine client for search
        self.search_client = None
        
        # Gemini model for generation with grounding
        self._gemini_initialized = False
        self._use_fallback = False
        
        # Fallback content for when search is not available
        self._fallback_content = {
            "mathematics": {
                "algebra": "Algebra is a branch of mathematics dealing with symbols and the rules for manipulating those symbols.",
                "geometry": "Geometry is a branch of mathematics concerned with questions of shape, size, relative position of figures.",
                "calculus": "Calculus is the mathematical study of continuous change.",
                "trigonometry": "Trigonometry is a branch of mathematics that studies relationships between side lengths and angles of triangles."
            },
            "physics": {
                "mechanics": "Mechanics is the area of physics concerned with the motions of objects and forces.",
                "thermodynamics": "Thermodynamics is a branch of physics that deals with heat, work, and temperature.",
                "electromagnetism": "Electromagnetism is a branch of physics involving the study of electromagnetic force."
            },
            "chemistry": {
                "organic": "Organic chemistry is a subdiscipline of chemistry that studies carbon compounds.",
                "inorganic": "Inorganic chemistry deals with the properties and behavior of inorganic compounds.",
                "physical": "Physical chemistry is the study of macroscopic and microscopic phenomena in chemical systems."
            },
            "biology": {
                "cell_biology": "Cell biology is a branch of biology that studies the structure and function of the cell.",
                "genetics": "Genetics is the study of genes, genetic variation, and heredity in organisms.",
                "ecology": "Ecology is the study of the relationships between living organisms and their environment."
            }
        }
    
    def _setup_authentication(self):
        """Set up Google Cloud authentication"""
        try:
            import os
            
            # Check if running on Google Cloud (ADC available)
            if os.getenv('GOOGLE_CLOUD_PROJECT') or os.getenv('GCLOUD_PROJECT'):
                logger.info("Running on Google Cloud, using Application Default Credentials")
                return True
            
            # Check for service account file
            creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            if not creds_path:
                # Try to find service-account.json
                backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                potential_paths = [
                    os.path.join(backend_dir, "service-account.json"),
                    "./service-account.json",
                    "service-account.json"
                ]
                
                for path in potential_paths:
                    if os.path.exists(path):
                        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = path
                        logger.info(f"Using service account from: {path}")
                        return True
            
            # Try to authenticate with default credentials
            import google.auth
            try:
                credentials, project = google.auth.default()
                logger.info(f"Using default credentials for project: {project}")
                return True
            except Exception as e:
                logger.warning(f"Could not authenticate with Google Cloud: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication setup failed: {e}")
            return False
    
    async def initialize(self):
        """Initialize Google RAG services"""
        try:
            # Set up authentication
            if not self._setup_authentication():
                logger.warning("Google Cloud authentication failed, using fallback mode")
                self._use_fallback = True
                return
            
            # Initialize Gemini
            if settings.gemini_api_key:
                genai.configure(api_key=settings.gemini_api_key)
                self._gemini_initialized = True
                logger.info("Gemini API initialized")
            else:
                logger.warning("Gemini API key not found")
                self._use_fallback = True
                return
            
            # Initialize Discovery Engine client for search
            if self.search_engine_id and self.data_store_id:
                try:
                    self.search_client = discoveryengine_v1.SearchServiceClient()
                    logger.info("Vertex AI Search initialized")
                except Exception as e:
                    logger.warning(f"Could not initialize Vertex AI Search: {e}")
                    logger.info("Will use Gemini with grounding instead")
            else:
                logger.info("Vertex AI Search not configured, using Gemini with grounding")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google RAG service: {e}")
            self._use_fallback = True
    
    def _get_fallback_content(self, query: str, subject: str) -> List[str]:
        """Get fallback content based on query and subject"""
        content_pieces = []
        
        # Get subject-specific content
        if subject and subject.lower() in self._fallback_content:
            subject_content = self._fallback_content[subject.lower()]
            
            # Simple keyword matching
            query_lower = query.lower()
            for topic, description in subject_content.items():
                if any(keyword in query_lower for keyword in topic.split('_')):
                    content_pieces.append(f"{topic.replace('_', ' ').title()}: {description}")
        
        # Add general content if no specific matches
        if not content_pieces:
            content_pieces.append(
                f"This is a question about {subject or 'general studies'}. "
                "I'll provide a helpful response based on standard curriculum knowledge."
            )
        
        return content_pieces
    
    async def query(self, query: RAGQuery) -> RAGResponse:
        """
        Process a RAG query using Google's services
        
        Args:
            query: RAG query object
            
        Returns:
            RAG response with generated text and sources
        """
        try:
            # Initialize if not already done
            if not self._gemini_initialized and not self._use_fallback:
                await self.initialize()
            
            # If using fallback mode, generate response directly
            if self._use_fallback:
                return await self._generate_fallback_response(query)
            
            # Try Vertex AI Search first
            search_results = []
            if self.search_client and self.search_engine_id:
                try:
                    search_results = await self._search_with_vertex_ai(query)
                except Exception as e:
                    logger.warning(f"Vertex AI Search failed: {e}")
            
            # If no search results, try Gemini with grounding
            if not search_results:
                return await self._generate_with_grounding(query)
            
            # Generate response using search results
            return await self._generate_with_search_results(query, search_results)
            
        except Exception as e:
            logger.error(f"Error in Google RAG query: {e}")
            # Fallback to simple generation
            return await self._generate_fallback_response(query)
    
    async def _search_with_vertex_ai(self, query: RAGQuery) -> List[Dict]:
        """Search using Vertex AI Search"""
        try:
            # Construct the search request
            serving_config = f"projects/{self.project_id}/locations/global/collections/default_collection/engines/{self.search_engine_id}/servingConfigs/default_config"
            
            request = discoveryengine_v1.SearchRequest(
                serving_config=serving_config,
                query=query.query,
                page_size=min(query.top_k, 10),
                query_expansion_spec=discoveryengine_v1.SearchRequest.QueryExpansionSpec(
                    condition=discoveryengine_v1.SearchRequest.QueryExpansionSpec.Condition.AUTO,
                ),
                spell_correction_spec=discoveryengine_v1.SearchRequest.SpellCorrectionSpec(
                    mode=discoveryengine_v1.SearchRequest.SpellCorrectionSpec.Mode.AUTO
                )
            )
            
            # Add subject filter if provided
            if query.subject:
                request.filter = f'subject: ANY("{query.subject.value}")'
            
            # Execute search
            response = self.search_client.search(request=request)
            
            # Process results
            results = []
            for result in response.results:
                document = result.document
                results.append({
                    "id": document.id,
                    "title": document.struct_data.get("title", ""),
                    "content": document.struct_data.get("content", ""),
                    "subject": document.struct_data.get("subject", ""),
                    "chapter": document.struct_data.get("chapter", ""),
                    "score": getattr(result, 'relevance_score', 0.8)
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Vertex AI Search error: {e}")
            return []
    
    async def _generate_with_grounding(self, query: RAGQuery) -> RAGResponse:
        """Generate response using Gemini with grounding"""
        try:
            # Use available Gemini model with fallback
            model_names = ['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-pro']
            model = None
            
            for model_name in model_names:
                try:
                    model = genai.GenerativeModel(model_name)
                    logger.info(f"Using Gemini model: {model_name}")
                    break
                except Exception as e:
                    logger.debug(f"Model {model_name} not available: {e}")
                    continue
            
            if model is None:
                raise Exception("No available Gemini model found")
            
            # Create grounded prompt
            subject_context = f" in {query.subject.value}" if query.subject else ""
            prompt = f"""You are an expert tutor for Class 12 students in India. Answer this question{subject_context}:

{query.query}

Provide a clear, accurate, and helpful response appropriate for Class 12 level. Include relevant examples and explanations."""

            # Generate with grounding (if available)
            try:
                response = model.generate_content(
                    prompt,
                    generation_config={
                        "temperature": 0.1,
                        "top_p": 0.8,
                        "top_k": 40,
                        "max_output_tokens": query.max_tokens or 500
                    }
                )
                
                generated_text = response.text if response.text else "I couldn't generate a response. Please try rephrasing your question."
                
            except Exception as e:
                logger.warning(f"Gemini generation failed: {e}")
                generated_text = "I'm having trouble generating a response right now. Please try again later."
            
            return RAGResponse(
                query=query.query,
                generated_text=generated_text,
                contexts=[],
                confidence=0.7,
                sources=[],
                metadata={
                    "mode": "gemini_grounding",
                    "subject": query.subject.value if query.subject else None
                }
            )
            
        except Exception as e:
            logger.error(f"Grounding generation failed: {e}")
            return await self._generate_fallback_response(query)
    
    async def _generate_with_search_results(self, query: RAGQuery, search_results: List[Dict]) -> RAGResponse:
        """Generate response using search results"""
        try:
            # Build context from search results
            contexts = []
            context_text_parts = []
            sources = []
            
            for idx, result in enumerate(search_results):
                # Create RAGContext
                rag_context = RAGContext(
                    chunk_id=result["id"],
                    content_id=result["id"],
                    text=result["content"],
                    similarity_score=result["score"],
                    metadata={
                        "title": result["title"],
                        "subject": result["subject"],
                        "chapter": result["chapter"]
                    },
                    source_type="vertex_search",
                    subject=query.subject
                )
                contexts.append(rag_context)
                
                # Build context text
                context_text_parts.append(
                    f"[Source {idx + 1}] {result['title']}\n{result['content']}"
                )
                
                # Build sources
                sources.append({
                    "id": result["id"],
                    "type": "vertex_search",
                    "title": result["title"],
                    "subject": result["subject"],
                    "chapter": result["chapter"],
                    "similarity": result["score"]
                })
            
            context_text = "\n\n".join(context_text_parts)
            
            # Generate response using Gemini with context
            model_names = ['gemini-2.0-flash-exp', 'gemini-1.5-flash', 'gemini-pro']
            model = None
            
            for model_name in model_names:
                try:
                    model = genai.GenerativeModel(model_name)
                    break
                except Exception:
                    continue
            
            if model is None:
                raise Exception("No available Gemini model found")
            
            prompt = f"""You are an expert tutor for Class 12 students in India. Use the provided context to answer the student's question.

Context from curriculum materials:
{context_text}

Student's Question: {query.query}

Instructions:
1. Answer using the information from the context above
2. Explain concepts clearly for Class 12 students
3. Include relevant examples from the context
4. If the context doesn't fully answer the question, acknowledge this

Answer:"""

            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.1,
                    "top_p": 0.8,
                    "top_k": 40,
                    "max_output_tokens": query.max_tokens or 500
                }
            )
            
            generated_text = response.text if response.text else "I couldn't generate a response based on the available content."
            
            # Calculate average confidence
            avg_confidence = sum(r["score"] for r in search_results) / len(search_results) if search_results else 0.5
            
            return RAGResponse(
                query=query.query,
                generated_text=generated_text,
                contexts=contexts,
                confidence=avg_confidence,
                sources=sources,
                metadata={
                    "mode": "vertex_search_with_gemini",
                    "search_results_count": len(search_results)
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to generate with search results: {e}")
            return await self._generate_fallback_response(query)
    
    async def _generate_fallback_response(self, query: RAGQuery) -> RAGResponse:
        """Generate fallback response when other methods fail"""
        try:
            # Get fallback content
            subject_str = query.subject.value if query.subject else "general"
            fallback_content = self._get_fallback_content(query.query, subject_str)
            
            # Try to use Gemini if available
            if self._gemini_initialized:
                try:
                    # Try available models
                    model_names = ['gemini-2.0-flash-exp', 'gemini-1.5-flash', 'gemini-pro']
                    model = None
                    
                    for model_name in model_names:
                        try:
                            model = genai.GenerativeModel(model_name)
                            break
                        except Exception:
                            continue
                    
                    if model is None:
                        raise Exception("No available Gemini model found")
                    
                    prompt = f"""You are an expert tutor for Class 12 students in India. Answer this question about {subject_str}:

{query.query}

Provide a clear, accurate response appropriate for Class 12 level."""

                    response = model.generate_content(
                        prompt,
                        generation_config={
                            "temperature": 0.2,
                            "max_output_tokens": query.max_tokens or 300
                        }
                    )
                    
                    generated_text = response.text if response.text else f"Here's what I know about this topic:\n\n{' '.join(fallback_content)}"
                    
                except Exception as e:
                    logger.warning(f"Fallback Gemini generation failed: {e}")
                    generated_text = f"I can help with this topic. {' '.join(fallback_content)}"
            else:
                generated_text = f"Here's information about your question:\n\n{' '.join(fallback_content)}"
            
            return RAGResponse(
                query=query.query,
                generated_text=generated_text,
                contexts=[],
                confidence=0.5,
                sources=[],
                metadata={
                    "mode": "fallback",
                    "subject": subject_str
                }
            )
            
        except Exception as e:
            logger.error(f"Fallback generation failed: {e}")
            return RAGResponse(
                query=query.query,
                generated_text="I'm experiencing technical difficulties. Please try again later.",
                contexts=[],
                confidence=0.1,
                sources=[],
                metadata={"mode": "error", "error": str(e)}
            )


# Global instance
google_rag_service = GoogleRAGService()