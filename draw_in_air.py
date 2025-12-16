import cv2
import numpy as np
import mediapipe as mp

class AirDrawer:
    def __init__(self):
        # Initialize MediaPipe
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.65,
            model_complexity=0
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        # Drawing state
        self.img_canvas = None
        self.p1, self.p2 = 0, 0
        self.current_gesture = "None"
        
        # Gesture Locking State
        self.gesture_lock_mode = None
        self.gesture_lock_counter = 0
        self.LOCK_THRESHOLD = 3
        self.UNLOCK_THRESHOLD = 3
        self.INTENTIONAL_SWITCH_THRESHOLD = 2

    def detect_fingers(self, landmark_list, hand_label):
        """Detect which fingers are up based on landmarks"""
        fingers = []
        
        # Thumb detection
        # Note: MediaPipe mirrors the image, so "Right" hand (in frame) appears as "Left" label usually if flipped
        # But we will rely on the label passed from processing
        
        # Adjust for mirrored view if needed, but standard logic:
        # Check x-coordinates for thumb
        
        thumb_tip_x = landmark_list[4][1]
        thumb_mcp_x = landmark_list[2][1]
        wrist_x = landmark_list[0][1]
        
        # Basic logic: Label "Left" means it looks like a left hand. 
        # If we flip the image (mirror), a right hand becomes a "Left" labeled hand.
        # Let's assume the image IS flipped horizontally (mirror view).
        # Then "Left" label = User's RIGHT hand.
        
        if hand_label == "Left": # User's Right Hand (in mirror mode)
            # Thumb extends to the RIGHT (positive X)
            if thumb_tip_x > thumb_mcp_x:
                fingers.append(1)
            else:
                fingers.append(0)
        else: # User's Left Hand
            # Thumb extends to the LEFT (negative X)
            if thumb_tip_x < thumb_mcp_x:
                fingers.append(1)
            else:
                fingers.append(0)

        # Other 4 fingers (Index, Middle, Ring, Pinky)
        # Check y-coordinates (tip higher than pip)
        # Note: Y increases downwards. So "higher" means smaller Y value.
        
        finger_tips = [8, 12, 16, 20] # Index, Middle, Ring, Pinky
        
        # Simple heuristic: tip should be above the pip joint (id - 2)
        for tip_id in finger_tips:
            if landmark_list[tip_id][2] < landmark_list[tip_id - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)
                
        return fingers

    def determine_gesture(self, fingers):
        """Determine gesture from finger state"""
        if len(fingers) != 5:
            return "None"
            
        # [Thumb, Index, Middle, Ring, Pinky]
        
        # Drawing: Thumb + Index
        if fingers == [1, 1, 0, 0, 0] or fingers == [1, 1, 1, 0, 0]: # Be forgiving, allow thumb+index or thumb+index+middle
             # Actually, original logic: thumb=1, index=1 (sum=2) -> Drawing
             # Let's stick to a clear set
             pass

        # Strict Checks based on common patterns
        
        count = sum(fingers)
        
        # Drawing: Index (+ maybe Thumb)
        # Typically "Pointer" gesture
        if fingers[1] == 1 and fingers[2] == 0: 
             return "Drawing"
             
        # Moving/Hover: Index + Middle
        if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0:
            return "Moving"
            
        # Erasing: All fingers up or palm open
        if count >= 4:
            return "Erasing"
            
        # Clearing: Closed fist? Or specific sign?
        # Let's use Pinky up = Clear? (Rock on?)
        if fingers[1] == 0 and fingers[4] == 1:
            return "Clearing"
            
        return "None"

    def process_frame(self, img):
        """Process a single frame"""
        # Flip and resize
        img = cv2.flip(img, 1)
        h, w, c = img.shape
        
        if self.img_canvas is None:
            self.img_canvas = np.zeros((h, w, 3), dtype=np.uint8)
            
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        result = self.hands.process(img_rgb)
        
        detected_gesture = "None"
        cursor_pos = None
        
        if result.multi_hand_landmarks:
            for idx, hand_lms in enumerate(result.multi_hand_landmarks):
                # Draw landmarks
                self.mp_draw.draw_landmarks(img, hand_lms, self.mp_hands.HAND_CONNECTIONS)
                
                # Get label
                label = result.multi_handedness[idx].classification[0].label
                
                # Get coords
                landmark_list = []
                for id, lm in enumerate(hand_lms.landmark):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    landmark_list.append([id, cx, cy])
                
                # Detect fingers & gesture
                fingers = self.detect_fingers(landmark_list, label)
                
                # Refine Gesture Logic (matching the robust logic from magic_learn.py typically)
                # Drawing: Index (fingers[1]) is UP, Middle (fingers[2]) is DOWN
                if fingers[1] == 1 and fingers[2] == 0:
                    detected_gesture = "Drawing"
                    cursor_pos = (landmark_list[8][1], landmark_list[8][2]) # Index tip
                    
                # Moving: Index and Middle UP
                elif fingers[1] == 1 and fingers[2] == 1:
                    detected_gesture = "Moving"
                    cursor_pos = (landmark_list[8][1], landmark_list[8][2])
                    
                # Erasing: Palm / All UP
                elif sum(fingers) >= 4:
                    detected_gesture = "Erasing"
                    cursor_pos = (landmark_list[9][1], landmark_list[9][2]) # Middle of hand
                
                # Clearing: Only Pinky? Or defined gesture?
                # Let's say Thumb + Pinky
                elif fingers[0] == 1 and fingers[4] == 1 and fingers[1]==0:
                    detected_gesture = "Clearing"

        # --- Gesture Locking Logic (to prevent flickering) ---
        if self.gesture_lock_mode is None:
            if detected_gesture in ["Drawing", "Moving", "Erasing"]:
                self.gesture_lock_counter += 1
                if self.gesture_lock_counter >= self.LOCK_THRESHOLD:
                    self.gesture_lock_mode = detected_gesture
                    self.current_gesture = detected_gesture
            else:
                self.gesture_lock_counter = 0
                self.current_gesture = detected_gesture
        else:
            if detected_gesture == self.gesture_lock_mode:
                self.gesture_lock_counter = 0
                self.current_gesture = self.gesture_lock_mode
            elif detected_gesture == "None":
                self.gesture_lock_counter += 1
                if self.gesture_lock_counter >= self.UNLOCK_THRESHOLD:
                    self.gesture_lock_mode = None
                    self.current_gesture = "None"
            else:
                # Switching gestures?
                # Instant switch for clear changes
                self.gesture_lock_mode = detected_gesture
                self.current_gesture = detected_gesture

        # --- Execution ---
        cv2.putText(img, f"Mode: {self.current_gesture}", (10, 50), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 255), 2)
        
        if self.current_gesture == "Drawing" and cursor_pos:
            cv2.circle(img, cursor_pos, 10, (255, 0, 255), cv2.FILLED)
            if self.p1 == 0 and self.p2 == 0:
                self.p1, self.p2 = cursor_pos
            else:
                cv2.line(self.img_canvas, (self.p1, self.p2), cursor_pos, (255, 0, 255), 5)
                self.p1, self.p2 = cursor_pos
                
        elif self.current_gesture == "Moving" and cursor_pos:
            cv2.circle(img, cursor_pos, 10, (0, 255, 0), cv2.FILLED) # Green cursor for moving (not drawing)
            self.p1, self.p2 = 0, 0
            
        elif self.current_gesture == "Erasing" and cursor_pos:
            cv2.circle(img, cursor_pos, 30, (0, 0, 0), cv2.FILLED)
            if self.p1 == 0 and self.p2 == 0:
                self.p1, self.p2 = cursor_pos
            else:
                cv2.line(self.img_canvas, (self.p1, self.p2), cursor_pos, (0, 0, 0), 40) # Eraser size
                self.p1, self.p2 = cursor_pos
                
        elif self.current_gesture == "Clearing":
            self.img_canvas = np.zeros((h, w, 3), dtype=np.uint8)
            cv2.putText(img, "CLEARED!", (w//2-100, h//2), cv2.FONT_HERSHEY_PLAIN, 3, (0, 0, 255), 3)
            self.p1, self.p2 = 0, 0
        else:
            self.p1, self.p2 = 0, 0

        # Merge Canvas
        # Create gray image of canvas to mask
        img_gray = cv2.cvtColor(self.img_canvas, cv2.COLOR_BGR2GRAY)
        _, img_inv = cv2.threshold(img_gray, 50, 255, cv2.THRESH_BINARY_INV)
        img_inv = cv2.cvtColor(img_inv, cv2.COLOR_GRAY2BGR)
        
        # Mask original image
        img = cv2.bitwise_and(img, img_inv)
        # Add canvas
        img = cv2.bitwise_or(img, self.img_canvas)
        
        return img

def main():
    print("Initializing Camera...")
    cap = cv2.VideoCapture(0)
    cap.set(3, 1280)
    cap.set(4, 720)
    
    drawer = AirDrawer()
    
    print("Starting Air Drawing. Press 'q' to quit.")
    print("Gestures:")
    print(" - Drawing: Index Finger UP")
    print(" - Moving: Index + Middle UP")
    print(" - Erasing: All Fingers UP (Palm)")
    print(" - Clearing: Thumb + Pinky UP")
    
    while True:
        success, img = cap.read()
        if not success:
            print("Failed to read camera")
            break
            
        img = drawer.process_frame(img)
        
        cv2.imshow("Air Drawing", img)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
