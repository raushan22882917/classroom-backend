"""Admin service for dashboard metrics and student oversight"""

from typing import Optional, List, Dict
from datetime import datetime, timedelta
from decimal import Decimal
from supabase import create_client, Client

from app.config import settings
from app.models.admin import (
    AdminDashboardMetrics,
    StudentAlert,
    StudentOverview,
    StudentDetailedProfile
)
from app.models.base import Subject
from app.utils.exceptions import APIException


class AdminService:
    """Service for admin operations"""
    
    def __init__(self):
        """Initialize admin service with Supabase client"""
        self.supabase: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_key  # Use service key for admin operations
        )
    
    async def get_dashboard_metrics(self) -> AdminDashboardMetrics:
        """
        Get aggregate metrics for admin dashboard
        
        Returns:
            AdminDashboardMetrics with active students, average mastery, completion rate, and flagged students
        """
        try:
            # Calculate active students (active in last 7 days)
            seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
            
            # Get total students count from progress table (unique user_ids)
            progress_response = self.supabase.table("progress").select("user_id").execute()
            unique_users = set(row["user_id"] for row in progress_response.data)
            total_students = len(unique_users)
            
            # Get active students (those with recent activity)
            active_progress = self.supabase.table("progress")\
                .select("user_id")\
                .gte("last_practiced_at", seven_days_ago)\
                .execute()
            active_users = set(row["user_id"] for row in active_progress.data)
            active_students = len(active_users)
            
            # Calculate average mastery score across all students and topics
            all_progress = self.supabase.table("progress")\
                .select("mastery_score")\
                .execute()
            
            if all_progress.data:
                total_mastery = sum(Decimal(str(row["mastery_score"])) for row in all_progress.data)
                average_mastery_score = total_mastery / len(all_progress.data)
            else:
                average_mastery_score = Decimal("0.00")
            
            # Calculate completion rate (topics with mastery >= 80%)
            completed_topics = [row for row in all_progress.data if Decimal(str(row["mastery_score"])) >= 80]
            completion_rate = Decimal("0.00")
            if all_progress.data:
                completion_rate = (Decimal(len(completed_topics)) / Decimal(len(all_progress.data))) * 100
            
            # Get flagged students (mastery < 50%)
            flagged_students = await self._get_flagged_students()
            
            # Get total content items
            content_response = self.supabase.table("content").select("id", count="exact").execute()
            total_content_items = content_response.count or 0
            
            # Get total test sessions
            test_response = self.supabase.table("test_sessions").select("id", count="exact").execute()
            total_test_sessions = test_response.count or 0
            
            return AdminDashboardMetrics(
                active_students=active_students,
                total_students=total_students,
                average_mastery_score=average_mastery_score.quantize(Decimal("0.01")),
                completion_rate=completion_rate.quantize(Decimal("0.01")),
                flagged_students=flagged_students,
                total_content_items=total_content_items,
                total_test_sessions=total_test_sessions,
                metadata={
                    "last_updated": datetime.now().isoformat(),
                    "active_threshold_days": 7
                }
            )
            
        except Exception as e:
            raise APIException(
                status_code=500,
                detail=f"Failed to fetch dashboard metrics: {str(e)}"
            )
    
    async def _get_flagged_students(self) -> List[StudentAlert]:
        """
        Get list of flagged students (mastery < 50%)
        
        Returns:
            List of StudentAlert objects
        """
        try:
            # Get students with low mastery scores
            low_mastery = self.supabase.table("progress")\
                .select("user_id, subject, mastery_score, last_practiced_at")\
                .lt("mastery_score", 50)\
                .execute()
            
            flagged_students = []
            
            # Group by user_id to avoid duplicates
            user_alerts = {}
            for row in low_mastery.data:
                user_id = row["user_id"]
                mastery_score = Decimal(str(row["mastery_score"]))
                
                # Determine severity based on mastery score
                if mastery_score < 30:
                    severity = "high"
                elif mastery_score < 40:
                    severity = "medium"
                else:
                    severity = "low"
                
                alert_reason = f"Low mastery in {row['subject']} ({mastery_score}%)"
                
                if user_id not in user_alerts or mastery_score < user_alerts[user_id]["score"]:
                    user_alerts[user_id] = {
                        "score": mastery_score,
                        "alert": StudentAlert(
                            user_id=user_id,
                            subject=Subject(row["subject"]),
                            mastery_score=mastery_score,
                            last_active=datetime.fromisoformat(row["last_practiced_at"]) if row.get("last_practiced_at") else None,
                            alert_reason=alert_reason,
                            alert_severity=severity
                        )
                    }
            
            flagged_students = [item["alert"] for item in user_alerts.values()]
            
            # Sort by severity and mastery score
            severity_order = {"high": 0, "medium": 1, "low": 2}
            flagged_students.sort(key=lambda x: (severity_order[x.alert_severity], x.mastery_score))
            
            return flagged_students
            
        except Exception as e:
            print(f"Error getting flagged students: {str(e)}")
            return []
    
    async def get_students(
        self,
        subject: Optional[Subject] = None,
        min_mastery: Optional[float] = None,
        max_mastery: Optional[float] = None,
        active_days: Optional[int] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[StudentOverview]:
        """
        Get list of students with filters
        
        Args:
            subject: Filter by subject
            min_mastery: Minimum mastery score
            max_mastery: Maximum mastery score
            active_days: Filter students active in last N days
            limit: Maximum number of results
            offset: Pagination offset
        
        Returns:
            List of StudentOverview objects
        """
        try:
            # Build query for progress data
            query = self.supabase.table("progress").select("*")
            
            if subject:
                query = query.eq("subject", subject.value)
            
            if min_mastery is not None:
                query = query.gte("mastery_score", min_mastery)
            
            if max_mastery is not None:
                query = query.lte("mastery_score", max_mastery)
            
            if active_days:
                cutoff_date = (datetime.now() - timedelta(days=active_days)).isoformat()
                query = query.gte("last_practiced_at", cutoff_date)
            
            progress_response = query.execute()
            
            # Group by user_id and calculate aggregates
            user_data = {}
            for row in progress_response.data:
                user_id = row["user_id"]
                
                if user_id not in user_data:
                    user_data[user_id] = {
                        "user_id": user_id,
                        "subjects": set(),
                        "mastery_scores": [],
                        "topics_completed": 0,
                        "total_time_minutes": 0,
                        "last_active": None,
                        "max_streak": 0
                    }
                
                user_data[user_id]["subjects"].add(Subject(row["subject"]))
                user_data[user_id]["mastery_scores"].append(Decimal(str(row["mastery_score"])))
                
                if Decimal(str(row["mastery_score"])) >= 80:
                    user_data[user_id]["topics_completed"] += 1
                
                user_data[user_id]["total_time_minutes"] += row.get("total_time_minutes", 0)
                
                if row.get("last_practiced_at"):
                    last_active = datetime.fromisoformat(row["last_practiced_at"])
                    if not user_data[user_id]["last_active"] or last_active > user_data[user_id]["last_active"]:
                        user_data[user_id]["last_active"] = last_active
                
                user_data[user_id]["max_streak"] = max(
                    user_data[user_id]["max_streak"],
                    row.get("streak_days", 0)
                )
            
            # Get test session data for each user
            for user_id in user_data.keys():
                test_sessions = self.supabase.table("test_sessions")\
                    .select("score")\
                    .eq("user_id", user_id)\
                    .eq("is_completed", True)\
                    .execute()
                
                user_data[user_id]["total_test_sessions"] = len(test_sessions.data)
                
                if test_sessions.data:
                    scores = [Decimal(str(s["score"])) for s in test_sessions.data if s.get("score")]
                    user_data[user_id]["average_test_score"] = sum(scores) / len(scores) if scores else None
                else:
                    user_data[user_id]["average_test_score"] = None
            
            # Convert to StudentOverview objects
            students = []
            for user_id, data in user_data.items():
                avg_mastery = sum(data["mastery_scores"]) / len(data["mastery_scores"]) if data["mastery_scores"] else Decimal("0.00")
                is_flagged = avg_mastery < 50
                
                students.append(StudentOverview(
                    user_id=user_id,
                    subjects=list(data["subjects"]),
                    average_mastery_score=avg_mastery.quantize(Decimal("0.01")),
                    total_topics_completed=data["topics_completed"],
                    total_time_minutes=data["total_time_minutes"],
                    total_test_sessions=data["total_test_sessions"],
                    average_test_score=data["average_test_score"].quantize(Decimal("0.01")) if data["average_test_score"] else None,
                    last_active=data["last_active"],
                    streak_days=data["max_streak"],
                    is_flagged=is_flagged,
                    created_at=datetime.now()  # Would need to get from users table
                ))
            
            # Sort by average mastery score (ascending to show struggling students first)
            students.sort(key=lambda x: x.average_mastery_score)
            
            # Apply pagination
            return students[offset:offset + limit]
            
        except Exception as e:
            raise APIException(
                status_code=500,
                detail=f"Failed to fetch students: {str(e)}"
            )
    
    async def get_student_profile(self, student_id: str) -> StudentDetailedProfile:
        """
        Get detailed profile for a specific student
        
        Args:
            student_id: Student user ID
        
        Returns:
            StudentDetailedProfile with comprehensive student data
        """
        try:
            # Get all progress data for student
            progress_response = self.supabase.table("progress")\
                .select("*")\
                .eq("user_id", student_id)\
                .execute()
            
            if not progress_response.data:
                raise APIException(
                    status_code=404,
                    detail=f"Student {student_id} not found"
                )
            
            # Aggregate progress by subject
            progress_by_subject = {}
            topics_completed = []
            total_time_minutes = 0
            max_streak = 0
            last_active = None
            subjects = set()
            achievements = []
            
            for row in progress_response.data:
                subject = row["subject"]
                subjects.add(Subject(subject))
                mastery_score = Decimal(str(row["mastery_score"]))
                
                if subject not in progress_by_subject:
                    progress_by_subject[subject] = {
                        "total_topics": 0,
                        "completed_topics": 0,
                        "average_mastery": Decimal("0.00"),
                        "mastery_scores": []
                    }
                
                progress_by_subject[subject]["total_topics"] += 1
                progress_by_subject[subject]["mastery_scores"].append(mastery_score)
                
                if mastery_score >= 80:
                    progress_by_subject[subject]["completed_topics"] += 1
                    topics_completed.append({
                        "topic_id": row["topic_id"],
                        "subject": subject,
                        "mastery_score": float(mastery_score),
                        "completed_at": row.get("last_practiced_at")
                    })
                
                total_time_minutes += row.get("total_time_minutes", 0)
                max_streak = max(max_streak, row.get("streak_days", 0))
                
                if row.get("last_practiced_at"):
                    practice_time = datetime.fromisoformat(row["last_practiced_at"])
                    if not last_active or practice_time > last_active:
                        last_active = practice_time
                
                # Collect achievements
                if row.get("achievements"):
                    achievements.extend(row["achievements"])
            
            # Calculate average mastery per subject
            for subject_data in progress_by_subject.values():
                if subject_data["mastery_scores"]:
                    subject_data["average_mastery"] = float(
                        (sum(subject_data["mastery_scores"]) / len(subject_data["mastery_scores"])).quantize(Decimal("0.01"))
                    )
                del subject_data["mastery_scores"]  # Remove raw scores from output
            
            # Get test sessions
            test_sessions_response = self.supabase.table("test_sessions")\
                .select("*")\
                .eq("user_id", student_id)\
                .order("start_time", desc=True)\
                .limit(20)\
                .execute()
            
            test_sessions = []
            test_scores = []
            
            for session in test_sessions_response.data:
                test_sessions.append({
                    "id": session["id"],
                    "subject": session["subject"],
                    "start_time": session["start_time"],
                    "end_time": session.get("end_time"),
                    "score": float(session["score"]) if session.get("score") else None,
                    "total_marks": session.get("total_marks"),
                    "is_completed": session.get("is_completed", False)
                })
                
                if session.get("score"):
                    test_scores.append(Decimal(str(session["score"])))
            
            average_test_score = None
            if test_scores:
                average_test_score = (sum(test_scores) / len(test_scores)).quantize(Decimal("0.01"))
            
            return StudentDetailedProfile(
                user_id=student_id,
                subjects=list(subjects),
                progress_by_subject=progress_by_subject,
                topics_completed=topics_completed,
                total_time_minutes=total_time_minutes,
                test_sessions=test_sessions,
                average_test_score=average_test_score,
                last_active=last_active,
                streak_days=max_streak,
                achievements=achievements,
                created_at=datetime.now(),  # Would need to get from users table
                metadata={
                    "total_progress_records": len(progress_response.data),
                    "total_test_sessions": len(test_sessions)
                }
            )
            
        except APIException:
            raise
        except Exception as e:
            raise APIException(
                status_code=500,
                detail=f"Failed to fetch student profile: {str(e)}"
            )
    
    async def export_students_data(
        self,
        subject: Optional[Subject] = None,
        min_mastery: Optional[float] = None,
        max_mastery: Optional[float] = None,
        active_days: Optional[int] = None
    ) -> List[Dict]:
        """
        Export student data for CSV generation
        
        Args:
            subject: Filter by subject
            min_mastery: Minimum mastery score
            max_mastery: Maximum mastery score
            active_days: Filter students active in last N days
        
        Returns:
            List of dictionaries with student export data
        """
        try:
            # Get students with filters
            students = await self.get_students(
                subject=subject,
                min_mastery=min_mastery,
                max_mastery=max_mastery,
                active_days=active_days,
                limit=1000,  # Export up to 1000 students
                offset=0
            )
            
            # Convert to export format
            export_data = []
            for student in students:
                export_data.append({
                    "user_id": student.user_id,
                    "name": student.name or "N/A",
                    "email": student.email or "N/A",
                    "subjects": ", ".join([s.value for s in student.subjects]),
                    "average_mastery_score": float(student.average_mastery_score),
                    "topics_completed": student.total_topics_completed,
                    "total_time_minutes": student.total_time_minutes,
                    "total_test_sessions": student.total_test_sessions,
                    "average_test_score": float(student.average_test_score) if student.average_test_score else None,
                    "last_active": student.last_active.isoformat() if student.last_active else "Never",
                    "streak_days": student.streak_days,
                    "is_flagged": student.is_flagged,
                    "created_at": student.created_at.isoformat()
                })
            
            return export_data
            
        except Exception as e:
            raise APIException(
                status_code=500,
                detail=f"Failed to export student data: {str(e)}"
            )


# Global admin service instance
admin_service = AdminService()
