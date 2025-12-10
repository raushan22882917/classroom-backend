# Magic Learn Advanced API Documentation

This document covers the advanced features and endpoints of the Magic Learn platform, including collaborative learning, AI tutoring, personalized learning paths, assessments, and content generation.

## Table of Contents

1. [Overview](#overview)
2. [Advanced Image Analysis](#advanced-image-analysis)
3. [Real-Time Analysis](#real-time-analysis)
4. [Collaborative Learning](#collaborative-learning)
5. [AI Tutor](#ai-tutor)
6. [Learning Paths](#learning-paths)
7. [Progress Tracking](#progress-tracking)
8. [Assessments](#assessments)
9. [Content Generation](#content-generation)
10. [WebSocket Integration](#websocket-integration)
11. [Authentication & Security](#authentication--security)

---

## Overview

The Magic Learn Advanced API extends the core platform with sophisticated AI-powered features for personalized and collaborative learning experiences. All endpoints are prefixed with `/api/magic-learn`.

### Key Features

- **Batch Image Analysis**: Process multiple images simultaneously
- **Real-Time Analysis**: Stream-based analysis for live content
- **Collaborative Sessions**: Multi-user learning environments
- **AI Tutoring**: Personalized AI-powered tutoring
- **Learning Paths**: Adaptive learning journey generation
- **Progress Tracking**: Comprehensive learning analytics
- **Dynamic Assessments**: AI-generated assessments
- **Content Generation**: Automated educational content creation

---

## Advanced Image Analysis

### Batch Analysis

**POST** `/api/magic-learn/batch-analysis`

Process multiple images in parallel with enhanced analysis capabilities.

#### Request Body

```json
{
  "images": [
    {
      "data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
      "instructions": "Focus on mathematical equations"
    },
    {
      "data": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD...",
      "instructions": "Analyze scientific diagrams"
    }
  ],
  "analysis_type": "mathematical",
  "user_id": "user123",
  "batch_name": "Homework Set 1"
}
```

#### Response

```json
{
  "success": true,
  "batch_id": "batch-uuid-123",
  "results": [
    {
      "success": true,
      "analysis": "## Mathematical Analysis\n\n### Quadratic Equation...",
      "detected_elements": ["quadratic_equation", "graph"],
      "confidence_score": 0.92,
      "processing_time": 2.3,
      "session_id": "batch-uuid-123_0",
      "key_concepts": ["Algebra", "Quadratic Functions"],
      "difficulty_assessment": "intermediate",
      "suggested_next_steps": ["Practice similar problems", "Explore graphing"],
      "structured_content": {
        "sections": [
          {"title": "Problem Analysis", "content": "..."},
          {"title": "Solution Steps", "content": "..."}
        ],
        "formulas": ["x = (-b ± √(b²-4ac)) / 2a"],
        "examples": ["Solve: 2x² + 5x - 3 = 0"]
      },
      "interactive_elements": [
        {
          "type": "calculator",
          "title": "Quadratic Formula Calculator",
          "config": {"formula": "quadratic"}
        }
      ]
    }
  ],
  "summary": "Analyzed 2 mathematical problems covering quadratic equations and graphing...",
  "total_processing_time": 4.1
}
```

---

## Real-Time Analysis

### Start Stream

**POST** `/api/magic-learn/realtime/start`

Start a real-time analysis stream for live content processing.

#### Request Body

```json
{
  "stream_id": "stream-123"
}
```

### Process Frame

**POST** `/api/magic-learn/realtime/process`

Process a single frame in the real-time stream.

#### Request Body

```json
{
  "stream_id": "stream-123",
  "frame_data": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD...",
  "analysis_type": "mathematical",
  "user_id": "user123"
}
```

#### Response

```json
{
  "success": true,
  "stream_id": "stream-123",
  "frame_number": 42,
  "analysis": "Detected geometric shapes: triangle, circle",
  "confidence": 0.85,
  "detected_objects": ["triangle", "circle", "line"],
  "timestamp": "2024-12-10T15:30:45.123Z"
}
```

### Stop Stream

**POST** `/api/magic-learn/realtime/stop`

Stop a real-time analysis stream.

---

## Collaborative Learning

### Create Session

**POST** `/api/magic-learn/collaborate/create`

Create a new collaborative learning session.

#### Request Body

```json
{
  "session_name": "Algebra Study Group",
  "participants": ["user123", "user456"],
  "session_type": "study_group",
  "max_participants": 6,
  "duration_minutes": 90
}
```

#### Response

```json
{
  "success": true,
  "session_id": "collab-session-uuid",
  "join_code": "ABC123",
  "session_url": "/magic-learn/collaborate/collab-session-uuid?code=ABC123",
  "expires_at": "2024-12-10T17:00:00Z"
}
```

### Join Session

**POST** `/api/magic-learn/collaborate/join`

Join an existing collaborative session.

#### Request Body

```json
{
  "session_id": "collab-session-uuid",
  "user_id": "user789",
  "join_code": "ABC123"
}
```

### Real-Time Collaboration Features

#### Update Participant State

**POST** `/api/magic-learn/collaborate/update-state`

Update participant state in real-time (cursor position, drawing state, etc.).

#### Send Chat Message

**POST** `/api/magic-learn/collaborate/chat`

Send chat messages within the collaborative session.

#### Get Session State

**GET** `/api/magic-learn/collaborate/state`

Get current session state including all participants and shared content.

---

## AI Tutor

### Chat with Tutor

**POST** `/api/magic-learn/ai-tutor/chat`

Have an interactive conversation with the AI tutor.

#### Request Body

```json
{
  "user_id": "user123",
  "question": "I don't understand how to solve quadratic equations",
  "context": "We're studying algebra in class",
  "subject": "mathematics",
  "difficulty_level": "intermediate",
  "learning_style": "visual"
}
```

#### Response

```json
{
  "success": true,
  "response": "I'd be happy to help you understand quadratic equations! Let me break this down step by step...",
  "explanation_type": "procedural",
  "follow_up_questions": [
    "Would you like to see how this applies to real-world problems?",
    "Do you want to practice with some examples?",
    "Are there specific parts of the formula that confuse you?"
  ],
  "related_concepts": [
    "Linear Equations",
    "Parabolas",
    "Factoring"
  ],
  "practice_problems": [
    {
      "problem": "Solve: x² + 5x + 6 = 0",
      "difficulty": "medium",
      "hints": ["Try factoring first", "Look for two numbers that multiply to 6 and add to 5"]
    }
  ],
  "confidence_score": 0.94
}
```

---

## Learning Paths

### Generate Learning Path

**POST** `/api/magic-learn/learning-path/generate`

Generate a personalized learning path based on user goals and preferences.

#### Request Body

```json
{
  "user_id": "user123",
  "subject_area": "mathematics",
  "current_level": "intermediate",
  "learning_goals": [
    "Master quadratic equations",
    "Understand graphing functions",
    "Prepare for calculus"
  ],
  "time_available": 5,
  "preferred_learning_style": "visual"
}
```

#### Response

```json
{
  "success": true,
  "path_id": "path-uuid-123",
  "milestones": [
    {
      "milestone_id": "milestone-1",
      "title": "Quadratic Functions Mastery",
      "description": "Master the fundamentals of quadratic functions",
      "estimated_hours": 8,
      "prerequisites": [],
      "learning_objectives": [
        "Understand quadratic function structure",
        "Solve quadratic equations using multiple methods",
        "Graph quadratic functions accurately"
      ],
      "activities": [
        {
          "type": "reading",
          "title": "Study Quadratic Functions Fundamentals",
          "estimated_minutes": 60,
          "resources": ["textbook", "online_articles"]
        },
        {
          "type": "visualization",
          "title": "Create Quadratic Functions Mind Map",
          "estimated_minutes": 45,
          "resources": ["mind_mapping_tool", "diagrams"]
        }
      ],
      "assessment_criteria": [
        "Demonstrates understanding of quadratic concepts",
        "Can solve problems accurately",
        "Shows clear reasoning"
      ],
      "difficulty_level": "intermediate"
    }
  ],
  "estimated_duration": 42,
  "recommended_activities": [
    {
      "type": "daily",
      "title": "Daily Review",
      "frequency": "daily",
      "duration_minutes": 15
    }
  ],
  "progress_tracking": {
    "tracking_frequency": "daily",
    "metrics": ["study_time", "concepts_mastered", "problems_solved"],
    "adaptive_difficulty": true
  }
}
```

### Get Learning Path

**GET** `/api/magic-learn/learning-path/{path_id}`

Retrieve a specific learning path by ID.

---

## Progress Tracking

### Track Progress

**POST** `/api/magic-learn/progress/track`

Record learning activity and update progress metrics.

#### Request Body

```json
{
  "user_id": "user123",
  "activity_type": "problem_solving",
  "activity_data": {
    "study_time_minutes": 45,
    "milestone_completed": "milestone-1",
    "current_milestone": "milestone-2",
    "subject_area": "mathematics",
    "performance_data": {
      "problems_solved": 8,
      "problems_correct": 6,
      "weak_areas": ["factoring", "graphing"],
      "strong_areas": ["basic_algebra", "arithmetic"]
    }
  },
  "timestamp": "2024-12-10T15:30:00Z"
}
```

#### Response

```json
{
  "success": true,
  "user_id": "user123",
  "current_level": "intermediate",
  "progress_percentage": 67.5,
  "achievements": [
    "First Milestone Completed",
    "5 Day Learning Streak"
  ],
  "next_recommendations": [
    "Focus on improving: factoring, graphing",
    "Continue working on your current milestone",
    "Keep up your learning streak - you're doing great!"
  ],
  "streak_count": 5
}
```

### Get User Progress

**GET** `/api/magic-learn/progress/{user_id}`

Get comprehensive progress data for a user.

### Get Progress Analytics

**GET** `/api/magic-learn/progress/{user_id}/analytics`

Get detailed analytics including learning velocity, completion rates, and performance trends.

---

## Assessments

### Generate Assessment

**POST** `/api/magic-learn/assessment/generate`

Generate a comprehensive assessment with AI-powered questions.

#### Request Body

```json
{
  "user_id": "user123",
  "subject": "mathematics",
  "topic": "quadratic_equations",
  "difficulty_level": "intermediate",
  "question_count": 10,
  "question_types": ["multiple_choice", "short_answer", "calculation"]
}
```

#### Response

```json
{
  "success": true,
  "assessment_id": "assessment-uuid-123",
  "questions": [
    {
      "question_id": "q1",
      "question_text": "What is the discriminant of the quadratic equation 2x² + 5x - 3 = 0?",
      "question_type": "calculation",
      "points": 3,
      "difficulty": "intermediate",
      "topic": "quadratic_equations",
      "learning_objective": "Calculate discriminant values"
    }
  ],
  "time_limit": 45,
  "scoring_rubric": {
    "total_points": 25,
    "grading_scale": {
      "A": {"min_percentage": 90, "description": "Excellent understanding"},
      "B": {"min_percentage": 80, "description": "Good understanding"}
    }
  },
  "learning_objectives": [
    "Demonstrate understanding of quadratic equation concepts",
    "Apply quadratic formula to solve problems"
  ]
}
```

### Submit Assessment

**POST** `/api/magic-learn/assessment/{assessment_id}/submit`

Submit completed assessment for grading.

#### Request Body

```json
{
  "user_id": "user123",
  "answers": {
    "q1": "49",
    "q2": "x = 1/2, x = -3",
    "q3": "The parabola opens upward because a > 0"
  }
}
```

#### Response

```json
{
  "success": true,
  "result_id": "result-uuid-123",
  "score": 22,
  "percentage": 88.0,
  "grade": "B",
  "feedback": "Good job! You show solid understanding of the material. Strengths: calculation, problem_solving. Areas for improvement: graphing_concepts.",
  "detailed_results": [
    {
      "question_id": "q1",
      "user_answer": "49",
      "correct_answer": "49",
      "points_earned": 3,
      "is_correct": true,
      "feedback": "Correct! Well done calculating the discriminant."
    }
  ]
}
```

---

## Content Generation

### Generate Educational Content

**POST** `/api/magic-learn/content/generate`

Generate comprehensive educational content using AI.

#### Request Body

```json
{
  "topic": "Quadratic Functions",
  "content_type": "lesson",
  "difficulty_level": "intermediate",
  "duration_minutes": 45,
  "learning_objectives": [
    "Understand quadratic function structure",
    "Graph quadratic functions",
    "Solve quadratic equations"
  ],
  "format_preferences": ["interactive", "visual"]
}
```

#### Response

```json
{
  "success": true,
  "content_id": "content-uuid-123",
  "title": "Quadratic Functions - Complete Lesson",
  "content": "# Quadratic Functions\n\n## Introduction\nWelcome to this comprehensive lesson on quadratic functions...",
  "metadata": {
    "topic": "Quadratic Functions",
    "content_type": "lesson",
    "difficulty_level": "intermediate",
    "word_count": 1250,
    "estimated_reading_time_minutes": 6,
    "key_topics": ["Vertex Form", "Standard Form", "Graphing"],
    "complexity_score": 0.7
  },
  "interactive_elements": [
    {
      "type": "interactive_graph",
      "title": "Quadratic Function Explorer",
      "description": "Manipulate coefficients to see how they affect the graph",
      "config": {
        "type": "function_grapher",
        "interactive": true,
        "parameters": ["a", "b", "c"]
      }
    }
  ],
  "assessment_questions": [
    {
      "question_id": "self-assess-1",
      "question_text": "How well do you understand: Understand quadratic function structure?",
      "question_type": "self_assessment",
      "scale": {"min": 1, "max": 5}
    }
  ]
}
```

### Get Generated Content

**GET** `/api/magic-learn/content/{content_id}`

Retrieve generated content by ID.

---

## WebSocket Integration

For real-time features like collaborative sessions and live analysis, the platform supports WebSocket connections:

### Connection Endpoint

```
ws://localhost:8000/ws/magic-learn/{session_id}
```

### Message Types

#### Participant Update
```json
{
  "type": "participant_update",
  "user_id": "user123",
  "data": {
    "cursor_position": {"x": 150, "y": 200},
    "current_tool": "drawing"
  }
}
```

#### Chat Message
```json
{
  "type": "chat_message",
  "user_id": "user123",
  "message": "I think this equation should be solved differently",
  "timestamp": "2024-12-10T15:30:00Z"
}
```

#### Canvas Update
```json
{
  "type": "canvas_update",
  "user_id": "user123",
  "canvas_data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA..."
}
```

---

## Authentication & Security

### API Key Authentication

Include your API key in the request headers:

```http
Authorization: Bearer your-api-key-here
```

### Rate Limits

- **Image Analysis**: 10 requests per minute per user
- **Real-Time Analysis**: 60 frames per minute per stream
- **AI Tutor**: 20 requests per minute per user
- **Content Generation**: 5 requests per minute per user

### Security Features

- **Input Validation**: All inputs are validated and sanitized
- **Content Filtering**: Generated content is filtered for appropriateness
- **Session Management**: Collaborative sessions have secure join codes
- **Data Privacy**: User data is encrypted and anonymized where possible

---

## Error Handling

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": "Detailed error message",
  "error_code": "INVALID_INPUT",
  "timestamp": "2024-12-10T15:30:00Z",
  "request_id": "req-uuid-123"
}
```

### Common Error Codes

- `INVALID_INPUT`: Request validation failed
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `SESSION_NOT_FOUND`: Collaborative session doesn't exist
- `ASSESSMENT_EXPIRED`: Assessment submission window closed
- `CONTENT_GENERATION_FAILED`: AI content generation error
- `INSUFFICIENT_PERMISSIONS`: User lacks required permissions

---

## SDK Examples

### Python SDK

```python
import magic_learn

# Initialize client
client = magic_learn.Client(api_key="your-api-key")

# Batch image analysis
batch_result = await client.analyze_batch([
    {"data": image1_base64, "instructions": "Focus on equations"},
    {"data": image2_base64, "instructions": "Analyze diagrams"}
])

# Create collaborative session
session = await client.create_collaborative_session(
    name="Study Group",
    participants=["user1", "user2"],
    max_participants=6
)

# Generate learning path
path = await client.generate_learning_path(
    user_id="user123",
    subject="mathematics",
    current_level="intermediate",
    goals=["Master algebra", "Prepare for calculus"]
)

# Chat with AI tutor
response = await client.chat_with_tutor(
    user_id="user123",
    question="How do I solve quadratic equations?",
    subject="mathematics"
)
```

### JavaScript SDK

```javascript
import MagicLearn from 'magic-learn-js';

const client = new MagicLearn({ apiKey: 'your-api-key' });

// Real-time analysis
const stream = await client.startRealtimeAnalysis('stream-123');
stream.onFrame((result) => {
  console.log('Detected:', result.detected_objects);
});

// Generate assessment
const assessment = await client.generateAssessment({
  subject: 'mathematics',
  topic: 'quadratic_equations',
  difficulty: 'intermediate',
  questionCount: 10
});

// Track progress
await client.trackProgress({
  userId: 'user123',
  activityType: 'problem_solving',
  activityData: {
    studyTimeMinutes: 45,
    problemsSolved: 8
  }
});
```

---

## Deployment & Scaling

### Infrastructure Requirements

- **CPU**: 4+ cores for AI processing
- **Memory**: 8GB+ RAM for model loading
- **Storage**: SSD for fast model access
- **Network**: High bandwidth for real-time features

### Scaling Considerations

- **Horizontal Scaling**: Multiple API instances behind load balancer
- **Database Scaling**: Separate read/write replicas
- **Caching**: Redis for session data and frequent queries
- **CDN**: Static content delivery for generated materials

### Monitoring

- **Health Checks**: `/api/magic-learn/health`
- **Metrics**: Response times, success rates, resource usage
- **Logging**: Structured logs for debugging and analytics
- **Alerts**: Automated alerts for system issues

---

This advanced API provides a comprehensive platform for AI-powered educational experiences with collaborative features, personalized learning paths, and intelligent content generation. The modular design allows for easy integration and scaling based on specific needs.