"""DrawInAir service with MediaPipe hand tracking and Gemini AI analysis"""

import cv2
import numpy as np
import base64
import io
from typing import Optional, Dict, Any, List, Tuple
from PIL import Image
import google.generativeai as genai
import os
import asyncio
import threading
import time

# MediaPipe imports with error handling
try:
    import mediapipe as mp
    from mediapipe.python.solutions import hands, drawing_utils
    MEDIAPIPE_AVAILABLE = True
    print("✅ MediaPipe loaded successfully")
except ImportError as e:
    print(f"⚠️ MediaPipe not available: {e}")
    MEDIAPIPE_AVAILABLE = False
    # Create mock objects to prevent import errors
    class MockHands:
        def __init__(self, **kwargs): pass
        def process(self, image): return None
        def close(self): pass
    
    class MockDrawingUtils:
        @staticmethod
        def draw_landmarks(image, landmark_list, connections): pass
    
    mp = type('MockMP', (), {})()
    hands = type('MockHands', (), {'Hands': MockHands, 'HAND_CONNECTIONS': []})()
    drawing_utils = MockDrawingUtils()

from app.models.magic_learn import GestureRecognitionRequest, GestureRecognitionResponse, RecognizedShape, GesturePoint

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


class DrawInAirService:
    """Service for hand gesture recognition and air drawing with MediaPipe"""
    
    def __init__(self):
        self.mp_hands = None
        self.canvas = None
        self.current_gesture = "None"
        self.p1, self.p2 = 0, 0  # Drawing position tracker
        self.gesture_lock_mode = None
        self.gesture_lock_counter = 0
        self.LOCK_THRESHOLD = 3
        self.UNLOCK_THRESHOLD = 3
        self.INTENTIONAL_SWITCH_THRESHOLD = 2
        self.canvas_width = 950
        self.canvas_height = 550
        
        # Initialize MediaPipe if available
        if MEDIAPIPE_AVAILABLE:
            self._initialize_mediapipe()
        
        self.canvas_lock = threading.Lock()
    
    def _initialize_mediapipe(self):
        """Initialize MediaPipe hands detection"""
        try:
            self.mp_hands = hands.Hands(
                static_image_mode=False,
                max_num_hands=1,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.65,
                model_complexity=0
            )
            print("✅ MediaPipe hands initialized")
        except Exception as e:
            print(f"⚠️ Failed to initialize MediaPipe: {e}")
            self.mp_hands = None
    
    async def start_session(self) -> Dict[str, Any]:
        """Start a new DrawInAir session"""
        try:
            # Initialize canvas
            with self.canvas_lock:
                self.canvas = np.zeros((self.canvas_height, self.canvas_width, 3), dtype=np.uint8)
            
            # Reset state
            self.current_gesture = "None"
            self.p1, self.p2 = 0, 0
            self.gesture_lock_mode = None
            self.gesture_lock_counter = 0
            
            return {
                'success': True,
                'message': 'DrawInAir session started',
                'canvas_size': {'width': self.canvas_width, 'height': self.canvas_height}
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def process_frame(self, frame_data: str) -> Dict[str, Any]:
        """Process video frame with hand tracking and gesture recognition"""
        if not MEDIAPIPE_AVAILABLE or not self.mp_hands:
            return {
                'success': False,
                'error': 'MediaPipe not available. Please install: pip install mediapipe opencv-python'
            }
        
        try:
            # Decode base64 frame
            if ',' in frame_data:
                frame_data = frame_data.split(',')[1]
            
            img_bytes = base64.b64decode(frame_data)
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return {'success': False, 'error': 'Failed to decode frame'}
            
            # Resize and flip for mirror effect
            img = cv2.resize(img, (self.canvas_width, self.canvas_height))
            img = cv2.flip(img, 1)  # Mirror horizontally
            
            # Process with MediaPipe
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            result = self.mp_hands.process(img_rgb)
            
            # Process hand landmarks
            landmark_list = []
            hand_label = None
            
            if result.multi_hand_landmarks:
                if result.multi_handedness:
                    hand_label = result.multi_handedness[0].classification[0].label
                
                for hand_lms in result.multi_hand_landmarks:
                    # Draw landmarks
                    drawing_utils.draw_landmarks(
                        image=img,
                        landmark_list=hand_lms,
                        connections=hands.HAND_CONNECTIONS
                    )
                    
                    # Get landmark coordinates
                    for id, lm in enumerate(hand_lms.landmark):
                        h, w, c = img.shape
                        cx, cy = int(lm.x * w), int(lm.y * h)
                        landmark_list.append([id, cx, cy])
            
            # Detect gestures
            gesture_info = self._detect_gestures(landmark_list, hand_label, img)
            
            # Execute gesture actions
            self._execute_gesture_actions(landmark_list, img)
            
            # Create output frame with canvas overlay
            output_frame = self._create_output_frame(img)
            
            # Encode frame as base64
            _, buffer = cv2.imencode('.png', output_frame)
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            return {
                'success': True,
                'frame': f'data:image/png;base64,{frame_base64}',
                'gesture': self.current_gesture,
                'gesture_info': gesture_info
            }
            
        except Exception as e:
            print(f"Error processing frame: {e}")
            return {'success': False, 'error': str(e)}
    
    def _detect_gestures(self, landmark_list: List, hand_label: Optional[str], img: np.ndarray) -> Dict[str, Any]:
        """Detect hand gestures from landmarks"""
        if not landmark_list:
            self.current_gesture = "None"
            return {'detected': 'None', 'confidence': 0.0}
        
        # Detect finger positions
        fingers = self._detect_fingers(landmark_list, hand_label)
        
        if len(fingers) != 5:
            self.current_gesture = "None"
            return {'detected': 'None', 'confidence': 0.0}
        
        # Draw finger indicators
        self._draw_finger_indicators(landmark_list, fingers, img)
        
        # Gesture recognition logic
        detected_gesture = self._classify_gesture(fingers)
        
        # Apply gesture locking logic
        self._apply_gesture_locking(detected_gesture)
        
        return {
            'detected': detected_gesture,
            'current': self.current_gesture,
            'fingers': fingers,
            'confidence': 0.9 if detected_gesture != "None" else 0.0
        }
    
    def _detect_fingers(self, landmark_list: List, hand_label: Optional[str]) -> List[int]:
        """Detect which fingers are up"""
        fingers = []
        
        if not landmark_list or len(landmark_list) < 21:
            return fingers
        
        # Thumb detection (different for left/right hand)
        thumb_tip_x = landmark_list[4][1]
        thumb_ip_x = landmark_list[3][1]
        thumb_mcp_x = landmark_list[2][1]
        wrist_x = landmark_list[0][1]
        
        # For mirrored camera view, MediaPipe labels are opposite
        actual_hand = "Right" if hand_label == "Left" else "Left"
        
        if actual_hand == "Right":
            thumb_extended = thumb_tip_x > thumb_mcp_x + abs(thumb_mcp_x - wrist_x) * 0.15
        else:
            thumb_extended = thumb_tip_x < thumb_mcp_x - abs(thumb_mcp_x - wrist_x) * 0.15
        
        fingers.append(1 if thumb_extended else 0)
        
        # Other fingers (Index, Middle, Ring, Pinky)
        finger_landmarks = [[8, 6], [12, 10], [16, 14], [20, 18]]
        
        # Calculate hand size for scale-independent detection
        wrist_y = landmark_list[0][2]
        middle_base_y = landmark_list[9][2]
        hand_size = abs(wrist_y - middle_base_y)
        if hand_size < 50:
            hand_size = 100
        
        for tip_id, pip_id in finger_landmarks:
            tip_y = landmark_list[tip_id][2]
            pip_y = landmark_list[pip_id][2]
            clearance_needed = hand_size * 0.15
            
            if (pip_y - tip_y) > clearance_needed:
                fingers.append(1)
            else:
                fingers.append(0)
        
        return fingers
    
    def _draw_finger_indicators(self, landmark_list: List, fingers: List[int], img: np.ndarray):
        """Draw visual indicators for finger positions"""
        fingertip_ids = [4, 8, 12, 16, 20]  # Thumb, Index, Middle, Ring, Pinky
        
        for i, tip_id in enumerate(fingertip_ids):
            if i < len(fingers) and tip_id < len(landmark_list):
                cx, cy = landmark_list[tip_id][1], landmark_list[tip_id][2]
                
                if fingers[i] == 1:
                    # Green for extended fingers
                    cv2.circle(img, (cx, cy), 12, (0, 255, 0), 2)
                    cv2.circle(img, (cx, cy), 8, (0, 255, 0), -1)
                else:
                    # Red for folded fingers
                    cv2.circle(img, (cx, cy), 8, (0, 0, 255), 2)
    
    def _classify_gesture(self, fingers: List[int]) -> str:
        """Classify gesture based on finger positions"""
        if len(fingers) != 5:
            return "None"
        
        finger_count = sum(fingers)
        
        # Gesture patterns
        if finger_count == 2 and fingers[0] == 1 and fingers[1] == 1:
            return "Drawing"
        elif finger_count == 3 and fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 1:
            return "Moving"
        elif finger_count == 2 and fingers[0] == 1 and fingers[2] == 1:
            return "Erasing"
        elif finger_count == 2 and fingers[0] == 1 and fingers[4] == 1:
            return "Clearing"
        elif finger_count == 2 and fingers[0] == 0 and fingers[1] == 1 and fingers[2] == 1:
            return "Analyzing"
        else:
            return "None"
    
    def _apply_gesture_locking(self, detected_gesture: str):
        """Apply smart gesture locking to prevent accidental switches"""
        if self.gesture_lock_mode is None:
            # Not locked yet
            if detected_gesture in ["Drawing", "Moving", "Erasing"]:
                self.gesture_lock_counter += 1
                if self.gesture_lock_counter >= self.LOCK_THRESHOLD:
                    self.gesture_lock_mode = detected_gesture
                    self.current_gesture = detected_gesture
                else:
                    self.current_gesture = detected_gesture
            else:
                self.gesture_lock_counter = 0
                self.current_gesture = detected_gesture
        else:
            # Already locked
            if detected_gesture == self.gesture_lock_mode:
                self.gesture_lock_counter = 0
                self.current_gesture = self.gesture_lock_mode
            elif detected_gesture in ["Drawing", "Moving", "Erasing"]:
                # Intentional switch detection
                is_intentional = self._is_intentional_switch(self.gesture_lock_mode, detected_gesture)
                
                if is_intentional:
                    self.gesture_lock_counter += 1
                    if self.gesture_lock_counter >= self.INTENTIONAL_SWITCH_THRESHOLD:
                        self.gesture_lock_mode = detected_gesture
                        self.gesture_lock_counter = 0
                        self.current_gesture = detected_gesture
                    else:
                        self.current_gesture = detected_gesture
                else:
                    self.gesture_lock_counter += 1
                    if self.gesture_lock_counter >= self.UNLOCK_THRESHOLD:
                        self.gesture_lock_mode = detected_gesture
                        self.gesture_lock_counter = 0
                        self.current_gesture = detected_gesture
                    else:
                        self.current_gesture = self.gesture_lock_mode
            elif detected_gesture in ["Clearing", "Analyzing"]:
                # Special gestures override lock
                self.gesture_lock_mode = None
                self.gesture_lock_counter = 0
                self.current_gesture = detected_gesture
            else:
                # Unknown gesture
                self.gesture_lock_counter += 1
                if self.gesture_lock_counter >= self.UNLOCK_THRESHOLD:
                    self.gesture_lock_mode = None
                    self.gesture_lock_counter = 0
                    self.current_gesture = "None"
                else:
                    self.current_gesture = self.gesture_lock_mode
    
    def _is_intentional_switch(self, current_mode: str, new_gesture: str) -> bool:
        """Determine if gesture switch is intentional"""
        intentional_switches = [
            ("Drawing", "Moving"),
            ("Moving", "Drawing"),
            ("Drawing", "Erasing"),
            ("Erasing", "Drawing"),
            ("Moving", "Erasing"),
            ("Erasing", "Moving")
        ]
        
        return (current_mode, new_gesture) in intentional_switches
    
    def _execute_gesture_actions(self, landmark_list: List, img: np.ndarray):
        """Execute actions based on current gesture"""
        if not landmark_list or self.canvas is None:
            return
        
        with self.canvas_lock:
            if self.current_gesture == "Drawing" and len(landmark_list) > 8:
                cx, cy = landmark_list[8][1], landmark_list[8][2]  # Index finger tip
                if self.p1 == 0 and self.p2 == 0:
                    self.p1, self.p2 = cx, cy
                else:
                    cv2.line(self.canvas, (self.p1, self.p2), (cx, cy), (255, 0, 255), 5)
                    self.p1, self.p2 = cx, cy
            
            elif self.current_gesture == "Moving" and len(landmark_list) > 8:
                cx, cy = landmark_list[8][1], landmark_list[8][2]
                cv2.circle(img, (cx, cy), 10, (0, 255, 0), 2)
                self.p1, self.p2 = 0, 0
            
            elif self.current_gesture == "Erasing" and len(landmark_list) > 12:
                cx, cy = landmark_list[12][1], landmark_list[12][2]  # Middle finger tip
                if self.p1 == 0 and self.p2 == 0:
                    self.p1, self.p2 = cx, cy
                else:
                    cv2.line(self.canvas, (self.p1, self.p2), (cx, cy), (0, 0, 0), 15)
                    self.p1, self.p2 = cx, cy
            
            elif self.current_gesture == "Clearing":
                self.canvas = np.zeros((self.canvas_height, self.canvas_width, 3), dtype=np.uint8)
                self.gesture_lock_mode = None
                self.gesture_lock_counter = 0
                self.p1, self.p2 = 0, 0
            
            elif self.current_gesture == "Analyzing":
                self.gesture_lock_mode = None
                self.gesture_lock_counter = 0
                self.p1, self.p2 = 0, 0
            
            else:
                self.p1, self.p2 = 0, 0
    
    def _create_output_frame(self, img: np.ndarray) -> np.ndarray:
        """Create output frame with canvas overlay"""
        if self.canvas is None:
            return img
        
        with self.canvas_lock:
            # Create transparent overlay
            overlay = np.zeros((self.canvas_height, self.canvas_width, 4), dtype=np.uint8)
            overlay[:, :, :3] = img  # RGB channels
            overlay[:, :, 3] = 255  # Alpha channel
            
            # Add canvas drawings
            canvas_gray = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2GRAY)
            _, canvas_mask = cv2.threshold(canvas_gray, 1, 255, cv2.THRESH_BINARY)
            
            # Blend canvas with image
            blended = cv2.addWeighted(img, 0.7, self.canvas, 1, 0)
            
            # Apply mask
            img_gray = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2GRAY)
            _, img_inv = cv2.threshold(img_gray, 50, 255, cv2.THRESH_BINARY_INV)
            img_inv = cv2.cvtColor(img_inv, cv2.COLOR_GRAY2BGR)
            blended = cv2.bitwise_and(blended, img_inv)
            final_img = cv2.bitwise_or(blended, self.canvas)
            
            return final_img
    
    async def analyze_drawing(self, image_data: str) -> Dict[str, Any]:
        """Analyze drawn content with Gemini AI"""
        if not GEMINI_API_KEY:
            return {
                'success': False,
                'error': 'Gemini API key not configured'
            }
        
        try:
            # Decode image
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return {'success': False, 'error': 'Failed to decode image'}
            
            # Convert to PIL Image
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(img_rgb)
            
            # Analyze with Gemini
            model = genai.GenerativeModel('gemini-2.5-flash-lite')
            
            prompt = """Analyze the image and provide the following:

* If a mathematical equation is present:
  - The equation represented in the image
  - The solution to the equation
  - A short explanation of the steps taken to arrive at the solution
  - If it's a triangle, assume it's mostly a right-angle triangle if sides are missing

* If a drawing is present and no equation is detected:
  - A brief description of the drawn image in simple terms
  - Educational insights about what's drawn
  - Suggestions for learning activities

* If only text is present:
  - Return the text content
  - Provide context and educational value

Format your response in clear, educational language suitable for students."""

            response = model.generate_content([prompt, pil_image])
            
            return {
                'success': True,
                'result': response.text
            }
            
        except Exception as e:
            print(f"Analysis error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def clear_canvas(self) -> Dict[str, Any]:
        """Clear the drawing canvas"""
        try:
            with self.canvas_lock:
                self.canvas = np.zeros((self.canvas_height, self.canvas_width, 3), dtype=np.uint8)
            
            self.p1, self.p2 = 0, 0
            self.current_gesture = "None"
            self.gesture_lock_mode = None
            self.gesture_lock_counter = 0
            
            return {'success': True, 'message': 'Canvas cleared'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def stop_session(self) -> Dict[str, Any]:
        """Stop DrawInAir session and cleanup resources"""
        try:
            # Close MediaPipe
            if self.mp_hands:
                self.mp_hands.close()
                self.mp_hands = None
            
            # Reset state
            with self.canvas_lock:
                self.canvas = None
            
            self.current_gesture = "None"
            self.p1, self.p2 = 0, 0
            self.gesture_lock_mode = None
            self.gesture_lock_counter = 0
            
            return {'success': True, 'message': 'DrawInAir session stopped'}
        except Exception as e:
            return {'success': False, 'error': str(e)}


# Service instance
draw_in_air_service = DrawInAirService()