"""Quiz service for managing quiz sessions"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from decimal import Decimal
import json

from supabase import create_client, Client
from app.config import settings
from app.models.quiz import (
    QuizSession,
    QuizSessionCreate,
    QuizAnswerSubmission,
    QuizResult
)
from app.models.base import Subject
from app.utils.exceptions import APIException


class QuizService:
    """Service for managing quiz sessions"""
    
    def __init__(self):
        """Initialize quiz service with Supabase client"""
        self.supabase: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
    
    async def start_quiz_session(
        self,
        quiz_create: QuizSessionCreate
    ) -> QuizSession:
        """
        Start a new quiz session
        
        Args:
            quiz_create: Quiz session creation data
            
        Returns:
            QuizSession object
        """
        try:
            # Calculate total marks from quiz data if not provided
            total_marks = quiz_create.total_marks
            if not total_marks and quiz_create.quiz_data:
                questions = quiz_create.quiz_data.get("questions", [])
                total_marks = sum(q.get("marks", 1) for q in questions)
            
            # Calculate duration if not provided (estimate 1 minute per question)
            duration_minutes = quiz_create.duration_minutes
            if not duration_minutes and quiz_create.quiz_data:
                questions = quiz_create.quiz_data.get("questions", [])
                duration_minutes = len(questions) * 2  # 2 minutes per question
            
            # Create quiz session
            session_data = {
                "user_id": quiz_create.user_id,
                "microplan_id": quiz_create.microplan_id,
                "quiz_data": quiz_create.quiz_data,
                "subject": quiz_create.subject.value,
                "duration_minutes": duration_minutes,
                "total_marks": total_marks,
                "answers": {},
                "is_completed": False,
                "metadata": {}
            }
            
            result = self.supabase.table("quiz_sessions").insert(session_data).execute()
            
            if not result.data or len(result.data) == 0:
                raise APIException(
                    status_code=500,
                    detail="Failed to create quiz session"
                )
            
            return QuizSession(**result.data[0])
            
        except Exception as e:
            if isinstance(e, APIException):
                raise
            raise APIException(
                status_code=500,
                detail=f"Failed to start quiz session: {str(e)}"
            )
    
    async def save_answer(
        self,
        session_id: str,
        user_id: str,
        answer_submission: QuizAnswerSubmission
    ) -> QuizSession:
        """
        Save an answer during a quiz session
        
        Args:
            session_id: Quiz session ID
            user_id: User ID (for verification)
            answer_submission: Answer submission data
            
        Returns:
            Updated QuizSession object
        """
        try:
            # Get current session
            session_result = self.supabase.table("quiz_sessions").select("*").eq(
                "id", session_id
            ).eq("user_id", user_id).execute()
            
            if not session_result.data or len(session_result.data) == 0:
                raise APIException(
                    status_code=404,
                    detail="Quiz session not found"
                )
            
            session_data = session_result.data[0]
            
            # Check if session is still active
            if session_data.get("is_completed"):
                raise APIException(
                    status_code=400,
                    detail="Quiz session is already completed"
                )
            
            # Check if time limit exceeded
            start_time = datetime.fromisoformat(
                session_data["start_time"].replace("Z", "+00:00")
            )
            duration_minutes = session_data.get("duration_minutes", 0)
            
            if duration_minutes > 0:
                elapsed_minutes = (datetime.utcnow() - start_time.replace(tzinfo=None)).total_seconds() / 60
                if elapsed_minutes > duration_minutes:
                    # Auto-submit if time exceeded
                    return await self.submit_quiz(session_id, user_id)
            
            # Update answers
            answers = session_data.get("answers", {})
            if isinstance(answers, str):
                answers = json.loads(answers)
            
            answers[answer_submission.question_id] = {
                "answer": answer_submission.answer,
                "timestamp": answer_submission.timestamp.isoformat()
            }
            
            # Save updated answers
            update_data = {"answers": answers}
            
            result = self.supabase.table("quiz_sessions").update(update_data).eq(
                "id", session_id
            ).eq("user_id", user_id).execute()
            
            if not result.data or len(result.data) == 0:
                raise APIException(
                    status_code=500,
                    detail="Failed to save answer"
                )
            
            return QuizSession(**result.data[0])
            
        except Exception as e:
            if isinstance(e, APIException):
                raise
            raise APIException(
                status_code=500,
                detail=f"Failed to save answer: {str(e)}"
            )
    
    async def submit_quiz(
        self,
        session_id: str,
        user_id: str
    ) -> QuizResult:
        """
        Submit a quiz session and calculate results
        
        Args:
            session_id: Quiz session ID
            user_id: User ID (for verification)
            
        Returns:
            QuizResult object with scores and feedback
        """
        try:
            # Get session
            session_result = self.supabase.table("quiz_sessions").select("*").eq(
                "id", session_id
            ).eq("user_id", user_id).execute()
            
            if not session_result.data or len(session_result.data) == 0:
                raise APIException(
                    status_code=404,
                    detail="Quiz session not found"
                )
            
            session_data = session_result.data[0]
            
            # Check if already completed
            if session_data.get("is_completed"):
                # Return existing result
                return await self._get_quiz_result(session_data)
            
            # Get quiz data and answers
            quiz_data = session_data.get("quiz_data", {})
            questions = quiz_data.get("questions", [])
            answers = session_data.get("answers", {})
            if isinstance(answers, str):
                answers = json.loads(answers)
            
            # Calculate score
            correct_answers = 0
            total_questions = len(questions)
            question_results = []
            
            for question in questions:
                question_id = question.get("id") or str(questions.index(question))
                user_answer = answers.get(question_id, {}).get("answer", "").strip().lower()
                correct_answer = question.get("correct_answer", "").strip().lower()
                
                # Simple answer matching (can be enhanced with AI evaluation)
                is_correct = user_answer == correct_answer
                
                if is_correct:
                    correct_answers += 1
                
                question_results.append({
                    "question_id": question_id,
                    "question": question.get("question", ""),
                    "user_answer": answers.get(question_id, {}).get("answer", ""),
                    "correct_answer": correct_answer,
                    "is_correct": is_correct,
                    "marks": question.get("marks", 1) if is_correct else 0
                })
            
            # Calculate total score
            total_marks = session_data.get("total_marks", total_questions)
            score = Decimal(str(correct_answers * (total_marks / total_questions)))
            percentage = (score / Decimal(str(total_marks))) * 100 if total_marks > 0 else Decimal("0")
            
            # Calculate time taken
            start_time = datetime.fromisoformat(
                session_data["start_time"].replace("Z", "+00:00")
            )
            end_time = datetime.utcnow()
            time_taken_minutes = int((end_time - start_time.replace(tzinfo=None)).total_seconds() / 60)
            
            # Update session as completed
            update_data = {
                "is_completed": True,
                "end_time": end_time.isoformat(),
                "score": float(score),
                "answers": answers
            }
            
            self.supabase.table("quiz_sessions").update(update_data).eq(
                "id", session_id
            ).eq("user_id", user_id).execute()
            
            # Create result
            result = QuizResult(
                session_id=session_id,
                score=score,
                total_marks=total_marks,
                percentage=percentage,
                time_taken_minutes=time_taken_minutes,
                correct_answers=correct_answers,
                total_questions=total_questions,
                question_results=question_results
            )
            
            return result
            
        except Exception as e:
            if isinstance(e, APIException):
                raise
            raise APIException(
                status_code=500,
                detail=f"Failed to submit quiz: {str(e)}"
            )
    
    async def _get_quiz_result(self, session_data: dict) -> QuizResult:
        """Helper to get quiz result from session data"""
        quiz_data = session_data.get("quiz_data", {})
        questions = quiz_data.get("questions", [])
        answers = session_data.get("answers", {})
        if isinstance(answers, str):
            answers = json.loads(answers)
        
        correct_answers = 0
        question_results = []
        
        for question in questions:
            question_id = question.get("id") or str(questions.index(question))
            user_answer = answers.get(question_id, {}).get("answer", "").strip().lower()
            correct_answer = question.get("correct_answer", "").strip().lower()
            
            is_correct = user_answer == correct_answer
            if is_correct:
                correct_answers += 1
            
            question_results.append({
                "question_id": question_id,
                "question": question.get("question", ""),
                "user_answer": answers.get(question_id, {}).get("answer", ""),
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "marks": question.get("marks", 1) if is_correct else 0
            })
        
        total_marks = session_data.get("total_marks", len(questions))
        score = Decimal(str(session_data.get("score", 0)))
        percentage = (score / Decimal(str(total_marks))) * 100 if total_marks > 0 else Decimal("0")
        
        start_time = datetime.fromisoformat(
            session_data["start_time"].replace("Z", "+00:00")
        )
        end_time_str = session_data.get("end_time")
        if end_time_str:
            end_time = datetime.fromisoformat(end_time_str.replace("Z", "+00:00"))
            time_taken_minutes = int((end_time - start_time.replace(tzinfo=None)).total_seconds() / 60)
        else:
            time_taken_minutes = 0
        
        return QuizResult(
            session_id=session_data["id"],
            score=score,
            total_marks=total_marks,
            percentage=percentage,
            time_taken_minutes=time_taken_minutes,
            correct_answers=correct_answers,
            total_questions=len(questions),
            question_results=question_results
        )
    
    async def get_session(self, session_id: str, user_id: str) -> QuizSession:
        """Get a quiz session by ID"""
        try:
            result = self.supabase.table("quiz_sessions").select("*").eq(
                "id", session_id
            ).eq("user_id", user_id).execute()
            
            if not result.data or len(result.data) == 0:
                raise APIException(
                    status_code=404,
                    detail="Quiz session not found"
                )
            
            return QuizSession(**result.data[0])
            
        except Exception as e:
            if isinstance(e, APIException):
                raise
            raise APIException(
                status_code=500,
                detail=f"Failed to get quiz session: {str(e)}"
            )






