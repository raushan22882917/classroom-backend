"""RAG pipeline endpoints"""

from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from app.models.rag import (
    RAGQuery,
    RAGResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    SimilaritySearchRequest,
    SimilaritySearchResult
)
from app.models.base import BaseResponse
from app.services.rag_service import rag_service
from app.utils.exceptions import RAGPipelineError

router = APIRouter(prefix="/rag", tags=["RAG Pipeline"])

# Initialize Gemini at module level for direct queries
import logging
logger = logging.getLogger(__name__)

def _get_gemini_model():
    """Get Gemini model with fallback chain - lazy initialization"""
    from app.config import settings
    import google.generativeai as genai
    
    if not settings.gemini_api_key:
        return None
    
    genai.configure(api_key=settings.gemini_api_key)
    
    # Try models in order of preference - include all available Gemini models
    # Note: We don't test generation here, just model creation
    # Actual availability will be tested during generate_content call
    
    # Get comprehensive model list from settings
    fast_chain = getattr(settings, 'gemini_models_fast_chain', 'gemini-2.5-flash,gemini-2.5-flash-lite,gemini-2.0-flash,gemini-2.0-flash-lite,gemini-1.5-flash')
    quality_chain = getattr(settings, 'gemini_models_quality_chain', 'gemini-3.0-pro,gemini-2.5-pro,gemini-1.5-pro')
    
    fast_models = [m.strip() for m in fast_chain.split(',') if m.strip()]
    quality_models = [m.strip() for m in quality_chain.split(',') if m.strip()]
    
    # Comprehensive model list: latest models first, then fallbacks
    model_names = [
        getattr(settings, 'gemini_model_fast', 'gemini-2.5-flash'),
        getattr(settings, 'gemini_model_quality', 'gemini-3.0-pro'),
    ] + fast_models + quality_models + [
        'gemini-3-pro-preview',  # Legacy preview model
        'gemini-1.5-pro',  # Legacy model
        'gemini-pro'  # Oldest fallback
    ]
    # Remove duplicates while preserving order
    seen = set()
    model_names = [x for x in model_names if not (x in seen or seen.add(x))]
    
    for model_name in model_names:
        try:
            model = genai.GenerativeModel(model_name)
            logger.info(f"Direct Gemini model created: {model_name}")
            return model, model_name
        except Exception as e:
            logger.debug(f"Failed to create {model_name}: {str(e)}")
            continue
    
    logger.error("Failed to create any Gemini model")
    return None, None

# Don't pre-initialize - lazy load when needed
direct_gemini_model = None
direct_gemini_model_name = None


@router.post("/query-direct", response_model=RAGResponse)
async def process_direct_gemini_query(query: RAGQuery):
    """
    Process a query using Gemini directly without embeddings (fallback mode)
    Useful when embedding service is not available
    
    Args:
        query: RAG query with text and subject
        
    Returns:
        Response with generated text
    """
    try:
        # Lazy load model if not already initialized
        global direct_gemini_model, direct_gemini_model_name
        if direct_gemini_model is None:
            logger.info("Initializing Gemini model...")
            result = _get_gemini_model()
            if result[0] is None:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="No available Gemini model found. Please check your API key and model availability."
                )
            direct_gemini_model, direct_gemini_model_name = result
            logger.info(f"Gemini model initialized: {direct_gemini_model_name}")
        
        model = direct_gemini_model
        
        # Build prompt
        subject_value = query.subject.value if query.subject and hasattr(query.subject, 'value') else (str(query.subject) if query.subject else 'General')
        subject_context = f"Subject: {subject_value}" if query.subject else ""
        
        prompt = f"""You are an expert tutor for Class 12 students in India. Answer the student's question clearly and helpfully.

{subject_context}

Student's Question: {query.query}

Instructions:
1. Provide a clear, accurate answer
2. Use simple language appropriate for Class 12 students
3. Include relevant examples or explanations
4. If you're not certain, acknowledge this

Answer:"""
        
        # Generate response with model fallback
        generated_text = None
        gen_error = None
        
        # Try current model first
        try:
            response = model.generate_content(prompt)
            
            # Handle response safely
            if not response:
                raise Exception("Empty response from Gemini")
            elif hasattr(response, 'text') and response.text:
                generated_text = response.text
            elif hasattr(response, 'candidates') and response.candidates:
                # Try to extract text from candidates
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    generated_text = candidate.content.parts[0].text if candidate.content.parts else None
                else:
                    raise Exception("Could not extract text from response candidates")
            else:
                raise Exception("Unexpected response format")
                
        except Exception as e:
            gen_error = e
            logger.warning(f"Failed to generate with {direct_gemini_model_name}: {str(e)}")
            
            # Try fallback models if current model failed
            if "not found" in str(e).lower() or "404" in str(e):
                logger.info("Model not found, trying fallback models...")
                from app.config import settings
                import google.generativeai as genai
                
                genai.configure(api_key=settings.gemini_api_key)
                
                # Get comprehensive fallback model list
                fast_chain = getattr(settings, 'gemini_models_fast_chain', 'gemini-2.5-flash,gemini-2.5-flash-lite,gemini-2.0-flash,gemini-2.0-flash-lite,gemini-1.5-flash')
                quality_chain = getattr(settings, 'gemini_models_quality_chain', 'gemini-3.0-pro,gemini-2.5-pro,gemini-1.5-pro')
                
                fast_models = [m.strip() for m in fast_chain.split(',') if m.strip()]
                quality_models = [m.strip() for m in quality_chain.split(',') if m.strip()]
                
                fallback_models = [
                    getattr(settings, 'gemini_model_fast', 'gemini-2.5-flash'),
                    getattr(settings, 'gemini_model_quality', 'gemini-3.0-pro'),
                ] + fast_models + quality_models + [
                    'gemini-3-pro-preview',
                    'gemini-1.5-pro',
                    'gemini-pro'
                ]
                # Remove duplicates while preserving order
                seen = set()
                fallback_models = [x for x in fallback_models if not (x in seen or seen.add(x))]
                
                for fallback_name in fallback_models:
                    if fallback_name == direct_gemini_model_name:
                        continue  # Skip already tried model
                    try:
                        logger.info(f"Trying fallback model: {fallback_name}")
                        fallback_model = genai.GenerativeModel(fallback_name)
                        response = fallback_model.generate_content(prompt)
                        
                        if response and hasattr(response, 'text') and response.text:
                            generated_text = response.text
                            # Update global model for next time
                            direct_gemini_model = fallback_model
                            direct_gemini_model_name = fallback_name
                            logger.info(f"Successfully used fallback model: {fallback_name}")
                            break
                    except Exception as fallback_error:
                        logger.debug(f"Fallback model {fallback_name} also failed: {str(fallback_error)}")
                        continue
        
        if generated_text is None:
            logger.error(f"All Gemini models failed. Last error: {str(gen_error)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Failed to generate response with any available Gemini model. Please check your API key and model availability."
            )
        
        # Build response
        response_data = RAGResponse(
            query=query.query,
            generated_text=generated_text,
            contexts=[],  # Empty list is valid for direct Gemini mode
            confidence=0.8,
            sources=[],
            metadata={"mode": "direct_gemini", "subject": subject_value if query.subject else None}
        )
        
        logger.info(f"Successfully generated direct Gemini response for query: {query.query[:50]}...")
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in direct Gemini query: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process direct query: {str(e)}"
        )


@router.post("/query", response_model=RAGResponse)
async def process_rag_query(query: RAGQuery):
    """
    Process a RAG query to retrieve relevant content and generate a response
    
    Args:
        query: RAG query with text, subject, and parameters
        
    Returns:
        RAG response with generated text, contexts, and sources
    """
    try:
        logger.info(f"Processing RAG query: {query.query[:50]}...")
        response = await rag_service.query(query)
        logger.info(f"Successfully processed RAG query")
        return response
    except RAGPipelineError as e:
        error_message = str(e)
        logger.warning(f"RAG pipeline error (will fallback to direct Gemini): {error_message}")
        
        # Check if it's an authentication error - provide user-friendly message
        is_auth_error = (
            "Unable to authenticate" in error_message or
            "authentication" in error_message.lower() or
            "Unable to authenticate your request" in error_message
        )
        
        if is_auth_error:
            # For auth errors, try fallback but with clear message
            logger.info(f"Authentication error detected, attempting direct Gemini fallback")
            try:
                direct_response = await process_direct_gemini_query(query)
                direct_response.metadata = direct_response.metadata or {}
                direct_response.metadata["fallback_reason"] = "authentication_error"
                direct_response.metadata["original_error"] = error_message
                direct_response.confidence = 0.6
                return direct_response
            except Exception as fallback_error:
                logger.error(f"Direct Gemini fallback also failed: {str(fallback_error)}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="I apologize, but I encountered an error while searching the curriculum. Please try rephrasing your question. Error: Failed to process RAG query: " + error_message
                )
        
        # For any RAG pipeline error, try direct Gemini fallback
            # For other RAG errors, still try fallback but with different message
            logger.info(f"RAG error detected, attempting direct Gemini fallback")
            try:
                direct_response = await process_direct_gemini_query(query)
                direct_response.metadata = direct_response.metadata or {}
                direct_response.metadata["fallback_reason"] = "rag_pipeline_error"
                direct_response.metadata["original_error"] = error_message
                direct_response.confidence = 0.6
                return direct_response
            except Exception as fallback_error:
                logger.error(f"Direct Gemini fallback failed: {str(fallback_error)}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"I encountered an issue while searching the curriculum. Please try rephrasing your question or try again later. Error: {error_message}"
                )
    except Exception as e:
        logger.error(f"Unexpected error in RAG query: {str(e)}", exc_info=True)
        import traceback
        logger.error(traceback.format_exc())
        
        # Try fallback for any unexpected error
        try:
            logger.info(f"Attempting direct Gemini fallback for unexpected error")
            direct_response = await process_direct_gemini_query(query)
            direct_response.metadata = direct_response.metadata or {}
            direct_response.metadata["fallback_reason"] = "unexpected_error"
            direct_response.confidence = 0.6
            return direct_response
        except Exception as fallback_error:
            logger.error(f"Fallback failed: {str(fallback_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="I apologize, but I encountered an error while processing your question. Please try rephrasing your question or try again later."
            )


# Embedding endpoint removed - now handled internally by Google RAG service


# Similarity search endpoint removed - now handled internally by Google RAG service


# Vector DB stats endpoint removed - Google RAG service handles this internally


@router.post("/initialize", response_model=BaseResponse)
async def initialize_rag_services():
    """
    Initialize Google RAG services
    
    Returns:
        Success response
    """
    try:
        # Initialize Google RAG service
        await rag_service.initialize()
        
        return BaseResponse(
            success=True,
            message="Google RAG service initialized successfully"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize Google RAG service: {str(e)}"
        )


@router.post("/evaluate")
async def evaluate_answer(request: dict):
    """
    Evaluate a user's answer against reference content using AI
    
    Args:
        request: Dictionary with question, user_answer, reference_content, and subject
        
    Returns:
        Evaluation result with score, feedback, strengths, and improvements
    """
    try:
        from app.config import settings
        import google.generativeai as genai
        
        question = request.get("question", "")
        user_answer = request.get("user_answer", "")
        reference_content = request.get("reference_content", "")
        subject = request.get("subject", "mathematics")
        
        if not question or not user_answer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required fields: question, user_answer"
            )
        
        # Check if API key is available
        if not settings.gemini_api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Gemini API key not configured"
            )
        
        # Initialize Gemini with model fallback
        genai.configure(api_key=settings.gemini_api_key)
        
        # Try models in order of preference - use comprehensive model list
        model = None
        
        # Get comprehensive model list from settings
        fast_chain = getattr(settings, 'gemini_models_fast_chain', 'gemini-2.5-flash,gemini-2.5-flash-lite,gemini-2.0-flash,gemini-2.0-flash-lite,gemini-1.5-flash')
        quality_chain = getattr(settings, 'gemini_models_quality_chain', 'gemini-3.0-pro,gemini-2.5-pro,gemini-1.5-pro')
        
        fast_models = [m.strip() for m in fast_chain.split(',') if m.strip()]
        quality_models = [m.strip() for m in quality_chain.split(',') if m.strip()]
        
        model_names = [
            getattr(settings, 'gemini_model_fast', 'gemini-2.5-flash'),
            getattr(settings, 'gemini_model_quality', 'gemini-3.0-pro'),
        ] + fast_models + quality_models + [
            'gemini-3-pro-preview',  # Legacy preview model
            'gemini-1.5-pro',  # Legacy model
            'gemini-pro'  # Oldest fallback
        ]
        # Remove duplicates while preserving order
        seen = set()
        model_names = [x for x in model_names if not (x in seen or seen.add(x))]
        
        for model_name in model_names:
            try:
                model = genai.GenerativeModel(model_name)
                logger.info(f"Using Gemini model for evaluation: {model_name}")
                break
            except Exception as e:
                logger.debug(f"Failed to create {model_name}: {str(e)}")
                continue
        
        if model is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No available Gemini model found"
            )
        
        # Create evaluation prompt
        evaluation_prompt = f"""You are an expert tutor evaluating a student's answer. Provide detailed feedback.

Reference Content:
{reference_content}

Question: {question}

Student's Answer: {user_answer}

Please evaluate the student's answer and provide:
1. A score (0-100) based on accuracy, completeness, and understanding
2. Overall feedback (2-3 sentences)
3. List of strengths (3-5 points)
4. List of areas for improvement (3-5 points)
5. Detailed analysis (2-3 paragraphs)

Format your response as JSON with the following structure:
{{
    "score": <number 0-100>,
    "feedback": "<overall feedback text>",
    "strengths": ["<strength 1>", "<strength 2>", ...],
    "improvements": ["<improvement 1>", "<improvement 2>", ...],
    "detailedAnalysis": "<detailed analysis text>"
}}

Be constructive and specific in your feedback. Focus on helping the student improve."""

        # Generate evaluation
        try:
            response = model.generate_content(evaluation_prompt)
            
            # Handle response safely
            if not response:
                raise Exception("Empty response from Gemini")
            elif hasattr(response, 'text') and response.text:
                response_text = response.text.strip()
            elif hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    response_text = candidate.content.parts[0].text if candidate.content.parts else ""
                else:
                    raise Exception("Could not extract text from response candidates")
            else:
                raise Exception("Unexpected response format")
        except Exception as gen_error:
            logger.error(f"Error generating evaluation: {str(gen_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate evaluation: {str(gen_error)}"
            )
        
        # Parse response
        if not response_text:
            raise Exception("Empty response text from Gemini")
        
        # Try to extract JSON from response
        import json
        import re
        
        # Try to find JSON in the response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
            except json.JSONDecodeError:
                # Fallback: create structured response from text
                result = {
                    "score": 75,
                    "feedback": response_text[:200] + "..." if len(response_text) > 200 else response_text,
                    "strengths": ["Answer shows understanding of the topic"],
                    "improvements": ["Could provide more detail", "Could include examples"],
                    "detailedAnalysis": response_text
                }
        else:
            # Fallback response
            result = {
                "score": 75,
                "feedback": response_text[:200] + "..." if len(response_text) > 200 else response_text,
                "strengths": ["Answer demonstrates knowledge"],
                "improvements": ["Could be more detailed"],
                "detailedAnalysis": response_text
            }
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate answer: {str(e)}"
        )
