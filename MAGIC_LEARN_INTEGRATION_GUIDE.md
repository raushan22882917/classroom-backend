# Magic Learn Frontend Integration Guide

## 🚀 Quick Start Integration

Magic Learn provides three powerful AI tools:
1. **Image Reader** - Upload and analyze images with AI
2. **DrawInAir** - Hand gesture drawing with MediaPipe
3. **Plot Crafter** - AI story generation

## 📋 Prerequisites

1. Backend deployed at: `https://classroom-backend-821372121985.us-central1.run.app`
2. CORS configured for `http://localhost:8080`
3. Frontend running on `http://localhost:8080`

## 🔧 Basic Setup

### 1. API Configuration

```javascript
// config/api.js
const API_BASE_URL = 'https://classroom-backend-821372121985.us-central1.run.app/api/magic-learn';

// API utility function
async function callMagicLearnAPI(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    ...options
  };

  try {
    console.log(`🌐 Calling: ${url}`);
    const response = await fetch(url, defaultOptions);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log(`✅ Response:`, data);
    return data;
  } catch (error) {
    console.error(`❌ API Error:`, error);
    throw error;
  }
}

// Test CORS connection
async function testConnection() {
  try {
    const result = await callMagicLearnAPI('/health');
    console.log('🎉 Magic Learn connection successful!', result);
    return true;
  } catch (error) {
    console.error('💥 Magic Learn connection failed:', error);
    return false;
  }
}

export { callMagicLearnAPI, testConnection, API_BASE_URL };
```

### 2. Test Connection First

```html
<!-- test.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Magic Learn Connection Test</title>
</head>
<body>
    <h1>Magic Learn Connection Test</h1>
    <button onclick="testConnection()">Test Connection</button>
    <div id="result"></div>

    <script>
        async function testConnection() {
            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = '🔄 Testing connection...';
            
            try {
                const response = await fetch('https://classroom-backend-821372121985.us-central1.run.app/api/magic-learn/health');
                const data = await response.json();
                
                resultDiv.innerHTML = `
                    <div style="color: green;">
                        ✅ Connection Successful!<br>
                        Status: ${data.status}<br>
                        Services: ${Object.keys(data.services).join(', ')}
                    </div>
                `;
            } catch (error) {
                resultDiv.innerHTML = `
                    <div style="color: red;">
                        ❌ Connection Failed!<br>
                        Error: ${error.message}
                    </div>
                `;
            }
        }
    </script>
</body>
</html>
```

## 🖼️ Image Reader Integration

### Complete Image Reader Component

```html
<!-- image-reader.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Magic Learn - Image Reader</title>
    <style>
        .container { max-width: 800px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif; }
        .upload-area { border: 2px dashed #ccc; padding: 40px; text-align: center; margin: 20px 0; border-radius: 8px; }
        .upload-area.dragover { border-color: #007bff; background-color: #f8f9fa; }
        .analysis-result { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .loading { text-align: center; color: #007bff; }
        .error { background: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px; }
        .success { background: #d4edda; color: #155724; padding: 15px; border-radius: 5px; }
        button { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
        button:hover { background: #0056b3; }
        button:disabled { background: #6c757d; cursor: not-allowed; }
        select, textarea { width: 100%; padding: 8px; margin: 5px 0; border: 1px solid #ddd; border-radius: 4px; }
        .preview-image { max-width: 300px; max-height: 300px; border-radius: 8px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🖼️ Magic Learn - Image Reader</h1>
        
        <!-- Upload Area -->
        <div class="upload-area" id="uploadArea">
            <p>📁 Drag and drop an image here, or click to select</p>
            <input type="file" id="imageInput" accept="image/*" style="display: none;">
            <button onclick="document.getElementById('imageInput').click()">Choose Image</button>
        </div>
        
        <!-- Preview -->
        <div id="imagePreview"></div>
        
        <!-- Analysis Options -->
        <div>
            <label>Analysis Type:</label>
            <select id="analysisType">
                <option value="general">General Analysis</option>
                <option value="mathematical">Mathematical Content</option>
                <option value="scientific">Scientific Diagrams</option>
                <option value="text_extraction">Text Extraction</option>
                <option value="object_identification">Object Identification</option>
            </select>
        </div>
        
        <div>
            <label>Custom Instructions (optional):</label>
            <textarea id="customInstructions" rows="3" placeholder="e.g., 'Solve this equation step by step' or 'Explain the scientific concepts shown'"></textarea>
        </div>
        
        <button id="analyzeBtn" onclick="analyzeImage()" disabled>🔍 Analyze Image</button>
        
        <!-- Results -->
        <div id="analysisResult"></div>
    </div>

    <script>
        const API_BASE_URL = 'https://classroom-backend-821372121985.us-central1.run.app/api/magic-learn';
        let selectedFile = null;

        // Setup drag and drop
        const uploadArea = document.getElementById('uploadArea');
        const imageInput = document.getElementById('imageInput');
        const analyzeBtn = document.getElementById('analyzeBtn');

        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFileSelect(files[0]);
            }
        });

        uploadArea.addEventListener('click', () => {
            imageInput.click();
        });

        imageInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFileSelect(e.target.files[0]);
            }
        });

        function handleFileSelect(file) {
            if (!file.type.startsWith('image/')) {
                showError('Please select an image file');
                return;
            }

            if (file.size > 10 * 1024 * 1024) { // 10MB limit
                showError('Image size must be less than 10MB');
                return;
            }

            selectedFile = file;
            
            // Show preview
            const reader = new FileReader();
            reader.onload = (e) => {
                document.getElementById('imagePreview').innerHTML = `
                    <img src="${e.target.result}" class="preview-image" alt="Preview">
                    <p>📁 ${file.name} (${(file.size / 1024).toFixed(1)} KB)</p>
                `;
            };
            reader.readAsDataURL(file);

            analyzeBtn.disabled = false;
        }

        async function analyzeImage() {
            if (!selectedFile) {
                showError('Please select an image first');
                return;
            }

            const analysisType = document.getElementById('analysisType').value;
            const customInstructions = document.getElementById('customInstructions').value;
            const resultDiv = document.getElementById('analysisResult');

            // Show loading
            resultDiv.innerHTML = '<div class="loading">🔄 Analyzing image with AI...</div>';
            analyzeBtn.disabled = true;

            try {
                // Create form data
                const formData = new FormData();
                formData.append('file', selectedFile);
                formData.append('analysis_type', analysisType);
                if (customInstructions) {
                    formData.append('custom_instructions', customInstructions);
                }

                // Call API
                const response = await fetch(`${API_BASE_URL}/image-reader/upload`, {
                    method: 'POST',
                    body: formData
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const result = await response.json();

                if (result.success) {
                    displayAnalysisResult(result);
                } else {
                    showError(result.error || 'Analysis failed');
                }

            } catch (error) {
                console.error('Analysis error:', error);
                showError(`Analysis failed: ${error.message}`);
            } finally {
                analyzeBtn.disabled = false;
            }
        }

        function displayAnalysisResult(result) {
            const resultDiv = document.getElementById('analysisResult');
            
            resultDiv.innerHTML = `
                <div class="analysis-result">
                    <h3>📊 Analysis Results</h3>
                    
                    <div style="display: flex; gap: 20px; margin-bottom: 15px;">
                        <div><strong>Confidence:</strong> ${(result.confidence_score * 100).toFixed(1)}%</div>
                        <div><strong>Processing Time:</strong> ${result.processing_time.toFixed(2)}s</div>
                        <div><strong>Type:</strong> ${result.analysis_type}</div>
                    </div>
                    
                    <div><strong>Detected Elements:</strong> ${result.detected_elements.join(', ')}</div>
                    
                    <div style="margin-top: 20px;">
                        <h4>🎯 AI Analysis:</h4>
                        <div style="background: white; padding: 15px; border-radius: 5px; border-left: 4px solid #007bff;">
                            ${formatMarkdown(result.analysis)}
                        </div>
                    </div>
                </div>
            `;
        }

        function formatMarkdown(text) {
            return text
                .replace(/### (.*)/g, '<h4>$1</h4>')
                .replace(/## (.*)/g, '<h3>$1</h3>')
                .replace(/# (.*)/g, '<h2>$1</h2>')
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/\n/g, '<br>');
        }

        function showError(message) {
            document.getElementById('analysisResult').innerHTML = `
                <div class="error">❌ ${message}</div>
            `;
        }

        // Test connection on load
        window.addEventListener('load', async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/health`);
                const data = await response.json();
                console.log('✅ Magic Learn connected:', data);
            } catch (error) {
                console.error('❌ Magic Learn connection failed:', error);
                showError('Backend connection failed. Please check if the server is running.');
            }
        });
    </script>
</body>
</html>
```

## ✋ DrawInAir Integration

### Complete DrawInAir Component

```html
<!-- draw-in-air.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Magic Learn - DrawInAir</title>
    <style>
        .container { max-width: 1000px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif; }
        .video-container { position: relative; display: inline-block; }
        #videoElement { width: 640px; height: 480px; border: 2px solid #ddd; border-radius: 8px; }
        #canvas { position: absolute; top: 0; left: 0; pointer-events: none; }
        .controls { margin: 20px 0; display: flex; gap: 10px; flex-wrap: wrap; }
        button { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; }
        button:hover { background: #0056b3; }
        button:disabled { background: #6c757d; cursor: not-allowed; }
        .gesture-info { background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0; }
        .gesture-display { font-size: 24px; font-weight: bold; color: #007bff; }
        .instructions { background: #e7f3ff; padding: 15px; border-radius: 8px; margin: 20px 0; }
        .analysis-result { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .error { background: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>✋ Magic Learn - DrawInAir</h1>
        
        <div class="instructions">
            <h3>🎯 Hand Gestures:</h3>
            <ul>
                <li><strong>Drawing:</strong> Thumb + Index finger extended</li>
                <li><strong>Moving:</strong> Thumb + Index + Middle finger extended</li>
                <li><strong>Erasing:</strong> Thumb + Middle finger extended</li>
                <li><strong>Clearing:</strong> Thumb + Pinky finger extended</li>
                <li><strong>Analyzing:</strong> Index + Middle finger extended (no thumb)</li>
            </ul>
        </div>
        
        <div class="video-container">
            <video id="videoElement" autoplay muted></video>
            <canvas id="canvas" width="640" height="480"></canvas>
        </div>
        
        <div class="controls">
            <button id="startBtn" onclick="startDrawInAir()">🚀 Start DrawInAir</button>
            <button id="stopBtn" onclick="stopDrawInAir()" disabled>⏹️ Stop</button>
            <button id="clearBtn" onclick="clearCanvas()">🧹 Clear Canvas</button>
            <button id="analyzeBtn" onclick="analyzeDrawing()">🔍 Analyze Drawing</button>
        </div>
        
        <div class="gesture-info">
            <div>Current Gesture: <span id="currentGesture" class="gesture-display">None</span></div>
            <div id="gestureDetails"></div>
        </div>
        
        <div id="analysisResult"></div>
    </div>

    <script>
        const API_BASE_URL = 'https://classroom-backend-821372121985.us-central1.run.app/api/magic-learn';
        
        let videoElement = document.getElementById('videoElement');
        let canvas = document.getElementById('canvas');
        let ctx = canvas.getContext('2d');
        let mediaStream = null;
        let isRunning = false;
        let animationFrame = null;

        async function startDrawInAir() {
            try {
                // Start backend session
                const sessionResult = await fetch(`${API_BASE_URL}/draw-in-air/start`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                
                if (!sessionResult.ok) {
                    throw new Error('Failed to start backend session');
                }

                // Get user media
                mediaStream = await navigator.mediaDevices.getUserMedia({ 
                    video: { width: 640, height: 480 } 
                });
                
                videoElement.srcObject = mediaStream;
                isRunning = true;
                
                // Update UI
                document.getElementById('startBtn').disabled = true;
                document.getElementById('stopBtn').disabled = false;
                
                // Start processing loop
                processVideoFrame();
                
                console.log('✅ DrawInAir started successfully');
                
            } catch (error) {
                console.error('❌ Failed to start DrawInAir:', error);
                showError(`Failed to start: ${error.message}`);
            }
        }

        async function processVideoFrame() {
            if (!isRunning || !mediaStream) return;

            try {
                // Capture frame from video
                const tempCanvas = document.createElement('canvas');
                tempCanvas.width = 640;
                tempCanvas.height = 480;
                const tempCtx = tempCanvas.getContext('2d');
                tempCtx.drawImage(videoElement, 0, 0, 640, 480);
                
                // Convert to base64
                const frameData = tempCanvas.toDataURL('image/jpeg', 0.8);
                
                // Send to backend for processing
                const response = await fetch(`${API_BASE_URL}/draw-in-air/process-frame`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ frame: frameData })
                });

                if (response.ok) {
                    const result = await response.json();
                    
                    if (result.success) {
                        // Update gesture display
                        document.getElementById('currentGesture').textContent = result.gesture || 'None';
                        
                        // Display processed frame with hand tracking
                        if (result.frame) {
                            const img = new Image();
                            img.onload = () => {
                                ctx.clearRect(0, 0, canvas.width, canvas.height);
                                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                            };
                            img.src = result.frame;
                        }
                        
                        // Show gesture info
                        if (result.gesture_info) {
                            document.getElementById('gestureDetails').innerHTML = `
                                <small>Detected: ${result.gesture_info.detected || 'None'} | 
                                Confidence: ${(result.gesture_info.confidence * 100).toFixed(1)}%</small>
                            `;
                        }
                    }
                }
                
            } catch (error) {
                console.error('Frame processing error:', error);
            }

            // Continue processing
            if (isRunning) {
                animationFrame = requestAnimationFrame(() => {
                    setTimeout(processVideoFrame, 100); // ~10 FPS
                });
            }
        }

        async function stopDrawInAir() {
            try {
                isRunning = false;
                
                if (animationFrame) {
                    cancelAnimationFrame(animationFrame);
                }
                
                if (mediaStream) {
                    mediaStream.getTracks().forEach(track => track.stop());
                    mediaStream = null;
                }
                
                videoElement.srcObject = null;
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                
                // Stop backend session
                await fetch(`${API_BASE_URL}/draw-in-air/stop`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                
                // Update UI
                document.getElementById('startBtn').disabled = false;
                document.getElementById('stopBtn').disabled = true;
                document.getElementById('currentGesture').textContent = 'None';
                document.getElementById('gestureDetails').innerHTML = '';
                
                console.log('✅ DrawInAir stopped');
                
            } catch (error) {
                console.error('❌ Failed to stop DrawInAir:', error);
            }
        }

        async function clearCanvas() {
            try {
                const response = await fetch(`${API_BASE_URL}/draw-in-air/clear`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                
                if (response.ok) {
                    console.log('✅ Canvas cleared');
                }
            } catch (error) {
                console.error('❌ Failed to clear canvas:', error);
            }
        }

        async function analyzeDrawing() {
            try {
                // Capture current canvas
                const imageData = canvas.toDataURL('image/png');
                
                document.getElementById('analysisResult').innerHTML = 
                    '<div style="text-align: center; color: #007bff;">🔄 Analyzing drawing...</div>';
                
                const response = await fetch(`${API_BASE_URL}/draw-in-air/analyze`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ image: imageData })
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const result = await response.json();
                
                if (result.success) {
                    document.getElementById('analysisResult').innerHTML = `
                        <div class="analysis-result">
                            <h3>🎯 Drawing Analysis</h3>
                            <div style="background: white; padding: 15px; border-radius: 5px; border-left: 4px solid #007bff;">
                                ${formatMarkdown(result.result)}
                            </div>
                        </div>
                    `;
                } else {
                    showError(result.error || 'Analysis failed');
                }
                
            } catch (error) {
                console.error('❌ Analysis failed:', error);
                showError(`Analysis failed: ${error.message}`);
            }
        }

        function formatMarkdown(text) {
            return text
                .replace(/### (.*)/g, '<h4>$1</h4>')
                .replace(/## (.*)/g, '<h3>$1</h3>')
                .replace(/# (.*)/g, '<h2>$1</h2>')
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/\n/g, '<br>');
        }

        function showError(message) {
            document.getElementById('analysisResult').innerHTML = `
                <div class="error">❌ ${message}</div>
            `;
        }

        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            if (isRunning) {
                stopDrawInAir();
            }
        });
    </script>
</body>
</html>
```

## 📚 Plot Crafter Integration

### Complete Plot Crafter Component

```html
<!-- plot-crafter.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Magic Learn - Plot Crafter</title>
    <style>
        .container { max-width: 800px; margin: 0 auto; padding: 20px; font-family: Arial, sans-serif; }
        .form-group { margin: 15px 0; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input, select, textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 14px; }
        textarea { resize: vertical; min-height: 100px; }
        button { background: #007bff; color: white; border: none; padding: 12px 24px; border-radius: 5px; cursor: pointer; font-size: 16px; }
        button:hover { background: #0056b3; }
        button:disabled { background: #6c757d; cursor: not-allowed; }
        .story-result { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .story-content { background: white; padding: 20px; border-radius: 5px; border-left: 4px solid #007bff; line-height: 1.6; }
        .story-meta { display: flex; gap: 20px; margin-bottom: 15px; flex-wrap: wrap; }
        .meta-item { background: #e7f3ff; padding: 8px 12px; border-radius: 4px; font-size: 14px; }
        .loading { text-align: center; color: #007bff; padding: 20px; }
        .error { background: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px; }
        .examples { background: #e7f3ff; padding: 15px; border-radius: 8px; margin: 20px 0; }
        .example-item { margin: 10px 0; padding: 10px; background: white; border-radius: 4px; cursor: pointer; }
        .example-item:hover { background: #f0f8ff; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 Magic Learn - Plot Crafter</h1>
        <p>Generate educational stories with AI-powered visualizations</p>
        
        <div class="examples">
            <h3>💡 Example Prompts:</h3>
            <div class="example-item" onclick="useExample('A student discovers the golden ratio in nature while studying sunflower patterns', 'Mathematics - Golden Ratio and Fibonacci')">
                🌻 <strong>Golden Ratio Discovery:</strong> A student discovers the golden ratio in nature while studying sunflower patterns
            </div>
            <div class="example-item" onclick="useExample('A young scientist uses chemistry to solve a mystery in their school lab', 'Chemistry - Chemical Reactions')">
                🧪 <strong>Chemistry Mystery:</strong> A young scientist uses chemistry to solve a mystery in their school lab
            </div>
            <div class="example-item" onclick="useExample('Time travelers visit ancient Egypt to learn about pyramid construction', 'History - Ancient Civilizations')">
                🏺 <strong>Ancient Egypt Adventure:</strong> Time travelers visit ancient Egypt to learn about pyramid construction
            </div>
        </div>
        
        <form id="storyForm">
            <div class="form-group">
                <label for="storyPrompt">Story Prompt *</label>
                <textarea id="storyPrompt" placeholder="Describe the story you want to create..." required></textarea>
            </div>
            
            <div class="form-group">
                <label for="educationalTopic">Educational Topic</label>
                <input type="text" id="educationalTopic" placeholder="e.g., Mathematics - Algebra, Science - Physics, History - World War II">
            </div>
            
            <div class="form-group">
                <label for="targetAgeGroup">Target Age Group</label>
                <select id="targetAgeGroup">
                    <option value="8-12">Ages 8-12</option>
                    <option value="12-18" selected>Ages 12-18</option>
                    <option value="18+">Ages 18+</option>
                </select>
            </div>
            
            <div class="form-group">
                <label for="storyLength">Story Length</label>
                <select id="storyLength">
                    <option value="short">Short (1-2 paragraphs)</option>
                    <option value="medium" selected>Medium (3-5 paragraphs)</option>
                    <option value="long">Long (Full story)</option>
                </select>
            </div>
            
            <button type="submit">✨ Generate Story</button>
        </form>
        
        <div id="storyResult"></div>
    </div>

    <script>
        const API_BASE_URL = 'https://classroom-backend-821372121985.us-central1.run.app/api/magic-learn';

        document.getElementById('storyForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            await generateStory();
        });

        function useExample(prompt, topic) {
            document.getElementById('storyPrompt').value = prompt;
            document.getElementById('educationalTopic').value = topic;
        }

        async function generateStory() {
            const storyPrompt = document.getElementById('storyPrompt').value.trim();
            const educationalTopic = document.getElementById('educationalTopic').value.trim();
            const targetAgeGroup = document.getElementById('targetAgeGroup').value;
            const storyLength = document.getElementById('storyLength').value;
            const resultDiv = document.getElementById('storyResult');

            if (!storyPrompt) {
                showError('Please enter a story prompt');
                return;
            }

            // Show loading
            resultDiv.innerHTML = '<div class="loading">🔄 Generating your educational story with AI...</div>';

            try {
                const response = await fetch(`${API_BASE_URL}/plot-crafter/generate`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        story_prompt: storyPrompt,
                        educational_topic: educationalTopic || null,
                        target_age_group: targetAgeGroup,
                        story_length: storyLength
                    })
                });

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }

                const result = await response.json();

                if (result.success) {
                    displayStoryResult(result);
                } else {
                    showError(result.error || 'Story generation failed');
                }

            } catch (error) {
                console.error('Story generation error:', error);
                showError(`Story generation failed: ${error.message}`);
            }
        }

        function displayStoryResult(result) {
            const story = result.story;
            const resultDiv = document.getElementById('storyResult');

            // Characters
            let charactersHtml = '';
            if (story.characters && story.characters.length > 0) {
                charactersHtml = story.characters.map(char => 
                    `<div class="meta-item">👤 ${char.name} (${char.element_type})</div>`
                ).join('');
            }

            // Educational elements
            let educationalHtml = '';
            if (story.educational_elements && story.educational_elements.length > 0) {
                educationalHtml = story.educational_elements.map(element => 
                    `<div class="meta-item">🎯 ${element}</div>`
                ).join('');
            }

            // Learning objectives
            let objectivesHtml = '';
            if (story.learning_objectives && story.learning_objectives.length > 0) {
                objectivesHtml = `
                    <h4>📋 Learning Objectives:</h4>
                    <ul>
                        ${story.learning_objectives.map(obj => `<li>${obj}</li>`).join('')}
                    </ul>
                `;
            }

            // Visualization prompts
            let visualizationHtml = '';
            if (result.visualization_prompts && result.visualization_prompts.length > 0) {
                visualizationHtml = `
                    <h4>🎨 Visualization Ideas:</h4>
                    <ul>
                        ${result.visualization_prompts.map(prompt => `<li>${prompt}</li>`).join('')}
                    </ul>
                `;
            }

            // Interactive elements
            let interactiveHtml = '';
            if (result.interactive_elements && result.interactive_elements.length > 0) {
                interactiveHtml = `
                    <h4>🎮 Interactive Elements:</h4>
                    ${result.interactive_elements.map(element => `
                        <div style="background: #fff3cd; padding: 10px; margin: 5px 0; border-radius: 4px;">
                            <strong>${element.type.toUpperCase()}:</strong> ${element.title || element.description}
                        </div>
                    `).join('')}
                `;
            }

            resultDiv.innerHTML = `
                <div class="story-result">
                    <h2>📖 ${story.title}</h2>
                    
                    <div class="story-meta">
                        ${charactersHtml}
                        ${educationalHtml}
                    </div>
                    
                    <div class="story-content">
                        ${formatMarkdown(story.content)}
                    </div>
                    
                    ${objectivesHtml}
                    ${visualizationHtml}
                    ${interactiveHtml}
                </div>
            `;
        }

        function formatMarkdown(text) {
            return text
                .replace(/### (.*)/g, '<h4>$1</h4>')
                .replace(/## (.*)/g, '<h3>$1</h3>')
                .replace(/# (.*)/g, '<h2>$1</h2>')
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/\n\n/g, '</p><p>')
                .replace(/\n/g, '<br>')
                .replace(/^/, '<p>')
                .replace(/$/, '</p>');
        }

        function showError(message) {
            document.getElementById('storyResult').innerHTML = `
                <div class="error">❌ ${message}</div>
            `;
        }

        // Test connection on load
        window.addEventListener('load', async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/health`);
                const data = await response.json();
                console.log('✅ Plot Crafter connected:', data);
            } catch (error) {
                console.error('❌ Plot Crafter connection failed:', error);
            }
        });
    </script>
</body>
</html>
```

## 🎯 Complete Integration Example

### Main Magic Learn Dashboard

```html
<!-- magic-learn-dashboard.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Magic Learn - AI Learning Platform</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px 0; text-align: center; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .tools-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; margin: 30px 0; }
        .tool-card { background: white; border-radius: 12px; padding: 24px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: transform 0.2s; }
        .tool-card:hover { transform: translateY(-2px); box-shadow: 0 8px 15px rgba(0,0,0,0.15); }
        .tool-icon { font-size: 48px; margin-bottom: 15px; }
        .tool-title { font-size: 24px; font-weight: bold; margin-bottom: 10px; color: #333; }
        .tool-description { color: #666; margin-bottom: 20px; line-height: 1.5; }
        .tool-button { background: #007bff; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-size: 16px; width: 100%; }
        .tool-button:hover { background: #0056b3; }
        .status-bar { background: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
        .status-indicator { display: flex; align-items: center; gap: 8px; }
        .status-dot { width: 10px; height: 10px; border-radius: 50%; }
        .status-online { background: #28a745; }
        .status-offline { background: #dc3545; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 Magic Learn</h1>
        <p>AI-Powered Learning Platform with Three Interactive Tools</p>
    </div>
    
    <div class="container">
        <div class="status-bar">
            <div class="status-indicator">
                <div class="status-dot" id="statusDot"></div>
                <span id="statusText">Checking connection...</span>
            </div>
            <div id="statusDetails"></div>
        </div>
        
        <div class="tools-grid">
            <div class="tool-card">
                <div class="tool-icon">🖼️</div>
                <div class="tool-title">Image Reader</div>
                <div class="tool-description">
                    Upload and analyze images with AI. Perfect for mathematical equations, 
                    scientific diagrams, and educational content analysis.
                </div>
                <button class="tool-button" onclick="openTool('image-reader')">
                    Launch Image Reader
                </button>
            </div>
            
            <div class="tool-card">
                <div class="tool-icon">✋</div>
                <div class="tool-title">DrawInAir</div>
                <div class="tool-description">
                    Draw in the air using hand gestures with MediaPipe tracking. 
                    Create mathematical equations and get instant AI analysis.
                </div>
                <button class="tool-button" onclick="openTool('draw-in-air')">
                    Launch DrawInAir
                </button>
            </div>
            
            <div class="tool-card">
                <div class="tool-icon">📚</div>
                <div class="tool-title">Plot Crafter</div>
                <div class="tool-description">
                    Generate educational stories with AI. Create engaging narratives 
                    that teach concepts through interactive storytelling.
                </div>
                <button class="tool-button" onclick="openTool('plot-crafter')">
                    Launch Plot Crafter
                </button>
            </div>
        </div>
        
        <div style="background: white; padding: 20px; border-radius: 8px; margin-top: 20px;">
            <h3>🚀 Quick Start Guide</h3>
            <ol style="margin: 15px 0; padding-left: 20px;">
                <li><strong>Image Reader:</strong> Upload photos of math problems, diagrams, or text for AI analysis</li>
                <li><strong>DrawInAir:</strong> Use hand gestures to draw equations in the air and get solutions</li>
                <li><strong>Plot Crafter:</strong> Create educational stories that make learning fun and engaging</li>
            </ol>
            
            <h4>🎯 Hand Gestures for DrawInAir:</h4>
            <ul style="margin: 10px 0; padding-left: 20px;">
                <li><strong>Drawing:</strong> Thumb + Index finger</li>
                <li><strong>Moving:</strong> Thumb + Index + Middle finger</li>
                <li><strong>Erasing:</strong> Thumb + Middle finger</li>
                <li><strong>Clearing:</strong> Thumb + Pinky finger</li>
                <li><strong>Analyzing:</strong> Index + Middle finger (no thumb)</li>
            </ul>
        </div>
    </div>

    <script>
        const API_BASE_URL = 'https://classroom-backend-821372121985.us-central1.run.app/api/magic-learn';

        async function checkConnection() {
            const statusDot = document.getElementById('statusDot');
            const statusText = document.getElementById('statusText');
            const statusDetails = document.getElementById('statusDetails');

            try {
                const response = await fetch(`${API_BASE_URL}/health`);
                const data = await response.json();

                statusDot.className = 'status-dot status-online';
                statusText.textContent = 'Magic Learn Online';
                statusDetails.innerHTML = `
                    <small>
                        Services: ${Object.keys(data.services).join(', ')} | 
                        Status: ${data.status}
                    </small>
                `;

                console.log('✅ Magic Learn connected:', data);
                return true;

            } catch (error) {
                statusDot.className = 'status-dot status-offline';
                statusText.textContent = 'Connection Failed';
                statusDetails.innerHTML = '<small>Please check if the backend server is running</small>';

                console.error('❌ Magic Learn connection failed:', error);
                return false;
            }
        }

        function openTool(toolName) {
            // Open tool in new window/tab
            const toolUrls = {
                'image-reader': './image-reader.html',
                'draw-in-air': './draw-in-air.html',
                'plot-crafter': './plot-crafter.html'
            };

            const url = toolUrls[toolName];
            if (url) {
                window.open(url, '_blank', 'width=1000,height=800');
            }
        }

        // Check connection on load
        window.addEventListener('load', checkConnection);

        // Recheck connection every 30 seconds
        setInterval(checkConnection, 30000);
    </script>
</body>
</html>
```

## 📝 Integration Checklist

### ✅ Before You Start

1. **Backend Status**: Ensure backend is deployed and running
2. **CORS Fixed**: Verify CORS allows `http://localhost:8080`
3. **API Keys**: Gemini API key configured in backend
4. **Dependencies**: MediaPipe and OpenCV installed on backend

### 🧪 Testing Steps

1. **Test Connection**: Open `magic-learn-dashboard.html` and verify green status
2. **Test Image Reader**: Upload a math equation image
3. **Test DrawInAir**: Allow camera access and try hand gestures
4. **Test Plot Crafter**: Generate a story with educational content

### 🔧 Troubleshooting

**CORS Issues:**
```javascript
// Add this to test CORS
fetch('https://classroom-backend-821372121985.us-central1.run.app/api/magic-learn/cors-test')
  .then(r => r.json())
  .then(d => console.log('CORS OK:', d))
  .catch(e => console.error('CORS Failed:', e));
```

**Camera Issues:**
- Ensure HTTPS or localhost for camera access
- Check browser permissions
- Try different browsers

**API Errors:**
- Check browser console for detailed errors
- Verify backend logs
- Test individual endpoints

## 🚀 Next Steps

1. **Deploy Frontend**: Host your HTML files on a web server
2. **Add Features**: Implement user accounts, save results, etc.
3. **Customize UI**: Match your brand and design system
4. **Mobile Support**: Add responsive design and touch gestures

Your Magic Learn integration is now complete! 🎉