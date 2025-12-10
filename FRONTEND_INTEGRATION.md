# Magic Learn Frontend Integration Guide

This guide shows how to integrate the Magic Learn backend with your frontend application.

## Quick Start

### 1. Basic Setup

```javascript
// API configuration
const API_BASE_URL = 'http://localhost:8000/api/magic-learn';

// Utility function for API calls
async function callMagicLearnAPI(endpoint, options = {}) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    ...options
  });
  
  if (!response.ok) {
    throw new Error(`API call failed: ${response.statusText}`);
  }
  
  return await response.json();
}
```

### 2. Image Reader Integration

```html
<!-- HTML -->
<div class="image-reader">
  <input type="file" id="imageInput" accept="image/*" />
  <select id="analysisType">
    <option value="general">General Analysis</option>
    <option value="mathematical">Mathematical</option>
    <option value="scientific">Scientific</option>
    <option value="text_extraction">Text Extraction</option>
    <option value="object_identification">Object Identification</option>
  </select>
  <textarea id="customInstructions" placeholder="Custom instructions (optional)"></textarea>
  <button onclick="analyzeImage()">Analyze Image</button>
  <div id="analysisResult"></div>
</div>
```

```javascript
// JavaScript
async function analyzeImage() {
  const fileInput = document.getElementById('imageInput');
  const analysisType = document.getElementById('analysisType').value;
  const customInstructions = document.getElementById('customInstructions').value;
  const resultDiv = document.getElementById('analysisResult');
  
  if (!fileInput.files[0]) {
    alert('Please select an image file');
    return;
  }
  
  // Show loading state
  resultDiv.innerHTML = '<div class="loading">🔄 Analyzing image...</div>';
  
  try {
    // Create form data
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('analysis_type', analysisType);
    if (customInstructions) {
      formData.append('custom_instructions', customInstructions);
    }
    
    // Call API
    const response = await fetch(`${API_BASE_URL}/image-reader/upload`, {
      method: 'POST',
      body: formData
    });
    
    const result = await response.json();
    
    if (result.success) {
      displayAnalysisResult(result);
    } else {
      resultDiv.innerHTML = `<div class="error">❌ ${result.error}</div>`;
    }
    
  } catch (error) {
    resultDiv.innerHTML = `<div class="error">❌ Error: ${error.message}</div>`;
  }
}

function displayAnalysisResult(result) {
  const resultDiv = document.getElementById('analysisResult');
  
  resultDiv.innerHTML = `
    <div class="analysis-result">
      <div class="confidence">
        <strong>Confidence:</strong> ${(result.confidence_score * 100).toFixed(1)}%
      </div>
      <div class="processing-time">
        <strong>Processing Time:</strong> ${result.processing_time.toFixed(2)}s
      </div>
      <div class="detected-elements">
        <strong>Detected Elements:</strong> ${result.detected_elements.join(', ')}
      </div>
      <div class="analysis-content">
        ${markdownToHtml(result.analysis)}
      </div>
    </div>
  `;
}

// Simple markdown to HTML converter (use a proper library in production)
function markdownToHtml(markdown) {
  return markdown
    .replace(/### (.*)/g, '<h3>$1</h3>')
    .replace(/## (.*)/g, '<h2>$1</h2>')
    .replace(/# (.*)/g, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>');
}
```

### 3. DrawInAir Integration

```html
<!-- HTML -->
<div class="draw-in-air">
  <canvas id="gestureCanvas" width="800" height="600"></canvas>
  <div class="controls">
    <button onclick="startDrawing()">Start Drawing</button>
    <button onclick="stopDrawing()">Stop Drawing</button>
    <button onclick="recognizeGesture()">Recognize Shapes</button>
    <button onclick="clearCanvas()">Clear</button>
  </div>
  <div id="gestureResult"></div>
</div>
```

```javascript
// JavaScript
class DrawInAirHandler {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.isDrawing = false;
    this.gesturePoints = [];
    this.setupCanvas();
  }
  
  setupCanvas() {
    this.canvas.addEventListener('mousedown', (e) => this.startGesture(e));
    this.canvas.addEventListener('mousemove', (e) => this.continueGesture(e));
    this.canvas.addEventListener('mouseup', () => this.endGesture());
    
    // Touch events for mobile
    this.canvas.addEventListener('touchstart', (e) => {
      e.preventDefault();
      const touch = e.touches[0];
      const mouseEvent = new MouseEvent('mousedown', {
        clientX: touch.clientX,
        clientY: touch.clientY
      });
      this.canvas.dispatchEvent(mouseEvent);
    });
    
    this.canvas.addEventListener('touchmove', (e) => {
      e.preventDefault();
      const touch = e.touches[0];
      const mouseEvent = new MouseEvent('mousemove', {
        clientX: touch.clientX,
        clientY: touch.clientY
      });
      this.canvas.dispatchEvent(mouseEvent);
    });
    
    this.canvas.addEventListener('touchend', (e) => {
      e.preventDefault();
      const mouseEvent = new MouseEvent('mouseup', {});
      this.canvas.dispatchEvent(mouseEvent);
    });
  }
  
  startGesture(e) {
    this.isDrawing = true;
    const rect = this.canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    this.gesturePoints = [{
      x: x,
      y: y,
      timestamp: new Date().toISOString()
    }];
    
    this.ctx.beginPath();
    this.ctx.moveTo(x, y);
  }
  
  continueGesture(e) {
    if (!this.isDrawing) return;
    
    const rect = this.canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    this.gesturePoints.push({
      x: x,
      y: y,
      timestamp: new Date().toISOString()
    });
    
    this.ctx.lineTo(x, y);
    this.ctx.stroke();
  }
  
  endGesture() {
    this.isDrawing = false;
  }
  
  async recognizeGesture() {
    if (this.gesturePoints.length < 3) {
      alert('Please draw something first');
      return;
    }
    
    const resultDiv = document.getElementById('gestureResult');
    resultDiv.innerHTML = '<div class="loading">🔄 Recognizing shapes...</div>';
    
    try {
      const result = await callMagicLearnAPI('/draw-in-air/recognize', {
        method: 'POST',
        body: JSON.stringify({
          gesture_points: this.gesturePoints,
          canvas_width: this.canvas.width,
          canvas_height: this.canvas.height
        })
      });
      
      if (result.success) {
        this.displayGestureResult(result);
      } else {
        resultDiv.innerHTML = `<div class="error">❌ ${result.error}</div>`;
      }
      
    } catch (error) {
      resultDiv.innerHTML = `<div class="error">❌ Error: ${error.message}</div>`;
    }
  }
  
  displayGestureResult(result) {
    const resultDiv = document.getElementById('gestureResult');
    
    let shapesHtml = '';
    result.recognized_shapes.forEach((shape, index) => {
      shapesHtml += `
        <div class="recognized-shape">
          <strong>Shape ${index + 1}:</strong> ${shape.shape_type} 
          (${(shape.confidence * 100).toFixed(1)}% confidence)
        </div>
      `;
    });
    
    let suggestionsHtml = '';
    result.suggestions.forEach(suggestion => {
      suggestionsHtml += `<li>${suggestion}</li>`;
    });
    
    resultDiv.innerHTML = `
      <div class="gesture-result">
        <div class="shapes">
          <h3>Recognized Shapes:</h3>
          ${shapesHtml}
        </div>
        <div class="interpretation">
          <h3>Interpretation:</h3>
          ${markdownToHtml(result.interpretation)}
        </div>
        <div class="suggestions">
          <h3>Learning Suggestions:</h3>
          <ul>${suggestionsHtml}</ul>
        </div>
      </div>
    `;
  }
  
  clearCanvas() {
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    this.gesturePoints = [];
    document.getElementById('gestureResult').innerHTML = '';
  }
}

// Initialize DrawInAir
const drawInAir = new DrawInAirHandler('gestureCanvas');

function startDrawing() {
  // Visual feedback that drawing mode is active
  document.getElementById('gestureCanvas').style.cursor = 'crosshair';
}

function stopDrawing() {
  drawInAir.isDrawing = false;
  document.getElementById('gestureCanvas').style.cursor = 'default';
}

function recognizeGesture() {
  drawInAir.recognizeGesture();
}

function clearCanvas() {
  drawInAir.clearCanvas();
}
```

### 4. Plot Crafter Integration

```html
<!-- HTML -->
<div class="plot-crafter">
  <div class="story-input">
    <textarea id="storyPrompt" placeholder="Enter your story prompt..." rows="3"></textarea>
    <input type="text" id="educationalTopic" placeholder="Educational topic (optional)" />
    <select id="targetAgeGroup">
      <option value="8-12">Ages 8-12</option>
      <option value="12-18" selected>Ages 12-18</option>
      <option value="18+">Ages 18+</option>
    </select>
    <select id="storyLength">
      <option value="short">Short</option>
      <option value="medium" selected>Medium</option>
      <option value="long">Long</option>
    </select>
    <button onclick="generateStory()">Generate Story</button>
  </div>
  <div id="storyResult"></div>
</div>
```

```javascript
// JavaScript
async function generateStory() {
  const storyPrompt = document.getElementById('storyPrompt').value;
  const educationalTopic = document.getElementById('educationalTopic').value;
  const targetAgeGroup = document.getElementById('targetAgeGroup').value;
  const storyLength = document.getElementById('storyLength').value;
  const resultDiv = document.getElementById('storyResult');
  
  if (!storyPrompt.trim()) {
    alert('Please enter a story prompt');
    return;
  }
  
  resultDiv.innerHTML = '<div class="loading">🔄 Generating story...</div>';
  
  try {
    const result = await callMagicLearnAPI('/plot-crafter/generate', {
      method: 'POST',
      body: JSON.stringify({
        story_prompt: storyPrompt,
        educational_topic: educationalTopic || null,
        target_age_group: targetAgeGroup,
        story_length: storyLength
      })
    });
    
    if (result.success) {
      displayStoryResult(result);
    } else {
      resultDiv.innerHTML = `<div class="error">❌ ${result.error}</div>`;
    }
    
  } catch (error) {
    resultDiv.innerHTML = `<div class="error">❌ Error: ${error.message}</div>`;
  }
}

function displayStoryResult(result) {
  const resultDiv = document.getElementById('storyResult');
  
  // Characters
  let charactersHtml = '';
  result.story.characters.forEach(character => {
    charactersHtml += `
      <div class="character">
        <strong>${character.name}</strong> (${character.element_type}): 
        ${character.description}
      </div>
    `;
  });
  
  // Educational elements
  let educationalHtml = '';
  result.story.educational_elements.forEach(element => {
    educationalHtml += `<span class="educational-tag">${element}</span>`;
  });
  
  // Interactive elements
  let interactiveHtml = '';
  result.interactive_elements.forEach((element, index) => {
    if (element.type === 'quiz') {
      interactiveHtml += `
        <div class="interactive-element quiz">
          <h4>📝 ${element.title}</h4>
          <button onclick="showQuiz(${index})">Take Quiz</button>
        </div>
      `;
    } else if (element.type === 'activity') {
      interactiveHtml += `
        <div class="interactive-element activity">
          <h4>🎯 ${element.title}</h4>
          <p>${element.description}</p>
        </div>
      `;
    }
  });
  
  resultDiv.innerHTML = `
    <div class="story-result">
      <div class="story-header">
        <h2>${result.story.title}</h2>
        <div class="story-meta">
          <div class="characters">
            <h3>Characters:</h3>
            ${charactersHtml}
          </div>
          <div class="educational-elements">
            <h3>Educational Concepts:</h3>
            ${educationalHtml}
          </div>
        </div>
      </div>
      
      <div class="story-content">
        <h3>Story:</h3>
        <div class="story-text">
          ${markdownToHtml(result.story.content)}
        </div>
      </div>
      
      <div class="interactive-elements">
        <h3>Interactive Elements:</h3>
        ${interactiveHtml}
      </div>
      
      <div class="visualization-prompts">
        <h3>Visualization Ideas:</h3>
        <ul>
          ${result.visualization_prompts.map(prompt => `<li>${prompt}</li>`).join('')}
        </ul>
      </div>
    </div>
  `;
  
  // Store interactive elements for later use
  window.currentStoryInteractives = result.interactive_elements;
}

function showQuiz(index) {
  const quiz = window.currentStoryInteractives[index];
  if (!quiz || quiz.type !== 'quiz') return;
  
  let quizHtml = `<div class="quiz-modal">
    <div class="quiz-content">
      <h3>${quiz.title}</h3>`;
  
  quiz.questions.forEach((question, qIndex) => {
    quizHtml += `
      <div class="question">
        <p><strong>Question ${qIndex + 1}:</strong> ${question.question}</p>
        <div class="options">
    `;
    
    question.options.forEach((option, oIndex) => {
      quizHtml += `
        <label>
          <input type="radio" name="q${qIndex}" value="${oIndex}">
          ${option}
        </label>
      `;
    });
    
    quizHtml += `</div></div>`;
  });
  
  quizHtml += `
      <button onclick="submitQuiz(${index})">Submit Quiz</button>
      <button onclick="closeQuiz()">Close</button>
    </div>
  </div>`;
  
  document.body.insertAdjacentHTML('beforeend', quizHtml);
}

function submitQuiz(index) {
  const quiz = window.currentStoryInteractives[index];
  let score = 0;
  
  quiz.questions.forEach((question, qIndex) => {
    const selected = document.querySelector(`input[name="q${qIndex}"]:checked`);
    if (selected && parseInt(selected.value) === question.correct) {
      score++;
    }
  });
  
  alert(`Quiz completed! Score: ${score}/${quiz.questions.length}`);
  closeQuiz();
}

function closeQuiz() {
  const modal = document.querySelector('.quiz-modal');
  if (modal) {
    modal.remove();
  }
}
```

### 5. CSS Styles

```css
/* Basic styles for Magic Learn components */
.magic-learn {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.image-reader, .draw-in-air, .plot-crafter {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.loading {
  text-align: center;
  padding: 20px;
  color: #007bff;
  font-weight: 500;
}

.error {
  background: #f8d7da;
  color: #721c24;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid #f5c6cb;
}

.analysis-result, .gesture-result, .story-result {
  background: white;
  border-radius: 8px;
  padding: 20px;
  margin-top: 16px;
  border: 1px solid #e9ecef;
}

.confidence, .processing-time {
  display: inline-block;
  margin-right: 20px;
  color: #6c757d;
  font-size: 14px;
}

.detected-elements {
  margin: 12px 0;
  color: #495057;
}

.analysis-content {
  margin-top: 16px;
  line-height: 1.6;
}

#gestureCanvas {
  border: 2px solid #dee2e6;
  border-radius: 8px;
  cursor: crosshair;
  background: white;
}

.controls {
  margin-top: 12px;
  display: flex;
  gap: 8px;
}

.controls button {
  background: #007bff;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.controls button:hover {
  background: #0056b3;
}

.recognized-shape {
  background: #e7f3ff;
  padding: 8px 12px;
  margin: 8px 0;
  border-radius: 6px;
  border-left: 4px solid #007bff;
}

.educational-tag {
  background: #28a745;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  margin-right: 8px;
  display: inline-block;
  margin-bottom: 4px;
}

.interactive-element {
  background: #fff3cd;
  border: 1px solid #ffeaa7;
  border-radius: 6px;
  padding: 12px;
  margin: 8px 0;
}

.quiz-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.quiz-content {
  background: white;
  padding: 24px;
  border-radius: 12px;
  max-width: 600px;
  max-height: 80vh;
  overflow-y: auto;
}

.question {
  margin-bottom: 20px;
}

.options label {
  display: block;
  margin: 8px 0;
  cursor: pointer;
}

.options input[type="radio"] {
  margin-right: 8px;
}

/* Responsive design */
@media (max-width: 768px) {
  .magic-learn {
    padding: 12px;
  }
  
  .image-reader, .draw-in-air, .plot-crafter {
    padding: 16px;
  }
  
  #gestureCanvas {
    width: 100%;
    height: 300px;
  }
  
  .controls {
    flex-wrap: wrap;
  }
}
```

### 6. Complete Integration Example

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Magic Learn - AI-Powered Learning Platform</title>
    <link rel="stylesheet" href="magic-learn.css">
</head>
<body>
    <div class="magic-learn">
        <header>
            <h1>🎯 Magic Learn</h1>
            <p>AI-powered learning platform with three interactive tools</p>
        </header>
        
        <nav class="tool-tabs">
            <button onclick="showTool('image-reader')" class="tab-button active">📸 Image Reader</button>
            <button onclick="showTool('draw-in-air')" class="tab-button">✋ DrawInAir</button>
            <button onclick="showTool('plot-crafter')" class="tab-button">📚 Plot Crafter</button>
        </nav>
        
        <!-- Image Reader Tool -->
        <div id="image-reader-tool" class="tool-panel active">
            <!-- Image Reader HTML from above -->
        </div>
        
        <!-- DrawInAir Tool -->
        <div id="draw-in-air-tool" class="tool-panel">
            <!-- DrawInAir HTML from above -->
        </div>
        
        <!-- Plot Crafter Tool -->
        <div id="plot-crafter-tool" class="tool-panel">
            <!-- Plot Crafter HTML from above -->
        </div>
    </div>
    
    <script src="magic-learn.js"></script>
</body>
</html>
```

```javascript
// Tool switching functionality
function showTool(toolName) {
  // Hide all tool panels
  document.querySelectorAll('.tool-panel').forEach(panel => {
    panel.classList.remove('active');
  });
  
  // Remove active class from all tabs
  document.querySelectorAll('.tab-button').forEach(button => {
    button.classList.remove('active');
  });
  
  // Show selected tool panel
  document.getElementById(`${toolName}-tool`).classList.add('active');
  
  // Add active class to selected tab
  event.target.classList.add('active');
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
  console.log('🚀 Magic Learn initialized');
  
  // Initialize DrawInAir when the page loads
  if (document.getElementById('gestureCanvas')) {
    window.drawInAir = new DrawInAirHandler('gestureCanvas');
  }
  
  // Check API health
  checkAPIHealth();
});

async function checkAPIHealth() {
  try {
    const health = await callMagicLearnAPI('/health');
    console.log('✅ Magic Learn API is healthy:', health);
  } catch (error) {
    console.error('❌ Magic Learn API is not available:', error);
    // Show user-friendly message
    document.body.insertAdjacentHTML('afterbegin', `
      <div class="api-warning">
        ⚠️ Magic Learn services are currently unavailable. Please try again later.
      </div>
    `);
  }
}
```

## Production Considerations

### 1. Error Handling
- Implement comprehensive error handling for network failures
- Show user-friendly error messages
- Add retry mechanisms for failed requests

### 2. Performance Optimization
- Implement image compression before upload
- Add loading states and progress indicators
- Cache analysis results when appropriate

### 3. Security
- Validate file types and sizes on the frontend
- Implement rate limiting on the frontend
- Sanitize user inputs

### 4. Accessibility
- Add proper ARIA labels
- Ensure keyboard navigation works
- Provide alternative text for images

### 5. Mobile Support
- Optimize touch interactions for DrawInAir
- Implement responsive design
- Test on various devices and screen sizes

This integration guide provides a complete foundation for building a Magic Learn frontend that works seamlessly with the backend API.