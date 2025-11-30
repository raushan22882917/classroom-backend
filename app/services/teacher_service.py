"""Teacher time-savers service for lesson planning, assessments, and parent communication"""

from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
import json
import re
import google.generativeai as genai
from supabase import Client
from app.config import settings
from app.models.base import Subject
from app.utils.exceptions import APIException

# Configure Gemini
genai.configure(api_key=settings.gemini_api_key)


class TeacherService:
    """Service for teacher time-saving features"""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        # Initialize Gemini model - use flash for speed, fallback to pro
        try:
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        except:
            try:
                self.model = genai.GenerativeModel('gemini-3-pro-preview')
            except:
                self.model = genai.GenerativeModel('gemini-pro')
    
    async def generate_lesson_plan(
        self,
        teacher_id: str,
        subject: Subject,
        topic: str,
        duration_minutes: int = 45,
        class_grade: int = 12,
        learning_objectives: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate lesson plan for a topic
        
        Args:
            teacher_id: Teacher user ID
            subject: Subject area
            topic: Topic to create lesson plan for
            duration_minutes: Duration of the lesson
            class_grade: Class grade level
            learning_objectives: Optional learning objectives
        
        Returns:
            Complete lesson plan with activities, assessments, and resources
        """
        try:
            # Get topic content if available
            topics_response = self.supabase.table('topics').select('*').eq('subject', subject.value).ilike('name', f'%{topic}%').limit(1).execute()
            topic_data = topics_response.data[0] if topics_response.data else None
            
            prompt = f"""Create a comprehensive lesson plan for Class {class_grade} {subject.value}.

Topic: {topic}
Duration: {duration_minutes} minutes
{f"Learning Objectives: {', '.join(learning_objectives)}" if learning_objectives else ""}

Create a detailed lesson plan with:
1. Learning objectives
2. Introduction/hook activity
3. Main content delivery (with timing)
4. Interactive activities
5. Formative assessment questions
6. Summary and closure
7. Homework/assignment suggestions
8. Differentiation strategies for different learning levels

Format as JSON:
{{
  "topic": "{topic}",
  "subject": "{subject.value}",
  "duration_minutes": {duration_minutes},
  "learning_objectives": ["obj1", "obj2"],
  "introduction": {{"activity": "...", "duration_minutes": 5}},
  "main_content": [
    {{"section": "...", "duration_minutes": 10, "activity": "...", "materials": ["..."]}}
  ],
  "interactive_activities": [
    {{"name": "...", "duration_minutes": 10, "description": "..."}}
  ],
  "formative_assessments": [
    {{"question": "...", "type": "multiple_choice|short_answer", "answer": "..."}}
  ],
  "summary": "...",
  "homework": "...",
  "differentiation": {{
    "struggling_students": "...",
    "advanced_students": "..."
  }}
}}"""

            response = self.model.generate_content(prompt)
            plan_text = response.text
            
            # Parse JSON response
            json_match = re.search(r'\{.*\}', plan_text, re.DOTALL)
            if json_match:
                plan_data = json.loads(json_match.group())
            else:
                raise APIException(
                    code="LESSON_PLAN_PARSING_ERROR",
                    message="Failed to parse lesson plan response",
                    status_code=500
                )
            
            return {
                'teacher_id': teacher_id,
                'subject': subject.value,
                'topic': topic,
                'lesson_plan': plan_data,
                'created_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise APIException(
                code="LESSON_PLAN_ERROR",
                message=f"Failed to generate lesson plan: {str(e)}",
                status_code=500
            )
    
    async def create_formative_assessment(
        self,
        teacher_id: str,
        subject: Subject,
        topic: str,
        question_count: int = 5,
        difficulty_levels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate formative assessment questions
        
        Args:
            teacher_id: Teacher user ID
            subject: Subject area
            topic: Topic for assessment
            question_count: Number of questions
            difficulty_levels: List of difficulty levels (easy, medium, hard)
        
        Returns:
            Assessment with questions, answers, and rubrics
        """
        try:
            if not difficulty_levels:
                difficulty_levels = ['easy', 'medium', 'hard']
            
            prompt = f"""Create a formative assessment for Class 12 {subject.value} on topic: {topic}

Number of questions: {question_count}
Difficulty levels: {', '.join(difficulty_levels)}

Create questions that:
1. Assess understanding of key concepts
2. Include various question types (multiple choice, short answer, problem-solving)
3. Have clear rubrics for grading
4. Include answer keys with explanations

Format as JSON:
{{
  "topic": "{topic}",
  "subject": "{subject.value}",
  "questions": [
    {{
      "question_number": 1,
      "question": "...",
      "type": "multiple_choice|short_answer|problem_solving",
      "difficulty": "easy|medium|hard",
      "options": ["A", "B", "C", "D"],  // if multiple choice
      "correct_answer": "...",
      "explanation": "...",
      "rubric": {{"points": 2, "criteria": "..."}},
      "learning_objective": "..."
    }}
  ],
  "total_points": 10,
  "estimated_time_minutes": 15
}}"""

            response = self.model.generate_content(prompt)
            assessment_text = response.text
            
            # Parse JSON response
            json_match = re.search(r'\{.*\}', assessment_text, re.DOTALL)
            if json_match:
                assessment_data = json.loads(json_match.group())
            else:
                raise APIException(
                    code="ASSESSMENT_PARSING_ERROR",
                    message="Failed to parse assessment response",
                    status_code=500
                )
            
            return {
                'teacher_id': teacher_id,
                'subject': subject.value,
                'topic': topic,
                'assessment': assessment_data,
                'created_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise APIException(
                code="ASSESSMENT_ERROR",
                message=f"Failed to create assessment: {str(e)}",
                status_code=500
            )
    
    async def generate_parent_message(
        self,
        teacher_id: str,
        student_id: str,
        message_type: str,
        subject: Optional[Subject] = None,
        custom_content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate parent communication message
        
        Args:
            teacher_id: Teacher user ID
            student_id: Student user ID
            message_type: Type of message (progress_update, concern, achievement, general)
            subject: Optional subject for subject-specific updates
            custom_content: Optional custom content to include
        
        Returns:
            Formatted message ready to send
        """
        try:
            # Get student information - use separate queries to avoid RLS issues
            try:
                student_profile_response = self.supabase.table('student_profiles').select('*').eq('user_id', student_id).limit(1).execute()
                student_profile_data = student_profile_response.data[0] if student_profile_response.data and len(student_profile_response.data) > 0 else None
            except Exception as e:
                print(f"Warning: Could not fetch student profile: {str(e)}")
                student_profile_data = None
            
            # Get profile separately
            profile_data = None
            if student_profile_data:
                try:
                    profile_response = self.supabase.table('profiles').select('*').eq('user_id', student_id).limit(1).execute()
                    profile_data = profile_response.data[0] if profile_response.data and len(profile_response.data) > 0 else None
                except Exception as e:
                    print(f"Warning: Could not fetch profile: {str(e)}")
                    profile_data = None
            
            student_data = {
                **student_profile_data,
                'profiles': profile_data
            } if student_profile_data else None
            
            # Get student progress if subject provided
            progress_data = None
            if subject:
                try:
                    progress_response = self.supabase.table('progress').select('*').eq('user_id', student_id).eq('subject', subject.value).limit(5).execute()
                    progress_data = progress_response.data or []
                    
                    # Get topic names separately if needed
                    if progress_data:
                        topic_ids = [p.get('topic_id') for p in progress_data if p.get('topic_id')]
                        if topic_ids:
                            topics_response = self.supabase.table('topics').select('id, name').in_('id', topic_ids).execute()
                            topics_map = {t['id']: t['name'] for t in (topics_response.data or [])}
                            for p in progress_data:
                                p['topics'] = {'name': topics_map.get(p.get('topic_id'))}
                except Exception as e:
                    # If progress query fails, continue without progress data
                    print(f"Warning: Could not fetch progress data: {str(e)}")
                    progress_data = []
            
            # Get student name safely
            student_name = 'Student'
            if student_data:
                if isinstance(student_data.get('profiles'), dict):
                    student_name = student_data.get('profiles', {}).get('full_name', 'Student')
                elif isinstance(student_data.get('profiles'), list) and len(student_data.get('profiles', [])) > 0:
                    student_name = student_data.get('profiles', [])[0].get('full_name', 'Student')
            
            # Format progress data safely
            progress_text = ""
            if progress_data:
                try:
                    progress_list = []
                    for p in progress_data[:3]:
                        topic_name = 'Unknown Topic'
                        if isinstance(p.get('topics'), dict):
                            topic_name = p.get('topics', {}).get('name', 'Unknown Topic')
                        progress_list.append({
                            'topic': topic_name,
                            'mastery': p.get('mastery_score', 0)
                        })
                    progress_text = f"\nStudent Progress: {json.dumps(progress_list, indent=2)}"
                except Exception as e:
                    print(f"Warning: Could not format progress data: {str(e)}")
            
            prompt = f"""Generate a professional, warm parent communication message.

Message Type: {message_type}
Student Name: {student_name}
{f"Subject: {subject.value}" if subject else ""}

{f"Custom Content: {custom_content}" if custom_content else ""}
{progress_text}

Create a message that is:
1. Professional yet warm and personal
2. Clear and concise
3. Actionable (if needed)
4. Encouraging and supportive
5. Appropriate for the message type

Format as JSON:
{{
  "subject": "Message Subject Line",
  "greeting": "Dear [Parent Name],",
  "body": "Main message content...",
  "key_points": ["point1", "point2"],
  "action_items": ["item1", "item2"],  // if applicable
  "closing": "Warm regards, [Teacher Name]",
  "suggested_follow_up": "..."  // if applicable
}}"""

            response = self.model.generate_content(prompt)
            message_text = response.text
            
            # Parse JSON response
            json_match = re.search(r'\{.*\}', message_text, re.DOTALL)
            if json_match:
                message_data = json.loads(json_match.group())
            else:
                # Get student name safely for fallback
                student_name = 'your child'
                if student_data:
                    if isinstance(student_data.get('profiles'), dict):
                        student_name = student_data.get('profiles', {}).get('full_name', 'your child')
                    elif isinstance(student_data.get('profiles'), list) and len(student_data.get('profiles', [])) > 0:
                        student_name = student_data.get('profiles', [])[0].get('full_name', 'your child')
                
                message_data = {
                    'subject': f'Update on {student_name}',
                    'body': message_text,
                    'greeting': 'Dear Parent,',
                    'closing': 'Best regards'
                }
            
            return {
                'teacher_id': teacher_id,
                'student_id': student_id,
                'message_type': message_type,
                'message': message_data,
                'created_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise APIException(
                code="PARENT_MESSAGE_ERROR",
                message=f"Failed to generate parent message: {str(e)}",
                status_code=500
            )

