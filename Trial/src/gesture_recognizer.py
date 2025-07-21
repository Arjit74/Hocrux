"""
ASL Gesture Recognizer using MediaPipe

This module provides gesture recognition functionality for American Sign Language
using MediaPipe's hand tracking and a simple gesture classification approach.
"""

import cv2
import numpy as np
import mediapipe as mp
from typing import Tuple, List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GestureRecognizer:
    """Recognizes ASL gestures using MediaPipe hand tracking."""
    
    def __init__(self, min_detection_confidence: float = 0.7, min_tracking_confidence: float = 0.5):
        """
        Initialize the gesture recognizer.
        
        Args:
            min_detection_confidence: Minimum confidence for hand detection
            min_tracking_confidence: Minimum confidence for hand tracking
        """
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        
        # Initialize MediaPipe Hands
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )
        
        # ASL Fingerspelling Alphabet (only single letters and numbers)
        self.gesture_map = {
            # Letters A-Z (0-25)
            0: "A", 1: "B", 2: "C", 3: "D", 4: "E", 5: "F", 6: "G", 7: "H", 8: "I", 9: "J",
            10: "K", 11: "L", 12: "M", 13: "N", 14: "O", 15: "P", 16: "Q", 17: "R", 18: "S", 19: "T",
            20: "U", 21: "V", 22: "W", 23: "X", 24: "Y", 25: "Z",
            # Numbers 1-0 (26-35)
            26: "1", 27: "2", 28: "3", 29: "4", 30: "5", 31: "6", 32: "7", 33: "8", 34: "9", 35: "0"
        }
        
        # Remove word map to prevent static phrases from appearing
        self.word_map = {}
        
        self.current_gesture = None
        self.gesture_history = []
        self.max_history = 10  # Number of frames to keep in history
        
        logger.info("Gesture Recognizer initialized")
    
    def process_frame(self, frame: np.ndarray) -> Tuple[Optional[str], float]:
        """
        Process a single frame to detect and recognize gestures.
        
        Args:
            frame: Input BGR image (will be horizontally flipped to un-mirror the feed)
            
        Returns:
            Tuple of (recognized_gesture, confidence)
        """
        # Flip the frame horizontally to un-mirror the camera feed
        frame = cv2.flip(frame, 1)
        
        # Convert the BGR image to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the frame with MediaPipe Hands
        results = self.hands.process(rgb_frame)
        
        if not results.multi_hand_landmarks:
            return None, 0.0
        
        # For simplicity, we'll just use the first detected hand
        hand_landmarks = results.multi_hand_landmarks[0]
        
        # Get hand landmarks as a numpy array
        landmarks = np.array([(lm.x, lm.y, lm.z) for lm in hand_landmarks.landmark])
        
        # Simple gesture recognition based on finger states
        # This is a placeholder - you should replace this with your actual gesture recognition logic
        gesture, confidence = self._classify_gesture(landmarks)
        
        # Update gesture history
        if gesture:
            self.gesture_history.append(gesture)
            if len(self.gesture_history) > self.max_history:
                self.gesture_history.pop(0)
            
            # Simple word recognition from gesture sequence
            recognized_word = self._recognize_word()
            if recognized_word:
                return recognized_word, confidence
            
            return gesture, confidence
        
        return None, 0.0
    
    def _classify_gesture(self, landmarks: np.ndarray) -> Tuple[Optional[str], float]:
        """
        Classify hand gesture based on landmark positions using hand geometry analysis.
        
        Args:
            landmarks: Array of hand landmarks (21 points with x, y, z coordinates)
            
        Returns:
            Tuple of (gesture, confidence)
        """
        # Calculate finger states (extended/bent)
        finger_states = self._get_finger_states(landmarks)
        
        # Calculate hand orientation
        hand_orientation = self._get_hand_orientation(landmarks)
        
        # Calculate distances between key points
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        middle_tip = landmarks[12]
        ring_tip = landmarks[16]
        pinky_tip = landmarks[20]
        wrist = landmarks[0]
        
        # Calculate distances between fingertips and wrist
        thumb_dist = np.linalg.norm(thumb_tip - wrist)
        index_dist = np.linalg.norm(index_tip - wrist)
        middle_dist = np.linalg.norm(middle_tip - wrist)
        ring_dist = np.linalg.norm(ring_tip - wrist)
        pinky_dist = np.linalg.norm(pinky_tip - wrist)
        
        # Calculate angles between fingers
        index_angle = self._angle_between(
            landmarks[5] - landmarks[0],
            landmarks[8] - landmarks[5]
        )
        
        # Letter A: Thumb over fingers (all fingers closed, thumb over)
        if (not finger_states[1] and not finger_states[2] and 
            not finger_states[3] and not finger_states[4] and
            thumb_dist > index_dist * 0.8):
            return "A", 0.9
            
        # Letter B: Flat hand, fingers together
        if (finger_states[1] and finger_states[2] and 
            finger_states[3] and finger_states[4] and
            abs(landmarks[8][1] - landmarks[12][1]) < 0.05 and
            abs(landmarks[12][1] - landmarks[16][1]) < 0.05 and
            abs(landmarks[16][1] - landmarks[20][1]) < 0.05):
            return "B", 0.9
            
        # Letter C: C shape with thumb and fingers
        if (abs(landmarks[4][0] - landmarks[8][0]) > 0.1 and
            abs(landmarks[4][0] - landmarks[20][0]) > 0.1 and
            landmarks[4][1] < landmarks[3][1] and  # Thumb up
            landmarks[8][1] < landmarks[6][1] and  # Index up
            landmarks[12][1] < landmarks[10][1] and  # Middle up
            landmarks[16][1] < landmarks[14][1] and  # Ring up
            landmarks[20][1] < landmarks[18][1]):    # Pinky up
            return "C", 0.85
            
        # Letter D: Index finger up, thumb touches middle finger
        if (finger_states[1] and not finger_states[2] and 
            not finger_states[3] and not finger_states[4] and
            np.linalg.norm(landmarks[4][:2] - landmarks[12][:2]) < 0.05):
            return "D", 0.9
            
        # Letter I: Pinky up, other fingers down
        if (not finger_states[1] and not finger_states[2] and 
            not finger_states[3] and finger_states[4]):
            return "I", 0.9
            
        # Letter L: Index and thumb extended, others curled
        if (finger_states[1] and not finger_states[2] and 
            not finger_states[3] and not finger_states[4] and
            landmarks[8][1] < landmarks[6][1] and  # Index up
            landmarks[4][0] < landmarks[3][0] and  # Thumb to side
            landmarks[4][1] > landmarks[3][1]):    # Thumb up
            return "L", 0.9
            
        # Letter V: Index and middle fingers up, others down (peace sign)
        if (finger_states[1] and finger_states[2] and 
            not finger_states[3] and not finger_states[4] and
            abs(landmarks[8][0] - landmarks[12][0]) > 0.1):  # Fingers spread
            return "V", 0.95
            
        # Letter W: Index, middle, and ring fingers up
        if (finger_states[1] and finger_states[2] and 
            finger_states[3] and not finger_states[4] and
            abs(landmarks[8][0] - landmarks[12][0]) > 0.1 and
            abs(landmarks[12][0] - landmarks[16][0]) > 0.1):
            return "W", 0.9
            
        # I LOVE YOU sign (ILY)
        if (finger_states[1] and finger_states[4] and  # Index and pinky up
            not finger_states[2] and not finger_states[3] and  # Middle and ring down
            landmarks[4][0] > landmarks[3][0] and  # Thumb out
            landmarks[12][1] > landmarks[9][1] and  # Middle finger down
            landmarks[16][1] > landmarks[13][1]):   # Ring finger down
            return "I LOVE YOU", 0.95
            
        # Default: Return the most probable letter based on extended fingers
        extended_count = sum(finger_states[1:])  # Count extended fingers (ignore thumb)
        if extended_count < len(self.gesture_map):
            return self.gesture_map.get(extended_count, "UNKNOWN"), 0.8
            
        return None, 0.0
        
    def _get_finger_states(self, landmarks: np.ndarray) -> List[bool]:
        """Determine which fingers are extended."""
        # Finger tips and their corresponding PIP joints
        finger_tips = [4, 8, 12, 16, 20]  # thumb, index, middle, ring, pinky
        pip_joints = [2, 6, 10, 14, 18]
        
        # Check if each finger is extended (tip y-coordinate is above PIP joint)
        states = [
            landmarks[tip][1] < landmarks[pip][1] - 0.02  # Small threshold
            for tip, pip in zip(finger_tips, pip_joints)
        ]
        return states
        
    def _get_hand_orientation(self, landmarks: np.ndarray) -> str:
        """Determine if hand is facing up or down."""
        # Compare y-coordinates of wrist and middle finger MCP
        if landmarks[0][1] < landmarks[9][1]:  # Wrist is above MCP
            return "up"
        return "down"
        
    def _angle_between(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """Calculate the angle between two vectors in degrees."""
        v1_u = v1 / np.linalg.norm(v1)
        v2_u = v2 / np.linalg.norm(v2)
        return np.degrees(np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0)))
    
    def _recognize_word(self) -> Optional[str]:
        """
        Recognize words from a sequence of gestures.
        
        This is a simple implementation that looks for known word patterns
        in the gesture history. You might want to implement a more sophisticated
        approach using a language model or sequence recognition.
        """
        if not self.gesture_history:
            return None
        
        # Convert gesture history to string for pattern matching
        gesture_sequence = ''.join(self.gesture_history)
        
        # Look for known words in the gesture sequence
        for word, pattern in self.word_map.items():
            word_pattern = ''.join(pattern)
            if word_pattern in gesture_sequence:
                # Clear history when a word is recognized
                self.gesture_history = []
                return word
        
        return None
    
    def draw_landmarks(self, frame: np.ndarray) -> np.ndarray:
        """
        Draw hand landmarks on the frame.
        
        Args:
            frame: Input BGR image
            
        Returns:
            Frame with landmarks drawn
        """
        # Convert the BGR image to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the frame with MediaPipe Hands
        results = self.hands.process(rgb_frame)
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Draw hand landmarks
                mp.solutions.drawing_utils.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                    mp.solutions.drawing_styles.get_default_hand_landmarks_style(),
                    mp.solutions.drawing_styles.get_default_hand_connections_style()
                )
        
        return frame
    
    def release(self):
        """Release resources."""
        self.hands.close()
        logger.info("Gesture Recognizer resources released")


# Example usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='ASL Gesture Recognition')
    parser.add_argument('--camera', type=int, default=0, help='Camera device ID')
    args = parser.parse_args()
    
    # Initialize the gesture recognizer
    recognizer = GestureRecognizer()
    
    # Open the camera
    cap = cv2.VideoCapture(args.camera)
    
    try:
        while True:
            # Read frame from camera
            ret, frame = cap.read()
            if not ret:
                logger.error("Failed to capture frame")
                break
            
            # Process the frame
            gesture, confidence = recognizer.process_frame(frame)
            
            # Draw landmarks on the frame
            frame = recognizer.draw_landmarks(frame)
            
            # Display the recognized gesture
            if gesture:
                cv2.putText(
                    frame, 
                    f"{gesture} ({confidence:.2f})", 
                    (10, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    1, 
                    (0, 255, 0), 
                    2, 
                    cv2.LINE_AA
                )
            
            # Show the frame
            cv2.imshow('ASL Gesture Recognition', frame)
            
            # Break the loop on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        # Release resources
        cap.release()
        recognizer.release()
        cv2.destroyAllWindows()
