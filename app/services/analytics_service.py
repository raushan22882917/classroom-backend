"""BigQuery analytics service"""

from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from decimal import Decimal
from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError
from supabase import Client

from app.models.base import Subject
from app.utils.exceptions import APIException
from app.config import settings


class AnalyticsService:
    """Service for BigQuery analytics and event logging"""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.bq_client = None
        self.dataset_id = None
        
        # Try to initialize BigQuery client, but don't fail if credentials are not available
        try:
            if settings.google_cloud_project:
                self.bq_client = bigquery.Client(project=settings.google_cloud_project)
                self.dataset_id = f"{settings.google_cloud_project}.learning_platform_analytics"
        except Exception as e:
            # BigQuery credentials not available - service will work without BigQuery
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"BigQuery not available: {str(e)}. Analytics will work without BigQuery logging.")
            self.bq_client = None
            self.dataset_id = None
    
    def _ensure_dataset_exists(self):
        """Ensure BigQuery dataset exists"""
        if not self.bq_client or not self.dataset_id:
            return
        try:
            self.bq_client.get_dataset(self.dataset_id)
        except GoogleCloudError:
            # Create dataset if it doesn't exist
            dataset = bigquery.Dataset(self.dataset_id)
            dataset.location = "US"
            self.bq_client.create_dataset(dataset, exists_ok=True)
    
    def _ensure_tables_exist(self):
        """Ensure BigQuery tables exist"""
        self._ensure_dataset_exists()
        
        # User events table
        events_schema = [
            bigquery.SchemaField("event_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("event_type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("event_data", "JSON", mode="NULLABLE"),
            bigquery.SchemaField("subject", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("topic_id", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
        ]
        
        events_table_id = f"{self.dataset_id}.user_events"
        events_table = bigquery.Table(events_table_id, schema=events_schema)
        
        # Test results table
        test_results_schema = [
            bigquery.SchemaField("test_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("subject", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("exam_set_id", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("score", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("total_marks", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("duration_minutes", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("questions_attempted", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("correct_answers", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
        ]
        
        test_results_table_id = f"{self.dataset_id}.test_results"
        test_results_table = bigquery.Table(test_results_table_id, schema=test_results_schema)
        
        # Progress snapshots table
        progress_snapshots_schema = [
            bigquery.SchemaField("snapshot_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("subject", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("topic_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("mastery_score", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("questions_attempted", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("correct_answers", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("total_time_minutes", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("streak_days", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
        ]
        
        progress_snapshots_table_id = f"{self.dataset_id}.progress_snapshots"
        progress_snapshots_table = bigquery.Table(progress_snapshots_table_id, schema=progress_snapshots_schema)
        
        # Create tables if they don't exist
        self.bq_client.create_table(events_table, exists_ok=True)
        self.bq_client.create_table(test_results_table, exists_ok=True)
        self.bq_client.create_table(progress_snapshots_table, exists_ok=True)
    
    async def log_event(
        self,
        user_id: str,
        event_type: str,
        event_data: Dict[str, Any] = None,
        subject: Optional[str] = None,
        topic_id: Optional[str] = None
    ):
        """
        Log a user event to BigQuery
        
        Args:
            user_id: User ID
            event_type: Type of event (e.g., 'doubt_asked', 'test_completed', 'video_watched')
            event_data: Additional event data
            subject: Optional subject
            topic_id: Optional topic ID
        """
        if not self.bq_client:
            return  # BigQuery not available, skip logging
        
        try:
            self._ensure_tables_exist()
            
            import uuid
            event_id = str(uuid.uuid4())
            
            rows_to_insert = [{
                "event_id": event_id,
                "user_id": user_id,
                "event_type": event_type,
                "event_data": event_data or {},
                "subject": subject,
                "topic_id": topic_id,
                "timestamp": datetime.utcnow().isoformat()
            }]
            
            table_id = f"{self.dataset_id}.user_events"
            errors = self.bq_client.insert_rows_json(table_id, rows_to_insert)
            
            if errors:
                print(f"BigQuery insert errors: {errors}")
        except Exception as e:
            # Log error but don't fail the request
            print(f"Failed to log event to BigQuery: {str(e)}")
    
    async def log_test_result(
        self,
        test_id: str,
        user_id: str,
        subject: str,
        exam_set_id: Optional[str],
        score: float,
        total_marks: int,
        duration_minutes: int,
        questions_attempted: int,
        correct_answers: int
    ):
        """
        Log a test result to BigQuery
        
        Args:
            test_id: Test session ID
            user_id: User ID
            subject: Subject
            exam_set_id: Exam set ID
            score: Score achieved
            total_marks: Total marks
            duration_minutes: Duration in minutes
            questions_attempted: Questions attempted
            correct_answers: Correct answers
        """
        if not self.bq_client:
            return  # BigQuery not available, skip logging
        
        try:
            self._ensure_tables_exist()
            
            rows_to_insert = [{
                "test_id": test_id,
                "user_id": user_id,
                "subject": subject,
                "exam_set_id": exam_set_id,
                "score": score,
                "total_marks": total_marks,
                "duration_minutes": duration_minutes,
                "questions_attempted": questions_attempted,
                "correct_answers": correct_answers,
                "timestamp": datetime.utcnow().isoformat()
            }]
            
            table_id = f"{self.dataset_id}.test_results"
            errors = self.bq_client.insert_rows_json(table_id, rows_to_insert)
            
            if errors:
                print(f"BigQuery insert errors: {errors}")
        except Exception as e:
            print(f"Failed to log test result to BigQuery: {str(e)}")
    
    async def log_progress_snapshot(
        self,
        user_id: str,
        subject: str,
        topic_id: str,
        mastery_score: float,
        questions_attempted: int,
        correct_answers: int,
        total_time_minutes: int,
        streak_days: int
    ):
        """
        Log a progress snapshot to BigQuery
        
        Args:
            user_id: User ID
            subject: Subject
            topic_id: Topic ID
            mastery_score: Mastery score
            questions_attempted: Questions attempted
            correct_answers: Correct answers
            total_time_minutes: Total time in minutes
            streak_days: Streak days
        """
        if not self.bq_client:
            return  # BigQuery not available, skip logging
        
        try:
            self._ensure_tables_exist()
            
            import uuid
            snapshot_id = str(uuid.uuid4())
            
            rows_to_insert = [{
                "snapshot_id": snapshot_id,
                "user_id": user_id,
                "subject": subject,
                "topic_id": topic_id,
                "mastery_score": mastery_score,
                "questions_attempted": questions_attempted,
                "correct_answers": correct_answers,
                "total_time_minutes": total_time_minutes,
                "streak_days": streak_days,
                "timestamp": datetime.utcnow().isoformat()
            }]
            
            table_id = f"{self.dataset_id}.progress_snapshots"
            errors = self.bq_client.insert_rows_json(table_id, rows_to_insert)
            
            if errors:
                print(f"BigQuery insert errors: {errors}")
        except Exception as e:
            print(f"Failed to log progress snapshot to BigQuery: {str(e)}")
    
    async def get_admin_dashboard_metrics(self) -> Dict[str, Any]:
        """
        Get aggregate metrics for admin dashboard
        
        Returns:
            Dictionary with dashboard metrics
        """
        try:
            # Get active students count (students who practiced in last 7 days)
            seven_days_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
            
            active_students_response = self.supabase.table("progress").select(
                "user_id"
            ).gte("last_practiced_at", seven_days_ago).execute()
            
            active_students = len(set(record["user_id"] for record in active_students_response.data))
            
            # Get average mastery score
            all_progress_response = self.supabase.table("progress").select(
                "mastery_score"
            ).execute()
            
            if all_progress_response.data:
                avg_mastery = sum(
                    float(record["mastery_score"]) for record in all_progress_response.data
                ) / len(all_progress_response.data)
            else:
                avg_mastery = 0.0
            
            # Get completion rate (topics with mastery >= 80%)
            completed_topics = sum(
                1 for record in all_progress_response.data
                if float(record["mastery_score"]) >= 80
            )
            total_topics = len(all_progress_response.data)
            completion_rate = (completed_topics / total_topics * 100) if total_topics > 0 else 0.0
            
            # Get flagged students (mastery < 50%)
            flagged_students_response = self.supabase.table("progress").select(
                "user_id, subject, topic_id, mastery_score"
            ).lt("mastery_score", 50).execute()
            
            flagged_students = {}
            for record in flagged_students_response.data:
                user_id = record["user_id"]
                if user_id not in flagged_students:
                    flagged_students[user_id] = {
                        "user_id": user_id,
                        "struggling_topics": []
                    }
                
                flagged_students[user_id]["struggling_topics"].append({
                    "subject": record["subject"],
                    "topic_id": record["topic_id"],
                    "mastery_score": float(record["mastery_score"])
                })
            
            return {
                "active_students": active_students,
                "avg_mastery_score": round(avg_mastery, 2),
                "completion_rate": round(completion_rate, 2),
                "flagged_students_count": len(flagged_students),
                "flagged_students": list(flagged_students.values())
            }
        except Exception as e:
            raise APIException(
                code="DASHBOARD_METRICS_ERROR",
                message=f"Failed to get dashboard metrics: {str(e)}",
                status_code=500
            )
    
    async def get_student_analytics(self, student_id: str) -> Dict[str, Any]:
        """
        Get detailed analytics for a specific student
        
        Args:
            student_id: Student user ID
            
        Returns:
            Dictionary with student analytics
        """
        try:
            # Get progress data
            progress_response = self.supabase.table("progress").select("*").eq(
                "user_id", student_id
            ).execute()
            
            # Get test results
            test_results_response = self.supabase.table("test_sessions").select("*").eq(
                "user_id", student_id
            ).eq("is_completed", True).execute()
            
            # Calculate statistics
            total_topics = len(progress_response.data)
            
            if progress_response.data:
                avg_mastery = sum(
                    float(record["mastery_score"]) for record in progress_response.data
                ) / total_topics
                total_time = sum(record["total_time_minutes"] for record in progress_response.data)
                max_streak = max(record["streak_days"] for record in progress_response.data)
            else:
                avg_mastery = 0.0
                total_time = 0
                max_streak = 0
            
            # Group by subject
            subjects = {}
            for record in progress_response.data:
                subject = record["subject"]
                if subject not in subjects:
                    subjects[subject] = {
                        "topics_count": 0,
                        "avg_mastery_score": 0.0,
                        "total_time_minutes": 0
                    }
                
                subjects[subject]["topics_count"] += 1
                subjects[subject]["avg_mastery_score"] += float(record["mastery_score"])
                subjects[subject]["total_time_minutes"] += record["total_time_minutes"]
            
            for subject in subjects:
                count = subjects[subject]["topics_count"]
                subjects[subject]["avg_mastery_score"] = round(
                    subjects[subject]["avg_mastery_score"] / count, 2
                )
            
            # Test performance
            test_count = len(test_results_response.data)
            if test_results_response.data:
                avg_test_score = sum(
                    float(record["score"]) for record in test_results_response.data
                ) / test_count
            else:
                avg_test_score = 0.0
            
            return {
                "student_id": student_id,
                "total_topics": total_topics,
                "avg_mastery_score": round(avg_mastery, 2),
                "total_time_minutes": total_time,
                "max_streak": max_streak,
                "subjects": subjects,
                "test_count": test_count,
                "avg_test_score": round(avg_test_score, 2),
                "recent_tests": test_results_response.data[:5]  # Last 5 tests
            }
        except Exception as e:
            raise APIException(
                code="STUDENT_ANALYTICS_ERROR",
                message=f"Failed to get student analytics: {str(e)}",
                status_code=500
            )
    
    async def get_performance_trends(
        self,
        user_id: Optional[str] = None,
        subject: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get performance trends over time
        
        Args:
            user_id: Optional user ID filter
            subject: Optional subject filter
            days: Number of days to look back
            
        Returns:
            Dictionary with trend data
        """
        if not self.bq_client:
            # BigQuery not available, return empty trends
            return {
                "period_days": days,
                "user_id": user_id,
                "subject": subject,
                "trends": []
            }
        
        try:
            self._ensure_tables_exist()
            
            # Build query for progress snapshots
            start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            query = f"""
                SELECT
                    DATE(timestamp) as date,
                    AVG(mastery_score) as avg_mastery,
                    SUM(questions_attempted) as total_questions,
                    SUM(correct_answers) as total_correct,
                    COUNT(DISTINCT user_id) as active_users
                FROM `{self.dataset_id}.progress_snapshots`
                WHERE timestamp >= @start_date
            """
            
            params = [
                bigquery.ScalarQueryParameter("start_date", "TIMESTAMP", start_date)
            ]
            
            if user_id:
                query += " AND user_id = @user_id"
                params.append(bigquery.ScalarQueryParameter("user_id", "STRING", user_id))
            
            if subject:
                query += " AND subject = @subject"
                params.append(bigquery.ScalarQueryParameter("subject", "STRING", subject))
            
            query += " GROUP BY date ORDER BY date"
            
            job_config = bigquery.QueryJobConfig(query_parameters=params)
            query_job = self.bq_client.query(query, job_config=job_config)
            results = query_job.result()
            
            trends = []
            for row in results:
                trends.append({
                    "date": row.date.isoformat(),
                    "avg_mastery": round(row.avg_mastery, 2),
                    "total_questions": row.total_questions,
                    "total_correct": row.total_correct,
                    "active_users": row.active_users
                })
            
            return {
                "period_days": days,
                "user_id": user_id,
                "subject": subject,
                "trends": trends
            }
        except Exception as e:
            # If BigQuery fails, return empty trends
            print(f"Failed to get performance trends: {str(e)}")
            return {
                "period_days": days,
                "user_id": user_id,
                "subject": subject,
                "trends": []
            }
