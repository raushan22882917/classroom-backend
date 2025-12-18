"""
Neo4j Graph Database Service for Deep Connected Reasoning
Provides intelligent knowledge graph management and relationship analysis
"""

import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict
import numpy as np
from collections import defaultdict, deque

# Neo4j imports
try:
    from neo4j import GraphDatabase, basic_auth
    from neomodel import (
        StructuredNode, StringProperty, IntegerProperty, 
        FloatProperty, DateTimeProperty, ArrayProperty,
        RelationshipTo, RelationshipFrom, Relationship,
        config, db
    )
    NEO4J_AVAILABLE = True
except ImportError:
    logging.warning("Neo4j libraries not available, using simulation layer")
    NEO4J_AVAILABLE = False

@dataclass
class ConceptNode:
    """Represents a concept in the knowledge graph"""
    id: str
    name: str
    type: str  # 'subject', 'topic', 'concept', 'skill', 'question'
    properties: Dict[str, Any]
    difficulty_level: int = 1
    mastery_threshold: float = 0.8
    
@dataclass
class RelationshipEdge:
    """Represents a relationship between concepts"""
    source_id: str
    target_id: str
    relationship_type: str  # 'prerequisite', 'related', 'part_of', 'applies_to'
    strength: float = 1.0
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}

@dataclass
class LearningPath:
    """Represents an optimal learning path"""
    user_id: str
    target_concept: str
    path_nodes: List[str]
    estimated_duration: int  # in minutes
    difficulty_progression: List[int]
    confidence_score: float

class Neo4jService:
    """
    Neo4j Graph Database Service for educational knowledge graphs
    Provides deep connected reasoning and relationship analysis
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.driver = None
        self.knowledge_graph = {}
        self.relationships = {}
        self.user_progress = {}
        self.concept_embeddings = {}
        
        # Neo4j connection settings
        self.neo4j_uri = self.config.get('neo4j_uri', 'bolt://localhost:7687')
        self.neo4j_user = self.config.get('neo4j_user', 'neo4j')
        self.neo4j_password = self.config.get('neo4j_password', 'password')
        
        # Initialize connection
        self._initialize_connection()
        
        # Initialize knowledge graph structure
        self._initialize_knowledge_graph()
        
        logging.info("Neo4j Service initialized with knowledge graph")
    
    def _initialize_connection(self):
        """Initialize Neo4j database connection"""
        try:
            if NEO4J_AVAILABLE:
                self.driver = GraphDatabase.driver(
                    self.neo4j_uri,
                    auth=basic_auth(self.neo4j_user, self.neo4j_password)
                )
                # Test connection
                with self.driver.session() as session:
                    result = session.run("RETURN 1 as test")
                    result.single()
                logging.info("Connected to Neo4j database")
            else:
                logging.info("Using simulated Neo4j service")
                self._initialize_simulated_graph()
        except Exception as e:
            logging.error(f"Failed to connect to Neo4j: {e}")
            logging.info("Falling back to simulated graph database")
            self._initialize_simulated_graph()
    
    def _initialize_simulated_graph(self):
        """Initialize simulated graph for development/testing"""
        self.knowledge_graph = {
            'nodes': {},
            'relationships': {},
            'indexes': {
                'by_type': defaultdict(list),
                'by_subject': defaultdict(list),
                'by_difficulty': defaultdict(list)
            }
        }
    
    def _initialize_knowledge_graph(self):
        """Initialize the educational knowledge graph structure"""
        # Create base educational structure
        asyncio.create_task(self._create_base_curriculum())
    
    async def _create_base_curriculum(self):
        """Create base curriculum structure in the knowledge graph"""
        # Mathematics curriculum
        math_concepts = [
            {'name': 'Algebra', 'type': 'subject', 'difficulty': 1},
            {'name': 'Linear Equations', 'type': 'topic', 'difficulty': 2, 'parent': 'Algebra'},
            {'name': 'Quadratic Equations', 'type': 'topic', 'difficulty': 3, 'parent': 'Algebra'},
            {'name': 'Calculus', 'type': 'subject', 'difficulty': 4},
            {'name': 'Derivatives', 'type': 'topic', 'difficulty': 5, 'parent': 'Calculus'},
            {'name': 'Integrals', 'type': 'topic', 'difficulty': 6, 'parent': 'Calculus'},
        ]
        
        # Physics curriculum
        physics_concepts = [
            {'name': 'Physics', 'type': 'subject', 'difficulty': 1},
            {'name': 'Mechanics', 'type': 'topic', 'difficulty': 2, 'parent': 'Physics'},
            {'name': 'Kinematics', 'type': 'concept', 'difficulty': 3, 'parent': 'Mechanics'},
            {'name': 'Dynamics', 'type': 'concept', 'difficulty': 4, 'parent': 'Mechanics'},
            {'name': 'Thermodynamics', 'type': 'topic', 'difficulty': 5, 'parent': 'Physics'},
        ]
        
        # Chemistry curriculum
        chemistry_concepts = [
            {'name': 'Chemistry', 'type': 'subject', 'difficulty': 1},
            {'name': 'Organic Chemistry', 'type': 'topic', 'difficulty': 3, 'parent': 'Chemistry'},
            {'name': 'Inorganic Chemistry', 'type': 'topic', 'difficulty': 2, 'parent': 'Chemistry'},
            {'name': 'Physical Chemistry', 'type': 'topic', 'difficulty': 4, 'parent': 'Chemistry'},
        ]
        
        all_concepts = math_concepts + physics_concepts + chemistry_concepts
        
        # Create nodes
        for concept in all_concepts:
            await self.create_concept_node(
                concept['name'],
                concept['type'],
                {'subject': concept.get('parent', concept['name'])},
                concept['difficulty']
            )
        
        # Create relationships
        relationships = [
            ('Linear Equations', 'Quadratic Equations', 'prerequisite'),
            ('Algebra', 'Calculus', 'prerequisite'),
            ('Quadratic Equations', 'Derivatives', 'prerequisite'),
            ('Derivatives', 'Integrals', 'prerequisite'),
            ('Kinematics', 'Dynamics', 'prerequisite'),
            ('Algebra', 'Kinematics', 'applies_to'),
            ('Calculus', 'Physics', 'applies_to'),
        ]
        
        for source, target, rel_type in relationships:
            await self.create_relationship(source, target, rel_type)
    
    async def create_concept_node(
        self, 
        name: str, 
        concept_type: str, 
        properties: Dict[str, Any] = None,
        difficulty_level: int = 1
    ) -> str:
        """Create a new concept node in the knowledge graph"""
        if properties is None:
            properties = {}
        
        concept_id = f"{concept_type}_{name.lower().replace(' ', '_')}"
        
        concept = ConceptNode(
            id=concept_id,
            name=name,
            type=concept_type,
            properties=properties,
            difficulty_level=difficulty_level
        )
        
        if self.driver:
            # Use actual Neo4j
            query = """
            CREATE (c:Concept {
                id: $id,
                name: $name,
                type: $type,
                difficulty_level: $difficulty_level,
                created_at: datetime(),
                properties: $properties
            })
            RETURN c.id as id
            """
            
            with self.driver.session() as session:
                result = session.run(query, {
                    'id': concept_id,
                    'name': name,
                    'type': concept_type,
                    'difficulty_level': difficulty_level,
                    'properties': json.dumps(properties)
                })
        else:
            # Use simulated graph
            self.knowledge_graph['nodes'][concept_id] = concept
            self.knowledge_graph['indexes']['by_type'][concept_type].append(concept_id)
            self.knowledge_graph['indexes']['by_difficulty'][difficulty_level].append(concept_id)
            
            if 'subject' in properties:
                subject = properties['subject']
                self.knowledge_graph['indexes']['by_subject'][subject].append(concept_id)
        
        logging.info(f"Created concept node: {name} ({concept_id})")
        return concept_id
    
    async def create_relationship(
        self, 
        source_name: str, 
        target_name: str, 
        relationship_type: str,
        strength: float = 1.0,
        properties: Dict[str, Any] = None
    ) -> bool:
        """Create a relationship between two concepts"""
        # Find concept IDs
        source_id = await self._find_concept_id(source_name)
        target_id = await self._find_concept_id(target_name)
        
        if not source_id or not target_id:
            logging.warning(f"Could not find concepts for relationship: {source_name} -> {target_name}")
            return False
        
        if properties is None:
            properties = {}
        
        relationship = RelationshipEdge(
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
            strength=strength,
            properties=properties
        )
        
        if self.driver:
            # Use actual Neo4j
            query = """
            MATCH (source:Concept {id: $source_id})
            MATCH (target:Concept {id: $target_id})
            CREATE (source)-[r:RELATES {
                type: $rel_type,
                strength: $strength,
                created_at: datetime(),
                properties: $properties
            }]->(target)
            RETURN r
            """
            
            with self.driver.session() as session:
                result = session.run(query, {
                    'source_id': source_id,
                    'target_id': target_id,
                    'rel_type': relationship_type,
                    'strength': strength,
                    'properties': json.dumps(properties)
                })
        else:
            # Use simulated graph
            rel_id = f"{source_id}_{target_id}_{relationship_type}"
            self.knowledge_graph['relationships'][rel_id] = relationship
        
        logging.info(f"Created relationship: {source_name} -{relationship_type}-> {target_name}")
        return True
    
    async def _find_concept_id(self, concept_name: str) -> Optional[str]:
        """Find concept ID by name"""
        if self.driver:
            query = "MATCH (c:Concept {name: $name}) RETURN c.id as id"
            with self.driver.session() as session:
                result = session.run(query, {'name': concept_name})
                record = result.single()
                return record['id'] if record else None
        else:
            # Search in simulated graph
            for concept_id, concept in self.knowledge_graph['nodes'].items():
                if concept.name == concept_name:
                    return concept_id
            return None
    
    async def find_learning_path(
        self, 
        user_id: str, 
        target_concept: str,
        current_knowledge: List[str] = None
    ) -> LearningPath:
        """Find optimal learning path to target concept"""
        if current_knowledge is None:
            current_knowledge = []
        
        # Get user's current progress
        user_progress = await self.get_user_progress(user_id)
        mastered_concepts = [
            concept for concept, progress in user_progress.items()
            if progress.get('mastery_level', 0) >= 0.8
        ]
        
        # Find prerequisites for target concept
        prerequisites = await self._find_prerequisites(target_concept)
        
        # Calculate learning path
        path_nodes = []
        missing_prerequisites = []
        
        for prereq in prerequisites:
            if prereq not in mastered_concepts and prereq not in current_knowledge:
                missing_prerequisites.append(prereq)
        
        # Sort by difficulty and dependencies
        sorted_prerequisites = await self._sort_by_learning_order(missing_prerequisites)
        path_nodes = sorted_prerequisites + [target_concept]
        
        # Estimate duration and difficulty progression
        estimated_duration = await self._estimate_learning_duration(path_nodes, user_id)
        difficulty_progression = await self._get_difficulty_progression(path_nodes)
        
        # Calculate confidence score
        confidence_score = await self._calculate_path_confidence(path_nodes, user_id)
        
        learning_path = LearningPath(
            user_id=user_id,
            target_concept=target_concept,
            path_nodes=path_nodes,
            estimated_duration=estimated_duration,
            difficulty_progression=difficulty_progression,
            confidence_score=confidence_score
        )
        
        return learning_path
    
    async def _find_prerequisites(self, concept_name: str) -> List[str]:
        """Find all prerequisites for a concept using graph traversal"""
        concept_id = await self._find_concept_id(concept_name)
        if not concept_id:
            return []
        
        prerequisites = []
        
        if self.driver:
            # Use Neo4j graph traversal
            query = """
            MATCH (target:Concept {id: $concept_id})
            MATCH path = (prereq:Concept)-[:RELATES*1..5 {type: 'prerequisite'}]->(target)
            RETURN DISTINCT prereq.name as name, length(path) as distance
            ORDER BY distance
            """
            
            with self.driver.session() as session:
                result = session.run(query, {'concept_id': concept_id})
                prerequisites = [record['name'] for record in result]
        else:
            # Use simulated graph traversal
            prerequisites = self._simulate_prerequisite_search(concept_id)
        
        return prerequisites
    
    def _simulate_prerequisite_search(self, concept_id: str) -> List[str]:
        """Simulate prerequisite search in the knowledge graph"""
        prerequisites = []
        visited = set()
        queue = deque([concept_id])
        
        while queue:
            current_id = queue.popleft()
            if current_id in visited:
                continue
            visited.add(current_id)
            
            # Find incoming prerequisite relationships
            for rel_id, relationship in self.knowledge_graph['relationships'].items():
                if (relationship.target_id == current_id and 
                    relationship.relationship_type == 'prerequisite'):
                    
                    source_concept = self.knowledge_graph['nodes'][relationship.source_id]
                    prerequisites.append(source_concept.name)
                    queue.append(relationship.source_id)
        
        return prerequisites
    
    async def _sort_by_learning_order(self, concepts: List[str]) -> List[str]:
        """Sort concepts by optimal learning order"""
        if not concepts:
            return []
        
        # Create dependency graph
        concept_dependencies = {}
        concept_difficulties = {}
        
        for concept in concepts:
            concept_id = await self._find_concept_id(concept)
            if concept_id:
                if self.driver:
                    # Get from Neo4j
                    pass  # Implementation for Neo4j
                else:
                    # Get from simulated graph
                    if concept_id in self.knowledge_graph['nodes']:
                        node = self.knowledge_graph['nodes'][concept_id]
                        concept_difficulties[concept] = node.difficulty_level
                        concept_dependencies[concept] = []
                        
                        # Find dependencies within the concept list
                        for rel_id, rel in self.knowledge_graph['relationships'].items():
                            if (rel.target_id == concept_id and 
                                rel.relationship_type == 'prerequisite'):
                                source_node = self.knowledge_graph['nodes'][rel.source_id]
                                if source_node.name in concepts:
                                    concept_dependencies[concept].append(source_node.name)
        
        # Topological sort with difficulty consideration
        sorted_concepts = []
        remaining = set(concepts)
        
        while remaining:
            # Find concepts with no remaining dependencies
            ready = []
            for concept in remaining:
                deps = concept_dependencies.get(concept, [])
                if all(dep not in remaining for dep in deps):
                    ready.append(concept)
            
            if not ready:
                # Break circular dependencies by difficulty
                ready = [min(remaining, key=lambda c: concept_difficulties.get(c, 0))]
            
            # Sort ready concepts by difficulty
            ready.sort(key=lambda c: concept_difficulties.get(c, 0))
            
            # Add to sorted list
            for concept in ready:
                sorted_concepts.append(concept)
                remaining.remove(concept)
        
        return sorted_concepts
    
    async def _estimate_learning_duration(self, path_nodes: List[str], user_id: str) -> int:
        """Estimate total learning duration for the path"""
        base_duration_per_concept = 45  # minutes
        total_duration = 0
        
        # Get user's learning velocity
        user_stats = await self.get_user_learning_stats(user_id)
        learning_velocity = user_stats.get('learning_velocity', 1.0)
        
        for concept in path_nodes:
            concept_id = await self._find_concept_id(concept)
            if concept_id:
                if self.driver:
                    # Get from Neo4j
                    pass
                else:
                    # Get from simulated graph
                    if concept_id in self.knowledge_graph['nodes']:
                        node = self.knowledge_graph['nodes'][concept_id]
                        difficulty_multiplier = node.difficulty_level * 0.5
                        concept_duration = base_duration_per_concept * (1 + difficulty_multiplier)
                        
                        # Adjust for user's learning velocity
                        concept_duration = concept_duration / learning_velocity
                        
                        total_duration += concept_duration
        
        return int(total_duration)
    
    async def _get_difficulty_progression(self, path_nodes: List[str]) -> List[int]:
        """Get difficulty progression for the learning path"""
        difficulties = []
        
        for concept in path_nodes:
            concept_id = await self._find_concept_id(concept)
            if concept_id:
                if concept_id in self.knowledge_graph['nodes']:
                    node = self.knowledge_graph['nodes'][concept_id]
                    difficulties.append(node.difficulty_level)
                else:
                    difficulties.append(1)  # Default difficulty
        
        return difficulties
    
    async def _calculate_path_confidence(self, path_nodes: List[str], user_id: str) -> float:
        """Calculate confidence score for the learning path"""
        if not path_nodes:
            return 0.0
        
        user_stats = await self.get_user_learning_stats(user_id)
        base_confidence = 0.7
        
        # Factor in user's historical performance
        avg_performance = user_stats.get('average_performance', 0.5)
        confidence_adjustment = (avg_performance - 0.5) * 0.4
        
        # Factor in path complexity
        path_complexity = len(path_nodes) / 10.0  # Normalize by expected max path length
        complexity_penalty = min(path_complexity * 0.2, 0.3)
        
        # Factor in difficulty variance
        difficulties = await self._get_difficulty_progression(path_nodes)
        if difficulties:
            difficulty_variance = np.var(difficulties)
            variance_penalty = min(difficulty_variance * 0.1, 0.2)
        else:
            variance_penalty = 0
        
        final_confidence = base_confidence + confidence_adjustment - complexity_penalty - variance_penalty
        return max(0.1, min(1.0, final_confidence))
    
    async def get_user_progress(self, user_id: str) -> Dict[str, Dict[str, Any]]:
        """Get user's learning progress across all concepts"""
        if user_id not in self.user_progress:
            self.user_progress[user_id] = {}
        
        return self.user_progress[user_id]
    
    async def update_user_progress(
        self, 
        user_id: str, 
        concept_name: str, 
        performance_data: Dict[str, Any]
    ):
        """Update user's progress on a specific concept"""
        if user_id not in self.user_progress:
            self.user_progress[user_id] = {}
        
        if concept_name not in self.user_progress[user_id]:
            self.user_progress[user_id][concept_name] = {
                'mastery_level': 0.0,
                'attempts': 0,
                'total_time': 0,
                'last_accessed': None,
                'performance_history': []
            }
        
        progress = self.user_progress[user_id][concept_name]
        
        # Update progress metrics
        progress['attempts'] += 1
        progress['total_time'] += performance_data.get('duration', 0)
        progress['last_accessed'] = datetime.now()
        progress['performance_history'].append({
            'timestamp': datetime.now(),
            'accuracy': performance_data.get('accuracy', 0.0),
            'completion_rate': performance_data.get('completion_rate', 0.0),
            'engagement_score': performance_data.get('engagement_score', 0.0)
        })
        
        # Calculate new mastery level
        recent_performances = progress['performance_history'][-5:]  # Last 5 attempts
        if recent_performances:
            avg_accuracy = np.mean([p['accuracy'] for p in recent_performances])
            avg_completion = np.mean([p['completion_rate'] for p in recent_performances])
            
            # Weighted mastery calculation
            new_mastery = (avg_accuracy * 0.6 + avg_completion * 0.4)
            
            # Apply learning curve (gradual improvement)
            current_mastery = progress['mastery_level']
            progress['mastery_level'] = current_mastery * 0.7 + new_mastery * 0.3
        
        logging.info(f"Updated progress for {user_id} on {concept_name}: {progress['mastery_level']:.2f}")
    
    async def get_user_learning_stats(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive learning statistics for a user"""
        progress = await self.get_user_progress(user_id)
        
        if not progress:
            return {
                'total_concepts': 0,
                'mastered_concepts': 0,
                'average_performance': 0.0,
                'learning_velocity': 1.0,
                'total_study_time': 0,
                'streak_days': 0
            }
        
        # Calculate statistics
        total_concepts = len(progress)
        mastered_concepts = sum(1 for p in progress.values() if p['mastery_level'] >= 0.8)
        
        all_performances = []
        total_study_time = 0
        
        for concept_progress in progress.values():
            total_study_time += concept_progress['total_time']
            for perf in concept_progress['performance_history']:
                all_performances.append(perf['accuracy'])
        
        average_performance = np.mean(all_performances) if all_performances else 0.0
        
        # Calculate learning velocity (improvement rate)
        learning_velocity = 1.0
        if len(all_performances) >= 10:
            recent_perf = np.mean(all_performances[-10:])
            early_perf = np.mean(all_performances[:10])
            if early_perf > 0:
                learning_velocity = recent_perf / early_perf
        
        return {
            'total_concepts': total_concepts,
            'mastered_concepts': mastered_concepts,
            'mastery_rate': mastered_concepts / total_concepts if total_concepts > 0 else 0,
            'average_performance': average_performance,
            'learning_velocity': learning_velocity,
            'total_study_time': total_study_time,
            'concepts_in_progress': total_concepts - mastered_concepts
        }
    
    async def get_concept_relationships(self, concept_name: str) -> Dict[str, List[str]]:
        """Get all relationships for a concept"""
        concept_id = await self._find_concept_id(concept_name)
        if not concept_id:
            return {}
        
        relationships = {
            'prerequisites': [],
            'dependents': [],
            'related': [],
            'applications': []
        }
        
        if self.driver:
            # Use Neo4j queries
            pass
        else:
            # Use simulated graph
            for rel_id, rel in self.knowledge_graph['relationships'].items():
                if rel.source_id == concept_id:
                    target_node = self.knowledge_graph['nodes'][rel.target_id]
                    if rel.relationship_type == 'prerequisite':
                        relationships['dependents'].append(target_node.name)
                    elif rel.relationship_type == 'related':
                        relationships['related'].append(target_node.name)
                    elif rel.relationship_type == 'applies_to':
                        relationships['applications'].append(target_node.name)
                
                elif rel.target_id == concept_id:
                    source_node = self.knowledge_graph['nodes'][rel.source_id]
                    if rel.relationship_type == 'prerequisite':
                        relationships['prerequisites'].append(source_node.name)
                    elif rel.relationship_type == 'related':
                        relationships['related'].append(source_node.name)
        
        return relationships
    
    async def recommend_next_concepts(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Recommend next concepts for the user to learn"""
        user_progress = await self.get_user_progress(user_id)
        user_stats = await self.get_user_learning_stats(user_id)
        
        mastered_concepts = [
            concept for concept, progress in user_progress.items()
            if progress['mastery_level'] >= 0.8
        ]
        
        recommendations = []
        
        # Find concepts that have prerequisites met
        for concept_id, concept in self.knowledge_graph['nodes'].items():
            if concept.name in mastered_concepts:
                continue
            
            # Check if prerequisites are met
            prerequisites = await self._find_prerequisites(concept.name)
            prerequisites_met = all(prereq in mastered_concepts for prereq in prerequisites)
            
            if prerequisites_met:
                # Calculate recommendation score
                difficulty_match = abs(concept.difficulty_level - user_stats.get('average_difficulty', 3))
                difficulty_score = max(0, 1 - difficulty_match / 5)
                
                # Factor in user's performance trend
                performance_score = user_stats.get('average_performance', 0.5)
                
                # Factor in concept importance (number of dependents)
                dependents = await self._count_dependents(concept.name)
                importance_score = min(dependents / 10, 1.0)
                
                total_score = (difficulty_score * 0.4 + 
                             performance_score * 0.3 + 
                             importance_score * 0.3)
                
                recommendations.append({
                    'concept': concept.name,
                    'type': concept.type,
                    'difficulty_level': concept.difficulty_level,
                    'score': total_score,
                    'estimated_duration': await self._estimate_concept_duration(concept.name, user_id),
                    'prerequisites_count': len(prerequisites),
                    'dependents_count': dependents
                })
        
        # Sort by score and return top recommendations
        recommendations.sort(key=lambda x: x['score'], reverse=True)
        return recommendations[:limit]
    
    async def _count_dependents(self, concept_name: str) -> int:
        """Count how many concepts depend on this one"""
        concept_id = await self._find_concept_id(concept_name)
        if not concept_id:
            return 0
        
        count = 0
        for rel_id, rel in self.knowledge_graph['relationships'].items():
            if (rel.source_id == concept_id and 
                rel.relationship_type == 'prerequisite'):
                count += 1
        
        return count
    
    async def _estimate_concept_duration(self, concept_name: str, user_id: str) -> int:
        """Estimate learning duration for a single concept"""
        return await self._estimate_learning_duration([concept_name], user_id)
    
    async def analyze_knowledge_gaps(self, user_id: str) -> Dict[str, Any]:
        """Analyze knowledge gaps and suggest improvements"""
        user_progress = await self.get_user_progress(user_id)
        
        gaps = {
            'missing_prerequisites': [],
            'weak_areas': [],
            'disconnected_knowledge': [],
            'suggested_reviews': []
        }
        
        for concept, progress in user_progress.items():
            mastery_level = progress['mastery_level']
            
            # Identify weak areas
            if 0.3 <= mastery_level < 0.8:
                gaps['weak_areas'].append({
                    'concept': concept,
                    'mastery_level': mastery_level,
                    'attempts': progress['attempts'],
                    'last_accessed': progress['last_accessed']
                })
            
            # Check for missing prerequisites
            if mastery_level < 0.8:
                prerequisites = await self._find_prerequisites(concept)
                for prereq in prerequisites:
                    if prereq not in user_progress or user_progress[prereq]['mastery_level'] < 0.8:
                        gaps['missing_prerequisites'].append({
                            'concept': concept,
                            'missing_prerequisite': prereq,
                            'impact': 'high' if mastery_level < 0.5 else 'medium'
                        })
        
        # Suggest reviews for concepts not accessed recently
        cutoff_date = datetime.now() - timedelta(days=14)
        for concept, progress in user_progress.items():
            if (progress['mastery_level'] >= 0.8 and 
                progress['last_accessed'] and 
                progress['last_accessed'] < cutoff_date):
                gaps['suggested_reviews'].append({
                    'concept': concept,
                    'mastery_level': progress['mastery_level'],
                    'days_since_access': (datetime.now() - progress['last_accessed']).days
                })
        
        return gaps
    
    async def get_graph_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph"""
        stats = {
            'total_nodes': len(self.knowledge_graph['nodes']),
            'total_relationships': len(self.knowledge_graph['relationships']),
            'node_types': defaultdict(int),
            'relationship_types': defaultdict(int),
            'difficulty_distribution': defaultdict(int),
            'subjects': set()
        }
        
        # Analyze nodes
        for concept in self.knowledge_graph['nodes'].values():
            stats['node_types'][concept.type] += 1
            stats['difficulty_distribution'][concept.difficulty_level] += 1
            if 'subject' in concept.properties:
                stats['subjects'].add(concept.properties['subject'])
        
        # Analyze relationships
        for rel in self.knowledge_graph['relationships'].values():
            stats['relationship_types'][rel.relationship_type] += 1
        
        stats['subjects'] = list(stats['subjects'])
        
        return stats

# Global service instance
neo4j_service = None

def get_neo4j_service() -> Neo4jService:
    """Get or create the global Neo4j service instance"""
    global neo4j_service
    if neo4j_service is None:
        neo4j_service = Neo4jService()
    return neo4j_service