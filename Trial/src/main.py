"""
ASL Translation Pipeline - Main Module

This is the main orchestrator for the ASL translation system.
It coordinates the webcam capture, gesture recognition, text processing,
TTS, and OBS overlay components.
"""

import os
import sys
import time
import argparse
import yaml
import cv2
import numpy as np
from loguru import logger
from pathlib import Path
from typing import Dict, Any, Optional

# Add src directory to path
sys.path.append(str(Path(__file__).parent))

# Import local modules
from gesture_recognizer import GestureRecognizer
from text_processor import TextProcessor
from tts_engine import TTSEngine
from obs_integration import OBSIntegration

class ASLTranslator:
    """Main class for the ASL translation pipeline."""
    
    def __init__(self, config_path: str = None):
        """Initialize the ASL translator with configuration."""
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Set up logging
        self._setup_logging()
        
        # Initialize components
        self.gesture_recognizer = GestureRecognizer(self.config)
        self.text_processor = TextProcessor(self.config)
        self.tts_engine = TTSEngine(self.config) if self.config.get('tts', {}).get('enabled', True) else None
        self.obs_integration = OBSIntegration(self.config) if self.config.get('obs', {}).get('enabled', True) else None
        
        # State
        self.is_running = False
        self.last_gesture = None
        self.last_text = ""
        self.frame_count = 0
        self.fps = 0
        self.last_fps_update = time.time()
        
        logger.info("ASL Translator initialized")
    
    def _load_config(self, config_path: str = None) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        # Default configuration
        default_config = {
            'camera': {
                'device_id': 0,
                'width': 1280,
                'height': 720,
                'fps': 30,
                'flip_horizontal': True
            },
            'gesture_recognizer': {
                'min_confidence': 0.7,
                'smoothing_window': 5
            },
            'text_processor': {
                'enable_grammar_correction': True,
                'min_confidence': 0.5,
                'gesture_mappings': {}
            },
            'tts': {
                'enabled': True,
                'engine': 'pyttsx3',  # or 'gtts'
                'rate': 150,
                'volume': 1.0,
                'voice': 0
            },
            'obs': {
                'enabled': True,
                'output_dir': 'output',
                'overlay_position': 'bottom',
                'auto_hide': True,
                'auto_hide_timeout': 5000  # ms
            },
            'debug': {
                'show_fps': True,
                'show_landmarks': True,
                'show_bbox': True,
                'log_level': 'INFO'
            }
        }
        
        # Load from file if provided
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    file_config = yaml.safe_load(f) or {}
                # Merge with defaults
                return self._deep_merge(default_config, file_config)
            except Exception as e:
                logger.error(f"Error loading config file: {e}")
        
        return default_config
    
    def _deep_merge(self, d1: Dict, d2: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = d1.copy()
        for k, v in d2.items():
            if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                result[k] = self._deep_merge(result[k], v)
            else:
                result[k] = v
        return result
    
    def _setup_logging(self):
        """Set up logging configuration."""
        log_level = self.config.get('debug', {}).get('log_level', 'INFO').upper()
        log_file = self.config.get('log_file', 'asl_translator.log')
        
        # Configure loguru
        logger.remove()  # Remove default handler
        
        # Add console handler
        logger.add(
            sys.stderr,
            level=log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
        
        # Add file handler if log file is specified
        if log_file:
            logger.add(
                log_file,
                level=log_level,
                rotation="10 MB",
                retention="10 days",
                compression="zip",
                enqueue=True
            )
    
    def _process_frame(self, frame: np.ndarray) -> Optional[Dict[str, Any]]:
        """Process a single frame through the pipeline."""
        # Process frame with gesture recognizer
        gesture_data = self.gesture_recognizer.process(frame)
        
        # If no hand detected, return None
        if not gesture_data or not gesture_data.get('gesture'):
            return None
        
        # Convert gesture to text
        text = self.text_processor.gesture_to_text(gesture_data)
        
        # Only process if we have text and it's different from last time
        if text and text != self.last_text:
            self.last_text = text
            
            # Update OBS overlay
            if self.obs_integration:
                self.obs_integration.update_overlay(text)
            
            # Speak the text
            if self.tts_engine:
                self.tts_engine.speak(text)
            
            logger.info(f"Detected: {text}")
        
        return gesture_data
    
    def _draw_debug_info(self, frame: np.ndarray, gesture_data: Optional[Dict[str, Any]]):
        """Draw debug information on the frame."""
        debug_config = self.config.get('debug', {})
        
        # Draw FPS
        if debug_config.get('show_fps', True):
            self._draw_fps(frame)
        
        # Draw gesture info if available
        if gesture_data and debug_config.get('show_bbox', True):
            self._draw_gesture_info(frame, gesture_data)
    
    def _draw_fps(self, frame: np.ndarray):
        """Draw FPS counter on the frame."""
        # Calculate FPS
        self.frame_count += 1
        now = time.time()
        if now - self.last_fps_update >= 1.0:  # Update FPS every second
            self.fps = self.frame_count / (now - self.last_fps_update)
            self.frame_count = 0
            self.last_fps_update = now
        
        # Draw FPS
        cv2.putText(
            frame, f"FPS: {self.fps:.1f}",
            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2
        )
    
    def _draw_gesture_info(self, frame: np.ndarray, gesture_data: Dict[str, Any]):
        """Draw gesture information on the frame."""
        gesture = gesture_data.get('gesture', '')
        confidence = gesture_data.get('confidence', 0)
        bbox = gesture_data.get('bbox')
        
        # Draw bounding box
        if bbox and self.config.get('debug', {}).get('show_bbox', True):
            x, y, w, h = bbox
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Draw label with confidence
            label = f"{gesture} ({confidence:.2f})"
            cv2.putText(
                frame, label, (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2
            )
    
    def run(self):
        """Run the main translation loop."""
        camera_config = self.config.get('camera', {})
        device_id = camera_config.get('device_id', 0)
        frame_width = camera_config.get('width', 1280)
        frame_height = camera_config.get('height', 720)
        
        # Open camera
        cap = cv2.VideoCapture(device_id)
        if not cap.isOpened():
            logger.error(f"Failed to open camera {device_id}")
            return
        
        # Set camera properties
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
        cap.set(cv2.CAP_PROP_FPS, camera_config.get('fps', 30))
        
        logger.info(f"Starting ASL translation with camera {device_id} ({frame_width}x{frame_height})")
        
        self.is_running = True
        
        try:
            while self.is_running:
                # Capture frame
                ret, frame = cap.read()
                if not ret:
                    logger.error("Failed to capture frame")
                    break
                
                # Flip frame if needed
                if camera_config.get('flip_horizontal', True):
                    frame = cv2.flip(frame, 1)
                
                # Process frame
                gesture_data = self._process_frame(frame.copy())
                
                # Draw debug info
                self._draw_debug_info(frame, gesture_data)
                
                # Show preview
                cv2.imshow('ASL Translator', frame)
                
                # Check for key press
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q') or key == 27:  # 'q' or ESC
                    break
                elif key == ord(' '):  # Space to toggle overlay
                    if self.obs_integration:
                        if self.obs_integration.overlay_data['show_overlay']:
                            self.obs_integration.hide_overlay()
                        else:
                            self.obs_integration.show_overlay()
        
        except KeyboardInterrupt:
            logger.info("Stopping...")
        
        finally:
            # Clean up
            self.is_running = False
            cap.release()
            cv2.destroyAllWindows()
            
            # Stop TTS if running
            if self.tts_engine:
                self.tts_engine.stop()
            
            logger.info("ASL Translator stopped")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='ASL Translator')
    parser.add_argument('--config', type=str, default='config/config.yaml',
                      help='Path to configuration file')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    # Create and run the translator
    translator = ASLTranslator(args.config)
    translator.run()
