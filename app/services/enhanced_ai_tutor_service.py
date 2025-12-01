"""Enhanced AI Tutor Service with conversational interface and personalized lesson plans"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
import re
import google.generativeai as genai
from supabase import Client

from app.config import settings
from app.models.base import Subject
from app.utils.exceptions import APIException
from app.services.rag_service import rag_service
from app.services.doubt_solver_service import doubt_solver_service
from app.services.progress_service import progress_service
from app.models.rag import RAGQuery


class EnhancedAITutorService:
    """Enhanced AI Tutor with conversational interface, homework help, and personalized lesson plans"""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        genai.configure(api_key=settings.gemini_api_key)
        try:
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        except:
            try:
                self.model = genai.GenerativeModel('gemini-3-pro-preview')
            except:
                self.model = genai.GenerativeModel('gemini-pro')
    
    async def create_session(
        self,
        user_id: str,
        session_name: Optional[str] = None,
        subject: Optional[Subject] = None
    ) -> Dict[str, Any]:
        """Create a new AI tutor session"""
        try:
            if not session_name:
                session_name = f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            session_data = {
                "user_id": user_id,
                "session_name": session_name,
                "subject": subject.value if subject else None,
                "is_active": True,
                "started_at": datetime.utcnow().isoformat(),
                "last_message_at": datetime.utcnow().isoformat(),
                "metadata": {}
            }
            
            result = self.supabase.table("ai_tutor_sessions").insert(session_data).execute()
            
            if not result.data:
                raise APIException("Failed to create session", 500)
            
            session = result.data[0]
            
            # Add welcome message
            welcome_message = {
                "session_id": session["id"],
                "role": "assistant",
                "content": f"Hello! I'm your AI tutor. I'm here to help you learn {subject.value if subject else 'your subjects'}. You can ask me questions, get help with homework, or request a personalized lesson plan based on your performance. How can I help you today?",
                "message_type": "text",
                "subject": subject.value if subject else None,
                "metadata": {}
            }
            
            self.supabase.table("ai_tutor_messages").insert(welcome_message).execute()
            
            return session
            
        except Exception as e:
            raise APIException(f"Error creating session: {str(e)}", 500)
    
    async def get_user_sessions(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get all sessions for a user"""
        try:
            result = self.supabase.table("ai_tutor_sessions")\
                .select("*")\
                .eq("user_id", user_id)\
                .order("last_message_at", desc=True)\
                .limit(limit)\
                .offset(offset)\
                .execute()
            
            return result.data or []
            
        except Exception as e:
            raise APIException(f"Error fetching sessions: {str(e)}", 500)
    
    async def get_session_messages(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get all messages in a session"""
        try:
            result = self.supabase.table("ai_tutor_messages")\
                .select("*")\
                .eq("session_id", session_id)\
                .order("created_at", desc=False)\
                .limit(limit)\
                .execute()
            
            return result.data or []
            
        except Exception as e:
            raise APIException(f"Error fetching messages: {str(e)}", 500)
    
    async def send_message(
        self,
        session_id: str,
        user_id: str,
        content: str,
        subject: Optional[Subject] = None,
        message_type: str = "text"
    ) -> Dict[str, Any]:
        """Send a message in a session and get AI response"""
        try:
            # Get session info
            session_result = self.supabase.table("ai_tutor_sessions")\
                .select("*")\
                .eq("id", session_id)\
                .eq("user_id", user_id)\
                .execute()
            
            if not session_result.data:
                raise APIException("Session not found", 404)
            
            session = session_result.data[0]
            
            # Save user message
            user_message = {
                "session_id": session_id,
                "role": "student",
                "content": content,
                "message_type": message_type,
                "subject": subject.value if subject else session.get("subject"),
                "metadata": {}
            }
            
            user_msg_result = self.supabase.table("ai_tutor_messages").insert(user_message).execute()
            
            # Get conversation history for context
            recent_messages = await self.get_session_messages(session_id, limit=10)
            conversation_context = "\n".join([
                f"{'Student' if msg['role'] == 'student' else 'AI Tutor'}: {msg['content']}"
                for msg in recent_messages[-5:]  # Last 5 messages for context
            ])
            
            # Get student performance data for personalized responses
            performance_data = await self._get_student_performance(user_id, subject or (Subject(session.get("subject")) if session.get("subject") else Subject.MATHEMATICS))
            
            # Determine message intent
            intent = self._classify_intent(content)
            
            # Generate AI response based on intent
            if intent == "greeting":
                ai_response = await self._handle_greeting(content, user_id, subject or (Subject(session.get("subject")) if session.get("subject") else Subject.MATHEMATICS), conversation_context, performance_data)
            elif intent == "homework_help":
                ai_response = await self._handle_homework_help(content, user_id, subject or (Subject(session.get("subject")) if session.get("subject") else Subject.MATHEMATICS), conversation_context)
            elif intent == "lesson_plan_request":
                ai_response = await self._handle_lesson_plan_request(content, user_id, subject or (Subject(session.get("subject")) if session.get("subject") else Subject.MATHEMATICS), performance_data)
            elif intent == "question":
                ai_response = await self._handle_question(content, user_id, subject or (Subject(session.get("subject")) if session.get("subject") else Subject.MATHEMATICS), conversation_context, performance_data)
            else:
                ai_response = await self._handle_general_message(content, user_id, subject or (Subject(session.get("subject")) if session.get("subject") else Subject.MATHEMATICS), conversation_context, performance_data)
            
            # Save AI response
            ai_message = {
                "session_id": session_id,
                "role": "assistant",
                "content": ai_response["content"],
                "message_type": ai_response.get("message_type", "text"),
                "subject": subject.value if subject else session.get("subject"),
                "metadata": ai_response.get("metadata", {})
            }
            
            ai_msg_result = self.supabase.table("ai_tutor_messages").insert(ai_message).execute()
            
            # Update session last_message_at
            self.supabase.table("ai_tutor_sessions")\
                .update({"last_message_at": datetime.utcnow().isoformat()})\
                .eq("id", session_id)\
                .execute()
            
            return {
                "user_message": user_msg_result.data[0] if user_msg_result.data else None,
                "ai_message": ai_msg_result.data[0] if ai_msg_result.data else None,
                "session_id": session_id
            }
            
        except Exception as e:
            raise APIException(f"Error sending message: {str(e)}", 500)
    
    def _classify_intent(self, content: str) -> str:
        """Classify the intent of the student's message"""
        content_lower = content.lower().strip()
        
        # Greeting keywords - handle with Gemini for friendly responses
        greeting_keywords = ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "greetings", "how are you", "how's it going", "what's up"]
        
        homework_keywords = ["homework", "assignment", "solve this", "help me with", "can you solve", "how do i solve"]
        lesson_plan_keywords = ["lesson plan", "study plan", "learning plan", "create a plan", "personalized plan", "study schedule"]
        # Expanded question keywords - treat most messages as questions to use RAG
        question_keywords = ["what", "why", "how", "explain", "tell me", "?", "question", "help", "understand", "learn", "teach", "show", "describe", "define", "meaning", "is", "are", "can", "could", "would", "should"]
        
        # Check for greetings first
        if any(keyword in content_lower for keyword in greeting_keywords) and len(content_lower.split()) <= 5:
            return "greeting"
        elif any(keyword in content_lower for keyword in homework_keywords):
            return "homework_help"
        elif any(keyword in content_lower for keyword in lesson_plan_keywords):
            return "lesson_plan_request"
        elif any(keyword in content_lower for keyword in question_keywords) or len(content.strip()) > 10:
            # Treat as question if it has question keywords OR is a substantial message
            return "question"
        else:
            # Even general messages should try RAG first
            return "question"
    
    async def _get_student_performance(self, user_id: str, subject: Subject) -> Dict[str, Any]:
        """Get student performance data for personalization"""
        try:
            # Get progress data
            progress_result = self.supabase.table("progress")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("subject", subject.value)\
                .execute()
            
            if not progress_result.data:
                return {
                    "average_mastery": 0,
                    "weak_topics": [],
                    "strong_topics": [],
                    "total_topics": 0,
                    "topics_attempted": 0
                }
            
            mastery_scores = [p.get("mastery_score", 0) for p in progress_result.data]
            average_mastery = sum(mastery_scores) / len(mastery_scores) if mastery_scores else 0
            
            # Identify weak and strong topics
            weak_topics = [
                {"topic_id": p.get("topic_id"), "mastery": p.get("mastery_score", 0)}
                for p in progress_result.data if p.get("mastery_score", 0) < 60
            ]
            
            strong_topics = [
                {"topic_id": p.get("topic_id"), "mastery": p.get("mastery_score", 0)}
                for p in progress_result.data if p.get("mastery_score", 0) >= 80
            ]
            
            return {
                "average_mastery": average_mastery,
                "weak_topics": weak_topics[:5],  # Top 5 weak topics
                "strong_topics": strong_topics[:5],  # Top 5 strong topics
                "total_topics": len(progress_result.data),
                "topics_attempted": len([p for p in progress_result.data if p.get("questions_attempted", 0) > 0])
            }
            
        except Exception as e:
            print(f"Error getting performance: {e}")
            return {
                "average_mastery": 0,
                "weak_topics": [],
                "strong_topics": [],
                "total_topics": 0,
                "topics_attempted": 0
            }
    
    async def _handle_greeting(
        self,
        content: str,
        user_id: str,
        subject: Subject,
        context: str,
        performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle greeting messages with Gemini for friendly, conversational responses"""
        try:
            # Get student name if available
            profile_result = self.supabase.table("profiles")\
                .select("full_name")\
                .eq("user_id", user_id)\
                .execute()
            
            student_name = profile_result.data[0].get("full_name", "there") if profile_result.data else "there"
            
            # Build friendly greeting prompt
            # Build context part separately to avoid backslash in f-string expression
            context_part = ""
            if context:
                context_part = f"Previous conversation:\n{context}\n"
            
            prompt = f"""You are a friendly, encouraging AI tutor helping a Class 12 student named {student_name} with {subject.value}.

Student said: {content}

{context_part}Respond in a warm, friendly, and encouraging way. Be conversational and welcoming. Keep it brief (1-2 sentences) and invite them to ask questions or get help with their studies.

Examples of good responses:
- "Hello! I'm excited to help you learn {subject.value}. What would you like to work on today?"
- "Hi there! I'm here to help you with {subject.value}. Feel free to ask me any questions!"
- "Hey! Great to see you! How can I help you with your studies today?"

Respond naturally and warmly:"""
            
            response = self.model.generate_content(prompt)
            
            return {
                "content": response.text,
                "message_type": "greeting",
                "metadata": {
                    "gemini_used": True,
                    "rag_used": False
                }
            }
            
        except Exception as e:
            # Fallback greeting
            return {
                "content": f"Hello! I'm your AI tutor for {subject.value}. I'm here to help you learn! What would you like to work on today?",
                "message_type": "greeting",
                "metadata": {
                    "error": str(e),
                    "gemini_used": False,
                    "rag_used": False
                }
            }
    
    async def _handle_question(
        self,
        content: str,
        user_id: str,
        subject: Subject,
        context: str,
        performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle a student question - ONLY using RAG from your data"""
        try:
            # Try RAG with subject filter first
            rag_query = RAGQuery(
                query=content,
                subject=subject,
                top_k=10,  # Get more results
                confidence_threshold=0.1  # Very low threshold
            )
            
            rag_response = await rag_service.query(rag_query)
            
            # If no results with subject, try without subject filter
            if (not rag_response.contexts or len(rag_response.contexts) == 0) and subject:
                print(f"No results with subject filter, trying without subject...")
                rag_query_no_subject = RAGQuery(
                    query=content,
                    subject=None,  # Remove subject filter
                    top_k=10,
                    confidence_threshold=0.1
                )
                rag_response = await rag_service.query(rag_query_no_subject)
            
            # If still no results, return helpful message
            if not rag_response.contexts or len(rag_response.contexts) == 0:
                return {
                    "content": "I couldn't find relevant information in the available content for your question. This might mean:\n\n1. The topic isn't covered in the uploaded curriculum materials yet\n2. The question needs to be rephrased\n3. Try asking about a different topic that's in the curriculum\n\nPlease try rephrasing your question or ask about a different topic.",
                    "message_type": "answer",
                    "metadata": {
                        "rag_used": False,
                        "confidence": 0.0,
                        "sources": [],
                        "reason": "no_content_found"
                    }
                }
            
            # Always return the RAG response, even if confidence is low
            # Format RAG response with sources
            formatted_response = rag_response.generated_text
            
            # Add confidence note if low
            if rag_response.confidence < 0.3:
                formatted_response = f"*Note: I found some related content (confidence: {rag_response.confidence:.0%}). Here's what I found:*\n\n{formatted_response}"
            
            # Add sources if available
            if rag_response.sources:
                formatted_response += "\n\n**Sources:**\n"
                for i, source in enumerate(rag_response.sources[:3], 1):
                    source_type = source.get("type", "Content")
                    chapter = source.get("chapter", "")
                    if chapter:
                        formatted_response += f"{i}. {source_type} - {chapter}\n"
                    else:
                        formatted_response += f"{i}. {source_type}\n"
            
            # Add context about related topics if available
            if rag_response.contexts and len(rag_response.contexts) > 1:
                formatted_response += f"\n\n*Based on {len(rag_response.contexts)} relevant content sections from the curriculum.*"
            
            return {
                "content": formatted_response,
                "message_type": "answer",
                "metadata": {
                    "answer_data": {
                        "answer": rag_response.generated_text,
                        "explanation": "",
                        "sources": rag_response.sources,
                        "contexts_count": len(rag_response.contexts),
                        "confidence": rag_response.confidence
                    },
                    "rag_used": True,
                    "confidence": rag_response.confidence,
                    "sources": rag_response.sources,
                    "contexts": [ctx.text[:200] + "..." if len(ctx.text) > 200 else ctx.text for ctx in rag_response.contexts[:3]]
                }
            }
            
        except Exception as e:
            import traceback
            print(f"Error in _handle_question: {str(e)}")
            print(traceback.format_exc())
            return {
                "content": f"I apologize, but I encountered an error while searching the curriculum. Please try rephrasing your question. Error: {str(e)}",
                "message_type": "text",
                "metadata": {
                    "error": str(e),
                    "rag_used": False
                }
            }
    
    async def _handle_homework_help(
        self,
        content: str,
        user_id: str,
        subject: Subject,
        context: str
    ) -> Dict[str, Any]:
        """Handle homework help request"""
        try:
            # Use doubt solver service for homework help
            doubt_response = await doubt_solver_service.process_text_doubt(
                user_id=user_id,
                text=content,
                subject=subject
            )
            
            # Format response for conversational interface
            help_content = f"I'll help you with this homework problem!\n\n"
            
            if doubt_response.answer:
                help_content += f"**Answer:** {doubt_response.answer}\n\n"
            
            if doubt_response.explanation:
                help_content += f"**Explanation:**\n{doubt_response.explanation}\n\n"
            
            if doubt_response.steps:
                help_content += "**Step-by-Step Solution:**\n"
                for i, step in enumerate(doubt_response.steps[:5], 1):
                    help_content += f"{i}. {step}\n"
                help_content += "\n"
            
            if doubt_response.related_content:
                help_content += "**Related Learning Resources:**\n"
                for content_item in doubt_response.related_content[:3]:
                    help_content += f"- {content_item.get('title', 'Resource')}\n"
            
            help_content += "\n💡 **Tip:** Try solving similar problems to strengthen your understanding!"
            
            return {
                "content": help_content,
                "message_type": "homework_help",
                "metadata": {
                    "doubt_response": doubt_response.dict() if hasattr(doubt_response, 'dict') else str(doubt_response)
                }
            }
            
        except Exception as e:
            return {
                "content": f"I'd love to help with your homework! Could you provide the specific problem or question? Error: {str(e)}",
                "message_type": "homework_help",
                "metadata": {}
            }
    
    async def _handle_lesson_plan_request(
        self,
        content: str,
        user_id: str,
        subject: Subject,
        performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle lesson plan generation request"""
        try:
            # Extract parameters from request
            days = 7
            hours_per_day = 2.0
            
            # Try to extract days and hours from content
            days_match = re.search(r'(\d+)\s*(?:day|days)', content.lower())
            if days_match:
                days = int(days_match.group(1))
            
            hours_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:hour|hours)', content.lower())
            if hours_match:
                hours_per_day = float(hours_match.group(1))
            
            # Get weak topics for focus
            weak_topics = performance_data.get("weak_topics", [])
            
            # Get all topics for the subject
            topics_result = self.supabase.table("topics")\
                .select("*")\
                .eq("subject", subject.value)\
                .order("order_index")\
                .execute()
            
            all_topics = topics_result.data or []
            
            # Build prompt for personalized lesson plan
            prompt = f"""Create a personalized {days}-day lesson plan for a Class 12 {subject.value} student.

Student Performance:
- Average Mastery: {performance_data.get('average_mastery', 0):.1f}%
- Weak Areas: {len(weak_topics)} topics need improvement
- Strong Areas: {len(performance_data.get('strong_topics', []))} topics mastered
- Topics Attempted: {performance_data.get('topics_attempted', 0)}/{performance_data.get('total_topics', 0)}

Available Time: {hours_per_day} hours per day for {days} days

All Topics to Cover:
{json.dumps([{'name': t.get('name'), 'chapter': t.get('chapter')} for t in all_topics[:15]], indent=2)}

Create a detailed, personalized lesson plan that:
1. Focuses on improving weak areas (60% of time)
2. Reinforces strong areas (20% of time)
3. Introduces new topics (20% of time)
4. Includes daily practice problems
5. Has review sessions every 3 days
6. Includes assessment checkpoints

Format as JSON:
{{
  "plan_name": "Personalized {subject.value} Plan",
  "duration_days": {days},
  "daily_schedule": [
    {{
      "day": 1,
      "date": "YYYY-MM-DD",
      "focus_areas": ["topic1", "topic2"],
      "activities": [
        {{"type": "concept_review", "topic": "topic1", "duration_minutes": 30, "description": "..."}},
        {{"type": "practice", "topic": "topic1", "duration_minutes": 45, "difficulty": "medium", "description": "..."}},
        {{"type": "weak_area_focus", "topic": "weak_topic", "duration_minutes": 30, "description": "..."}}
      ],
      "goals": ["goal1", "goal2"],
      "estimated_hours": {hours_per_day}
    }}
  ],
  "review_days": [3, 6],
  "assessment_checkpoints": [
    {{"day": 3, "type": "quiz", "topics": ["topic1", "topic2"], "marks": 20}}
  ],
  "focus_on_weak_areas": {len(weak_topics) > 0},
  "weak_topics_to_improve": {json.dumps([t.get('topic_id') for t in weak_topics[:5]])}
}}"""
            
            response = self.model.generate_content(prompt)
            plan_text = response.text
            
            # Parse JSON
            json_match = re.search(r'\{.*\}', plan_text, re.DOTALL)
            if json_match:
                plan_data = json.loads(json_match.group())
            else:
                raise APIException("Failed to parse lesson plan", 500)
            
            # Save lesson plan to database
            lesson_plan_data = {
                "user_id": user_id,
                "subject": subject.value,
                "plan_name": plan_data.get("plan_name", f"Personalized {subject.value} Plan"),
                "plan_data": plan_data,
                "based_on_performance": True,
                "performance_snapshot": performance_data,
                "start_date": datetime.now().date().isoformat(),
                "end_date": (datetime.now() + timedelta(days=days)).date().isoformat(),
                "is_active": True
            }
            
            plan_result = self.supabase.table("ai_tutor_lesson_plans").insert(lesson_plan_data).execute()
            
            response_content = f"""📚 **Personalized Lesson Plan Created!**

I've created a {days}-day lesson plan for {subject.value} based on your performance.

**Key Features:**
- Focus on {len(weak_topics)} weak areas that need improvement
- Daily practice sessions ({hours_per_day} hours/day)
- Review sessions every 3 days
- Assessment checkpoints to track progress

**Plan Overview:**
- Duration: {days} days
- Daily Time: {hours_per_day} hours
- Total Hours: {days * hours_per_day} hours
- Focus Areas: {len(weak_topics)} topics to strengthen

The plan has been saved and you can access it anytime. Would you like me to explain any specific day's schedule in detail?"""
            
            return {
                "content": response_content,
                "message_type": "lesson_plan",
                "metadata": {
                    "lesson_plan_id": plan_result.data[0]["id"] if plan_result.data else None,
                    "plan_data": plan_data
                }
            }
            
        except Exception as e:
            return {
                "content": f"I'd be happy to create a personalized lesson plan! Could you specify the duration (e.g., '7 days' or '2 weeks') and how many hours per day you can study? Error: {str(e)}",
                "message_type": "lesson_plan",
                "metadata": {}
            }
    
    async def _handle_general_message(
        self,
        content: str,
        user_id: str,
        subject: Subject,
        context: str,
        performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle general conversational messages - using RAG only"""
        try:
            # Try to find relevant content using RAG - treat as question
            # This ensures we always try to find content
            return await self._handle_question(content, user_id, subject, context, performance_data)
            
        except Exception as e:
            return {
                "content": "I'm here to help you learn! Could you ask me a specific question about the curriculum? I can help explain concepts, solve problems, or clarify topics from your study materials.",
                "message_type": "text",
                "metadata": {
                    "error": str(e),
                    "rag_used": False
                }
            }
    
    async def generate_performance_based_lesson_plan(
        self,
        user_id: str,
        subject: Subject,
        days: int = 7,
        hours_per_day: float = 2.0
    ) -> Dict[str, Any]:
        """Generate a personalized lesson plan based on student performance"""
        try:
            # Get performance data
            performance_data = await self._get_student_performance(user_id, subject)
            
            # Get topics
            topics_result = self.supabase.table("topics")\
                .select("*")\
                .eq("subject", subject.value)\
                .order("order_index")\
                .execute()
            
            all_topics = topics_result.data or []
            
            # Build comprehensive prompt
            prompt = f"""Create a comprehensive, personalized {days}-day lesson plan for a Class 12 {subject.value} student.

**Student Performance Analysis:**
- Average Mastery Score: {performance_data.get('average_mastery', 0):.1f}%
- Weak Topics (need improvement): {len(performance_data.get('weak_topics', []))}
- Strong Topics (mastered): {len(performance_data.get('strong_topics', []))}
- Total Topics Covered: {performance_data.get('topics_attempted', 0)}/{performance_data.get('total_topics', 0)}

**Time Available:**
- {hours_per_day} hours per day
- {days} days total
- {days * hours_per_day} total hours

**All Topics:**
{json.dumps([{'name': t.get('name'), 'chapter': t.get('chapter')} for t in all_topics[:20]], indent=2)}

**Create a detailed plan with:**
1. Daily schedule with specific topics and activities
2. 60% focus on weak areas, 20% on new topics, 20% on reinforcement
3. Practice problems with varying difficulty
4. Review sessions every 3 days
5. Assessment checkpoints
6. Realistic daily goals

**Format as JSON:**
{{
  "plan_name": "Personalized {subject.value} Improvement Plan",
  "duration_days": {days},
  "total_hours": {days * hours_per_day},
  "focus_strategy": "60% weak areas, 20% new topics, 20% reinforcement",
  "daily_schedule": [
    {{
      "day": 1,
      "date": "YYYY-MM-DD",
      "focus_areas": ["weak_topic1", "new_topic1"],
      "activities": [
        {{
          "type": "concept_learning",
          "topic": "topic_name",
          "duration_minutes": 30,
          "description": "Learn core concepts",
          "resources": ["NCERT", "Practice problems"]
        }},
        {{
          "type": "practice",
          "topic": "topic_name",
          "duration_minutes": 45,
          "difficulty": "medium",
          "question_count": 10,
          "description": "Practice problems"
        }},
        {{
          "type": "weak_area_focus",
          "topic": "weak_topic",
          "duration_minutes": 30,
          "description": "Extra practice on weak area"
        }}
      ],
      "goals": ["Master concept X", "Solve 10 practice problems"],
      "estimated_hours": {hours_per_day},
      "review_topics": ["previous_topic1"]
    }}
  ],
  "review_schedule": [
    {{"day": 3, "topics": ["topic1", "topic2"], "type": "quick_review"}},
    {{"day": 6, "topics": ["all_week_topics"], "type": "comprehensive_review"}}
  ],
  "assessment_checkpoints": [
    {{"day": 3, "type": "quiz", "topics": ["topic1", "topic2"], "marks": 20, "duration_minutes": 30}},
    {{"day": 7, "type": "test", "topics": ["all_week"], "marks": 50, "duration_minutes": 60}}
  ],
  "weak_topics_focus": {json.dumps([t.get('topic_id') for t in performance_data.get('weak_topics', [])[:5]])},
  "learning_objectives": ["objective1", "objective2"]
}}"""
            
            response = self.model.generate_content(prompt)
            plan_text = response.text
            
            # Parse JSON
            json_match = re.search(r'\{.*\}', plan_text, re.DOTALL)
            if json_match:
                plan_data = json.loads(json_match.group())
            else:
                raise APIException("Failed to parse lesson plan response", 500)
            
            # Save to database
            lesson_plan_data = {
                "user_id": user_id,
                "subject": subject.value,
                "plan_name": plan_data.get("plan_name", f"Personalized {subject.value} Plan"),
                "plan_data": plan_data,
                "based_on_performance": True,
                "performance_snapshot": performance_data,
                "start_date": datetime.now().date().isoformat(),
                "end_date": (datetime.now() + timedelta(days=days)).date().isoformat(),
                "is_active": True
            }
            
            result = self.supabase.table("ai_tutor_lesson_plans").insert(lesson_plan_data).execute()
            
            return {
                "lesson_plan_id": result.data[0]["id"] if result.data else None,
                "plan": plan_data,
                "performance_data": performance_data,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise APIException(f"Error generating lesson plan: {str(e)}", 500)
    
    async def get_lesson_plans(
        self,
        user_id: str,
        subject: Optional[Subject] = None,
        is_active: Optional[bool] = True
    ) -> List[Dict[str, Any]]:
        """Get lesson plans for a user"""
        try:
            query = self.supabase.table("ai_tutor_lesson_plans")\
                .select("*")\
                .eq("user_id", user_id)
            
            if subject:
                query = query.eq("subject", subject.value)
            
            if is_active is not None:
                query = query.eq("is_active", is_active)
            
            result = query.order("created_at", desc=True).execute()
            
            return result.data or []
            
        except Exception as e:
            raise APIException(f"Error fetching lesson plans: {str(e)}", 500)
    
    async def get_teacher_student_sessions(
        self,
        teacher_id: str,
        student_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get AI tutor sessions for students in teacher's school (limited access)"""
        try:
            # Get teacher's school
            teacher_profile = self.supabase.table("teacher_profiles")\
                .select("school_id")\
                .eq("user_id", teacher_id)\
                .execute()
            
            if not teacher_profile.data or not teacher_profile.data[0].get("school_id"):
                return []  # Teacher not assigned to a school
            
            school_id = teacher_profile.data[0]["school_id"]
            
            # Get students in the school
            students_result = self.supabase.table("student_profiles")\
                .select("user_id")\
                .eq("school_id", school_id)\
                .execute()
            
            student_ids = [s["user_id"] for s in (students_result.data or [])]
            
            if not student_ids:
                return []
            
            # Filter by specific student if provided
            if student_id:
                if student_id not in student_ids:
                    return []  # Student not in teacher's school
                student_ids = [student_id]
            
            # Get sessions for these students
            result = self.supabase.table("ai_tutor_sessions")\
                .select("*")\
                .in_("user_id", student_ids)\
                .order("last_message_at", desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data or []
            
        except Exception as e:
            raise APIException(f"Error fetching student sessions: {str(e)}", 500)

