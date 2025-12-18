"""
Interactive Learning Dashboard
Provides real-time interactive visualizations and controls for enhanced learning
"""

import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
import numpy as np
from dataclasses import dataclass, asdict

# Dashboard components
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import plotly.figure_factory as ff
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logging.warning("Plotly not available for dashboard visualizations")

@dataclass
class DashboardWidget:
    """Represents a dashboard widget"""
    id: str
    title: str
    type: str  # 'chart', 'metric', 'control', 'text', 'interactive'
    content: Dict[str, Any]
    position: Tuple[int, int]  # (row, col)
    size: Tuple[int, int]  # (width, height)
    refresh_interval: int = 0  # seconds, 0 = no auto-refresh
    interactive: bool = True

@dataclass
class DashboardLayout:
    """Represents dashboard layout configuration"""
    id: str
    name: str
    description: str
    widgets: List[DashboardWidget]
    grid_size: Tuple[int, int]  # (rows, cols)
    theme: str = "light"
    auto_refresh: bool = True

class InteractiveDashboard:
    """
    Interactive Learning Dashboard for real-time learning analytics and controls
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.layouts = {}
        self.active_sessions = {}
        self.real_time_data = {}
        
        # Initialize default layouts
        self._initialize_default_layouts()
        
        logging.info("Interactive Dashboard initialized")
    
    def _initialize_default_layouts(self):
        """Initialize default dashboard layouts"""
        # Student Learning Dashboard
        self.layouts['student_dashboard'] = self._create_student_dashboard()
        
        # Teacher Analytics Dashboard
        self.layouts['teacher_dashboard'] = self._create_teacher_dashboard()
        
        # Knowledge Graph Explorer
        self.layouts['knowledge_explorer'] = self._create_knowledge_explorer()
        
        # Memory Intelligence Dashboard
        self.layouts['memory_dashboard'] = self._create_memory_dashboard()
        
        # Interactive Learning Lab
        self.layouts['learning_lab'] = self._create_learning_lab()
    
    def _create_student_dashboard(self) -> DashboardLayout:
        """Create student-focused learning dashboard"""
        widgets = [
            # Progress Overview
            DashboardWidget(
                id="progress_overview",
                title="Learning Progress",
                type="chart",
                content={
                    "chart_type": "progress_ring",
                    "data_source": "user_progress",
                    "metrics": ["completion_rate", "mastery_level", "streak_days"],
                    "interactive_features": ["drill_down", "time_range_selector"]
                },
                position=(0, 0),
                size=(2, 2),
                refresh_interval=30
            ),
            
            # Knowledge Map
            DashboardWidget(
                id="knowledge_map",
                title="Knowledge Network",
                type="interactive",
                content={
                    "component_type": "network_graph",
                    "data_source": "knowledge_graph",
                    "features": [
                        "concept_nodes",
                        "relationship_edges",
                        "mastery_coloring",
                        "interactive_exploration",
                        "zoom_and_pan"
                    ],
                    "controls": {
                        "filter_by_subject": True,
                        "filter_by_mastery": True,
                        "layout_algorithm": ["force", "hierarchical", "circular"]
                    }
                },
                position=(0, 2),
                size=(3, 4),
                interactive=True
            ),
            
            # Real-time Performance
            DashboardWidget(
                id="performance_metrics",
                title="Performance Metrics",
                type="chart",
                content={
                    "chart_type": "multi_metric",
                    "metrics": [
                        {"name": "Accuracy", "value": 0.85, "target": 0.9, "trend": "up"},
                        {"name": "Speed", "value": 0.75, "target": 0.8, "trend": "stable"},
                        {"name": "Engagement", "value": 0.92, "target": 0.85, "trend": "up"}
                    ],
                    "visualization": "gauge_charts"
                },
                position=(2, 0),
                size=(2, 2)
            ),
            
            # Learning Recommendations
            DashboardWidget(
                id="recommendations",
                title="Recommended Next Steps",
                type="interactive",
                content={
                    "component_type": "recommendation_cards",
                    "data_source": "ai_recommendations",
                    "features": [
                        "concept_cards",
                        "difficulty_indicators",
                        "time_estimates",
                        "prerequisite_checks",
                        "one_click_start"
                    ]
                },
                position=(3, 0),
                size=(2, 3),
                interactive=True
            ),
            
            # Study Session Controls
            DashboardWidget(
                id="session_controls",
                title="Study Session",
                type="control",
                content={
                    "component_type": "session_manager",
                    "controls": [
                        {"type": "start_session", "label": "Start Learning"},
                        {"type": "pause_session", "label": "Take Break"},
                        {"type": "end_session", "label": "End Session"},
                        {"type": "help_request", "label": "Get Help"}
                    ],
                    "status_display": {
                        "current_topic": True,
                        "time_elapsed": True,
                        "questions_completed": True,
                        "current_streak": True
                    }
                },
                position=(4, 0),
                size=(2, 2),
                interactive=True
            ),
            
            # Achievement Tracker
            DashboardWidget(
                id="achievements",
                title="Achievements & Badges",
                type="interactive",
                content={
                    "component_type": "achievement_gallery",
                    "features": [
                        "earned_badges",
                        "progress_bars",
                        "milestone_celebrations",
                        "leaderboard_position"
                    ],
                    "gamification": {
                        "points_display": True,
                        "level_progression": True,
                        "challenge_notifications": True
                    }
                },
                position=(4, 2),
                size=(2, 2),
                interactive=True
            )
        ]
        
        return DashboardLayout(
            id="student_dashboard",
            name="Student Learning Dashboard",
            description="Comprehensive learning dashboard for students",
            widgets=widgets,
            grid_size=(6, 6),
            theme="light",
            auto_refresh=True
        )
    
    def _create_teacher_dashboard(self) -> DashboardLayout:
        """Create teacher-focused analytics dashboard"""
        widgets = [
            # Class Overview
            DashboardWidget(
                id="class_overview",
                title="Class Performance Overview",
                type="chart",
                content={
                    "chart_type": "class_heatmap",
                    "data_source": "class_analytics",
                    "metrics": ["student_progress", "engagement_levels", "difficulty_areas"],
                    "interactive_features": ["student_drill_down", "time_filtering"]
                },
                position=(0, 0),
                size=(3, 3)
            ),
            
            # Learning Analytics
            DashboardWidget(
                id="learning_analytics",
                title="Learning Analytics",
                type="chart",
                content={
                    "chart_type": "multi_series_line",
                    "data_source": "learning_metrics",
                    "series": [
                        "average_accuracy",
                        "completion_rates",
                        "engagement_scores",
                        "help_requests"
                    ],
                    "time_range": "last_30_days"
                },
                position=(0, 3),
                size=(3, 3)
            ),
            
            # Student Progress Matrix
            DashboardWidget(
                id="progress_matrix",
                title="Student Progress Matrix",
                type="interactive",
                content={
                    "component_type": "progress_matrix",
                    "data_source": "student_progress",
                    "features": [
                        "student_rows",
                        "concept_columns",
                        "mastery_color_coding",
                        "interactive_cells",
                        "filtering_controls"
                    ]
                },
                position=(3, 0),
                size=(3, 4),
                interactive=True
            ),
            
            # Intervention Alerts
            DashboardWidget(
                id="intervention_alerts",
                title="Intervention Alerts",
                type="interactive",
                content={
                    "component_type": "alert_system",
                    "alert_types": [
                        "struggling_students",
                        "disengaged_learners",
                        "advanced_ready",
                        "concept_difficulties"
                    ],
                    "actions": [
                        "send_message",
                        "schedule_meeting",
                        "assign_resources",
                        "create_group"
                    ]
                },
                position=(3, 4),
                size=(2, 2),
                interactive=True
            ),
            
            # Content Analytics
            DashboardWidget(
                id="content_analytics",
                title="Content Performance",
                type="chart",
                content={
                    "chart_type": "content_effectiveness",
                    "data_source": "content_metrics",
                    "metrics": [
                        "concept_difficulty_distribution",
                        "resource_usage_patterns",
                        "assessment_performance",
                        "time_on_task"
                    ]
                },
                position=(5, 0),
                size=(2, 3)
            )
        ]
        
        return DashboardLayout(
            id="teacher_dashboard",
            name="Teacher Analytics Dashboard",
            description="Comprehensive analytics dashboard for teachers",
            widgets=widgets,
            grid_size=(6, 6),
            theme="professional",
            auto_refresh=True
        )
    
    def _create_knowledge_explorer(self) -> DashboardLayout:
        """Create interactive knowledge graph explorer"""
        widgets = [
            # Main Knowledge Graph
            DashboardWidget(
                id="main_knowledge_graph",
                title="Knowledge Graph Explorer",
                type="interactive",
                content={
                    "component_type": "3d_knowledge_graph",
                    "data_source": "neo4j_graph",
                    "features": [
                        "3d_visualization",
                        "concept_clustering",
                        "relationship_filtering",
                        "path_highlighting",
                        "interactive_navigation"
                    ],
                    "controls": {
                        "layout_algorithms": ["force_directed", "hierarchical", "circular"],
                        "node_sizing": ["importance", "mastery", "difficulty"],
                        "edge_filtering": ["prerequisite", "related", "applies_to"],
                        "search_and_filter": True
                    }
                },
                position=(0, 0),
                size=(4, 4),
                interactive=True
            ),
            
            # Concept Details Panel
            DashboardWidget(
                id="concept_details",
                title="Concept Details",
                type="interactive",
                content={
                    "component_type": "concept_inspector",
                    "features": [
                        "concept_information",
                        "prerequisite_tree",
                        "dependent_concepts",
                        "learning_resources",
                        "performance_data"
                    ],
                    "actions": [
                        "start_learning",
                        "add_to_plan",
                        "mark_mastered",
                        "request_help"
                    ]
                },
                position=(0, 4),
                size=(2, 2),
                interactive=True
            ),
            
            # Learning Path Planner
            DashboardWidget(
                id="path_planner",
                title="Learning Path Planner",
                type="interactive",
                content={
                    "component_type": "path_planner",
                    "features": [
                        "drag_drop_concepts",
                        "automatic_ordering",
                        "difficulty_balancing",
                        "time_estimation",
                        "prerequisite_validation"
                    ],
                    "planning_modes": ["guided", "manual", "ai_optimized"]
                },
                position=(2, 4),
                size=(2, 2),
                interactive=True
            ),
            
            # Graph Statistics
            DashboardWidget(
                id="graph_statistics",
                title="Graph Statistics",
                type="chart",
                content={
                    "chart_type": "graph_metrics",
                    "metrics": [
                        "total_concepts",
                        "relationship_density",
                        "learning_paths",
                        "mastery_distribution"
                    ],
                    "visualizations": ["pie_charts", "bar_charts", "metrics_cards"]
                },
                position=(4, 0),
                size=(2, 2)
            ),
            
            # Search and Filter Controls
            DashboardWidget(
                id="search_controls",
                title="Search & Filter",
                type="control",
                content={
                    "component_type": "advanced_search",
                    "search_types": [
                        "concept_search",
                        "path_search",
                        "similarity_search",
                        "prerequisite_search"
                    ],
                    "filters": [
                        "subject_filter",
                        "difficulty_filter",
                        "mastery_filter",
                        "relationship_filter"
                    ]
                },
                position=(4, 2),
                size=(2, 2),
                interactive=True
            )
        ]
        
        return DashboardLayout(
            id="knowledge_explorer",
            name="Knowledge Graph Explorer",
            description="Interactive exploration of the knowledge graph",
            widgets=widgets,
            grid_size=(6, 6),
            theme="dark",
            auto_refresh=False
        )
    
    def _create_memory_dashboard(self) -> DashboardLayout:
        """Create memory intelligence dashboard"""
        widgets = [
            # Memory Usage Overview
            DashboardWidget(
                id="memory_overview",
                title="Memory Intelligence Overview",
                type="chart",
                content={
                    "chart_type": "memory_metrics",
                    "data_source": "memmachine_stats",
                    "metrics": [
                        "total_memories",
                        "memory_pools",
                        "storage_usage",
                        "access_patterns"
                    ]
                },
                position=(0, 0),
                size=(2, 2)
            ),
            
            # Learning Pattern Analysis
            DashboardWidget(
                id="learning_patterns",
                title="Learning Pattern Analysis",
                type="interactive",
                content={
                    "component_type": "pattern_analyzer",
                    "data_source": "learning_patterns",
                    "visualizations": [
                        "temporal_patterns",
                        "subject_preferences",
                        "difficulty_progression",
                        "engagement_cycles"
                    ],
                    "interactive_features": [
                        "pattern_filtering",
                        "time_range_selection",
                        "pattern_comparison"
                    ]
                },
                position=(0, 2),
                size=(3, 2),
                interactive=True
            ),
            
            # Memory Timeline
            DashboardWidget(
                id="memory_timeline",
                title="Learning Memory Timeline",
                type="interactive",
                content={
                    "component_type": "memory_timeline",
                    "data_source": "memory_entries",
                    "features": [
                        "chronological_view",
                        "importance_sizing",
                        "subject_coloring",
                        "interactive_zoom",
                        "memory_details_popup"
                    ]
                },
                position=(2, 0),
                size=(4, 2),
                interactive=True
            ),
            
            # Retention Analysis
            DashboardWidget(
                id="retention_analysis",
                title="Knowledge Retention Analysis",
                type="chart",
                content={
                    "chart_type": "retention_curves",
                    "data_source": "retention_data",
                    "analysis_types": [
                        "forgetting_curves",
                        "spaced_repetition_effectiveness",
                        "concept_retention_rates",
                        "review_scheduling"
                    ]
                },
                position=(3, 2),
                size=(3, 2)
            ),
            
            # Memory Insights
            DashboardWidget(
                id="memory_insights",
                title="AI Memory Insights",
                type="interactive",
                content={
                    "component_type": "insight_generator",
                    "insight_types": [
                        "learning_velocity_trends",
                        "optimal_study_times",
                        "concept_connection_strength",
                        "personalized_recommendations"
                    ],
                    "actions": [
                        "apply_insights",
                        "schedule_reviews",
                        "adjust_difficulty",
                        "optimize_path"
                    ]
                },
                position=(4, 0),
                size=(2, 4),
                interactive=True
            )
        ]
        
        return DashboardLayout(
            id="memory_dashboard",
            name="Memory Intelligence Dashboard",
            description="Advanced memory and learning pattern analysis",
            widgets=widgets,
            grid_size=(6, 6),
            theme="neural",
            auto_refresh=True
        )
    
    def _create_learning_lab(self) -> DashboardLayout:
        """Create interactive learning laboratory"""
        widgets = [
            # Interactive Simulator
            DashboardWidget(
                id="main_simulator",
                title="Interactive Learning Simulator",
                type="interactive",
                content={
                    "component_type": "multi_subject_simulator",
                    "simulators": {
                        "mathematics": ["algebra_visualizer", "calculus_explorer", "geometry_lab"],
                        "physics": ["mechanics_simulator", "wave_lab", "circuit_builder"],
                        "chemistry": ["molecule_builder", "reaction_chamber", "periodic_explorer"]
                    },
                    "features": [
                        "real_time_calculation",
                        "parameter_adjustment",
                        "result_visualization",
                        "step_by_step_guidance"
                    ]
                },
                position=(0, 0),
                size=(4, 4),
                interactive=True
            ),
            
            # Experiment Controls
            DashboardWidget(
                id="experiment_controls",
                title="Experiment Controls",
                type="control",
                content={
                    "component_type": "experiment_controller",
                    "controls": [
                        {"type": "parameter_sliders", "label": "Adjust Parameters"},
                        {"type": "run_experiment", "label": "Run Experiment"},
                        {"type": "reset_simulation", "label": "Reset"},
                        {"type": "save_results", "label": "Save Results"}
                    ],
                    "parameter_sets": [
                        "beginner_presets",
                        "intermediate_challenges",
                        "advanced_scenarios"
                    ]
                },
                position=(0, 4),
                size=(2, 2),
                interactive=True
            ),
            
            # Results Analysis
            DashboardWidget(
                id="results_analysis",
                title="Results Analysis",
                type="chart",
                content={
                    "chart_type": "experiment_results",
                    "analysis_tools": [
                        "data_plotting",
                        "trend_analysis",
                        "statistical_summary",
                        "comparison_tools"
                    ],
                    "export_options": ["csv", "pdf", "image"]
                },
                position=(2, 4),
                size=(2, 2)
            ),
            
            # Learning Objectives
            DashboardWidget(
                id="learning_objectives",
                title="Learning Objectives",
                type="interactive",
                content={
                    "component_type": "objective_tracker",
                    "features": [
                        "objective_checklist",
                        "progress_indicators",
                        "concept_connections",
                        "mastery_validation"
                    ]
                },
                position=(4, 0),
                size=(2, 2),
                interactive=True
            ),
            
            # Collaborative Space
            DashboardWidget(
                id="collaboration",
                title="Collaborative Learning",
                type="interactive",
                content={
                    "component_type": "collaboration_hub",
                    "features": [
                        "shared_experiments",
                        "peer_discussions",
                        "group_challenges",
                        "teacher_guidance"
                    ]
                },
                position=(4, 2),
                size=(2, 2),
                interactive=True
            ),
            
            # AI Tutor Assistant
            DashboardWidget(
                id="ai_tutor",
                title="AI Tutor Assistant",
                type="interactive",
                content={
                    "component_type": "ai_tutor_chat",
                    "features": [
                        "contextual_help",
                        "concept_explanations",
                        "problem_solving_guidance",
                        "personalized_hints"
                    ]
                },
                position=(4, 4),
                size=(2, 2),
                interactive=True
            )
        ]
        
        return DashboardLayout(
            id="learning_lab",
            name="Interactive Learning Laboratory",
            description="Hands-on interactive learning environment",
            widgets=widgets,
            grid_size=(6, 6),
            theme="lab",
            auto_refresh=False
        )
    
    async def generate_dashboard_html(
        self, 
        layout_id: str, 
        user_data: Dict[str, Any] = None
    ) -> str:
        """Generate complete HTML dashboard"""
        if layout_id not in self.layouts:
            raise ValueError(f"Layout {layout_id} not found")
        
        layout = self.layouts[layout_id]
        
        # Generate HTML structure
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{layout.name}</title>
            
            <!-- External Libraries -->
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
            
            <!-- Styles -->
            <style>
                {self._generate_dashboard_css(layout)}
            </style>
        </head>
        <body>
            <div class="dashboard-container" id="dashboard-{layout.id}">
                <header class="dashboard-header">
                    <h1>{layout.name}</h1>
                    <div class="dashboard-controls">
                        <button id="refresh-btn" class="control-btn">Refresh</button>
                        <button id="fullscreen-btn" class="control-btn">Fullscreen</button>
                        <button id="settings-btn" class="control-btn">Settings</button>
                    </div>
                </header>
                
                <main class="dashboard-grid">
                    {await self._generate_widgets_html(layout.widgets, user_data)}
                </main>
            </div>
            
            <!-- JavaScript -->
            <script>
                {await self._generate_dashboard_js(layout, user_data)}
            </script>
        </body>
        </html>
        """
        
        return html_content
    
    def _generate_dashboard_css(self, layout: DashboardLayout) -> str:
        """Generate CSS for dashboard layout"""
        theme_colors = {
            "light": {
                "primary": "#2E86AB",
                "secondary": "#A23B72",
                "background": "#F8F9FA",
                "surface": "#FFFFFF",
                "text": "#333333"
            },
            "dark": {
                "primary": "#4FC3F7",
                "secondary": "#FF6B9D",
                "background": "#1A1A1A",
                "surface": "#2D2D2D",
                "text": "#FFFFFF"
            },
            "professional": {
                "primary": "#1976D2",
                "secondary": "#388E3C",
                "background": "#F5F5F5",
                "surface": "#FFFFFF",
                "text": "#212121"
            },
            "neural": {
                "primary": "#9C27B0",
                "secondary": "#FF5722",
                "background": "#0A0A0A",
                "surface": "#1E1E1E",
                "text": "#E0E0E0"
            },
            "lab": {
                "primary": "#00BCD4",
                "secondary": "#FFC107",
                "background": "#FAFAFA",
                "surface": "#FFFFFF",
                "text": "#424242"
            }
        }
        
        colors = theme_colors.get(layout.theme, theme_colors["light"])
        
        return f"""
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: {colors['background']};
            color: {colors['text']};
            overflow-x: hidden;
        }}
        
        .dashboard-container {{
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        
        .dashboard-header {{
            background-color: {colors['surface']};
            padding: 1rem 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 3px solid {colors['primary']};
        }}
        
        .dashboard-header h1 {{
            color: {colors['primary']};
            font-size: 1.8rem;
            font-weight: 600;
        }}
        
        .dashboard-controls {{
            display: flex;
            gap: 0.5rem;
        }}
        
        .control-btn {{
            background-color: {colors['primary']};
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: background-color 0.3s;
        }}
        
        .control-btn:hover {{
            background-color: {colors['secondary']};
        }}
        
        .dashboard-grid {{
            flex: 1;
            display: grid;
            grid-template-columns: repeat({layout.grid_size[1]}, 1fr);
            grid-template-rows: repeat({layout.grid_size[0]}, 1fr);
            gap: 1rem;
            padding: 1rem;
            min-height: calc(100vh - 80px);
        }}
        
        .widget {{
            background-color: {colors['surface']};
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 1rem;
            display: flex;
            flex-direction: column;
            transition: transform 0.3s, box-shadow 0.3s;
        }}
        
        .widget:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.15);
        }}
        
        .widget-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid {colors['primary']};
        }}
        
        .widget-title {{
            font-size: 1.1rem;
            font-weight: 600;
            color: {colors['primary']};
        }}
        
        .widget-content {{
            flex: 1;
            display: flex;
            flex-direction: column;
        }}
        
        .interactive-widget {{
            cursor: pointer;
        }}
        
        .metric-card {{
            background: linear-gradient(135deg, {colors['primary']}, {colors['secondary']});
            color: white;
            padding: 1rem;
            border-radius: 6px;
            text-align: center;
            margin: 0.5rem 0;
        }}
        
        .metric-value {{
            font-size: 2rem;
            font-weight: bold;
        }}
        
        .metric-label {{
            font-size: 0.9rem;
            opacity: 0.9;
        }}
        
        .chart-container {{
            width: 100%;
            height: 100%;
            min-height: 200px;
        }}
        
        .control-panel {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin: 0.5rem 0;
        }}
        
        .control-element {{
            padding: 0.5rem;
            border: 1px solid {colors['primary']};
            border-radius: 4px;
            background-color: {colors['background']};
            color: {colors['text']};
        }}
        
        .loading-spinner {{
            border: 3px solid {colors['background']};
            border-top: 3px solid {colors['primary']};
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: auto;
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        
        .notification {{
            position: fixed;
            top: 20px;
            right: 20px;
            background-color: {colors['primary']};
            color: white;
            padding: 1rem;
            border-radius: 4px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            z-index: 1000;
            animation: slideIn 0.3s ease-out;
        }}
        
        @keyframes slideIn {{
            from {{ transform: translateX(100%); }}
            to {{ transform: translateX(0); }}
        }}
        
        @media (max-width: 768px) {{
            .dashboard-grid {{
                grid-template-columns: 1fr;
                grid-template-rows: auto;
            }}
            
            .widget {{
                grid-column: 1 !important;
                grid-row: auto !important;
            }}
        }}
        """
    
    async def _generate_widgets_html(
        self, 
        widgets: List[DashboardWidget], 
        user_data: Dict[str, Any] = None
    ) -> str:
        """Generate HTML for dashboard widgets"""
        html_parts = []
        
        for widget in widgets:
            widget_html = f"""
            <div class="widget {'interactive-widget' if widget.interactive else ''}" 
                 id="widget-{widget.id}"
                 style="grid-column: {widget.position[1] + 1} / span {widget.size[0]};
                        grid-row: {widget.position[0] + 1} / span {widget.size[1]};">
                
                <div class="widget-header">
                    <h3 class="widget-title">{widget.title}</h3>
                    <div class="widget-controls">
                        {await self._generate_widget_controls(widget)}
                    </div>
                </div>
                
                <div class="widget-content" id="content-{widget.id}">
                    {await self._generate_widget_content(widget, user_data)}
                </div>
            </div>
            """
            html_parts.append(widget_html)
        
        return "\n".join(html_parts)
    
    async def _generate_widget_controls(self, widget: DashboardWidget) -> str:
        """Generate controls for a widget"""
        controls = []
        
        if widget.refresh_interval > 0:
            controls.append('<button class="widget-btn" onclick="refreshWidget(\'{}\')">↻</button>'.format(widget.id))
        
        if widget.interactive:
            controls.append('<button class="widget-btn" onclick="expandWidget(\'{}\')">⛶</button>'.format(widget.id))
        
        return " ".join(controls)
    
    async def _generate_widget_content(
        self, 
        widget: DashboardWidget, 
        user_data: Dict[str, Any] = None
    ) -> str:
        """Generate content for a specific widget"""
        if widget.type == "chart":
            return f'<div class="chart-container" id="chart-{widget.id}"></div>'
        
        elif widget.type == "metric":
            return await self._generate_metric_content(widget, user_data)
        
        elif widget.type == "control":
            return await self._generate_control_content(widget)
        
        elif widget.type == "interactive":
            return await self._generate_interactive_content(widget, user_data)
        
        elif widget.type == "text":
            return f'<div class="text-content">{widget.content.get("text", "")}</div>'
        
        else:
            return '<div class="loading-spinner"></div>'
    
    async def _generate_metric_content(
        self, 
        widget: DashboardWidget, 
        user_data: Dict[str, Any] = None
    ) -> str:
        """Generate metric widget content"""
        metrics = widget.content.get("metrics", [])
        html_parts = []
        
        for metric in metrics:
            if isinstance(metric, dict):
                html_parts.append(f"""
                <div class="metric-card">
                    <div class="metric-value">{metric.get('value', 0)}</div>
                    <div class="metric-label">{metric.get('name', 'Metric')}</div>
                </div>
                """)
        
        return "\n".join(html_parts)
    
    async def _generate_control_content(self, widget: DashboardWidget) -> str:
        """Generate control widget content"""
        controls = widget.content.get("controls", [])
        html_parts = ['<div class="control-panel">']
        
        for control in controls:
            if isinstance(control, dict):
                control_type = control.get("type", "button")
                label = control.get("label", "Control")
                
                if control_type == "button":
                    html_parts.append(f'<button class="control-element" onclick="handleControl(\'{control_type}\', \'{widget.id}\')">{label}</button>')
                elif control_type == "slider":
                    html_parts.append(f'<input type="range" class="control-element" onchange="handleControl(\'{control_type}\', \'{widget.id}\', this.value)">')
                elif control_type == "select":
                    options = control.get("options", [])
                    select_html = f'<select class="control-element" onchange="handleControl(\'{control_type}\', \'{widget.id}\', this.value)">'
                    for option in options:
                        select_html += f'<option value="{option}">{option}</option>'
                    select_html += '</select>'
                    html_parts.append(select_html)
        
        html_parts.append('</div>')
        return "\n".join(html_parts)
    
    async def _generate_interactive_content(
        self, 
        widget: DashboardWidget, 
        user_data: Dict[str, Any] = None
    ) -> str:
        """Generate interactive widget content"""
        component_type = widget.content.get("component_type", "generic")
        
        if component_type == "network_graph":
            return '<div id="network-{}" class="network-container"></div>'.format(widget.id)
        elif component_type == "3d_knowledge_graph":
            return '<div id="3d-graph-{}" class="graph-3d-container"></div>'.format(widget.id)
        elif component_type == "recommendation_cards":
            return '<div id="recommendations-{}" class="recommendations-container"></div>'.format(widget.id)
        else:
            return f'<div id="interactive-{widget.id}" class="interactive-container">Interactive content loading...</div>'
    
    async def _generate_dashboard_js(
        self, 
        layout: DashboardLayout, 
        user_data: Dict[str, Any] = None
    ) -> str:
        """Generate JavaScript for dashboard functionality"""
        return f"""
        // Dashboard Configuration
        const dashboardConfig = {{
            layoutId: '{layout.id}',
            autoRefresh: {str(layout.auto_refresh).lower()},
            theme: '{layout.theme}',
            widgets: {json.dumps([asdict(w) for w in layout.widgets])}
        }};
        
        // Global Variables
        let refreshIntervals = {{}};
        let websocket = null;
        
        // Initialize Dashboard
        document.addEventListener('DOMContentLoaded', function() {{
            initializeDashboard();
            setupWebSocket();
            loadWidgetData();
        }});
        
        function initializeDashboard() {{
            console.log('Initializing dashboard:', dashboardConfig.layoutId);
            
            // Setup refresh intervals
            dashboardConfig.widgets.forEach(widget => {{
                if (widget.refresh_interval > 0) {{
                    refreshIntervals[widget.id] = setInterval(() => {{
                        refreshWidget(widget.id);
                    }}, widget.refresh_interval * 1000);
                }}
            }});
            
            // Setup event listeners
            document.getElementById('refresh-btn').addEventListener('click', refreshAllWidgets);
            document.getElementById('fullscreen-btn').addEventListener('click', toggleFullscreen);
            document.getElementById('settings-btn').addEventListener('click', openSettings);
        }}
        
        function setupWebSocket() {{
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${{protocol}}//${{window.location.host}}/ws/dashboard/${{dashboardConfig.layoutId}}`;
            
            websocket = new WebSocket(wsUrl);
            
            websocket.onopen = function(event) {{
                console.log('WebSocket connected');
                showNotification('Dashboard connected', 'success');
            }};
            
            websocket.onmessage = function(event) {{
                const data = JSON.parse(event.data);
                handleRealTimeUpdate(data);
            }};
            
            websocket.onclose = function(event) {{
                console.log('WebSocket disconnected');
                setTimeout(setupWebSocket, 5000); // Reconnect after 5 seconds
            }};
        }}
        
        function loadWidgetData() {{
            dashboardConfig.widgets.forEach(widget => {{
                loadWidget(widget.id);
            }});
        }}
        
        async function loadWidget(widgetId) {{
            try {{
                const widget = dashboardConfig.widgets.find(w => w.id === widgetId);
                if (!widget) return;
                
                const response = await fetch(`/api/dashboard/widget-data/${{widgetId}}`, {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{
                        widget_config: widget,
                        user_data: {json.dumps(user_data or {})}
                    }})
                }});
                
                const data = await response.json();
                
                if (data.success) {{
                    renderWidget(widgetId, data.widget_data);
                }} else {{
                    showError(widgetId, data.error || 'Failed to load widget');
                }}
            }} catch (error) {{
                console.error('Error loading widget:', widgetId, error);
                showError(widgetId, 'Network error');
            }}
        }}
        
        function renderWidget(widgetId, data) {{
            const widget = dashboardConfig.widgets.find(w => w.id === widgetId);
            if (!widget) return;
            
            const contentElement = document.getElementById(`content-${{widgetId}}`);
            
            switch (widget.type) {{
                case 'chart':
                    renderChart(widgetId, data);
                    break;
                case 'interactive':
                    renderInteractive(widgetId, data);
                    break;
                case 'metric':
                    renderMetrics(widgetId, data);
                    break;
                default:
                    contentElement.innerHTML = '<p>Widget type not supported</p>';
            }}
        }}
        
        function renderChart(widgetId, data) {{
            const chartElement = document.getElementById(`chart-${{widgetId}}`);
            if (!chartElement) return;
            
            if (typeof Plotly !== 'undefined' && data.plotly_data) {{
                Plotly.newPlot(chartElement, data.plotly_data.data, data.plotly_data.layout, {{
                    responsive: true,
                    displayModeBar: true
                }});
            }}
        }}
        
        function renderInteractive(widgetId, data) {{
            const widget = dashboardConfig.widgets.find(w => w.id === widgetId);
            const componentType = widget.content.component_type;
            
            switch (componentType) {{
                case 'network_graph':
                    renderNetworkGraph(widgetId, data);
                    break;
                case '3d_knowledge_graph':
                    render3DGraph(widgetId, data);
                    break;
                case 'recommendation_cards':
                    renderRecommendations(widgetId, data);
                    break;
                default:
                    console.log('Interactive component not implemented:', componentType);
            }}
        }}
        
        function renderNetworkGraph(widgetId, data) {{
            // Implementation for network graph using D3.js
            const container = document.getElementById(`network-${{widgetId}}`);
            if (!container || typeof d3 === 'undefined') return;
            
            // Clear previous content
            d3.select(container).selectAll("*").remove();
            
            const width = container.clientWidth;
            const height = container.clientHeight || 300;
            
            const svg = d3.select(container)
                .append("svg")
                .attr("width", width)
                .attr("height", height);
            
            // Add network graph implementation here
            console.log('Rendering network graph with data:', data);
        }}
        
        function render3DGraph(widgetId, data) {{
            // Implementation for 3D graph using Three.js
            const container = document.getElementById(`3d-graph-${{widgetId}}`);
            if (!container || typeof THREE === 'undefined') return;
            
            console.log('Rendering 3D graph with data:', data);
        }}
        
        function renderRecommendations(widgetId, data) {{
            const container = document.getElementById(`recommendations-${{widgetId}}`);
            if (!container) return;
            
            const recommendations = data.recommendations || [];
            let html = '<div class="recommendations-grid">';
            
            recommendations.forEach(rec => {{
                html += `
                    <div class="recommendation-card" onclick="startLearning('${{rec.concept}}')">
                        <h4>${{rec.concept}}</h4>
                        <p>Difficulty: ${{rec.difficulty_level}}</p>
                        <p>Duration: ${{rec.estimated_duration}} min</p>
                        <div class="score-bar">
                            <div class="score-fill" style="width: ${{rec.score * 100}}%"></div>
                        </div>
                    </div>
                `;
            }});
            
            html += '</div>';
            container.innerHTML = html;
        }}
        
        function renderMetrics(widgetId, data) {{
            const contentElement = document.getElementById(`content-${{widgetId}}`);
            const metrics = data.metrics || [];
            
            let html = '';
            metrics.forEach(metric => {{
                html += `
                    <div class="metric-card">
                        <div class="metric-value">${{metric.value}}</div>
                        <div class="metric-label">${{metric.name}}</div>
                    </div>
                `;
            }});
            
            contentElement.innerHTML = html;
        }}
        
        function refreshWidget(widgetId) {{
            console.log('Refreshing widget:', widgetId);
            loadWidget(widgetId);
        }}
        
        function refreshAllWidgets() {{
            console.log('Refreshing all widgets');
            loadWidgetData();
        }}
        
        function handleRealTimeUpdate(data) {{
            if (data.widget_id && data.update_data) {{
                renderWidget(data.widget_id, data.update_data);
            }}
        }}
        
        function handleControl(controlType, widgetId, value) {{
            console.log('Control action:', controlType, widgetId, value);
            
            // Send control action to backend
            fetch('/api/dashboard/control-action', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json'
                }},
                body: JSON.stringify({{
                    widget_id: widgetId,
                    control_type: controlType,
                    value: value
                }})
            }});
        }}
        
        function startLearning(concept) {{
            console.log('Starting learning for concept:', concept);
            // Implement learning session start
        }}
        
        function expandWidget(widgetId) {{
            console.log('Expanding widget:', widgetId);
            // Implement widget expansion/modal
        }}
        
        function toggleFullscreen() {{
            if (!document.fullscreenElement) {{
                document.documentElement.requestFullscreen();
            }} else {{
                document.exitFullscreen();
            }}
        }}
        
        function openSettings() {{
            console.log('Opening dashboard settings');
            // Implement settings modal
        }}
        
        function showNotification(message, type = 'info') {{
            const notification = document.createElement('div');
            notification.className = `notification notification-${{type}}`;
            notification.textContent = message;
            
            document.body.appendChild(notification);
            
            setTimeout(() => {{
                notification.remove();
            }}, 3000);
        }}
        
        function showError(widgetId, error) {{
            const contentElement = document.getElementById(`content-${{widgetId}}`);
            contentElement.innerHTML = `<div class="error-message">Error: ${{error}}</div>`;
        }}
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', function() {{
            Object.values(refreshIntervals).forEach(interval => {{
                clearInterval(interval);
            }});
            
            if (websocket) {{
                websocket.close();
            }}
        }});
        """
    
    async def get_widget_data(
        self, 
        widget_id: str, 
        widget_config: Dict[str, Any],
        user_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Get data for a specific widget"""
        try:
            # This would integrate with the actual services
            # For now, return mock data based on widget type
            
            widget_type = widget_config.get("type")
            
            if widget_type == "chart":
                return await self._get_chart_data(widget_id, widget_config, user_data)
            elif widget_type == "interactive":
                return await self._get_interactive_data(widget_id, widget_config, user_data)
            elif widget_type == "metric":
                return await self._get_metric_data(widget_id, widget_config, user_data)
            else:
                return {"error": f"Unknown widget type: {widget_type}"}
        
        except Exception as e:
            logging.error(f"Error getting widget data for {widget_id}: {e}")
            return {"error": str(e)}
    
    async def _get_chart_data(
        self, 
        widget_id: str, 
        widget_config: Dict[str, Any],
        user_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Get chart data for visualization"""
        # Mock data - replace with actual service calls
        if "progress" in widget_id:
            return {
                "plotly_data": {
                    "data": [{
                        "type": "scatter",
                        "x": ["Mon", "Tue", "Wed", "Thu", "Fri"],
                        "y": [65, 72, 78, 85, 90],
                        "mode": "lines+markers",
                        "name": "Progress"
                    }],
                    "layout": {
                        "title": "Learning Progress",
                        "xaxis": {"title": "Day"},
                        "yaxis": {"title": "Score (%)"}
                    }
                }
            }
        
        return {"plotly_data": {"data": [], "layout": {}}}
    
    async def _get_interactive_data(
        self, 
        widget_id: str, 
        widget_config: Dict[str, Any],
        user_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Get interactive component data"""
        component_type = widget_config.get("content", {}).get("component_type")
        
        if component_type == "recommendation_cards":
            return {
                "recommendations": [
                    {
                        "concept": "Quadratic Equations",
                        "difficulty_level": 3,
                        "estimated_duration": 45,
                        "score": 0.85
                    },
                    {
                        "concept": "Derivatives",
                        "difficulty_level": 4,
                        "estimated_duration": 60,
                        "score": 0.78
                    }
                ]
            }
        
        return {"data": "Interactive data"}
    
    async def _get_metric_data(
        self, 
        widget_id: str, 
        widget_config: Dict[str, Any],
        user_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Get metric data"""
        return {
            "metrics": [
                {"name": "Accuracy", "value": "85%"},
                {"name": "Speed", "value": "75%"},
                {"name": "Engagement", "value": "92%"}
            ]
        }

# Global dashboard instance
interactive_dashboard = None

def get_interactive_dashboard() -> InteractiveDashboard:
    """Get or create the global Interactive Dashboard instance"""
    global interactive_dashboard
    if interactive_dashboard is None:
        interactive_dashboard = InteractiveDashboard()
    return interactive_dashboard