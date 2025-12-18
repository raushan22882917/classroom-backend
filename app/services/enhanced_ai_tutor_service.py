"""Enhanced AI Tutor Service with conversational interface, persistent memory, and connected reasoning"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json
import re
from supabase import Client

from app.config import settings
from app.models.base import Subject
from app.utils.exceptions import APIException
from app.services.rag_service import rag_service
from app.services.doubt_solver_service import doubt_solver_service
from app.services.progress_service import progress_service
from app.models.rag import RAGQuery

# Import MemMachine and Neo4j services for enhanced intelligence
from app.services.memmachine_service import get_memmachine_service, LearningContext
from app.services.neo4j_service import get_neo4j_service
from app.services.interactive_learning_service import get_interactive_learning_service

# Try to import Google Generative AI, fallback if not available
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None


class EnhancedAITutorService:
    """Enhanced AI Tutor with conversational interface, persistent memory, and connected reasoning"""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        
        # Initialize Gemini if available
        if GEMINI_AVAILABLE and hasattr(settings, 'gemini_api_key') and settings.gemini_api_key:
            try:
                genai.configure(api_key=settings.gemini_api_key)
                try:
                    self.model = genai.GenerativeModel('gemini-2.5-flash')
                except:
                    try:
                        self.model = genai.GenerativeModel('gemini-1.5-flash')
                    except:
                        self.model = genai.GenerativeModel('gemini-pro')
                self.gemini_enabled = True
            except Exception as e:
                print(f"Gemini initialization failed: {e}")
                self.model = None
                self.gemini_enabled = False
        else:
            self.model = None
            self.gemini_enabled = False
        
        # Initialize MemMachine and Neo4j services for enhanced intelligence
        self.memmachine = get_memmachine_service()
        self.neo4j = get_neo4j_service()
        self.interactive_service = get_interactive_learning_service()
        
        # Session memory cache for real-time interactions
        self.session_memory = {}
        self.conversation_context = {}
    
    async def create_session(
        self,
        user_id: str,
        session_name: Optional[str] = None,
        subject: Optional[Subject] = None
    ) -> Dict[str, Any]:
        """Create a new AI tutor session with MemMachine integration"""
        try:
            if not session_name:
                session_name = f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            # Get user's learning history from MemMachine
            learning_history = await self.memmachine.get_user_learning_history(
                user_id=user_id,
                subject=subject.value if subject else None,
                days_back=30,
                limit=10
            )
            
            # Get user's knowledge graph progress
            user_stats = await self.neo4j.get_user_learning_stats(user_id)
            knowledge_gaps = await self.neo4j.analyze_knowledge_gaps(user_id)
            
            # Create enhanced session data
            session_data = {
                "user_id": user_id,
                "session_name": session_name,
                "subject": subject.value if subject else None,
                "is_active": True,
                "started_at": datetime.utcnow().isoformat(),
                "last_message_at": datetime.utcnow().isoformat(),
                "metadata": {
                    "learning_history_count": len(learning_history),
                    "user_stats": user_stats,
                    "knowledge_gaps": len(knowledge_gaps.get('weak_areas', [])),
                    "memmachine_enabled": True,
                    "neo4j_enabled": True
                }
            }
            
            result = self.supabase.table("ai_tutor_sessions").insert(session_data).execute()
            
            if not result.data:
                raise APIException(
                    code="CREATE_SESSION_ERROR",
                    message="Failed to create session",
                    status_code=500
                )
            
            session = result.data[0]
            session_id = session["id"]
            
            # Initialize session memory in MemMachine
            session_context = LearningContext(
                user_id=user_id,
                session_id=session_id,
                subject=subject.value if subject else "general",
                topic="ai_tutoring_session",
                difficulty_level=1,
                learning_objectives=["interactive_tutoring", "personalized_help"],
                previous_knowledge=user_stats,
                current_progress={"session_started": True}
            )
            
            # Store session initialization in MemMachine
            await self.memmachine.store_learning_session(session_context, {
                "session_type": "ai_tutoring",
                "session_name": session_name,
                "initialization_data": {
                    "learning_history_available": len(learning_history) > 0,
                    "knowledge_gaps_identified": len(knowledge_gaps.get('weak_areas', [])),
                    "user_mastery_rate": user_stats.get('mastery_rate', 0),
                    "total_concepts": user_stats.get('total_concepts', 0)
                },
                "performance_metrics": {
                    "session_created": True,
                    "engagement_score": 1.0
                }
            })
            
            # Cache session context for quick access
            self.session_memory[session_id] = {
                "user_id": user_id,
                "subject": subject.value if subject else None,
                "learning_history": learning_history,
                "user_stats": user_stats,
                "knowledge_gaps": knowledge_gaps,
                "session_context": session_context,
                "created_at": datetime.now()
            }
            
            # Generate personalized welcome message based on user's history
            welcome_content = await self._generate_personalized_welcome(
                user_id, subject, learning_history, user_stats, knowledge_gaps
            )
            
            # Add enhanced welcome message
            welcome_message = {
                "session_id": session_id,
                "role": "assistant",
                "content": welcome_content,
                "message_type": "welcome",
                "subject": subject.value if subject else None,
                "metadata": {
                    "personalized": True,
                    "based_on_history": len(learning_history) > 0,
                    "knowledge_gaps_mentioned": len(knowledge_gaps.get('weak_areas', [])) > 0
                }
            }
            
            self.supabase.table("ai_tutor_messages").insert(welcome_message).execute()
            
            return session
            
        except Exception as e:
            raise APIException(
                code="CREATE_SESSION_ERROR",
                message=f"Error creating session: {str(e)}",
                status_code=500
            )
    
    async def _generate_personalized_welcome(
        self,
        user_id: str,
        subject: Optional[Subject],
        learning_history: List[Any],
        user_stats: Dict[str, Any],
        knowledge_gaps: Dict[str, Any]
    ) -> str:
        """Generate a personalized welcome message based on user's learning data"""
        try:
            # Build context from user's data
            context_parts = []
            
            if learning_history:
                recent_sessions = len(learning_history)
                context_parts.append(f"I see you've had {recent_sessions} recent learning sessions")
                
                # Get most recent subject
                if learning_history[0].content.get('context', {}).get('subject'):
                    recent_subject = learning_history[0].content['context']['subject']
                    context_parts.append(f"with recent focus on {recent_subject}")
            
            if user_stats.get('mastered_concepts', 0) > 0:
                mastered = user_stats['mastered_concepts']
                total = user_stats.get('total_concepts', mastered)
                context_parts.append(f"You've mastered {mastered} out of {total} concepts")
            
            weak_areas = knowledge_gaps.get('weak_areas', [])
            if weak_areas:
                weak_count = len(weak_areas)
                context_parts.append(f"I notice {weak_count} areas where we can focus on improvement")
            
            # Generate personalized message
            if context_parts:
                context_text = ". ".join(context_parts)
                welcome_msg = f"Welcome back! {context_text}. "
            else:
                welcome_msg = "Hello! I'm excited to start learning with you. "
            
            subject_text = f" in {subject.value}" if subject else ""
            
            welcome_msg += f"I'm your AI tutor with advanced memory and knowledge mapping capabilities{subject_text}. "
            welcome_msg += "I remember our previous conversations and can track your progress across all topics. "
            
            # Add interactive features mention
            welcome_msg += "\n\n🎯 **What I can help you with:**\n"
            welcome_msg += "• **Smart Q&A**: Ask me anything and I'll remember the context\n"
            welcome_msg += "• **Interactive Learning**: Access visual simulations and practice tools\n"
            welcome_msg += "• **Personalized Paths**: Get learning routes based on your progress\n"
            welcome_msg += "• **Knowledge Mapping**: See how concepts connect to each other\n"
            welcome_msg += "• **Memory Insights**: Track your learning patterns over time\n"
            
            if weak_areas:
                welcome_msg += f"\n💡 **Focus Suggestion**: I recommend we work on {weak_areas[0].get('concept', 'key concepts')} to strengthen your foundation."
            
            welcome_msg += "\n\nWhat would you like to explore today?"
            
            return welcome_msg
            
        except Exception as e:
            # Fallback welcome message
            subject_text = f" for {subject.value}" if subject else ""
            return f"Hello! I'm your enhanced AI tutor{subject_text} with persistent memory and intelligent knowledge mapping. I can remember our conversations, track your progress, and provide personalized learning experiences. How can I help you today?"
    
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
            error_msg = str(e)
            # Check for Supabase authentication errors
            if "Invalid API key" in error_msg or "401" in error_msg or "JSON could not be generated" in error_msg:
                raise APIException(
                    code="SUPABASE_AUTH_ERROR",
                    message="Database authentication failed. Please check Supabase service key configuration.",
                    status_code=503
                )
            # Re-raise other errors
            raise APIException(
                code="FETCH_SESSIONS_ERROR",
                message=f"Error fetching sessions: {str(e)}",
                status_code=500
            )
    
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
            raise APIException(
                code="FETCH_MESSAGES_ERROR",
                message=f"Error fetching messages: {str(e)}",
                status_code=500
            )
    
    async def send_message(
        self,
        session_id: str,
        user_id: str,
        content: str,
        subject: Optional[Subject] = None,
        message_type: str = "text"
    ) -> Dict[str, Any]:
        """Send a message in a session and get enhanced AI response with memory and knowledge graph integration"""
        try:
            # Get session info
            session_result = self.supabase.table("ai_tutor_sessions")\
                .select("*")\
                .eq("id", session_id)\
                .eq("user_id", user_id)\
                .execute()
            
            if not session_result.data:
                raise APIException(
                    code="SESSION_NOT_FOUND",
                    message="Session not found",
                    status_code=404
                )
            
            session = session_result.data[0]
            
            # Get or initialize session memory
            if session_id not in self.session_memory:
                await self._initialize_session_memory(session_id, user_id, subject)
            
            session_memory = self.session_memory[session_id]
            
            # Store user message in MemMachine for persistent memory
            message_context = LearningContext(
                user_id=user_id,
                session_id=session_id,
                subject=subject.value if subject else session.get("subject", "general"),
                topic="conversation",
                difficulty_level=1,
                learning_objectives=["interactive_conversation"],
                previous_knowledge=session_memory.get("user_stats", {}),
                current_progress={"message_count": len(await self.get_session_messages(session_id, limit=100))}
            )
            
            # Analyze message for learning insights
            message_analysis = await self._analyze_message_for_learning(content, user_id, subject)
            
            await self.memmachine.store_learning_session(message_context, {
                "message_type": "user_input",
                "content": content,
                "message_analysis": message_analysis,
                "timestamp": datetime.now().isoformat(),
                "performance_metrics": {
                    "engagement_score": message_analysis.get("engagement_score", 0.8),
                    "complexity_level": message_analysis.get("complexity_level", 1)
                }
            })
            
            # Save user message to database
            user_message = {
                "session_id": session_id,
                "role": "student",
                "content": content,
                "message_type": message_type,
                "subject": subject.value if subject else session.get("subject"),
                "metadata": {
                    "analysis": message_analysis,
                    "memory_stored": True
                }
            }
            
            user_msg_result = self.supabase.table("ai_tutor_messages").insert(user_message).execute()
            
            # Get enhanced conversation context from MemMachine
            conversation_context = await self._get_enhanced_conversation_context(session_id, user_id)
            
            # Get real-time performance data and knowledge graph insights
            performance_data = await self._get_enhanced_performance_data(user_id, subject or (Subject(session.get("subject")) if session.get("subject") else Subject.MATHEMATICS))
            
            # Determine message intent with enhanced classification
            intent = await self._classify_intent_enhanced(content, conversation_context, performance_data)
            
            # Generate AI response with full intelligence integration
            ai_response = await self._generate_enhanced_response(
                content=content,
                intent=intent,
                user_id=user_id,
                session_id=session_id,
                subject=subject or (Subject(session.get("subject")) if session.get("subject") else Subject.MATHEMATICS),
                conversation_context=conversation_context,
                performance_data=performance_data,
                session_memory=session_memory
            )
            
            # Store AI response in MemMachine
            await self.memmachine.store_learning_session(message_context, {
                "message_type": "ai_response",
                "content": ai_response["content"],
                "intent": intent,
                "response_metadata": ai_response.get("metadata", {}),
                "timestamp": datetime.now().isoformat(),
                "performance_metrics": {
                    "response_quality": ai_response.get("quality_score", 0.9),
                    "helpfulness": ai_response.get("helpfulness_score", 0.8)
                }
            })
            
            # Update knowledge graph with interaction data
            if intent in ["question", "homework_help"] and ai_response.get("concepts_discussed"):
                for concept in ai_response["concepts_discussed"]:
                    await self.neo4j.update_user_progress(
                        user_id=user_id,
                        concept_name=concept,
                        performance_data={
                            "accuracy": ai_response.get("understanding_level", 0.7),
                            "engagement_score": message_analysis.get("engagement_score", 0.8),
                            "duration": 300  # Estimated 5 minutes per interaction
                        }
                    )
            
            # Save enhanced AI response
            ai_message = {
                "session_id": session_id,
                "role": "assistant",
                "content": ai_response["content"],
                "message_type": ai_response.get("message_type", "text"),
                "subject": subject.value if subject else session.get("subject"),
                "metadata": {
                    **ai_response.get("metadata", {}),
                    "enhanced_intelligence": True,
                    "memory_integration": True,
                    "knowledge_graph_updated": len(ai_response.get("concepts_discussed", [])) > 0
                }
            }
            
            ai_msg_result = self.supabase.table("ai_tutor_messages").insert(ai_message).execute()
            
            # Update session with enhanced metadata
            self.supabase.table("ai_tutor_sessions")\
                .update({
                    "last_message_at": datetime.utcnow().isoformat(),
                    "metadata": {
                        **session.get("metadata", {}),
                        "total_interactions": session.get("metadata", {}).get("total_interactions", 0) + 1,
                        "last_intent": intent,
                        "concepts_discussed": ai_response.get("concepts_discussed", [])
                    }
                })\
                .eq("id", session_id)\
                .execute()
            
            # Update session memory cache
            self.session_memory[session_id]["last_interaction"] = {
                "timestamp": datetime.now(),
                "intent": intent,
                "concepts": ai_response.get("concepts_discussed", []),
                "user_message": content,
                "ai_response": ai_response["content"]
            }
            
            return {
                "user_message": user_msg_result.data[0] if user_msg_result.data else None,
                "ai_message": ai_msg_result.data[0] if ai_msg_result.data else None,
                "session_id": session_id,
                "enhanced_features": {
                    "memory_integration": True,
                    "knowledge_graph_updated": len(ai_response.get("concepts_discussed", [])) > 0,
                    "intent_detected": intent,
                    "concepts_discussed": ai_response.get("concepts_discussed", []),
                    "interactive_components_suggested": ai_response.get("interactive_suggestions", [])
                }
            }
            
        except Exception as e:
            raise APIException(
                code="SEND_MESSAGE_ERROR",
                message=f"Error sending message: {str(e)}",
                status_code=500
            )
    
    async def _initialize_session_memory(self, session_id: str, user_id: str, subject: Optional[Subject]):
        """Initialize session memory if not already cached"""
        try:
            # Get user's learning history from MemMachine
            learning_history = await self.memmachine.get_user_learning_history(
                user_id=user_id,
                subject=subject.value if subject else None,
                days_back=30,
                limit=10
            )
            
            # Get user's knowledge graph progress
            user_stats = await self.neo4j.get_user_learning_stats(user_id)
            knowledge_gaps = await self.neo4j.analyze_knowledge_gaps(user_id)
            
            self.session_memory[session_id] = {
                "user_id": user_id,
                "subject": subject.value if subject else None,
                "learning_history": learning_history,
                "user_stats": user_stats,
                "knowledge_gaps": knowledge_gaps,
                "created_at": datetime.now(),
                "last_interaction": None
            }
            
        except Exception as e:
            # Fallback to basic session memory
            self.session_memory[session_id] = {
                "user_id": user_id,
                "subject": subject.value if subject else None,
                "learning_history": [],
                "user_stats": {},
                "knowledge_gaps": {},
                "created_at": datetime.now(),
                "error": str(e)
            }
    
    async def _analyze_message_for_learning(self, content: str, user_id: str, subject: Optional[Subject]) -> Dict[str, Any]:
        """Analyze user message for learning insights"""
        try:
            analysis = {
                "message_length": len(content),
                "word_count": len(content.split()),
                "question_indicators": ["?", "what", "how", "why", "explain"] 
            }
            
            # Calculate engagement score based on message characteristics
            engagement_score = 0.5  # Base score
            
            if analysis["word_count"] > 10:
                engagement_score += 0.2  # Detailed messages show engagement
            
            if any(indicator in content.lower() for indicator in analysis["question_indicators"]):
                engagement_score += 0.2  # Questions show active learning
                analysis["contains_question"] = True
            
            if len(content) > 50:
                engagement_score += 0.1  # Longer messages show thoughtfulness
            
            # Detect complexity level
            complexity_indicators = ["because", "however", "therefore", "although", "moreover"]
            if any(indicator in content.lower() for indicator in complexity_indicators):
                analysis["complexity_level"] = 2
                engagement_score += 0.1
            else:
                analysis["complexity_level"] = 1
            
            analysis["engagement_score"] = min(engagement_score, 1.0)
            
            # Detect subject-specific keywords
            if subject:
                subject_keywords = {
                    "mathematics": ["equation", "solve", "calculate", "formula", "graph"],
                    "physics": ["force", "energy", "motion", "velocity", "acceleration"],
                    "chemistry": ["reaction", "molecule", "element", "compound", "bond"]
                }
                
                keywords = subject_keywords.get(subject.value.lower(), [])
                found_keywords = [kw for kw in keywords if kw in content.lower()]
                analysis["subject_keywords"] = found_keywords
                
                if found_keywords:
                    engagement_score += 0.1
                    analysis["subject_relevance"] = len(found_keywords) / len(keywords)
            
            return analysis
            
        except Exception as e:
            return {
                "error": str(e),
                "engagement_score": 0.5,
                "complexity_level": 1
            }
    
    async def _get_enhanced_conversation_context(self, session_id: str, user_id: str) -> str:
        """Get enhanced conversation context using MemMachine data"""
        try:
            # Get recent messages from database
            recent_messages = await self.get_session_messages(session_id, limit=10)
            
            # Get broader learning context from MemMachine
            learning_patterns = await self.memmachine.analyze_learning_patterns(user_id)
            
            # Build enhanced context
            context_parts = []
            
            # Add recent conversation
            if recent_messages:
                context_parts.append("Recent conversation:")
                for msg in recent_messages[-5:]:
                    role = "Student" if msg['role'] == 'student' else "AI Tutor"
                    context_parts.append(f"{role}: {msg['content'][:100]}...")
            
            # Add learning patterns insight
            if learning_patterns and not learning_patterns.get('error'):
                total_sessions = learning_patterns.get('total_sessions', 0)
                if total_sessions > 0:
                    context_parts.append(f"\nLearning History: {total_sessions} total sessions")
                    
                    velocity = learning_patterns.get('learning_velocity', 1.0)
                    context_parts.append(f"Learning velocity: {velocity:.1f}x")
                    
                    focus_areas = learning_patterns.get('recommended_focus_areas', [])
                    if focus_areas:
                        context_parts.append(f"Focus areas: {', '.join([area.get('topic', '') for area in focus_areas[:3]])}")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            # Fallback to basic context
            recent_messages = await self.get_session_messages(session_id, limit=5)
            return "\n".join([
                f"{'Student' if msg['role'] == 'student' else 'AI Tutor'}: {msg['content']}"
                for msg in recent_messages[-3:]
            ])
    
    async def _get_enhanced_performance_data(self, user_id: str, subject: Subject) -> Dict[str, Any]:
        """Get enhanced performance data combining traditional and knowledge graph data"""
        try:
            # Get traditional performance data
            traditional_data = await self._get_student_performance(user_id, subject)
            
            # Get knowledge graph insights
            user_stats = await self.neo4j.get_user_learning_stats(user_id)
            knowledge_gaps = await self.neo4j.analyze_knowledge_gaps(user_id)
            recommendations = await self.neo4j.recommend_next_concepts(user_id, limit=5)
            
            # Combine data
            enhanced_data = {
                **traditional_data,
                "knowledge_graph_stats": user_stats,
                "knowledge_gaps": knowledge_gaps,
                "recommended_concepts": recommendations,
                "mastery_rate": user_stats.get("mastery_rate", 0),
                "learning_velocity": user_stats.get("learning_velocity", 1.0),
                "concepts_in_progress": user_stats.get("concepts_in_progress", 0)
            }
            
            return enhanced_data
            
        except Exception as e:
            # Fallback to traditional data
            return await self._get_student_performance(user_id, subject)
    
    async def _classify_intent_enhanced(
        self, 
        content: str, 
        conversation_context: str, 
        performance_data: Dict[str, Any]
    ) -> str:
        """Enhanced intent classification using context and performance data"""
        try:
            # Start with basic classification
            basic_intent = self._classify_intent(content)
            
            # Enhance based on context and performance
            content_lower = content.lower().strip()
            
            # Check for interactive learning requests
            interactive_keywords = ["show me", "visualize", "simulate", "interactive", "demo", "practice"]
            if any(keyword in content_lower for keyword in interactive_keywords):
                return "interactive_request"
            
            # Check for knowledge graph exploration
            graph_keywords = ["how does", "connect", "relationship", "related to", "prerequisite", "depends on"]
            if any(keyword in content_lower for keyword in graph_keywords):
                return "knowledge_exploration"
            
            # Check for memory/progress queries
            memory_keywords = ["my progress", "what did we", "remember", "last time", "history"]
            if any(keyword in content_lower for keyword in memory_keywords):
                return "memory_query"
            
            # Check for personalized learning requests
            personal_keywords = ["for me", "my level", "personalized", "adapted", "customized"]
            if any(keyword in content_lower for keyword in personal_keywords):
                return "personalized_request"
            
            # Enhanced context-based classification
            if "weak" in conversation_context.lower() and ("help" in content_lower or "improve" in content_lower):
                return "weakness_improvement"
            
            return basic_intent
            
        except Exception as e:
            return self._classify_intent(content)
    
    async def _generate_enhanced_response(
        self,
        content: str,
        intent: str,
        user_id: str,
        session_id: str,
        subject: Subject,
        conversation_context: str,
        performance_data: Dict[str, Any],
        session_memory: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate enhanced AI response with full intelligence integration"""
        try:
            # Route to appropriate enhanced handler
            if intent == "interactive_request":
                return await self._handle_interactive_request(content, user_id, subject, performance_data)
            elif intent == "knowledge_exploration":
                return await self._handle_knowledge_exploration(content, user_id, subject, performance_data)
            elif intent == "memory_query":
                return await self._handle_memory_query(content, user_id, session_memory)
            elif intent == "personalized_request":
                return await self._handle_personalized_request(content, user_id, subject, performance_data)
            elif intent == "weakness_improvement":
                return await self._handle_weakness_improvement(content, user_id, subject, performance_data)
            elif intent == "greeting":
                return await self._handle_greeting_enhanced(content, user_id, subject, conversation_context, performance_data, session_memory)
            elif intent == "question":
                return await self._handle_question_enhanced(content, user_id, subject, conversation_context, performance_data)
            elif intent == "homework_help":
                return await self._handle_homework_help_enhanced(content, user_id, subject, conversation_context, performance_data)
            elif intent == "lesson_plan_request":
                return await self._handle_lesson_plan_request_enhanced(content, user_id, subject, performance_data)
            else:
                return await self._handle_general_message_enhanced(content, user_id, subject, conversation_context, performance_data)
                
        except Exception as e:
            return {
                "content": f"I apologize, but I encountered an error while processing your request. Let me try to help you in a different way. Error: {str(e)}",
                "message_type": "error",
                "metadata": {"error": str(e)},
                "concepts_discussed": [],
                "interactive_suggestions": []
            }
    
    async def _handle_interactive_request(
        self, 
        content: str, 
        user_id: str, 
        subject: Subject, 
        performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle requests for interactive learning components"""
        try:
            # Get available interactive components
            component_library = await self.interactive_service.get_component_library()
            
            # Find relevant components based on subject and content
            relevant_components = []
            content_lower = content.lower()
            
            for comp_id, comp_info in component_library["library"]["components"].items():
                if comp_info.get("subject") == subject.value.lower():
                    # Check if component matches request
                    if any(keyword in content_lower for keyword in [
                        comp_info.get("topic", "").lower(),
                        comp_info.get("title", "").lower().split()[-1]
                    ]):
                        relevant_components.append({
                            "id": comp_id,
                            "title": comp_info["title"],
                            "type": comp_info["type"],
                            "duration": comp_info["duration"],
                            "difficulty": comp_info["difficulty"]
                        })
            
            if not relevant_components:
                # Suggest general components for the subject
                for comp_id, comp_info in component_library["library"]["components"].items():
                    if comp_info.get("subject") == subject.value.lower():
                        relevant_components.append({
                            "id": comp_id,
                            "title": comp_info["title"],
                            "type": comp_info["type"],
                            "duration": comp_info["duration"],
                            "difficulty": comp_info["difficulty"]
                        })
                        if len(relevant_components) >= 3:
                            break
            
            # Generate response with interactive suggestions
            response_content = f"🎮 **Interactive Learning Available!**\n\n"
            response_content += f"I found {len(relevant_components)} interactive components for {subject.value}:\n\n"
            
            for i, comp in enumerate(relevant_components[:3], 1):
                response_content += f"**{i}. {comp['title']}**\n"
                response_content += f"   • Type: {comp['type'].title()}\n"
                response_content += f"   • Duration: ~{comp['duration']} minutes\n"
                response_content += f"   • Difficulty: Level {comp['difficulty']}\n\n"
            
            response_content += "🚀 **To start an interactive session:**\n"
            response_content += "1. Choose a component from above\n"
            response_content += "2. I'll create a personalized learning session\n"
            response_content += "3. You'll get real-time feedback and progress tracking\n\n"
            
            response_content += "Which interactive component interests you most?"
            
            return {
                "content": response_content,
                "message_type": "interactive_suggestion",
                "metadata": {
                    "available_components": relevant_components,
                    "component_count": len(relevant_components)
                },
                "concepts_discussed": [subject.value],
                "interactive_suggestions": relevant_components,
                "quality_score": 0.9,
                "helpfulness_score": 0.95
            }
            
        except Exception as e:
            return {
                "content": f"I'd love to show you interactive learning tools! Let me know what specific topic in {subject.value} you'd like to explore interactively.",
                "message_type": "interactive_suggestion",
                "metadata": {"error": str(e)},
                "concepts_discussed": [],
                "interactive_suggestions": []
            }
    
    async def _handle_knowledge_exploration(
        self, 
        content: str, 
        user_id: str, 
        subject: Subject, 
        performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle knowledge graph exploration requests"""
        try:
            # Extract concept from content
            content_words = content.lower().split()
            
            # Get concept relationships from knowledge graph
            concepts_discussed = []
            relationships_info = []
            
            # Try to find mentioned concepts in the knowledge graph
            graph_stats = await self.neo4j.get_graph_statistics()
            
            # Simple concept extraction (can be enhanced with NLP)
            potential_concepts = []
            for word in content_words:
                if len(word) > 3 and word.isalpha():
                    potential_concepts.append(word.title())
            
            # Get relationships for found concepts
            for concept in potential_concepts[:3]:  # Limit to 3 concepts
                try:
                    relationships = await self.neo4j.get_concept_relationships(concept)
                    if relationships and any(relationships.values()):
                        concepts_discussed.append(concept)
                        relationships_info.append({
                            "concept": concept,
                            "relationships": relationships
                        })
                except:
                    continue
            
            if relationships_info:
                response_content = f"🕸️ **Knowledge Graph Exploration**\n\n"
                
                for rel_info in relationships_info:
                    concept = rel_info["concept"]
                    rels = rel_info["relationships"]
                    
                    response_content += f"**{concept} Connections:**\n"
                    
                    if rels.get("prerequisites"):
                        response_content += f"📚 Prerequisites: {', '.join(rels['prerequisites'])}\n"
                    
                    if rels.get("dependents"):
                        response_content += f"🎯 Leads to: {', '.join(rels['dependents'])}\n"
                    
                    if rels.get("related"):
                        response_content += f"🔗 Related topics: {', '.join(rels['related'])}\n"
                    
                    if rels.get("applications"):
                        response_content += f"⚡ Applications: {', '.join(rels['applications'])}\n"
                    
                    response_content += "\n"
                
                # Add learning path suggestion
                if concepts_discussed:
                    learning_path = await self.neo4j.find_learning_path(
                        user_id=user_id,
                        target_concept=concepts_discussed[0]
                    )
                    
                    if learning_path.path_nodes:
                        response_content += f"🛤️ **Suggested Learning Path to {concepts_discussed[0]}:**\n"
                        for i, node in enumerate(learning_path.path_nodes, 1):
                            response_content += f"{i}. {node}\n"
                        response_content += f"\n⏱️ Estimated time: {learning_path.estimated_duration} minutes\n"
                        response_content += f"🎯 Confidence: {learning_path.confidence_score:.0%}\n"
            
            else:
                # General knowledge graph overview
                response_content = f"🕸️ **Knowledge Graph Overview**\n\n"
                response_content += f"📊 **Current Graph Statistics:**\n"
                response_content += f"• Total concepts: {graph_stats.get('total_nodes', 0)}\n"
                response_content += f"• Relationships: {graph_stats.get('total_relationships', 0)}\n"
                response_content += f"• Subjects covered: {', '.join(graph_stats.get('subjects', []))}\n\n"
                
                response_content += "🔍 **Ask me about:**\n"
                response_content += "• How concepts connect to each other\n"
                response_content += "• Prerequisites for any topic\n"
                response_content += "• Learning paths to your goals\n"
                response_content += "• Related topics to explore\n\n"
                
                response_content += "Try asking: 'How does algebra connect to calculus?' or 'What are the prerequisites for derivatives?'"
            
            return {
                "content": response_content,
                "message_type": "knowledge_exploration",
                "metadata": {
                    "concepts_found": concepts_discussed,
                    "relationships_explored": len(relationships_info),
                    "graph_stats": graph_stats
                },
                "concepts_discussed": concepts_discussed,
                "interactive_suggestions": [],
                "quality_score": 0.85,
                "helpfulness_score": 0.9
            }
            
        except Exception as e:
            return {
                "content": f"I can help you explore how concepts connect! Ask me about relationships between topics, prerequisites, or learning paths. What would you like to explore?",
                "message_type": "knowledge_exploration",
                "metadata": {"error": str(e)},
                "concepts_discussed": [],
                "interactive_suggestions": []
            }
    
    async def _handle_memory_query(
        self, 
        content: str, 
        user_id: str, 
        session_memory: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle queries about learning history and progress"""
        try:
            # Get comprehensive learning patterns from MemMachine
            learning_patterns = await self.memmachine.analyze_learning_patterns(user_id)
            
            response_content = f"🧠 **Your Learning Memory**\n\n"
            
            if learning_patterns and not learning_patterns.get('error'):
                total_sessions = learning_patterns.get('total_sessions', 0)
                subjects_studied = learning_patterns.get('subjects_studied', 0)
                velocity = learning_patterns.get('learning_velocity', 1.0)
                
                response_content += f"📈 **Learning Statistics:**\n"
                response_content += f"• Total learning sessions: {total_sessions}\n"
                response_content += f"• Subjects explored: {subjects_studied}\n"
                response_content += f"• Learning velocity: {velocity:.1f}x average\n\n"
                
                # Subject breakdown
                subject_breakdown = learning_patterns.get('subject_breakdown', {})
                if subject_breakdown:
                    response_content += f"📚 **Subject Breakdown:**\n"
                    for subject, stats in subject_breakdown.items():
                        count = stats.get('count', 0)
                        avg_perf = stats.get('avg_performance', 0)
                        response_content += f"• {subject}: {count} sessions, {avg_perf:.0%} avg performance\n"
                    response_content += "\n"
                
                # Focus areas
                focus_areas = learning_patterns.get('recommended_focus_areas', [])
                if focus_areas:
                    response_content += f"🎯 **Areas for Improvement:**\n"
                    for area in focus_areas[:3]:
                        topic = area.get('topic', 'Unknown')
                        performance = area.get('avg_performance', 0)
                        priority = area.get('priority', 'medium')
                        response_content += f"• {topic}: {performance:.0%} mastery ({priority} priority)\n"
                    response_content += "\n"
                
                # Recent activity
                learning_history = session_memory.get('learning_history', [])
                if learning_history:
                    response_content += f"🕒 **Recent Activity:**\n"
                    for entry in learning_history[:3]:
                        timestamp = entry.timestamp.strftime('%Y-%m-%d %H:%M')
                        subject = entry.content.get('context', {}).get('subject', 'General')
                        topic = entry.content.get('context', {}).get('topic', 'Learning')
                        response_content += f"• {timestamp}: {subject} - {topic}\n"
            
            else:
                response_content += "I'm still building your learning profile. Keep interacting with me to develop a comprehensive memory of your learning journey!\n\n"
                response_content += "I'll remember:\n"
                response_content += "• Topics you've studied\n"
                response_content += "• Your performance patterns\n"
                response_content += "• Areas where you excel\n"
                response_content += "• Concepts that need more practice\n"
            
            response_content += "\n💡 **Memory Features:**\n"
            response_content += "• I remember all our conversations\n"
            response_content += "• I track your progress across topics\n"
            response_content += "• I identify your learning patterns\n"
            response_content += "• I suggest personalized improvements\n"
            
            return {
                "content": response_content,
                "message_type": "memory_insight",
                "metadata": {
                    "learning_patterns": learning_patterns,
                    "memory_available": len(session_memory.get('learning_history', [])) > 0
                },
                "concepts_discussed": [],
                "interactive_suggestions": [],
                "quality_score": 0.9,
                "helpfulness_score": 0.85
            }
            
        except Exception as e:
            return {
                "content": f"I'm building a comprehensive memory of your learning journey! Each interaction helps me understand your progress better. What specific aspect of your learning would you like to know about?",
                "message_type": "memory_insight",
                "metadata": {"error": str(e)},
                "concepts_discussed": [],
                "interactive_suggestions": []
            }
    
    async def _handle_personalized_request(
        self, 
        content: str, 
        user_id: str, 
        subject: Subject, 
        performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle personalized learning requests"""
        try:
            # Get recommendations from knowledge graph
            recommendations = performance_data.get('recommended_concepts', [])
            knowledge_gaps = performance_data.get('knowledge_gaps', {})
            
            response_content = f"🎯 **Personalized Learning Plan for You**\n\n"
            
            # Current status
            mastery_rate = performance_data.get('mastery_rate', 0)
            learning_velocity = performance_data.get('learning_velocity', 1.0)
            
            response_content += f"📊 **Your Current Status:**\n"
            response_content += f"• Mastery rate: {mastery_rate:.0%}\n"
            response_content += f"• Learning velocity: {learning_velocity:.1f}x\n"
            response_content += f"• Concepts mastered: {performance_data.get('knowledge_graph_stats', {}).get('mastered_concepts', 0)}\n\n"
            
            # Personalized recommendations
            if recommendations:
                response_content += f"🌟 **Recommended Next Steps:**\n"
                for i, rec in enumerate(recommendations[:3], 1):
                    concept = rec.get('concept', 'Unknown')
                    score = rec.get('score', 0)
                    duration = rec.get('estimated_duration', 30)
                    difficulty = rec.get('difficulty_level', 1)
                    
                    response_content += f"{i}. **{concept}**\n"
                    response_content += f"   • Match score: {score:.0%}\n"
                    response_content += f"   • Estimated time: {duration} minutes\n"
                    response_content += f"   • Difficulty: Level {difficulty}\n\n"
            
            # Weak areas to focus on
            weak_areas = knowledge_gaps.get('weak_areas', [])
            if weak_areas:
                response_content += f"💪 **Areas to Strengthen:**\n"
                for area in weak_areas[:3]:
                    concept = area.get('concept', 'Unknown')
                    mastery = area.get('mastery_level', 0)
                    response_content += f"• {concept}: {mastery:.0%} mastery\n"
                response_content += "\n"
            
            response_content += "🚀 **What would you like to focus on?**\n"
            response_content += "I can create an interactive learning session tailored to your level!"
            
            return {
                "content": response_content,
                "message_type": "personalized_plan",
                "metadata": {
                    "recommendations": recommendations,
                    "weak_areas": weak_areas,
                    "personalization_score": 0.95
                },
                "concepts_discussed": [rec.get('concept', '') for rec in recommendations[:3]],
                "interactive_suggestions": [],
                "quality_score": 0.95,
                "helpfulness_score": 0.9
            }
            
        except Exception as e:
            return {
                "content": f"I can create a personalized learning plan based on your progress! What specific goals do you have for {subject.value}?",
                "message_type": "personalized_plan",
                "metadata": {"error": str(e)},
                "concepts_discussed": [],
                "interactive_suggestions": []
            }
    
    async def _handle_weakness_improvement(
        self, 
        content: str, 
        user_id: str, 
        subject: Subject, 
        performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle requests to improve weak areas"""
        try:
            knowledge_gaps = performance_data.get('knowledge_gaps', {})
            weak_areas = knowledge_gaps.get('weak_areas', [])
            
            if not weak_areas:
                return {
                    "content": f"Great news! You don't have any significant weak areas in {subject.value}. You're doing well! Would you like to explore advanced topics or review specific concepts?",
                    "message_type": "weakness_improvement",
                    "metadata": {"no_weak_areas": True},
                    "concepts_discussed": [],
                    "interactive_suggestions": []
                }
            
            response_content = f"💪 **Let's Strengthen Your Weak Areas!**\n\n"
            response_content += f"I've identified {len(weak_areas)} areas where focused practice will help:\n\n"
            
            for i, area in enumerate(weak_areas[:3], 1):
                concept = area.get('concept', 'Unknown')
                mastery = area.get('mastery_level', 0)
                attempts = area.get('attempts', 0)
                
                response_content += f"**{i}. {concept}**\n"
                response_content += f"   • Current mastery: {mastery:.0%}\n"
                response_content += f"   • Practice attempts: {attempts}\n"
                
                # Get learning path for this concept
                try:
                    learning_path = await self.neo4j.find_learning_path(user_id, concept)
                    if learning_path.path_nodes:
                        response_content += f"   • Prerequisites: {', '.join(learning_path.path_nodes[:-1])}\n"
                        response_content += f"   • Estimated time: {learning_path.estimated_duration} minutes\n"
                except:
                    pass
                
                response_content += "\n"
            
            response_content += "🎯 **Improvement Strategy:**\n"
            response_content += "1. Review prerequisites and fundamentals\n"
            response_content += "2. Practice with interactive simulations\n"
            response_content += "3. Solve progressively harder problems\n"
            response_content += "4. Regular review and assessment\n\n"
            
            response_content += "Which area would you like to work on first? I can create a targeted practice session!"
            
            return {
                "content": response_content,
                "message_type": "weakness_improvement",
                "metadata": {
                    "weak_areas": weak_areas,
                    "improvement_plan_available": True
                },
                "concepts_discussed": [area.get('concept', '') for area in weak_areas[:3]],
                "interactive_suggestions": [],
                "quality_score": 0.9,
                "helpfulness_score": 0.95
            }
            
        except Exception as e:
            return {
                "content": f"I can help you improve in areas where you're struggling! Let me analyze your performance and create a targeted improvement plan.",
                "message_type": "weakness_improvement",
                "metadata": {"error": str(e)},
                "concepts_discussed": [],
                "interactive_suggestions": []
            }
    
    async def _handle_greeting_enhanced(
        self, 
        content: str, 
        user_id: str, 
        subject: Subject, 
        conversation_context: str, 
        performance_data: Dict[str, Any],
        session_memory: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhanced greeting handler with memory integration"""
        basic_greeting = await self._handle_greeting(content, user_id, subject, conversation_context, performance_data)
        
        # Add memory-based personalization
        learning_history = session_memory.get('learning_history', [])
        if learning_history:
            last_session = learning_history[0]
            last_topic = last_session.content.get('context', {}).get('topic', '')
            
            if last_topic:
                basic_greeting["content"] += f"\n\n💡 Last time we worked on {last_topic}. Would you like to continue or explore something new?"
        
        basic_greeting["metadata"]["memory_enhanced"] = True
        basic_greeting["concepts_discussed"] = []
        
        return basic_greeting
    
    async def _handle_question_enhanced(
        self, 
        content: str, 
        user_id: str, 
        subject: Subject, 
        conversation_context: str, 
        performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhanced question handler with concept tracking"""
        basic_response = await self._handle_question(content, user_id, subject, conversation_context, performance_data)
        
        # Extract concepts from the response
        concepts_discussed = []
        if basic_response.get("metadata", {}).get("answer_data"):
            # Simple concept extraction from sources
            sources = basic_response["metadata"]["answer_data"].get("sources", [])
            for source in sources:
                chapter = source.get("chapter", "")
                if chapter:
                    concepts_discussed.append(chapter)
        
        basic_response["concepts_discussed"] = concepts_discussed
        basic_response["understanding_level"] = basic_response.get("metadata", {}).get("confidence", 0.7)
        
        return basic_response
    
    async def _handle_homework_help_enhanced(
        self, 
        content: str, 
        user_id: str, 
        subject: Subject, 
        conversation_context: str, 
        performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhanced homework help with concept tracking"""
        basic_response = await self._handle_homework_help(content, user_id, subject, conversation_context)
        
        # Add concept tracking
        basic_response["concepts_discussed"] = [subject.value]
        basic_response["understanding_level"] = 0.8
        
        return basic_response
    
    async def _handle_lesson_plan_request_enhanced(
        self, 
        content: str, 
        user_id: str, 
        subject: Subject, 
        performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhanced lesson plan request with knowledge graph integration"""
        basic_response = await self._handle_lesson_plan_request(content, user_id, subject, performance_data)
        
        # Add knowledge graph insights
        weak_areas = performance_data.get('knowledge_gaps', {}).get('weak_areas', [])
        basic_response["concepts_discussed"] = [area.get('concept', '') for area in weak_areas[:5]]
        
        return basic_response
    
    async def _handle_general_message_enhanced(
        self, 
        content: str, 
        user_id: str, 
        subject: Subject, 
        conversation_context: str, 
        performance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Enhanced general message handler"""
        basic_response = await self._handle_general_message(content, user_id, subject, conversation_context, performance_data)
        
        basic_response["concepts_discussed"] = []
        basic_response["interactive_suggestions"] = []
        
        return basic_response
    
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
            
            if self.gemini_enabled and self.model:
                response = self.model.generate_content(prompt)
                return {
                    "content": response.text,
                    "message_type": "greeting",
                    "metadata": {
                        "gemini_used": True,
                        "rag_used": False
                    }
                }
            else:
                # Fallback greeting without Gemini
                return {
                    "content": f"Hello {student_name}! I'm your enhanced AI tutor for {subject.value} with persistent memory and knowledge graph capabilities. I can remember our conversations, track your progress, and provide personalized learning experiences. How can I help you today?",
                    "message_type": "greeting",
                    "metadata": {
                        "gemini_used": False,
                        "rag_used": False,
                        "fallback_used": True
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
            
            if self.gemini_enabled and self.model:
                response = self.model.generate_content(prompt)
                plan_text = response.text
                
                # Parse JSON
                json_match = re.search(r'\{.*\}', plan_text, re.DOTALL)
                if json_match:
                    plan_data = json.loads(json_match.group())
                else:
                    raise APIException(
                        code="PARSE_LESSON_PLAN_ERROR",
                        message="Failed to parse lesson plan",
                        status_code=500
                    )
            else:
                # Fallback lesson plan without Gemini
                plan_data = {
                    "plan_name": f"Personalized {subject.value} Plan",
                    "duration_days": days,
                    "total_hours": days * hours_per_day,
                    "focus_strategy": "Balanced learning approach",
                    "daily_schedule": [
                        {
                            "day": i + 1,
                            "date": (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d"),
                            "focus_areas": [f"Topic {i+1}"],
                            "activities": [
                                {
                                    "type": "concept_learning",
                                    "topic": f"Topic {i+1}",
                                    "duration_minutes": int(hours_per_day * 30),
                                    "description": "Learn core concepts",
                                    "resources": ["Study materials"]
                                },
                                {
                                    "type": "practice",
                                    "topic": f"Topic {i+1}",
                                    "duration_minutes": int(hours_per_day * 30),
                                    "difficulty": "medium",
                                    "question_count": 10,
                                    "description": "Practice problems"
                                }
                            ],
                            "goals": [f"Master Topic {i+1}"],
                            "estimated_hours": hours_per_day
                        }
                        for i in range(days)
                    ],
                    "weak_topics_focus": [t.get('topic_id') for t in weak_topics[:5]],
                    "learning_objectives": ["Improve understanding", "Practice regularly"]
                }
            
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
            
            if self.gemini_enabled and self.model:
                response = self.model.generate_content(prompt)
                plan_text = response.text
                
                # Parse JSON
                json_match = re.search(r'\{.*\}', plan_text, re.DOTALL)
                if json_match:
                    plan_data = json.loads(json_match.group())
                else:
                    raise APIException(
                        code="PARSE_LESSON_PLAN_RESPONSE_ERROR",
                        message="Failed to parse lesson plan response",
                        status_code=500
                    )
            else:
                # Fallback lesson plan without Gemini
                plan_data = {
                    "plan_name": f"Personalized {subject.value} Improvement Plan",
                    "duration_days": days,
                    "total_hours": days * hours_per_day,
                    "focus_strategy": "60% weak areas, 20% new topics, 20% reinforcement",
                    "daily_schedule": [
                        {
                            "day": i + 1,
                            "date": (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d"),
                            "focus_areas": [f"Focus Area {i+1}"],
                            "activities": [
                                {
                                    "type": "concept_learning",
                                    "topic": f"Topic {i+1}",
                                    "duration_minutes": int(hours_per_day * 20),
                                    "description": "Learn core concepts",
                                    "resources": ["NCERT", "Practice problems"]
                                },
                                {
                                    "type": "practice",
                                    "topic": f"Topic {i+1}",
                                    "duration_minutes": int(hours_per_day * 30),
                                    "difficulty": "medium",
                                    "question_count": 10,
                                    "description": "Practice problems"
                                },
                                {
                                    "type": "weak_area_focus",
                                    "topic": "weak_topic",
                                    "duration_minutes": int(hours_per_day * 10),
                                    "description": "Extra practice on weak area"
                                }
                            ],
                            "goals": [f"Master concept {i+1}", "Solve practice problems"],
                            "estimated_hours": hours_per_day,
                            "review_topics": [f"previous_topic_{i}"] if i > 0 else []
                        }
                        for i in range(days)
                    ],
                    "review_schedule": [
                        {"day": 3, "topics": ["topic1", "topic2"], "type": "quick_review"},
                        {"day": 6, "topics": ["all_week_topics"], "type": "comprehensive_review"}
                    ],
                    "assessment_checkpoints": [
                        {"day": 3, "type": "quiz", "topics": ["topic1", "topic2"], "marks": 20, "duration_minutes": 30},
                        {"day": 7, "type": "test", "topics": ["all_week"], "marks": 50, "duration_minutes": 60}
                    ],
                    "weak_topics_focus": [t.get('topic_id') for t in performance_data.get('weak_topics', [])[:5]],
                    "learning_objectives": ["Improve weak areas", "Build strong foundation"]
                }
            
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
            raise APIException(
                code="GENERATE_LESSON_PLAN_ERROR",
                message=f"Error generating lesson plan: {str(e)}",
                status_code=500
            )
    
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
            raise APIException(
                code="FETCH_LESSON_PLANS_ERROR",
                message=f"Error fetching lesson plans: {str(e)}",
                status_code=500
            )
    
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
            raise APIException(
                code="FETCH_STUDENT_SESSIONS_ERROR",
                message=f"Error fetching student sessions: {str(e)}",
                status_code=500
            )
    
    async def create_interactive_learning_session(
        self,
        user_id: str,
        component_ids: List[str],
        preferences: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create an interactive learning session from the chat interface"""
        try:
            # Get user's performance data for personalization
            user_stats = await self.neo4j.get_user_learning_stats(user_id)
            
            # Set default preferences based on user data
            if not preferences:
                preferences = {
                    "difficulty_preference": min(max(1, int(user_stats.get('average_performance', 0.5) * 5)), 5),
                    "learning_style": "visual",  # Can be enhanced with user preference tracking
                    "pace_preference": "medium"
                }
            
            # Create interactive session
            session_id = await self.interactive_service.create_learning_session(
                user_id=user_id,
                components=component_ids,
                preferences=preferences
            )
            
            # Store session creation in MemMachine
            session_context = LearningContext(
                user_id=user_id,
                session_id=session_id,
                subject="interactive_learning",
                topic="component_session",
                difficulty_level=preferences.get("difficulty_preference", 3),
                learning_objectives=["interactive_practice", "skill_building"],
                previous_knowledge=user_stats,
                current_progress={"session_created": True}
            )
            
            await self.memmachine.store_learning_session(session_context, {
                "session_type": "interactive_learning",
                "components": component_ids,
                "preferences": preferences,
                "performance_metrics": {
                    "session_created": True,
                    "engagement_score": 1.0
                }
            })
            
            return {
                "success": True,
                "session_id": session_id,
                "components": component_ids,
                "preferences": preferences,
                "message": f"Interactive learning session created with {len(component_ids)} components!"
            }
            
        except Exception as e:
            raise APIException(
                code="CREATE_INTERACTIVE_SESSION_ERROR",
                message=f"Error creating interactive session: {str(e)}",
                status_code=500
            )
    
    async def get_learning_insights(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive learning insights combining all intelligence sources"""
        try:
            # Get data from all sources
            learning_patterns = await self.memmachine.analyze_learning_patterns(user_id)
            user_stats = await self.neo4j.get_user_learning_stats(user_id)
            knowledge_gaps = await self.neo4j.analyze_knowledge_gaps(user_id)
            recommendations = await self.neo4j.recommend_next_concepts(user_id, limit=10)
            
            # Combine insights
            insights = {
                "memory_insights": learning_patterns,
                "knowledge_graph_insights": {
                    "user_stats": user_stats,
                    "knowledge_gaps": knowledge_gaps,
                    "recommendations": recommendations
                },
                "combined_analysis": {
                    "total_learning_sessions": learning_patterns.get('total_sessions', 0),
                    "mastery_rate": user_stats.get('mastery_rate', 0),
                    "learning_velocity": max(
                        learning_patterns.get('learning_velocity', 1.0),
                        user_stats.get('learning_velocity', 1.0)
                    ),
                    "focus_areas": knowledge_gaps.get('weak_areas', [])[:5],
                    "next_recommendations": recommendations[:5]
                },
                "generated_at": datetime.now().isoformat()
            }
            
            return insights
            
        except Exception as e:
            raise APIException(
                code="GET_INSIGHTS_ERROR",
                message=f"Error getting learning insights: {str(e)}",
                status_code=500
            )

