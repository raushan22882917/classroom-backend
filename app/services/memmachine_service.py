"""
MemVerge MemMachine Service for Persistent Long-term Memory
Provides intelligent memory management for AI agents with persistent storage
"""

import json
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict
import hashlib
import pickle
import numpy as np
from pathlib import Path

# MemVerge MemMachine imports (simulated for now - replace with actual SDK)
try:
    # from memverge.memmachine import MemMachine, MemoryPool, PersistentMemory
    # For now, we'll create a simulation layer
    pass
except ImportError:
    logging.warning("MemVerge MemMachine SDK not available, using simulation layer")

@dataclass
class MemoryEntry:
    """Represents a memory entry in the persistent storage"""
    id: str
    content: Any
    metadata: Dict[str, Any]
    timestamp: datetime
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    importance_score: float = 0.0
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.last_accessed is None:
            self.last_accessed = self.timestamp

@dataclass
class LearningContext:
    """Context for learning sessions"""
    user_id: str
    session_id: str
    subject: str
    topic: str
    difficulty_level: int
    learning_objectives: List[str]
    previous_knowledge: Dict[str, Any]
    current_progress: Dict[str, Any]

class MemMachineService:
    """
    MemVerge MemMachine Service for persistent AI agent memory
    Provides intelligent memory management with automatic persistence
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.memory_pools = {}
        self.persistent_storage = {}
        self.memory_index = {}
        self.access_patterns = {}
        
        # Initialize storage paths
        self.storage_path = Path(self.config.get('storage_path', './memmachine_data'))
        self.storage_path.mkdir(exist_ok=True)
        
        # Memory management settings
        self.max_memory_size = self.config.get('max_memory_size', 1024 * 1024 * 1024)  # 1GB
        self.retention_policy = self.config.get('retention_policy', 'importance_based')
        self.compression_enabled = self.config.get('compression', True)
        
        # Initialize memory pools
        self._initialize_memory_pools()
        
        # Load existing persistent memory
        self._load_persistent_memory()
        
        logging.info("MemMachine Service initialized with persistent memory")
    
    def _initialize_memory_pools(self):
        """Initialize different memory pools for different types of data"""
        self.memory_pools = {
            'learning_sessions': {},
            'user_profiles': {},
            'knowledge_graphs': {},
            'interaction_history': {},
            'ai_responses': {},
            'feedback_data': {},
            'performance_metrics': {},
            'adaptive_models': {}
        }
    
    def _load_persistent_memory(self):
        """Load persistent memory from storage"""
        try:
            for pool_name in self.memory_pools.keys():
                pool_file = self.storage_path / f"{pool_name}.pkl"
                if pool_file.exists():
                    with open(pool_file, 'rb') as f:
                        self.memory_pools[pool_name] = pickle.load(f)
                    logging.info(f"Loaded {len(self.memory_pools[pool_name])} entries from {pool_name}")
        except Exception as e:
            logging.error(f"Error loading persistent memory: {e}")
    
    def _save_persistent_memory(self, pool_name: str = None):
        """Save memory pools to persistent storage"""
        try:
            pools_to_save = [pool_name] if pool_name else self.memory_pools.keys()
            
            for pool in pools_to_save:
                pool_file = self.storage_path / f"{pool}.pkl"
                with open(pool_file, 'wb') as f:
                    pickle.dump(self.memory_pools[pool], f)
                logging.debug(f"Saved {len(self.memory_pools[pool])} entries to {pool}")
        except Exception as e:
            logging.error(f"Error saving persistent memory: {e}")
    
    def _generate_memory_id(self, content: Any, metadata: Dict[str, Any]) -> str:
        """Generate unique ID for memory entry"""
        content_str = json.dumps(content, sort_keys=True, default=str)
        metadata_str = json.dumps(metadata, sort_keys=True, default=str)
        combined = f"{content_str}_{metadata_str}_{datetime.now().isoformat()}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    async def store_memory(
        self, 
        pool_name: str, 
        content: Any, 
        metadata: Dict[str, Any] = None,
        importance_score: float = 0.5,
        tags: List[str] = None
    ) -> str:
        """Store a memory entry in the specified pool"""
        if metadata is None:
            metadata = {}
        
        memory_id = self._generate_memory_id(content, metadata)
        
        memory_entry = MemoryEntry(
            id=memory_id,
            content=content,
            metadata=metadata,
            timestamp=datetime.now(),
            importance_score=importance_score,
            tags=tags or []
        )
        
        # Store in memory pool
        if pool_name not in self.memory_pools:
            self.memory_pools[pool_name] = {}
        
        self.memory_pools[pool_name][memory_id] = memory_entry
        
        # Update index for fast retrieval
        self._update_memory_index(pool_name, memory_entry)
        
        # Save to persistent storage
        self._save_persistent_memory(pool_name)
        
        logging.info(f"Stored memory entry {memory_id} in pool {pool_name}")
        return memory_id
    
    def _update_memory_index(self, pool_name: str, memory_entry: MemoryEntry):
        """Update memory index for fast retrieval"""
        if pool_name not in self.memory_index:
            self.memory_index[pool_name] = {
                'by_tags': {},
                'by_timestamp': [],
                'by_importance': []
            }
        
        # Index by tags
        for tag in memory_entry.tags:
            if tag not in self.memory_index[pool_name]['by_tags']:
                self.memory_index[pool_name]['by_tags'][tag] = []
            self.memory_index[pool_name]['by_tags'][tag].append(memory_entry.id)
        
        # Index by timestamp and importance
        self.memory_index[pool_name]['by_timestamp'].append((memory_entry.timestamp, memory_entry.id))
        self.memory_index[pool_name]['by_importance'].append((memory_entry.importance_score, memory_entry.id))
        
        # Keep indexes sorted
        self.memory_index[pool_name]['by_timestamp'].sort(reverse=True)
        self.memory_index[pool_name]['by_importance'].sort(reverse=True)
    
    async def retrieve_memory(
        self, 
        pool_name: str, 
        memory_id: str = None,
        tags: List[str] = None,
        limit: int = 10,
        min_importance: float = 0.0
    ) -> List[MemoryEntry]:
        """Retrieve memory entries based on criteria"""
        if pool_name not in self.memory_pools:
            return []
        
        results = []
        
        if memory_id:
            # Retrieve specific memory
            if memory_id in self.memory_pools[pool_name]:
                entry = self.memory_pools[pool_name][memory_id]
                entry.access_count += 1
                entry.last_accessed = datetime.now()
                results.append(entry)
        else:
            # Retrieve based on criteria
            pool = self.memory_pools[pool_name]
            
            for entry in pool.values():
                # Check importance threshold
                if entry.importance_score < min_importance:
                    continue
                
                # Check tags if specified
                if tags and not any(tag in entry.tags for tag in tags):
                    continue
                
                # Update access info
                entry.access_count += 1
                entry.last_accessed = datetime.now()
                results.append(entry)
        
        # Sort by importance and recency
        results.sort(key=lambda x: (x.importance_score, x.last_accessed), reverse=True)
        
        # Save updated access info
        self._save_persistent_memory(pool_name)
        
        return results[:limit]
    
    async def store_learning_session(self, context: LearningContext, session_data: Dict[str, Any]) -> str:
        """Store a complete learning session with context"""
        memory_data = {
            'context': asdict(context),
            'session_data': session_data,
            'performance_metrics': session_data.get('performance_metrics', {}),
            'learning_outcomes': session_data.get('learning_outcomes', []),
            'interaction_patterns': session_data.get('interaction_patterns', {}),
            'ai_responses': session_data.get('ai_responses', []),
            'user_feedback': session_data.get('user_feedback', {})
        }
        
        metadata = {
            'user_id': context.user_id,
            'session_id': context.session_id,
            'subject': context.subject,
            'topic': context.topic,
            'difficulty_level': context.difficulty_level,
            'session_duration': session_data.get('duration', 0),
            'completion_rate': session_data.get('completion_rate', 0.0)
        }
        
        # Calculate importance score based on performance and engagement
        importance_score = self._calculate_session_importance(session_data)
        
        tags = [
            context.subject,
            context.topic,
            f"difficulty_{context.difficulty_level}",
            f"user_{context.user_id}"
        ]
        
        return await self.store_memory(
            'learning_sessions',
            memory_data,
            metadata,
            importance_score,
            tags
        )
    
    def _calculate_session_importance(self, session_data: Dict[str, Any]) -> float:
        """Calculate importance score for a learning session"""
        base_score = 0.5
        
        # Factor in completion rate
        completion_rate = session_data.get('completion_rate', 0.0)
        base_score += completion_rate * 0.3
        
        # Factor in performance metrics
        performance = session_data.get('performance_metrics', {})
        accuracy = performance.get('accuracy', 0.0)
        base_score += accuracy * 0.2
        
        # Factor in engagement metrics
        engagement = session_data.get('engagement_score', 0.0)
        base_score += engagement * 0.2
        
        # Factor in difficulty level
        difficulty = session_data.get('difficulty_level', 1)
        base_score += min(difficulty * 0.1, 0.3)
        
        return min(base_score, 1.0)
    
    async def get_user_learning_history(
        self, 
        user_id: str, 
        subject: str = None,
        days_back: int = 30,
        limit: int = 50
    ) -> List[MemoryEntry]:
        """Get user's learning history with optional filtering"""
        tags = [f"user_{user_id}"]
        if subject:
            tags.append(subject)
        
        # Get recent sessions
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        sessions = await self.retrieve_memory(
            'learning_sessions',
            tags=tags,
            limit=limit
        )
        
        # Filter by date
        recent_sessions = [
            session for session in sessions
            if session.timestamp >= cutoff_date
        ]
        
        return recent_sessions
    
    async def analyze_learning_patterns(self, user_id: str) -> Dict[str, Any]:
        """Analyze user's learning patterns from memory"""
        history = await self.get_user_learning_history(user_id, days_back=90)
        
        if not history:
            return {'error': 'No learning history found'}
        
        # Analyze patterns
        subjects = {}
        topics = {}
        performance_trends = []
        engagement_trends = []
        
        for session in history:
            session_data = session.content['session_data']
            context = session.content['context']
            
            # Subject analysis
            subject = context['subject']
            if subject not in subjects:
                subjects[subject] = {'count': 0, 'total_time': 0, 'avg_performance': 0}
            
            subjects[subject]['count'] += 1
            subjects[subject]['total_time'] += session_data.get('duration', 0)
            
            # Performance tracking
            performance = session_data.get('performance_metrics', {})
            if 'accuracy' in performance:
                performance_trends.append({
                    'timestamp': session.timestamp,
                    'accuracy': performance['accuracy'],
                    'subject': subject
                })
        
        # Calculate insights
        insights = {
            'total_sessions': len(history),
            'subjects_studied': len(subjects),
            'subject_breakdown': subjects,
            'performance_trends': performance_trends[-20:],  # Last 20 sessions
            'learning_velocity': self._calculate_learning_velocity(history),
            'knowledge_retention': self._estimate_knowledge_retention(history),
            'recommended_focus_areas': self._identify_focus_areas(history)
        }
        
        return insights
    
    def _calculate_learning_velocity(self, history: List[MemoryEntry]) -> float:
        """Calculate how quickly the user is learning"""
        if len(history) < 2:
            return 0.0
        
        recent_sessions = history[:10]  # Last 10 sessions
        total_progress = sum(
            session.content['session_data'].get('completion_rate', 0)
            for session in recent_sessions
        )
        
        return total_progress / len(recent_sessions)
    
    def _estimate_knowledge_retention(self, history: List[MemoryEntry]) -> Dict[str, float]:
        """Estimate knowledge retention by subject"""
        retention_by_subject = {}
        
        for session in history:
            context = session.content['context']
            subject = context['subject']
            
            if subject not in retention_by_subject:
                retention_by_subject[subject] = []
            
            # Simple retention model based on performance over time
            performance = session.content['session_data'].get('performance_metrics', {})
            accuracy = performance.get('accuracy', 0.0)
            days_ago = (datetime.now() - session.timestamp).days
            
            # Decay function for retention estimation
            retention_score = accuracy * np.exp(-days_ago / 30.0)  # 30-day half-life
            retention_by_subject[subject].append(retention_score)
        
        # Average retention by subject
        return {
            subject: np.mean(scores) if scores else 0.0
            for subject, scores in retention_by_subject.items()
        }
    
    def _identify_focus_areas(self, history: List[MemoryEntry]) -> List[Dict[str, Any]]:
        """Identify areas that need more focus"""
        focus_areas = []
        
        # Analyze performance by topic
        topic_performance = {}
        
        for session in history:
            context = session.content['context']
            topic = context['topic']
            
            if topic not in topic_performance:
                topic_performance[topic] = []
            
            performance = session.content['session_data'].get('performance_metrics', {})
            accuracy = performance.get('accuracy', 0.0)
            topic_performance[topic].append(accuracy)
        
        # Identify low-performing topics
        for topic, performances in topic_performance.items():
            avg_performance = np.mean(performances)
            if avg_performance < 0.7:  # Below 70% accuracy
                focus_areas.append({
                    'topic': topic,
                    'avg_performance': avg_performance,
                    'sessions_count': len(performances),
                    'priority': 'high' if avg_performance < 0.5 else 'medium'
                })
        
        # Sort by priority and performance
        focus_areas.sort(key=lambda x: x['avg_performance'])
        
        return focus_areas[:5]  # Top 5 focus areas
    
    async def cleanup_old_memories(self, days_to_keep: int = 365):
        """Clean up old memories based on retention policy"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cleaned_count = 0
        
        for pool_name, pool in self.memory_pools.items():
            to_remove = []
            
            for memory_id, entry in pool.items():
                # Keep important memories longer
                if entry.importance_score > 0.8:
                    continue
                
                # Keep frequently accessed memories
                if entry.access_count > 10:
                    continue
                
                # Remove old, low-importance memories
                if entry.timestamp < cutoff_date:
                    to_remove.append(memory_id)
            
            # Remove identified memories
            for memory_id in to_remove:
                del pool[memory_id]
                cleaned_count += 1
            
            # Save updated pool
            if to_remove:
                self._save_persistent_memory(pool_name)
        
        logging.info(f"Cleaned up {cleaned_count} old memory entries")
        return cleaned_count
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about memory usage"""
        stats = {
            'total_pools': len(self.memory_pools),
            'pools': {},
            'total_entries': 0,
            'storage_size_mb': 0
        }
        
        for pool_name, pool in self.memory_pools.items():
            pool_stats = {
                'entry_count': len(pool),
                'avg_importance': 0.0,
                'most_recent': None,
                'oldest': None
            }
            
            if pool:
                importances = [entry.importance_score for entry in pool.values()]
                pool_stats['avg_importance'] = np.mean(importances)
                
                timestamps = [entry.timestamp for entry in pool.values()]
                pool_stats['most_recent'] = max(timestamps).isoformat()
                pool_stats['oldest'] = min(timestamps).isoformat()
            
            stats['pools'][pool_name] = pool_stats
            stats['total_entries'] += pool_stats['entry_count']
        
        # Calculate storage size
        try:
            for pool_file in self.storage_path.glob("*.pkl"):
                stats['storage_size_mb'] += pool_file.stat().st_size / (1024 * 1024)
        except Exception as e:
            logging.error(f"Error calculating storage size: {e}")
        
        return stats

# Global service instance
memmachine_service = None

def get_memmachine_service() -> MemMachineService:
    """Get or create the global MemMachine service instance"""
    global memmachine_service
    if memmachine_service is None:
        memmachine_service = MemMachineService()
    return memmachine_service