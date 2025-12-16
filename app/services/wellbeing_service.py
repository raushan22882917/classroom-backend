"""Well-being and focus service for time-boxing, motivation, and distraction management"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import google.generativeai as genai
from supabase import Client
from app.config import settings
from app.models.base import Subject
from app.utils.exceptions import APIException

# Configure Gemini
genai.configure(api_key=settings.gemini_api_key)


class WellbeingService:
    """Service for student well-being and focus features"""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        # Use gemini-2.5-flash (fastest and most capable) or fallback to older models
        try:
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        except:
            try:
                self.model = genai.GenerativeModel('gemini-1.5-flash')
            except:
                self.model = genai.GenerativeModel('gemini-pro')
    
    async def start_focus_session(
        self,
        user_id: str,
        duration_minutes: int,
        subject: Optional[Subject] = None,
        goal: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Start a focused study session with time-boxing
        
        Args:
            user_id: Student user ID
            duration_minutes: Duration of focus session
            subject: Optional subject for the session
            goal: Optional learning goal
        
        Returns:
            Focus session details
        """
        try:
            session_data = {
                'user_id': user_id,
                'duration_minutes': duration_minutes,
                'subject': subject.value if subject else None,
                'goal': goal,
                'start_time': datetime.utcnow().isoformat(),
                'end_time': (datetime.utcnow() + timedelta(minutes=duration_minutes)).isoformat(),
                'status': 'active',
                'distractions_blocked': 0
            }
            
            # Insert into database
            response = self.supabase.table('focus_sessions').insert(session_data).execute()
            
            return {
                'session_id': response.data[0]['id'],
                **session_data
            }
        except Exception as e:
            raise APIException(
                code="FOCUS_SESSION_ERROR",
                message=f"Failed to start focus session: {str(e)}",
                status_code=500
            )
    
    async def end_focus_session(
        self,
        session_id: str,
        user_id: str,
        distractions_count: int = 0,
        completed: bool = True
    ) -> Dict[str, Any]:
        """
        End a focus session and get summary
        
        Args:
            session_id: Focus session ID
            user_id: Student user ID
            distractions_count: Number of distractions encountered
            completed: Whether session was completed
        
        Returns:
            Session summary with achievements
        """
        try:
            # Get session
            session_response = self.supabase.table('focus_sessions').select('*').eq('id', session_id).eq('user_id', user_id).execute()
            if not session_response.data:
                raise APIException(
                    code="SESSION_NOT_FOUND",
                    message="Focus session not found",
                    status_code=404
                )
            
            session = session_response.data[0]
            start_time = datetime.fromisoformat(session['start_time'].replace('Z', '+00:00'))
            end_time = datetime.utcnow()
            actual_duration = (end_time - start_time).total_seconds() / 60
            
            # Update session
            update_data = {
                'status': 'completed' if completed else 'interrupted',
                'actual_duration_minutes': actual_duration,
                'distractions_blocked': distractions_count,
                'end_time': end_time.isoformat()
            }
            
            self.supabase.table('focus_sessions').update(update_data).eq('id', session_id).execute()
            
            # Generate motivational message
            motivation = await self._generate_motivation_message(
                user_id,
                actual_duration,
                session.get('duration_minutes'),
                completed,
                distractions_count
            )
            
            return {
                'session_id': session_id,
                'duration_minutes': actual_duration,
                'planned_duration_minutes': session.get('duration_minutes'),
                'completed': completed,
                'distractions_blocked': distractions_count,
                'motivation': motivation,
                'achievements': await self._check_achievements(user_id, actual_duration, completed)
            }
        except Exception as e:
            raise APIException(
                code="FOCUS_SESSION_END_ERROR",
                message=f"Failed to end focus session: {str(e)}",
                status_code=500
            )
    
    async def get_motivation_message(
        self,
        user_id: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get personalized motivation message
        
        Args:
            user_id: Student user ID
            context: Optional context (e.g., 'struggling', 'achievement', 'daily_checkin')
        
        Returns:
            Motivational message and tips
        """
        try:
            # Get student progress
            progress_response = self.supabase.table('progress').select('*').eq('user_id', user_id).execute()
            streak = progress_response.data[0].get('streak_days', 0) if progress_response.data else 0
            
            # Get recent focus sessions
            sessions_response = self.supabase.table('focus_sessions').select('*').eq('user_id', user_id).order('start_time', desc=True).limit(7).execute()
            recent_sessions = sessions_response.data
            
            prompt = f"""Generate a personalized motivational message for a Class 12 student.

Context: {context or 'general encouragement'}
Current streak: {streak} days
Recent study sessions: {len(recent_sessions)} sessions this week

Create a message that:
1. Acknowledges their effort and progress
2. Provides encouragement
3. Includes a study tip or strategy
4. Is warm and supportive

Format as JSON:
{{
  "message": "Main motivational message...",
  "encouragement": "Specific encouragement...",
  "study_tip": "Practical tip...",
  "quote": "Inspirational quote (optional)",
  "next_steps": ["suggestion1", "suggestion2"]
}}"""

            response = self.model.generate_content(prompt)
            message_text = response.text
            
            # Parse JSON response
            import json
            import re
            json_match = re.search(r'\{.*\}', message_text, re.DOTALL)
            if json_match:
                motivation_data = json.loads(json_match.group())
            else:
                motivation_data = {
                    'message': message_text,
                    'encouragement': 'Keep up the great work!',
                    'study_tip': 'Take regular breaks to maintain focus',
                    'next_steps': []
                }
            
            return {
                'user_id': user_id,
                'motivation': motivation_data,
                'streak_days': streak,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            raise APIException(
                code="MOTIVATION_ERROR",
                message=f"Failed to generate motivation: {str(e)}",
                status_code=500
            )
    
    async def get_distraction_guard_settings(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get distraction guard settings for user
        
        Args:
            user_id: Student user ID
        
        Returns:
            Distraction guard settings
        """
        try:
            # Get or create settings
            settings_response = self.supabase.table('user_settings').select('*').eq('user_id', user_id).eq('setting_type', 'distraction_guard').execute()
            
            if settings_response.data:
                return settings_response.data[0].get('settings', {})
            else:
                # Default settings
                default_settings = {
                    'block_social_media': True,
                    'block_entertainment': True,
                    'allow_emergency_calls': True,
                    'focus_mode_enabled': False,
                    'break_reminders': True,
                    'break_interval_minutes': 25
                }
                return default_settings
        except Exception as e:
            raise APIException(
                code="SETTINGS_ERROR",
                message=f"Failed to get distraction guard settings: {str(e)}",
                status_code=500
            )
    
    async def update_distraction_guard_settings(
        self,
        user_id: str,
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update distraction guard settings
        
        Args:
            user_id: Student user ID
            settings: Settings to update
        
        Returns:
            Updated settings
        """
        try:
            # Upsert settings
            settings_data = {
                'user_id': user_id,
                'setting_type': 'distraction_guard',
                'settings': settings,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            response = self.supabase.table('user_settings').upsert(settings_data, on_conflict='user_id,setting_type').execute()
            return response.data[0] if response.data else settings_data
        except Exception as e:
            raise APIException(
                code="SETTINGS_UPDATE_ERROR",
                message=f"Failed to update settings: {str(e)}",
                status_code=500
            )
    
    async def _generate_motivation_message(
        self,
        user_id: str,
        actual_duration: float,
        planned_duration: float,
        completed: bool,
        distractions: int
    ) -> Dict[str, Any]:
        """Generate motivation message for completed session"""
        completion_rate = (actual_duration / planned_duration * 100) if planned_duration > 0 else 0
        
        if completed and completion_rate >= 90:
            return {
                'type': 'achievement',
                'message': f'Great job! You completed your {planned_duration}-minute focus session!',
                'encouragement': 'Your dedication is paying off. Keep up the excellent work!'
            }
        elif completed:
            return {
                'type': 'encouragement',
                'message': f'You completed {actual_duration:.0f} minutes of focused study!',
                'encouragement': 'Every minute counts. Well done!'
            }
        else:
            return {
                'type': 'support',
                'message': 'It\'s okay to take breaks. You can always start a new session!',
                'encouragement': 'Remember: progress, not perfection.'
            }
    
    async def _check_achievements(
        self,
        user_id: str,
        duration: float,
        completed: bool
    ) -> List[str]:
        """Check for new achievements"""
        achievements = []
        
        # Check for focus milestones
        sessions_response = self.supabase.table('focus_sessions').select('*').eq('user_id', user_id).eq('status', 'completed').execute()
        total_sessions = len(sessions_response.data)
        
        if total_sessions == 1:
            achievements.append('first_focus_session')
        elif total_sessions == 10:
            achievements.append('focus_master_10')
        elif total_sessions == 50:
            achievements.append('focus_master_50')
        
        # Check for duration achievements
        if duration >= 60:
            achievements.append('hour_of_focus')
        elif duration >= 120:
            achievements.append('two_hour_focus')
        
        return achievements

