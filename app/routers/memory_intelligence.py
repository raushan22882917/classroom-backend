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