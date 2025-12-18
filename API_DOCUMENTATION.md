# 🚀 Interactive Learning Platform - API Documentation

## Overview

The Interactive Learning Platform provides a comprehensive set of APIs powered by MemVerge MemMachine for persistent memory and Neo4j Graph Database for connected reasoning. This documentation covers all available endpoints and their usage.

## Base URL
```
http://localhost:8000/api
```

## Authentication
Currently, the API uses simple user identification. In production, implement proper authentication mechanisms.

---

## 🧠 Memory Intelligence APIs

### Store Learning Session
Store a complete learning session with context in persistent memory.

**Endpoint:** `POST /memory/store-session`

**Parameters:**
- `user_id` (query, required): User identifier
- `session_data` (body, required): Complete session data

**Request Body:**
```json
{
  "session_id": "session_20241218_143000",
  "subject": "mathematics",
  "topic": "quadratic_equations",
  "difficulty_level": 3,
  "learning_objectives": ["solve quadratic equations", "understand discriminant"],
  "previous_knowledge": {"linear_equations": 0.9},
  "current_progress": {"completion_rate": 0.85},
  "performance_metrics": {
    "accuracy": 0.87,
    "engagement_score": 0.92,
    "time_spent": 2700
  },
  "duration": 45,
  "learning_outcomes": ["mastered factoring", "improved problem solving"]
}
```

**Response:**
```json
{
  "success": true,
  "memory_id": "mem_abc123def456",
  "message": "Learning session stored successfully in persistent memory"
}
```

### Get Learning History
Retrieve user's learning history from persistent memory.

**Endpoint:** `GET /memory/learning-history/{user_id}`

**Parameters:**
- `user_id` (path, required): User identifier
- `subject` (query, optional): Filter by subject
- `days_back` (query, optional): Days to look back (default: 30)
- `limit` (query, optional): Maximum sessions (default: 50)

**Response:**
```json
{
  "success": true,
  "user_id": "student_001",
  "total_sessions": 15,
  "history": [
    {
      "memory_id": "mem_abc123",
      "timestamp": "2024-12-18T14:30:00",
      "subject": "mathematics",
      "topic": "quadratic_equations",
      "difficulty_level": 3,
      "performance_metrics": {
        "accuracy": 0.87,
        "engagement_score": 0.92
      },
      "duration": 45,
      "completion_rate": 0.85,
      "importance_score": 0.78,
      "access_count": 3
    }
  ]
}
```

### Analyze Learning Patterns
Get AI-powered analysis of user's learning patterns.

**Endpoint:** `GET /memory/learning-patterns/{user_id}`

**Response:**
```json
{
  "success": true,
  "user_id": "student_001",
  "analysis": {
    "total_sessions": 127,
    "subjects_studied": 3,
    "subject_breakdown": {
      "mathematics": {
        "count": 45,
        "total_time": 2250,
        "avg_performance": 0.84
      }
    },
    "performance_trends": [
      {
        "timestamp": "2024-12-18T14:30:00",
        "accuracy": 0.87,
        "subject": "mathematics"
      }
    ],
    "learning_velocity": 1.3,
    "knowledge_retention": {
      "mathematics": 0.82,
      "physics": 0.75
    },
    "recommended_focus_areas": [
      {
        "topic": "organic_chemistry",
        "avg_performance": 0.45,
        "sessions_count": 8,
        "priority": "high"
      }
    ]
  },
  "generated_at": "2024-12-18T15:00:00"
}
```

### Memory Statistics
Get comprehensive memory usage statistics.

**Endpoint:** `GET /memory/stats`

**Response:**
```json
{
  "success": true,
  "statistics": {
    "total_pools": 8,
    "total_entries": 1247,
    "storage_size_mb": 156.7,
    "pools": {
      "learning_sessions": {
        "entry_count": 127,
        "avg_importance": 0.73,
        "most_recent": "2024-12-18T14:30:00",
        "oldest": "2024-11-01T09:15:00"
      }
    }
  },
  "generated_at": "2024-12-18T15:00:00"
}
```

---

## 🕸️ Knowledge Graph APIs

### Create Concept
Create a new concept node in the knowledge graph.

**Endpoint:** `POST /knowledge-graph/create-concept`

**Parameters:**
- `name` (query, required): Concept name
- `concept_type` (query, required): Type (subject, topic, concept, skill)
- `difficulty_level` (query, optional): Difficulty 1-5 (default: 1)
- `properties` (body, optional): Additional properties

**Request Body:**
```json
{
  "subject": "mathematics",
  "description": "Equations with degree 2",
  "prerequisites": ["linear_equations"],
  "learning_resources": ["textbook_ch5", "video_series_2"]
}
```

**Response:**
```json
{
  "success": true,
  "concept_id": "concept_quadratic_equations",
  "message": "Concept 'Quadratic Equations' created successfully"
}
```

### Create Relationship
Create a relationship between two concepts.

**Endpoint:** `POST /knowledge-graph/create-relationship`

**Parameters:**
- `source_concept` (query, required): Source concept name
- `target_concept` (query, required): Target concept name
- `relationship_type` (query, required): Type (prerequisite, related, applies_to)
- `strength` (query, optional): Relationship strength (default: 1.0)
- `properties` (body, optional): Additional properties

**Response:**
```json
{
  "success": true,
  "message": "Relationship created: Linear Equations -prerequisite-> Quadratic Equations"
}
```

### Find Learning Path
Find optimal learning path to target concept.

**Endpoint:** `GET /knowledge-graph/learning-path/{user_id}`

**Parameters:**
- `user_id` (path, required): User identifier
- `target_concept` (query, required): Target concept to learn
- `current_knowledge` (query, optional): Currently known concepts

**Response:**
```json
{
  "success": true,
  "learning_path": {
    "user_id": "student_001",
    "target_concept": "Derivatives",
    "path_nodes": [
      "Linear Equations",
      "Quadratic Equations", 
      "Functions",
      "Limits",
      "Derivatives"
    ],
    "estimated_duration": 180,
    "difficulty_progression": [2, 3, 3, 4, 5],
    "confidence_score": 0.78
  }
}
```

### Get Recommendations
Get personalized learning recommendations.

**Endpoint:** `GET /knowledge-graph/recommendations/{user_id}`

**Parameters:**
- `user_id` (path, required): User identifier
- `limit` (query, optional): Number of recommendations (default: 5)

**Response:**
```json
{
  "success": true,
  "user_id": "student_001",
  "recommendations": [
    {
      "concept": "Quadratic Equations",
      "type": "topic",
      "difficulty_level": 3,
      "score": 0.85,
      "estimated_duration": 45,
      "prerequisites_count": 1,
      "dependents_count": 3
    }
  ]
}
```

### Update Progress
Update user's progress on a specific concept.

**Endpoint:** `POST /knowledge-graph/update-progress`

**Parameters:**
- `user_id` (query, required): User identifier
- `concept_name` (query, required): Concept name

**Request Body:**
```json
{
  "accuracy": 0.87,
  "completion_rate": 0.92,
  "engagement_score": 0.89,
  "duration": 2700
}
```

**Response:**
```json
{
  "success": true,
  "message": "Progress updated for student_001 on Quadratic Equations"
}
```

### Get User Statistics
Get comprehensive learning statistics.

**Endpoint:** `GET /knowledge-graph/user-stats/{user_id}`

**Response:**
```json
{
  "success": true,
  "user_id": "student_001",
  "statistics": {
    "total_concepts": 15,
    "mastered_concepts": 8,
    "mastery_rate": 0.53,
    "average_performance": 0.84,
    "learning_velocity": 1.3,
    "total_study_time": 2520,
    "concepts_in_progress": 7
  }
}
```

### Analyze Knowledge Gaps
Identify knowledge gaps and improvement areas.

**Endpoint:** `GET /knowledge-graph/knowledge-gaps/{user_id}`

**Response:**
```json
{
  "success": true,
  "user_id": "student_001",
  "knowledge_gaps": {
    "missing_prerequisites": [
      {
        "concept": "Derivatives",
        "missing_prerequisite": "Limits",
        "impact": "high"
      }
    ],
    "weak_areas": [
      {
        "concept": "Quadratic Equations",
        "mastery_level": 0.65,
        "attempts": 8,
        "last_accessed": "2024-12-17T10:30:00"
      }
    ],
    "suggested_reviews": [
      {
        "concept": "Linear Equations",
        "mastery_level": 0.92,
        "days_since_access": 21
      }
    ]
  }
}
```

---

## 🎮 Interactive Learning APIs

### Create Interactive Session
Create a new interactive learning session.

**Endpoint:** `POST /interactive/create-session`

**Parameters:**
- `user_id` (query, required): User identifier

**Request Body:**
```json
{
  "components": [
    "algebra_visualizer",
    "adaptive_quiz",
    "concept_mapper"
  ],
  "preferences": {
    "difficulty_preference": 3,
    "learning_style": "visual",
    "pace_preference": "medium"
  }
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "session_student_001_20241218_143000",
  "message": "Interactive learning session created successfully"
}
```

### Process Interaction
Process user interaction and provide real-time feedback.

**Endpoint:** `POST /interactive/process-interaction`

**Parameters:**
- `session_id` (query, required): Session identifier

**Request Body:**
```json
{
  "type": "answer_submission",
  "data": {
    "question_id": "q_001",
    "answer": "2x",
    "correct": true,
    "time_taken": 15
  },
  "response_time": 15
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "feedback": {
      "type": "positive",
      "message": "Excellent work! You got it right.",
      "encouragement": "Keep up the great work!",
      "next_steps": []
    },
    "engagement_score": 0.92,
    "progress": 0.4,
    "next_action": {
      "primary_action": "continue",
      "alternatives": [],
      "reasoning": "You're making good progress!"
    }
  }
}
```

### Get Session Analytics
Get comprehensive analytics for a learning session.

**Endpoint:** `GET /interactive/session-analytics/{session_id}`

**Response:**
```json
{
  "success": true,
  "analytics": {
    "session_overview": {
      "session_id": "session_001",
      "user_id": "student_001",
      "duration_minutes": 45.5,
      "components_completed": 2,
      "total_components": 3,
      "completion_rate": 0.67
    },
    "engagement_metrics": {
      "attention_score": 0.89,
      "interaction_frequency": 2.3,
      "time_on_task": 45,
      "help_requests": 2,
      "exploration_depth": 0.78
    },
    "performance_metrics": {
      "total_interactions": 23,
      "correct_answers": 18,
      "accuracy": 0.78,
      "average_response_time": 12.5
    },
    "learning_velocity": 1.8,
    "adaptive_adjustments": [
      {
        "type": "increase_difficulty",
        "reason": "High performance and engagement",
        "adjustment": 0.2,
        "timestamp": "2024-12-18T14:45:00"
      }
    ],
    "recommendations": [
      {
        "type": "performance",
        "priority": "low",
        "message": "You're ready for more challenging content",
        "action": "increase_difficulty"
      }
    ]
  }
}
```

### Get Component Library
Get available interactive learning components.

**Endpoint:** `GET /interactive/component-library`

**Response:**
```json
{
  "success": true,
  "library": {
    "total_components": 12,
    "components": {
      "algebra_visualizer": {
        "title": "Interactive Algebra Visualizer",
        "type": "visualization",
        "difficulty": 3,
        "duration": 30,
        "objectives": [
          "Understand relationship between equations and graphs",
          "Explore effects of parameter changes"
        ],
        "prerequisites": ["basic_algebra"],
        "subject": "mathematics",
        "interactive_level": "high"
      }
    },
    "categories": {
      "by_type": {
        "visualization": ["algebra_visualizer", "geometry_explorer"],
        "simulation": ["physics_lab", "chemistry_lab"],
        "quiz": ["adaptive_quiz"]
      },
      "by_subject": {
        "mathematics": ["algebra_visualizer", "calculus_simulator"],
        "physics": ["physics_lab", "wave_simulator"],
        "chemistry": ["molecule_builder", "reaction_simulator"]
      }
    }
  }
}
```

---

## 📊 Dashboard APIs

### Get Dashboard HTML
Get complete HTML dashboard for specified layout.

**Endpoint:** `GET /dashboard/{layout_id}`

**Parameters:**
- `layout_id` (path, required): Dashboard layout ID
- `user_id` (query, optional): User ID for personalization

**Available Layouts:**
- `student_dashboard` - Student-focused learning dashboard
- `teacher_dashboard` - Teacher analytics dashboard  
- `knowledge_explorer` - Interactive knowledge graph explorer
- `memory_dashboard` - Memory intelligence dashboard
- `learning_lab` - Interactive learning laboratory

**Response:** HTML content for the dashboard

### Get Widget Data
Get data for a specific dashboard widget.

**Endpoint:** `POST /dashboard/widget-data/{widget_id}`

**Request Body:**
```json
{
  "widget_config": {
    "type": "chart",
    "content": {
      "chart_type": "progress_ring",
      "data_source": "user_progress"
    }
  },
  "user_data": {
    "user_id": "student_001"
  }
}
```

**Response:**
```json
{
  "success": true,
  "widget_data": {
    "plotly_data": {
      "data": [
        {
          "type": "scatter",
          "x": ["Mon", "Tue", "Wed", "Thu", "Fri"],
          "y": [65, 72, 78, 85, 90],
          "mode": "lines+markers"
        }
      ],
      "layout": {
        "title": "Learning Progress",
        "xaxis": {"title": "Day"},
        "yaxis": {"title": "Score (%)"}
      }
    }
  }
}
```

### Handle Control Actions
Process dashboard control actions.

**Endpoint:** `POST /dashboard/control-action`

**Request Body:**
```json
{
  "widget_id": "session_controls",
  "control_type": "start_session",
  "value": "mathematics"
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "action_processed": true,
    "session_started": true
  }
}
```

### Get Available Layouts
Get list of available dashboard layouts.

**Endpoint:** `GET /dashboard/layouts`

**Response:**
```json
{
  "success": true,
  "layouts": [
    {
      "id": "student_dashboard",
      "name": "Student Learning Dashboard",
      "description": "Comprehensive learning dashboard for students",
      "theme": "light",
      "widget_count": 6,
      "grid_size": [6, 6]
    }
  ]
}
```

---

## 🤖 Intelligence APIs

### Get Comprehensive Profile
Get complete user profile combining memory and graph data.

**Endpoint:** `GET /intelligence/comprehensive-profile/{user_id}`

**Response:**
```json
{
  "success": true,
  "comprehensive_profile": {
    "user_id": "student_001",
    "learning_patterns": {
      "total_sessions": 127,
      "learning_velocity": 1.3,
      "knowledge_retention": {"mathematics": 0.82}
    },
    "learning_statistics": {
      "total_concepts": 15,
      "mastered_concepts": 8,
      "average_performance": 0.84
    },
    "knowledge_gaps": {
      "missing_prerequisites": [],
      "weak_areas": [],
      "suggested_reviews": []
    },
    "recommendations": [
      {
        "concept": "Derivatives",
        "score": 0.85,
        "estimated_duration": 60
      }
    ],
    "generated_at": "2024-12-18T15:00:00"
  }
}
```

### Smart Session Planning
Create intelligent learning session based on user data and goals.

**Endpoint:** `POST /intelligence/smart-session-planning`

**Parameters:**
- `user_id` (query, required): User identifier
- `time_available` (query, required): Available time in minutes

**Request Body:**
```json
{
  "learning_goals": [
    "master quadratic equations",
    "understand derivatives"
  ],
  "preferences": {
    "difficulty_preference": 3,
    "learning_style": "visual"
  }
}
```

**Response:**
```json
{
  "success": true,
  "smart_session_plan": {
    "user_id": "student_001",
    "learning_goals": ["master quadratic equations"],
    "time_available": 60,
    "session_id": "session_smart_001",
    "recommended_components": ["algebra_visualizer", "adaptive_quiz"],
    "learning_paths": [
      {
        "target": "Quadratic Equations",
        "path": ["Linear Equations", "Quadratic Equations"],
        "duration": 45,
        "confidence": 0.85
      }
    ],
    "personalization": {
      "difficulty_adjustment": 0.84,
      "learning_velocity": 1.3,
      "preferred_style": "visual"
    }
  }
}
```

---

## Error Handling

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": "Additional error details if available"
  }
}
```

Common HTTP status codes:
- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Not Found (resource doesn't exist)
- `500` - Internal Server Error

---

## Rate Limiting

The API implements rate limiting to ensure fair usage:
- Default: 100 requests per minute per IP
- Authenticated users: 1000 requests per minute
- Heavy operations (analytics): 10 requests per minute

---

## WebSocket Support

Real-time features are available via WebSocket connections:

**Dashboard Updates:**
```
ws://localhost:8000/ws/dashboard/{layout_id}
```

**Learning Sessions:**
```
ws://localhost:8000/ws/session/{session_id}
```

---

## SDK and Examples

### Python SDK Example
```python
import requests

# Base configuration
BASE_URL = "http://localhost:8000/api"
USER_ID = "student_001"

# Store a learning session
session_data = {
    "subject": "mathematics",
    "topic": "quadratic_equations",
    "performance_metrics": {"accuracy": 0.87}
}

response = requests.post(
    f"{BASE_URL}/memory/store-session",
    params={"user_id": USER_ID},
    json=session_data
)

print(response.json())
```

### JavaScript SDK Example
```javascript
// Create interactive session
const createSession = async (userId, components) => {
  const response = await fetch('/api/interactive/create-session', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      components: components,
      preferences: {learning_style: 'visual'}
    })
  });
  
  return response.json();
};

// Usage
createSession('student_001', ['algebra_visualizer', 'adaptive_quiz'])
  .then(result => console.log(result));
```

---

This comprehensive API documentation covers all available endpoints in the Interactive Learning Platform. For additional support or feature requests, please refer to the main documentation or contact the development team.