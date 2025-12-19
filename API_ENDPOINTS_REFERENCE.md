# Complete API Endpoints Reference

Base URL: `http://127.0.0.1:8000`

## 🔍 RAG (Retrieval-Augmented Generation) Endpoints

### POST /api/rag/query
**Description:** Main RAG query endpoint with curriculum search
```json
{
  "query": "Explain photosynthesis",
  "user_id": "user_123",
  "subject": "biology",
  "grade": 12,
  "max_tokens": 2000
}
```

### POST /api/rag/query-direct
**Description:** Direct Gemini query (fallback mode)
```json
{
  "query": "What is calculus?",
  "user_id": "user_123",
  "subject": "mathematics"
}
```

### POST /api/rag/initialize
**Description:** Initialize RAG services
```json
{}
```

### POST /api/rag/evaluate
**Description:** Evaluate student answers
```json
{
  "question": "What is photosynthesis?",
  "user_answer": "Process where plants make food",
  "reference_content": "Photosynthesis is...",
  "subject": "biology"
}
```

---

## 🧠 Memory Intelligence Endpoints

### Memory Storage
#### POST /api/memory/store-session?user_id={user_id}
**Description:** Store learning session in persistent memory
```json
{
  "session_id": "session_001",
  "subject": "mathematics",
  "topic": "derivatives",
  "difficulty_level": 3,
  "learning_objectives": ["understand derivatives"],
  "performance_metrics": {
    "accuracy": 0.85,
    "completion_time": 1800
  },
  "duration": 1800,
  "completion_rate": 0.9
}
```

#### GET /api/memory/learning-history/{user_id}
**Description:** Get user's learning history
**Query Params:** `subject`, `days_back`, `limit`

#### GET /api/memory/learning-patterns/{user_id}
**Description:** Analyze user's learning patterns

#### GET /api/memory/stats
**Description:** Get memory usage statistics

---

## 🕸️ Knowledge Graph Endpoints

### Concept Management
#### POST /api/knowledge-graph/create-concept
**Description:** Create new concept in knowledge graph
**Query Params:** `name`, `concept_type`, `difficulty_level`
```json
{
  "description": "Mathematical concept description"
}
```

#### POST /api/knowledge-graph/create-relationship
**Description:** Create relationship between concepts
**Query Params:** `source_concept`, `target_concept`, `relationship_type`, `strength`

#### GET /api/knowledge-graph/concept-relationships/{concept_name}
**Description:** Get all relationships for a concept

### Learning Path & Recommendations
#### GET /api/knowledge-graph/learning-path/{user_id}
**Description:** Find optimal learning path
**Query Params:** `target_concept`, `current_knowledge[]`

#### GET /api/knowledge-graph/recommendations/{user_id}
**Description:** Get personalized learning recommendations
**Query Params:** `limit`

#### POST /api/knowledge-graph/update-progress
**Description:** Update user progress on concept
**Query Params:** `user_id`, `concept_name`
```json
{
  "performance_score": 0.85,
  "time_spent": 1200,
  "mastery_level": 0.7
}
```

#### GET /api/knowledge-graph/user-stats/{user_id}
**Description:** Get user learning statistics

#### GET /api/knowledge-graph/knowledge-gaps/{user_id}
**Description:** Analyze knowledge gaps

#### GET /api/knowledge-graph/stats
**Description:** Get knowledge graph statistics

---

## 💭 Context Memory Endpoints

### Context Storage & Retrieval
#### POST /api/context/remember?user_id={user_id}
**Description:** Store any context for long-term retrieval
```json
{
  "type": "learning",
  "content": {
    "activity": "quiz_completion",
    "score": 85,
    "performance_data": {
      "accuracy": 0.85,
      "time_taken": 600
    }
  },
  "subject": "mathematics",
  "topic": "derivatives",
  "importance": 0.8,
  "tags": ["quiz", "mathematics"],
  "source": "quiz_interface",
  "session_id": "session_001"
}
```

#### GET /api/context/recall/{user_id}
**Description:** Retrieve stored contexts
**Query Params:** `context_type`, `subject`, `topic`, `tags[]`, `limit`, `days_back`, `min_importance`

#### POST /api/context/smart-suggestions/{user_id}
**Description:** Get intelligent suggestions based on context
**Query Params:** `suggestion_type`
```json
{
  "current_subject": "mathematics",
  "current_topic": "integration",
  "time_available": 30
}
```

#### POST /api/context/bulk-remember?user_id={user_id}
**Description:** Bulk store multiple contexts
```json
{
  "contexts": [
    {
      "type": "interaction",
      "content": {"component": "calculator", "action": "used"},
      "importance": 0.3,
      "tags": ["tool_usage"]
    }
  ]
}
```

#### GET /api/context/user-timeline/{user_id}
**Description:** Get comprehensive user activity timeline
**Query Params:** `days_back`, `include_learning`, `include_interactions`

---

## 🎮 Interactive Learning Endpoints

#### POST /api/interactive/create-session?user_id={user_id}
**Description:** Create interactive learning session
```json
{
  "components": ["adaptive_quiz", "concept_mapper"],
  "preferences": {
    "difficulty": "medium",
    "learning_style": "visual"
  }
}
```

#### POST /api/interactive/process-interaction?session_id={session_id}
**Description:** Process user interaction
```json
{
  "interaction_type": "answer_selected",
  "data": {"answer": "A", "time_taken": 15}
}
```

#### GET /api/interactive/session-analytics/{session_id}
**Description:** Get session analytics

#### GET /api/interactive/component-library
**Description:** Get available interactive components

#### POST /api/interactive/create-visualization?chart_type={type}
**Description:** Create interactive visualizations
```json
{
  "data": {
    "labels": ["Week 1", "Week 2"],
    "scores": [75, 82]
  },
  "title": "Learning Progress"
}
```

---

## 🤖 Enhanced AI Tutor Endpoints

#### POST /api/ai-tutor/create-session
**Description:** Create enhanced AI tutor session
**Query Params:** `user_id`, `session_name`, `subject`

#### POST /api/ai-tutor/send-message
**Description:** Send message to AI tutor
**Query Params:** `session_id`, `user_id`
```json
{
  "content": "Explain derivatives",
  "subject": "mathematics",
  "message_type": "text"
}
```

#### GET /api/ai-tutor/learning-insights/{user_id}
**Description:** Get comprehensive learning insights

#### POST /api/ai-tutor/create-interactive-session?user_id={user_id}
**Description:** Create interactive session from AI tutor
```json
{
  "component_ids": ["quiz_generator", "concept_explainer"],
  "preferences": {
    "difficulty": "adaptive"
  }
}
```

---

## 🔔 Notification Endpoints

#### GET /api/notifications/{user_id}
**Description:** Get user notifications
**Query Params:** `limit`, `unread_only`

#### POST /api/notifications/{user_id}
**Description:** Create notification
```json
{
  "type": "success",
  "title": "Quiz Completed!",
  "message": "You scored 85%",
  "action": {
    "label": "View Results",
    "url": "/quiz/results/123"
  },
  "auto_dismiss": false
}
```

#### POST /api/notifications/{notification_id}/dismiss?user_id={user_id}
**Description:** Dismiss notification

#### POST /api/notifications/{user_id}/mark-all-read
**Description:** Mark all notifications as read

---

## 📝 Notes Endpoints

#### GET /api/notes?user_id={user_id}
**Description:** Get user notes
**Query Params:** `limit`, `subject`, `topic`

#### POST /api/notes?user_id={user_id}
**Description:** Create user note
```json
{
  "title": "Derivatives Study Notes",
  "content": "Key points about derivatives...",
  "subject": "mathematics",
  "topic": "derivatives",
  "type": "study_note",
  "tags": ["calculus", "important"]
}
```

#### PUT /api/notes/{note_id}?user_id={user_id}
**Description:** Update existing note
```json
{
  "title": "Updated title",
  "content": "Updated content"
}
```

---

## 🎯 AI Tutoring Endpoints

#### GET /api/ai-tutoring/sessions?user_id={user_id}
**Description:** Get AI tutoring sessions
**Query Params:** `limit`, `offset`

#### POST /api/ai-tutoring/sessions
**Description:** Create AI tutoring session
```json
{
  "user_id": "user_123",
  "subject": "mathematics",
  "topic": "calculus",
  "grade": 12
}
```

#### POST /api/ai-tutoring/sessions/message
**Description:** Send message in tutoring session
```json
{
  "session_id": "session_123",
  "user_id": "user_123",
  "content": "Explain derivatives",
  "subject": "mathematics"
}
```

#### GET /api/ai-tutoring/sessions/{session_id}/messages?limit={limit}
**Description:** Get session messages

#### GET /api/ai-tutoring/health
**Description:** AI tutoring service health check

#### POST /api/ai-tutoring/answer
**Description:** Get AI tutoring answer
```json
{
  "question": "What is derivative?",
  "user_id": "user_123",
  "subject": "mathematics"
}
```

#### GET /api/ai-tutoring/lesson-plans?subject={subject}
**Description:** Get lesson plans

#### POST /api/ai-tutoring/lesson-plans/generate
**Description:** Generate lesson plan
```json
{
  "subject": "mathematics",
  "topic": "derivatives",
  "grade": 12,
  "duration": 60
}
```

---

## ❓ Doubt Solver Endpoints

#### POST /api/doubt/text
**Description:** Solve text-based doubts
```json
{
  "question": "Explain Newton's laws",
  "user_id": "user_123",
  "subject": "physics"
}
```

#### POST /api/doubt/image
**Description:** Solve image-based doubts
```json
{
  "image_data": "base64_encoded_image",
  "user_id": "user_123",
  "subject": "mathematics"
}
```

#### POST /api/doubt/voice
**Description:** Solve voice-based doubts
```json
{
  "audio_data": "base64_encoded_audio",
  "user_id": "user_123"
}
```

#### POST /api/doubt/wolfram/chat?query={query}&include_steps={boolean}
**Description:** Wolfram Alpha integration

#### GET /api/doubt/history?user_id={user_id}
**Description:** Get doubt history

---

## 📊 Quiz & Exam Endpoints

### Quiz Endpoints
#### POST /api/quiz/start
**Description:** Start quiz session
```json
{
  "user_id": "user_123",
  "subject": "mathematics",
  "topic": "algebra",
  "difficulty": "medium"
}
```

#### POST /api/quiz/answer
**Description:** Submit quiz answer
```json
{
  "session_id": "session_123",
  "question_id": "q1",
  "answer": "A",
  "user_id": "user_123"
}
```

#### POST /api/quiz/submit
**Description:** Submit complete quiz

#### GET /api/quiz/session/{session_id}
**Description:** Get quiz session details

### Exam Endpoints
#### GET /api/exam/sets
**Description:** Get available exam sets

#### GET /api/exam/sets/{exam_set_id}
**Description:** Get specific exam set

#### POST /api/exam/start
**Description:** Start exam session
```json
{
  "user_id": "user_123",
  "exam_set_id": "exam_001",
  "subject": "physics"
}
```

#### POST /api/exam/answer
**Description:** Submit exam answer

#### POST /api/exam/submit
**Description:** Submit complete exam

#### GET /api/exam/results/{session_id}
**Description:** Get exam results

#### GET /api/exam/history?user_id={user_id}
**Description:** Get exam history

---

## 📈 Progress & Analytics Endpoints

### Progress Endpoints
#### GET /api/progress/{user_id}
**Description:** Get user progress

#### GET /api/progress/{user_id}/summary
**Description:** Get progress summary

#### GET /api/progress/{user_id}/achievements
**Description:** Get user achievements

#### GET /api/progress/{user_id}/topic/{topic_id}
**Description:** Get topic-specific progress

### Analytics Endpoints
#### GET /api/analytics/dashboard
**Description:** Get analytics dashboard

#### GET /api/analytics/trends
**Description:** Get analytics trends

#### GET /api/analytics/student/{student_id}
**Description:** Get student analytics

#### POST /api/analytics/event
**Description:** Track analytics event
```json
{
  "user_id": "user_123",
  "event_type": "quiz_completed",
  "metadata": {"score": 85, "subject": "mathematics"}
}
```

#### POST /api/analytics/test-result
**Description:** Record test result

#### POST /api/analytics/progress-snapshot
**Description:** Take progress snapshot

---

## 📚 Homework & Microplan Endpoints

### Homework Endpoints
#### POST /api/homework/start
**Description:** Start homework session
```json
{
  "user_id": "user_123",
  "subject": "mathematics",
  "topic": "trigonometry"
}
```

#### GET /api/homework/sessions?user_id={user_id}
**Description:** Get homework sessions

#### GET /api/homework/session/{session_id}
**Description:** Get specific homework session

#### POST /api/homework/attempt
**Description:** Submit homework attempt

#### POST /api/homework/hint
**Description:** Get homework hint

### Microplan Endpoints
#### POST /api/microplan/generate
**Description:** Generate microplan
```json
{
  "user_id": "user_123",
  "subject": "chemistry",
  "available_time": 60,
  "difficulty_preference": "medium"
}
```

#### GET /api/microplan/today?user_id={user_id}
**Description:** Get today's microplan

#### GET /api/microplan/{microplan_id}
**Description:** Get specific microplan

#### POST /api/microplan/{microplan_id}/complete
**Description:** Mark microplan as complete

#### GET /api/microplan/{plan_date}?user_id={user_id}
**Description:** Get microplan for specific date

---

## 🎓 Teacher & Admin Endpoints

### Teacher Endpoints
#### GET /api/teacher/dashboard?teacher_id={teacher_id}
**Description:** Get teacher dashboard

#### GET /api/teacher/students?teacher_id={teacher_id}
**Description:** Get teacher's students

#### GET /api/teacher/students/{student_id}/performance
**Description:** Get student performance

#### GET /api/teacher/quizzes?teacher_id={teacher_id}
**Description:** Get teacher's quizzes

#### GET /api/teacher/quizzes/{quiz_id}
**Description:** Get specific quiz

#### POST /api/teacher/quiz-sessions
**Description:** Create quiz session

#### POST /api/teacher/assessment
**Description:** Create assessment

#### POST /api/teacher/lesson-plan
**Description:** Create lesson plan

#### POST /api/teacher/parent-message
**Description:** Send message to parent

### Admin Endpoints
#### GET /api/admin/dashboard
**Description:** Get admin dashboard

#### GET /api/admin/users
**Description:** Get all users

#### GET /api/admin/students
**Description:** Get all students

#### GET /api/admin/students/{student_id}
**Description:** Get specific student

#### GET /api/admin/teachers
**Description:** Get all teachers

#### GET /api/admin/schools
**Description:** Get all schools

#### GET /api/admin/schools/{school_id}
**Description:** Get specific school

#### GET /api/admin/schools/{school_id}/students
**Description:** Get school students

#### GET /api/admin/schools/{school_id}/teachers
**Description:** Get school teachers

#### GET /api/admin/export
**Description:** Export data

---

## 🌐 Translation & Wellbeing Endpoints

### Translation Endpoints
#### GET /api/translation/languages
**Description:** Get supported languages

#### POST /api/translation/translate
**Description:** Translate text
```json
{
  "text": "Hello, how are you?",
  "target_language": "es",
  "source_language": "en"
}
```

#### POST /api/translation/detect
**Description:** Detect language
```json
{
  "text": "Bonjour, comment allez-vous?"
}
```

#### POST /api/translation/translate/batch
**Description:** Batch translate multiple texts

### Wellbeing Endpoints
#### POST /api/wellbeing/focus/start
**Description:** Start focus session
```json
{
  "user_id": "user_123",
  "duration": 25,
  "activity": "study"
}
```

#### POST /api/wellbeing/focus/end
**Description:** End focus session

#### GET /api/wellbeing/motivation/{user_id}
**Description:** Get motivation content

#### GET /api/wellbeing/distraction-guard/{user_id}
**Description:** Get distraction guard settings

---

## 📹 Videos & HOTS Endpoints

### Videos Endpoints
#### GET /api/videos/subject/{subject}
**Description:** Get videos by subject

#### GET /api/videos/topic/{topic_id}
**Description:** Get videos by topic

#### GET /api/videos/{video_id}
**Description:** Get specific video

#### GET /api/videos/search/youtube?query={query}&max_results={number}
**Description:** Search YouTube videos

#### GET /api/videos/youtube/{youtube_id}
**Description:** Get YouTube video details

#### POST /api/videos/curate
**Description:** Curate video content

### HOTS (Higher Order Thinking Skills) Endpoints
#### POST /api/hots/generate
**Description:** Generate HOTS question
```json
{
  "subject": "physics",
  "topic": "mechanics",
  "difficulty": "hard",
  "user_id": "user_123"
}
```

#### POST /api/hots/attempt
**Description:** Submit HOTS attempt

#### GET /api/hots/performance/{user_id}
**Description:** Get HOTS performance

#### GET /api/hots/topic/{topic_id}
**Description:** Get HOTS questions for topic

---

## 💬 Messages Endpoints

#### GET /api/messages/conversations?user_id={user_id}
**Description:** Get user conversations

#### GET /api/messages/conversations/{conversation_id}/messages
**Description:** Get conversation messages

#### POST /api/messages/send
**Description:** Send message
```json
{
  "conversation_id": "conv_123",
  "sender_id": "user_123",
  "content": "Hello there!",
  "message_type": "text"
}
```

#### POST /api/messages/messages/{message_id}/read
**Description:** Mark message as read

#### GET /api/messages/suggestions?user_id={user_id}
**Description:** Get message suggestions

#### POST /api/messages/improve
**Description:** Improve message content

---

## ⚡ Basic Endpoints

#### GET /
**Description:** Root endpoint - API status

#### GET /ready
**Description:** Readiness probe

#### GET /info
**Description:** API service information

#### GET /api/health
**Description:** Health check

#### GET /api/health/config
**Description:** Health configuration

---

## 📊 Dashboard Endpoints

#### GET /api/dashboard/{layout_id}
**Description:** Get dashboard layout

#### GET /api/dashboard/layouts
**Description:** Get available layouts

#### GET /api/dashboard/widget-data/{widget_id}
**Description:** Get widget data

#### POST /api/dashboard/control-action
**Description:** Execute dashboard control action

---

## 🔧 Content Management Endpoints

#### GET /api/content/list
**Description:** List all content

#### GET /api/content/{content_id}
**Description:** Get specific content

#### GET /api/content/preview/{content_id}
**Description:** Preview content

#### GET /api/content/open/{content_id}
**Description:** Open content

#### POST /api/content/upload
**Description:** Upload content

#### POST /api/content/upload/file
**Description:** Upload file

#### GET /api/content/folders
**Description:** Get content folders

#### GET /api/content/by-folder?folder_id={folder_id}
**Description:** Get content by folder

#### GET /api/content/status/{content_id}
**Description:** Get content status

#### POST /api/content/reindex
**Description:** Reindex content

#### GET /api/content/index-status
**Description:** Get indexing status

---

## 📝 Usage Notes

1. **Authentication:** Most endpoints require user authentication via `user_id` parameter
2. **Rate Limiting:** API has rate limiting enabled
3. **CORS:** Configured for frontend origins
4. **Error Handling:** All endpoints return structured error responses
5. **Pagination:** Use `limit` and `offset` parameters where available
6. **Filtering:** Many GET endpoints support filtering via query parameters

## 🔑 Common Query Parameters

- `user_id`: User identifier (required for most endpoints)
- `limit`: Maximum number of results (default varies by endpoint)
- `offset`: Number of results to skip (for pagination)
- `subject`: Filter by subject (mathematics, physics, chemistry, biology)
- `topic`: Filter by specific topic
- `days_back`: Number of days to look back (for historical data)
- `include_*`: Boolean flags to include/exclude certain data

## 📱 Frontend Integration Tips

1. **Use max_tokens=2000** for RAG queries to get complete responses
2. **Store session_id** from AI tutoring sessions for follow-up messages
3. **Implement polling** for long-running operations
4. **Cache** frequently accessed data like component library
5. **Handle errors gracefully** with fallback UI states
6. **Use bulk operations** when possible for better performance