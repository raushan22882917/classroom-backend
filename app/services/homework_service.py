"""Homework assistant service with graduated hints"""

import json
import uuid
from typing import Optional, Dict, List
from datetime import datetime
from google import genai
from supabase import create_client, Client

from app.config import settings
from app.models.base import Subject
from app.models.doubt import (
    HomeworkSession,
    HomeworkAttempt,
    HintResponse,
    HomeworkStartRequest,
    HomeworkStartResponse,
    HomeworkAttemptRequest,
    HomeworkAttemptResponse
)
from app.services.wolfram_service import wolfram_service
from app.utils.exceptions import APIException


class HomeworkService:
    """Service for homework assistance with graduated hints"""
    
    def __init__(self):
        """Initialize homework service"""
        self._supabase_client: Optional[Client] = None
        self.wolfram_service = wolfram_service
        # Initialize Gemini client with API key
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = "gemini-3-pro-preview"  # Use the same model as teacher service
        
        # Hint generation prompts
        self.hint_prompts = {
            1: """Generate a basic hint for this homework problem. The hint should:
- Point the student in the right direction
- NOT reveal the solution
- Help them understand what concept to apply
- Be encouraging and supportive

Question: {question}
Subject: {subject}

Provide only the hint text, no additional formatting.""",
            
            2: """Generate a detailed hint for this homework problem. The hint should:
- Provide more specific guidance than the basic hint
- Show the approach or method to use
- Still NOT reveal the complete solution
- Include relevant formulas or concepts if applicable

Question: {question}
Subject: {subject}
Previous hint: {previous_hint}

Provide only the hint text, no additional formatting.""",
            
            3: """Generate the complete solution for this homework problem. Include:
- Step-by-step solution
- Clear explanations for each step
- Final answer
- Any relevant formulas or concepts used

Question: {question}
Subject: {subject}

Provide the complete solution."""
        }
        
        # Answer evaluation prompt
        self.evaluation_prompt = """Evaluate if the student's answer is correct for this question.

Question: {question}
Subject: {subject}
Student's Answer: {student_answer}
{correct_answer_hint}

Provide a JSON response with:
1. is_correct: true if the answer is correct, false otherwise
2. feedback: Constructive feedback for the student (2-3 sentences)
3. explanation: Brief explanation of why the answer is correct or incorrect

For numerical answers, consider answers within 1% tolerance as correct.
For text answers, check if the key concepts are present even if wording differs.

Response format:
{{
  "is_correct": true/false,
  "feedback": "feedback text",
  "explanation": "explanation text"
}}

Only respond with the JSON, no additional text."""
    
    
    def _get_supabase_client(self) -> Client:
        """Get or create Supabase client"""
        if self._supabase_client is None:
            self._supabase_client = create_client(
                settings.supabase_url,
                settings.supabase_service_key
            )
        return self._supabase_client
    
    async def start_homework_session(
        self,
        request: HomeworkStartRequest
    ) -> HomeworkStartResponse:
        """
        Start a new homework session
        
        Args:
            request: Homework start request with question and user details
            
        Returns:
            HomeworkStartResponse with session ID
        """
        try:
            supabase = self._get_supabase_client()
            
            # Generate question ID if not provided
            question_id = request.question_id or str(uuid.uuid4())
            
            # Create session data
            session_data = {
                "user_id": request.user_id,
                "question_id": question_id,
                "question": request.question,
                "subject": request.subject.value,
                "hints_revealed": 0,
                "attempts": [],
                "is_complete": False,
                "solution_revealed": False,
                "correct_answer": request.correct_answer,
                "metadata": request.metadata or {},
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Insert into database
            response = supabase.table("homework_sessions").insert(session_data).execute()
            
            if not response.data or len(response.data) == 0:
                raise Exception("Failed to create homework session")
            
            session_id = response.data[0]["id"]
            
            return HomeworkStartResponse(
                session_id=session_id,
                question=request.question,
                subject=request.subject,
                message="Homework session started. Try solving the problem first, then request hints if needed."
            )
            
        except Exception as e:
            raise APIException(
                code="START_SESSION_ERROR",
                message=f"Failed to start homework session: {str(e)}",
                status_code=500
            )
    
    async def get_hint(
        self,
        session_id: str,
        hint_level: Optional[int] = None
    ) -> HintResponse:
        """
        Get a hint for the homework problem
        
        Args:
            session_id: Homework session ID
            hint_level: Specific hint level (1-3), or None for next level
            
        Returns:
            HintResponse with hint text
        """
        try:
            supabase = self._get_supabase_client()
            
            # Get session
            response = supabase.table("homework_sessions")\
                .select("*")\
                .eq("id", session_id)\
                .execute()
            
            if not response.data or len(response.data) == 0:
                raise APIException(
                    code="SESSION_NOT_FOUND",
                    message="Homework session not found",
                    status_code=404
                )
            
            session = response.data[0]
            
            # Validate required fields
            if not session.get("question"):
                raise APIException(
                    code="MISSING_QUESTION",
                    message="Homework session is missing question",
                    status_code=400
                )
            
            if not session.get("subject"):
                raise APIException(
                    code="MISSING_SUBJECT",
                    message="Homework session is missing subject",
                    status_code=400
                )
            
            # Check if session is complete
            if session.get("is_complete", False):
                raise APIException(
                    code="SESSION_COMPLETE",
                    message="Homework session is already complete",
                    status_code=400
                )
            
            # Determine hint level
            current_hints_revealed = session.get("hints_revealed", 0) or 0
            if hint_level is None:
                # Get next hint level
                next_level = current_hints_revealed + 1
            else:
                # Use requested level
                next_level = hint_level
            
            # Validate hint level
            if next_level < 1 or next_level > 3:
                raise APIException(
                    code="INVALID_HINT_LEVEL",
                    message="Hint level must be between 1 and 3",
                    status_code=400
                )
            
            # Check if hint already revealed
            if next_level <= current_hints_revealed:
                raise APIException(
                    code="HINT_ALREADY_REVEALED",
                    message=f"Hint level {next_level} has already been revealed",
                    status_code=400
                )
            
            # Generate hint
            hint_text = await self._generate_hint(
                question=session["question"],
                subject=session["subject"],
                hint_level=next_level,
                previous_hint=None  # Could fetch from metadata if stored
            )
            
            # Store hint in metadata
            metadata = session.get("metadata", {})
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    metadata = {}
            
            # Store all revealed hints in metadata
            if "hints" not in metadata:
                metadata["hints"] = {}
            metadata["hints"][str(next_level)] = hint_text
            
            # Update session
            update_data = {
                "hints_revealed": next_level,
                "solution_revealed": next_level == 3,
                "metadata": metadata,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            supabase.table("homework_sessions")\
                .update(update_data)\
                .eq("id", session_id)\
                .execute()
            
            return HintResponse(
                session_id=session_id,
                hint_level=next_level,
                hint_text=hint_text,
                is_final_hint=next_level == 3
            )
            
        except APIException:
            raise
        except Exception as e:
            error_msg = f"Failed to get hint: {str(e)}"
            print(f"[HomeworkService] ERROR in get_hint: {error_msg}")
            import traceback
            traceback.print_exc()
            raise APIException(
                code="GET_HINT_ERROR",
                message=error_msg,
                status_code=500
            )
    
    async def _generate_hint(
        self,
        question: str,
        subject: str,
        hint_level: int,
        previous_hint: Optional[str] = None
    ) -> str:
        """
        Generate hint using Gemini
        
        Args:
            question: Homework question
            subject: Subject name
            hint_level: Hint level (1-3)
            previous_hint: Previous hint text if available
            
        Returns:
            Generated hint text
        """
        try:
            # Check if Gemini API key is configured
            if not settings.gemini_api_key or not settings.gemini_api_key.strip():
                raise Exception("Gemini API key is not configured. Please set GEMINI_API_KEY in .env file")
            
            # Get prompt template
            prompt_template = self.hint_prompts.get(hint_level)
            if not prompt_template:
                raise Exception(f"Invalid hint level: {hint_level}")
            
            # Format prompt
            prompt = prompt_template.format(
                question=question,
                subject=subject,
                previous_hint=previous_hint or "N/A"
            )
            
            # Generate hint using the new Google GenAI API
            print(f"[HomeworkService] Generating hint level {hint_level} for subject {subject}")
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt
                )
                
                # Extract text from response
                hint_text = response.text.strip() if hasattr(response, 'text') and response.text else ""
                
                if not hint_text:
                    raise Exception("Generated hint is empty")
                
                print(f"[HomeworkService] Hint generated successfully (length: {len(hint_text)})")
                
                return hint_text
            except Exception as api_error:
                error_msg = f"Gemini API error: {str(api_error)}"
                print(f"[HomeworkService] {error_msg}")
                raise Exception(error_msg)
            
        except Exception as e:
            error_msg = f"Failed to generate hint: {str(e)}"
            print(f"[HomeworkService] ERROR: {error_msg}")
            import traceback
            traceback.print_exc()
            raise Exception(error_msg)
    
    async def submit_attempt(
        self,
        request: HomeworkAttemptRequest
    ) -> HomeworkAttemptResponse:
        """
        Submit an answer attempt for homework
        
        Args:
            request: Homework attempt request with session ID and answer
            
        Returns:
            HomeworkAttemptResponse with evaluation feedback
        """
        try:
            supabase = self._get_supabase_client()
            
            # Get session
            response = supabase.table("homework_sessions")\
                .select("*")\
                .eq("id", request.session_id)\
                .execute()
            
            if not response.data or len(response.data) == 0:
                raise APIException(
                    code="SESSION_NOT_FOUND",
                    message="Homework session not found",
                    status_code=404
                )
            
            session = response.data[0]
            
            # Check if session is complete
            if session["is_complete"]:
                raise APIException(
                    code="SESSION_COMPLETE",
                    message="Homework session is already complete",
                    status_code=400
                )
            
            # Get current attempts
            attempts = session.get("attempts", [])
            attempts_count = len(attempts)
            
            # Evaluate answer
            evaluation = await self._evaluate_answer(
                question=session["question"],
                subject=session["subject"],
                student_answer=request.answer,
                correct_answer=session.get("correct_answer")
            )
            
            is_correct = evaluation["is_correct"]
            feedback = evaluation["feedback"]
            
            # Create attempt record
            attempt = {
                "answer": request.answer,
                "timestamp": datetime.utcnow().isoformat(),
                "is_correct": is_correct,
                "feedback": feedback
            }
            
            attempts.append(attempt)
            attempts_count = len(attempts)
            
            # Check if should reveal solution (3 attempts or correct answer)
            solution_revealed = session["solution_revealed"] or attempts_count >= 3 or is_correct
            is_complete = is_correct or attempts_count >= 3
            
            # Get solution if revealing
            solution = None
            if solution_revealed and not session["solution_revealed"]:
                solution = await self._generate_hint(
                    question=session["question"],
                    subject=session["subject"],
                    hint_level=3,
                    previous_hint=None
                )
            
            # Update session
            update_data = {
                "attempts": attempts,
                "is_complete": is_complete,
                "solution_revealed": solution_revealed,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            supabase.table("homework_sessions")\
                .update(update_data)\
                .eq("id", request.session_id)\
                .execute()
            
            return HomeworkAttemptResponse(
                session_id=request.session_id,
                is_correct=is_correct,
                feedback=feedback,
                attempts_count=attempts_count,
                solution_revealed=solution_revealed,
                solution=solution
            )
            
        except APIException:
            raise
        except Exception as e:
            raise APIException(
                code="SUBMIT_ATTEMPT_ERROR",
                message=f"Failed to submit attempt: {str(e)}",
                status_code=500
            )
    
    async def _evaluate_answer(
        self,
        question: str,
        subject: str,
        student_answer: str,
        correct_answer: Optional[str] = None
    ) -> Dict:
        """
        Evaluate student's answer
        
        Args:
            question: Homework question
            subject: Subject name
            student_answer: Student's submitted answer
            correct_answer: Optional correct answer for verification
            
        Returns:
            Dictionary with is_correct, feedback, and explanation
        """
        try:
            # Check if numerical question and use Wolfram for verification
            is_numerical = await self._is_numerical_question(question)
            
            if is_numerical and correct_answer:
                # Try Wolfram verification for numerical answers
                try:
                    wolfram_result = await self.wolfram_service.verify_answer(
                        question=question,
                        student_answer=student_answer,
                        expected_answer=correct_answer
                    )
                    
                    if wolfram_result:
                        return {
                            "is_correct": wolfram_result.get("is_correct", False),
                            "feedback": wolfram_result.get("feedback", "Answer evaluated using Wolfram verification."),
                            "explanation": wolfram_result.get("explanation", "")
                        }
                except Exception as e:
                    print(f"Wolfram verification failed: {e}")
                    # Fall through to Gemini evaluation
            
            # Use Gemini for evaluation
            # Build correct answer hint
            correct_answer_hint = ""
            if correct_answer:
                correct_answer_hint = f"Correct Answer (for reference): {correct_answer}"
            
            # Format prompt
            prompt = self.evaluation_prompt.format(
                question=question,
                subject=subject,
                student_answer=student_answer,
                correct_answer_hint=correct_answer_hint
            )
            
            # Generate evaluation using the new Google GenAI API
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            # Parse JSON response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            evaluation = json.loads(response_text)
            
            return {
                "is_correct": evaluation.get("is_correct", False),
                "feedback": evaluation.get("feedback", "Answer evaluated."),
                "explanation": evaluation.get("explanation", "")
            }
            
        except Exception as e:
            print(f"Evaluation error: {e}")
            # Fallback evaluation
            return {
                "is_correct": False,
                "feedback": "Unable to evaluate answer automatically. Please review the solution.",
                "explanation": str(e)
            }
    
    async def _is_numerical_question(self, question: str) -> bool:
        """
        Check if question is numerical
        
        Args:
            question: Question text
            
        Returns:
            True if numerical, False otherwise
        """
        import re
        
        # Patterns for numerical questions
        patterns = [
            r'\d+\s*[\+\-\*/\^]\s*\d+',
            r'solve|calculate|compute|find\s+the\s+value',
            r'equation|integral|derivative|limit',
            r'=\s*\?|\?\s*=',
        ]
        
        question_lower = question.lower()
        for pattern in patterns:
            if re.search(pattern, question_lower):
                return True
        return False
    
    async def get_session(self, session_id: str) -> HomeworkSession:
        """
        Get homework session by ID
        
        Args:
            session_id: Session ID
            
        Returns:
            HomeworkSession object
        """
        try:
            supabase = self._get_supabase_client()
            
            response = supabase.table("homework_sessions")\
                .select("*")\
                .eq("id", session_id)\
                .execute()
            
            if not response.data or len(response.data) == 0:
                raise APIException(
                    code="SESSION_NOT_FOUND",
                    message="Homework session not found",
                    status_code=404
                )
            
            session_data = response.data[0]
            
            return HomeworkSession(
                id=session_data["id"],
                user_id=session_data["user_id"],
                question_id=session_data["question_id"],
                question=session_data["question"],
                subject=session_data.get("subject", ""),
                hints_revealed=session_data.get("hints_revealed", 0),
                attempts=session_data.get("attempts", []),
                is_complete=session_data.get("is_complete", False),
                solution_revealed=session_data.get("solution_revealed", False),
                correct_answer=session_data.get("correct_answer"),
                metadata=session_data.get("metadata", {}),
                created_at=datetime.fromisoformat(session_data["created_at"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(session_data["updated_at"].replace("Z", "+00:00"))
            )
            
        except APIException:
            raise
        except Exception as e:
            raise APIException(
                code="GET_SESSION_ERROR",
                message=f"Failed to get session: {str(e)}",
                status_code=500
            )
    
    async def get_user_sessions(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[HomeworkSession]:
        """
        Get homework sessions for a user
        
        Args:
            user_id: User ID
            limit: Number of records to fetch
            offset: Offset for pagination
            
        Returns:
            List of HomeworkSession objects
        """
        try:
            supabase = self._get_supabase_client()
            
            # Log the query for debugging
            print(f"[HomeworkService] Querying homework_sessions for user_id: {user_id}")
            
            # Try to get a count first to see if there's any data
            count_response = supabase.table("homework_sessions")\
                .select("id", count="exact")\
                .eq("user_id", user_id)\
                .execute()
            
            print(f"[HomeworkService] Total sessions for user_id {user_id}: {count_response.count if hasattr(count_response, 'count') else 'unknown'}")
            
            response = supabase.table("homework_sessions")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .offset(offset)\
                .execute()
            
            print(f"[HomeworkService] Query returned {len(response.data) if response.data else 0} sessions")
            if response.data and len(response.data) > 0:
                print(f"[HomeworkService] First session user_id: {response.data[0].get('user_id')}")
                print(f"[HomeworkService] First session question: {response.data[0].get('question', '')[:50]}...")
            else:
                # Try to see if there's ANY data in the table
                all_response = supabase.table("homework_sessions")\
                    .select("user_id")\
                    .limit(5)\
                    .execute()
                if all_response.data:
                    print(f"[HomeworkService] Found {len(all_response.data)} total sessions in table")
                    print(f"[HomeworkService] Sample user_ids in table: {[r.get('user_id') for r in all_response.data[:3]]}")
                else:
                    print(f"[HomeworkService] No sessions found in table at all")
            
            sessions = []
            for session_data in response.data:
                sessions.append(HomeworkSession(
                    id=session_data["id"],
                    user_id=session_data["user_id"],
                    question_id=session_data["question_id"],
                    question=session_data["question"],
                    subject=session_data.get("subject", ""),
                    hints_revealed=session_data.get("hints_revealed", 0),
                    attempts=session_data.get("attempts", []),
                    is_complete=session_data.get("is_complete", False),
                    solution_revealed=session_data.get("solution_revealed", False),
                    correct_answer=session_data.get("correct_answer"),
                    metadata=session_data.get("metadata", {}),
                    created_at=datetime.fromisoformat(session_data["created_at"].replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat(session_data["updated_at"].replace("Z", "+00:00"))
                ))
            
            return sessions
            
        except Exception as e:
            print(f"[HomeworkService] Error getting user sessions: {str(e)}")
            print(f"[HomeworkService] Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            raise APIException(
                code="GET_USER_SESSIONS_ERROR",
                message=f"Failed to get user sessions: {str(e)}",
                status_code=500
            )
    
    async def get_all_sessions(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[HomeworkSession]:
        """
        Get all homework sessions (no user filter)
        
        Args:
            limit: Number of records to fetch
            offset: Offset for pagination
            
        Returns:
            List of HomeworkSession objects
        """
        try:
            supabase = self._get_supabase_client()
            
            print(f"[HomeworkService] Querying ALL homework_sessions (limit: {limit}, offset: {offset})")
            
            response = supabase.table("homework_sessions")\
                .select("*")\
                .order("created_at", desc=True)\
                .limit(limit)\
                .offset(offset)\
                .execute()
            
            print(f"[HomeworkService] Query returned {len(response.data) if response.data else 0} sessions")
            
            sessions = []
            for session_data in response.data:
                sessions.append(HomeworkSession(
                    id=session_data["id"],
                    user_id=session_data["user_id"],
                    question_id=session_data["question_id"],
                    question=session_data["question"],
                    subject=session_data.get("subject", ""),
                    hints_revealed=session_data.get("hints_revealed", 0),
                    attempts=session_data.get("attempts", []),
                    is_complete=session_data.get("is_complete", False),
                    solution_revealed=session_data.get("solution_revealed", False),
                    correct_answer=session_data.get("correct_answer"),
                    metadata=session_data.get("metadata", {}),
                    created_at=datetime.fromisoformat(session_data["created_at"].replace("Z", "+00:00")),
                    updated_at=datetime.fromisoformat(session_data["updated_at"].replace("Z", "+00:00"))
                ))
            
            return sessions
            
        except Exception as e:
            print(f"[HomeworkService] Error getting all sessions: {str(e)}")
            import traceback
            traceback.print_exc()
            raise APIException(
                code="GET_ALL_SESSIONS_ERROR",
                message=f"Failed to get all sessions: {str(e)}",
                status_code=500
            )


# Global instance
homework_service = HomeworkService()
