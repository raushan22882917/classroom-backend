# Neo4j Knowledge Graph & Memory Intelligence API Endpoints

Base URL: `https://classroom-backend-121270846496.europe-west1.run.app`

## Memory Intelligence (MemMachine) Endpoints

### 1. Store Learning Session
- **POST** `/api/memory/store-session`
- **Query Parameters:**
  - `user_id` (required): User ID
- **Body:** Learning session data
- **Description:** Store a learning session in persistent memory

### 2. Get Learning History
- **GET** `/api/memory/learning-history/{user_id}`
- **Path Parameters:**
  - `user_id`: User ID
- **Description:** Retrieve user's learning history from memory

### 3. Analyze Learning Patterns
- **GET** `/api/memory/learning-patterns/{user_id}`
- **Path Parameters:**
  - `user_id`: User ID
- **Description:** Analyze user's learning patterns from persistent memory

### 4. Get Memory Statistics
- **GET** `/api/memory/stats`
- **Description:** Get statistics about memory usage and storage

## Neo4j Knowledge Graph Endpoints

### 1. Create Concept
- **POST** `/api/knowledge-graph/create-concept`
- **Query Parameters:**
  - `name` (required): Concept name
- **Description:** Create a new concept in the knowledge graph

### 2. Create Relationship
- **POST** `/api/knowledge-graph/create-relationship`
- **Query Parameters:**
  - `source_concept` (required): Source concept name
  - `target_concept` (required): Target concept name
  - `relationship_type` (required): Type of relationship
- **Description:** Create a relationship between two concepts

### 3. Find Learning Path
- **GET** `/api/knowledge-graph/learning-path/{user_id}`
- **Path Parameters:**
  - `user_id`: User ID
- **Query Parameters:**
  - `target_concept` (optional): Target concept to learn
- **Description:** Find optimal learning path for user

### 4. Get Learning Recommendations
- **GET** `/api/knowledge-graph/recommendations/{user_id}`
- **Path Parameters:**
  - `user_id`: User ID
- **Description:** Get personalized learning recommendations

### 5. Update User Progress
- **POST** `/api/knowledge-graph/update-progress`
- **Query Parameters:**
  - `user_id` (required): User ID
  - `concept_name` (required): Concept name
  - `mastery_level` (required): Mastery level (0.0-1.0)
- **Description:** Update user's progress on a concept

### 6. Get User Learning Stats
- **GET** `/api/knowledge-graph/user-stats/{user_id}`
- **Path Parameters:**
  - `user_id`: User ID
- **Description:** Get comprehensive learning statistics for a user

### 7. Get Concept Relationships
- **GET** `/api/knowledge-graph/concept-relationships/{concept_name}`
- **Path Parameters:**
  - `concept_name`: Concept name
- **Description:** Get all relationships for a specific concept

### 8. Analyze Knowledge Gaps
- **GET** `/api/knowledge-graph/knowledge-gaps/{user_id}`
- **Path Parameters:**
  - `user_id`: User ID
- **Description:** Analyze knowledge gaps and suggest improvements

### 9. Get Graph Statistics
- **GET** `/api/knowledge-graph/stats`
- **Description:** Get statistics about the knowledge graph

## Interactive Learning Endpoints

### 1. Create Interactive Session
- **POST** `/api/interactive/create-session`
- **Query Parameters:**
  - `user_id` (required): User ID
- **Description:** Create a new interactive learning session

### 2. Process Interaction
- **POST** `/api/interactive/process-interaction`
- **Query Parameters:**
  - `session_id` (required): Session ID
- **Description:** Process user interaction in learning session

### 3. Get Session Analytics
- **GET** `/api/interactive/session-analytics/{session_id}`
- **Path Parameters:**
  - `session_id`: Session ID
- **Description:** Get comprehensive analytics for a learning session

### 4. Get Component Library
- **GET** `/api/interactive/component-library`
- **Description:** Get the complete interactive component library

### 5. Create Visualization
- **POST** `/api/interactive/create-visualization`
- **Body:** Data for visualization
- **Description:** Create interactive visualizations

## Combined Intelligence Endpoints

### 1. Get Comprehensive User Profile
- **GET** `/api/intelligence/comprehensive-profile/{user_id}`
- **Path Parameters:**
  - `user_id`: User ID
- **Description:** Get comprehensive user profile combining memory and graph data

### 2. Smart Session Planning
- **POST** `/api/intelligence/smart-session-planning`
- **Query Parameters:**
  - `user_id` (required): User ID
- **Description:** Create intelligent learning session plans

## Enhanced AI Tutor Endpoints

### 1. Create AI Tutor Session
- **POST** `/api/ai-tutor/create-session`
- **Query Parameters:**
  - `user_id` (required): User ID
- **Description:** Create enhanced AI tutor session with memory integration

### 2. Send Message to AI Tutor
- **POST** `/api/ai-tutor/send-message`
- **Query Parameters:**
  - `session_id` (required): Session ID
- **Description:** Send message to enhanced AI tutor

### 3. Get Learning Insights
- **GET** `/api/ai-tutor/learning-insights/{user_id}`
- **Path Parameters:**
  - `user_id`: User ID
- **Description:** Get comprehensive learning insights combining MemMachine and Neo4j data

### 4. Create Interactive Session from Chat
- **POST** `/api/ai-tutor/create-interactive-session`
- **Query Parameters:**
  - `user_id` (required): User ID
- **Description:** Create interactive session from chat context

## Context & Long-term Memory Endpoints

### 1. Remember Context
- **POST** `/api/context/remember`
- **Query Parameters:**
  - `user_id` (required): User ID
- **Description:** Store context in long-term memory

### 2. Recall Context
- **GET** `/api/context/recall/{user_id}`
- **Path Parameters:**
  - `user_id`: User ID
- **Description:** Recall stored context from memory

### 3. Get Smart Suggestions
- **POST** `/api/context/smart-suggestions/{user_id}`
- **Path Parameters:**
  - `user_id`: User ID
- **Description:** Get smart context-aware suggestions

### 4. Bulk Remember Contexts
- **POST** `/api/context/bulk-remember`
- **Query Parameters:**
  - `user_id` (required): User ID
- **Description:** Store multiple contexts in bulk

### 5. Get User Timeline
- **GET** `/api/context/user-timeline/{user_id}`
- **Path Parameters:**
  - `user_id`: User ID
- **Description:** Get chronological timeline of user interactions

## Notification Endpoints

### 1. Get User Notifications
- **GET** `/api/notifications/{user_id}`
- **Path Parameters:**
  - `user_id`: User ID
- **Description:** Get notifications for user

### 2. Create Notification
- **POST** `/api/notifications/{user_id}`
- **Path Parameters:**
  - `user_id`: User ID
- **Description:** Create new notification

### 3. Dismiss Notification
- **POST** `/api/notifications/{notification_id}/dismiss`
- **Path Parameters:**
  - `notification_id`: Notification ID
- **Description:** Dismiss a specific notification

### 4. Mark All Notifications Read
- **POST** `/api/notifications/{user_id}/mark-all-read`
- **Path Parameters:**
  - `user_id`: User ID
- **Description:** Mark all notifications as read

## Notes Endpoints

### 1. Get User Notes
- **GET** `/api/notes`
- **Query Parameters:**
  - `user_id` (required): User ID
- **Description:** Get user's notes

### 2. Create Note
- **POST** `/api/notes`
- **Query Parameters:**
  - `user_id` (required): User ID
- **Description:** Create new note

### 3. Update Note
- **PUT** `/api/notes/{note_id}`
- **Path Parameters:**
  - `note_id`: Note ID
- **Description:** Update existing note

### 4. Delete Note
- **DELETE** `/api/notes/{note_id}`
- **Path Parameters:**
  - `note_id`: Note ID
- **Description:** Delete note

## Dashboard Endpoints

### 1. Get Dashboard HTML
- **GET** `/api/dashboard/{layout_id}`
- **Path Parameters:**
  - `layout_id`: Layout ID
- **Description:** Get dashboard HTML for specific layout

### 2. Get Widget Data
- **POST** `/api/dashboard/widget-data/{widget_id}`
- **Path Parameters:**
  - `widget_id`: Widget ID
- **Description:** Get data for specific widget

### 3. Handle Control Action
- **POST** `/api/dashboard/control-action`
- **Body:** Widget ID and action data
- **Description:** Handle dashboard control actions

### 4. Get Available Layouts
- **GET** `/api/dashboard/layouts`
- **Description:** Get list of available dashboard layouts

## Example Usage

```bash
# Create a concept in Neo4j
curl -X POST "https://classroom-backend-121270846496.europe-west1.run.app/api/knowledge-graph/create-concept?name=Calculus"

# Get learning recommendations
curl "https://classroom-backend-121270846496.europe-west1.run.app/api/knowledge-graph/recommendations/user123"

# Store learning session in memory
curl -X POST "https://classroom-backend-121270846496.europe-west1.run.app/api/memory/store-session?user_id=user123" \
  -H "Content-Type: application/json" \
  -d '{"session_data": "learning session details"}'

# Get comprehensive user profile
curl "https://classroom-backend-121270846496.europe-west1.run.app/api/intelligence/comprehensive-profile/user123"
```

## Authentication
Most endpoints require user authentication. Make sure to include proper authentication headers when making requests.

## Rate Limiting
The API has rate limiting in place. Check response headers for rate limit information.