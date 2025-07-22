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
import logging
import logging.handlers
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.handlers.RotatingFileHandler(
            'asl_gesture_overlay.log',
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
    ]
)

# Set log level for external libraries
logging.getLogger('werkzeug').setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
from urllib.parse import urlparse, parse_qs
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    def _speak_gesture(self, text):
        """Handle speaking the gesture with proper spacing and flow."""
        try:
            if not text or not text.strip():
                logger.warning("Attempted to speak empty text")
                return
                
            current_time = time.time()
            
            # Don't speak if we just spoke recently
            time_since_last_speak = current_time - self.last_speak_time
            if time_since_last_speak < self.min_speak_interval:
                logger.debug(f"Skipping speech - too soon since last speak: {time_since_last_speak:.2f}s < {self.min_speak_interval}s")
                return
            
            # Clean and prepare the text
            text = text.strip()
            
            # Add space between words if needed
            if (self.last_spoken_text and 
                self.last_spoken_text[-1].isalnum() and 
                text[0].isalnum()):
                text = ' ' + text
            
            logger.info(f"Speaking gesture: '{text}'")
            
            # Update last spoken text and time
            self.last_spoken_text = text
            self.last_speak_time = current_time
            
            # Ensure TTS is available
            if not hasattr(self, 'tts') or not self.tts:
                logger.error("TTS not initialized!")
                return
                
            # Log TTS engine info
            logger.debug(f"Using TTS engine: {type(self.tts).__name__}")
            
            # Speak the text in a non-blocking way
            speak_thread = threading.Thread(
                target=self._safe_speak,
                args=(text,),
                name=f"TTS-{text[:20]}{'...' if len(text) > 20 else ''}",
                daemon=True
            )
            speak_thread.start()
            logger.debug(f"Started TTS thread for: '{text}'")
            
        except Exception as e:
            logger.error(f"Error in _speak_gesture: {e}", exc_info=True)
    
    def _safe_speak(self, text):
        """Safely call the TTS speak method with error handling."""
        try:
            self.tts.speak(text, block=False)
            logger.debug(f"Successfully spoke: '{text}'")
        except Exception as e:
            logger.error(f"Error in TTS speak: {e}", exc_info=True)
        
    def __init__(self, config):
        self.config = config
        self.overlay_url = f"http://{config['overlay']['host']}:{config['overlay']['port']}{config['overlay']['endpoint']}"
        self.gesture_recognizer = GestureRecognizer()
        self.running = False
        self.cap = None
        
        # Initialize TTS and conversation state
        self.tts = TTSManager(lang='en', slow=False)
        self.last_spoken_text = ""
        self.last_speak_time = 0
        self.min_speak_interval = 0.8  # Reduced minimum time between phrases
        self.gesture_buffer = []
        self.buffer_size = 3  # Number of consistent detections required
        self.current_gesture = None
        self.gesture_start_time = 0
        
    def _init_camera(self):
        """Initialize the camera, trying both physical camera and OBS Virtual Camera."""
        max_attempts = 4  # Increased to try more camera sources
        for attempt in range(max_attempts):
            try:
                # Release any existing camera instance
                if hasattr(self, 'cap') and self.cap is not None:
                    self.cap.release()
                
                # Try different camera sources
                if attempt == 0:
                    # Try OBS Virtual Camera first (Windows)
                    self.cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)  # OBS Virtual Camera is often index 1
                    print("Trying OBS Virtual Camera...")
                elif attempt == 1:
                    # Try OBS Virtual Camera with different index
                    self.cap = cv2.VideoCapture(2, cv2.CAP_DSHOW)
                    print("Trying OBS Virtual Camera (index 2)...")
                elif attempt == 2:
                    # Try physical camera with DirectShow
                    self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                    print("Trying physical camera with DirectShow...")
                else:
                    # Last attempt with default backend
                    self.cap = cv2.VideoCapture(0)
                    print("Trying default camera...")
                
                if not self.cap.isOpened():
                    raise RuntimeError(f"Could not open camera (attempt {attempt + 1}/{max_attempts})")
                
                # Set camera properties with priority on speed
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Higher resolution for better recognition
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                self.cap.set(cv2.CAP_PROP_FPS, 30)  # 30 FPS is sufficient for ASL
                
                # For OBS Virtual Camera, we might not be able to set these properties
                if attempt < 2:  # Skip for OBS Virtual Camera attempts
                    try:
                        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
                        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimal buffer size
                    except:
                        pass
                else:
                    # For physical camera, try to optimize settings
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
    
    def update_overlay(self, text: str, confidence: float, speak: bool = True):
        """
        Update the OBS overlay with new text and confidence.
        Only sends updates for valid gestures with sufficient confidence.
        """
        try:
            current_time = time.time()
            min_confidence = self.config.get('gesture', {}).get('min_confidence', 0.7)

            if not text or confidence < min_confidence:
                return  # Don't push weak/empty gestures

            is_new = text != getattr(self, 'last_gesture', None)
            time_held = current_time - getattr(self, 'last_gesture_time', 0)

            data = {
                'text': text,
                'confidence': float(confidence),
                'timestamp': current_time,
                'status': 'active',
                'detection': {
                    'gesture': text,
                    'confidence': float(confidence),
                    'time_held': time_held,
                    'is_new': is_new
                }
            }

            self.last_gesture = text
            self.last_gesture_time = current_time

            response = requests.post(
                self.overlay_url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=1.0
            )

            if response.status_code != 200:
                logger.warning(f"Overlay update failed with status {response.status_code}")
            else:
                logger.debug(f"Updated overlay: {text} (Confidence: {confidence:.1%})")

            if speak and hasattr(self, 'tts') and self.tts:
                self._speak_gesture(text)

        except requests.RequestException as e:
            logger.error(f"Failed to update overlay: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in update_overlay: {e}")
        time.sleep(0.05)

    def run(self):
        """Run the gesture detection and overlay update loop."""
        if not self._init_camera():
            return

        self.running = True
        last_gesture = None
        last_update = 0
        last_gesture_time = 0
        last_spoken_time = 0
        gesture_hold_time = 0
        min_gesture_duration = 0.8
        gesture_cooldown = 1.5

        print("Gesture detection started. Press 'q' to quit.")

        try:
            while self.running:
                current_time = time.time()

                # Capture frame
                ret, frame = self.cap.read()
                if not ret:
                    print("Failed to capture frame")
                    break

                # Run detection every ~0.1s
                if current_time - last_update >= 0.1:
                    gesture, confidence = self.gesture_recognizer.process_frame(frame)

                    if gesture and confidence > 0.7:
                        if gesture == last_gesture:
                            gesture_hold_time = current_time - last_gesture_time
                        else:
                            last_gesture = gesture
                            last_gesture_time = current_time
                            gesture_hold_time = 0

                        # Always update the overlay visually
                        self.update_overlay(gesture, confidence, speak=False)

                        # Speak after hold & cooldown
                        if gesture_hold_time >= min_gesture_duration and (current_time - last_spoken_time) >= gesture_cooldown:
                            self.update_overlay(gesture, confidence, speak=True)
                            last_spoken_time = current_time
                    else:
                        # Do not clear overlay on weak gestures
                        pass

                    last_update = current_time

                # Optional: show live frame
                cv2.imshow('Gesture Detection', frame)
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
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class Detection:
    text: str = 'No gesture detected'
    confidence: float = 0.0
    timestamp: float = 0.0
    status: str = 'waiting'
    detection: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.detection is None:
            self.detection = {
                'gesture': self.text,
                'confidence': self.confidence,
                'time_held': 0.0
            }

# Global state for the current detection
current_detection = Detection()

def start_overlay_server(port=8000):
    """Start a Flask server for the overlay with API endpoints."""
    from flask import Flask, jsonify, request, make_response, send_from_directory
    from flask_cors import CORS
    import json
    
    app = Flask(__name__, static_folder=os.path.join('..', 'obs_overlay'))
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:8000", "http://127.0.0.1:8000"],
            "methods": ["GET", "OPTIONS"],
            "allow_headers": ["Content-Type"]
        }
    })
    
    # Rate limiting
    from functools import wraps
    from time import time
    
    RATE_LIMIT = 10  # Max requests per second
    last_request_time = 0
    
    def rate_limited(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            nonlocal last_request_time
            current_time = time()
            time_since_last = current_time - last_request_time
            
            # Enforce minimum time between requests (100ms)
            min_interval = 1.0 / RATE_LIMIT
            if time_since_last < min_interval:
                return make_response('Too many requests', 429)
            
            last_request_time = current_time
            return f(*args, **kwargs)
        return decorated_function
    
    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'overlay.html')
    
    @app.route('/<path:path>')
    def serve_static(path):
        return send_from_directory(app.static_folder, path)
    
    @app.route('/api/update', methods=['POST', 'OPTIONS'])
    @rate_limited
    def update_detection():
        global current_detection
        if request.method == 'OPTIONS':
            response = make_response()
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
            response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
            return response
            
        try:
            data = request.get_json(force=True)
            if not data:
                return jsonify({'status': 'error', 'message': 'No data provided'}), 400
                
            # Get current timestamp
            import time as time_module
            current_time = time_module.time()
            
            current_detection = Detection(
                text=data.get('text', 'No gesture detected'),
                confidence=float(data.get('confidence', 0.0)),
                timestamp=current_time,
                status='active' if float(data.get('confidence', 0.0)) > 0.5 else 'waiting',
                detection={
                    'gesture': data.get('text'),
                    'confidence': float(data.get('confidence', 0.0)),
                    'time_held': 0.0
                }
            )
            
            # Only log successful updates
            if float(data.get('confidence', 0)) > 0.7:
                print(f"Updated detection: {current_detection.text} (Confidence: {current_detection.confidence:.2f})")
                
            response = jsonify({'status': 'success'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
            
        except Exception as e:
            print(f"Error in update_detection: {str(e)}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/current', methods=['GET', 'OPTIONS'])
    @rate_limited
    def get_current():
        try:
            # Convert Detection object to dict
            detection_dict = {
                'text': current_detection.text,
                'confidence': current_detection.confidence,
                'timestamp': current_detection.timestamp,
                'status': current_detection.status,
                'detection': current_detection.detection
            }
            response = jsonify(detection_dict)
            # Add cache control headers
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response
        except Exception as e:
            print(f"Error in get_current: {e}")
            return jsonify({
                'text': 'Error',
                'confidence': 0.0,
                'timestamp': time.time(),
                'status': 'error',
                'detection': {'gesture': 'Error', 'confidence': 0.0, 'time_held': 0.0}
            })
    
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
