# Frontend Integration Guide - Memory Intelligence & Notifications

## Fixed Issues

✅ **Smart Suggestions Endpoint**: Changed from GET to POST to match frontend expectations
✅ **Notes Endpoint**: Created missing `/api/notes` endpoint  
✅ **Notifications System**: Added complete notification system with dismiss functionality

## Updated API Endpoints

### 1. Smart Suggestions (Fixed - Now POST)
```javascript
// ✅ CORRECT - Now works with POST
const response = await fetch(`/api/context/smart-suggestions/${userId}?suggestion_type=next_action`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    current_context: {
      page: 'classroom',
      activity: 'quiz_creation'
    }
  })
});
```

### 2. Notes Endpoint (New)
```javascript
// ✅ Get user notes
const notes = await fetch(`/api/notes?user_id=${userId}&limit=50`);

// ✅ Create a note
const newNote = await fetch('/api/notes?user_id=' + userId, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    title: 'My Note',
    content: 'Note content here',
    subject: 'mathematics',
    topic: 'algebra'
  })
});
```

### 3. Notifications System (New)

#### Get Notifications
```javascript
const notifications = await fetch(`/api/notifications/${userId}`);
// Returns: { notifications: [...], unread_count: 2 }
```

#### Create Quiz Success Notification
```javascript
async function showQuizCreatedNotification(userId, quizId) {
  const response = await fetch(`/api/notifications/${userId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      type: 'success',
      title: 'Quiz Created Successfully!',
      message: 'Your quiz has been created and is ready for students.',
      action: {
        label: 'View Quiz',
        url: `/quiz/${quizId}`
      },
      auto_dismiss: false,  // Don't auto-dismiss, let user close it
      importance: 0.8
    })
  });
  return response.json();
}
```

#### Dismiss Notification (Close Button)
```javascript
async function dismissNotification(notificationId, userId) {
  const response = await fetch(`/api/notifications/${notificationId}/dismiss?user_id=${userId}`, {
    method: 'POST'
  });
  return response.json();
}
```

## React Component Example

```jsx
import React, { useState, useEffect } from 'react';

const NotificationSystem = ({ userId }) => {
  const [notifications, setNotifications] = useState([]);

  useEffect(() => {
    fetchNotifications();
  }, [userId]);

  const fetchNotifications = async () => {
    try {
      const response = await fetch(`/api/notifications/${userId}`);
      const data = await response.json();
      setNotifications(data.notifications || []);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  };

  const handleDismiss = async (notificationId) => {
    try {
      await fetch(`/api/notifications/${notificationId}/dismiss?user_id=${userId}`, {
        method: 'POST'
      });
      
      // Remove from local state
      setNotifications(prev => 
        prev.filter(notif => notif.id !== notificationId)
      );
    } catch (error) {
      console.error('Error dismissing notification:', error);
    }
  };

  const getNotificationStyle = (type) => {
    const baseStyle = "p-4 mb-3 rounded-lg border-l-4 relative";
    switch (type) {
      case 'success': return `${baseStyle} bg-green-50 border-green-400 text-green-800`;
      case 'error': return `${baseStyle} bg-red-50 border-red-400 text-red-800`;
      case 'warning': return `${baseStyle} bg-yellow-50 border-yellow-400 text-yellow-800`;
      default: return `${baseStyle} bg-blue-50 border-blue-400 text-blue-800`;
    }
  };

  return (
    <div className="fixed top-4 right-4 z-50 max-w-sm">
      {notifications.map((notification) => (
        <div key={notification.id} className={getNotificationStyle(notification.type)}>
          {/* Close Button */}
          <button
            onClick={() => handleDismiss(notification.id)}
            className="absolute top-2 right-2 text-gray-500 hover:text-gray-700"
          >
            ✕
          </button>
          
          {/* Notification Content */}
          <div className="pr-8">
            <h4 className="font-semibold">{notification.title}</h4>
            <p className="text-sm mt-1">{notification.message}</p>
            
            {/* Action Button */}
            {notification.action && (
              <button
                onClick={() => window.location.href = notification.action.url}
                className="mt-2 px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
              >
                {notification.action.label}
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default NotificationSystem;
```

## Vue.js Component Example

```vue
<template>
  <div class="notification-container">
    <div
      v-for="notification in notifications"
      :key="notification.id"
      :class="getNotificationClass(notification.type)"
      class="notification"
    >
      <!-- Close Button -->
      <button
        @click="dismissNotification(notification.id)"
        class="close-btn"
      >
        ✕
      </button>
      
      <!-- Content -->
      <div class="notification-content">
        <h4>{{ notification.title }}</h4>
        <p>{{ notification.message }}</p>
        
        <!-- Action Button -->
        <button
          v-if="notification.action"
          @click="handleAction(notification.action)"
          class="action-btn"
        >
          {{ notification.action.label }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'NotificationSystem',
  props: {
    userId: {
      type: String,
      required: true
    }
  },
  data() {
    return {
      notifications: []
    };
  },
  mounted() {
    this.fetchNotifications();
  },
  methods: {
    async fetchNotifications() {
      try {
        const response = await fetch(`/api/notifications/${this.userId}`);
        const data = await response.json();
        this.notifications = data.notifications || [];
      } catch (error) {
        console.error('Error fetching notifications:', error);
      }
    },
    
    async dismissNotification(notificationId) {
      try {
        await fetch(`/api/notifications/${notificationId}/dismiss?user_id=${this.userId}`, {
          method: 'POST'
        });
        
        this.notifications = this.notifications.filter(
          notif => notif.id !== notificationId
        );
      } catch (error) {
        console.error('Error dismissing notification:', error);
      }
    },
    
    getNotificationClass(type) {
      const classes = {
        success: 'notification-success',
        error: 'notification-error',
        warning: 'notification-warning',
        info: 'notification-info'
      };
      return classes[type] || classes.info;
    },
    
    handleAction(action) {
      if (action.url) {
        this.$router.push(action.url);
      }
    }
  }
};
</script>

<style scoped>
.notification-container {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 1000;
  max-width: 20rem;
}

.notification {
  position: relative;
  padding: 1rem;
  margin-bottom: 0.75rem;
  border-radius: 0.5rem;
  border-left: 4px solid;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.notification-success {
  background-color: #f0f9ff;
  border-left-color: #10b981;
  color: #065f46;
}

.notification-error {
  background-color: #fef2f2;
  border-left-color: #ef4444;
  color: #991b1b;
}

.close-btn {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  color: #6b7280;
}

.close-btn:hover {
  color: #374151;
}

.action-btn {
  margin-top: 0.5rem;
  padding: 0.25rem 0.75rem;
  background-color: #3b82f6;
  color: white;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  font-size: 0.875rem;
}

.action-btn:hover {
  background-color: #2563eb;
}
</style>
```

## Integration Steps

### 1. Add to Your Main App Component
```javascript
// In your main App.jsx or App.vue
import NotificationSystem from './components/NotificationSystem';

// Add to your render/template
<NotificationSystem userId={currentUserId} />
```

### 2. Trigger Notifications After Actions
```javascript
// After creating a quiz
async function createQuiz(quizData) {
  try {
    const quiz = await createQuizAPI(quizData);
    
    // Show success notification
    await fetch(`/api/notifications/${userId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: 'success',
        title: 'Quiz Created!',
        message: `Quiz "${quiz.title}" has been created successfully.`,
        action: {
          label: 'View Quiz',
          url: `/quiz/${quiz.id}`
        },
        auto_dismiss: false
      })
    });
    
  } catch (error) {
    // Show error notification
    await fetch(`/api/notifications/${userId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: 'error',
        title: 'Quiz Creation Failed',
        message: 'There was an error creating your quiz. Please try again.',
        auto_dismiss: true,
        dismiss_after: 8000
      })
    });
  }
}
```

### 3. Remember User Context
```javascript
// Remember when user creates a quiz
async function rememberQuizCreation(userId, quizData) {
  await fetch(`/api/context/remember?user_id=${userId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      type: 'interaction',
      content: {
        action: 'quiz_created',
        quiz_id: quizData.id,
        quiz_title: quizData.title,
        subject: quizData.subject,
        questions_count: quizData.questions.length
      },
      subject: quizData.subject,
      topic: quizData.topic,
      importance: 0.8,
      tags: ['quiz', 'creation', 'teacher_action'],
      source: 'quiz_creator',
      component: 'quiz_creation_form'
    })
  });
}
```

## Summary

✅ **Fixed Issues:**
- Smart suggestions endpoint now accepts POST requests
- Added missing notes endpoint
- Created comprehensive notification system with dismiss functionality

✅ **New Features:**
- Persistent notifications that survive page reloads
- Close button functionality for all notifications
- Different notification types (success, error, warning, info)
- Action buttons in notifications
- Auto-dismiss options
- Bulk mark as read functionality

The notification system will now properly show quiz creation messages and allow users to dismiss them with a close button. The messages are stored persistently so they won't vanish instantly and will be available until the user explicitly dismisses them.