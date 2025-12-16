"""Exam service for managing exam sets and test sessions"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from decimal import Decimal
import json
import google.generativeai as genai

from supabase import create_client, Client
from app.config import settings
from app.models.exam import (
    ExamSet,
    ExamSetCreate,
    ExamQuestion,
    TestSession,
    TestSessionCreate,
    TestSessionUpdate,
    AnswerSubmission,
    TestResult,
    PerformanceTrend
)
from app.models.base import Subject
from app.utils.exceptions import APIException

# Configure Gemini
genai.configure(api_key=settings.gemini_api_key)


class ExamService:
    """Service for managing exams and test sessions"""
    
    def __init__(self):
        """Initialize exam service with Supabase client"""
        self.supabase: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
    
    async def get_exam_sets(
        self,
        subject: Optional[Subject] = None,
        year: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[ExamSet]:
        """
        Get available exam sets with optional filtering
        
        Args:
            subject: Filter by subject
            year: Filter by year
            limit: Maximum number of results
            offset: Pagination offset
            
        Returns:
            List of ExamSet objects
        """
        try:
            # Query pyqs table to build exam sets
            query = self.supabase.table("pyqs").select("*")
            
            if subject:
                query = query.eq("subject", subject.value)
            
            if year:
                query = query.eq("year", year)
            
            query = query.order("year", desc=True).order("marks", desc=True)
            
            result = query.execute()
            
            if not result.data:
                return []
            
            # Group questions by subject and year to create exam sets
            exam_sets_dict: Dict[tuple, List[Dict]] = {}
            
            for pyq in result.data:
                key = (pyq["subject"], pyq["year"])
                if key not in exam_sets_dict:
                    exam_sets_dict[key] = []
                exam_sets_dict[key].append(pyq)
            
            # Build ExamSet objects
            exam_sets = []
            for (subj, yr), questions in exam_sets_dict.items():
                # Calculate total marks and duration
                total_marks = sum(q.get("marks", 0) for q in questions)
                # Estimate 2 minutes per mark
                duration_minutes = total_marks * 2
                
                # Convert questions to ExamQuestion format
                exam_questions = []
                for q in questions:
                    exam_questions.append(ExamQuestion(
                        id=q["id"],
                        question=q["question"],
                        marks=q.get("marks", 0),
                        question_type="short_answer",  # Default type
                        correct_answer=q.get("solution"),
                        metadata=q.get("metadata", {})
                    ))
                
                exam_set = ExamSet(
                    id=f"{subj}_{yr}",
                    subject=Subject(subj),
                    year=yr,
                    duration_minutes=duration_minutes,
                    total_marks=total_marks,
                    questions=exam_questions,
                    metadata={"question_count": len(exam_questions)}
                )
                
                exam_sets.append(exam_set)
            
            # Sort by year (most recent first)
            exam_sets.sort(key=lambda x: x.year, reverse=True)
            
            # Apply pagination
            return exam_sets[offset:offset + limit]
            
        except Exception as e:
            raise APIException(
                code="FETCH_EXAM_SETS_ERROR",
                message=f"Failed to fetch exam sets: {str(e)}",
                status_code=500
            )
    
    async def get_exam_set_by_id(self, exam_set_id: str) -> Optional[ExamSet]:
        """
        Get a specific exam set by ID
        
        Args:
            exam_set_id: Exam set ID (format: subject_year)
            
        Returns:
            ExamSet object or None
        """
        try:
            # Parse exam_set_id (format: subject_year)
            parts = exam_set_id.split("_")
            if len(parts) < 2:
                return None
            
            subject_str = "_".join(parts[:-1])
            year = int(parts[-1])
            
            # Get all exam sets and find the matching one
            exam_sets = await self.get_exam_sets(
                subject=Subject(subject_str),
                year=year
            )
            
            if exam_sets:
                return exam_sets[0]
            
            return None
            
        except Exception as e:
            print(f"Error fetching exam set: {str(e)}")
            return None
    
    async def create_exam_set(self, exam_set_create: ExamSetCreate) -> ExamSet:
        """
        Create a new exam set (admin or teacher)
        
        Args:
            exam_set_create: Exam set creation data
            
        Returns:
            Created ExamSet object
        """
        try:
            # Insert questions as PYQs
            question_ids = []
            
            for question_data in exam_set_create.questions:
                pyq_data = {
                    "subject": exam_set_create.subject.value,
                    "year": exam_set_create.year,
                    "question": question_data.get("question", ""),
                    "solution": question_data.get("solution", ""),
                    "marks": question_data.get("marks", 0),
                    "difficulty": question_data.get("difficulty", "medium"),
                    "metadata": question_data.get("metadata", {})
                }
                
                result = self.supabase.table("pyqs").insert(pyq_data).execute()
                
                if result.data and len(result.data) > 0:
                    question_ids.append(result.data[0]["id"])
            
            # Fetch the created exam set
            exam_set_id = f"{exam_set_create.subject.value}_{exam_set_create.year}"
            exam_set = await self.get_exam_set_by_id(exam_set_id)
            
            if exam_set:
                return exam_set
            
            raise Exception("Failed to create exam set")
            
        except Exception as e:
            raise APIException(
                code="CREATE_EXAM_SET_ERROR",
                message=f"Failed to create exam set: {str(e)}",
                status_code=500
            )
    
    async def start_test_session(
        self,
        session_create: TestSessionCreate
    ) -> TestSession:
        """
        Start a new test session
        
        Args:
            session_create: Test session creation data
            
        Returns:
            Created TestSession object
        """
        try:
            # Validate required fields first
            if not session_create.user_id:
                raise APIException(
                    code="MISSING_USER_ID",
                    message="User ID is required",
                    status_code=400
                )
            
            # Get exam set details if exam_set_id is provided
            duration_minutes = session_create.duration_minutes
            total_marks = session_create.total_marks
            
            if session_create.exam_set_id:
                try:
                    exam_set = await self.get_exam_set_by_id(session_create.exam_set_id)
                    if exam_set:
                        # Use exam set values (they should always be present)
                        duration_minutes = exam_set.duration_minutes
                        total_marks = exam_set.total_marks
                    else:
                        # If exam_set_id is provided but exam set not found, that's an error
                        raise APIException(
                            code="EXAM_SET_NOT_FOUND",
                            message=f"Exam set with ID '{session_create.exam_set_id}' not found. Please check the exam set ID format (should be 'subject_year', e.g., 'mathematics_2023').",
                            status_code=404
                        )
                except APIException:
                    raise
                except Exception as e:
                    # If there's an error parsing the exam_set_id, provide helpful error
                    raise APIException(
                        code="INVALID_EXAM_SET_ID",
                        message=f"Invalid exam set ID format: '{session_create.exam_set_id}'. Expected format: 'subject_year' (e.g., 'mathematics_2023'). Error: {str(e)}",
                        status_code=400
                    )
            
            # Validate that we have required values
            # If exam_set_id was provided, we should have gotten values from it
            # If not, user must provide them directly
            if not duration_minutes:
                if session_create.exam_set_id:
                    raise APIException(
                        code="MISSING_DURATION",
                        message="Failed to get duration from exam set. Please try again or provide duration_minutes directly.",
                        status_code=500
                    )
                else:
                    raise APIException(
                        code="MISSING_DURATION",
                        message="Duration minutes is required. Please provide duration_minutes or a valid exam_set_id.",
                        status_code=400
                    )
            
            if not total_marks:
                if session_create.exam_set_id:
                    raise APIException(
                        code="MISSING_TOTAL_MARKS",
                        message="Failed to get total marks from exam set. Please try again or provide total_marks directly.",
                        status_code=500
                    )
                else:
                    raise APIException(
                        code="MISSING_TOTAL_MARKS",
                        message="Total marks is required. Please provide total_marks or a valid exam_set_id.",
                        status_code=400
                    )
            
            # Check if user has already attempted this exam set
            if session_create.exam_set_id:
                # Check for existing sessions (both completed and incomplete) with the same exam_set_id
                existing_sessions = self.supabase.table("test_sessions").select("*").eq(
                    "user_id", session_create.user_id
                ).execute()
                
                # Check if any session has the same exam_set_id in metadata
                for session in existing_sessions.data or []:
                    session_metadata = session.get("metadata", {})
                    if isinstance(session_metadata, str):
                        import json
                        try:
                            session_metadata = json.loads(session_metadata)
                        except:
                            session_metadata = {}
                    
                    if session_metadata.get("exam_set_id") == session_create.exam_set_id:
                        if session.get("is_completed", False):
                            raise APIException(
                                code="EXAM_ALREADY_COMPLETED",
                                message="You have already completed this exam. You cannot attempt it again.",
                                status_code=403
                            )
                        else:
                            # There's an incomplete session - user should resume it instead
                            raise APIException(
                                code="EXAM_IN_PROGRESS",
                                message="You have an incomplete exam session. Please complete or submit your current attempt before starting a new one.",
                                status_code=409
                            )
            
            # Ensure subject is properly formatted
            # Handle both Subject enum and string
            if hasattr(session_create.subject, 'value'):
                subject_value = session_create.subject.value
            elif isinstance(session_create.subject, str):
                # Validate it's a valid subject
                valid_subjects = ['mathematics', 'physics', 'chemistry', 'biology']
                if session_create.subject.lower() not in valid_subjects:
                    raise APIException(
                        code="INVALID_SUBJECT",
                        message=f"Invalid subject: '{session_create.subject}'. Must be one of: {', '.join(valid_subjects)}",
                        status_code=400
                    )
                subject_value = session_create.subject.lower()
            else:
                subject_value = str(session_create.subject)
            
            # Create test session
            # Note: start_time has a default value in the database, so we don't need to set it
            # Note: exam_set_id in test_sessions expects a UUID, but exam sets use format "subject_year"
            # So we store the exam_set_id in metadata instead
            session_data = {
                "user_id": session_create.user_id,
                "subject": subject_value,
                "duration_minutes": duration_minutes,
                "total_marks": total_marks,
                "answers": {},
                "is_completed": False,
                "metadata": {}
            }
            
            # Store exam_set_id in metadata since it's not a UUID
            # The exam_set_id column expects UUID, but exam sets use format "subject_year"
            if session_create.exam_set_id:
                session_data["metadata"]["exam_set_id"] = session_create.exam_set_id
            
            result = self.supabase.table("test_sessions").insert(session_data).execute()
            
            if not result.data or len(result.data) == 0:
                raise APIException(
                    code="SESSION_CREATION_FAILED",
                    message="Failed to create test session: No data returned from database",
                    status_code=500
                )
            
            return TestSession(**result.data[0])
            
        except APIException:
            raise
        except Exception as e:
            import traceback
            error_detail = str(e)
            traceback.print_exc()
            print(f"Error in start_test_session: {error_detail}")
            raise APIException(
                code="SESSION_CREATION_ERROR",
                message=f"Failed to start test session: {error_detail}",
                status_code=500
            )
    
    async def save_answer(
        self,
        session_id: str,
        user_id: str,
        answer_submission: AnswerSubmission
    ) -> TestSession:
        """
        Save an answer during a test session
        
        Args:
            session_id: Test session ID
            user_id: User ID (for verification)
            answer_submission: Answer submission data
            
        Returns:
            Updated TestSession object
        """
        try:
            # Get current session
            session_result = self.supabase.table("test_sessions").select("*").eq(
                "id", session_id
            ).eq("user_id", user_id).execute()
            
            if not session_result.data or len(session_result.data) == 0:
                raise APIException(
                    code="SESSION_NOT_FOUND",
                    message="Test session not found",
                    status_code=404
                )
            
            session_data = session_result.data[0]
            
            # Check if session is still active
            if session_data.get("is_completed"):
                raise APIException(
                    code="SESSION_COMPLETED",
                    message="Test session is already completed",
                    status_code=400
                )
            
            # Check if time limit exceeded
            duration_minutes = session_data.get("duration_minutes", 0)
            
            if duration_minutes > 0 and session_data.get("start_time"):
                try:
                    start_time_str = session_data["start_time"]
                    # Handle different datetime formats
                    if isinstance(start_time_str, str):
                        # Remove timezone info if present and parse
                        if start_time_str.endswith("Z"):
                            start_time_str = start_time_str.replace("Z", "+00:00")
                        start_time = datetime.fromisoformat(start_time_str)
                    elif isinstance(start_time_str, datetime):
                        start_time = start_time_str
                    else:
                        # If it's already a datetime object or other format, skip time check
                        start_time = None
                    
                    if start_time:
                        # Convert to UTC if timezone-aware, otherwise assume UTC
                        if start_time.tzinfo is not None:
                            start_time_utc = start_time.astimezone(timezone.utc).replace(tzinfo=None)
                        else:
                            start_time_utc = start_time
                        
                        elapsed_minutes = (datetime.utcnow() - start_time_utc).total_seconds() / 60
                        if elapsed_minutes > duration_minutes:
                            # Auto-submit if time exceeded
                            return await self.submit_test(session_id, user_id)
                except (ValueError, TypeError, AttributeError) as e:
                    # If datetime parsing fails, log but continue (don't block answer saving)
                    print(f"Warning: Failed to parse start_time for time check: {str(e)}")
                    # Continue without time check
            
            # Update answers
            answers = session_data.get("answers", {})
            if isinstance(answers, str):
                answers = json.loads(answers)
            elif answers is None:
                answers = {}
            
            # Handle timestamp - could be datetime object or string
            timestamp_value = answer_submission.timestamp
            if isinstance(timestamp_value, datetime):
                timestamp_str = timestamp_value.isoformat()
            elif isinstance(timestamp_value, str):
                timestamp_str = timestamp_value
            else:
                # Fallback to current time if timestamp is invalid
                timestamp_str = datetime.utcnow().isoformat()
            
            answers[answer_submission.question_id] = {
                "answer": answer_submission.answer,
                "timestamp": timestamp_str
            }
            
            # Save updated answers
            update_data = {"answers": answers}
            
            result = self.supabase.table("test_sessions").update(update_data).eq(
                "id", session_id
            ).eq("user_id", user_id).execute()
            
            if result.data and len(result.data) > 0:
                return TestSession(**result.data[0])
            
            raise Exception("Failed to save answer")
            
        except APIException:
            raise
        except Exception as e:
            import traceback
            error_detail = str(e)
            traceback.print_exc()
            print(f"Error in save_answer: {error_detail}")
            print(f"Session ID: {session_id}, User ID: {user_id}")
            print(f"Answer submission: question_id={answer_submission.question_id}, answer_length={len(answer_submission.answer) if answer_submission.answer else 0}")
            raise APIException(
                code="SAVE_ANSWER_ERROR",
                message=f"Failed to save answer: {error_detail}",
                status_code=500
            )
    
    async def submit_test(
        self,
        session_id: str,
        user_id: str
    ) -> TestSession:
        """
        Submit a test session and calculate score
        
        Args:
            session_id: Test session ID
            user_id: User ID (for verification)
            
        Returns:
            Completed TestSession object with score
        """
        try:
            # Get current session
            session_result = self.supabase.table("test_sessions").select("*").eq(
                "id", session_id
            ).eq("user_id", user_id).execute()
            
            if not session_result.data or len(session_result.data) == 0:
                raise APIException(
                    code="SESSION_NOT_FOUND",
                    message="Test session not found",
                    status_code=404
                )
            
            session_data = session_result.data[0]
            
            # Check if already completed
            if session_data.get("is_completed"):
                return TestSession(**session_data)
            
            # Get exam set to evaluate answers
            # Check metadata first (new format), then exam_set_id (old format)
            exam_set_id = session_data.get("metadata", {}).get("exam_set_id") or session_data.get("exam_set_id")
            if not exam_set_id:
                raise APIException(
                    code="NO_EXAM_SET",
                    message="Cannot evaluate test without exam set",
                    status_code=400
                )
            
            exam_set = await self.get_exam_set_by_id(exam_set_id)
            if not exam_set:
                raise APIException(
                    code="EXAM_SET_NOT_FOUND",
                    message="Exam set not found",
                    status_code=404
                )
            
            # Evaluate answers
            answers = session_data.get("answers", {})
            if isinstance(answers, str):
                answers = json.loads(answers)
            
            total_score = Decimal("0.0")
            
            for question in exam_set.questions:
                if question.id in answers:
                    student_answer = answers[question.id].get("answer", "")
                    
                    # Evaluate answer using Gemini for subjective questions
                    score = await self._evaluate_answer(
                        question=question.question,
                        student_answer=student_answer,
                        model_answer=question.correct_answer or "",
                        max_marks=question.marks
                    )
                    
                    total_score += Decimal(str(score))
            
            # Update session with score and completion
            update_data = {
                "score": float(total_score),
                "is_completed": True,
                "end_time": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table("test_sessions").update(update_data).eq(
                "id", session_id
            ).eq("user_id", user_id).execute()
            
            if result.data and len(result.data) > 0:
                return TestSession(**result.data[0])
            
            raise Exception("Failed to submit test")
            
        except APIException:
            raise
        except Exception as e:
            raise APIException(
                code="SUBMIT_TEST_ERROR",
                message=f"Failed to submit test: {str(e)}",
                status_code=500
            )
    
    async def _evaluate_answer(
        self,
        question: str,
        student_answer: str,
        model_answer: str,
        max_marks: int
    ) -> float:
        """
        Evaluate a student's answer using Gemini
        
        Args:
            question: The question text
            student_answer: Student's answer
            model_answer: Model/correct answer
            max_marks: Maximum marks for the question
            
        Returns:
            Score awarded (0 to max_marks)
        """
        try:
            # Use Gemini to evaluate the answer - use faster model
            model_name = getattr(settings, 'gemini_model_fast', 'gemini-2.5-flash')
            try:
                model = genai.GenerativeModel(model_name)
            except:
                model_name = getattr(settings, 'gemini_model_standard', 'gemini-1.5-flash')
                try:
                    model = genai.GenerativeModel(model_name)
                except:
                    model = genai.GenerativeModel("gemini-2.5-flash")
            
            prompt = f"""You are an expert examiner evaluating a student's answer.

Question: {question}

Model Answer: {model_answer}

Student's Answer: {student_answer}

Maximum Marks: {max_marks}

Evaluate the student's answer and provide a score out of {max_marks} marks.
Consider:
- Correctness of concepts
- Completeness of answer
- Clarity of explanation
- Relevant examples or steps

Respond with ONLY a JSON object in this format:
{{
    "score": <number between 0 and {max_marks}>,
    "feedback": "<brief feedback on the answer>"
}}"""
            
            response = model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extract JSON from response
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response_text)
            score = float(result.get("score", 0))
            
            # Ensure score is within bounds
            score = max(0, min(score, max_marks))
            
            return score
            
        except Exception as e:
            print(f"Error evaluating answer with Gemini: {str(e)}")
            # Fallback: simple keyword matching
            if not student_answer.strip():
                return 0.0
            
            # Award partial marks if answer is not empty
            return max_marks * 0.5
    
    async def get_test_results(
        self,
        session_id: str,
        user_id: str
    ) -> TestResult:
        """
        Get detailed test results with model answers and marking rubric
        
        Args:
            session_id: Test session ID
            user_id: User ID (for verification)
            
        Returns:
            TestResult object with detailed breakdown
        """
        try:
            # Get session
            session_result = self.supabase.table("test_sessions").select("*").eq(
                "id", session_id
            ).eq("user_id", user_id).execute()
            
            if not session_result.data or len(session_result.data) == 0:
                raise APIException(
                    code="SESSION_NOT_FOUND",
                    message="Test session not found",
                    status_code=404
                )
            
            session_data = session_result.data[0]
            
            if not session_data.get("is_completed"):
                raise APIException(
                    code="TEST_NOT_COMPLETED",
                    message="Test is not yet completed",
                    status_code=400
                )
            
            # Get exam set
            # Check metadata first (new format), then exam_set_id (old format)
            exam_set_id = session_data.get("metadata", {}).get("exam_set_id") or session_data.get("exam_set_id")
            if not exam_set_id:
                raise APIException(
                    code="NO_EXAM_SET",
                    message="No exam set associated with this session",
                    status_code=400
                )
            
            exam_set = await self.get_exam_set_by_id(exam_set_id)
            if not exam_set:
                raise APIException(
                    code="EXAM_SET_NOT_FOUND",
                    message="Exam set not found",
                    status_code=404
                )
            
            # Calculate time taken
            start_time = datetime.fromisoformat(
                session_data["start_time"].replace("Z", "+00:00")
            )
            end_time = datetime.fromisoformat(
                session_data["end_time"].replace("Z", "+00:00")
            )
            time_taken_minutes = int((end_time - start_time).total_seconds() / 60)
            
            # Build question results
            answers = session_data.get("answers", {})
            if isinstance(answers, str):
                answers = json.loads(answers)
            
            question_results = []
            model_answers = []
            correct_count = 0
            
            for question in exam_set.questions:
                student_answer = ""
                if question.id in answers:
                    student_answer = answers[question.id].get("answer", "")
                
                # Re-evaluate to get detailed feedback
                score = await self._evaluate_answer(
                    question=question.question,
                    student_answer=student_answer,
                    model_answer=question.correct_answer or "",
                    max_marks=question.marks
                )
                
                is_correct = score >= (question.marks * 0.7)  # 70% threshold
                if is_correct:
                    correct_count += 1
                
                question_results.append({
                    "question_id": question.id,
                    "question": question.question,
                    "student_answer": student_answer,
                    "marks_awarded": score,
                    "max_marks": question.marks,
                    "is_correct": is_correct
                })
                
                model_answers.append({
                    "question_id": question.id,
                    "question": question.question,
                    "model_answer": question.correct_answer or "",
                    "marks": question.marks
                })
            
            # Calculate percentage
            score = Decimal(str(session_data.get("score", 0)))
            total_marks = session_data.get("total_marks", 0)
            percentage = (score / Decimal(str(total_marks)) * 100) if total_marks > 0 else Decimal("0")
            
            # Build marking rubric
            marking_rubric = {
                "total_questions": len(exam_set.questions),
                "correct_answers": correct_count,
                "partially_correct": len([q for q in question_results if 0 < q["marks_awarded"] < q["max_marks"]]),
                "incorrect": len([q for q in question_results if q["marks_awarded"] == 0]),
                "evaluation_method": "AI-powered evaluation using Gemini"
            }
            
            return TestResult(
                session_id=session_id,
                score=score,
                total_marks=total_marks,
                percentage=percentage,
                time_taken_minutes=time_taken_minutes,
                correct_answers=correct_count,
                total_questions=len(exam_set.questions),
                question_results=question_results,
                model_answers=model_answers,
                marking_rubric=marking_rubric
            )
            
        except APIException:
            raise
        except Exception as e:
            raise APIException(
                code="GET_RESULTS_ERROR",
                message=f"Failed to get test results: {str(e)}",
                status_code=500
            )
    
    async def get_test_history(
        self,
        user_id: str,
        subject: Optional[Subject] = None,
        limit: int = 20
    ) -> PerformanceTrend:
        """
        Get test history and performance trends for a user
        
        Args:
            user_id: User ID
            subject: Optional subject filter
            limit: Maximum number of sessions to retrieve
            
        Returns:
            PerformanceTrend object with historical data
        """
        try:
            # Get test sessions
            query = self.supabase.table("test_sessions").select("*").eq(
                "user_id", user_id
            ).eq("is_completed", True)
            
            if subject:
                query = query.eq("subject", subject.value)
            
            query = query.order("created_at", desc=True).limit(limit)
            
            result = query.execute()
            
            if not result.data:
                # Return empty trend
                return PerformanceTrend(
                    user_id=user_id,
                    subject=subject or Subject.MATHEMATICS,
                    test_sessions=[],
                    average_score=Decimal("0"),
                    improvement_rate=Decimal("0"),
                    strengths=[],
                    weaknesses=[]
                )
            
            # Build test session summaries
            test_sessions = []
            total_score = Decimal("0")
            total_marks = 0
            
            for session in result.data:
                score = Decimal(str(session.get("score", 0)))
                marks = session.get("total_marks", 0)
                
                percentage = (score / Decimal(str(marks)) * 100) if marks > 0 else Decimal("0")
                
                test_sessions.append({
                    "session_id": session["id"],
                    "subject": session["subject"],
                    "date": session["created_at"],
                    "score": float(score),
                    "total_marks": marks,
                    "percentage": float(percentage)
                })
                
                total_score += score
                total_marks += marks
            
            # Calculate average score
            avg_score = (total_score / Decimal(str(total_marks)) * 100) if total_marks > 0 else Decimal("0")
            
            # Calculate improvement rate (compare first half vs second half)
            improvement_rate = Decimal("0")
            if len(test_sessions) >= 4:
                mid_point = len(test_sessions) // 2
                recent_avg = sum(s["percentage"] for s in test_sessions[:mid_point]) / mid_point
                older_avg = sum(s["percentage"] for s in test_sessions[mid_point:]) / (len(test_sessions) - mid_point)
                improvement_rate = Decimal(str(recent_avg - older_avg))
            
            # Analyze strengths and weaknesses (simplified)
            strengths = []
            weaknesses = []
            
            if avg_score >= 80:
                strengths.append("Consistently high performance")
            elif avg_score >= 60:
                strengths.append("Good understanding of concepts")
            
            if improvement_rate > 10:
                strengths.append("Showing significant improvement")
            elif improvement_rate < -10:
                weaknesses.append("Performance declining - needs attention")
            
            if avg_score < 50:
                weaknesses.append("Needs more practice and concept revision")
            
            return PerformanceTrend(
                user_id=user_id,
                subject=subject or Subject(result.data[0]["subject"]),
                test_sessions=test_sessions,
                average_score=avg_score,
                improvement_rate=improvement_rate,
                strengths=strengths,
                weaknesses=weaknesses
            )
            
        except Exception as e:
            raise APIException(
                code="GET_HISTORY_ERROR",
                message=f"Failed to get test history: {str(e)}",
                status_code=500
            )


# Global service instance
exam_service = ExamService()
