"""
Memory Intelligence Router
Provides endpoints for MemVerge MemMachine and Neo4j Graph Database features
"""

from fastapi import APIRouter, HTTPException, Query, Body
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

from app.services.memmachine_service import get_memmachine_service, LearningContext
from app.services.neo4j_service import get_neo4j_service
from app.services.interactive_learning_service import get_interactive_learning_service
from app.utils.interactive_dashboard import get_interactive_dashboard
from app.models.memory_intelligence import (
    ContextData, ContextResponse, SmartSuggestion, UserInsights,
    TimelineEvent, TimelineSummary, BulkContextRequest,
    RememberContextResponse, RecallContextResponse, SmartSuggestionsResponse,
    BulkRememberResponse, UserTimelineResponse, ContextType, SuggestionType
)

router = APIRouter()

# MemMachine Endpoints
@router.post("/memory/store-session")
async def store_learning_session(
    user_id: str = Query(..., description="User ID"),
    session_data: Dict[str, Any] = Body(..., description="Learning session data")
):
    """Store a complete learning session in persistent memory"""
    try:
        memmachine = get_memmachine_service()
        
        # Create learning context
        context = LearningContext(
            user_id=user_id,
            session_id=session_data.get('session_id', f"session_{datetime.now().isoformat()}"),
            subject=session_data.get('subject', 'general'),
            topic=session_data.get('topic', 'unknown'),
            difficulty_level=session_data.get('difficulty_level', 1),
            learning_objectives=session_data.get('learning_objectives', []),
            previous_knowledge=session_data.get('previous_knowledge', {}),
            current_progress=session_data.get('current_progress', {})
        )
        
        memory_id = await memmachine.store_learning_session(context, session_data)
        
        return {
            "success": True,
            "memory_id": memory_id,
            "message": "Learning session stored successfully in persistent memory"
        }
    
    except Exception as e:
        logging.error(f"Error storing learning session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memory/learning-history/{user_id}")
async def get_learning_history(
    user_id: str,
    subject: Optional[str] = Query(None, description="Filter by subject"),
    days_back: int = Query(30, description="Days to look back"),
    limit: int = Query(50, description="Maximum number of sessions")
):
    """Get user's learning history from persistent memory"""
    try:
        memmachine = get_memmachine_service()
        
        history = await memmachine.get_user_learning_history(
            user_id=user_id,
            subject=subject,
            days_back=days_back,
            limit=limit
        )
        
        # Format history for response
        formatted_history = []
        for entry in history:
            formatted_history.append({
                "memory_id": entry.id,
                "timestamp": entry.timestamp.isoformat(),
                "subject": entry.content['context']['subject'],
                "topic": entry.content['context']['topic'],
                "difficulty_level": entry.content['context']['difficulty_level'],
                "performance_metrics": entry.content['session_data'].get('performance_metrics', {}),
                "duration": entry.content['session_data'].get('duration', 0),
                "completion_rate": entry.content['session_data'].get('completion_rate', 0.0),
                "importance_score": entry.importance_score,
                "access_count": entry.access_count
            })
        
        return {
            "success": True,
            "user_id": user_id,
            "total_sessions": len(formatted_history),
            "history": formatted_history
        }
    
    except Exception as e:
        logging.error(f"Error retrieving learning history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memory/learning-patterns/{user_id}")
async def analyze_learning_patterns(user_id: str):
    """Analyze user's learning patterns from persistent memory"""
    try:
        memmachine = get_memmachine_service()
        
        patterns = await memmachine.analyze_learning_patterns(user_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "analysis": patterns,
            "generated_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        logging.error(f"Error analyzing learning patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memory/stats")
async def get_memory_statistics():
    """Get statistics about memory usage and storage"""
    try:
        memmachine = get_memmachine_service()
        
        stats = await memmachine.get_memory_stats()
        
        return {
            "success": True,
            "statistics": stats,
            "generated_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        logging.error(f"Error retrieving memory statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Neo4j Knowledge Graph Endpoints
@router.post("/knowledge-graph/create-concept")
async def create_concept(
    name: str = Query(..., description="Concept name"),
    concept_type: str = Query(..., description="Type of concept"),
    properties: Dict[str, Any] = Body(default={}, description="Additional properties"),
    difficulty_level: int = Query(1, description="Difficulty level (1-5)")
):
    """Create a new concept in the knowledge graph"""
    try:
        neo4j_service = get_neo4j_service()
        
        concept_id = await neo4j_service.create_concept_node(
            name=name,
            concept_type=concept_type,
            properties=properties,
            difficulty_level=difficulty_level
        )
        
        return {
            "success": True,
            "concept_id": concept_id,
            "message": f"Concept '{name}' created successfully"
        }
    
    except Exception as e:
        logging.error(f"Error creating concept: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/knowledge-graph/create-relationship")
async def create_relationship(
    source_concept: str = Query(..., description="Source concept name"),
    target_concept: str = Query(..., description="Target concept name"),
    relationship_type: str = Query(..., description="Type of relationship"),
    strength: float = Query(1.0, description="Relationship strength"),
    properties: Dict[str, Any] = Body(default={}, description="Additional properties")
):
    """Create a relationship between two concepts"""
    try:
        neo4j_service = get_neo4j_service()
        
        success = await neo4j_service.create_relationship(
            source_name=source_concept,
            target_name=target_concept,
            relationship_type=relationship_type,
            strength=strength,
            properties=properties
        )
        
        if success:
            return {
                "success": True,
                "message": f"Relationship created: {source_concept} -{relationship_type}-> {target_concept}"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to create relationship")
    
    except Exception as e:
        logging.error(f"Error creating relationship: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-graph/learning-path/{user_id}")
async def find_learning_path(
    user_id: str,
    target_concept: str = Query(..., description="Target concept to learn"),
    current_knowledge: List[str] = Query(default=[], description="Currently known concepts")
):
    """Find optimal learning path to target concept"""
    try:
        neo4j_service = get_neo4j_service()
        
        learning_path = await neo4j_service.find_learning_path(
            user_id=user_id,
            target_concept=target_concept,
            current_knowledge=current_knowledge
        )
        
        return {
            "success": True,
            "learning_path": {
                "user_id": learning_path.user_id,
                "target_concept": learning_path.target_concept,
                "path_nodes": learning_path.path_nodes,
                "estimated_duration": learning_path.estimated_duration,
                "difficulty_progression": learning_path.difficulty_progression,
                "confidence_score": learning_path.confidence_score
            }
        }
    
    except Exception as e:
        logging.error(f"Error finding learning path: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-graph/recommendations/{user_id}")
async def get_learning_recommendations(
    user_id: str,
    limit: int = Query(5, description="Number of recommendations")
):
    """Get personalized learning recommendations"""
    try:
        neo4j_service = get_neo4j_service()
        
        recommendations = await neo4j_service.recommend_next_concepts(
            user_id=user_id,
            limit=limit
        )
        
        return {
            "success": True,
            "user_id": user_id,
            "recommendations": recommendations
        }
    
    except Exception as e:
        logging.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/knowledge-graph/update-progress")
async def update_user_progress(
    user_id: str = Query(..., description="User ID"),
    concept_name: str = Query(..., description="Concept name"),
    performance_data: Dict[str, Any] = Body(..., description="Performance data")
):
    """Update user's progress on a specific concept"""
    try:
        neo4j_service = get_neo4j_service()
        
        await neo4j_service.update_user_progress(
            user_id=user_id,
            concept_name=concept_name,
            performance_data=performance_data
        )
        
        return {
            "success": True,
            "message": f"Progress updated for {user_id} on {concept_name}"
        }
    
    except Exception as e:
        logging.error(f"Error updating progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-graph/user-stats/{user_id}")
async def get_user_learning_stats(user_id: str):
    """Get comprehensive learning statistics for a user"""
    try:
        neo4j_service = get_neo4j_service()
        
        stats = await neo4j_service.get_user_learning_stats(user_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "statistics": stats
        }
    
    except Exception as e:
        logging.error(f"Error getting user stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-graph/concept-relationships/{concept_name}")
async def get_concept_relationships(concept_name: str):
    """Get all relationships for a specific concept"""
    try:
        neo4j_service = get_neo4j_service()
        
        relationships = await neo4j_service.get_concept_relationships(concept_name)
        
        return {
            "success": True,
            "concept": concept_name,
            "relationships": relationships
        }
    
    except Exception as e:
        logging.error(f"Error getting concept relationships: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-graph/knowledge-gaps/{user_id}")
async def analyze_knowledge_gaps(user_id: str):
    """Analyze knowledge gaps and suggest improvements"""
    try:
        neo4j_service = get_neo4j_service()
        
        gaps = await neo4j_service.analyze_knowledge_gaps(user_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "knowledge_gaps": gaps
        }
    
    except Exception as e:
        logging.error(f"Error analyzing knowledge gaps: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-graph/stats")
async def get_graph_statistics():
    """Get statistics about the knowledge graph"""
    try:
        neo4j_service = get_neo4j_service()
        
        stats = await neo4j_service.get_graph_statistics()
        
        return {
            "success": True,
            "graph_statistics": stats
        }
    
    except Exception as e:
        logging.error(f"Error getting graph statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Interactive Learning Endpoints
@router.post("/interactive/create-session")
async def create_interactive_session(
    user_id: str = Query(..., description="User ID"),
    components: List[str] = Body(..., description="List of component IDs"),
    preferences: Dict[str, Any] = Body(default={}, description="User preferences")
):
    """Create a new interactive learning session"""
    try:
        interactive_service = get_interactive_learning_service()
        
        session_id = await interactive_service.create_learning_session(
            user_id=user_id,
            components=components,
            preferences=preferences
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "message": "Interactive learning session created successfully"
        }
    
    except Exception as e:
        logging.error(f"Error creating interactive session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/interactive/process-interaction")
async def process_interaction(
    session_id: str = Query(..., description="Session ID"),
    interaction_data: Dict[str, Any] = Body(..., description="Interaction data")
):
    """Process user interaction and provide real-time feedback"""
    try:
        interactive_service = get_interactive_learning_service()
        
        result = await interactive_service.process_interaction(
            session_id=session_id,
            interaction_data=interaction_data
        )
        
        return {
            "success": True,
            "result": result
        }
    
    except Exception as e:
        logging.error(f"Error processing interaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/interactive/session-analytics/{session_id}")
async def get_session_analytics(session_id: str):
    """Get comprehensive analytics for a learning session"""
    try:
        interactive_service = get_interactive_learning_service()
        
        analytics = await interactive_service.get_session_analytics(session_id)
        
        return {
            "success": True,
            "analytics": analytics
        }
    
    except Exception as e:
        logging.error(f"Error getting session analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/interactive/component-library")
async def get_component_library():
    """Get the complete interactive component library"""
    try:
        interactive_service = get_interactive_learning_service()
        
        library = await interactive_service.get_component_library()
        
        return {
            "success": True,
            "library": library
        }
    
    except Exception as e:
        logging.error(f"Error getting component library: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/interactive/create-visualization")
async def create_visualization(
    data: Dict[str, Any] = Body(..., description="Data for visualization"),
    chart_type: str = Query("interactive", description="Type of chart to create")
):
    """Create interactive visualizations for learning data"""
    try:
        interactive_service = get_interactive_learning_service()
        
        visualization = await interactive_service.create_visualization(
            data=data,
            chart_type=chart_type
        )
        
        return {
            "success": True,
            "visualization": visualization
        }
    
    except Exception as e:
        logging.error(f"Error creating visualization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Combined Intelligence Endpoints
@router.get("/intelligence/comprehensive-profile/{user_id}")
async def get_comprehensive_user_profile(user_id: str):
    """Get comprehensive user profile combining memory and graph data"""
    try:
        memmachine = get_memmachine_service()
        neo4j_service = get_neo4j_service()
        
        # Get data from both services
        learning_patterns = await memmachine.analyze_learning_patterns(user_id)
        learning_stats = await neo4j_service.get_user_learning_stats(user_id)
        knowledge_gaps = await neo4j_service.analyze_knowledge_gaps(user_id)
        recommendations = await neo4j_service.recommend_next_concepts(user_id, limit=10)
        
        profile = {
            "user_id": user_id,
            "learning_patterns": learning_patterns,
            "learning_statistics": learning_stats,
            "knowledge_gaps": knowledge_gaps,
            "recommendations": recommendations,
            "generated_at": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "comprehensive_profile": profile
        }
    
    except Exception as e:
        logging.error(f"Error getting comprehensive profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/intelligence/smart-session-planning")
async def create_smart_learning_session(
    user_id: str = Query(..., description="User ID"),
    learning_goals: List[str] = Body(..., description="Learning goals"),
    time_available: int = Query(..., description="Available time in minutes"),
    preferences: Dict[str, Any] = Body(default={}, description="User preferences")
):
    """Create an intelligent learning session based on user data and goals"""
    try:
        memmachine = get_memmachine_service()
        neo4j_service = get_neo4j_service()
        interactive_service = get_interactive_learning_service()
        
        # Analyze user's current state
        learning_patterns = await memmachine.analyze_learning_patterns(user_id)
        user_stats = await neo4j_service.get_user_learning_stats(user_id)
        
        # Find optimal learning paths for goals
        learning_paths = []
        for goal in learning_goals:
            path = await neo4j_service.find_learning_path(user_id, goal)
            learning_paths.append(path)
        
        # Select appropriate interactive components
        component_library = await interactive_service.get_component_library()
        
        # Create intelligent session plan
        session_plan = {
            "user_id": user_id,
            "learning_goals": learning_goals,
            "time_available": time_available,
            "recommended_components": [],
            "learning_paths": [
                {
                    "target": path.target_concept,
                    "path": path.path_nodes,
                    "duration": path.estimated_duration,
                    "confidence": path.confidence_score
                }
                for path in learning_paths
            ],
            "personalization": {
                "difficulty_adjustment": user_stats.get('average_performance', 0.5),
                "learning_velocity": user_stats.get('learning_velocity', 1.0),
                "preferred_style": learning_patterns.get('learning_style', 'mixed')
            }
        }
        
        # Create the actual interactive session
        selected_components = ["adaptive_quiz", "concept_mapper"]  # Smart selection logic here
        session_id = await interactive_service.create_learning_session(
            user_id=user_id,
            components=selected_components,
            preferences=preferences
        )
        
        session_plan["session_id"] = session_id
        
        return {
            "success": True,
            "smart_session_plan": session_plan
        }
    
    except Exception as e:
        logging.error(f"Error creating smart learning session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Enhanced AI Tutor Endpoints
@router.post("/ai-tutor/create-session")
async def create_enhanced_ai_tutor_session(
    user_id: str = Query(..., description="User ID"),
    session_name: Optional[str] = Query(None, description="Session name"),
    subject: Optional[str] = Query(None, description="Subject")
):
    """Create an enhanced AI tutor session with MemMachine and Neo4j integration"""
    try:
        # Import here to avoid circular imports
        from app.services.enhanced_ai_tutor_service import EnhancedAITutorService
        from app.models.base import Subject
        from supabase import create_client
        from app.config import settings
        
        # Create service instance (in production, this should be a singleton)
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        tutor_service = EnhancedAITutorService(supabase)
        
        # Convert subject string to enum if provided
        subject_enum = None
        if subject:
            try:
                subject_enum = Subject(subject.upper())
            except ValueError:
                subject_enum = Subject.MATHEMATICS  # Default fallback
        
        session = await tutor_service.create_session(
            user_id=user_id,
            session_name=session_name,
            subject=subject_enum
        )
        
        return {
            "success": True,
            "session": session,
            "enhanced_features": {
                "memory_integration": True,
                "knowledge_graph": True,
                "interactive_components": True,
                "personalized_welcome": True
            }
        }
    
    except Exception as e:
        logging.error(f"Error creating enhanced AI tutor session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai-tutor/send-message")
async def send_enhanced_message(
    session_id: str = Query(..., description="Session ID"),
    user_id: str = Query(..., description="User ID"),
    message_data: Dict[str, Any] = Body(..., description="Message data")
):
    """Send a message to the enhanced AI tutor with full intelligence integration"""
    try:
        from app.services.enhanced_ai_tutor_service import EnhancedAITutorService
        from app.models.base import Subject
        from supabase import create_client
        from app.config import settings
        
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        tutor_service = EnhancedAITutorService(supabase)
        
        content = message_data.get("content", "")
        subject_str = message_data.get("subject")
        message_type = message_data.get("message_type", "text")
        
        subject_enum = None
        if subject_str:
            try:
                subject_enum = Subject(subject_str.upper())
            except ValueError:
                subject_enum = Subject.MATHEMATICS
        
        response = await tutor_service.send_message(
            session_id=session_id,
            user_id=user_id,
            content=content,
            subject=subject_enum,
            message_type=message_type
        )
        
        return {
            "success": True,
            "response": response
        }
    
    except Exception as e:
        logging.error(f"Error sending enhanced message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ai-tutor/learning-insights/{user_id}")
async def get_comprehensive_learning_insights(user_id: str):
    """Get comprehensive learning insights combining MemMachine and Neo4j data"""
    try:
        from app.services.enhanced_ai_tutor_service import EnhancedAITutorService
        from supabase import create_client
        from app.config import settings
        
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        tutor_service = EnhancedAITutorService(supabase)
        
        insights = await tutor_service.get_learning_insights(user_id)
        
        return {
            "success": True,
            "insights": insights
        }
    
    except Exception as e:
        logging.error(f"Error getting learning insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai-tutor/create-interactive-session")
async def create_interactive_session_from_chat(
    user_id: str = Query(..., description="User ID"),
    session_data: Dict[str, Any] = Body(..., description="Interactive session data")
):
    """Create an interactive learning session from the AI tutor chat"""
    try:
        from app.services.enhanced_ai_tutor_service import EnhancedAITutorService
        from supabase import create_client
        from app.config import settings
        
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        tutor_service = EnhancedAITutorService(supabase)
        
        component_ids = session_data.get("component_ids", [])
        preferences = session_data.get("preferences", {})
        
        result = await tutor_service.create_interactive_learning_session(
            user_id=user_id,
            component_ids=component_ids,
            preferences=preferences
        )
        
        return {
            "success": True,
            "interactive_session": result
        }
    
    except Exception as e:
        logging.error(f"Error creating interactive session from chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Unified Long-term Memory & Context Routes
@router.post("/context/remember", response_model=RememberContextResponse)
async def remember_context(
    user_id: str = Query(..., description="User ID"),
    context_data: ContextData = Body(..., description="Context data to remember")
):
    """
    Universal context memory endpoint - stores any context for long-term retrieval
    Can be used from anywhere in the frontend to remember user interactions, preferences, learning state, etc.
    """
    try:
        memmachine = get_memmachine_service()
        neo4j_service = get_neo4j_service()
        
        # Extract context information
        context_type = context_data.type.value
        content = context_data.content
        subject = context_data.subject
        topic = context_data.topic
        importance = context_data.importance
        tags = context_data.tags.copy()
        
        # Add user-specific tags
        tags.extend([f"user_{user_id}", context_type])
        if subject:
            tags.append(subject)
        if topic:
            tags.append(topic)
        
        # Store in MemMachine for persistent memory
        memory_metadata = {
            "user_id": user_id,
            "context_type": context_type,
            "subject": subject,
            "topic": topic,
            "source": context_data.source or "frontend",
            "session_id": context_data.session_id,
            "page_url": context_data.page_url,
            "component": context_data.component
        }
        
        memory_id = await memmachine.store_memory(
            pool_name="user_contexts",
            content=content,
            metadata=memory_metadata,
            importance_score=importance,
            tags=tags
        )
        
        # If it's learning-related, also update Neo4j knowledge graph
        if context_type in ["learning", "concept_interaction", "performance"]:
            if topic and "performance_data" in content:
                await neo4j_service.update_user_progress(
                    user_id=user_id,
                    concept_name=topic,
                    performance_data=content["performance_data"]
                )
        
        return RememberContextResponse(
            success=True,
            memory_id=memory_id,
            message="Context remembered successfully",
            stored_at=datetime.now().isoformat(),
            tags=tags
        )
    
    except Exception as e:
        logging.error(f"Error remembering context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/context/recall/{user_id}", response_model=RecallContextResponse)
async def recall_context(
    user_id: str,
    context_type: Optional[str] = Query(None, description="Filter by context type"),
    subject: Optional[str] = Query(None, description="Filter by subject"),
    topic: Optional[str] = Query(None, description="Filter by topic"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    limit: int = Query(20, description="Maximum number of contexts to return"),
    days_back: int = Query(30, description="Days to look back"),
    min_importance: float = Query(0.0, description="Minimum importance score")
):
    """
    Universal context recall endpoint - retrieves stored contexts for the user
    Can be used from anywhere in the frontend to recall previous interactions, preferences, learning state, etc.
    """
    try:
        memmachine = get_memmachine_service()
        
        # Build search tags
        search_tags = [f"user_{user_id}"]
        if context_type:
            search_tags.append(context_type)
        if subject:
            search_tags.append(subject)
        if topic:
            search_tags.append(topic)
        if tags:
            search_tags.extend(tags)
        
        # Retrieve contexts from MemMachine
        contexts = await memmachine.retrieve_memory(
            pool_name="user_contexts",
            tags=search_tags,
            limit=limit,
            min_importance=min_importance
        )
        
        # Filter by date if specified
        if days_back:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            contexts = [ctx for ctx in contexts if ctx.timestamp >= cutoff_date]
        
        # Format for frontend consumption
        formatted_contexts = []
        for ctx in contexts:
            formatted_contexts.append(ContextResponse(
                memory_id=ctx.id,
                content=ctx.content,
                metadata=ctx.metadata,
                timestamp=ctx.timestamp.isoformat(),
                importance_score=ctx.importance_score,
                access_count=ctx.access_count,
                last_accessed=ctx.last_accessed.isoformat() if ctx.last_accessed else None,
                tags=ctx.tags,
                context_type=ctx.metadata.get("context_type", "general"),
                subject=ctx.metadata.get("subject"),
                topic=ctx.metadata.get("topic"),
                source=ctx.metadata.get("source", "unknown")
            ))
        
        return RecallContextResponse(
            success=True,
            user_id=user_id,
            total_contexts=len(formatted_contexts),
            contexts=formatted_contexts,
            filters_applied={
                "context_type": context_type,
                "subject": subject,
                "topic": topic,
                "tags": tags,
                "days_back": days_back,
                "min_importance": min_importance
            }
        )
    
    except Exception as e:
        logging.error(f"Error recalling context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/context/smart-suggestions/{user_id}", response_model=SmartSuggestionsResponse)
async def get_smart_context_suggestions(
    user_id: str,
    suggestion_type: str = Query("next_action", description="Type of suggestions needed"),
    current_context: Dict[str, Any] = Body(default={}, description="Current user context")
):
    """
    Get intelligent suggestions based on user's stored contexts and current situation
    Uses both MemMachine and Neo4j to provide personalized recommendations
    """
    try:
        memmachine = get_memmachine_service()
        neo4j_service = get_neo4j_service()
        
        # Get user's recent contexts
        recent_contexts = await memmachine.retrieve_memory(
            pool_name="user_contexts",
            tags=[f"user_{user_id}"],
            limit=50,
            min_importance=0.3
        )
        
        # Get learning statistics from Neo4j
        learning_stats = await neo4j_service.get_user_learning_stats(user_id)
        
        # Get learning recommendations
        learning_recommendations = await neo4j_service.recommend_next_concepts(user_id, limit=5)
        
        # Analyze patterns in recent contexts
        context_patterns = {}
        subject_frequency = {}
        topic_frequency = {}
        time_patterns = {}
        
        for ctx in recent_contexts:
            # Subject patterns
            subject = ctx.metadata.get("subject")
            if subject:
                subject_frequency[subject] = subject_frequency.get(subject, 0) + 1
            
            # Topic patterns
            topic = ctx.metadata.get("topic")
            if topic:
                topic_frequency[topic] = topic_frequency.get(topic, 0) + 1
            
            # Time patterns
            hour = ctx.timestamp.hour
            time_patterns[hour] = time_patterns.get(hour, 0) + 1
        
        # Generate intelligent suggestions based on type
        suggestions = []
        
        if suggestion_type == "next_action":
            # Suggest next learning actions
            if learning_recommendations:
                for rec in learning_recommendations[:3]:
                    suggestions.append({
                        "type": "learning_recommendation",
                        "action": f"Study {rec['concept']}",
                        "reason": f"Based on your progress, this {rec['type']} is ready to learn",
                        "estimated_duration": rec['estimated_duration'],
                        "difficulty": rec['difficulty_level'],
                        "confidence": rec['score']
                    })
            
            # Suggest review based on patterns
            if topic_frequency:
                most_studied = max(topic_frequency.items(), key=lambda x: x[1])
                suggestions.append({
                    "type": "review_suggestion",
                    "action": f"Review {most_studied[0]}",
                    "reason": f"You've been studying this topic frequently ({most_studied[1]} times recently)",
                    "estimated_duration": 15,
                    "confidence": 0.8
                })
        
        elif suggestion_type == "content_recommendation":
            # Recommend content based on learning gaps
            knowledge_gaps = await neo4j_service.analyze_knowledge_gaps(user_id)
            
            for gap in knowledge_gaps.get("weak_areas", [])[:3]:
                suggestions.append({
                    "type": "content_recommendation",
                    "action": f"Practice {gap['concept']}",
                    "reason": f"Mastery level is {gap['mastery_level']:.1%}, needs improvement",
                    "estimated_duration": 30,
                    "priority": "high" if gap['mastery_level'] < 0.5 else "medium"
                })
        
        elif suggestion_type == "study_schedule":
            # Suggest optimal study times based on patterns
            if time_patterns:
                best_hour = max(time_patterns.items(), key=lambda x: x[1])[0]
                suggestions.append({
                    "type": "schedule_suggestion",
                    "action": f"Schedule study session at {best_hour}:00",
                    "reason": f"You're most active at this time ({time_patterns[best_hour]} recent sessions)",
                    "confidence": 0.7
                })
        
        # Add personalized insights
        insights = {
            "most_studied_subject": max(subject_frequency.items(), key=lambda x: x[1])[0] if subject_frequency else None,
            "most_studied_topic": max(topic_frequency.items(), key=lambda x: x[1])[0] if topic_frequency else None,
            "peak_activity_hour": max(time_patterns.items(), key=lambda x: x[1])[0] if time_patterns else None,
            "total_contexts": len(recent_contexts),
            "learning_velocity": learning_stats.get("learning_velocity", 1.0),
            "mastery_rate": learning_stats.get("mastery_rate", 0.0)
        }
        
        return SmartSuggestionsResponse(
            success=True,
            user_id=user_id,
            suggestion_type=suggestion_type,
            suggestions=suggestions,
            insights=insights,
            generated_at=datetime.now().isoformat()
        )
    
    except Exception as e:
        logging.error(f"Error generating smart suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/context/bulk-remember", response_model=BulkRememberResponse)
async def bulk_remember_contexts(
    user_id: str = Query(..., description="User ID"),
    request: BulkContextRequest = Body(..., description="Bulk context request")
):
    """
    Bulk store multiple contexts at once - useful for session end or batch operations
    """
    try:
        memmachine = get_memmachine_service()
        neo4j_service = get_neo4j_service()
        
        stored_contexts = []
        learning_updates = []
        
        for context_data in request.contexts:
            # Extract context information
            context_type = context_data.type.value
            content = context_data.content
            subject = context_data.subject
            topic = context_data.topic
            importance = context_data.importance
            tags = context_data.tags.copy()
            
            # Add user-specific tags
            tags.extend([f"user_{user_id}", context_type])
            if subject:
                tags.append(subject)
            if topic:
                tags.append(topic)
            
            # Store in MemMachine
            memory_metadata = {
                "user_id": user_id,
                "context_type": context_type,
                "subject": subject,
                "topic": topic,
                "source": context_data.source or "frontend_bulk",
                "session_id": context_data.session_id,
                "batch_id": context_data.batch_id
            }
            
            memory_id = await memmachine.store_memory(
                pool_name="user_contexts",
                content=content,
                metadata=memory_metadata,
                importance_score=importance,
                tags=tags
            )
            
            stored_contexts.append({
                "memory_id": memory_id,
                "context_type": context_type,
                "subject": subject,
                "topic": topic
            })
            
            # Collect learning updates for Neo4j
            if context_type in ["learning", "concept_interaction", "performance"] and topic and "performance_data" in content:
                learning_updates.append({
                    "concept_name": topic,
                    "performance_data": content["performance_data"]
                })
        
        # Batch update Neo4j
        for update in learning_updates:
            await neo4j_service.update_user_progress(
                user_id=user_id,
                concept_name=update["concept_name"],
                performance_data=update["performance_data"]
            )
        
        return BulkRememberResponse(
            success=True,
            user_id=user_id,
            total_stored=len(stored_contexts),
            stored_contexts=stored_contexts,
            learning_updates=len(learning_updates),
            stored_at=datetime.now().isoformat()
        )
    
    except Exception as e:
        logging.error(f"Error bulk remembering contexts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/context/user-timeline/{user_id}")
async def get_user_timeline(
    user_id: str,
    days_back: int = Query(7, description="Days to look back"),
    include_learning: bool = Query(True, description="Include learning progress"),
    include_interactions: bool = Query(True, description="Include user interactions")
):
    """
    Get a comprehensive timeline of user's activities and progress
    Combines data from both MemMachine and Neo4j for a complete picture
    """
    try:
        memmachine = get_memmachine_service()
        neo4j_service = get_neo4j_service()
        
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Get contexts from MemMachine
        contexts = await memmachine.retrieve_memory(
            pool_name="user_contexts",
            tags=[f"user_{user_id}"],
            limit=200,
            min_importance=0.1
        )
        
        # Filter by date
        recent_contexts = [ctx for ctx in contexts if ctx.timestamp >= cutoff_date]
        
        # Get learning history if requested
        learning_history = []
        if include_learning:
            learning_history = await memmachine.get_user_learning_history(
                user_id=user_id,
                days_back=days_back,
                limit=100
            )
        
        # Build timeline events
        timeline_events = []
        
        # Add context events
        for ctx in recent_contexts:
            if not include_interactions and ctx.metadata.get("context_type") == "interaction":
                continue
            
            timeline_events.append({
                "timestamp": ctx.timestamp.isoformat(),
                "type": "context",
                "event_type": ctx.metadata.get("context_type", "general"),
                "title": f"{ctx.metadata.get('context_type', 'Activity').title()}",
                "description": _generate_context_description(ctx),
                "subject": ctx.metadata.get("subject"),
                "topic": ctx.metadata.get("topic"),
                "importance": ctx.importance_score,
                "source": ctx.metadata.get("source", "unknown"),
                "data": {
                    "memory_id": ctx.id,
                    "tags": ctx.tags,
                    "access_count": ctx.access_count
                }
            })
        
        # Add learning session events
        for session in learning_history:
            timeline_events.append({
                "timestamp": session.timestamp.isoformat(),
                "type": "learning_session",
                "event_type": "learning",
                "title": f"Learning Session: {session.content['context']['topic']}",
                "description": f"Studied {session.content['context']['subject']} - {session.content['context']['topic']}",
                "subject": session.content['context']['subject'],
                "topic": session.content['context']['topic'],
                "importance": session.importance_score,
                "data": {
                    "session_id": session.content['context']['session_id'],
                    "duration": session.content['session_data'].get('duration', 0),
                    "completion_rate": session.content['session_data'].get('completion_rate', 0),
                    "performance": session.content['session_data'].get('performance_metrics', {})
                }
            })
        
        # Sort timeline by timestamp (most recent first)
        timeline_events.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Generate summary statistics
        summary = {
            "total_events": len(timeline_events),
            "learning_sessions": len([e for e in timeline_events if e['type'] == 'learning_session']),
            "interactions": len([e for e in timeline_events if e['event_type'] == 'interaction']),
            "subjects_studied": len(set(e['subject'] for e in timeline_events if e['subject'])),
            "most_active_day": _find_most_active_day(timeline_events),
            "average_daily_activity": len(timeline_events) / max(days_back, 1)
        }
        
        return {
            "success": True,
            "user_id": user_id,
            "timeline_period": {
                "days_back": days_back,
                "start_date": cutoff_date.isoformat(),
                "end_date": datetime.now().isoformat()
            },
            "summary": summary,
            "timeline": timeline_events
        }
    
    except Exception as e:
        logging.error(f"Error generating user timeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _generate_context_description(ctx) -> str:
    """Generate a human-readable description for a context entry"""
    context_type = ctx.metadata.get("context_type", "general")
    subject = ctx.metadata.get("subject")
    topic = ctx.metadata.get("topic")
    
    if context_type == "learning":
        return f"Learned about {topic}" if topic else f"Studied {subject}" if subject else "Learning activity"
    elif context_type == "interaction":
        return f"Interacted with {ctx.metadata.get('component', 'system')}"
    elif context_type == "performance":
        return f"Performance recorded for {topic}" if topic else "Performance data"
    elif context_type == "preference":
        return "Updated preferences"
    else:
        return f"{context_type.title()} activity"

def _find_most_active_day(events) -> Optional[str]:
    """Find the day with most activity"""
    if not events:
        return None
    
    day_counts = {}
    for event in events:
        day = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00')).date().isoformat()
        day_counts[day] = day_counts.get(day, 0) + 1
    
    return max(day_counts.items(), key=lambda x: x[1])[0] if day_counts else None

# Notification/Message Endpoints
@router.get("/notifications/{user_id}")
async def get_user_notifications(
    user_id: str,
    limit: int = Query(10, description="Maximum number of notifications"),
    unread_only: bool = Query(False, description="Only return unread notifications")
):
    """
    Get user notifications and messages (like quiz creation confirmations)
    """
    try:
        memmachine = get_memmachine_service()
        
        # Get notification contexts
        search_tags = [f"user_{user_id}", "notification"]
        if unread_only:
            search_tags.append("unread")
        
        notifications = await memmachine.retrieve_memory(
            pool_name="user_contexts",
            tags=search_tags,
            limit=limit,
            min_importance=0.3
        )
        
        # Format notifications
        formatted_notifications = []
        for notif in notifications:
            # Skip read notifications if unread_only is True
            if unread_only and "read" in notif.tags:
                continue
            
            formatted_notifications.append({
                "id": notif.id,
                "type": notif.content.get("type", "info"),
                "title": notif.content.get("title", "Notification"),
                "message": notif.content.get("message", ""),
                "action": notif.content.get("action"),
                "data": notif.content.get("data", {}),
                "created_at": notif.timestamp.isoformat(),
                "is_read": "read" in notif.tags,
                "importance": notif.importance_score,
                "auto_dismiss": notif.content.get("auto_dismiss", False),
                "dismiss_after": notif.content.get("dismiss_after", 5000)  # milliseconds
            })
        
        return {
            "success": True,
            "user_id": user_id,
            "notifications": formatted_notifications,
            "total_count": len(formatted_notifications),
            "unread_count": len([n for n in formatted_notifications if not n["is_read"]])
        }
    
    except Exception as e:
        logging.error(f"Error getting notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/notifications/{user_id}")
async def create_notification(
    user_id: str,
    notification_data: Dict[str, Any] = Body(..., description="Notification data")
):
    """
    Create a new notification for the user
    """
    try:
        memmachine = get_memmachine_service()
        
        # Extract notification data
        notif_type = notification_data.get("type", "info")  # info, success, warning, error
        title = notification_data.get("title", "Notification")
        message = notification_data.get("message", "")
        action = notification_data.get("action")  # Optional action button
        data = notification_data.get("data", {})
        auto_dismiss = notification_data.get("auto_dismiss", True)
        dismiss_after = notification_data.get("dismiss_after", 5000)
        importance = notification_data.get("importance", 0.5)
        
        # Create notification content
        content = {
            "type": notif_type,
            "title": title,
            "message": message,
            "action": action,
            "data": data,
            "auto_dismiss": auto_dismiss,
            "dismiss_after": dismiss_after,
            "created_by": "system"
        }
        
        # Set up tags
        tags = [f"user_{user_id}", "notification", "unread", notif_type]
        
        # Store notification
        memory_id = await memmachine.store_memory(
            pool_name="user_contexts",
            content=content,
            metadata={
                "user_id": user_id,
                "context_type": "notification",
                "source": "notification_system"
            },
            importance_score=importance,
            tags=tags
        )
        
        return {
            "success": True,
            "notification_id": memory_id,
            "message": "Notification created successfully",
            "created_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        logging.error(f"Error creating notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/notifications/{notification_id}/dismiss")
async def dismiss_notification(
    notification_id: str,
    user_id: str = Query(..., description="User ID")
):
    """
    Dismiss/close a notification (mark as read)
    """
    try:
        memmachine = get_memmachine_service()
        
        # Get the notification
        notifications = await memmachine.retrieve_memory(
            pool_name="user_contexts",
            memory_id=notification_id
        )
        
        if not notifications:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        notification = notifications[0]
        
        # Verify ownership
        if notification.metadata.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        # Update tags to mark as read
        updated_tags = [tag for tag in notification.tags if tag != "unread"]
        updated_tags.append("read")
        
        # Update content to mark as dismissed
        updated_content = notification.content.copy()
        updated_content["dismissed_at"] = datetime.now().isoformat()
        updated_content["dismissed"] = True
        
        # Store updated notification
        await memmachine.store_memory(
            pool_name="user_contexts",
            content=updated_content,
            metadata=notification.metadata,
            importance_score=0.1,  # Lower importance for dismissed notifications
            tags=updated_tags
        )
        
        return {
            "success": True,
            "message": "Notification dismissed successfully",
            "dismissed_at": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error dismissing notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/notifications/{user_id}/mark-all-read")
async def mark_all_notifications_read(user_id: str):
    """
    Mark all notifications as read for a user
    """
    try:
        memmachine = get_memmachine_service()
        
        # Get all unread notifications
        unread_notifications = await memmachine.retrieve_memory(
            pool_name="user_contexts",
            tags=[f"user_{user_id}", "notification", "unread"],
            limit=100
        )
        
        marked_count = 0
        for notification in unread_notifications:
            # Update tags to mark as read
            updated_tags = [tag for tag in notification.tags if tag != "unread"]
            updated_tags.append("read")
            
            # Update content
            updated_content = notification.content.copy()
            updated_content["marked_read_at"] = datetime.now().isoformat()
            
            # Store updated notification
            await memmachine.store_memory(
                pool_name="user_contexts",
                content=updated_content,
                metadata=notification.metadata,
                importance_score=0.1,
                tags=updated_tags
            )
            marked_count += 1
        
        return {
            "success": True,
            "message": f"Marked {marked_count} notifications as read",
            "marked_count": marked_count,
            "marked_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        logging.error(f"Error marking notifications as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Notes Endpoints
@router.get("/notes")
async def get_user_notes(
    user_id: str = Query(..., description="User ID"),
    limit: int = Query(50, description="Maximum number of notes to return"),
    subject: Optional[str] = Query(None, description="Filter by subject"),
    topic: Optional[str] = Query(None, description="Filter by topic")
):
    """
    Get user's notes and annotations
    This endpoint retrieves stored contexts that represent user notes, annotations, and saved content
    """
    try:
        memmachine = get_memmachine_service()
        
        # Build search tags for notes
        search_tags = [f"user_{user_id}"]
        
        # Add note-related context types
        note_contexts = await memmachine.retrieve_memory(
            pool_name="user_contexts",
            tags=search_tags,
            limit=limit * 2,  # Get more to filter
            min_importance=0.1
        )
        
        # Filter for note-like contexts
        notes = []
        for ctx in note_contexts:
            context_type = ctx.metadata.get("context_type", "")
            
            # Include contexts that are note-like
            if context_type in ["note", "annotation", "bookmark", "learning", "preference"]:
                # Apply subject/topic filters if specified
                if subject and ctx.metadata.get("subject") != subject:
                    continue
                if topic and ctx.metadata.get("topic") != topic:
                    continue
                
                note_data = {
                    "id": ctx.id,
                    "content": ctx.content,
                    "title": ctx.content.get("title", f"{context_type.title()} - {ctx.metadata.get('topic', 'General')}"),
                    "type": context_type,
                    "subject": ctx.metadata.get("subject"),
                    "topic": ctx.metadata.get("topic"),
                    "created_at": ctx.timestamp.isoformat(),
                    "updated_at": ctx.last_accessed.isoformat() if ctx.last_accessed else ctx.timestamp.isoformat(),
                    "importance": ctx.importance_score,
                    "tags": ctx.tags,
                    "source": ctx.metadata.get("source", "user")
                }
                
                notes.append(note_data)
        
        # Sort by importance and recency
        notes.sort(key=lambda x: (x['importance'], x['created_at']), reverse=True)
        
        # Limit results
        notes = notes[:limit]
        
        return {
            "success": True,
            "user_id": user_id,
            "total_notes": len(notes),
            "notes": notes,
            "filters": {
                "subject": subject,
                "topic": topic,
                "limit": limit
            }
        }
    
    except Exception as e:
        logging.error(f"Error retrieving user notes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/notes")
async def create_user_note(
    user_id: str = Query(..., description="User ID"),
    note_data: Dict[str, Any] = Body(..., description="Note data")
):
    """
    Create a new user note
    """
    try:
        memmachine = get_memmachine_service()
        
        # Extract note information
        title = note_data.get("title", "Untitled Note")
        content = note_data.get("content", "")
        subject = note_data.get("subject")
        topic = note_data.get("topic")
        note_type = note_data.get("type", "note")
        tags = note_data.get("tags", [])
        
        # Add note-specific tags
        tags.extend([f"user_{user_id}", "note", note_type])
        if subject:
            tags.append(subject)
        if topic:
            tags.append(topic)
        
        # Store note as context
        note_content = {
            "title": title,
            "content": content,
            "note_type": note_type,
            "created_by": "user"
        }
        
        metadata = {
            "user_id": user_id,
            "context_type": "note",
            "subject": subject,
            "topic": topic,
            "source": "notes_interface"
        }
        
        memory_id = await memmachine.store_memory(
            pool_name="user_contexts",
            content=note_content,
            metadata=metadata,
            importance_score=0.7,  # Notes are generally important
            tags=tags
        )
        
        return {
            "success": True,
            "note_id": memory_id,
            "message": "Note created successfully",
            "created_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        logging.error(f"Error creating user note: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/notes/{note_id}")
async def update_user_note(
    note_id: str,
    user_id: str = Query(..., description="User ID"),
    note_data: Dict[str, Any] = Body(..., description="Updated note data")
):
    """
    Update an existing user note
    """
    try:
        memmachine = get_memmachine_service()
        
        # Retrieve existing note
        existing_notes = await memmachine.retrieve_memory(
            pool_name="user_contexts",
            memory_id=note_id
        )
        
        if not existing_notes:
            raise HTTPException(status_code=404, detail="Note not found")
        
        existing_note = existing_notes[0]
        
        # Verify ownership
        if existing_note.metadata.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this note")
        
        # Update note content
        updated_content = existing_note.content.copy()
        updated_content.update({
            "title": note_data.get("title", updated_content.get("title")),
            "content": note_data.get("content", updated_content.get("content")),
            "updated_at": datetime.now().isoformat()
        })
        
        # Update metadata
        updated_metadata = existing_note.metadata.copy()
        updated_metadata.update({
            "subject": note_data.get("subject", updated_metadata.get("subject")),
            "topic": note_data.get("topic", updated_metadata.get("topic"))
        })
        
        # Store updated note (creates new version)
        memory_id = await memmachine.store_memory(
            pool_name="user_contexts",
            content=updated_content,
            metadata=updated_metadata,
            importance_score=existing_note.importance_score,
            tags=existing_note.tags
        )
        
        return {
            "success": True,
            "note_id": memory_id,
            "message": "Note updated successfully",
            "updated_at": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error updating user note: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/notes/{note_id}")
async def delete_user_note(
    note_id: str,
    user_id: str = Query(..., description="User ID")
):
    """
    Delete a user note (mark as deleted)
    """
    try:
        memmachine = get_memmachine_service()
        
        # Retrieve existing note to verify ownership
        existing_notes = await memmachine.retrieve_memory(
            pool_name="user_contexts",
            memory_id=note_id
        )
        
        if not existing_notes:
            raise HTTPException(status_code=404, detail="Note not found")
        
        existing_note = existing_notes[0]
        
        # Verify ownership
        if existing_note.metadata.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this note")
        
        # Mark as deleted by updating importance to 0 and adding deleted tag
        deleted_content = existing_note.content.copy()
        deleted_content["deleted"] = True
        deleted_content["deleted_at"] = datetime.now().isoformat()
        
        deleted_tags = existing_note.tags.copy()
        deleted_tags.append("deleted")
        
        # Store deleted version with very low importance
        await memmachine.store_memory(
            pool_name="user_contexts",
            content=deleted_content,
            metadata=existing_note.metadata,
            importance_score=0.01,  # Very low importance
            tags=deleted_tags
        )
        
        return {
            "success": True,
            "message": "Note deleted successfully",
            "deleted_at": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting user note: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Interactive Dashboard Endpoints
@router.get("/dashboard/{layout_id}")
async def get_dashboard_html(
    layout_id: str,
    user_id: Optional[str] = Query(None, description="User ID for personalization")
):
    """Get complete HTML dashboard for the specified layout"""
    try:
        dashboard = get_interactive_dashboard()
        
        user_data = {"user_id": user_id} if user_id else {}
        
        html_content = await dashboard.generate_dashboard_html(layout_id, user_data)
        
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html_content)
    
    except Exception as e:
        logging.error(f"Error generating dashboard HTML: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/dashboard/widget-data/{widget_id}")
async def get_widget_data(
    widget_id: str,
    widget_config: Dict[str, Any] = Body(..., description="Widget configuration"),
    user_data: Dict[str, Any] = Body(default={}, description="User data")
):
    """Get data for a specific dashboard widget"""
    try:
        dashboard = get_interactive_dashboard()
        
        widget_data = await dashboard.get_widget_data(widget_id, widget_config, user_data)
        
        return {
            "success": True,
            "widget_data": widget_data
        }
    
    except Exception as e:
        logging.error(f"Error getting widget data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/dashboard/control-action")
async def handle_control_action(
    widget_id: str = Body(..., description="Widget ID"),
    control_type: str = Body(..., description="Control type"),
    value: Any = Body(None, description="Control value")
):
    """Handle dashboard control actions"""
    try:
        # Process control action based on type
        result = {"action_processed": True}
        
        if control_type == "start_session":
            # Start a learning session
            result["session_started"] = True
        elif control_type == "pause_session":
            # Pause current session
            result["session_paused"] = True
        elif control_type == "parameter_change":
            # Handle parameter changes in interactive components
            result["parameter_updated"] = value
        
        return {
            "success": True,
            "result": result
        }
    
    except Exception as e:
        logging.error(f"Error handling control action: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard/layouts")
async def get_available_layouts():
    """Get list of available dashboard layouts"""
    try:
        dashboard = get_interactive_dashboard()
        
        layouts = []
        for layout_id, layout in dashboard.layouts.items():
            layouts.append({
                "id": layout.id,
                "name": layout.name,
                "description": layout.description,
                "theme": layout.theme,
                "widget_count": len(layout.widgets),
                "grid_size": layout.grid_size
            })
        
        return {
            "success": True,
            "layouts": layouts
        }
    
    except Exception as e:
        logging.error(f"Error getting dashboard layouts: {e}")
        raise HTTPException(status_code=500, detail=str(e))