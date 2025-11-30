"""Microplan generation service with spaced repetition"""

from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal
import random

from supabase import create_client, Client
from app.config import settings
from app.models.progress import MicroPlan, MicroPlanCreate
from app.models.content import ContentType, PYQ, HOTSQuestion, ContentItem
from app.models.base import Subject
from app.utils.exceptions import APIException


class SM2Algorithm:
    """
    Simple implementation of the SM-2 spaced repetition algorithm
    
    The SM-2 algorithm calculates optimal review intervals based on:
    - Quality of recall (0-5 scale)
    - Number of repetitions
    - Previous ease factor
    """
    
    @staticmethod
    def calculate_next_interval(
        quality: float,
        repetitions: int,
        previous_interval: int,
        previous_ease_factor: float = 2.5
    ) -> Tuple[int, float, int]:
        """
        Calculate next review interval using SM-2 algorithm
        
        Args:
            quality: Quality of recall (0-5, where 5 is perfect recall)
            repetitions: Number of successful repetitions
            previous_interval: Previous interval in days
            previous_ease_factor: Previous ease factor (default 2.5)
            
        Returns:
            Tuple of (next_interval, new_ease_factor, new_repetitions)
        """
        # Calculate new ease factor
        ease_factor = previous_ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        
        # Ensure ease factor is at least 1.3
        if ease_factor < 1.3:
            ease_factor = 1.3
        
        # Calculate repetitions
        if quality < 3:
            # Failed recall - reset repetitions
            new_repetitions = 0
            next_interval = 1
        else:
            # Successful recall
            new_repetitions = repetitions + 1
            
            if new_repetitions == 1:
                next_interval = 1
            elif new_repetitions == 2:
                next_interval = 6
            else:
                next_interval = int(previous_interval * ease_factor)
        
        return next_interval, ease_factor, new_repetitions
    
    @staticmethod
    def is_due_for_review(
        last_reviewed: date,
        interval: int,
        today: Optional[date] = None
    ) -> bool:
        """
        Check if a topic is due for review
        
        Args:
            last_reviewed: Date of last review
            interval: Review interval in days
            today: Current date (defaults to today)
            
        Returns:
            True if review is due, False otherwise
        """
        if today is None:
            today = date.today()
        
        next_review_date = last_reviewed + timedelta(days=interval)
        return today >= next_review_date


class MicroPlanService:
    """Service for generating personalized daily micro-plans"""
    
    def __init__(self):
        """Initialize microplan service with Supabase client"""
        self.supabase: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
        self.sm2 = SM2Algorithm()
    
    async def generate_microplan(
        self,
        user_id: str,
        plan_date: Optional[date] = None,
        subject: Optional[Subject] = None
    ) -> MicroPlan:
        """
        Generate a personalized daily micro-plan for a student
        
        The micro-plan includes:
        - 1 concept summary (NCERT content)
        - 2 PYQs (Previous Year Questions)
        - 1 HOTS question
        - 1 quiz (generated from topic questions)
        
        Selection is adaptive based on:
        - Student's mastery scores
        - Spaced repetition scheduling
        - Recent activity
        
        Args:
            user_id: Student user ID
            plan_date: Date for the micro-plan (defaults to today)
            subject: Specific subject to focus on (optional)
            
        Returns:
            MicroPlan object with selected content
            
        Raises:
            APIException: If generation fails
        """
        try:
            if plan_date is None:
                plan_date = date.today()
            
            # Check if micro-plan already exists for this date
            existing_plan = await self._get_existing_plan(user_id, plan_date, subject)
            if existing_plan:
                return existing_plan
            
            # Get student's progress and mastery scores
            progress_data = await self._get_student_progress(user_id, subject)
            
            # Determine subject if not specified (rotate or pick weakest)
            if subject is None:
                subject = await self._select_subject(user_id, progress_data)
            
            # Select content using adaptive algorithm
            concept_summary = await self._select_concept_summary(
                user_id, subject, progress_data
            )
            
            pyqs = await self._select_pyqs(
                user_id, subject, progress_data, count=2
            )
            
            hots_question = await self._select_hots_question(
                user_id, subject, progress_data
            )
            
            quiz_data = await self._generate_quiz(
                user_id, subject, progress_data
            )
            
            # Create micro-plan in database
            microplan_create = MicroPlanCreate(
                user_id=user_id,
                plan_date=plan_date,
                subject=subject,
                concept_summary_id=concept_summary.id if concept_summary else None,
                pyq_ids=[pyq.id for pyq in pyqs],
                hots_question_id=hots_question.id if hots_question else None,
                quiz_data=quiz_data,
                estimated_minutes=15
            )
            
            microplan = await self._save_microplan(microplan_create)
            
            return microplan
            
        except Exception as e:
            raise APIException(
                status_code=500,
                detail=f"Failed to generate micro-plan: {str(e)}"
            )
    
    async def _get_existing_plan(
        self,
        user_id: str,
        plan_date: date,
        subject: Optional[Subject]
    ) -> Optional[MicroPlan]:
        """Check if a micro-plan already exists for the given date"""
        try:
            query = self.supabase.table("microplans").select("*").eq(
                "user_id", user_id
            ).eq("plan_date", plan_date.isoformat())
            
            if subject:
                query = query.eq("subject", subject.value)
            
            result = query.execute()
            
            if result.data and len(result.data) > 0:
                plan_data = result.data[0]
                return MicroPlan(**plan_data)
            
            return None
            
        except Exception as e:
            print(f"Error checking existing plan: {str(e)}")
            return None
    
    async def _get_student_progress(
        self,
        user_id: str,
        subject: Optional[Subject]
    ) -> List[Dict[str, Any]]:
        """Get student's progress and mastery scores"""
        try:
            query = self.supabase.table("progress").select("*").eq("user_id", user_id)
            
            if subject:
                query = query.eq("subject", subject.value)
            
            result = query.execute()
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error fetching student progress: {str(e)}")
            return []
    
    async def _select_subject(
        self,
        user_id: str,
        progress_data: List[Dict[str, Any]]
    ) -> Subject:
        """
        Select subject for micro-plan
        
        Strategy:
        - If no progress data, pick randomly
        - Otherwise, pick subject with lowest average mastery score
        """
        if not progress_data:
            # Random selection if no progress data
            return random.choice(list(Subject))
        
        # Calculate average mastery by subject
        subject_mastery = {}
        for progress in progress_data:
            subj = progress.get("subject")
            score = float(progress.get("mastery_score", 0))
            
            if subj not in subject_mastery:
                subject_mastery[subj] = []
            subject_mastery[subj].append(score)
        
        # Find subject with lowest average mastery
        avg_mastery = {
            subj: sum(scores) / len(scores)
            for subj, scores in subject_mastery.items()
        }
        
        weakest_subject = min(avg_mastery, key=avg_mastery.get)
        return Subject(weakest_subject)
    
    async def _select_concept_summary(
        self,
        user_id: str,
        subject: Subject,
        progress_data: List[Dict[str, Any]]
    ) -> Optional[ContentItem]:
        """
        Select a concept summary (NCERT content) using spaced repetition
        
        Strategy:
        - Prioritize topics due for review based on SM-2 algorithm
        - Fall back to new topics if no reviews due
        """
        try:
            # Get topics for this subject
            topics_result = self.supabase.table("topics").select("*").eq(
                "subject", subject.value
            ).order("order_index").execute()
            
            if not topics_result.data:
                return None
            
            # Calculate which topics are due for review using SM-2
            topics_due = []
            new_topics = []
            
            for topic in topics_result.data:
                topic_id = topic["id"]
                
                # Find progress for this topic
                topic_progress = next(
                    (p for p in progress_data if p.get("topic_id") == topic_id),
                    None
                )
                
                if topic_progress:
                    # Use SM-2 to determine if review is due
                    last_practiced = topic_progress.get("last_practiced_at")
                    if last_practiced:
                        last_date = datetime.fromisoformat(
                            last_practiced.replace("Z", "+00:00")
                        ).date()
                        
                        # Calculate interval based on mastery score
                        # Convert mastery (0-100) to quality (0-5) for SM-2
                        mastery = float(topic_progress.get("mastery_score", 0))
                        quality = mastery / 20.0  # Scale to 0-5
                        
                        # Get metadata for SM-2 tracking
                        metadata = topic_progress.get("metadata", {})
                        repetitions = metadata.get("sm2_repetitions", 0)
                        interval = metadata.get("sm2_interval", 1)
                        
                        # Check if due for review
                        if self.sm2.is_due_for_review(last_date, interval):
                            # Priority based on how overdue and mastery
                            days_overdue = (date.today() - last_date).days - interval
                            priority = days_overdue * (100 - mastery)
                            topics_due.append((topic, priority, mastery))
                    else:
                        # Has progress but never practiced - treat as new
                        new_topics.append((topic, 0))
                else:
                    # New topic - high priority
                    new_topics.append((topic, 0))
            
            # Prioritize: overdue topics first, then new topics
            if topics_due:
                # Sort by priority (highest first)
                topics_due.sort(key=lambda x: -x[1])
                selected_topic = topics_due[0][0]
            elif new_topics:
                # Pick first new topic
                selected_topic = new_topics[0][0]
            else:
                # No topics due, pick a random topic for reinforcement
                selected_topic = random.choice(topics_result.data)
            
            # Get NCERT content for this topic
            content_result = self.supabase.table("content").select("*").eq(
                "type", ContentType.NCERT.value
            ).eq("subject", subject.value).eq(
                "topic_id", selected_topic["id"]
            ).limit(1).execute()
            
            if content_result.data and len(content_result.data) > 0:
                return ContentItem(**content_result.data[0])
            
            return None
            
        except Exception as e:
            print(f"Error selecting concept summary: {str(e)}")
            return None
    
    async def _select_pyqs(
        self,
        user_id: str,
        subject: Subject,
        progress_data: List[Dict[str, Any]],
        count: int = 2
    ) -> List[PYQ]:
        """
        Select PYQs based on student's mastery level
        
        Strategy:
        - Mix of difficulty levels based on overall mastery
        - Prefer recent years
        - Avoid recently attempted questions
        """
        try:
            # Calculate average mastery for subject
            subject_progress = [
                p for p in progress_data
                if p.get("subject") == subject.value
            ]
            
            avg_mastery = 50.0  # Default
            if subject_progress:
                avg_mastery = sum(
                    float(p.get("mastery_score", 0))
                    for p in subject_progress
                ) / len(subject_progress)
            
            # Determine difficulty distribution based on mastery
            if avg_mastery < 40:
                # Focus on easy questions
                difficulties = ["easy", "easy", "medium"]
            elif avg_mastery < 70:
                # Mix of medium and hard
                difficulties = ["medium", "medium", "hard"]
            else:
                # Focus on hard questions
                difficulties = ["hard", "hard", "medium"]
            
            # Get PYQs
            pyqs_result = self.supabase.table("pyqs").select("*").eq(
                "subject", subject.value
            ).order("year", desc=True).limit(50).execute()
            
            if not pyqs_result.data:
                return []
            
            # Filter by difficulty and randomly select
            selected_pyqs = []
            for difficulty in difficulties[:count]:
                matching_pyqs = [
                    pyq for pyq in pyqs_result.data
                    if pyq.get("difficulty") == difficulty
                ]
                
                if matching_pyqs:
                    selected = random.choice(matching_pyqs)
                    selected_pyqs.append(PYQ(**selected))
                    
                if len(selected_pyqs) >= count:
                    break
            
            # If we don't have enough, fill with random ones
            while len(selected_pyqs) < count and pyqs_result.data:
                random_pyq = random.choice(pyqs_result.data)
                if not any(p.id == random_pyq["id"] for p in selected_pyqs):
                    selected_pyqs.append(PYQ(**random_pyq))
            
            return selected_pyqs[:count]
            
        except Exception as e:
            print(f"Error selecting PYQs: {str(e)}")
            return []
    
    async def _select_hots_question(
        self,
        user_id: str,
        subject: Subject,
        progress_data: List[Dict[str, Any]]
    ) -> Optional[HOTSQuestion]:
        """
        Select a HOTS question
        
        Strategy:
        - Select from topics where student has >60% mastery
        - Prefer topics not recently practiced with HOTS
        """
        try:
            # Find topics with good mastery (>60%)
            strong_topics = [
                p.get("topic_id")
                for p in progress_data
                if p.get("subject") == subject.value
                and float(p.get("mastery_score", 0)) > 60
            ]
            
            query = self.supabase.table("hots_questions").select("*").eq(
                "subject", subject.value
            )
            
            if strong_topics:
                query = query.in_("topic_id", strong_topics)
            
            result = query.limit(20).execute()
            
            if result.data and len(result.data) > 0:
                selected = random.choice(result.data)
                return HOTSQuestion(**selected)
            
            return None
            
        except Exception as e:
            print(f"Error selecting HOTS question: {str(e)}")
            return None
    
    async def _generate_quiz(
        self,
        user_id: str,
        subject: Subject,
        progress_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate a quick quiz (3-5 questions)
        
        Strategy:
        - Mix of multiple choice and short answer
        - Based on recently studied topics
        """
        try:
            # For now, return a simple quiz structure
            # In a full implementation, this would generate actual questions
            quiz = {
                "title": f"Quick {subject.value.title()} Quiz",
                "questions": [],
                "total_marks": 10,
                "duration_minutes": 5,
                "instructions": "Answer all questions to the best of your ability"
            }
            
            # Get some PYQs for the quiz
            pyqs_result = self.supabase.table("pyqs").select("*").eq(
                "subject", subject.value
            ).limit(10).execute()
            
            if pyqs_result.data:
                # Select 3 random questions
                selected = random.sample(
                    pyqs_result.data,
                    min(3, len(pyqs_result.data))
                )
                
                for i, pyq in enumerate(selected):
                    quiz["questions"].append({
                        "id": pyq["id"],
                        "question_number": i + 1,
                        "question": pyq["question"],
                        "marks": pyq.get("marks", 3),
                        "type": "short_answer"
                    })
            
            return quiz
            
        except Exception as e:
            print(f"Error generating quiz: {str(e)}")
            return {
                "title": f"Quick {subject.value.title()} Quiz",
                "questions": [],
                "total_marks": 0,
                "duration_minutes": 5
            }
    
    async def _save_microplan(self, microplan_create: MicroPlanCreate) -> MicroPlan:
        """Save micro-plan to database"""
        try:
            data = {
                "user_id": microplan_create.user_id,
                "plan_date": microplan_create.plan_date.isoformat(),
                "subject": microplan_create.subject.value,
                "concept_summary_id": microplan_create.concept_summary_id,
                "pyq_ids": microplan_create.pyq_ids,
                "hots_question_id": microplan_create.hots_question_id,
                "quiz_data": microplan_create.quiz_data,
                "estimated_minutes": microplan_create.estimated_minutes,
                "is_completed": False,
                "metadata": {}
            }
            
            result = self.supabase.table("microplans").insert(data).execute()
            
            if result.data and len(result.data) > 0:
                return MicroPlan(**result.data[0])
            
            raise Exception("Failed to save micro-plan")
            
        except Exception as e:
            raise APIException(
                status_code=500,
                detail=f"Failed to save micro-plan: {str(e)}"
            )
    
    async def get_microplan_by_id(
        self,
        microplan_id: str
    ) -> MicroPlan:
        """Get a micro-plan by ID"""
        try:
            result = self.supabase.table("microplans").select("*").eq(
                "id", microplan_id
            ).execute()
            
            if not result.data or len(result.data) == 0:
                raise APIException(
                    status_code=404,
                    detail="Micro-plan not found"
                )
            
            return await self._build_microplan(result.data[0])
            
        except Exception as e:
            if isinstance(e, APIException):
                raise
            raise APIException(
                status_code=500,
                detail=f"Failed to get micro-plan: {str(e)}"
            )
    
    async def get_microplan(
        self,
        user_id: str,
        plan_date: Optional[date] = None
    ) -> Optional[MicroPlan]:
        """Get micro-plan for a specific date"""
        try:
            if plan_date is None:
                plan_date = date.today()
            
            result = self.supabase.table("microplans").select("*").eq(
                "user_id", user_id
            ).eq("plan_date", plan_date.isoformat()).execute()
            
            if result.data and len(result.data) > 0:
                return await self._build_microplan(result.data[0])
            
            return None
            
        except Exception as e:
            print(f"Error fetching micro-plan: {str(e)}")
            return None
    
    async def mark_completed(
        self,
        microplan_id: str,
        user_id: str
    ) -> MicroPlan:
        """Mark a micro-plan as completed"""
        try:
            data = {
                "is_completed": True,
                "completed_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table("microplans").update(data).eq(
                "id", microplan_id
            ).eq("user_id", user_id).execute()
            
            if result.data and len(result.data) > 0:
                return MicroPlan(**result.data[0])
            
            raise APIException(
                status_code=404,
                detail="Micro-plan not found"
            )
            
        except APIException:
            raise
        except Exception as e:
            raise APIException(
                status_code=500,
                detail=f"Failed to mark micro-plan as completed: {str(e)}"
            )


# Global service instance
microplan_service = MicroPlanService()
