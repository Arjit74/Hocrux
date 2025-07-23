#!/usr/bin/env python3
"""
Enhanced test script for the Apoorv gesture recognition model.
This script tests the model with real-time webcam feed using hand detection.
"""

import os
import sys
import cv2
import numpy as np
import time
from collections import deque
import mediapipe as mp
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Setup MediaPipe for hand detection
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# Global variables for prediction stabilization
prediction_buffer = deque(maxlen=15)  # Buffer to stabilize predictions
frame_threshold = 10  # Number of consistent frames required for a prediction
last_prediction = "No prediction yet"
last_update_time = time.time()
PREDICTION_DELAY = 1.0  # Minimum time between predictions in seconds

def preprocess_hand_roi(hand_roi, target_size=(64, 64)):
    """Preprocess hand ROI for prediction"""
    # Convert to grayscale
    gray = cv2.cvtColor(hand_roi, cv2.COLOR_BGR2GRAY)
    
    # Resize to target size
    gray = cv2.resize(gray, target_size)
    
    # Normalize
    gray = gray.astype('float32') / 255.0
    
    # Add channel and batch dimensions
    gray = np.expand_dims(gray, axis=-1)
    gray = np.expand_dims(gray, axis=0)
    
    return gray

def test_with_webcam():
    """Test the model with webcam feed and hand detection."""
    from src.Apoorv_gesture_recognizer import GestureRecognizer
    
    # Initialize the recognizer with default paths
    model_path = os.path.join('Model', 'sign_model.h5')
    label_map_path = os.path.join('Model', 'label_map.npy')
    
    print(f"Loading model from: {os.path.abspath(model_path)}")
    print(f"Loading label map from: {os.path.abspath(label_map_path)}")
    
    # Initialize recognizer
    recognizer = GestureRecognizer(model_path=model_path, label_map_path=label_map_path)
    
    # Load label map to see what gestures we're looking for
    try:
        label_map = np.load(label_map_path, allow_pickle=True).item()
        print("\nLabel map contents (index: label):")
        print("-" * 30)
        for idx, label in label_map.items():
            print(f"{idx}: {label}")
        print("\nMake sure your hand gesture matches one of these classes.")
    except Exception as e:
        print(f"\nCould not load label map: {e}")
    
    # Start webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam")
        return
    
    print("\nPress 'q' to quit")
    print("Press 'd' to toggle debug info")
    print("Press 's' to save a test image\n")
    
    debug_mode = False
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to capture frame")
                break
                
            # Convert to RGB for hand detection
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detect hands
            results = hands.process(rgb_frame)
            gesture = "No hand detected"
            confidence = 0.0
            
            if results.multi_hand_landmarks:
                # Get hand landmarks
                hand_landmarks = results.multi_hand_landmarks[0]
                
                # Get hand bounding box
                h, w, _ = frame.shape
                x_coords = [lm.x * w for lm in hand_landmarks.landmark]
                y_coords = [lm.y * h for lm in hand_landmarks.landmark]
                x_min, x_max = int(min(x_coords)), int(max(x_coords))
                y_min, y_max = int(min(y_coords)), int(max(y_coords))
                
                # Add padding
                padding = 20
                x_min = max(0, x_min - padding)
                y_min = max(0, y_min - padding)
                x_max = min(w, x_max + padding)
                y_max = min(h, y_max + padding)
                
                # Extract hand ROI
                hand_roi = frame[y_min:y_max, x_min:x_max]
                
                if hand_roi.size > 0:  # Ensure we have a valid ROI
                    try:
                        # Get prediction
                        if debug_mode:
                            gesture, confidence, debug_info = recognizer.predict(hand_roi, debug=True)
                            print("\nDebug Info:")
                            for k, v in debug_info.items():
                                print(f"{k}: {v}")
                        else:
                            gesture, confidence = recognizer.predict(hand_roi)
                        
                        # Stabilize predictions
                        current_time = time.time()
                        prediction_buffer.append(gesture)
                        
                        # Get most common prediction in buffer
                        if len(prediction_buffer) >= frame_threshold:
                            most_common = max(set(prediction_buffer), key=prediction_buffer.count)
                            if debug_mode:
                                print(f"\nRaw prediction: {gesture}")
                                print(f"Prediction buffer: {list(prediction_buffer)}")
                                print(f"Most common: {most_common} (count: {prediction_buffer.count(most_common)})")
                            
                            if (prediction_buffer.count(most_common) > frame_threshold * 0.7 and 
                                (most_common != last_prediction or 
                                 (current_time - last_update_time) > PREDICTION_DELAY)):
                                print(f"\n🔵 New stable prediction: {most_common}")
                                last_prediction = most_common
                                last_update_time = current_time
                            
                            gesture = last_prediction
                            if debug_mode:
                                print(f"Final gesture: {gesture}")
                        
                        # Draw hand bounding box
                        cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
                        
                    except Exception as e:
                        import traceback
                        print(f"\n❌ Prediction error: {e}")
                        print("Traceback:")
                        traceback.print_exc()
                        gesture = "Error"
            
            # Display the result
            cv2.putText(frame, f"Gesture: {gesture}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(frame, f"Confidence: {confidence:.2f}", (10, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            # Show the frame
            cv2.imshow('ASL Gesture Recognition', frame)
            
            # Handle key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('d'):
                debug_mode = not debug_mode
                print(f"Debug mode: {'ON' if debug_mode else 'OFF'}")
            elif key == ord('s'):
                # Save test image
                os.makedirs('debug_test_images', exist_ok=True)
                timestamp = int(time.time())
                cv2.imwrite(f'debug_test_images/test_{timestamp}.jpg', frame)
                print(f"Saved test image: debug_test_images/test_{timestamp}.jpg")
                
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("Test completed.")

if __name__ == "__main__":
    print("Testing Apoorv Gesture Recognition Model")
    print("--------------------------------------")
    test_with_webcam()
    print("\nTest completed.")
