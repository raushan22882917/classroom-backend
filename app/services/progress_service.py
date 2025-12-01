"""Progress tracking service"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from supabase import Client, create_client

from app.models.progress import (
    Progress,
    ProgressCreate,
    ProgressUpdate,
    MasteryScore
)
from app.models.base import Subject
from app.utils.exceptions import APIException
from app.config import settings


class ProgressService:
    """Service for managing student progress and mastery scores"""
    
    def __init__(self, supabase_client: Client, analytics_service=None):
        self.supabase = supabase_client
        self.analytics_service = analytics_service
    
    async def get_user_progress(self, user_id: str, subject: Optional[Subject] = None) -> List[Progress]:
        """
        Get all progress records for a user, optionally filtered by subject
        
        Args:
            user_id: User ID
            subject: Optional subject filter
            
        Returns:
            List of Progress records
        """
        try:
            query = self.supabase.table("progress").select("*").eq("user_id", user_id)
            
            if subject:
                query = query.eq("subject", subject.value)
            
            response = query.execute()
            
            if not response.data:
                return []
        except Exception as e:
            error_msg = str(e)
            # Check for Supabase authentication errors
            if "Invalid API key" in error_msg or "401" in error_msg or "JSON could not be generated" in error_msg:
                raise APIException(
                    code="SUPABASE_AUTH_ERROR",
                    message="Database authentication failed. Please check Supabase service key configuration.",
                    status_code=503
                )
            # Re-raise other errors
            raise
        
        # Parse records safely, handling JSONB fields and type conversions
        progress_records = []
        for record in response.data:
            try:
                # Convert mastery_score to Decimal if needed
                if 'mastery_score' in record and record['mastery_score'] is not None:
                    if isinstance(record['mastery_score'], str):
                        record['mastery_score'] = Decimal(record['mastery_score'])
                    elif isinstance(record['mastery_score'], (int, float)):
                        record['mastery_score'] = Decimal(str(record['mastery_score']))
                else:
                    record['mastery_score'] = Decimal("0.00")
                
                # Convert subject to Subject enum if it's a string
                if 'subject' in record and isinstance(record['subject'], str):
                    try:
                        record['subject'] = Subject(record['subject'])
                    except ValueError:
                        # Skip invalid subject
                        continue
                
                # Convert datetime strings to datetime objects
                if 'last_practiced_at' in record and record['last_practiced_at']:
                    if isinstance(record['last_practiced_at'], str):
                        try:
                            # Try ISO format first
                            if 'T' in record['last_practiced_at']:
                                record['last_practiced_at'] = datetime.fromisoformat(record['last_practiced_at'].replace('Z', '+00:00'))
                            else:
                                record['last_practiced_at'] = datetime.strptime(record['last_practiced_at'], '%Y-%m-%d %H:%M:%S%z')
                        except:
                            try:
                                record['last_practiced_at'] = datetime.strptime(record['last_practiced_at'], '%Y-%m-%d %H:%M:%S')
                            except:
                                record['last_practiced_at'] = None
                
                # Convert date strings to date objects
                if 'last_streak_date' in record and record['last_streak_date']:
                    if isinstance(record['last_streak_date'], str):
                        try:
                            if 'T' in record['last_streak_date']:
                                record['last_streak_date'] = datetime.fromisoformat(record['last_streak_date'].replace('Z', '+00:00')).date()
                            else:
                                record['last_streak_date'] = datetime.strptime(record['last_streak_date'], '%Y-%m-%d').date()
                        except:
                            record['last_streak_date'] = None
                
                # Convert created_at and updated_at to datetime
                for date_field in ['created_at', 'updated_at']:
                    if date_field in record and record[date_field]:
                        if isinstance(record[date_field], str):
                            try:
                                if 'T' in record[date_field]:
                                    record[date_field] = datetime.fromisoformat(record[date_field].replace('Z', '+00:00'))
                                else:
                                    record[date_field] = datetime.strptime(record[date_field], '%Y-%m-%d %H:%M:%S%z')
                            except:
                                try:
                                    record[date_field] = datetime.strptime(record[date_field], '%Y-%m-%d %H:%M:%S')
                                except:
                                    pass
                
                # Ensure achievements is a list
                if 'achievements' in record:
                    if isinstance(record['achievements'], str):
                        import json
                        try:
                            record['achievements'] = json.loads(record['achievements'])
                        except:
                            record['achievements'] = []
                    elif not isinstance(record['achievements'], list):
                        record['achievements'] = []
                else:
                    record['achievements'] = []
                
                # Ensure metadata is a dict
                if 'metadata' in record:
                    if isinstance(record['metadata'], str):
                        import json
                        try:
                            record['metadata'] = json.loads(record['metadata'])
                        except:
                            record['metadata'] = {}
                    elif not isinstance(record['metadata'], dict):
                        record['metadata'] = {}
                else:
                    record['metadata'] = {}
                
                # Ensure all required fields have defaults
                if 'questions_attempted' not in record:
                    record['questions_attempted'] = 0
                if 'correct_answers' not in record:
                    record['correct_answers'] = 0
                if 'total_time_minutes' not in record:
                    record['total_time_minutes'] = 0
                if 'streak_days' not in record:
                    record['streak_days'] = 0
                
                progress_records.append(Progress(**record))
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to parse progress record: {str(e)}, skipping record. Record: {record}")
                continue
        
        return progress_records
    
    async def get_progress_by_topic(self, user_id: str, topic_id: str) -> Optional[Progress]:
        """
        Get progress for a specific topic
        
        Args:
            user_id: User ID
            topic_id: Topic ID
            
        Returns:
            Progress record or None
        """
        try:
            response = self.supabase.table("progress").select("*").eq(
                "user_id", user_id
            ).eq("topic_id", topic_id).execute()
            
            if not response.data:
                return None
            
            return Progress(**response.data[0])
        except Exception as e:
            raise APIException(
                code="PROGRESS_FETCH_ERROR",
                message=f"Failed to fetch progress: {str(e)}",
                status_code=500
            )
    
    def calculate_mastery_score(
        self,
        correct_answers: int,
        total_questions: int,
        avg_time_per_question: float,
        difficulty_weights: Dict[str, float] = None
    ) -> Decimal:
        """
        Calculate mastery score based on accuracy, time, and difficulty
        
        Formula:
        - Base score: (correct_answers / total_questions) * 100
        - Time factor: Bonus/penalty based on time efficiency
        - Difficulty factor: Weight based on question difficulty
        
        Args:
            correct_answers: Number of correct answers
            total_questions: Total questions attempted
            avg_time_per_question: Average time per question in seconds
            difficulty_weights: Optional difficulty weights
            
        Returns:
            Mastery score (0-100)
        """
        if total_questions == 0:
            return Decimal("0.00")
        
        # Base accuracy score (0-100)
        accuracy = (correct_answers / total_questions) * 100
        
        # Time efficiency factor
        # Optimal time: 60-120 seconds per question
        # Faster than 60s: bonus up to 10%
        # Slower than 120s: penalty up to 10%
        time_factor = 1.0
        if avg_time_per_question < 60:
            # Bonus for speed (max 10%)
            time_factor = 1.0 + min(0.1, (60 - avg_time_per_question) / 600)
        elif avg_time_per_question > 120:
            # Penalty for slowness (max 10%)
            time_factor = 1.0 - min(0.1, (avg_time_per_question - 120) / 1200)
        
        # Apply time factor
        score = accuracy * time_factor
        
        # Ensure score is within bounds
        score = max(0, min(100, score))
        
        return Decimal(str(round(score, 2)))
    
    async def update_progress(
        self,
        user_id: str,
        topic_id: str,
        subject: Subject,
        correct_answers: int,
        total_questions: int,
        time_spent_minutes: int
    ) -> Progress:
        """
        Update progress for a topic with new activity data
        
        Args:
            user_id: User ID
            topic_id: Topic ID
            subject: Subject
            correct_answers: Number of correct answers in this session
            total_questions: Total questions in this session
            time_spent_minutes: Time spent in minutes
            
        Returns:
            Updated Progress record
        """
        try:
            # Get existing progress
            existing = await self.get_progress_by_topic(user_id, topic_id)
            
            if existing:
                # Update existing progress
                new_correct = existing.correct_answers + correct_answers
                new_attempted = existing.questions_attempted + total_questions
                new_time = existing.total_time_minutes + time_spent_minutes
                
                # Calculate new mastery score
                avg_time_per_question = (new_time * 60) / new_attempted if new_attempted > 0 else 0
                new_mastery = self.calculate_mastery_score(
                    new_correct,
                    new_attempted,
                    avg_time_per_question
                )
                
                # Update streak
                streak_days, last_streak_date = self._update_streak(
                    existing.last_streak_date
                )
                
                update_data = {
                    "mastery_score": float(new_mastery),
                    "questions_attempted": new_attempted,
                    "correct_answers": new_correct,
                    "total_time_minutes": new_time,
                    "last_practiced_at": datetime.utcnow().isoformat(),
                    "streak_days": streak_days,
                    "last_streak_date": last_streak_date.isoformat() if last_streak_date else None,
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                response = self.supabase.table("progress").update(update_data).eq(
                    "id", str(existing.id)
                ).execute()
                
                progress = Progress(**response.data[0])
                
                # Log progress snapshot to BigQuery
                if self.analytics_service:
                    await self.analytics_service.log_progress_snapshot(
                        user_id=user_id,
                        subject=subject.value,
                        topic_id=topic_id,
                        mastery_score=float(new_mastery),
                        questions_attempted=new_attempted,
                        correct_answers=new_correct,
                        total_time_minutes=new_time,
                        streak_days=streak_days
                    )
                
                return progress
            else:
                # Create new progress record
                avg_time_per_question = (time_spent_minutes * 60) / total_questions if total_questions > 0 else 0
                mastery_score = self.calculate_mastery_score(
                    correct_answers,
                    total_questions,
                    avg_time_per_question
                )
                
                today = date.today()
                
                create_data = {
                    "user_id": user_id,
                    "topic_id": topic_id,
                    "subject": subject.value,
                    "mastery_score": float(mastery_score),
                    "questions_attempted": total_questions,
                    "correct_answers": correct_answers,
                    "total_time_minutes": time_spent_minutes,
                    "last_practiced_at": datetime.utcnow().isoformat(),
                    "streak_days": 1,
                    "last_streak_date": today.isoformat(),
                    "achievements": [],
                    "metadata": {}
                }
                
                response = self.supabase.table("progress").insert(create_data).execute()
                
                progress = Progress(**response.data[0])
                
                # Log progress snapshot to BigQuery
                if self.analytics_service:
                    await self.analytics_service.log_progress_snapshot(
                        user_id=user_id,
                        subject=subject.value,
                        topic_id=topic_id,
                        mastery_score=float(mastery_score),
                        questions_attempted=total_questions,
                        correct_answers=correct_answers,
                        total_time_minutes=time_spent_minutes,
                        streak_days=1
                    )
                
                return progress
        except Exception as e:
            raise APIException(
                code="PROGRESS_UPDATE_ERROR",
                message=f"Failed to update progress: {str(e)}",
                status_code=500
            )
    
    def _update_streak(self, last_streak_date: Optional[date]) -> tuple[int, date]:
        """
        Update streak based on last streak date
        
        Args:
            last_streak_date: Last date user practiced
            
        Returns:
            Tuple of (streak_days, new_last_streak_date)
        """
        today = date.today()
        
        if not last_streak_date:
            # First time practicing
            return 1, today
        
        days_diff = (today - last_streak_date).days
        
        if days_diff == 0:
            # Same day, no change
            return 1, last_streak_date
        elif days_diff == 1:
            # Consecutive day, increment streak
            return 1, today  # Will be incremented by caller
        else:
            # Streak broken, reset
            return 1, today
    
    async def get_user_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get summary of user's overall progress
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with summary statistics
        """
        try:
            try:
                progress_records = await self.get_user_progress(user_id)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Failed to get user progress, returning empty summary: {str(e)}")
                progress_records = []
            
            if not progress_records:
                return {
                    "total_topics": 0,
                    "average_mastery": 0.0,
                    "total_topics_attempted": 0,
                    "total_questions_attempted": 0,
                    "total_correct_answers": 0,
                    "total_time_minutes": 0,
                    "current_streak": 0,
                    "subject_breakdown": {}
                }
            
            # Calculate overall statistics
            total_topics = len(progress_records)
            if total_topics == 0:
                return {
                    "total_topics": 0,
                    "average_mastery": 0.0,
                    "total_topics_attempted": 0,
                    "total_questions_attempted": 0,
                    "total_correct_answers": 0,
                    "total_time_minutes": 0,
                    "current_streak": 0,
                    "subject_breakdown": {}
                }
            
            # Safely calculate averages, handling Decimal types
            mastery_scores = []
            total_questions = 0
            total_correct = 0
            total_time = 0
            streaks = []
            
            for p in progress_records:
                try:
                    if hasattr(p, 'mastery_score') and p.mastery_score is not None:
                        mastery_scores.append(float(p.mastery_score))
                    else:
                        mastery_scores.append(0.0)
                    
                    total_questions += getattr(p, 'questions_attempted', 0) or 0
                    total_correct += getattr(p, 'correct_answers', 0) or 0
                    total_time += getattr(p, 'total_time_minutes', 0) or 0
                    streaks.append(getattr(p, 'streak_days', 0) or 0)
                except Exception as e:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Error processing progress record: {str(e)}")
                    continue
            
            # Calculate average mastery safely
            if mastery_scores and len(mastery_scores) > 0:
                avg_mastery = sum(mastery_scores) / len(mastery_scores)
            else:
                avg_mastery = 0.0
            
            current_streak = max(streaks) if streaks else 0
            
            # Group by subject
            subjects = {}
            for record in progress_records:
                try:
                    # Safely get subject value
                    subject_attr = getattr(record, 'subject', None)
                    if subject_attr:
                        if hasattr(subject_attr, 'value'):
                            subject = subject_attr.value
                        elif isinstance(subject_attr, str):
                            subject = subject_attr
                        else:
                            subject = str(subject_attr)
                    else:
                        subject = 'unknown'
                    
                    if subject not in subjects:
                        subjects[subject] = {
                            "topics_attempted": 0,
                            "average_mastery": 0.0,
                            "questions_attempted": 0,
                            "correct_answers": 0
                        }
                    
                    subjects[subject]["topics_attempted"] += 1
                    mastery_val = float(getattr(record, 'mastery_score', 0)) if getattr(record, 'mastery_score', None) else 0.0
                    subjects[subject]["average_mastery"] += mastery_val
                    subjects[subject]["questions_attempted"] += getattr(record, 'questions_attempted', 0) or 0
                    subjects[subject]["correct_answers"] += getattr(record, 'correct_answers', 0) or 0
                except Exception as e:
                    # Skip records with errors
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Skipping record due to error: {str(e)}")
                    continue
            
            # Calculate averages for each subject
            subject_breakdown = {}
            for subject, data in subjects.items():
                count = data["topics_attempted"]
                subject_breakdown[subject] = {
                    "topics_attempted": count,
                    "average_mastery": round(data["average_mastery"] / count, 2) if count > 0 else 0.0,
                    "questions_attempted": data["questions_attempted"],
                    "correct_answers": data["correct_answers"]
                }
            
            return {
                "total_topics": total_topics,
                "total_topics_attempted": total_topics,
                "average_mastery": round(float(avg_mastery), 2),
                "total_questions_attempted": total_questions,
                "total_correct_answers": total_correct,
                "total_time_minutes": total_time,
                "current_streak": current_streak,
                "subject_breakdown": subject_breakdown
            }
        except Exception as e:
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            logger.error(f"Error in get_user_summary: {str(e)}")
            logger.error(traceback.format_exc())
            # Return empty summary instead of raising exception
            return {
                "total_topics": 0,
                "total_topics_attempted": 0,
                "average_mastery": 0.0,
                "total_questions_attempted": 0,
                "total_correct_answers": 0,
                "total_time_minutes": 0,
                "current_streak": 0,
                "subject_breakdown": {}
            }
    
    async def check_and_award_achievements(self, user_id: str, topic_id: str) -> List[Dict[str, Any]]:
        """
        Check if user has earned any achievements for a topic
        
        Args:
            user_id: User ID
            topic_id: Topic ID
            
        Returns:
            List of newly earned achievements
        """
        try:
            progress = await self.get_progress_by_topic(user_id, topic_id)
            
            if not progress:
                return []
            
            new_achievements = []
            existing_achievement_ids = {a.get("id") for a in progress.achievements}
            
            # Check for mastery achievements
            if progress.mastery_score >= 80 and "mastery_80" not in existing_achievement_ids:
                new_achievements.append({
                    "id": "mastery_80",
                    "name": "Topper Badge",
                    "description": "Achieved 80% mastery in this topic",
                    "icon": "🏆",
                    "earned_at": datetime.utcnow().isoformat()
                })
            
            if progress.mastery_score >= 90 and "mastery_90" not in existing_achievement_ids:
                new_achievements.append({
                    "id": "mastery_90",
                    "name": "Excellence Badge",
                    "description": "Achieved 90% mastery in this topic",
                    "icon": "⭐",
                    "earned_at": datetime.utcnow().isoformat()
                })
            
            # Check for streak achievements
            if progress.streak_days >= 7 and "streak_7" not in existing_achievement_ids:
                new_achievements.append({
                    "id": "streak_7",
                    "name": "Week Warrior",
                    "description": "Maintained a 7-day learning streak",
                    "icon": "🔥",
                    "earned_at": datetime.utcnow().isoformat()
                })
            
            if progress.streak_days >= 30 and "streak_30" not in existing_achievement_ids:
                new_achievements.append({
                    "id": "streak_30",
                    "name": "Month Master",
                    "description": "Maintained a 30-day learning streak",
                    "icon": "💪",
                    "earned_at": datetime.utcnow().isoformat()
                })
            
            # Update progress with new achievements
            if new_achievements:
                updated_achievements = progress.achievements + new_achievements
                
                self.supabase.table("progress").update({
                    "achievements": updated_achievements,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", str(progress.id)).execute()
            
            return new_achievements
        except Exception as e:
            raise APIException(
                code="ACHIEVEMENT_CHECK_ERROR",
                message=f"Failed to check achievements: {str(e)}",
                status_code=500
            )


# Global instance for services that need direct access
supabase_client = create_client(
    settings.supabase_url,
    settings.supabase_service_key
)

progress_service = ProgressService(supabase_client)
