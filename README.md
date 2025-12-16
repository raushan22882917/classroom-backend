# 🤏 Hand Gesture Drawing Application

A machine learning-powered hand gesture recognition system that allows users to draw using hand movements detected through a camera.

## 🎯 Core Features

- **Real-time Hand Detection**: Uses computer vision to detect hand movements
- **Gesture-based Drawing**: Draw by moving your hand in the camera view
- **No MediaPipe Required**: Works with basic OpenCV for immediate use
- **Educational Integration**: Connected to learning APIs for educational content

## 📁 Project Structure

### Core Application
- `hand_drawing_app.py` - **Main hand gesture drawing application**
- `app/main.py` - FastAPI server with all endpoints
- `requirements.txt` - Python dependencies

### API & Services
- Core educational platform services
- `app/utils/image_processing.py` - Image processing utilities

### Documentation
- `API_SUMMARY.md` - Complete API documentation and usage examples

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Hand Drawing App
```bash
python3 hand_drawing_app.py
```

### 3. Start API Server (Optional)
```bash
uvicorn app.main:app --reload
```

## 🎮 How to Use Hand Drawing

1. **Start the Application**: Run `python3 hand_drawing_app.py`
2. **Position Your Hand**: Show your hand to the camera
3. **Draw**: Move your hand in the **upper area** of the screen to draw
4. **Stop Drawing**: Move your hand to the **lower area** to stop
5. **Controls**:
   - Press `c` to clear the canvas
   - Press `s` to save your drawing
   - Press `q` to quit
   - Press `h` to toggle help

## 🔧 Technical Details

### Hand Detection Method
- Uses HSV color space for skin tone detection
- Applies morphological operations for noise reduction
- Finds contours and identifies the largest as the hand
- Tracks the topmost point as the fingertip

### Drawing Logic
- **Drawing Zone**: Upper 67% of the camera view
- **Control Zone**: Lower 33% of the camera view
- Draws lines between consecutive hand positions
- Supports different colors and thickness

### API Integration
- Connects to FastAPI backend for advanced features
- Supports landmark marking and analysis
- Educational content integration
- Real-time processing capabilities

## 📊 API Endpoints

### Core Hand Gesture APIs
- `POST /api/magic-learn/landmarks/start` - Start landmark session
- `POST /api/magic-learn/landmarks/process-frame` - Process video frame
- `POST /api/magic-learn/landmarks/mark` - Mark custom landmarks
- `GET /api/magic-learn/landmarks/analysis` - Get educational analysis

### Drawing APIs
- `POST /api/magic-learn/draw-in-air/start` - Start air drawing
- `POST /api/magic-learn/draw-in-air/process-frame` - Process drawing frame
- `POST /api/magic-learn/draw-in-air/analyze` - Analyze drawings

See `API_SUMMARY.md` for complete documentation.

## 🎓 Educational Features

- **Anatomy Learning**: Learn about hand structure and movement
- **Gesture Recognition**: Understand different hand gestures
- **Biomechanics**: Study hand movement patterns
- **Interactive Learning**: Hands-on experience with computer vision

## 🔧 Requirements

### Minimum Requirements
- Python 3.7+
- OpenCV (`opencv-python`)
- NumPy
- Camera access

### Optional (for advanced features)
- MediaPipe (`pip install mediapipe`)
- FastAPI server running
- Internet connection for API features

## 🎯 Current Status

✅ **Working Features**:
- Basic hand detection and drawing
- Real-time camera processing
- Canvas management (clear, save)
- API integration ready
- Educational content available

⚠️ **Optional Enhancements**:
- MediaPipe integration (install `mediapipe` for better accuracy)
- Advanced gesture recognition
- Multi-hand support

## 🚀 Next Steps

1. **Install MediaPipe** for improved hand detection:
   ```bash
   pip install mediapipe
   ```

2. **Test with different lighting conditions** for optimal performance

3. **Explore API features** by starting the FastAPI server

4. **Customize drawing colors and gestures** in the code

## 🎉 Ready to Use!

The hand gesture drawing application is fully functional and ready for educational use. Start with `python3 hand_drawing_app.py` and begin drawing with your hands!