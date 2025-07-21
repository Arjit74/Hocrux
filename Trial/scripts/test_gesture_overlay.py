#!/usr/bin/env python3
"""
ASL Gesture Overlay Tester

This script demonstrates real-time gesture detection with an OBS overlay.
It captures video from the camera, detects gestures, and displays them in the overlay.
"""

import os
import sys
import cv2
import time
import json
import requests
import threading
import argparse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Import the TTS manager
from src.tts_manager import TTSManager

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the gesture recognizer
from src.gesture_recognizer import GestureRecognizer

# Configuration
CONFIG = {
    'camera': {
        'device_id': 0,  # Try 1 for OBS Virtual Camera
        'width': 1280,
        'height': 720,
        'fps': 30
    },
    'overlay': {
        'host': 'localhost',
        'port': 8000,
        'endpoint': '/api/update'
    }
}

class GestureOverlayTester:
    def __init__(self, config):
        self.config = config
        self.overlay_url = f"http://{config['overlay']['host']}:{config['overlay']['port']}{config['overlay']['endpoint']}"
        self.gesture_recognizer = GestureRecognizer()
        self.running = False
        self.cap = None
        
        # Initialize TTS
        self.tts = TTSManager(lang='en', slow=False)
        self.last_spoken_text = ""
        self.last_speak_time = 0
        self.min_speak_interval = 2.0  # Minimum seconds between speaking the same text
        
    def _init_camera(self):
        """Initialize the camera with optimized settings for performance."""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # Release any existing camera instance
                if hasattr(self, 'cap') and self.cap is not None:
                    self.cap.release()
                
                # Try different camera backends with optimized settings
                if attempt == 0:
                    # First try with DirectShow (works well on Windows) with MJPG codec
                    self.cap = cv2.VideoCapture(self.config['camera']['device_id'], cv2.CAP_DSHOW)
                    # Set buffer size to 1 to reduce latency
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    # Set MJPG codec which is typically faster than default
                    self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
                else:
                    # Fall back to default backend with reduced resolution for better performance
                    self.cap = cv2.VideoCapture(self.config['camera']['device_id'])
                
                if not self.cap.isOpened():
                    raise RuntimeError(f"Could not open camera (attempt {attempt + 1}/{max_attempts})")
                
                # Set camera properties with priority on speed
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Lower resolution for better performance
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.cap.set(cv2.CAP_PROP_FPS, 30)  # 30 FPS is sufficient for ASL
                
                # Disable auto-focus and auto-exposure for more consistent performance
                try:
                    self.cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
                    self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)  # 1 = manual mode
                    self.cap.set(cv2.CAP_PROP_EXPOSURE, 0.25)     # Adjust exposure if needed
                except:
                    pass  # Ignore if camera doesn't support these settings
                
                # Test frame capture with timeout
                start_time = time.time()
                while time.time() - start_time < 2:  # 2 second timeout
                    ret, frame = self.cap.read()
                    if ret:
                        actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
                        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        print(f"Camera initialized: {actual_width}x{actual_height} @ {actual_fps:.1f}fps")
                        return True
                    time.sleep(0.1)
                
                raise RuntimeError("Could not read frame from camera")
                
            except Exception as e:
                if attempt == max_attempts - 1:
                    print(f"Failed to initialize camera after {max_attempts} attempts: {e}")
                    return False
                print(f"Camera initialization attempt {attempt + 1} failed: {e}")
                if hasattr(self, 'cap') and self.cap is not None:
                    self.cap.release()
    
    def update_overlay(self, text, confidence=0.0):
        """Update the overlay with detected gesture information and speak the text."""
        try:
            current_time = time.time()
            
            # Only update if we have a valid gesture with sufficient confidence
            display_text = text if confidence > 0.5 else 'No gesture detected'
            
            # Speak the detected text if it's new and has sufficient confidence
            if (confidence > 0.5 and 
                display_text != self.last_spoken_text and 
                (current_time - self.last_speak_time) > self.min_speak_interval):
                
                # Update last spoken text and time
                self.last_spoken_text = display_text
                self.last_speak_time = current_time
                
                # Speak the text in a non-blocking way
                threading.Thread(
                    target=self.tts.speak,
                    args=(display_text,),
                    daemon=True
                ).start()
            
            data = {
                'text': display_text,
                'confidence': confidence,
                'timestamp': current_time,
                'status': 'active' if confidence > 0.5 else 'waiting',
                'detection': {
                    'gesture': display_text,
                    'confidence': confidence,
                    'time_held': 0.0
                }
            }
            
            response = requests.post(
                self.overlay_url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=1.0
            )
            
            if response.status_code != 200:
                print(f"Failed to update overlay: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Error updating overlay: {e}")
    
    def run(self):
        """Run the gesture detection and overlay update loop."""
        if not self._init_camera():
            return
        
        self.running = True
        last_gesture = None
        last_update = 0
        
        print("Gesture detection started. Press 'q' to quit.")
        
        try:
            while self.running:
                # Capture frame
                ret, frame = self.cap.read()
                if not ret:
                    print("Failed to capture frame")
                    break
                
                # Process frame at ~10 FPS to reduce CPU usage
                current_time = time.time()
                if current_time - last_update >= 0.1:  # 10 FPS
                    # Process frame with gesture recognizer
                    gesture, confidence = self.gesture_recognizer.process_frame(frame)
                    
                    # Only update if we have a new gesture with sufficient confidence
                    if gesture and confidence > 0.7:  # Minimum confidence threshold
                        if gesture != last_gesture:
                            print(f"Detected gesture: {gesture} (Confidence: {confidence:.1%})")
                            self.update_overlay(gesture, confidence)
                            last_gesture = gesture
                    
                    last_update = current_time
                
                # Display the frame (for debugging)
                cv2.imshow('Gesture Detection', frame)
                
                # Check for quit key
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        except KeyboardInterrupt:
            print("\nStopping gesture detection...")
        except Exception as e:
            print(f"Error in gesture detection: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Release resources."""
        self.running = False
        if hasattr(self, 'cap') and self.cap is not None:
            self.cap.release()
        cv2.destroyAllWindows()
        print("Gesture detection stopped.")

# Global variable to store the current detection state
import time
from dataclasses import dataclass, asdict

@dataclass
class DetectionState:
    gesture: str = ''
    confidence: float = 0.0
    timestamp: float = 0.0
    status: str = 'waiting'
    last_updated: float = 0.0
    
    def to_dict(self):
        return {
            'gesture': self.gesture,
            'confidence': self.confidence,
            'timestamp': self.timestamp,
            'status': self.status,
            'detection': {
                'gesture': self.gesture,
                'confidence': self.confidence,
                'time_held': time.time() - self.timestamp if self.timestamp > 0 else 0.0
            }
        }

# Initialize global state
current_detection = DetectionState()

def start_overlay_server(port=8000):
    """Start a Flask server for the overlay with API endpoints."""
    from flask import Flask, request, jsonify, send_from_directory
    from flask_cors import CORS
    import json
    
    app = Flask(__name__, static_folder=os.path.join('..', 'obs_overlay'))
    CORS(app)  # Enable CORS for all routes
    
    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'overlay.html')
    
    @app.route('/<path:path>')
    def serve_static(path):
        return send_from_directory(app.static_folder, path)
    
    @app.route('/api/update', methods=['POST', 'OPTIONS'])
    def update_detection():
        global current_detection
        if request.method == 'OPTIONS':
            # Handle preflight request
            response = jsonify({'status': 'success'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
            response.headers.add('Access-Control-Allow-Methods', 'POST')
            return response
            
        try:
            data = request.get_json()
            if not data:
                return jsonify({'status': 'error', 'message': 'No data provided'}), 400
                
            new_text = data.get('text', '')
            new_confidence = float(data.get('confidence', 0))
            now = time.time()
            
            # Only update if there's a significant change or after a cooldown
            min_confidence_change = 0.1  # 10% confidence change threshold
            cooldown_period = 0.5  # 500ms cooldown between updates
            
            should_update = (
                (new_text != current_detection.gesture) or  # Text changed
                (abs(new_confidence - current_detection.confidence) > min_confidence_change) or  # Significant confidence change
                (now - current_detection.last_updated > cooldown_period)  # Cooldown period passed
            )
            
            if should_update and new_confidence > 0.1:  # Minimum confidence threshold
                current_detection.gesture = new_text
                current_detection.confidence = new_confidence
                current_detection.timestamp = now
                current_detection.status = 'active' if new_text else 'waiting'
                current_detection.last_updated = now
                
            response = jsonify({'status': 'success'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
            
        except Exception as e:
            print(f"Error in update_detection: {str(e)}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/current')
    def get_current_detection():
        response = jsonify(current_detection.to_dict())
        response.headers.add('Access-Control-Allow-Origin', '*')
        # Add cache control headers to prevent unnecessary requests
        response.headers.add('Cache-Control', 'no-cache, no-store, must-revalidate')
        response.headers.add('Pragma', 'no-cache')
        response.headers.add('Expires', '0')
        return response
    
    print(f"Overlay server running at http://localhost:{port}")
    print("Open this URL in OBS browser source:")
    print(f"http://localhost:{port}/overlay.html")
    
    # Change to the directory containing the overlay files
    os.chdir(os.path.join(os.path.dirname(__file__), '..', 'obs_overlay'))
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def main():
    parser = argparse.ArgumentParser(description='ASL Gesture Overlay Tester')
    parser.add_argument('--server-only', action='store_true', help='Only run the overlay server')
    parser.add_argument('--port', type=int, default=8000, help='Port for the overlay server')
    args = parser.parse_args()
    
    if args.server_only:
        start_overlay_server(args.port)
    else:
        # Start the overlay server in a separate thread
        server_thread = threading.Thread(target=start_overlay_server, args=(args.port,), daemon=True)
        server_thread.start()
        
        # Give the server a moment to start
        time.sleep(1)
        
        # Start the gesture detection
        tester = GestureOverlayTester({
            **CONFIG,
            'overlay': {**CONFIG['overlay'], 'port': args.port}
        })
        tester.run()

if __name__ == "__main__":
    main()
