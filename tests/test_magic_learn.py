"""
Comprehensive tests for Magic Learn service
Tests all three features: DrawInAir, Image Reader, and Plot Crafter
"""

import pytest
import json
import base64
from unittest.mock import Mock, patch, MagicMock
import io
import os
import sys

# Add the app directory to the path so we can import the service
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Mock the problematic imports before importing the service
sys.modules['cv2'] = Mock()
sys.modules['mediapipe'] = Mock()
sys.modules['mediapipe.python.solutions'] = Mock()
sys.modules['mediapipe.python.solutions.hands'] = Mock()
sys.modules['mediapipe.python.solutions.drawing_utils'] = Mock()

# Mock environment variables to avoid API key requirement
with patch.dict(os.environ, {
    'GEMINI_API_KEY': 'test_gemini_key'
}):
    # Import the Flask app from magic_learn
    from app.services.magic_learn import app, get_gemini_model


@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_image_base64():
    """Create a sample base64 encoded image for testing"""
    # Create a simple test image using PIL
    from PIL import Image
    import numpy as np
    
    # Create a simple test image
    img_array = np.zeros((100, 100, 3), dtype=np.uint8)
    img_array[20:80, 20:80] = [255, 255, 255]  # White rectangle
    
    img = Image.fromarray(img_array)
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f"data:image/jpeg;base64,{img_base64}"


@pytest.fixture
def sample_canvas_image():
    """Create a sample canvas image for DrawInAir testing"""
    # Create a simple drawing canvas using PIL
    from PIL import Image, ImageDraw
    
    # Create a simple drawing canvas
    img = Image.new('RGB', (950, 550), color='black')
    draw = ImageDraw.Draw(img)
    draw.line([(100, 100), (200, 200)], fill='magenta', width=5)
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{img_base64}"


class TestHealthEndpoints:
    """Test health check and root endpoints"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns API documentation"""
        response = client.get('/')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['service'] == 'Magic Learn Backend API'
        assert data['status'] == 'running'
        assert 'DrawInAir' in data['features']
        assert 'Image Reader' in data['features']
        assert 'Plot Crafter' in data['features']
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['service'] == 'Magic Learn Backend'


class TestGeminiAPI:
    """Test Gemini API configuration"""
    
    def test_get_gemini_model(self):
        """Test getting Gemini model instance"""
        model = get_gemini_model()
        assert model is not None
        # The model should be a mock in our test environment
        assert hasattr(model, 'generate_content')


class TestDrawInAir:
    """Test DrawInAir functionality"""
    
    def test_start_drawinair(self, client):
        """Test starting DrawInAir service"""
        response = client.post('/api/drawinair/start')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'DrawInAir initialized' in data['message']
    
    def test_stop_drawinair(self, client):
        """Test stopping DrawInAir service"""
        response = client.post('/api/drawinair/stop')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'stopped' in data['message'].lower()
    
    def test_get_current_gesture(self, client):
        """Test getting current gesture"""
        response = client.get('/api/drawinair/gesture')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'gesture' in data
    
    def test_clear_canvas(self, client):
        """Test clearing drawing canvas"""
        response = client.post('/api/drawinair/clear')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'cleared' in data['message'].lower()
    
    def test_process_browser_frame_no_data(self, client):
        """Test processing frame without data"""
        response = client.post('/api/drawinair/process-frame',
                             json={})
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'No frame data' in data['error']
    
    def test_process_browser_frame_with_invalid_data(self, client):
        """Test processing frame with invalid base64 data"""
        response = client.post('/api/drawinair/process-frame',
                             json={'frame': 'invalid_base64_data'})
        
        # Should handle invalid data gracefully
        assert response.status_code == 400 or response.status_code == 500
        data = json.loads(response.data)
        assert data['success'] is False
    
    @patch('app.services.magic_learn.get_gemini_model')
    @patch('app.services.magic_learn.cv2')
    @patch('app.services.magic_learn.np')
    @patch('app.services.magic_learn.Image')
    def test_analyze_drawing_success(self, mock_Image, mock_np, mock_cv2, mock_get_model, client, sample_canvas_image):
        """Test successful drawing analysis"""
        # Mock numpy array with proper array interface
        import numpy as np
        mock_img_array = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_np.frombuffer.return_value = Mock()
        
        # Mock cv2 functions
        mock_cv2.imdecode.return_value = mock_img_array
        mock_cv2.cvtColor.return_value = mock_img_array
        
        # Mock PIL Image
        mock_pil_image = Mock()
        mock_Image.fromarray.return_value = mock_pil_image
        
        # Mock Gemini response
        mock_model = Mock()
        mock_model.generate_content.return_value.text = "This is a simple line drawing."
        mock_get_model.return_value = mock_model
        
        response = client.post('/api/drawinair/analyze',
                             json={'image': sample_canvas_image})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'result' in data
    
    def test_analyze_drawing_no_image(self, client):
        """Test analysis without image"""
        response = client.post('/api/drawinair/analyze',
                             json={})
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'No image provided' in data['error']


class TestImageReader:
    """Test Image Reader functionality"""
    
    @patch('app.services.magic_learn.get_gemini_model')
    def test_analyze_image_success(self, mock_get_model, client, sample_image_base64):
        """Test successful image analysis"""
        # Mock Gemini response
        mock_model = Mock()
        mock_model.generate_content.return_value.text = "This image contains a white rectangle on a black background."
        mock_get_model.return_value = mock_model
        
        # Extract base64 data
        image_data = sample_image_base64.split(',')[1]
        
        response = client.post('/api/image-reader/analyze',
                             json={
                                 'imageData': image_data,
                                 'mimeType': 'image/jpeg',
                                 'instructions': 'Describe what you see'
                             })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'result' in data
    
    def test_analyze_image_no_data(self, client):
        """Test image analysis without image data"""
        response = client.post('/api/image-reader/analyze',
                             json={})
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'No image data provided' in data['error']
    
    @patch('app.services.magic_learn.get_gemini_model')
    def test_analyze_image_with_instructions(self, mock_get_model, client, sample_image_base64):
        """Test image analysis with custom instructions"""
        # Mock Gemini response
        mock_model = Mock()
        mock_model.generate_content.return_value.text = "Mathematical analysis: This appears to be a geometric shape."
        mock_get_model.return_value = mock_model
        
        image_data = sample_image_base64.split(',')[1]
        
        response = client.post('/api/image-reader/analyze',
                             json={
                                 'imageData': image_data,
                                 'mimeType': 'image/jpeg',
                                 'instructions': 'Focus on mathematical content'
                             })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'result' in data


class TestPlotCrafter:
    """Test Plot Crafter functionality"""
    
    @patch('app.services.magic_learn.get_gemini_model')
    def test_generate_plot_success(self, mock_get_model, client):
        """Test successful plot generation"""
        # Mock Gemini response
        mock_model = Mock()
        mock_model.generate_content.return_value.text = "Imagine you're baking a cake. This is exactly how fractions work because you divide the whole cake into equal parts."
        mock_get_model.return_value = mock_model
        
        response = client.post('/api/plot-crafter/generate',
                             json={'theme': 'fractions'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'result' in data
    
    def test_generate_plot_no_theme(self, client):
        """Test plot generation without theme"""
        response = client.post('/api/plot-crafter/generate',
                             json={})
        assert response.status_code == 400
        
        data = json.loads(response.data)
        assert 'No theme provided' in data['error']
    
    @patch('app.services.magic_learn.get_gemini_model')
    def test_generate_plot_complex_theme(self, mock_get_model, client):
        """Test plot generation with complex mathematical theme"""
        # Mock Gemini response
        mock_model = Mock()
        mock_model.generate_content.return_value.text = "Imagine you're on a Ferris wheel. This is exactly how trigonometry works because the wheel creates perfect circles and sine waves."
        mock_get_model.return_value = mock_model
        
        response = client.post('/api/plot-crafter/generate',
                             json={'theme': 'trigonometry and sine waves'})
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'result' in data


class TestErrorHandling:
    """Test error handling across all features"""
    
    @patch('app.services.magic_learn.get_gemini_model')
    @patch('app.services.magic_learn.cv2')
    @patch('app.services.magic_learn.np')
    @patch('app.services.magic_learn.Image')
    def test_api_error_handling_drawinair(self, mock_Image, mock_np, mock_cv2, mock_get_model, client, sample_canvas_image):
        """Test API error handling for DrawInAir"""
        # Mock numpy array
        import numpy as np
        mock_img_array = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_np.frombuffer.return_value = Mock()
        
        # Mock cv2 functions
        mock_cv2.imdecode.return_value = mock_img_array
        mock_cv2.cvtColor.return_value = mock_img_array
        
        # Mock PIL Image
        mock_pil_image = Mock()
        mock_Image.fromarray.return_value = mock_pil_image
        
        # Mock API error
        mock_model = Mock()
        mock_model.generate_content.side_effect = Exception("API error")
        mock_get_model.return_value = mock_model
        
        response = client.post('/api/drawinair/analyze',
                             json={'image': sample_canvas_image})
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['success'] is False
    
    @patch('app.services.magic_learn.get_gemini_model')
    def test_non_quota_error_handling(self, mock_get_model, client, sample_image_base64):
        """Test handling of API errors"""
        # Mock API error
        mock_model = Mock()
        mock_model.generate_content.side_effect = Exception("Network error")
        mock_get_model.return_value = mock_model
        
        image_data = sample_image_base64.split(',')[1]
        
        response = client.post('/api/image-reader/analyze',
                             json={'imageData': image_data})
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['success'] is False


class TestCameraInitialization:
    """Test camera initialization functionality"""
    
    @patch('app.services.magic_learn.cv2.VideoCapture')
    @patch('app.services.magic_learn.hands.Hands')
    def test_initialize_camera_success(self, mock_hands, mock_video_capture):
        """Test successful camera initialization"""
        # Mock camera
        mock_camera = Mock()
        mock_camera.isOpened.return_value = True
        mock_video_capture.return_value = mock_camera
        
        # Mock MediaPipe hands
        mock_hands.return_value = Mock()
        
        # Import and test the function
        from app.services.magic_learn import initialize_camera
        result = initialize_camera()
        assert result is True
        
        # Verify camera settings were applied
        mock_camera.set.assert_called()
    
    @patch('app.services.magic_learn.cv2.VideoCapture')
    def test_initialize_camera_failure(self, mock_video_capture):
        """Test camera initialization failure"""
        # Mock camera that fails to open
        mock_camera = Mock()
        mock_camera.isOpened.return_value = False
        mock_video_capture.return_value = mock_camera
        
        # Import and test the function
        from app.services.magic_learn import initialize_camera
        result = initialize_camera()
        assert result is False


if __name__ == '__main__':
    # Run tests with verbose output
    pytest.main([__file__, '-v'])