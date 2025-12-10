"""Collaborative learning service for Magic Learn platform"""

import asyncio
import json
import time
import uuid
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
import redis
from dataclasses import dataclass, asdict
import google.generativeai as genai
import os

from app.models.magic_learn import (
    CollaborativeSessionRequest, CollaborativeSessionResponse,
    LearningPathRequest, LearningPathResponse,
    AITutorRequest, AITutorResponse,
    DifficultyLevel, AnalysisType
)

# Configure Redis for real-time collaboration (fallback to in-memory if not available)
try:
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        decode_responses=True
    )
    redis_client.ping()
    REDIS_AVAILABLE = True
    print("✅ Redis connected for collaborative features")
except:
    redis_client = None
    REDIS_AVAILABLE = False
    print("⚠️ Redis not available, using in-memory storage for collaboration")

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


@dataclass
class CollaborativeSession:
    """Data class for collaborative session"""
    session_id: str
    session_name: str
    creator_id: str
    participants: List[str]
    session_type: str
    created_at: datetime
    expires_at: datetime
    join_code: str
    max_participants: int
    current_activity: Optional[str] = None
    shared_canvas: Optional[str] = None
    chat_messages: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.chat_messages is None:
            self.chat_messages = []


@dataclass
class ParticipantState:
    """Data class for participant state in collaborative session"""
    user_id: str
    session_id: str
    joined_at: datetime
    last_active: datetime
    current_tool: str
    cursor_position: Optional[Dict[str, float]] = None
    drawing_state: Optional[Dict[str, Any]] = None


class CollaborativeLearningService:
    """Service for managing collaborative learning sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, CollaborativeSession] = {}
        self.participants: Dict[str, ParticipantState] = {}
        self.session_locks = {}
        
    async def create_session(self, request: CollaborativeSessionRequest) -> CollaborativeSessionResponse:
        """Create a new collaborative learning session"""
        
        try:
            session_id = str(uuid.uuid4())
            join_code = self._generate_join_code()
            
            # Calculate expiration time
            expires_at = datetime.utcnow() + timedelta(minutes=request.duration_minutes or 60)
            
            # Create session
            session = CollaborativeSession(
                session_id=session_id,
                session_name=request.session_name,
                creator_id=request.participants[0] if request.participants else "anonymous",
                participants=request.participants,
                session_type=request.session_type,
                created_at=datetime.utcnow(),
                expires_at=expires_at,
                join_code=join_code,
                max_participants=request.max_participants
            )
            
            # Store session
            await self._store_session(session)
            
            # Generate session URL
            session_url = f"/magic-learn/collaborate/{session_id}?code={join_code}"
            
            return CollaborativeSessionResponse(
                success=True,
                session_id=session_id,
                join_code=join_code,
                session_url=session_url,
                expires_at=expires_at
            )
            
        except Exception as e:
            return CollaborativeSessionResponse(
                success=False,
                session_id="",
                join_code="",
                session_url="",
                expires_at=datetime.utcnow()
            )
    
    async def join_session(self, session_id: str, user_id: str, join_code: str) -> Dict[str, Any]:
        """Join an existing collaborative session"""
        
        try:
            session = await self._get_session(session_id)
            
            if not session:
                return {"success": False, "error": "Session not found"}
            
            if session.join_code != join_code:
                return {"success": False, "error": "Invalid join code"}
            
            if datetime.utcnow() > session.expires_at:
                return {"success": False, "error": "Session has expired"}
            
            if len(session.participants) >= session.max_participants:
                return {"success": False, "error": "Session is full"}
            
            # Add participant if not already in session
            if user_id not in session.participants:
                session.participants.append(user_id)
                await self._store_session(session)
            
            # Create participant state
            participant = ParticipantState(
                user_id=user_id,
                session_id=session_id,
                joined_at=datetime.utcnow(),
                last_active=datetime.utcnow(),
                current_tool="none"
            )
            
            await self._store_participant(participant)
            
            return {
                "success": True,
                "session": asdict(session),
                "participant_count": len(session.participants)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def leave_session(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """Leave a collaborative session"""
        
        try:
            session = await self._get_session(session_id)
            
            if session and user_id in session.participants:
                session.participants.remove(user_id)
                await self._store_session(session)
            
            # Remove participant state
            await self._remove_participant(user_id, session_id)
            
            return {"success": True, "message": "Left session successfully"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def update_participant_state(self, session_id: str, user_id: str, 
                                     state_update: Dict[str, Any]) -> Dict[str, Any]:
        """Update participant state in real-time"""
        
        try:
            participant = await self._get_participant(user_id, session_id)
            
            if not participant:
                return {"success": False, "error": "Participant not found"}
            
            # Update state
            participant.last_active = datetime.utcnow()
            
            if "current_tool" in state_update:
                participant.current_tool = state_update["current_tool"]
            
            if "cursor_position" in state_update:
                participant.cursor_position = state_update["cursor_position"]
            
            if "drawing_state" in state_update:
                participant.drawing_state = state_update["drawing_state"]
            
            await self._store_participant(participant)
            
            # Broadcast update to other participants
            await self._broadcast_participant_update(session_id, user_id, state_update)
            
            return {"success": True, "message": "State updated"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def send_chat_message(self, session_id: str, user_id: str, message: str) -> Dict[str, Any]:
        """Send a chat message in collaborative session"""
        
        try:
            session = await self._get_session(session_id)
            
            if not session:
                return {"success": False, "error": "Session not found"}
            
            if user_id not in session.participants:
                return {"success": False, "error": "Not a participant"}
            
            # Create message
            chat_message = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "type": "text"
            }
            
            # Add to session chat
            session.chat_messages.append(chat_message)
            await self._store_session(session)
            
            # Broadcast message
            await self._broadcast_chat_message(session_id, chat_message)
            
            return {"success": True, "message_id": chat_message["id"]}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def update_shared_canvas(self, session_id: str, user_id: str, 
                                 canvas_data: str) -> Dict[str, Any]:
        """Update shared canvas in collaborative session"""
        
        try:
            session = await self._get_session(session_id)
            
            if not session:
                return {"success": False, "error": "Session not found"}
            
            if user_id not in session.participants:
                return {"success": False, "error": "Not a participant"}
            
            # Update shared canvas
            session.shared_canvas = canvas_data
            await self._store_session(session)
            
            # Broadcast canvas update
            await self._broadcast_canvas_update(session_id, canvas_data, user_id)
            
            return {"success": True, "message": "Canvas updated"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_session_state(self, session_id: str, user_id: str) -> Dict[str, Any]:
        """Get current session state for a participant"""
        
        try:
            session = await self._get_session(session_id)
            
            if not session:
                return {"success": False, "error": "Session not found"}
            
            if user_id not in session.participants:
                return {"success": False, "error": "Not a participant"}
            
            # Get all participants' states
            participant_states = []
            for participant_id in session.participants:
                participant = await self._get_participant(participant_id, session_id)
                if participant:
                    participant_states.append(asdict(participant))
            
            return {
                "success": True,
                "session": asdict(session),
                "participants": participant_states,
                "chat_messages": session.chat_messages[-50:],  # Last 50 messages
                "shared_canvas": session.shared_canvas
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _generate_join_code(self) -> str:
        """Generate a unique join code"""
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    async def _store_session(self, session: CollaborativeSession):
        """Store session data"""
        if REDIS_AVAILABLE:
            await self._store_session_redis(session)
        else:
            self.sessions[session.session_id] = session
    
    async def _get_session(self, session_id: str) -> Optional[CollaborativeSession]:
        """Retrieve session data"""
        if REDIS_AVAILABLE:
            return await self._get_session_redis(session_id)
        else:
            return self.sessions.get(session_id)
    
    async def _store_participant(self, participant: ParticipantState):
        """Store participant state"""
        if REDIS_AVAILABLE:
            await self._store_participant_redis(participant)
        else:
            key = f"{participant.user_id}_{participant.session_id}"
            self.participants[key] = participant
    
    async def _get_participant(self, user_id: str, session_id: str) -> Optional[ParticipantState]:
        """Retrieve participant state"""
        if REDIS_AVAILABLE:
            return await self._get_participant_redis(user_id, session_id)
        else:
            key = f"{user_id}_{session_id}"
            return self.participants.get(key)
    
    async def _remove_participant(self, user_id: str, session_id: str):
        """Remove participant state"""
        if REDIS_AVAILABLE:
            await self._remove_participant_redis(user_id, session_id)
        else:
            key = f"{user_id}_{session_id}"
            if key in self.participants:
                del self.participants[key]
    
    # Redis-specific methods
    async def _store_session_redis(self, session: CollaborativeSession):
        """Store session in Redis"""
        try:
            session_data = asdict(session)
            # Convert datetime objects to ISO strings
            session_data['created_at'] = session.created_at.isoformat()
            session_data['expires_at'] = session.expires_at.isoformat()
            
            redis_client.setex(
                f"session:{session.session_id}",
                int((session.expires_at - datetime.utcnow()).total_seconds()),
                json.dumps(session_data)
            )
        except Exception as e:
            print(f"Redis store session error: {e}")
    
    async def _get_session_redis(self, session_id: str) -> Optional[CollaborativeSession]:
        """Get session from Redis"""
        try:
            session_data = redis_client.get(f"session:{session_id}")
            if session_data:
                data = json.loads(session_data)
                # Convert ISO strings back to datetime objects
                data['created_at'] = datetime.fromisoformat(data['created_at'])
                data['expires_at'] = datetime.fromisoformat(data['expires_at'])
                return CollaborativeSession(**data)
            return None
        except Exception as e:
            print(f"Redis get session error: {e}")
            return None
    
    async def _store_participant_redis(self, participant: ParticipantState):
        """Store participant in Redis"""
        try:
            participant_data = asdict(participant)
            # Convert datetime objects to ISO strings
            participant_data['joined_at'] = participant.joined_at.isoformat()
            participant_data['last_active'] = participant.last_active.isoformat()
            
            redis_client.setex(
                f"participant:{participant.user_id}:{participant.session_id}",
                3600,  # 1 hour expiry
                json.dumps(participant_data)
            )
        except Exception as e:
            print(f"Redis store participant error: {e}")
    
    async def _get_participant_redis(self, user_id: str, session_id: str) -> Optional[ParticipantState]:
        """Get participant from Redis"""
        try:
            participant_data = redis_client.get(f"participant:{user_id}:{session_id}")
            if participant_data:
                data = json.loads(participant_data)
                # Convert ISO strings back to datetime objects
                data['joined_at'] = datetime.fromisoformat(data['joined_at'])
                data['last_active'] = datetime.fromisoformat(data['last_active'])
                return ParticipantState(**data)
            return None
        except Exception as e:
            print(f"Redis get participant error: {e}")
            return None
    
    async def _remove_participant_redis(self, user_id: str, session_id: str):
        """Remove participant from Redis"""
        try:
            redis_client.delete(f"participant:{user_id}:{session_id}")
        except Exception as e:
            print(f"Redis remove participant error: {e}")
    
    # Broadcasting methods (would integrate with WebSocket in production)
    async def _broadcast_participant_update(self, session_id: str, user_id: str, update: Dict[str, Any]):
        """Broadcast participant state update to other participants"""
        # In production, this would use WebSocket connections
        print(f"Broadcasting participant update for {user_id} in session {session_id}: {update}")
    
    async def _broadcast_chat_message(self, session_id: str, message: Dict[str, Any]):
        """Broadcast chat message to all participants"""
        # In production, this would use WebSocket connections
        print(f"Broadcasting chat message in session {session_id}: {message}")
    
    async def _broadcast_canvas_update(self, session_id: str, canvas_data: str, user_id: str):
        """Broadcast canvas update to all participants"""
        # In production, this would use WebSocket connections
        print(f"Broadcasting canvas update from {user_id} in session {session_id}")


class AITutorService:
    """Advanced AI tutor service with personalized learning"""
    
    def __init__(self):
        self.conversation_history = {}
        self.learning_profiles = {}
    
    async def chat_with_tutor(self, request: AITutorRequest) -> AITutorResponse:
        """Have a conversation with the AI tutor"""
        
        if not GEMINI_API_KEY:
            return AITutorResponse(
                success=False,
                response="AI tutor service is not available",
                explanation_type="error",
                follow_up_questions=[],
                related_concepts=[],
                practice_problems=[],
                confidence_score=0.0
            )
        
        try:
            # Get conversation history
            history = self.conversation_history.get(request.user_id, [])
            
            # Create personalized prompt
            prompt = await self._create_tutor_prompt(request, history)
            
            # Generate response with Gemini
            model = genai.GenerativeModel('gemini-2.5-flash-lite')
            response = model.generate_content([prompt])
            
            # Parse and structure the response
            structured_response = await self._structure_tutor_response(
                response.text, request.question, request.subject
            )
            
            # Update conversation history
            history.append({
                "question": request.question,
                "response": structured_response["response"],
                "timestamp": datetime.utcnow().isoformat()
            })
            self.conversation_history[request.user_id] = history[-10:]  # Keep last 10 exchanges
            
            return AITutorResponse(
                success=True,
                response=structured_response["response"],
                explanation_type=structured_response["explanation_type"],
                follow_up_questions=structured_response["follow_up_questions"],
                related_concepts=structured_response["related_concepts"],
                practice_problems=structured_response["practice_problems"],
                confidence_score=structured_response["confidence_score"]
            )
            
        except Exception as e:
            return AITutorResponse(
                success=False,
                response=f"I apologize, but I encountered an error: {str(e)}",
                explanation_type="error",
                follow_up_questions=[],
                related_concepts=[],
                practice_problems=[],
                confidence_score=0.0
            )
    
    async def _create_tutor_prompt(self, request: AITutorRequest, history: List[Dict]) -> str:
        """Create a personalized tutor prompt"""
        
        # Build context from history
        context = ""
        if history:
            context = "Previous conversation:\n"
            for exchange in history[-3:]:  # Last 3 exchanges
                context += f"Student: {exchange['question']}\n"
                context += f"Tutor: {exchange['response'][:200]}...\n\n"
        
        # Create difficulty-appropriate prompt
        difficulty_guidance = {
            DifficultyLevel.BEGINNER: "Use simple language, provide lots of examples, and break down concepts into small steps.",
            DifficultyLevel.INTERMEDIATE: "Provide clear explanations with examples and some technical detail.",
            DifficultyLevel.ADVANCED: "Use appropriate technical language and provide in-depth analysis.",
            DifficultyLevel.EXPERT: "Engage in sophisticated discussion with advanced concepts and applications."
        }
        
        prompt = f"""You are an expert AI tutor specializing in {request.subject or 'general education'}. 

{context}

Current Question: {request.question}

Additional Context: {request.context or 'None provided'}

Student Level: {request.difficulty_level.value}
Learning Style: {request.learning_style or 'Not specified'}

Instructions:
{difficulty_guidance.get(request.difficulty_level, difficulty_guidance[DifficultyLevel.INTERMEDIATE])}

Please provide:
1. A clear, helpful response to the student's question
2. The type of explanation you're providing (conceptual, procedural, example-based, etc.)
3. 2-3 follow-up questions to deepen understanding
4. Related concepts the student might want to explore
5. 1-2 practice problems if appropriate

Format your response as a helpful tutor would, being encouraging and supportive while maintaining academic rigor appropriate to the student's level."""

        return prompt
    
    async def _structure_tutor_response(self, response_text: str, question: str, subject: str) -> Dict[str, Any]:
        """Structure the tutor response into components"""
        
        # Extract different components from the response
        # This is a simplified version - in production, you'd use more sophisticated NLP
        
        lines = response_text.split('\n')
        response_parts = {
            "response": response_text,
            "explanation_type": await self._classify_explanation_type(response_text),
            "follow_up_questions": await self._extract_follow_up_questions(response_text),
            "related_concepts": await self._extract_related_concepts(response_text, subject),
            "practice_problems": await self._extract_practice_problems(response_text),
            "confidence_score": await self._calculate_response_confidence(response_text, question)
        }
        
        return response_parts
    
    async def _classify_explanation_type(self, response: str) -> str:
        """Classify the type of explanation provided"""
        response_lower = response.lower()
        
        if any(word in response_lower for word in ['step', 'first', 'then', 'next', 'finally']):
            return "procedural"
        elif any(word in response_lower for word in ['example', 'for instance', 'imagine', 'consider']):
            return "example_based"
        elif any(word in response_lower for word in ['concept', 'theory', 'principle', 'definition']):
            return "conceptual"
        elif any(word in response_lower for word in ['solve', 'calculate', 'compute', 'find']):
            return "problem_solving"
        else:
            return "general_explanation"
    
    async def _extract_follow_up_questions(self, response: str) -> List[str]:
        """Extract follow-up questions from the response"""
        questions = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.endswith('?') and len(line) > 10:
                # Clean up the question
                if line.startswith(('- ', '* ', '1. ', '2. ', '3. ')):
                    line = line[2:].strip()
                questions.append(line)
        
        # Generate some default follow-up questions if none found
        if not questions:
            questions = [
                "Can you think of a real-world application for this concept?",
                "What would happen if we changed one of the variables?",
                "How does this relate to what you already know?"
            ]
        
        return questions[:3]  # Limit to 3 questions
    
    async def _extract_related_concepts(self, response: str, subject: str) -> List[str]:
        """Extract related concepts from the response"""
        concepts = []
        
        # Subject-specific concept extraction
        if subject and subject.lower() == 'mathematics':
            math_concepts = ['algebra', 'geometry', 'calculus', 'statistics', 'trigonometry', 'probability']
            for concept in math_concepts:
                if concept in response.lower():
                    concepts.append(concept.title())
        
        # General concept extraction
        concept_indicators = ['related to', 'similar to', 'connects to', 'builds on']
        for indicator in concept_indicators:
            if indicator in response.lower():
                # Extract text after the indicator
                parts = response.lower().split(indicator)
                if len(parts) > 1:
                    following_text = parts[1][:100]  # First 100 chars
                    # Extract potential concepts (simplified)
                    words = following_text.split()
                    for word in words[:5]:  # First 5 words
                        if len(word) > 3 and word.isalpha():
                            concepts.append(word.title())
        
        return list(set(concepts))[:5]  # Unique concepts, max 5
    
    async def _extract_practice_problems(self, response: str) -> List[Dict[str, Any]]:
        """Extract practice problems from the response"""
        problems = []
        
        # Look for practice problem indicators
        if any(phrase in response.lower() for phrase in ['practice', 'try', 'exercise', 'problem']):
            # This is simplified - in production, you'd use more sophisticated extraction
            problems.append({
                "problem": "Apply the same concept to a similar scenario",
                "difficulty": "medium",
                "hints": ["Use the same approach", "Check your work step by step"]
            })
        
        return problems
    
    async def _calculate_response_confidence(self, response: str, question: str) -> float:
        """Calculate confidence score for the response"""
        
        # Simple heuristic based on response quality indicators
        confidence = 0.5  # Base confidence
        
        # Length indicates thoroughness
        if len(response) > 200:
            confidence += 0.2
        if len(response) > 500:
            confidence += 0.1
        
        # Presence of examples
        if any(word in response.lower() for word in ['example', 'for instance', 'such as']):
            confidence += 0.1
        
        # Structured response
        if any(word in response for word in ['1.', '2.', '3.', '-', '*']):
            confidence += 0.1
        
        # Mathematical notation (if applicable)
        if any(char in response for char in ['=', '+', '-', '×', '÷', '$']):
            confidence += 0.1
        
        return min(confidence, 1.0)  # Cap at 1.0


# Service instances
collaborative_service = CollaborativeLearningService()
ai_tutor_service = AITutorService()