"""
Interactive Learning Service
Provides highly interactive and engaging learning experiences
"""

import json
import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict
import numpy as np
import random
from enum import Enum

# Interactive components
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logging.warning("Plotly not available for interactive visualizations")

class InteractionType(Enum):
    """Types of interactive learning components"""
    QUIZ = "quiz"
    SIMULATION = "simulation"
    VISUALIZATION = "visualization"
    GAME = "game"
    COLLABORATIVE = "collaborative"
    ADAPTIVE_PRACTICE = "adaptive_practice"
    VIRTUAL_LAB = "virtual_lab"
    STORYTELLING = "storytelling"

class DifficultyLevel(Enum):
    """Difficulty levels for adaptive learning"""
    BEGINNER = 1
    ELEMENTARY = 2
    INTERMEDIATE = 3
    ADVANCED = 4
    EXPERT = 5

@dataclass
class InteractiveComponent:
    """Represents an interactive learning component"""
    id: str
    title: str
    type: InteractionType
    content: Dict[str, Any]
    difficulty: DifficultyLevel
    estimated_duration: int  # minutes
    learning_objectives: List[str]
    prerequisites: List[str]
    metadata: Dict[str, Any]

@dataclass
class LearningSession:
    """Represents an interactive learning session"""
    session_id: str
    user_id: str
    components: List[InteractiveComponent]
    current_component: int
    start_time: datetime
    interactions: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]
    adaptive_adjustments: List[Dict[str, Any]]

@dataclass
class UserEngagement:
    """Tracks user engagement metrics"""
    user_id: str
    session_id: str
    attention_score: float
    interaction_frequency: float
    completion_rate: float
    time_on_task: int
    help_requests: int
    exploration_depth: float

class InteractiveLearningService:
    """
    Service for creating and managing interactive learning experiences
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.active_sessions = {}
        self.component_library = {}
        self.user_preferences = {}
        self.engagement_tracker = {}
        
        # Initialize component library
        self._initialize_component_library()
        
        # Real-time interaction settings
        self.real_time_feedback = self.config.get('real_time_feedback', True)
        self.adaptive_difficulty = self.config.get('adaptive_difficulty', True)
        self.gamification_enabled = self.config.get('gamification', True)
        
        logging.info("Interactive Learning Service initialized")
    
    def _initialize_component_library(self):
        """Initialize the library of interactive components"""
        # Mathematics interactive components
        self.component_library.update({
            'algebra_visualizer': self._create_algebra_visualizer(),
            'calculus_simulator': self._create_calculus_simulator(),
            'geometry_explorer': self._create_geometry_explorer(),
            'statistics_dashboard': self._create_statistics_dashboard(),
        })
        
        # Physics interactive components
        self.component_library.update({
            'physics_lab': self._create_physics_lab(),
            'wave_simulator': self._create_wave_simulator(),
            'circuit_builder': self._create_circuit_builder(),
            'mechanics_playground': self._create_mechanics_playground(),
        })
        
        # Chemistry interactive components
        self.component_library.update({
            'molecule_builder': self._create_molecule_builder(),
            'reaction_simulator': self._create_reaction_simulator(),
            'periodic_table_explorer': self._create_periodic_table_explorer(),
        })
        
        # General learning components
        self.component_library.update({
            'adaptive_quiz': self._create_adaptive_quiz(),
            'concept_mapper': self._create_concept_mapper(),
            'collaborative_whiteboard': self._create_collaborative_whiteboard(),
            'storytelling_engine': self._create_storytelling_engine(),
        })
    
    def _create_calculus_simulator(self) -> InteractiveComponent:
        """Create calculus simulation component"""
        return InteractiveComponent(
            id="calculus_simulator",
            title="Interactive Calculus Simulator",
            type=InteractionType.SIMULATION,
            content={
                "simulation_type": "mathematical",
                "features": [
                    "derivative_visualization",
                    "integral_approximation",
                    "limit_exploration",
                    "optimization_problems"
                ],
                "tools": [
                    "function_plotter",
                    "tangent_line_drawer",
                    "area_calculator",
                    "rate_of_change_analyzer"
                ],
                "real_time_calculation": True,
                "step_by_step_solutions": True
            },
            difficulty=DifficultyLevel.ADVANCED,
            estimated_duration=35,
            learning_objectives=[
                "Visualize calculus concepts",
                "Understand derivatives and integrals",
                "Explore mathematical relationships",
                "Solve optimization problems"
            ],
            prerequisites=["algebra", "functions"],
            metadata={
                "subject": "mathematics",
                "topic": "calculus",
                "interactive_level": "very_high"
            }
        )
    
    def _create_geometry_explorer(self) -> InteractiveComponent:
        """Create geometry exploration component"""
        return InteractiveComponent(
            id="geometry_explorer",
            title="Interactive Geometry Explorer",
            type=InteractionType.VISUALIZATION,
            content={
                "component_type": "geometry_canvas",
                "features": [
                    "shape_construction",
                    "measurement_tools",
                    "transformation_controls",
                    "proof_assistance"
                ]
            },
            difficulty=DifficultyLevel.INTERMEDIATE,
            estimated_duration=25,
            learning_objectives=["Understand geometric relationships"],
            prerequisites=["basic_math"],
            metadata={"subject": "mathematics", "topic": "geometry"}
        )
    
    def _create_statistics_dashboard(self) -> InteractiveComponent:
        """Create statistics dashboard component"""
        return InteractiveComponent(
            id="statistics_dashboard",
            title="Interactive Statistics Dashboard",
            type=InteractionType.VISUALIZATION,
            content={
                "component_type": "stats_dashboard",
                "features": [
                    "data_visualization",
                    "statistical_analysis",
                    "hypothesis_testing",
                    "distribution_exploration"
                ]
            },
            difficulty=DifficultyLevel.ADVANCED,
            estimated_duration=40,
            learning_objectives=["Understand statistical concepts"],
            prerequisites=["algebra", "probability"],
            metadata={"subject": "mathematics", "topic": "statistics"}
        )
    
    def _create_physics_lab(self) -> InteractiveComponent:
        """Create physics laboratory component"""
        return InteractiveComponent(
            id="physics_lab",
            title="Virtual Physics Laboratory",
            type=InteractionType.VIRTUAL_LAB,
            content={
                "lab_type": "mechanics",
                "experiments": [
                    {
                        "name": "Projectile Motion",
                        "description": "Explore projectile motion with adjustable parameters"
                    }
                ]
            },
            difficulty=DifficultyLevel.ADVANCED,
            estimated_duration=45,
            learning_objectives=["Conduct virtual physics experiments"],
            prerequisites=["basic_physics", "mathematics"],
            metadata={"subject": "physics", "topic": "mechanics"}
        )
    
    def _create_wave_simulator(self) -> InteractiveComponent:
        """Create wave simulation component"""
        return InteractiveComponent(
            id="wave_simulator",
            title="Wave Motion Simulator",
            type=InteractionType.SIMULATION,
            content={
                "simulation_type": "wave_physics",
                "features": ["wave_generation", "interference_patterns"]
            },
            difficulty=DifficultyLevel.ADVANCED,
            estimated_duration=30,
            learning_objectives=["Understand wave properties"],
            prerequisites=["physics", "trigonometry"],
            metadata={"subject": "physics", "topic": "waves"}
        )
    
    def _create_circuit_builder(self) -> InteractiveComponent:
        """Create circuit building component"""
        return InteractiveComponent(
            id="circuit_builder",
            title="Electronic Circuit Builder",
            type=InteractionType.SIMULATION,
            content={
                "simulation_type": "electronics",
                "features": ["component_library", "circuit_simulation"]
            },
            difficulty=DifficultyLevel.INTERMEDIATE,
            estimated_duration=35,
            learning_objectives=["Build and analyze circuits"],
            prerequisites=["basic_physics"],
            metadata={"subject": "physics", "topic": "electronics"}
        )
    
    def _create_mechanics_playground(self) -> InteractiveComponent:
        """Create mechanics playground component"""
        return InteractiveComponent(
            id="mechanics_playground",
            title="Mechanics Playground",
            type=InteractionType.SIMULATION,
            content={
                "simulation_type": "mechanics",
                "features": ["force_vectors", "motion_analysis"]
            },
            difficulty=DifficultyLevel.INTERMEDIATE,
            estimated_duration=30,
            learning_objectives=["Explore mechanical systems"],
            prerequisites=["physics"],
            metadata={"subject": "physics", "topic": "mechanics"}
        )
    
    def _create_molecule_builder(self) -> InteractiveComponent:
        """Create molecule building component"""
        return InteractiveComponent(
            id="molecule_builder",
            title="3D Molecule Builder",
            type=InteractionType.SIMULATION,
            content={
                "simulation_type": "chemistry",
                "features": ["atom_placement", "bond_formation", "3d_visualization"]
            },
            difficulty=DifficultyLevel.INTERMEDIATE,
            estimated_duration=25,
            learning_objectives=["Build molecular structures"],
            prerequisites=["basic_chemistry"],
            metadata={"subject": "chemistry", "topic": "molecular_structure"}
        )
    
    def _create_reaction_simulator(self) -> InteractiveComponent:
        """Create chemical reaction simulator"""
        return InteractiveComponent(
            id="reaction_simulator",
            title="Chemical Reaction Simulator",
            type=InteractionType.SIMULATION,
            content={
                "simulation_type": "chemical_reactions",
                "features": ["reactant_mixing", "product_formation", "energy_tracking"]
            },
            difficulty=DifficultyLevel.ADVANCED,
            estimated_duration=40,
            learning_objectives=["Understand chemical reactions"],
            prerequisites=["chemistry", "stoichiometry"],
            metadata={"subject": "chemistry", "topic": "reactions"}
        )
    
    def _create_periodic_table_explorer(self) -> InteractiveComponent:
        """Create periodic table explorer"""
        return InteractiveComponent(
            id="periodic_table_explorer",
            title="Interactive Periodic Table",
            type=InteractionType.VISUALIZATION,
            content={
                "component_type": "periodic_table",
                "features": ["element_details", "trend_visualization", "property_comparison"]
            },
            difficulty=DifficultyLevel.BEGINNER,
            estimated_duration=20,
            learning_objectives=["Explore element properties"],
            prerequisites=["basic_chemistry"],
            metadata={"subject": "chemistry", "topic": "periodic_table"}
        )
    
    def _create_concept_mapper(self) -> InteractiveComponent:
        """Create concept mapping component"""
        return InteractiveComponent(
            id="concept_mapper",
            title="Interactive Concept Mapper",
            type=InteractionType.VISUALIZATION,
            content={
                "component_type": "concept_map",
                "features": ["node_creation", "relationship_linking", "collaborative_editing"]
            },
            difficulty=DifficultyLevel.BEGINNER,
            estimated_duration=15,
            learning_objectives=["Organize knowledge visually"],
            prerequisites=[],
            metadata={"subject": "any", "topic": "organization"}
        )
    
    def _create_algebra_visualizer(self) -> InteractiveComponent:
        """Create interactive algebra visualization component"""
        return InteractiveComponent(
            id="algebra_visualizer",
            title="Interactive Algebra Visualizer",
            type=InteractionType.VISUALIZATION,
            content={
                "component_type": "graph_plotter",
                "features": [
                    "equation_input",
                    "real_time_graphing",
                    "parameter_sliders",
                    "transformation_tools",
                    "step_by_step_solutions"
                ],
                "supported_functions": [
                    "linear", "quadratic", "polynomial", 
                    "exponential", "logarithmic", "trigonometric"
                ],
                "interactive_elements": {
                    "equation_editor": {
                        "type": "math_input",
                        "placeholder": "Enter equation (e.g., y = 2x + 3)",
                        "validation": True,
                        "suggestions": True
                    },
                    "parameter_controls": {
                        "sliders": ["a", "b", "c", "h", "k"],
                        "range": [-10, 10],
                        "step": 0.1
                    },
                    "graph_canvas": {
                        "zoom": True,
                        "pan": True,
                        "grid": True,
                        "axes_labels": True,
                        "point_plotting": True
                    }
                },
                "learning_modes": [
                    "exploration",
                    "guided_practice",
                    "problem_solving",
                    "assessment"
                ]
            },
            difficulty=DifficultyLevel.INTERMEDIATE,
            estimated_duration=30,
            learning_objectives=[
                "Understand relationship between equations and graphs",
                "Explore effects of parameter changes",
                "Develop algebraic intuition",
                "Practice equation manipulation"
            ],
            prerequisites=["basic_algebra", "coordinate_system"],
            metadata={
                "subject": "mathematics",
                "topic": "algebra",
                "interactive_level": "high",
                "technology_required": ["javascript", "canvas"]
            }
        )
    
    def _create_physics_lab(self) -> InteractiveComponent:
        """Create virtual physics laboratory"""
        return InteractiveComponent(
            id="physics_lab",
            title="Virtual Physics Laboratory",
            type=InteractionType.VIRTUAL_LAB,
            content={
                "lab_type": "mechanics",
                "experiments": [
                    {
                        "name": "Projectile Motion",
                        "description": "Explore projectile motion with adjustable parameters",
                        "variables": ["initial_velocity", "angle", "height", "gravity"],
                        "measurements": ["range", "max_height", "time_of_flight"],
                        "visualization": "trajectory_plot"
                    },
                    {
                        "name": "Pendulum Oscillation",
                        "description": "Study simple harmonic motion",
                        "variables": ["length", "mass", "initial_angle", "damping"],
                        "measurements": ["period", "frequency", "amplitude"],
                        "visualization": "oscillation_graph"
                    },
                    {
                        "name": "Collision Analysis",
                        "description": "Investigate elastic and inelastic collisions",
                        "variables": ["mass1", "mass2", "velocity1", "velocity2"],
                        "measurements": ["final_velocities", "kinetic_energy", "momentum"],
                        "visualization": "collision_animation"
                    }
                ],
                "tools": [
                    "stopwatch",
                    "ruler",
                    "protractor",
                    "force_meter",
                    "data_logger"
                ],
                "safety_features": [
                    "parameter_limits",
                    "warning_system",
                    "reset_button",
                    "help_system"
                ]
            },
            difficulty=DifficultyLevel.ADVANCED,
            estimated_duration=45,
            learning_objectives=[
                "Conduct virtual physics experiments",
                "Understand cause-and-effect relationships",
                "Practice data collection and analysis",
                "Develop scientific inquiry skills"
            ],
            prerequisites=["basic_physics", "mathematics"],
            metadata={
                "subject": "physics",
                "topic": "mechanics",
                "interactive_level": "very_high",
                "simulation_engine": "physics_2d"
            }
        )
    
    def _create_adaptive_quiz(self) -> InteractiveComponent:
        """Create adaptive quiz system"""
        return InteractiveComponent(
            id="adaptive_quiz",
            title="Adaptive Learning Quiz",
            type=InteractionType.ADAPTIVE_PRACTICE,
            content={
                "quiz_engine": "adaptive",
                "question_types": [
                    "multiple_choice",
                    "fill_in_blank",
                    "drag_and_drop",
                    "matching",
                    "ordering",
                    "drawing",
                    "calculation"
                ],
                "adaptation_algorithm": {
                    "difficulty_adjustment": "irt_based",  # Item Response Theory
                    "content_selection": "knowledge_tracing",
                    "feedback_timing": "immediate",
                    "hint_system": "progressive"
                },
                "personalization": {
                    "learning_style": ["visual", "auditory", "kinesthetic"],
                    "pace_preference": ["slow", "medium", "fast"],
                    "challenge_level": ["conservative", "moderate", "aggressive"]
                },
                "gamification": {
                    "points_system": True,
                    "badges": True,
                    "leaderboards": True,
                    "achievements": True,
                    "progress_bars": True
                }
            },
            difficulty=DifficultyLevel.INTERMEDIATE,
            estimated_duration=20,
            learning_objectives=[
                "Assess current knowledge level",
                "Identify learning gaps",
                "Practice problem-solving",
                "Build confidence through success"
            ],
            prerequisites=["topic_introduction"],
            metadata={
                "subject": "any",
                "topic": "assessment",
                "interactive_level": "high",
                "ai_powered": True
            }
        )
    
    def _create_collaborative_whiteboard(self) -> InteractiveComponent:
        """Create collaborative learning whiteboard"""
        return InteractiveComponent(
            id="collaborative_whiteboard",
            title="Collaborative Learning Whiteboard",
            type=InteractionType.COLLABORATIVE,
            content={
                "collaboration_features": {
                    "real_time_sync": True,
                    "multi_user": True,
                    "voice_chat": True,
                    "video_chat": True,
                    "screen_sharing": True
                },
                "drawing_tools": [
                    "pen", "highlighter", "eraser", "shapes",
                    "text", "sticky_notes", "arrows", "math_symbols"
                ],
                "templates": [
                    "blank_canvas",
                    "graph_paper",
                    "coordinate_plane",
                    "concept_map",
                    "flowchart",
                    "timeline"
                ],
                "ai_assistance": {
                    "handwriting_recognition": True,
                    "equation_solving": True,
                    "concept_suggestions": True,
                    "error_detection": True
                },
                "session_management": {
                    "save_sessions": True,
                    "export_formats": ["pdf", "png", "svg"],
                    "version_history": True,
                    "permission_control": True
                }
            },
            difficulty=DifficultyLevel.BEGINNER,
            estimated_duration=60,
            learning_objectives=[
                "Collaborate effectively with peers",
                "Visualize and organize ideas",
                "Practice communication skills",
                "Build shared understanding"
            ],
            prerequisites=[],
            metadata={
                "subject": "any",
                "topic": "collaboration",
                "interactive_level": "very_high",
                "real_time": True
            }
        )
    
    def _create_storytelling_engine(self) -> InteractiveComponent:
        """Create interactive storytelling component"""
        return InteractiveComponent(
            id="storytelling_engine",
            title="Interactive Learning Stories",
            type=InteractionType.STORYTELLING,
            content={
                "story_types": [
                    "adventure_learning",
                    "mystery_solving",
                    "historical_simulation",
                    "scientific_discovery",
                    "mathematical_journey"
                ],
                "narrative_elements": {
                    "characters": "adaptive_personas",
                    "plot": "branching_storylines",
                    "setting": "immersive_environments",
                    "challenges": "educational_puzzles"
                },
                "interaction_mechanics": {
                    "choice_points": "decision_making",
                    "mini_games": "skill_practice",
                    "exploration": "discovery_learning",
                    "dialogue": "conversational_ai"
                },
                "learning_integration": {
                    "concept_introduction": "story_context",
                    "practice_opportunities": "embedded_activities",
                    "assessment": "story_outcomes",
                    "reflection": "character_discussions"
                },
                "personalization": {
                    "difficulty_scaling": True,
                    "interest_matching": True,
                    "learning_style": True,
                    "cultural_adaptation": True
                }
            },
            difficulty=DifficultyLevel.INTERMEDIATE,
            estimated_duration=40,
            learning_objectives=[
                "Engage with content through narrative",
                "Apply knowledge in context",
                "Develop critical thinking",
                "Build emotional connection to learning"
            ],
            prerequisites=["basic_reading"],
            metadata={
                "subject": "any",
                "topic": "engagement",
                "interactive_level": "very_high",
                "narrative_driven": True
            }
        )
    
    async def create_learning_session(
        self, 
        user_id: str, 
        components: List[str],
        preferences: Dict[str, Any] = None
    ) -> str:
        """Create a new interactive learning session"""
        session_id = f"session_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Get components from library
        session_components = []
        for component_id in components:
            if component_id in self.component_library:
                session_components.append(self.component_library[component_id])
        
        # Apply user preferences
        if preferences:
            session_components = self._apply_preferences(session_components, preferences)
        
        # Create session
        session = LearningSession(
            session_id=session_id,
            user_id=user_id,
            components=session_components,
            current_component=0,
            start_time=datetime.now(),
            interactions=[],
            performance_metrics={},
            adaptive_adjustments=[]
        )
        
        self.active_sessions[session_id] = session
        
        # Initialize engagement tracking
        self.engagement_tracker[session_id] = UserEngagement(
            user_id=user_id,
            session_id=session_id,
            attention_score=1.0,
            interaction_frequency=0.0,
            completion_rate=0.0,
            time_on_task=0,
            help_requests=0,
            exploration_depth=0.0
        )
        
        logging.info(f"Created interactive learning session {session_id} for user {user_id}")
        return session_id
    
    def _apply_preferences(
        self, 
        components: List[InteractiveComponent], 
        preferences: Dict[str, Any]
    ) -> List[InteractiveComponent]:
        """Apply user preferences to customize components"""
        customized_components = []
        
        for component in components:
            # Create a copy to avoid modifying the original
            customized = InteractiveComponent(
                id=component.id,
                title=component.title,
                type=component.type,
                content=component.content.copy(),
                difficulty=component.difficulty,
                estimated_duration=component.estimated_duration,
                learning_objectives=component.learning_objectives.copy(),
                prerequisites=component.prerequisites.copy(),
                metadata=component.metadata.copy()
            )
            
            # Apply difficulty preference
            if 'difficulty_preference' in preferences:
                preferred_difficulty = preferences['difficulty_preference']
                if preferred_difficulty != component.difficulty.value:
                    customized.content['difficulty_adjustment'] = preferred_difficulty
            
            # Apply learning style preferences
            if 'learning_style' in preferences:
                learning_style = preferences['learning_style']
                if learning_style == 'visual':
                    customized.content['visual_emphasis'] = True
                elif learning_style == 'auditory':
                    customized.content['audio_narration'] = True
                elif learning_style == 'kinesthetic':
                    customized.content['hands_on_activities'] = True
            
            # Apply pace preference
            if 'pace_preference' in preferences:
                pace = preferences['pace_preference']
                if pace == 'slow':
                    customized.estimated_duration = int(customized.estimated_duration * 1.5)
                elif pace == 'fast':
                    customized.estimated_duration = int(customized.estimated_duration * 0.7)
            
            customized_components.append(customized)
        
        return customized_components
    
    async def process_interaction(
        self, 
        session_id: str, 
        interaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process user interaction and provide real-time feedback"""
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        session = self.active_sessions[session_id]
        current_component = session.components[session.current_component]
        
        # Record interaction
        interaction = {
            "timestamp": datetime.now(),
            "component_id": current_component.id,
            "interaction_type": interaction_data.get("type"),
            "data": interaction_data.get("data", {}),
            "response_time": interaction_data.get("response_time", 0)
        }
        session.interactions.append(interaction)
        
        # Update engagement metrics
        await self._update_engagement_metrics(session_id, interaction)
        
        # Generate real-time feedback
        feedback = await self._generate_feedback(session, interaction)
        
        # Check for adaptive adjustments
        if self.adaptive_difficulty:
            adjustment = await self._check_adaptive_adjustment(session, interaction)
            if adjustment:
                session.adaptive_adjustments.append(adjustment)
                feedback["adaptive_adjustment"] = adjustment
        
        # Update performance metrics
        await self._update_performance_metrics(session, interaction)
        
        return {
            "feedback": feedback,
            "engagement_score": self.engagement_tracker[session_id].attention_score,
            "progress": session.current_component / len(session.components),
            "next_action": await self._suggest_next_action(session)
        }
    
    async def _update_engagement_metrics(
        self, 
        session_id: str, 
        interaction: Dict[str, Any]
    ):
        """Update user engagement metrics"""
        engagement = self.engagement_tracker[session_id]
        session = self.active_sessions[session_id]
        
        # Update interaction frequency
        time_since_start = (datetime.now() - session.start_time).total_seconds()
        engagement.interaction_frequency = len(session.interactions) / max(time_since_start / 60, 1)
        
        # Update attention score based on response time
        response_time = interaction.get("response_time", 0)
        if response_time > 0:
            # Optimal response time range (2-10 seconds)
            if 2 <= response_time <= 10:
                attention_adjustment = 0.1
            elif response_time < 2:
                attention_adjustment = -0.05  # Too fast, might be guessing
            else:
                attention_adjustment = -0.1   # Too slow, might be distracted
            
            engagement.attention_score = max(0, min(1, 
                engagement.attention_score + attention_adjustment))
        
        # Update completion rate
        engagement.completion_rate = session.current_component / len(session.components)
        
        # Update time on task
        engagement.time_on_task = int(time_since_start / 60)
        
        # Track help requests
        if interaction.get("type") == "help_request":
            engagement.help_requests += 1
    
    async def _generate_feedback(
        self, 
        session: LearningSession, 
        interaction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate real-time feedback for user interaction"""
        feedback = {
            "type": "informative",
            "message": "",
            "suggestions": [],
            "encouragement": "",
            "next_steps": []
        }
        
        interaction_type = interaction.get("type")
        interaction_data = interaction.get("data", {})
        
        # Generate feedback based on interaction type
        if interaction_type == "answer_submission":
            correct = interaction_data.get("correct", False)
            if correct:
                feedback["type"] = "positive"
                feedback["message"] = "Excellent work! You got it right."
                feedback["encouragement"] = random.choice([
                    "Keep up the great work!",
                    "You're doing fantastic!",
                    "Your understanding is improving!",
                    "Well done!"
                ])
            else:
                feedback["type"] = "constructive"
                feedback["message"] = "Not quite right, but you're on the right track!"
                feedback["suggestions"] = [
                    "Review the key concepts",
                    "Try breaking down the problem step by step",
                    "Consider the relationships between variables"
                ]
                feedback["encouragement"] = "Learning from mistakes is part of the process!"
        
        elif interaction_type == "exploration":
            feedback["type"] = "encouraging"
            feedback["message"] = "Great exploration! You're discovering new connections."
            feedback["next_steps"] = [
                "Try adjusting different parameters",
                "Observe how changes affect the outcome",
                "Form hypotheses about what you see"
            ]
        
        elif interaction_type == "help_request":
            feedback["type"] = "supportive"
            feedback["message"] = "I'm here to help! Let's work through this together."
            feedback["suggestions"] = await self._generate_contextual_hints(session, interaction)
        
        return feedback
    
    async def _generate_contextual_hints(
        self, 
        session: LearningSession, 
        interaction: Dict[str, Any]
    ) -> List[str]:
        """Generate contextual hints based on current learning context"""
        current_component = session.components[session.current_component]
        
        # Basic hints based on component type
        hints = []
        
        if current_component.type == InteractionType.QUIZ:
            hints = [
                "Read the question carefully",
                "Eliminate obviously wrong answers first",
                "Look for keywords that might give clues",
                "Think about what you've learned recently"
            ]
        elif current_component.type == InteractionType.SIMULATION:
            hints = [
                "Try changing one variable at a time",
                "Observe the patterns in the results",
                "Think about cause and effect relationships",
                "Compare with real-world examples"
            ]
        elif current_component.type == InteractionType.VISUALIZATION:
            hints = [
                "Look for patterns in the visual representation",
                "Try different viewing angles or scales",
                "Connect the visual to the mathematical concept",
                "Use the interactive controls to explore"
            ]
        
        return hints[:3]  # Return top 3 hints
    
    async def _check_adaptive_adjustment(
        self, 
        session: LearningSession, 
        interaction: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check if adaptive difficulty adjustment is needed"""
        if len(session.interactions) < 3:
            return None  # Need more data
        
        # Analyze recent performance
        recent_interactions = session.interactions[-5:]
        correct_answers = sum(1 for i in recent_interactions 
                            if i.get("data", {}).get("correct", False))
        accuracy = correct_answers / len(recent_interactions)
        
        # Check engagement level
        engagement = self.engagement_tracker[session.session_id]
        
        adjustment = None
        
        # Increase difficulty if performing too well
        if accuracy > 0.9 and engagement.attention_score > 0.8:
            adjustment = {
                "type": "increase_difficulty",
                "reason": "High performance and engagement",
                "adjustment": 0.2,
                "timestamp": datetime.now()
            }
        
        # Decrease difficulty if struggling
        elif accuracy < 0.4 or engagement.attention_score < 0.5:
            adjustment = {
                "type": "decrease_difficulty",
                "reason": "Low performance or engagement",
                "adjustment": -0.2,
                "timestamp": datetime.now()
            }
        
        # Provide additional support if many help requests
        elif engagement.help_requests > 3:
            adjustment = {
                "type": "increase_support",
                "reason": "Multiple help requests",
                "adjustment": "more_hints",
                "timestamp": datetime.now()
            }
        
        return adjustment
    
    async def _update_performance_metrics(
        self, 
        session: LearningSession, 
        interaction: Dict[str, Any]
    ):
        """Update session performance metrics"""
        if "performance_metrics" not in session.performance_metrics:
            session.performance_metrics = {
                "total_interactions": 0,
                "correct_answers": 0,
                "accuracy": 0.0,
                "average_response_time": 0.0,
                "help_requests": 0,
                "exploration_actions": 0
            }
        
        metrics = session.performance_metrics
        metrics["total_interactions"] += 1
        
        interaction_type = interaction.get("type")
        interaction_data = interaction.get("data", {})
        
        if interaction_type == "answer_submission":
            if interaction_data.get("correct", False):
                metrics["correct_answers"] += 1
            metrics["accuracy"] = metrics["correct_answers"] / metrics["total_interactions"]
        
        elif interaction_type == "help_request":
            metrics["help_requests"] += 1
        
        elif interaction_type == "exploration":
            metrics["exploration_actions"] += 1
        
        # Update average response time
        response_time = interaction.get("response_time", 0)
        if response_time > 0:
            current_avg = metrics["average_response_time"]
            total_timed = sum(1 for i in session.interactions if i.get("response_time", 0) > 0)
            metrics["average_response_time"] = (
                (current_avg * (total_timed - 1) + response_time) / total_timed
            )
    
    async def _suggest_next_action(self, session: LearningSession) -> Dict[str, Any]:
        """Suggest the next action for the user"""
        current_component = session.components[session.current_component]
        engagement = self.engagement_tracker[session.session_id]
        
        suggestions = {
            "primary_action": "",
            "alternatives": [],
            "reasoning": ""
        }
        
        # Check if current component is complete
        component_progress = self._calculate_component_progress(session)
        
        if component_progress >= 0.8:
            # Move to next component
            if session.current_component < len(session.components) - 1:
                suggestions["primary_action"] = "next_component"
                suggestions["reasoning"] = "You've mastered this component!"
            else:
                suggestions["primary_action"] = "complete_session"
                suggestions["reasoning"] = "Congratulations! You've completed the session."
        
        elif engagement.attention_score < 0.6:
            # Suggest a break or change of pace
            suggestions["primary_action"] = "take_break"
            suggestions["alternatives"] = ["change_activity", "get_help"]
            suggestions["reasoning"] = "A short break might help you refocus."
        
        elif component_progress < 0.3:
            # Suggest more practice or help
            suggestions["primary_action"] = "continue_practice"
            suggestions["alternatives"] = ["get_hint", "review_concept"]
            suggestions["reasoning"] = "Keep practicing to build your understanding."
        
        else:
            # Continue with current component
            suggestions["primary_action"] = "continue"
            suggestions["reasoning"] = "You're making good progress!"
        
        return suggestions
    
    def _calculate_component_progress(self, session: LearningSession) -> float:
        """Calculate progress on current component"""
        current_component = session.components[session.current_component]
        
        # Count interactions with current component
        component_interactions = [
            i for i in session.interactions
            if i.get("component_id") == current_component.id
        ]
        
        if not component_interactions:
            return 0.0
        
        # Calculate progress based on component type
        if current_component.type == InteractionType.QUIZ:
            # Progress based on correct answers
            correct_count = sum(1 for i in component_interactions
                              if i.get("data", {}).get("correct", False))
            return min(correct_count / 5, 1.0)  # Assume 5 questions for mastery
        
        elif current_component.type == InteractionType.SIMULATION:
            # Progress based on exploration depth
            exploration_count = sum(1 for i in component_interactions
                                  if i.get("type") == "exploration")
            return min(exploration_count / 10, 1.0)  # Assume 10 explorations for mastery
        
        else:
            # General progress based on time and interactions
            time_spent = len(component_interactions) * 2  # Assume 2 minutes per interaction
            expected_time = current_component.estimated_duration
            return min(time_spent / expected_time, 1.0)
    
    async def get_session_analytics(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive analytics for a learning session"""
        if session_id not in self.active_sessions:
            return {"error": "Session not found"}
        
        session = self.active_sessions[session_id]
        engagement = self.engagement_tracker[session_id]
        
        # Calculate session duration
        session_duration = (datetime.now() - session.start_time).total_seconds() / 60
        
        # Analyze interaction patterns
        interaction_timeline = []
        for i, interaction in enumerate(session.interactions):
            interaction_timeline.append({
                "sequence": i + 1,
                "timestamp": interaction["timestamp"],
                "type": interaction["interaction_type"],
                "component": interaction["component_id"],
                "response_time": interaction.get("response_time", 0)
            })
        
        # Calculate learning velocity
        learning_velocity = len(session.interactions) / max(session_duration, 1)
        
        # Identify learning patterns
        patterns = self._identify_learning_patterns(session)
        
        analytics = {
            "session_overview": {
                "session_id": session_id,
                "user_id": session.user_id,
                "duration_minutes": round(session_duration, 2),
                "components_completed": session.current_component + 1,
                "total_components": len(session.components),
                "completion_rate": (session.current_component + 1) / len(session.components)
            },
            "engagement_metrics": {
                "attention_score": engagement.attention_score,
                "interaction_frequency": engagement.interaction_frequency,
                "time_on_task": engagement.time_on_task,
                "help_requests": engagement.help_requests,
                "exploration_depth": engagement.exploration_depth
            },
            "performance_metrics": session.performance_metrics,
            "learning_velocity": learning_velocity,
            "interaction_timeline": interaction_timeline,
            "learning_patterns": patterns,
            "adaptive_adjustments": session.adaptive_adjustments,
            "recommendations": await self._generate_session_recommendations(session)
        }
        
        return analytics
    
    def _identify_learning_patterns(self, session: LearningSession) -> Dict[str, Any]:
        """Identify learning patterns from session data"""
        patterns = {
            "learning_style_indicators": {},
            "difficulty_preferences": {},
            "interaction_preferences": {},
            "time_patterns": {}
        }
        
        # Analyze interaction types
        interaction_types = {}
        for interaction in session.interactions:
            itype = interaction.get("interaction_type", "unknown")
            interaction_types[itype] = interaction_types.get(itype, 0) + 1
        
        # Determine learning style indicators
        if interaction_types.get("exploration", 0) > interaction_types.get("answer_submission", 0):
            patterns["learning_style_indicators"]["exploratory"] = True
        
        if interaction_types.get("help_request", 0) > len(session.interactions) * 0.2:
            patterns["learning_style_indicators"]["support_seeking"] = True
        
        # Analyze response times for pacing preferences
        response_times = [i.get("response_time", 0) for i in session.interactions if i.get("response_time", 0) > 0]
        if response_times:
            avg_response_time = np.mean(response_times)
            if avg_response_time < 5:
                patterns["time_patterns"]["fast_paced"] = True
            elif avg_response_time > 15:
                patterns["time_patterns"]["deliberate"] = True
        
        return patterns
    
    async def _generate_session_recommendations(self, session: LearningSession) -> List[Dict[str, Any]]:
        """Generate recommendations based on session performance"""
        recommendations = []
        engagement = self.engagement_tracker[session.session_id]
        
        # Engagement-based recommendations
        if engagement.attention_score < 0.6:
            recommendations.append({
                "type": "engagement",
                "priority": "high",
                "message": "Consider taking more frequent breaks or trying different activity types",
                "action": "adjust_pacing"
            })
        
        # Performance-based recommendations
        accuracy = session.performance_metrics.get("accuracy", 0)
        if accuracy < 0.6:
            recommendations.append({
                "type": "performance",
                "priority": "medium",
                "message": "Review foundational concepts before moving to advanced topics",
                "action": "review_prerequisites"
            })
        elif accuracy > 0.9:
            recommendations.append({
                "type": "performance",
                "priority": "low",
                "message": "You're ready for more challenging content",
                "action": "increase_difficulty"
            })
        
        # Help-seeking pattern recommendations
        if engagement.help_requests > 5:
            recommendations.append({
                "type": "support",
                "priority": "medium",
                "message": "Consider additional study materials or peer collaboration",
                "action": "provide_resources"
            })
        
        return recommendations
    
    async def create_visualization(
        self, 
        data: Dict[str, Any], 
        chart_type: str = "interactive"
    ) -> Dict[str, Any]:
        """Create interactive visualizations for learning data"""
        if not PLOTLY_AVAILABLE:
            return {"error": "Visualization library not available"}
        
        try:
            if chart_type == "learning_progress":
                return self._create_progress_chart(data)
            elif chart_type == "engagement_timeline":
                return self._create_engagement_timeline(data)
            elif chart_type == "knowledge_map":
                return self._create_knowledge_map(data)
            elif chart_type == "performance_radar":
                return self._create_performance_radar(data)
            else:
                return {"error": f"Unknown chart type: {chart_type}"}
        
        except Exception as e:
            logging.error(f"Error creating visualization: {e}")
            return {"error": str(e)}
    
    def _create_progress_chart(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create interactive progress chart"""
        fig = go.Figure()
        
        # Add progress line
        fig.add_trace(go.Scatter(
            x=data.get("timestamps", []),
            y=data.get("progress_values", []),
            mode='lines+markers',
            name='Learning Progress',
            line=dict(color='#2E86AB', width=3),
            marker=dict(size=8)
        ))
        
        # Add target line
        if "target_progress" in data:
            fig.add_hline(
                y=data["target_progress"],
                line_dash="dash",
                line_color="red",
                annotation_text="Target"
            )
        
        fig.update_layout(
            title="Learning Progress Over Time",
            xaxis_title="Time",
            yaxis_title="Progress (%)",
            hovermode='x unified',
            template="plotly_white"
        )
        
        return {"chart": fig.to_json(), "type": "progress"}
    
    def _create_engagement_timeline(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create engagement timeline visualization"""
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Attention Score', 'Interaction Frequency'),
            vertical_spacing=0.1
        )
        
        # Attention score
        fig.add_trace(
            go.Scatter(
                x=data.get("timestamps", []),
                y=data.get("attention_scores", []),
                mode='lines+markers',
                name='Attention',
                line=dict(color='#A23B72')
            ),
            row=1, col=1
        )
        
        # Interaction frequency
        fig.add_trace(
            go.Bar(
                x=data.get("timestamps", []),
                y=data.get("interaction_frequencies", []),
                name='Interactions',
                marker_color='#F18F01'
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            title="Engagement Timeline",
            template="plotly_white",
            showlegend=False
        )
        
        return {"chart": fig.to_json(), "type": "engagement"}
    
    async def get_component_library(self) -> Dict[str, Any]:
        """Get the complete interactive component library"""
        library_info = {}
        
        for component_id, component in self.component_library.items():
            library_info[component_id] = {
                "title": component.title,
                "type": component.type.value,
                "difficulty": component.difficulty.value,
                "duration": component.estimated_duration,
                "objectives": component.learning_objectives,
                "prerequisites": component.prerequisites,
                "subject": component.metadata.get("subject"),
                "topic": component.metadata.get("topic"),
                "interactive_level": component.metadata.get("interactive_level")
            }
        
        return {
            "total_components": len(library_info),
            "components": library_info,
            "categories": {
                "by_type": self._group_by_type(),
                "by_subject": self._group_by_subject(),
                "by_difficulty": self._group_by_difficulty()
            }
        }
    
    def _group_by_type(self) -> Dict[str, List[str]]:
        """Group components by interaction type"""
        groups = {}
        for component_id, component in self.component_library.items():
            type_name = component.type.value
            if type_name not in groups:
                groups[type_name] = []
            groups[type_name].append(component_id)
        return groups
    
    def _group_by_subject(self) -> Dict[str, List[str]]:
        """Group components by subject"""
        groups = {}
        for component_id, component in self.component_library.items():
            subject = component.metadata.get("subject", "general")
            if subject not in groups:
                groups[subject] = []
            groups[subject].append(component_id)
        return groups
    
    def _group_by_difficulty(self) -> Dict[str, List[str]]:
        """Group components by difficulty level"""
        groups = {}
        for component_id, component in self.component_library.items():
            difficulty = component.difficulty.value
            if difficulty not in groups:
                groups[difficulty] = []
            groups[difficulty].append(component_id)
        return groups

# Additional helper functions for specific interactive components

# Global service instance
interactive_learning_service = None

def get_interactive_learning_service() -> InteractiveLearningService:
    """Get or create the global Interactive Learning service instance"""
    global interactive_learning_service
    if interactive_learning_service is None:
        interactive_learning_service = InteractiveLearningService()
    return interactive_learning_service