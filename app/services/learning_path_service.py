"""Learning path and assessment services for Magic Learn platform"""

import asyncio
import json
import time
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import google.generativeai as genai
import os
from dataclasses import dataclass, asdict

from app.models.magic_learn import (
    LearningPathRequest, LearningPathResponse,
    AssessmentRequest, AssessmentResponse,
    ProgressTrackingRequest, ProgressTrackingResponse,
    ContentGenerationRequest, ContentGenerationResponse,
    DifficultyLevel, AnalysisType
)

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


@dataclass
class LearningMilestone:
    """Data class for learning milestone"""
    milestone_id: str
    title: str
    description: str
    estimated_hours: int
    prerequisites: List[str]
    learning_objectives: List[str]
    activities: List[Dict[str, Any]]
    assessment_criteria: List[str]
    difficulty_level: DifficultyLevel


@dataclass
class UserProgress:
    """Data class for user progress tracking"""
    user_id: str
    subject_area: str
    current_level: DifficultyLevel
    completed_milestones: List[str]
    current_milestone: Optional[str]
    total_study_hours: float
    streak_days: int
    last_activity: datetime
    achievements: List[str]
    weak_areas: List[str]
    strong_areas: List[str]


class LearningPathService:
    """Service for generating personalized learning paths"""
    
    def __init__(self):
        self.learning_paths = {}
        self.user_progress = {}
        
    async def generate_learning_path(self, request: LearningPathRequest) -> LearningPathResponse:
        """Generate a personalized learning path for a user"""
        
        try:
            path_id = str(uuid.uuid4())
            
            # Analyze user requirements
            path_analysis = await self._analyze_learning_requirements(request)
            
            # Generate milestones
            milestones = await self._generate_milestones(request, path_analysis)
            
            # Create recommended activities
            activities = await self._generate_recommended_activities(request, milestones)
            
            # Estimate duration
            estimated_duration = await self._calculate_estimated_duration(
                milestones, request.time_available
            )
            
            # Create progress tracking configuration
            progress_config = await self._create_progress_tracking_config(request)
            
            # Store learning path
            learning_path = {
                "path_id": path_id,
                "user_id": request.user_id,
                "subject_area": request.subject_area,
                "milestones": [asdict(m) for m in milestones],
                "activities": activities,
                "created_at": datetime.utcnow().isoformat(),
                "estimated_duration": estimated_duration,
                "progress_config": progress_config
            }
            
            self.learning_paths[path_id] = learning_path
            
            return LearningPathResponse(
                success=True,
                path_id=path_id,
                milestones=[asdict(m) for m in milestones],
                estimated_duration=estimated_duration,
                recommended_activities=activities,
                progress_tracking=progress_config
            )
            
        except Exception as e:
            return LearningPathResponse(
                success=False,
                path_id="",
                milestones=[],
                estimated_duration=0,
                recommended_activities=[],
                progress_tracking={}
            )
    
    async def _analyze_learning_requirements(self, request: LearningPathRequest) -> Dict[str, Any]:
        """Analyze user learning requirements and preferences"""
        
        if not GEMINI_API_KEY:
            return self._default_learning_analysis(request)
        
        try:
            model = genai.GenerativeModel('gemini-2.5-flash-lite')
            
            prompt = f"""Analyze the following learning requirements and provide a structured learning path analysis:

Subject Area: {request.subject_area}
Current Level: {request.current_level.value}
Learning Goals: {', '.join(request.learning_goals)}
Time Available: {request.time_available} hours per week
Learning Style: {request.preferred_learning_style}

Please provide:
1. Key topics to cover in order of priority
2. Recommended learning sequence
3. Estimated difficulty progression
4. Suggested learning methods based on learning style
5. Potential challenges and how to address them

Format as a structured analysis for creating a personalized learning path."""

            response = model.generate_content([prompt])
            
            # Parse the response into structured data
            return await self._parse_learning_analysis(response.text, request)
            
        except Exception as e:
            print(f"Learning analysis error: {e}")
            return self._default_learning_analysis(request)
    
    def _default_learning_analysis(self, request: LearningPathRequest) -> Dict[str, Any]:
        """Default learning analysis when AI is not available"""
        
        subject_topics = {
            "mathematics": ["Algebra", "Geometry", "Calculus", "Statistics"],
            "science": ["Physics", "Chemistry", "Biology"],
            "programming": ["Basics", "Data Structures", "Algorithms", "Projects"],
            "language": ["Grammar", "Vocabulary", "Reading", "Writing", "Speaking"]
        }
        
        topics = subject_topics.get(request.subject_area.lower(), ["Fundamentals", "Intermediate", "Advanced"])
        
        return {
            "key_topics": topics,
            "learning_sequence": topics,
            "difficulty_progression": "gradual",
            "learning_methods": [request.preferred_learning_style or "visual"],
            "challenges": ["Time management", "Concept retention"],
            "recommendations": ["Regular practice", "Spaced repetition"]
        }
    
    async def _parse_learning_analysis(self, analysis_text: str, request: LearningPathRequest) -> Dict[str, Any]:
        """Parse AI-generated learning analysis into structured data"""
        
        # This is a simplified parser - in production, use more sophisticated NLP
        lines = analysis_text.split('\n')
        
        analysis = {
            "key_topics": [],
            "learning_sequence": [],
            "difficulty_progression": "gradual",
            "learning_methods": [request.preferred_learning_style or "visual"],
            "challenges": [],
            "recommendations": []
        }
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Identify sections
            if "topic" in line.lower():
                current_section = "key_topics"
            elif "sequence" in line.lower():
                current_section = "learning_sequence"
            elif "challenge" in line.lower():
                current_section = "challenges"
            elif "recommend" in line.lower():
                current_section = "recommendations"
            
            # Extract list items
            if line.startswith(('- ', '* ', '1.', '2.', '3.', '4.', '5.')):
                item = line[2:].strip() if line.startswith(('- ', '* ')) else line[3:].strip()
                if current_section and current_section in analysis:
                    analysis[current_section].append(item)
        
        return analysis
    
    async def _generate_milestones(self, request: LearningPathRequest, 
                                 analysis: Dict[str, Any]) -> List[LearningMilestone]:
        """Generate learning milestones based on analysis"""
        
        milestones = []
        topics = analysis.get("key_topics", ["Fundamentals", "Intermediate", "Advanced"])
        
        for i, topic in enumerate(topics):
            milestone_id = str(uuid.uuid4())
            
            # Determine difficulty progression
            if i == 0:
                difficulty = DifficultyLevel.BEGINNER
            elif i < len(topics) - 1:
                difficulty = DifficultyLevel.INTERMEDIATE
            else:
                difficulty = DifficultyLevel.ADVANCED
            
            # Generate activities for this milestone
            activities = await self._generate_milestone_activities(topic, difficulty, request.preferred_learning_style)
            
            milestone = LearningMilestone(
                milestone_id=milestone_id,
                title=f"{topic} Mastery",
                description=f"Master the fundamentals of {topic} in {request.subject_area}",
                estimated_hours=max(5, request.time_available // len(topics)),
                prerequisites=[milestones[-1].milestone_id] if milestones else [],
                learning_objectives=await self._generate_learning_objectives(topic, difficulty),
                activities=activities,
                assessment_criteria=await self._generate_assessment_criteria(topic, difficulty),
                difficulty_level=difficulty
            )
            
            milestones.append(milestone)
        
        return milestones
    
    async def _generate_milestone_activities(self, topic: str, difficulty: DifficultyLevel, 
                                          learning_style: str) -> List[Dict[str, Any]]:
        """Generate activities for a specific milestone"""
        
        activities = []
        
        # Base activities for all learning styles
        activities.append({
            "type": "reading",
            "title": f"Study {topic} Fundamentals",
            "description": f"Read and understand key concepts in {topic}",
            "estimated_minutes": 60,
            "resources": ["textbook", "online_articles"]
        })
        
        # Learning style specific activities
        if learning_style.lower() == "visual":
            activities.extend([
                {
                    "type": "visualization",
                    "title": f"Create {topic} Mind Map",
                    "description": f"Create visual representations of {topic} concepts",
                    "estimated_minutes": 45,
                    "resources": ["mind_mapping_tool", "diagrams"]
                },
                {
                    "type": "video",
                    "title": f"Watch {topic} Tutorials",
                    "description": f"Watch educational videos about {topic}",
                    "estimated_minutes": 30,
                    "resources": ["video_platform", "animations"]
                }
            ])
        elif learning_style.lower() == "kinesthetic":
            activities.extend([
                {
                    "type": "hands_on",
                    "title": f"Practice {topic} Exercises",
                    "description": f"Solve hands-on problems related to {topic}",
                    "estimated_minutes": 90,
                    "resources": ["practice_problems", "interactive_tools"]
                },
                {
                    "type": "experiment",
                    "title": f"{topic} Lab Activity",
                    "description": f"Conduct experiments or simulations for {topic}",
                    "estimated_minutes": 60,
                    "resources": ["lab_materials", "simulation_software"]
                }
            ])
        else:  # auditory or default
            activities.extend([
                {
                    "type": "discussion",
                    "title": f"Discuss {topic} Concepts",
                    "description": f"Participate in discussions about {topic}",
                    "estimated_minutes": 45,
                    "resources": ["discussion_forum", "study_group"]
                },
                {
                    "type": "audio",
                    "title": f"Listen to {topic} Lectures",
                    "description": f"Listen to audio lectures about {topic}",
                    "estimated_minutes": 60,
                    "resources": ["audio_lectures", "podcasts"]
                }
            ])
        
        # Assessment activity
        activities.append({
            "type": "assessment",
            "title": f"{topic} Knowledge Check",
            "description": f"Test your understanding of {topic}",
            "estimated_minutes": 30,
            "resources": ["quiz_platform", "self_assessment"]
        })
        
        return activities
    
    async def _generate_learning_objectives(self, topic: str, difficulty: DifficultyLevel) -> List[str]:
        """Generate learning objectives for a topic"""
        
        base_objectives = [
            f"Understand the fundamental concepts of {topic}",
            f"Apply {topic} principles to solve problems",
            f"Explain {topic} concepts clearly to others"
        ]
        
        if difficulty == DifficultyLevel.INTERMEDIATE:
            base_objectives.extend([
                f"Analyze complex {topic} scenarios",
                f"Compare different approaches in {topic}"
            ])
        elif difficulty == DifficultyLevel.ADVANCED:
            base_objectives.extend([
                f"Synthesize {topic} knowledge with other domains",
                f"Evaluate and critique {topic} methodologies",
                f"Create original solutions using {topic} principles"
            ])
        
        return base_objectives
    
    async def _generate_assessment_criteria(self, topic: str, difficulty: DifficultyLevel) -> List[str]:
        """Generate assessment criteria for a topic"""
        
        criteria = [
            f"Demonstrates understanding of {topic} concepts",
            f"Can solve {topic} problems accurately",
            f"Shows clear reasoning in {topic} applications"
        ]
        
        if difficulty in [DifficultyLevel.INTERMEDIATE, DifficultyLevel.ADVANCED]:
            criteria.extend([
                f"Connects {topic} to real-world applications",
                f"Shows creativity in problem-solving approaches"
            ])
        
        if difficulty == DifficultyLevel.ADVANCED:
            criteria.extend([
                f"Demonstrates mastery through teaching others",
                f"Can extend {topic} concepts to new domains"
            ])
        
        return criteria
    
    async def _generate_recommended_activities(self, request: LearningPathRequest, 
                                            milestones: List[LearningMilestone]) -> List[Dict[str, Any]]:
        """Generate overall recommended activities"""
        
        activities = []
        
        # Daily activities
        activities.append({
            "type": "daily",
            "title": "Daily Review",
            "description": "Spend 15 minutes reviewing previous concepts",
            "frequency": "daily",
            "duration_minutes": 15
        })
        
        # Weekly activities
        activities.append({
            "type": "weekly",
            "title": "Weekly Practice Session",
            "description": "Dedicated practice time for current milestone",
            "frequency": "weekly",
            "duration_minutes": request.time_available * 60 // 7  # Convert hours to minutes per day
        })
        
        # Monthly activities
        activities.append({
            "type": "monthly",
            "title": "Progress Assessment",
            "description": "Comprehensive review and assessment of progress",
            "frequency": "monthly",
            "duration_minutes": 120
        })
        
        return activities
    
    async def _calculate_estimated_duration(self, milestones: List[LearningMilestone], 
                                          time_available: int) -> int:
        """Calculate estimated duration in days"""
        
        total_hours = sum(milestone.estimated_hours for milestone in milestones)
        hours_per_week = time_available
        
        if hours_per_week > 0:
            weeks_needed = total_hours / hours_per_week
            return int(weeks_needed * 7)  # Convert to days
        
        return 90  # Default 3 months
    
    async def _create_progress_tracking_config(self, request: LearningPathRequest) -> Dict[str, Any]:
        """Create progress tracking configuration"""
        
        return {
            "tracking_frequency": "daily",
            "metrics": [
                "study_time",
                "concepts_mastered",
                "problems_solved",
                "streak_days"
            ],
            "milestones_tracking": True,
            "adaptive_difficulty": True,
            "reminder_settings": {
                "daily_reminder": True,
                "weekly_summary": True,
                "milestone_celebration": True
            },
            "analytics": {
                "learning_velocity": True,
                "concept_retention": True,
                "difficulty_progression": True
            }
        }
    
    async def get_learning_path(self, path_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a learning path by ID"""
        return self.learning_paths.get(path_id)
    
    async def update_learning_path(self, path_id: str, updates: Dict[str, Any]) -> bool:
        """Update a learning path"""
        if path_id in self.learning_paths:
            self.learning_paths[path_id].update(updates)
            return True
        return False


class ProgressTrackingService:
    """Service for tracking user learning progress"""
    
    def __init__(self):
        self.user_progress = {}
        self.activity_logs = {}
    
    async def track_progress(self, request: ProgressTrackingRequest) -> ProgressTrackingResponse:
        """Track user learning progress"""
        
        try:
            # Get or create user progress
            progress = await self._get_or_create_progress(request.user_id)
            
            # Update progress based on activity
            await self._update_progress(progress, request)
            
            # Calculate current metrics
            metrics = await self._calculate_progress_metrics(progress)
            
            # Generate recommendations
            recommendations = await self._generate_recommendations(progress, request)
            
            # Update streak
            streak_count = await self._update_streak(progress, request.timestamp)
            
            # Check for achievements
            achievements = await self._check_achievements(progress, request)
            
            return ProgressTrackingResponse(
                success=True,
                user_id=request.user_id,
                current_level=progress.current_level.value,
                progress_percentage=metrics["progress_percentage"],
                achievements=achievements,
                next_recommendations=recommendations,
                streak_count=streak_count
            )
            
        except Exception as e:
            return ProgressTrackingResponse(
                success=False,
                user_id=request.user_id,
                current_level="unknown",
                progress_percentage=0.0,
                achievements=[],
                next_recommendations=[],
                streak_count=0
            )
    
    async def _get_or_create_progress(self, user_id: str) -> UserProgress:
        """Get existing progress or create new one"""
        
        if user_id not in self.user_progress:
            self.user_progress[user_id] = UserProgress(
                user_id=user_id,
                subject_area="general",
                current_level=DifficultyLevel.BEGINNER,
                completed_milestones=[],
                current_milestone=None,
                total_study_hours=0.0,
                streak_days=0,
                last_activity=datetime.utcnow(),
                achievements=[],
                weak_areas=[],
                strong_areas=[]
            )
        
        return self.user_progress[user_id]
    
    async def _update_progress(self, progress: UserProgress, request: ProgressTrackingRequest):
        """Update user progress based on activity"""
        
        activity_data = request.activity_data
        
        # Update study time
        if "study_time_minutes" in activity_data:
            progress.total_study_hours += activity_data["study_time_minutes"] / 60
        
        # Update completed milestones
        if "milestone_completed" in activity_data:
            milestone_id = activity_data["milestone_completed"]
            if milestone_id not in progress.completed_milestones:
                progress.completed_milestones.append(milestone_id)
        
        # Update current milestone
        if "current_milestone" in activity_data:
            progress.current_milestone = activity_data["current_milestone"]
        
        # Update subject area
        if "subject_area" in activity_data:
            progress.subject_area = activity_data["subject_area"]
        
        # Update performance areas
        if "performance_data" in activity_data:
            perf_data = activity_data["performance_data"]
            if "weak_areas" in perf_data:
                progress.weak_areas = perf_data["weak_areas"]
            if "strong_areas" in perf_data:
                progress.strong_areas = perf_data["strong_areas"]
        
        # Update last activity
        progress.last_activity = request.timestamp
        
        # Store updated progress
        self.user_progress[request.user_id] = progress
    
    async def _calculate_progress_metrics(self, progress: UserProgress) -> Dict[str, Any]:
        """Calculate progress metrics"""
        
        # Simple progress calculation based on completed milestones
        # In production, this would be more sophisticated
        total_milestones = 10  # Assume 10 milestones per subject
        completed_count = len(progress.completed_milestones)
        progress_percentage = (completed_count / total_milestones) * 100
        
        return {
            "progress_percentage": min(progress_percentage, 100.0),
            "completed_milestones": completed_count,
            "total_study_hours": progress.total_study_hours,
            "current_streak": progress.streak_days
        }
    
    async def _generate_recommendations(self, progress: UserProgress, 
                                      request: ProgressTrackingRequest) -> List[str]:
        """Generate next step recommendations"""
        
        recommendations = []
        
        # Based on weak areas
        if progress.weak_areas:
            recommendations.append(f"Focus on improving: {', '.join(progress.weak_areas[:2])}")
        
        # Based on study time
        if progress.total_study_hours < 5:
            recommendations.append("Try to maintain consistent daily study sessions")
        
        # Based on streak
        if progress.streak_days == 0:
            recommendations.append("Start building a daily learning streak")
        elif progress.streak_days < 7:
            recommendations.append("Keep up your learning streak - you're doing great!")
        
        # Based on current milestone
        if progress.current_milestone:
            recommendations.append("Continue working on your current milestone")
        else:
            recommendations.append("Choose your next learning milestone")
        
        # Default recommendations
        if not recommendations:
            recommendations = [
                "Practice regularly to reinforce learning",
                "Try explaining concepts to someone else",
                "Take breaks to avoid burnout"
            ]
        
        return recommendations[:3]  # Limit to 3 recommendations
    
    async def _update_streak(self, progress: UserProgress, activity_timestamp: datetime) -> int:
        """Update and return current streak count"""
        
        last_activity_date = progress.last_activity.date()
        current_date = activity_timestamp.date()
        
        # Check if activity is on consecutive day
        if (current_date - last_activity_date).days == 1:
            progress.streak_days += 1
        elif (current_date - last_activity_date).days > 1:
            progress.streak_days = 1  # Reset streak
        # If same day, keep current streak
        
        return progress.streak_days
    
    async def _check_achievements(self, progress: UserProgress, 
                                request: ProgressTrackingRequest) -> List[str]:
        """Check for new achievements"""
        
        new_achievements = []
        
        # Streak achievements
        if progress.streak_days == 7 and "7_day_streak" not in progress.achievements:
            new_achievements.append("7 Day Learning Streak")
            progress.achievements.append("7_day_streak")
        elif progress.streak_days == 30 and "30_day_streak" not in progress.achievements:
            new_achievements.append("30 Day Learning Streak")
            progress.achievements.append("30_day_streak")
        
        # Study time achievements
        if progress.total_study_hours >= 10 and "10_hours" not in progress.achievements:
            new_achievements.append("10 Hours of Learning")
            progress.achievements.append("10_hours")
        elif progress.total_study_hours >= 50 and "50_hours" not in progress.achievements:
            new_achievements.append("50 Hours of Learning")
            progress.achievements.append("50_hours")
        
        # Milestone achievements
        milestone_count = len(progress.completed_milestones)
        if milestone_count >= 5 and "5_milestones" not in progress.achievements:
            new_achievements.append("5 Milestones Completed")
            progress.achievements.append("5_milestones")
        
        return new_achievements
    
    async def get_user_progress(self, user_id: str) -> Optional[UserProgress]:
        """Get user progress data"""
        return self.user_progress.get(user_id)
    
    async def get_progress_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get detailed progress analytics"""
        
        progress = await self._get_or_create_progress(user_id)
        
        # Calculate analytics
        analytics = {
            "total_study_time": progress.total_study_hours,
            "average_daily_time": progress.total_study_hours / max(1, progress.streak_days),
            "completion_rate": len(progress.completed_milestones) / 10 * 100,  # Assume 10 total milestones
            "learning_velocity": len(progress.completed_milestones) / max(1, progress.total_study_hours),
            "strong_areas": progress.strong_areas,
            "improvement_areas": progress.weak_areas,
            "achievement_count": len(progress.achievements),
            "current_streak": progress.streak_days,
            "last_activity": progress.last_activity.isoformat()
        }
        
        return analytics


# Service instances
learning_path_service = LearningPathService()
progress_tracking_service = ProgressTrackingService()