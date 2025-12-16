"""HOTS (Higher Order Thinking Skills) question generation and tracking service"""

import google.generativeai as genai
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from app.config import settings
from app.models.base import Subject
from app.models.content import HOTSQuestion, HOTSQuestionCreate, DifficultyLevel
from app.models.progress import Progress, ProgressUpdate
from app.utils.exceptions import APIException
from supabase import create_client, Client

# Initialize Supabase client
supabase: Client = create_client(settings.supabase_url, settings.supabase_service_key)

# Configure Gemini
genai.configure(api_key=settings.gemini_api_key)


class HOTSService:
    """Service for HOTS question generation and tracking"""
    
    def __init__(self):
        # Use faster model for better response times - can fallback if not available
        model_name = getattr(settings, 'gemini_model_fast', 'gemini-2.5-flash')
        try:
            self.model = genai.GenerativeModel(model_name)
        except:
            # Fallback to standard if fast model not available
            model_name = getattr(settings, 'gemini_model_standard', 'gemini-1.5-flash')
            try:
                self.model = genai.GenerativeModel(model_name)
            except:
                # Final fallback to flash
                self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    async def generate_hots_questions(
        self,
        topic_id: str,
        count: int = 3
    ) -> List[HOTSQuestion]:
        """
        Generate HOTS questions for a given topic using Gemini
        
        Args:
            topic_id: Topic UUID
            count: Number of questions to generate (default 3)
            
        Returns:
            List of generated HOTS questions
        """
        try:
            # Fetch topic details
            topic_response = supabase.table("topics").select("*").eq("id", topic_id).execute()
            
            if not topic_response.data:
                raise APIException(
                    code="TOPIC_NOT_FOUND",
                    message=f"Topic with id {topic_id} not found",
                    status_code=404
                )
            
            topic = topic_response.data[0]
            subject = topic["subject"]
            chapter = topic["chapter"]
            topic_name = topic["name"]
            
            # Fetch related NCERT content for context
            content_response = supabase.table("content").select("content_text").eq(
                "topic_id", topic_id
            ).eq("type", "ncert").limit(3).execute()
            
            context = ""
            if content_response.data:
                context = "\n\n".join([item["content_text"][:500] for item in content_response.data])
            
            # Create prompt for Gemini
            prompt = self._create_generation_prompt(
                subject=subject,
                chapter=chapter,
                topic_name=topic_name,
                context=context,
                count=count
            )
            
            # Generate questions using Gemini
            response = self.model.generate_content(prompt)
            
            # Parse response and create questions
            questions = self._parse_gemini_response(
                response.text,
                subject=subject,
                topic_id=topic_id
            )
            
            # Store questions in database
            stored_questions = []
            for question_data in questions:
                question_create = HOTSQuestionCreate(**question_data)
                stored_question = await self._store_question(question_create)
                stored_questions.append(stored_question)
            
            return stored_questions
            
        except Exception as e:
            if isinstance(e, APIException):
                raise
            raise APIException(
                code="HOTS_GENERATION_FAILED",
                message=f"Failed to generate HOTS questions: {str(e)}",
                status_code=500
            )
    
    def _create_generation_prompt(
        self,
        subject: str,
        chapter: str,
        topic_name: str,
        context: str,
        count: int
    ) -> str:
        """Create prompt for Gemini to generate HOTS questions"""
        
        prompt = f"""You are an expert Class 12 {subject} teacher creating Higher Order Thinking Skills (HOTS) questions.

Topic: {topic_name}
Chapter: {chapter}
Subject: {subject}

Context from NCERT:
{context if context else "No specific context provided"}

Generate {count} HOTS questions that are:
1. Case-based or application-oriented (not just recall or simple calculation)
2. Require critical thinking, analysis, synthesis, or evaluation
3. Similar to questions that top-performing students solve
4. Aligned with CBSE Class 12 standards
5. Include real-world scenarios or novel situations

For each question, provide:
- A detailed question statement (can include a case study or scenario)
- A comprehensive solution with step-by-step reasoning
- Question type (case_based or application)

Format your response as follows for each question:

QUESTION 1:
[Question text here]

SOLUTION 1:
[Detailed solution here]

TYPE 1:
[case_based or application]

---

QUESTION 2:
[Question text here]

SOLUTION 2:
[Detailed solution here]

TYPE 2:
[case_based or application]

---

Continue for all {count} questions."""
        
        return prompt
    
    def _parse_gemini_response(
        self,
        response_text: str,
        subject: str,
        topic_id: str
    ) -> List[Dict[str, Any]]:
        """Parse Gemini response into structured question data"""
        
        questions = []
        
        # Split by question separator
        question_blocks = response_text.split("---")
        
        for block in question_blocks:
            if not block.strip():
                continue
            
            # Extract question, solution, and type
            question_text = ""
            solution_text = ""
            question_type = "case_based"
            
            lines = block.strip().split("\n")
            current_section = None
            
            for line in lines:
                line = line.strip()
                
                if line.startswith("QUESTION"):
                    current_section = "question"
                    continue
                elif line.startswith("SOLUTION"):
                    current_section = "solution"
                    continue
                elif line.startswith("TYPE"):
                    current_section = "type"
                    continue
                
                if current_section == "question" and line:
                    question_text += line + "\n"
                elif current_section == "solution" and line:
                    solution_text += line + "\n"
                elif current_section == "type" and line:
                    if "application" in line.lower():
                        question_type = "application"
                    else:
                        question_type = "case_based"
            
            if question_text and solution_text:
                questions.append({
                    "subject": subject,
                    "topic_id": topic_id,
                    "question": question_text.strip(),
                    "solution": solution_text.strip(),
                    "difficulty": DifficultyLevel.HARD,
                    "question_type": question_type,
                    "metadata": {
                        "generated_by": "gemini",
                        "generated_at": datetime.utcnow().isoformat()
                    }
                })
        
        return questions
    
    async def _store_question(self, question_create: HOTSQuestionCreate) -> HOTSQuestion:
        """Store HOTS question in database"""
        
        question_data = {
            "subject": question_create.subject,
            "topic_id": question_create.topic_id,
            "question": question_create.question,
            "solution": question_create.solution,
            "difficulty": question_create.difficulty,
            "question_type": question_create.question_type,
            "metadata": question_create.metadata
        }
        
        response = supabase.table("hots_questions").insert(question_data).execute()
        
        if not response.data:
            raise APIException(
                code="HOTS_STORAGE_FAILED",
                message="Failed to store HOTS question",
                status_code=500
            )
        
        return HOTSQuestion(**response.data[0])
    
    async def get_questions_by_topic(self, topic_id: str) -> List[HOTSQuestion]:
        """
        Fetch HOTS questions for a specific topic
        
        Args:
            topic_id: Topic UUID
            
        Returns:
            List of HOTS questions
        """
        try:
            response = supabase.table("hots_questions").select("*").eq(
                "topic_id", topic_id
            ).order("created_at", desc=True).execute()
            
            return [HOTSQuestion(**item) for item in response.data]
            
        except Exception as e:
            raise APIException(
                code="HOTS_FETCH_FAILED",
                message=f"Failed to fetch HOTS questions: {str(e)}",
                status_code=500
            )
    
    async def submit_attempt(
        self,
        user_id: str,
        question_id: str,
        answer: str,
        time_taken_minutes: int
    ) -> Dict[str, Any]:
        """
        Submit an attempt for a HOTS question and evaluate
        
        Args:
            user_id: User UUID
            question_id: HOTS question UUID
            answer: Student's answer
            time_taken_minutes: Time taken to solve
            
        Returns:
            Evaluation result with feedback and updated mastery
        """
        try:
            # Fetch question
            question_response = supabase.table("hots_questions").select("*").eq(
                "id", question_id
            ).execute()
            
            if not question_response.data:
                raise APIException(
                    code="QUESTION_NOT_FOUND",
                    message=f"HOTS question with id {question_id} not found",
                    status_code=404
                )
            
            question = question_response.data[0]
            
            # Evaluate answer using Gemini
            evaluation = await self._evaluate_answer(
                question=question["question"],
                solution=question["solution"],
                student_answer=answer
            )
            
            # Update HOTS mastery tracking
            await self._update_hots_mastery(
                user_id=user_id,
                topic_id=question["topic_id"],
                subject=question["subject"],
                is_correct=evaluation["is_correct"],
                time_taken_minutes=time_taken_minutes
            )
            
            return {
                "question_id": question_id,
                "is_correct": evaluation["is_correct"],
                "score": evaluation["score"],
                "feedback": evaluation["feedback"],
                "model_solution": question["solution"],
                "mastery_updated": True
            }
            
        except Exception as e:
            if isinstance(e, APIException):
                raise
            raise APIException(
                code="HOTS_ATTEMPT_FAILED",
                message=f"Failed to submit HOTS attempt: {str(e)}",
                status_code=500
            )
    
    async def _evaluate_answer(
        self,
        question: str,
        solution: str,
        student_answer: str
    ) -> Dict[str, Any]:
        """Evaluate student answer using Gemini"""
        
        prompt = f"""You are evaluating a student's answer to a HOTS question.

Question:
{question}

Model Solution:
{solution}

Student's Answer:
{student_answer}

Evaluate the student's answer and provide:
1. Whether the answer is correct (yes/no)
2. A score out of 100
3. Detailed feedback on what was good and what could be improved

Format your response as:
CORRECT: [yes/no]
SCORE: [0-100]
FEEDBACK: [Your detailed feedback here]"""
        
        response = self.model.generate_content(prompt)
        response_text = response.text
        
        # Parse response
        is_correct = False
        score = 0
        feedback = ""
        
        for line in response_text.split("\n"):
            line = line.strip()
            if line.startswith("CORRECT:"):
                is_correct = "yes" in line.lower()
            elif line.startswith("SCORE:"):
                try:
                    score = int(line.split(":")[1].strip())
                except:
                    score = 50 if is_correct else 0
            elif line.startswith("FEEDBACK:"):
                feedback = line.split(":", 1)[1].strip()
        
        # If feedback wasn't parsed correctly, use the whole response
        if not feedback:
            feedback = response_text
        
        return {
            "is_correct": is_correct,
            "score": score,
            "feedback": feedback
        }
    
    async def _update_hots_mastery(
        self,
        user_id: str,
        topic_id: str,
        subject: str,
        is_correct: bool,
        time_taken_minutes: int
    ) -> None:
        """Update HOTS mastery tracking in progress table"""
        
        # Fetch or create progress record
        progress_response = supabase.table("progress").select("*").eq(
            "user_id", user_id
        ).eq("topic_id", topic_id).execute()
        
        if progress_response.data:
            # Update existing progress
            progress = progress_response.data[0]
            
            # Get HOTS-specific metadata
            metadata = progress.get("metadata", {})
            hots_data = metadata.get("hots", {
                "questions_attempted": 0,
                "correct_answers": 0,
                "mastery_score": 0.0
            })
            
            # Update HOTS metrics
            hots_data["questions_attempted"] += 1
            if is_correct:
                hots_data["correct_answers"] += 1
            
            # Calculate HOTS mastery score
            hots_mastery = (hots_data["correct_answers"] / hots_data["questions_attempted"]) * 100
            hots_data["mastery_score"] = round(hots_mastery, 2)
            
            # Check for topper badge (80% mastery)
            achievements = progress.get("achievements", [])
            if hots_mastery >= 80 and not any(a.get("type") == "topper_badge" for a in achievements):
                achievements.append({
                    "type": "topper_badge",
                    "name": "Topper Badge",
                    "description": "Achieved 80% mastery on HOTS questions",
                    "earned_at": datetime.utcnow().isoformat(),
                    "topic_id": topic_id
                })
            
            metadata["hots"] = hots_data
            
            # Update progress
            supabase.table("progress").update({
                "metadata": metadata,
                "achievements": achievements,
                "total_time_minutes": progress["total_time_minutes"] + time_taken_minutes,
                "last_practiced_at": datetime.utcnow().isoformat()
            }).eq("id", progress["id"]).execute()
            
        else:
            # Create new progress record
            metadata = {
                "hots": {
                    "questions_attempted": 1,
                    "correct_answers": 1 if is_correct else 0,
                    "mastery_score": 100.0 if is_correct else 0.0
                }
            }
            
            supabase.table("progress").insert({
                "user_id": user_id,
                "topic_id": topic_id,
                "subject": subject,
                "mastery_score": 0,
                "questions_attempted": 0,
                "correct_answers": 0,
                "total_time_minutes": time_taken_minutes,
                "last_practiced_at": datetime.utcnow().isoformat(),
                "metadata": metadata
            }).execute()
    
    async def get_hots_performance(self, user_id: str) -> Dict[str, Any]:
        """
        Get HOTS performance analytics for a user
        
        Args:
            user_id: User UUID
            
        Returns:
            HOTS performance metrics
        """
        try:
            # Fetch all progress records for user
            progress_response = supabase.table("progress").select("*").eq(
                "user_id", user_id
            ).execute()
            
            if not progress_response.data:
                return {
                    "total_hots_attempted": 0,
                    "total_hots_correct": 0,
                    "overall_hots_mastery": 0.0,
                    "topics_with_topper_badge": [],
                    "subject_breakdown": {}
                }
            
            # Aggregate HOTS metrics
            total_attempted = 0
            total_correct = 0
            topics_with_badge = []
            subject_breakdown = {}
            
            for progress in progress_response.data:
                metadata = progress.get("metadata", {})
                hots_data = metadata.get("hots", {})
                
                if hots_data:
                    attempted = hots_data.get("questions_attempted", 0)
                    correct = hots_data.get("correct_answers", 0)
                    
                    total_attempted += attempted
                    total_correct += correct
                    
                    # Check for topper badge
                    achievements = progress.get("achievements", [])
                    if any(a.get("type") == "topper_badge" for a in achievements):
                        topics_with_badge.append({
                            "topic_id": progress["topic_id"],
                            "subject": progress["subject"],
                            "mastery_score": hots_data.get("mastery_score", 0)
                        })
                    
                    # Subject breakdown
                    subject = progress["subject"]
                    if subject not in subject_breakdown:
                        subject_breakdown[subject] = {
                            "attempted": 0,
                            "correct": 0,
                            "mastery": 0.0
                        }
                    
                    subject_breakdown[subject]["attempted"] += attempted
                    subject_breakdown[subject]["correct"] += correct
            
            # Calculate overall mastery
            overall_mastery = (total_correct / total_attempted * 100) if total_attempted > 0 else 0.0
            
            # Calculate subject mastery
            for subject in subject_breakdown:
                attempted = subject_breakdown[subject]["attempted"]
                correct = subject_breakdown[subject]["correct"]
                subject_breakdown[subject]["mastery"] = (correct / attempted * 100) if attempted > 0 else 0.0
            
            return {
                "total_hots_attempted": total_attempted,
                "total_hots_correct": total_correct,
                "overall_hots_mastery": round(overall_mastery, 2),
                "topics_with_topper_badge": topics_with_badge,
                "subject_breakdown": subject_breakdown
            }
            
        except Exception as e:
            raise APIException(
                code="HOTS_PERFORMANCE_FAILED",
                message=f"Failed to fetch HOTS performance: {str(e)}",
                status_code=500
            )


# Global service instance
hots_service = HOTSService()
