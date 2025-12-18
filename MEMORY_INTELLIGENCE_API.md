# Memory Intelligence API Documentation

## Overview

The Memory Intelligence API provides powerful long-term memory and context storage capabilities that can be used from anywhere in the frontend. It combines MemMachine persistent memory with Neo4j knowledge graph for intelligent context management and personalized recommendations.

## Base URL
```
http://localhost:8000/api
```

## Core Endpoints

### 1. Remember Context
**POST** `/context/remember?user_id={user_id}`

Store any context for long-term retrieval. Use this to remember user interactions, learning progress, preferences, navigation patterns, etc.

**Request Body:**
```json
{
  "type": "learning|interaction|preference|navigation|performance|general",
  "content": {
    // Any JSON object containing the context data
  },
  "subject": "biology",           // Optional
  "topic": "photosynthesis",      // Optional  
  "importance": 0.8,              // 0.0-1.0, default 0.5
  "tags": ["quiz", "correct"],    // Optional tags for categorization
  "source": "quiz_component",     // Optional source identifier
  "session_id": "session_123",    // Optional session ID
  "page_url": "/biology/quiz",    // Optional page URL
  "component": "interactive_quiz" // Optional component name
}
```

**Response:**
```json
{
  "success": true,
  "memory_id": "abc123",
  "message": "Context remembered successfully",
  "stored_at": "2025-12-18T11:14:16.238234",
  "tags": ["quiz", "correct", "user_123", "learning", "biology"]
}
```

### 2. Recall Context  
**GET** `/context/recall/{user_id}`

Retrieve stored contexts with flexible filtering options.

**Query Parameters:**
- `context_type`: Filter by type (learning, interaction, etc.)
- `subject`: Filter by subject
- `topic`: Filter by topic  
- `tags`: Filter by tags (can specify multiple)
- `limit`: Max results (default 20)
- `days_back`: Days to look back (default 30)
- `min_importance`: Minimum importance score (default 0.0)

**Example:**
```
GET /context/recall/user_123?context_type=learning&subject=biology&limit=5
```


**Response:**
```json
{
  "success": true,
  "user_id": "user_123",
  "total_contexts": 1,
  "contexts": [
    {
      "memory_id": "abc123",
      "content": { /* stored content */ },
      "metadata": { /* context metadata */ },
      "timestamp": "2025-12-18T11:14:16.236411",
      "importance_score": 0.8,
      "access_count": 1,
      "last_accessed": "2025-12-18T11:14:27.005558",
      "tags": ["biology", "learning"],
      "context_type": "learning",
      "subject": "biology",
      "topic": "photosynthesis",
      "source": "quiz_component"
    }
  ],
  "filters_applied": { /* applied filters */ }
}
```

### 3. Smart Suggestions
**GET** `/context/smart-suggestions/{user_id}?suggestion_type={type}`

Get intelligent suggestions based on stored contexts and learning patterns.

**Suggestion Types:**
- `next_action`: What to do next
- `content_recommendation`: What content to study
- `study_schedule`: When to study
- `review_suggestion`: What to review
- `learning_path`: Optimal learning path

**Request Body (optional):**
```json
{
  "current_context": {
    "page": "biology_quiz",
    "subject": "biology",
    "topic": "photosynthesis"
  }
}
```

**Response:**
```json
{
  "success": true,
  "user_id": "user_123",
  "suggestion_type": "next_action",
  "suggestions": [
    {
      "type": "learning_recommendation",
      "action": "Study Kinematics",
      "reason": "Based on your progress, this concept is ready to learn",
      "estimated_duration": 45,
      "difficulty": 3,
      "confidence": 0.85
    }
  ],
  "insights": {
    "most_studied_subject": "biology",
    "most_studied_topic": "photosynthesis",
    "peak_activity_hour": 14,
    "total_contexts": 25,
    "learning_velocity": 1.2,
    "mastery_rate": 0.75
  }
}
```

### 4. Bulk Remember
**POST** `/context/bulk-remember?user_id={user_id}`

Store multiple contexts at once (useful for session end or batch operations).

**Request Body:**
```json
{
  "contexts": [
    {
      "type": "preference",
      "content": { "setting": "difficulty", "value": "intermediate" },
      "importance": 0.7,
      "tags": ["preference"]
    },
    {
      "type": "navigation",
      "content": { "from": "/quiz", "to": "/lessons" },
      "importance": 0.3,
      "tags": ["navigation"]
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "user_id": "user_123",
  "total_stored": 2,
  "stored_contexts": [
    { "memory_id": "abc", "context_type": "preference" },
    { "memory_id": "def", "context_type": "navigation" }
  ],
  "learning_updates": 0,
  "stored_at": "2025-12-18T11:16:07.809722"
}
```

### 5. User Timeline
**GET** `/context/user-timeline/{user_id}`

Get a comprehensive timeline of user activities and progress.

**Query Parameters:**
- `days_back`: Days to look back (default 7)
- `include_learning`: Include learning sessions (default true)
- `include_interactions`: Include interactions (default true)

**Response:**
```json
{
  "success": true,
  "user_id": "user_123",
  "timeline_period": {
    "days_back": 7,
    "start_date": "2025-12-11T11:14:45",
    "end_date": "2025-12-18T11:14:45"
  },
  "summary": {
    "total_events": 15,
    "learning_sessions": 8,
    "interactions": 7,
    "subjects_studied": 3,
    "most_active_day": "2025-12-17",
    "average_daily_activity": 2.14
  },
  "timeline": [
    {
      "timestamp": "2025-12-18T10:30:00",
      "type": "learning_session",
      "event_type": "learning",
      "title": "Learning Session: Photosynthesis",
      "description": "Studied biology - photosynthesis",
      "subject": "biology",
      "topic": "photosynthesis",
      "importance": 0.8,
      "data": {
        "duration": 45,
        "completion_rate": 0.95,
        "performance": { "accuracy": 0.85 }
      }
    }
  ]
}
```

## Context Types

### Learning Context
Store learning activities, quiz results, lesson completions:
```json
{
  "type": "learning",
  "content": {
    "question": "What is photosynthesis?",
    "answer": "Process by which plants make food",
    "performance_data": {
      "accuracy": 0.85,
      "completion_rate": 1.0,
      "duration": 120
    }
  },
  "subject": "biology",
  "topic": "photosynthesis",
  "importance": 0.8
}
```

### Interaction Context
Store user interactions with components:
```json
{
  "type": "interaction",
  "content": {
    "component": "interactive_quiz",
    "action": "answer_question",
    "result": "correct"
  },
  "component": "interactive_quiz",
  "page_url": "/biology/quiz"
}
```

### Preference Context
Store user preferences and settings:
```json
{
  "type": "preference",
  "content": {
    "setting": "difficulty_level",
    "old_value": "beginner",
    "new_value": "intermediate"
  },
  "importance": 0.7
}
```

### Navigation Context
Track user navigation patterns:
```json
{
  "type": "navigation",
  "content": {
    "from_page": "/biology/quiz",
    "to_page": "/chemistry/lessons",
    "duration_on_page": 300
  }
}
```

## Frontend Integration Examples

### React/Vue Example
```javascript
// Remember a learning context
async function rememberLearningActivity(userId, activityData) {
  const response = await fetch(`/api/context/remember?user_id=${userId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      type: 'learning',
      content: activityData,
      subject: activityData.subject,
      topic: activityData.topic,
      importance: 0.8,
      tags: ['quiz', 'completed'],
      source: 'quiz_component'
    })
  });
  return response.json();
}

// Recall user's learning history
async function getUserLearningHistory(userId, subject) {
  const response = await fetch(
    `/api/context/recall/${userId}?context_type=learning&subject=${subject}&limit=20`
  );
  return response.json();
}

// Get smart suggestions
async function getNextSteps(userId) {
  const response = await fetch(
    `/api/context/smart-suggestions/${userId}?suggestion_type=next_action`
  );
  return response.json();
}
```

## Use Cases

1. **Personalized Welcome Messages**: Recall recent activity to greet users
2. **Resume Learning**: Show where user left off
3. **Smart Recommendations**: Suggest next topics based on progress
4. **Progress Tracking**: Visualize learning journey over time
5. **Adaptive Difficulty**: Adjust based on performance patterns
6. **Study Reminders**: Suggest optimal study times
7. **Knowledge Gaps**: Identify weak areas needing review
8. **Learning Analytics**: Generate insights from stored contexts

## Best Practices

1. **Tag Consistently**: Use consistent tags for easier filtering
2. **Set Importance**: Higher importance = longer retention
3. **Include Context**: Store enough data to be useful later
4. **Batch Operations**: Use bulk-remember for multiple contexts
5. **Filter Wisely**: Use appropriate filters to get relevant data
6. **Monitor Storage**: Check memory stats periodically

## Error Handling

All endpoints return standard error responses:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": []
  }
}
```

Common error codes:
- `VALIDATION_ERROR`: Invalid input data
- `NOT_FOUND`: Resource not found
- `INTERNAL_SERVER_ERROR`: Server error

## Rate Limiting

The API uses rate limiting to prevent abuse. Current limits:
- Remember: 100 requests/minute per user
- Recall: 200 requests/minute per user
- Suggestions: 50 requests/minute per user
