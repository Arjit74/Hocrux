#!/usr/bin/env python3
"""
ASL Translation Pipeline - Main Application

This script captures video from the webcam, processes frames to detect ASL gestures,
and displays the recognized text in an OBS overlay with confidence scores.
"""

import os
import sys
import time
import json
import logging
import cv2
import requests
import pyttsx3
import argparse
import threading
from typing import Tuple, Optional, Dict, Any

# Import the gesture recognizer and overlay server
from gesture_recognizer import GestureRecognizer
from overlay_server import start_server as start_overlay_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('asl_translator.log')
    ]
)
logger = logging.getLogger(__name__)

class ASLTranslator:
    """Main class for the ASL translation pipeline."""
    
    def __init__(self, config_path: str = None):
        """Initialize the ASL translator with optional configuration."""
        self.config = self._load_config(config_path)
        self.cap = None
        self.running = False
        self.overlay_url = f"http://{self.config['overlay']['host']}:{self.config['overlay']['port']}/api/update"
        self.last_gesture_time = 0
        self.current_gesture = None
        
        # Start the overlay server in a separate thread
        self._start_overlay_server()
        
        # Initialize components
        self._init_camera()
        self._init_gesture_recognizer()
        self._init_tts()
        
        logger.info("ASL Translator initialized")
    
    def _load_config(self, config_path: Optional[str] = None) -> dict:
        """Load configuration from file or use defaults."""
        default_config = {
            'camera': {
                'device_id': 1,  # Try 1 for OBS Virtual Camera, or 0 for default
                'width': 1280,
                'height': 720,
                'fps': 30
            },
            'overlay': {
                'host': 'localhost',
                'port': 8000,
                'auto_hide': True,
                'hide_timeout': 5000
            },
            'gesture': {
                'min_confidence': 0.7,
                'update_interval': 0.5,  # seconds
                'min_detection_confidence': 0.7,
                'min_tracking_confidence': 0.5
            },
            'tts': {
                'enabled': True,
                'engine': 'pyttsx3',  # or 'gtts'
                'rate': 150,
                'volume': 1.0,
                'voice': None  # None for default voice
            },
            'debug': {
                'show_video': True
            }
        }
        
        # TODO: Load from config file if provided
        return default_config
    
    def _start_overlay_server(self):
        """Start the overlay server in a separate thread."""
        def run_server():
            start_overlay_server(
                host=self.config['overlay']['host'],
                port=self.config['overlay']['port'],
                debug=False
            )
        
        # Start the overlay server in a daemon thread
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        logger.info(f"Overlay server started at http://{self.config['overlay']['host']}:{self.config['overlay']['port']}")

    def _init_camera(self):
        """Initialize the camera with configured settings."""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # Try different camera backends
                if attempt == 0:
                    # First try with DirectShow (works well on Windows)
                    self.cap = cv2.VideoCapture(self.config['camera']['device_id'], cv2.CAP_DSHOW)
                elif attempt == 1:
                    # Fall back to default backend
                    self.cap = cv2.VideoCapture(self.config['camera']['device_id'])
                else:
                    # Last attempt with different device ID (useful for OBS Virtual Camera)
                    self.cap = cv2.VideoCapture(1)  # Try device ID 1 (OBS Virtual Camera)
                
                if not self.cap.isOpened():
                    raise RuntimeError(f"Could not open camera (attempt {attempt + 1}/{max_attempts})")
                
                # Set camera properties
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config['camera']['width'])
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config['camera']['height'])
                self.cap.set(cv2.CAP_PROP_FPS, self.config['camera']['fps'])
                
                # Test frame capture
                ret, frame = self.cap.read()
                if not ret:
                    raise RuntimeError("Could not read frame from camera")
                
                logger.info(f"Camera initialized: {self.config['camera']['width']}x{self.config['camera']['height']} @ {self.config['camera']['fps']}fps")
                return
                
            except Exception as e:
                if attempt == max_attempts - 1:
                    logger.error(f"Failed to initialize camera after {max_attempts} attempts: {e}")
                    raise
                logger.warning(f"Camera initialization attempt {attempt + 1} failed: {e}")
                if hasattr(self, 'cap') and self.cap is not None:
                    self.cap.release()
    
    def _init_gesture_recognizer(self):
        """Initialize the gesture recognizer."""
        self.gesture_recognizer = GestureRecognizer(
            min_detection_confidence=self.config['gesture']['min_detection_confidence'],
            min_tracking_confidence=self.config['gesture']['min_tracking_confidence']
        )
    
    def _init_tts(self):
        """Initialize the text-to-speech engine with enhanced settings."""
        if not self.config['tts']['enabled']:
            self.tts_engine = None
            return

        try:
            # Initialize TTS engine with debug logging
            logger.info("Initializing TTS engine...")
            self.tts_engine = pyttsx3.init()
            
            # Get available voices for debugging
            voices = self.tts_engine.getProperty('voices')
            logger.info(f"Available TTS voices: {[v.name for v in voices]}")
            
            # Set TTS properties
            self.tts_engine.setProperty('rate', self.config['tts']['rate'])
            self.tts_engine.setProperty('volume', self.config['tts']['volume'])
            
            # Set voice if specified, otherwise use first available voice
            if self.config['tts']['voice']:
                self.tts_engine.setProperty('voice', self.config['tts']['voice'])
            elif voices:
                # Try to find an English voice
                for voice in voices:
                    if 'english' in voice.languages[0].lower() if voice.languages else False:
                        self.tts_engine.setProperty('voice', voice.id)
                        logger.info(f"Using voice: {voice.name}")
                        break
                
            logger.info("TTS engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize TTS: {e}")
            logger.warning("TTS will be disabled due to initialization error")
            self.tts_engine = None
    
    def recognize_gesture(self, frame) -> Tuple[str, float]:
        """
        Recognize ASL gesture from a video frame.
        
        Args:
            frame: Input video frame
            
        Returns:
            Tuple of (recognized_text, confidence)
        """
        # TODO: Replace with actual gesture recognition
        gestures = [
            ("Hello!", 0.92),
            ("How are you?", 0.85),
            ("My name is...", 0.88),
            ("Thank you!", 0.95),
            ("I need help", 0.82)
        ]
        
        # Simple round-robin for demo
        index = int(time.time() * 0.5) % len(gestures)
        return gestures[index]
    
    def update_overlay(self, text: str, confidence: float, speak: bool = True):
        """
        Update the OBS overlay with new text and confidence.
        
        Args:
            text: The text to display in the overlay
            confidence: Confidence score of the recognition (0.0-1.0)
            speak: Whether to trigger TTS for this update
        """
        try:
            # Format the data with additional information
            data = {
                'text': text,
                'confidence': f"{confidence:.1%}",
                'timestamp': time.time(),
                'status': 'active' if text else 'waiting',
                'detection': {
                    'gesture': text,
                    'confidence': confidence,
                    'time_held': time.time() - getattr(self, 'last_gesture_time', 0)
                }
            }
            
            # Send update to overlay server with timeout
            response = requests.post(
                self.overlay_url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=1.0
            )
            
            # Log the response for debugging
            if response.status_code != 200:
                logger.warning(f"Overlay update failed with status {response.status_code}")
            
            # Speak the text if requested and TTS is enabled
            if speak and text and self.tts_engine:
                self.speak(text)
                
            # Store the last gesture time for tracking
            if text:
                self.last_gesture_time = time.time()
                    
        except requests.RequestException as e:
            logger.error(f"Failed to update overlay: {e}")
            
        # Small delay to prevent overwhelming the overlay server
        time.sleep(0.05)
    
    def speak(self, text: str):
        """Convert text to speech if TTS is enabled with better error handling."""
        if not text.strip():
            return
            
        if self.tts_engine is None:
            logger.warning("TTS engine is not initialized")
            return
        
        try:
            logger.info(f"Speaking: {text}")
            
            # Special handling for single letters
            if len(text.strip()) == 1 and text.isalpha():
                # Add a small pause before and after the letter for clarity
                self.tts_engine.say(f"The letter {text}")
            else:
                self.tts_engine.say(text)
                
            self.tts_engine.runAndWait()
            logger.debug("TTS playback completed")
            
        except RuntimeError as e:
            if "run loop already started" in str(e).lower():
                # Try to reinitialize the TTS engine if it's in a bad state
                logger.warning("TTS engine in bad state, attempting to reinitialize...")
                try:
                    self.tts_engine.endLoop()
                    self.tts_engine = None
                    self._init_tts()
                    if self.tts_engine:
                        self.tts_engine.say(text)
                        self.tts_engine.runAndWait()
                except Exception as reinit_error:
                    logger.error(f"Failed to reinitialize TTS: {reinit_error}")
            else:
                logger.error(f"TTS RuntimeError: {e}")
                
        except Exception as e:
            logger.error(f"Error in TTS: {e}")
            logger.warning("TTS will be disabled due to error")
            self.tts_engine = None
    
    def run(self):
        """Run the main translation loop."""
        self.running = True
        last_update = 0
        last_gesture = None
        last_gesture_time = 0
        gesture_hold_time = 0
        min_gesture_duration = 0.8  # seconds to hold gesture before recognition
        gesture_cooldown = 1.5  # seconds before same gesture can be recognized again
        current_time = time.time()
        
        logger.info("Starting ASL translation pipeline...")
        
        try:
            while self.running:
                current_time = time.time()
                # Capture frame
                ret, frame = self.cap.read()
                if not ret:
                    logger.error("Failed to capture frame")
                    break
                
                # Get current time
                current_time = time.time()
                
                # Process frame at configured interval
                if current_time - last_update >= self.config['gesture']['update_interval']:
                    # Process frame with gesture recognizer
                    gesture, confidence = self.gesture_recognizer.process_frame(frame)
                    
                    # Update overlay at regular intervals
                    if current_time - last_update >= self.config['gesture']['update_interval']:
                        if gesture and confidence >= self.config['gesture']['min_confidence']:
                            # Track gesture hold time
                            if gesture == last_gesture:
                                gesture_hold_time = current_time - last_gesture_time
                            else:
                                last_gesture = gesture
                                last_gesture_time = current_time
                                gesture_hold_time = 0
                            
                            # Only update if gesture is held long enough
                            if gesture_hold_time >= min_gesture_duration:
                                # Check if we should speak (new gesture or cooldown passed)
                                should_speak = (
                                    last_gesture != gesture or 
                                    (current_time - last_gesture_time) >= gesture_cooldown
                                )
                                
                                logger.info(f"Recognized: {gesture} (Confidence: {confidence:.2f}, Hold: {gesture_hold_time:.1f}s)")
                                self.update_overlay(gesture, confidence, speak=should_speak)
                                
                                # Reset timing for cooldown
                                if should_speak:
                                    last_gesture_time = current_time
                    
                    last_update = current_time
                
                # Draw debug information
                if self.config.get('debug', {}).get('show_video', False):
                    # Draw landmarks on the frame
                    debug_frame = self.gesture_recognizer.draw_landmarks(frame)
                    
                    # Display the recognized gesture
                    if last_gesture:
                        cv2.putText(
                            debug_frame, 
                            f"{last_gesture} ({confidence:.2f})", 
                            (10, 50), 
                            cv2.FONT_HERSHEY_SIMPLEX, 
                            1, 
                            (0, 255, 0), 
                            2, 
                            cv2.LINE_AA
                        )
                    
                    # Show the frame
                    cv2.imshow('ASL Translator', debug_frame)
                    
                    # Check for exit key
                    if cv2.waitKey(1) & 0xFF in (ord('q'), 27):  # 'q' or ESC
                        break
                        
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Release resources and clean up."""
        self.running = False
        
        if self.cap and self.cap.isOpened():
            self.cap.release()
            
        cv2.destroyAllWindows()
        logger.info("ASL Translator shutdown complete")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='ASL Translation Pipeline')
    parser.add_argument('--config', type=str, help='Path to config file')
    parser.add_argument('--device', type=int, default=0, help='Camera device ID')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--no-tts', action='store_true', help='Disable text-to-speech')
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        translator = ASLTranslator(config_path=args.config)
        
        # Override config with command line arguments
        if args.device is not None:
            translator.config['camera']['device_id'] = args.device
        if args.no_tts:
            translator.config['tts']['enabled'] = False
        if args.debug:
            translator.config['debug'] = {'show_video': True}
        
        translator.run()
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
