"""
Magic Learn Router - FastAPI integration for Magic Learn service
Provides DrawInAir, Image Reader, and Plot Crafter functionality
"""

import base64
import json
from typing import Optional
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import google.generativeai as genai
from app.config import settings
import os

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is required. Add it to .env file.")

genai.configure(api_key=GEMINI_API_KEY)

router = APIRouter()

# Pydantic models for request/response
class AnalyzeDrawingRequest(BaseModel):
    image: str  # Base64 encoded image

class AnalyzeImageRequest(BaseModel):
    imageData: str  # Base64 encoded image data
    mimeType: Optional[str] = "image/jpeg"
    instructions: Optional[str] = ""

class GeneratePlotRequest(BaseModel):
    theme: str

class ProcessFrameRequest(BaseModel):
    frame: str  # Base64 encoded frame data

class APIResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None

# Global variables for DrawInAir state
current_gesture = "None"
canvas_cleared = False

def get_gemini_model():
    """Get configured Gemini model instance"""
    return genai.GenerativeModel('gemini-2.5-flash-lite')

# ==================== HEALTH CHECK ====================

@router.get("/magic-learn/health")
async def health_check():
    """Health check for Magic Learn service"""
    return {
        "status": "healthy",
        "service": "Magic Learn Backend",
        "features": ["DrawInAir", "Image Reader", "Plot Crafter"]
    }

@router.get("/magic-learn")
async def magic_learn_info():
    """Magic Learn service information"""
    return {
        "service": "Magic Learn Backend API",
        "status": "running",
        "version": "1.0.0",
        "features": ["DrawInAir", "Image Reader", "Plot Crafter"],
        "endpoints": {
            "health": "/api/magic-learn/health",
            "drawinair": {
                "start": "POST /api/magic-learn/drawinair/start",
                "stop": "POST /api/magic-learn/drawinair/stop",
                "gesture": "GET /api/magic-learn/drawinair/gesture",
                "analyze": "POST /api/magic-learn/drawinair/analyze",
                "clear": "POST /api/magic-learn/drawinair/clear",
                "process_frame": "POST /api/magic-learn/drawinair/process-frame"
            },
            "image_reader": {
                "analyze": "POST /api/magic-learn/image-reader/analyze"
            },
            "plot_crafter": {
                "generate": "POST /api/magic-learn/plot-crafter/generate"
            }
        }
    }

# ==================== DRAWINAIR ENDPOINTS ====================

@router.post("/magic-learn/drawinair/start")
async def start_drawinair():
    """Start DrawInAir service"""
    try:
        global current_gesture, canvas_cleared
        current_gesture = "None"
        canvas_cleared = False
        
        return {
            "success": True,
            "message": "DrawInAir initialized successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start DrawInAir: {str(e)}")

@router.post("/magic-learn/drawinair/stop")
async def stop_drawinair():
    """Stop DrawInAir service"""
    try:
        global current_gesture, canvas_cleared
        current_gesture = "None"
        canvas_cleared = False
        
        return {
            "success": True,
            "message": "DrawInAir stopped successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop DrawInAir: {str(e)}")

@router.get("/magic-learn/drawinair/gesture")
async def get_current_gesture():
    """Get current hand gesture"""
    return {
        "success": True,
        "gesture": current_gesture
    }

@router.post("/magic-learn/drawinair/clear")
async def clear_canvas():
    """Clear drawing canvas"""
    try:
        global canvas_cleared
        canvas_cleared = True
        
        return {
            "success": True,
            "message": "Canvas cleared successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear canvas: {str(e)}")

@router.post("/magic-learn/drawinair/process-frame")
async def process_frame(request: ProcessFrameRequest):
    """Process video frame for hand gesture detection"""
    try:
        if not request.frame:
            raise HTTPException(status_code=400, detail="No frame data provided")
        
        # For now, return a simple response since we don't have MediaPipe/OpenCV in FastAPI
        # In a real implementation, this would process the frame with MediaPipe
        global current_gesture
        
        # Simulate gesture detection
        current_gesture = "Drawing"  # Default gesture for demo
        
        # Return processed frame (in real implementation, this would be the processed image)
        return {
            "success": True,
            "frame": request.frame,  # Echo back the frame for demo
            "gesture": current_gesture
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process frame: {str(e)}")

@router.post("/magic-learn/drawinair/analyze")
async def analyze_drawing(request: AnalyzeDrawingRequest):
    """Analyze drawn content with Gemini AI"""
    try:
        if not request.image:
            raise HTTPException(status_code=400, detail="No image provided")
        
        # Decode base64 image
        image_data = request.image
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        try:
            image_bytes = base64.b64decode(image_data)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 image data")
        
        # Analyze with Gemini
        model = get_gemini_model()
        prompt = """
        Analyze the image provided (which is a drawing or text) and act as an expert educational tutor. Provide a detailed, structured response in Markdown format.

        **Structure Your Response As Follows:**

        # 1. Identification 🔍
        - Clearly state what you see in the image (e.g., "This is a handwritten equation," "This is a geometric diagram," "This is a drawing of a biological cell").

        # 2. Detailed Explanation 📖
        - **If it's Math:**
          - State the problem clearly.
          - Solve it step-by-step, explaining EACH step.
          - State the final answer clearly.
          - Explain the underlying concept (e.g., "This uses the Pythagorean theorem...").
        - **If it's a Drawing:**
          - Describe the details of the drawing.
          - Explain the subject matter in depth (e.g., if it's a heart, explain its function).
        - **If it's Text/Question:**
          - Answer the question comprehensively.

        # 3. Key Learning Points 🧠
        - Bullet point 2-3 key concepts or facts the user should remember about this topic.

        # 4. Real-World Example 🌍
        - Briefly connect this concept to a real-world application to make it relatable.

        **Tone:** Encouraging, clear, and educational.
        """
        
        # Create image part for Gemini
        image_part = {
            "mime_type": "image/png",
            "data": image_bytes
        }
        
        response = model.generate_content([prompt, image_part])
        
        return {
            "success": True,
            "result": response.text
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

# ==================== IMAGE READER ENDPOINTS ====================

@router.post("/magic-learn/image-reader/analyze")
async def analyze_image(request: AnalyzeImageRequest):
    """Analyze uploaded image with Gemini AI"""
    try:
        if not request.imageData:
            raise HTTPException(status_code=400, detail="No image data provided")
        
        # Decode base64 image
        try:
            image_bytes = base64.b64decode(request.imageData)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid base64 image data")
        
        # Analyze with Gemini
        model = get_gemini_model()
        prompt = f"Analyze the image and provide details. {request.instructions if request.instructions else 'Provide a comprehensive analysis of what you see in the image.'}"
        
        # Create image part for Gemini
        image_part = {
            "mime_type": request.mimeType,
            "data": image_bytes
        }
        
        response = model.generate_content([prompt, image_part])
        
        return {
            "success": True,
            "result": response.text
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")

# ==================== PLOT CRAFTER ENDPOINTS ====================

@router.post("/magic-learn/plot-crafter/generate")
async def generate_plot(request: GeneratePlotRequest):
    """Generate real-life example explanation using Gemini AI"""
    try:
        if not request.theme:
            raise HTTPException(status_code=400, detail="No theme provided")
        
        # Generate explanation with Gemini
        model = get_gemini_model()
        prompt = f"""Explain the concept "{request.theme}" using a SINGLE real-life example in simple, interactive language.

CRITICAL REQUIREMENTS:
- Use ONLY ONE PARAGRAPH (maximum 4-5 sentences)
- Explain with a relatable, everyday real-life scenario
- Use simple, conversational language that anyone can understand
- Make it interactive and engaging
- DO NOT write a long story - just one clear, concise example
- Focus on helping the user understand the concept quickly

Example format: "Imagine you're [everyday scenario]. This is exactly how [concept] works because [simple explanation]."

Topic: {request.theme}

Provide your ONE PARAGRAPH real-life example explanation:"""

        response = model.generate_content([prompt])

        return {
            "success": True,
            "result": response.text
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plot generation failed: {str(e)}")

# ==================== LEGACY FLASK-STYLE ENDPOINTS ====================
# These endpoints maintain compatibility with the original Flask implementation

@router.get("/magic-learn/api/health")
async def legacy_health():
    """Legacy health endpoint for backward compatibility"""
    return await health_check()

@router.post("/magic-learn/api/drawinair/start")
async def legacy_start_drawinair():
    """Legacy DrawInAir start endpoint"""
    return await start_drawinair()

@router.post("/magic-learn/api/drawinair/stop")
async def legacy_stop_drawinair():
    """Legacy DrawInAir stop endpoint"""
    return await stop_drawinair()

@router.get("/magic-learn/api/drawinair/gesture")
async def legacy_get_gesture():
    """Legacy gesture endpoint"""
    return await get_current_gesture()

@router.post("/magic-learn/api/drawinair/clear")
async def legacy_clear_canvas():
    """Legacy clear canvas endpoint"""
    return await clear_canvas()

@router.post("/magic-learn/api/drawinair/analyze")
async def legacy_analyze_drawing(request: Request):
    """Legacy analyze drawing endpoint"""
    try:
        body = await request.json()
        analyze_request = AnalyzeDrawingRequest(**body)
        return await analyze_drawing(analyze_request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")

@router.post("/magic-learn/api/image-reader/analyze")
async def legacy_analyze_image(request: Request):
    """Legacy image analysis endpoint"""
    try:
        body = await request.json()
        analyze_request = AnalyzeImageRequest(**body)
        return await analyze_image(analyze_request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")

@router.post("/magic-learn/api/plot-crafter/generate")
async def legacy_generate_plot(request: Request):
    """Legacy plot generation endpoint"""
    try:
        body = await request.json()
        plot_request = GeneratePlotRequest(**body)
        return await generate_plot(plot_request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")