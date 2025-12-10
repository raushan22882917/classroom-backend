# Magic Learn API Documentation

Magic Learn is a comprehensive AI-powered learning platform with three main tools for transforming educational content into interactive learning experiences.

## Overview

The Magic Learn API provides three core services:

1. **Image Reader** - Analyzes uploaded images and sketches with AI vision models
2. **DrawInAir** - Hand gesture recognition for air drawing and shape detection
3. **Plot Crafter** - Story-based learning with AI-generated visualizations

## Base URL

All endpoints are prefixed with `/api/magic-learn`

## Authentication

Currently, the API supports optional user tracking via `user_id` parameter. No authentication is required for basic usage.

---

## Image Reader API

### Analyze Image (Base64)

**POST** `/api/magic-learn/image-reader/analyze`

Analyze base64-encoded images with AI vision models.

#### Request Body

```json
{
  "image_data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
  "analysis_type": "mathematical",
  "custom_instructions": "Explain the mathematical concepts shown",
  "user_id": "user123"
}
```

#### Parameters

- `image_data` (string, required): Base64 encoded image data
- `analysis_type` (string, optional): Type of analysis to perform
  - `mathematical` - Mathematical equations and formulas
  - `scientific` - Scientific diagrams and charts  
  - `text_extraction` - Extract and analyze text content
  - `object_identification` - Identify objects and shapes
  - `general` - Comprehensive analysis (default)
- `custom_instructions` (string, optional): Custom analysis instructions
- `user_id` (string, optional): User ID for tracking

#### Response

```json
{
  "success": true,
  "analysis": "## Mathematical Analysis\n\n### Detected Elements\nI can see a quadratic equation...",
  "detected_elements": ["quadratic_equation", "mathematical_symbols"],
  "confidence_score": 0.92,
  "processing_time": 2.3,
  "analysis_type": "mathematical",
  "error": null
}
```

### Upload and Analyze Image

**POST** `/api/magic-learn/image-reader/upload`

Upload image files directly for analysis.

#### Request (Form Data)

- `file` (file, required): Image file (JPG, PNG, WEBP, max 10MB)
- `analysis_type` (string, optional): Analysis type (see above)
- `custom_instructions` (string, optional): Custom instructions
- `user_id` (string, optional): User ID for tracking

#### Response

Same as analyze endpoint above.

---

## DrawInAir API

### Recognize Gestures

**POST** `/api/magic-learn/draw-in-air/recognize`

Recognize shapes and patterns from hand gesture points.

#### Request Body

```json
{
  "gesture_points": [
    {
      "x": 100.5,
      "y": 200.3,
      "timestamp": "2024-12-10T10:30:00Z"
    },
    {
      "x": 105.2,
      "y": 205.1,
      "timestamp": "2024-12-10T10:30:00.1Z"
    }
  ],
  "canvas_width": 800,
  "canvas_height": 600,
  "user_id": "user123"
}
```

#### Parameters

- `gesture_points` (array, required): Array of gesture coordinate points
  - `x` (number): X coordinate
  - `y` (number): Y coordinate  
  - `timestamp` (string): ISO timestamp of the point
- `canvas_width` (number, required): Canvas width in pixels
- `canvas_height` (number, required): Canvas height in pixels
- `user_id` (string, optional): User ID for tracking

#### Response

```json
{
  "success": true,
  "recognized_shapes": [
    {
      "shape_type": "circle",
      "confidence": 0.89,
      "coordinates": [...],
      "properties": {
        "center_x": 150.0,
        "center_y": 200.0,
        "radius": 50.0,
        "area": 7853.98
      }
    }
  ],
  "interpretation": "## Gesture Recognition Results\n\n### Shape 1: Circle...",
  "suggestions": [
    "Explore circle properties: circumference = 2πr",
    "Learn about pi (π) and its significance"
  ],
  "error": null
}
```

---

## Plot Crafter API

### Generate Story

**POST** `/api/magic-learn/plot-crafter/generate`

Generate educational stories with AI-powered visualizations.

#### Request Body

```json
{
  "story_prompt": "A student discovers the golden ratio in nature",
  "educational_topic": "Mathematics - Golden Ratio",
  "target_age_group": "12-18",
  "story_length": "medium",
  "user_id": "user123"
}
```

#### Parameters

- `story_prompt` (string, required): Story prompt or theme
- `educational_topic` (string, optional): Educational topic to incorporate
- `target_age_group` (string, optional): Target age group (default: "12-18")
- `story_length` (string, optional): Story length - "short", "medium", "long" (default: "medium")
- `user_id` (string, optional): User ID for tracking

#### Response

```json
{
  "success": true,
  "story": {
    "title": "The Mathematical Adventure of Alex and the Golden Ratio",
    "content": "# The Mathematical Adventure...\n\n## Chapter 1...",
    "characters": [
      {
        "element_type": "protagonist",
        "name": "Alex",
        "description": "Curious student who discovers mathematical patterns",
        "properties": {
          "age": "16",
          "interests": ["mathematics", "nature"]
        }
      }
    ],
    "settings": [
      {
        "element_type": "location",
        "name": "School Garden",
        "description": "Where Alex discovers the sunflower pattern",
        "properties": {
          "atmosphere": "peaceful"
        }
      }
    ],
    "educational_elements": [
      "Golden Ratio (φ ≈ 1.618)",
      "Fibonacci Sequence",
      "Pattern Recognition"
    ],
    "learning_objectives": [
      "Understand the concept of the Golden Ratio",
      "Recognize mathematical patterns in nature"
    ]
  },
  "visualization_prompts": [
    "A curious student examining a sunflower with spiral seed patterns",
    "Mathematics classroom with golden ratio formula on blackboard"
  ],
  "interactive_elements": [
    {
      "type": "quiz",
      "title": "Golden Ratio Quiz",
      "questions": [...]
    },
    {
      "type": "activity", 
      "title": "Find the Golden Ratio",
      "description": "Measure rectangles around you..."
    }
  ],
  "error": null
}
```

---

## Utility Endpoints

### Health Check

**GET** `/api/magic-learn/health`

Check the health status of Magic Learn services.

#### Response

```json
{
  "status": "healthy",
  "services": {
    "image_reader": "active",
    "draw_in_air": "active",
    "plot_crafter": "active"
  },
  "timestamp": 1702201800.123
}
```

### Get Analytics

**GET** `/api/magic-learn/analytics`

Get usage analytics for the Magic Learn platform.

#### Response

```json
{
  "total_sessions": 1250,
  "image_reader_usage": 650,
  "draw_in_air_usage": 300,
  "plot_crafter_usage": 300,
  "average_processing_time": 2.5,
  "success_rate": 92.5,
  "popular_analysis_types": [
    {
      "type": "mathematical",
      "count": 45,
      "percentage": 35.0
    }
  ]
}
```

### Get Analysis Types

**GET** `/api/magic-learn/analysis-types`

Get available analysis types for the image reader.

#### Response

```json
{
  "analysis_types": [
    {
      "value": "mathematical",
      "label": "Mathematical Content",
      "description": "Analyze equations, formulas, and mathematical diagrams"
    },
    {
      "value": "scientific",
      "label": "Scientific Diagrams", 
      "description": "Analyze scientific charts, diagrams, and illustrations"
    }
  ]
}
```

### Get Examples

**GET** `/api/magic-learn/examples`

Get example use cases and sample content for Magic Learn tools.

#### Response

```json
{
  "image_reader_examples": [
    {
      "title": "Mathematical Equations",
      "description": "Upload sketches of quadratic equations...",
      "sample_instructions": "Explain the mathematical concepts..."
    }
  ],
  "draw_in_air_examples": [...],
  "plot_crafter_examples": [...]
}
```

### Submit Feedback

**POST** `/api/magic-learn/feedback`

Submit feedback for a Magic Learn session.

#### Request Body

```json
{
  "session_id": "session-uuid-123",
  "rating": 5,
  "feedback_text": "Great analysis of my math problem!",
  "user_id": "user123"
}
```

#### Parameters

- `session_id` (string, required): Session ID from previous API call
- `rating` (number, required): Rating from 1-5
- `feedback_text` (string, optional): Optional feedback text
- `user_id` (string, optional): User ID

#### Response

```json
{
  "success": true,
  "message": "Feedback submitted successfully",
  "session_id": "session-uuid-123"
}
```

---

## Error Handling

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": "Error message describing what went wrong",
  "analysis": "",
  "detected_elements": [],
  "confidence_score": 0.0,
  "processing_time": 0.0
}
```

### Common Error Codes

- `400 Bad Request` - Invalid input parameters
- `413 Payload Too Large` - Image file exceeds 10MB limit
- `415 Unsupported Media Type` - Invalid image format
- `500 Internal Server Error` - Server processing error

---

## Usage Examples

### JavaScript/TypeScript

```javascript
// Image Reader Example
const analyzeImage = async (imageFile) => {
  const formData = new FormData();
  formData.append('file', imageFile);
  formData.append('analysis_type', 'mathematical');
  formData.append('custom_instructions', 'Solve this equation step by step');
  
  const response = await fetch('/api/magic-learn/image-reader/upload', {
    method: 'POST',
    body: formData
  });
  
  return await response.json();
};

// DrawInAir Example
const recognizeGesture = async (gesturePoints, canvasSize) => {
  const response = await fetch('/api/magic-learn/draw-in-air/recognize', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      gesture_points: gesturePoints,
      canvas_width: canvasSize.width,
      canvas_height: canvasSize.height
    })
  });
  
  return await response.json();
};

// Plot Crafter Example
const generateStory = async (prompt, topic) => {
  const response = await fetch('/api/magic-learn/plot-crafter/generate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      story_prompt: prompt,
      educational_topic: topic,
      target_age_group: '12-18',
      story_length: 'medium'
    })
  });
  
  return await response.json();
};
```

### Python

```python
import requests
import base64

# Image Reader Example
def analyze_image(image_path, analysis_type='general'):
    with open(image_path, 'rb') as f:
        files = {'file': f}
        data = {
            'analysis_type': analysis_type,
            'custom_instructions': 'Explain the concepts shown'
        }
        
        response = requests.post(
            'http://localhost:8000/api/magic-learn/image-reader/upload',
            files=files,
            data=data
        )
        
    return response.json()

# DrawInAir Example  
def recognize_gesture(gesture_points, canvas_width, canvas_height):
    data = {
        'gesture_points': gesture_points,
        'canvas_width': canvas_width,
        'canvas_height': canvas_height
    }
    
    response = requests.post(
        'http://localhost:8000/api/magic-learn/draw-in-air/recognize',
        json=data
    )
    
    return response.json()

# Plot Crafter Example
def generate_story(prompt, topic=None):
    data = {
        'story_prompt': prompt,
        'educational_topic': topic,
        'target_age_group': '12-18',
        'story_length': 'medium'
    }
    
    response = requests.post(
        'http://localhost:8000/api/magic-learn/plot-crafter/generate',
        json=data
    )
    
    return response.json()
```

---

## Rate Limits

- **Image Reader**: 10 requests per minute per IP
- **DrawInAir**: 30 requests per minute per IP  
- **Plot Crafter**: 5 requests per minute per IP

Rate limits are enforced using the `slowapi` middleware and return `429 Too Many Requests` when exceeded.

---

## Best Practices

1. **Image Quality**: Upload clear, high-contrast images for better analysis
2. **File Size**: Keep images under 5MB for faster processing
3. **Gesture Smoothing**: Collect gesture points at consistent intervals (10-50ms)
4. **Error Handling**: Always check the `success` field in responses
5. **Feedback**: Submit feedback to help improve the AI models
6. **Caching**: Cache story content and analysis results when appropriate

---

## Support

For technical support or feature requests, please contact the development team or create an issue in the project repository.