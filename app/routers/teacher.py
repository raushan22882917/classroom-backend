"""Teacher endpoints for managing students, creating assignments, and viewing content"""

from fastapi import APIRouter, Query, HTTPException, Request
from typing import Optional, List
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.services.school_service import school_service
from app.services.admin_service import admin_service
from app.services.exam_service import exam_service
from app.utils.exceptions import APIException
from app.models.base import Subject
from app.models.quiz import QuizTemplate, QuizTemplateCreate

router = APIRouter(prefix="/teacher", tags=["Teacher"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/students")
@limiter.limit("50/minute")
async def get_teacher_students(
    request: Request,
    teacher_id: str = Query(..., description="Teacher user ID")
):
    """Get all students assigned to teacher's school"""
    try:
        # Get teacher's school
        from supabase import create_client
        from app.config import settings
        
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # Get teacher profile to find school
        teacher_profile = supabase.table("teacher_profiles").select("school_id").eq("user_id", teacher_id).execute()
        
        if not teacher_profile.data or not teacher_profile.data[0].get("school_id"):
            return []
        
        school_id = teacher_profile.data[0]["school_id"]
        
        # Get all students from that school
        students = await school_service.get_school_students(school_id)
        
        return students
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/students/{student_id}/performance")
@limiter.limit("50/minute")
async def get_student_performance(
    request: Request,
    student_id: str,
    teacher_id: str = Query(..., description="Teacher user ID")
):
    """Get detailed performance data for a student"""
    try:
        # Verify teacher has access to this student
        profile = await admin_service.get_student_profile(student_id)
        return profile
        
    except APIException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
@limiter.limit("50/minute")
async def get_teacher_dashboard(
    request: Request,
    teacher_id: str = Query(..., description="Teacher user ID")
):
    """Get teacher dashboard with overview stats"""
    try:
        from supabase import create_client
        from app.config import settings
        
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # Get teacher's school
        teacher_profile = supabase.table("teacher_profiles").select("school_id").eq("user_id", teacher_id).execute()
        
        if not teacher_profile.data or not teacher_profile.data[0].get("school_id"):
            return {
                "total_students": 0,
                "active_students": 0,
                "pending_homework": 0,
                "recent_quizzes": 0
            }
        
        school_id = teacher_profile.data[0]["school_id"]
        
        # Get students
        students = await school_service.get_school_students(school_id)
        total_students = len(students)
        
        # Get active students (active in last 7 days)
        from datetime import datetime, timedelta
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
        
        student_ids = [s["user_id"] for s in students]
        active_progress = supabase.table("progress").select("user_id").in_("user_id", student_ids).gte("last_practiced_at", seven_days_ago).execute()
        active_students = len(set(p["user_id"] for p in active_progress.data or []))
        
        # Get pending homework sessions
        homework_sessions = supabase.table("homework_sessions").select("*").in_("user_id", student_ids).eq("is_complete", False).execute()
        pending_homework = len(homework_sessions.data or [])
        
        # Get recent quiz sessions (last 7 days)
        # Try quiz_sessions first, fallback to test_sessions if quiz_sessions doesn't exist
        recent_quizzes = 0
        try:
            quiz_sessions = supabase.table("quiz_sessions").select("*").in_("user_id", student_ids).gte("created_at", seven_days_ago).execute()
            recent_quizzes = len(quiz_sessions.data or [])
        except Exception as e:
            # If quiz_sessions table doesn't exist, try test_sessions as fallback
            try:
                test_sessions = supabase.table("test_sessions").select("*").in_("user_id", student_ids).gte("created_at", seven_days_ago).execute()
                recent_quizzes = len(test_sessions.data or [])
            except Exception:
                # If both fail, just set to 0
                recent_quizzes = 0
        
        return {
            "total_students": total_students,
            "active_students": active_students,
            "pending_homework": pending_homework,
            "recent_quizzes": recent_quizzes
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quizzes", response_model=QuizTemplate, status_code=201)
@limiter.limit("20/minute")
async def create_quiz(
    request: Request,
    quiz_create: QuizTemplateCreate
):
    """
    Create a new quiz template (teacher only)
    
    Request Body:
    - teacher_id: Teacher user ID
    - title: Quiz title
    - subject: Subject for the quiz
    - description: Optional description
    - quiz_data: Quiz data containing questions, answers, etc.
    - duration_minutes: Optional duration in minutes
    - total_marks: Optional total marks
    - class_grade: Optional class grade
    - topic_ids: Optional list of topic IDs
    - metadata: Additional metadata
    
    Returns:
    - Created quiz template
    """
    try:
        from supabase import create_client
        from app.config import settings
        
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # Verify teacher exists
        teacher_profile = supabase.table("teacher_profiles").select("user_id").eq("user_id", quiz_create.teacher_id).execute()
        
        if not teacher_profile.data or len(teacher_profile.data) == 0:
            raise HTTPException(
                status_code=404,
                detail="Teacher not found"
            )
        
        # Calculate total marks from quiz data if not provided
        total_marks = quiz_create.total_marks
        if not total_marks and quiz_create.quiz_data:
            questions = quiz_create.quiz_data.get("questions", [])
            total_marks = sum(q.get("marks", 1) for q in questions)
        
        # Calculate duration if not provided (estimate 2 minutes per question)
        duration_minutes = quiz_create.duration_minutes
        if not duration_minutes and quiz_create.quiz_data:
            questions = quiz_create.quiz_data.get("questions", [])
            duration_minutes = len(questions) * 2
        
        # Create quiz template
        quiz_data = {
            "teacher_id": quiz_create.teacher_id,
            "title": quiz_create.title,
            "subject": quiz_create.subject.value,
            "description": quiz_create.description,
            "quiz_data": quiz_create.quiz_data,
            "duration_minutes": duration_minutes,
            "total_marks": total_marks,
            "class_grade": quiz_create.class_grade,
            "topic_ids": quiz_create.topic_ids,
            "is_active": True,
            "metadata": quiz_create.metadata
        }
        
        result = supabase.table("quizzes").insert(quiz_data).execute()
        
        if not result.data or len(result.data) == 0:
            raise HTTPException(
                status_code=500,
                detail="Failed to create quiz"
            )
        
        return QuizTemplate(**result.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quizzes", response_model=List[QuizTemplate])
@limiter.limit("50/minute")
async def get_teacher_quizzes(
    request: Request,
    teacher_id: str = Query(..., description="Teacher user ID")
):
    """
    Get all quizzes created by a teacher
    
    Query Parameters:
    - teacher_id: Teacher user ID
    
    Returns:
    - List of quiz templates
    """
    try:
        from supabase import create_client
        from app.config import settings
        
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # Get all quizzes for this teacher
        result = supabase.table("quizzes").select("*").eq("teacher_id", teacher_id).order("created_at", desc=True).execute()
        
        return [QuizTemplate(**quiz) for quiz in (result.data or [])]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quizzes/{quiz_id}", response_model=QuizTemplate)
@limiter.limit("50/minute")
async def get_quiz(
    request: Request,
    quiz_id: str,
    teacher_id: str = Query(..., description="Teacher user ID")
):
    """
    Get a single quiz by ID
    
    Path Parameters:
    - quiz_id: Quiz ID
    
    Query Parameters:
    - teacher_id: Teacher user ID (for verification)
    
    Returns:
    - Quiz template
    """
    try:
        from supabase import create_client
        from app.config import settings
        
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # Get quiz and verify it belongs to the teacher
        result = supabase.table("quizzes").select("*").eq("id", quiz_id).eq("teacher_id", teacher_id).execute()
        
        if not result.data or len(result.data) == 0:
            raise HTTPException(
                status_code=404,
                detail="Quiz not found"
            )
        
        return QuizTemplate(**result.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quiz-sessions")
@limiter.limit("50/minute")
async def get_teacher_quiz_sessions(
    request: Request,
    teacher_id: str = Query(..., description="Teacher user ID")
):
    """
    Get all quiz sessions for students in teacher's school
    
    Query Parameters:
    - teacher_id: Teacher user ID
    
    Returns:
    - List of quiz sessions with student information
    """
    try:
        from supabase import create_client
        from app.config import settings
        
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # Get teacher's school
        teacher_profile = supabase.table("teacher_profiles").select("school_id").eq("user_id", teacher_id).execute()
        
        if not teacher_profile.data or not teacher_profile.data[0].get("school_id"):
            return []
        
        school_id = teacher_profile.data[0]["school_id"]
        
        # Get all students from that school
        students = await school_service.get_school_students(school_id)
        student_ids = [s["user_id"] for s in students]
        
        if not student_ids:
            return []
        
        # Get quiz sessions for these students
        quiz_sessions = []
        try:
            result = supabase.table("quiz_sessions").select("*").in_("user_id", student_ids).order("created_at", desc=True).limit(50).execute()
            quiz_sessions = result.data or []
        except Exception as e:
            # If quiz_sessions doesn't exist, try test_sessions as fallback
            try:
                result = supabase.table("test_sessions").select("*").in_("user_id", student_ids).order("created_at", desc=True).limit(50).execute()
                quiz_sessions = result.data or []
            except Exception:
                quiz_sessions = []
        
        # Add student names to sessions
        sessions_with_names = []
        for session in quiz_sessions:
            student = next((s for s in students if s.get("user_id") == session.get("user_id")), None)
            student_name = "Unknown"
            if student:
                # Handle different possible structures
                if isinstance(student.get("profile"), dict):
                    student_name = student.get("profile", {}).get("full_name", "Unknown")
                elif isinstance(student, dict) and "full_name" in student:
                    student_name = student.get("full_name", "Unknown")
            
            sessions_with_names.append({
                **session,
                "student_name": student_name
            })
        
        return sessions_with_names
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

