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

# Prediction stabilization
prediction_buffer = deque(maxlen=15)  # Buffer to stabilize predictions
frame_threshold = 10  # Number of consistent frames required for a prediction
last_prediction = None
last_update_time = time.time()
PREDICTION_DELAY = 1.0  # Minimum time between predictions in seconds

from src.Apoorv_gesture_recognizer import GestureRecognizer

def test_with_webcam():
    """Test the model with webcam feed."""
    # Initialize the recognizer with default paths
    model_path = os.path.join('Model', 'sign_model.h5')
    label_map_path = os.path.join('Model', 'label_map.npy')
    
    print(f"Loading model from: {os.path.abspath(model_path)}")
    print(f"Loading label map from: {os.path.abspath(label_map_path)}")
    
    # Load label map to see what gestures we're looking for
    import numpy as np
    try:
        label_map = np.load(label_map_path, allow_pickle=True).item()
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam")
        return
    
    print("\nPress 'q' to quit")
    print("Press 'd' to toggle debug info")
    print("Press 's' to save a test image\n")
    
    debug_mode = False
            print(f"Added channel dim: {debug_info.get('added_channel_dim')}")
            print(f"Batch shape: {debug_info.get('batch_shape')}")
            print(f"Prediction shape: {debug_info.get('prediction_shape')}")
            print("\nTop 3 predictions:")
            for i, (label, conf) in enumerate(debug_info.get('top_predictions', [])):
                print(f"  {i+1}. {label}: {conf:.4f}")
            print("\nFinal prediction:", debug_info.get('final_prediction'))
            if 'error' in debug_info:
                print("\nERROR:", debug_info['error'])
            print("="*50 + "\n")
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    print("Testing Apoorv Gesture Recognition Model")
    print("--------------------------------------")
    test_with_webcam()
    print("\nTest completed.")
