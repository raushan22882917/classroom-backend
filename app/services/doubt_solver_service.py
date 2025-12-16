"""Doubt solver service for processing student queries"""

import re
import io
from typing import Optional, Dict, List
from datetime import datetime
import google.generativeai as genai
from google.cloud import vision
from google.cloud import speech
from PIL import Image, ImageEnhance
from supabase import create_client, Client

from app.config import settings
from app.models.doubt import (
    DoubtQuery,
    DoubtResponse,
    DoubtType,
    WolframStep,
    Source
)
from app.models.base import Subject
from app.models.content import ContentItem, PYQ, HOTSQuestion
from app.services.rag_service import rag_service
from app.services.wolfram_service import wolfram_service
from app.models.rag import RAGQuery
from app.utils.exceptions import APIException


class DoubtSolverService:
    """Service for processing doubt queries with multi-modal input"""
    
    def __init__(self):
        """Initialize doubt solver service"""
        self.rag_service = rag_service
        self._gemini_initialized = False
        self._supabase_client: Optional[Client] = None
        self._vision_client: Optional[vision.ImageAnnotatorClient] = None
        self._speech_client: Optional[speech.SpeechClient] = None
        self.wolfram_service = wolfram_service
        
        # Classification prompt template
        self.classification_prompt = """Analyze the following student question and classify it:

Question: {question}

Provide a JSON response with:
1. subject: one of [mathematics, physics, chemistry, biology]
2. concept: the main concept or topic being asked about
3. is_numerical: true if it involves numerical calculations, false otherwise

Response format:
{{
  "subject": "subject_name",
  "concept": "concept_description",
  "is_numerical": true/false
}}

Only respond with the JSON, no additional text."""
    
    def _initialize_gemini(self):
        """Initialize Gemini API"""
        if not self._gemini_initialized:
            genai.configure(api_key=settings.gemini_api_key)
            self._gemini_initialized = True
    
    def _get_supabase_client(self) -> Client:
        """Get or create Supabase client"""
        if self._supabase_client is None:
            self._supabase_client = create_client(
                settings.supabase_url,
                settings.supabase_service_key
            )
        return self._supabase_client
    
    async def classify_query(self, text: str) -> Dict:
        """
        Classify the query to identify subject and concept
        
        Args:
            text: Query text
            
        Returns:
            Dictionary with subject, concept, and is_numerical
        """
        try:
            self._initialize_gemini()
            
            prompt = self.classification_prompt.format(question=text)
            # Use faster model for better response times
            model_name = getattr(settings, 'gemini_model_fast', 'gemini-2.5-flash')
            try:
                model = genai.GenerativeModel(model_name)
            except:
                model_name = getattr(settings, 'gemini_model_standard', 'gemini-1.5-flash')
                try:
                    model = genai.GenerativeModel(model_name)
                except:
                    model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            
            # Parse JSON response
            import json
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            classification = json.loads(response_text)
            
            # Validate subject
            subject_str = classification.get("subject", "").lower()
            valid_subjects = ["mathematics", "physics", "chemistry", "biology"]
            if subject_str not in valid_subjects:
                # Default to mathematics if unclear
                subject_str = "mathematics"
            
            return {
                "subject": subject_str,
                "concept": classification.get("concept", "general"),
                "is_numerical": classification.get("is_numerical", False)
            }
            
        except Exception as e:
            # Fallback classification
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Classification error: {e}, using fallback")
            try:
                is_numerical = self._detect_numerical_simple(text)
            except:
                is_numerical = False
            return {
                "subject": "mathematics",
                "concept": "general",
                "is_numerical": is_numerical
            }
    
    def _detect_numerical_simple(self, text: str) -> bool:
        """
        Simple numerical detection using regex patterns
        
        Args:
            text: Query text
            
        Returns:
            True if numerical, False otherwise
        """
        # Patterns for numerical questions
        patterns = [
            r'\d+\s*[\+\-\*/\^]\s*\d+',  # Basic arithmetic
            r'solve|calculate|compute|find\s+the\s+value',  # Calculation keywords
            r'equation|integral|derivative|limit',  # Math operations
            r'=\s*\?|\?\s*=',  # Equation with unknown
            r'\d+\s*x\s*\d+',  # Multiplication notation
        ]
        
        text_lower = text.lower()
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return True
        return False
    
    async def get_related_pyq(
        self,
        subject: str,
        concept: str,
        limit: int = 1
    ) -> Optional[PYQ]:
        """
        Get related PYQ from database
        
        Args:
            subject: Subject name
            concept: Concept/topic
            limit: Number of PYQs to fetch
            
        Returns:
            PYQ object or None
        """
        try:
            supabase = self._get_supabase_client()
            
            # Query PYQs for the subject
            response = supabase.table("pyqs")\
                .select("*")\
                .eq("subject", subject)\
                .limit(limit)\
                .execute()
            
            if response.data and len(response.data) > 0:
                pyq_data = response.data[0]
                return PYQ(
                    id=pyq_data["id"],
                    subject=Subject(pyq_data["subject"]),
                    year=pyq_data["year"],
                    question=pyq_data["question"],
                    solution=pyq_data["solution"],
                    marks=pyq_data["marks"],
                    topic_ids=pyq_data.get("topic_ids", []),
                    difficulty=pyq_data.get("difficulty"),
                    metadata=pyq_data.get("metadata", {}),
                    created_at=datetime.fromisoformat(pyq_data["created_at"].replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat(pyq_data["updated_at"].replace("Z", "+00:00"))
                )
            
            return None
            
        except Exception as e:
            print(f"Error fetching PYQ: {e}")
            return None
    
    async def get_related_hots(
        self,
        subject: str,
        concept: str,
        limit: int = 1
    ) -> Optional[HOTSQuestion]:
        """
        Get related HOTS question from database
        
        Args:
            subject: Subject name
            concept: Concept/topic
            limit: Number of HOTS questions to fetch
            
        Returns:
            HOTSQuestion object or None
        """
        try:
            supabase = self._get_supabase_client()
            
            # Query HOTS questions for the subject
            response = supabase.table("hots_questions")\
                .select("*")\
                .eq("subject", subject)\
                .limit(limit)\
                .execute()
            
            if response.data and len(response.data) > 0:
                hots_data = response.data[0]
                return HOTSQuestion(
                    id=hots_data["id"],
                    subject=Subject(hots_data["subject"]),
                    topic_id=hots_data.get("topic_id"),
                    question=hots_data["question"],
                    solution=hots_data["solution"],
                    difficulty=hots_data.get("difficulty", "hard"),
                    question_type=hots_data.get("question_type", "case_based"),
                    metadata=hots_data.get("metadata", {}),
                    created_at=datetime.fromisoformat(hots_data["created_at"].replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat(hots_data["updated_at"].replace("Z", "+00:00"))
                )
            
            return None
            
        except Exception as e:
            print(f"Error fetching HOTS question: {e}")
            return None
    
    async def process_text_doubt(
        self,
        user_id: str,
        text: str,
        subject: Optional[Subject] = None
    ) -> DoubtResponse:
        """
        Process a text-based doubt query
        
        Args:
            user_id: User ID
            text: Question text
            subject: Optional subject hint
            
        Returns:
            DoubtResponse with answer and related content
        """
        try:
            # Step 1: Classify the query
            classification = await self.classify_query(text)
            classified_subject = classification["subject"]
            concept = classification["concept"]
            is_numerical = classification["is_numerical"]
            
            # Use provided subject if available, otherwise use classified
            if subject:
                query_subject = subject.value if hasattr(subject, 'value') else str(subject)
            else:
                query_subject = classified_subject
            
            # Ensure query_subject is a valid Subject enum value
            try:
                subject_enum = Subject(query_subject)
            except (ValueError, TypeError):
                # Fallback to mathematics if invalid
                subject_enum = Subject.MATHEMATICS
                query_subject = "mathematics"
            
            # Step 2: Use RAG service to get NCERT content and explanation
            try:
                rag_query = RAGQuery(
                    query=text,
                    subject=subject_enum,
                    top_k=5,
                    confidence_threshold=0.5
                )
                
                rag_response = await self.rag_service.query(rag_query)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"RAG service error: {str(e)}")
                # Create a minimal RAG response to continue
                from app.models.rag import RAGResponse, RAGContext
                rag_response = RAGResponse(
                    query=text,
                    generated_text=f"I'll help you understand: {text}",
                    contexts=[],
                    sources=[],
                    confidence=0.5,
                    metadata={}
                )
            
            # Step 3: Get related PYQ
            try:
                related_pyq = await self.get_related_pyq(
                    subject=query_subject,
                    concept=concept
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to get related PYQ: {str(e)}")
                related_pyq = None
            
            # Step 4: Get related HOTS question
            try:
                related_hots = await self.get_related_hots(
                    subject=query_subject,
                    concept=concept
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to get related HOTS: {str(e)}")
                related_hots = None
            
            # Step 5: Check if numerical and get Wolfram solution
            wolfram_steps = None
            if is_numerical:
                try:
                    wolfram_result = await self.wolfram_service.solve_math_problem(
                        query=text,
                        include_steps=True
                    )
                    
                    if wolfram_result:
                        wolfram_steps = self.wolfram_service.format_steps_for_response(wolfram_result)
                except Exception as e:
                    print(f"Wolfram integration error: {e}")
                    # Continue without Wolfram if it fails
            
            # Step 6: Extract NCERT summary from RAG response
            ncert_summary = rag_response.generated_text
            
            # Step 7: Extract solved example from contexts if available
            solved_example = None
            if rag_response.contexts and len(rag_response.contexts) > 0:
                # Use the first context as an example
                first_context = rag_response.contexts[0]
                try:
                    example_subject = Subject(query_subject)
                except (ValueError, TypeError):
                    example_subject = Subject.mathematics
                
                solved_example = ContentItem(
                    id=first_context.content_id,
                    type="ncert",
                    subject=example_subject,
                    chapter=first_context.metadata.get("chapter", ""),
                    topic_id=first_context.metadata.get("topic_id"),
                    difficulty="medium",
                    title=f"Example from {first_context.metadata.get('chapter', 'NCERT')}",
                    content_text=first_context.text,
                    metadata=first_context.metadata,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            
            # Step 8: Build sources list
            sources = [
                Source(
                    content_id=src["id"],
                    type=src["type"],
                    title=f"{src['type'].upper()} - {src.get('chapter', 'N/A')}",
                    confidence=src["similarity"],
                    excerpt=None
                )
                for src in rag_response.sources
            ]
            
            # Step 9: Create doubt query record
            try:
                classified_subject_enum = Subject(classified_subject)
            except (ValueError, TypeError):
                classified_subject_enum = Subject.mathematics
            
            doubt_id = await self._store_doubt(
                user_id=user_id,
                doubt_type=DoubtType.TEXT,
                content=text,
                subject=subject,
                classified_subject=classified_subject_enum,
                classified_concept=concept,
                confidence=rag_response.confidence
            )
            
            # Step 10: Build and return response
            return DoubtResponse(
                query_id=doubt_id,
                ncert_summary=ncert_summary,
                solved_example=solved_example,
                related_pyq=related_pyq,
                hots_question=related_hots,
                wolfram_steps=wolfram_steps,
                sources=sources,
                confidence=rag_response.confidence,
                metadata={
                    "classified_subject": classified_subject,
                    "concept": concept,
                    "is_numerical": is_numerical,
                    "wolfram_used": wolfram_steps is not None,
                    "rag_chunks_retrieved": len(rag_response.contexts)
                }
            )
            
        except APIException:
            raise
        except Exception as e:
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to process text doubt: {str(e)}")
            logger.error(traceback.format_exc())
            raise APIException(
                status_code=500,
                detail=f"Failed to process text doubt: {str(e)}"
            )
    
    def _get_vision_client(self) -> vision.ImageAnnotatorClient:
        """Get or create Vision API client"""
        if self._vision_client is None:
            self._vision_client = vision.ImageAnnotatorClient()
        return self._vision_client
    
    def _get_speech_client(self) -> speech.SpeechClient:
        """Get or create Speech API client"""
        if self._speech_client is None:
            self._speech_client = speech.SpeechClient()
        return self._speech_client
    
    async def preprocess_image(self, image_bytes: bytes) -> bytes:
        """
        Preprocess image for better OCR results
        
        Args:
            image_bytes: Raw image bytes
            
        Returns:
            Preprocessed image bytes
        """
        try:
            # Open image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Auto-rotate based on EXIF data
            try:
                from PIL import ImageOps
                image = ImageOps.exif_transpose(image)
            except Exception:
                pass
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.3)
            
            # Convert back to bytes
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=95)
            return output.getvalue()
            
        except Exception as e:
            print(f"Image preprocessing error: {e}")
            # Return original if preprocessing fails
            return image_bytes
    
    async def extract_text_from_image(self, image_bytes: bytes) -> str:
        """
        Extract text from image using Google Cloud Vision API
        
        Args:
            image_bytes: Image file bytes
            
        Returns:
            Extracted text
        """
        try:
            # Preprocess image
            processed_image = await self.preprocess_image(image_bytes)
            
            # Get Vision client
            client = self._get_vision_client()
            
            # Create image object
            image = vision.Image(content=processed_image)
            
            # Perform text detection
            response = client.text_detection(image=image)
            
            if response.error.message:
                raise Exception(f"Vision API error: {response.error.message}")
            
            # Extract text
            texts = response.text_annotations
            if texts:
                # First annotation contains the full text
                extracted_text = texts[0].description
                return extracted_text.strip()
            else:
                raise Exception("No text found in image")
                
        except Exception as e:
            raise APIException(
                status_code=500,
                detail=f"Failed to extract text from image: {str(e)}"
            )
    
    async def extract_text_from_voice(self, audio_bytes: bytes, audio_format: str = "wav") -> str:
        """
        Extract text from voice recording using Google Cloud Speech-to-Text API
        
        Args:
            audio_bytes: Audio file bytes
            audio_format: Audio format (wav, mp3, etc.)
            
        Returns:
            Transcribed text
        """
        try:
            # Get Speech client
            client = self._get_speech_client()
            
            # Determine encoding based on format
            encoding_map = {
                "wav": speech.RecognitionConfig.AudioEncoding.LINEAR16,
                "mp3": speech.RecognitionConfig.AudioEncoding.MP3,
                "flac": speech.RecognitionConfig.AudioEncoding.FLAC,
                "ogg": speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
                "webm": speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            }
            
            encoding = encoding_map.get(audio_format.lower(), speech.RecognitionConfig.AudioEncoding.LINEAR16)
            
            # Configure recognition
            config = speech.RecognitionConfig(
                encoding=encoding,
                sample_rate_hertz=16000,
                language_code="en-IN",  # Indian English
                alternative_language_codes=["hi-IN"],  # Hindi as alternative
                enable_automatic_punctuation=True,
                model="default"
            )
            
            audio = speech.RecognitionAudio(content=audio_bytes)
            
            # Perform recognition
            response = client.recognize(config=config, audio=audio)
            
            # Extract transcription
            if response.results:
                transcript = " ".join(
                    result.alternatives[0].transcript
                    for result in response.results
                )
                return transcript.strip()
            else:
                raise Exception("No speech detected in audio")
                
        except Exception as e:
            raise APIException(
                status_code=500,
                detail=f"Failed to transcribe audio: {str(e)}"
            )
    
    async def process_image_doubt(
        self,
        user_id: str,
        image_bytes: bytes,
        subject: Optional[Subject] = None
    ) -> DoubtResponse:
        """
        Process an image-based doubt query
        
        Args:
            user_id: User ID
            image_bytes: Image file bytes
            subject: Optional subject hint
            
        Returns:
            DoubtResponse with answer and related content
        """
        try:
            # Step 1: Extract text from image using OCR
            extracted_text = await self.extract_text_from_image(image_bytes)
            
            if not extracted_text or len(extracted_text.strip()) < 5:
                raise APIException(
                    status_code=400,
                    detail="Could not extract meaningful text from image. Please ensure the image is clear and contains text."
                )
            
            # Step 2: Process as text doubt
            response = await self.process_text_doubt(
                user_id=user_id,
                text=extracted_text,
                subject=subject
            )
            
            # Update metadata to indicate image source
            response.metadata["input_type"] = "image"
            response.metadata["extracted_text"] = extracted_text
            
            return response
            
        except APIException:
            raise
        except Exception as e:
            raise APIException(
                status_code=500,
                detail=f"Failed to process image doubt: {str(e)}"
            )
    
    async def process_voice_doubt(
        self,
        user_id: str,
        audio_bytes: bytes,
        audio_format: str = "wav",
        subject: Optional[Subject] = None
    ) -> DoubtResponse:
        """
        Process a voice-based doubt query
        
        Args:
            user_id: User ID
            audio_bytes: Audio file bytes
            audio_format: Audio format (wav, mp3, etc.)
            subject: Optional subject hint
            
        Returns:
            DoubtResponse with answer and related content
        """
        try:
            # Step 1: Transcribe audio to text
            transcribed_text = await self.extract_text_from_voice(audio_bytes, audio_format)
            
            if not transcribed_text or len(transcribed_text.strip()) < 5:
                raise APIException(
                    status_code=400,
                    detail="Could not transcribe meaningful text from audio. Please speak clearly and try again."
                )
            
            # Step 2: Process as text doubt
            response = await self.process_text_doubt(
                user_id=user_id,
                text=transcribed_text,
                subject=subject
            )
            
            # Update metadata to indicate voice source
            response.metadata["input_type"] = "voice"
            response.metadata["transcribed_text"] = transcribed_text
            
            return response
            
        except APIException:
            raise
        except Exception as e:
            raise APIException(
                status_code=500,
                detail=f"Failed to process voice doubt: {str(e)}"
            )
    
    async def _store_doubt(
        self,
        user_id: str,
        doubt_type: DoubtType,
        content: str,
        subject: Optional[Subject],
        classified_subject: Subject,
        classified_concept: str,
        confidence: float
    ) -> str:
        """
        Store doubt query in database
        
        Args:
            user_id: User ID
            doubt_type: Type of doubt (text, image, voice)
            content: Doubt content/text
            subject: User-provided subject
            classified_subject: AI-classified subject
            classified_concept: AI-classified concept
            confidence: Confidence score
            
        Returns:
            Doubt ID
        """
        try:
            supabase = self._get_supabase_client()
            
            doubt_data = {
                "user_id": user_id,
                "type": doubt_type.value,
                "content": content,
                "subject": subject.value if subject else None,
                "classified_subject": classified_subject.value,
                "classified_concept": classified_concept,
                "confidence": float(confidence),
                "metadata": {},
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            response = supabase.table("doubts").insert(doubt_data).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]["id"]
            else:
                raise Exception("Failed to insert doubt record")
                
        except Exception as e:
            print(f"Error storing doubt: {e}")
            # Return a temporary ID if storage fails
            import uuid
            return str(uuid.uuid4())
    
    async def get_doubt_history(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict]:
        """
        Get doubt history for a user
        
        Args:
            user_id: User ID
            limit: Number of records to fetch
            offset: Offset for pagination
            
        Returns:
            List of doubt records
        """
        try:
            supabase = self._get_supabase_client()
            
            response = supabase.table("doubts")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .offset(offset)\
                .execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            print(f"Error fetching doubt history: {e}")
            return []


# Global instance
doubt_solver_service = DoubtSolverService()
