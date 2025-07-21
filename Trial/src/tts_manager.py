"""
Text-to-Speech Manager for ASL Translator

This module provides natural-sounding text-to-speech functionality
for the ASL Translator application.
"""

import os
import tempfile
import threading
from gtts import gTTS
import pygame
import time
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TTSManager:
    """Manages text-to-speech functionality for the ASL Translator."""
    
    def __init__(self, lang: str = 'en', slow: bool = False):
        """Initialize the TTS manager.
        
        Args:
            lang: Language code (e.g., 'en' for English)
            slow: Whether to speak slowly
        """
        self.lang = lang
        self.slow = slow
        self.is_playing = False
        self.current_file: Optional[str] = None
        self.playback_thread: Optional[threading.Thread] = None
        self.stop_playback = threading.Event()
        
        # Initialize pygame mixer for audio playback
        self._init_audio()
    
    def _init_audio(self):
        """Initialize the audio system."""
        try:
            pygame.mixer.init()
            pygame.mixer.music.set_volume(1.0)  # Maximum volume
        except Exception as e:
            logger.error(f"Failed to initialize audio: {e}")
    
    def speak(self, text: str, block: bool = False):
        """Convert text to speech and play it.
        
        Args:
            text: The text to speak
            block: If True, block until speech is finished
        """
        if not text or text == 'No gesture detected':
            return
            
        # Stop any currently playing speech
        self.stop()
        
        try:
            # Create a temporary file for the speech
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
                temp_file = f.name
            
            # Generate speech using gTTS
            tts = gTTS(text=text, lang=self.lang, slow=self.slow)
            tts.save(temp_file)
            self.current_file = temp_file
            
            # Play the speech in a separate thread to avoid blocking
            self.playback_thread = threading.Thread(
                target=self._play_audio,
                args=(temp_file,)
            )
            self.playback_thread.daemon = True
            self.playback_thread.start()
            
            if block:
                self.playback_thread.join()
                
        except Exception as e:
            logger.error(f"Error in text-to-speech: {e}")
            if os.path.exists(temp_file):
                try:
                    os.unlink(temp_file)
                except:
                    pass
    
    def _play_audio(self, file_path: str):
        """Play the audio file."""
        try:
            self.is_playing = True
            self.stop_playback.clear()
            
            # Load and play the audio file
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            
            # Wait for playback to finish or stop signal
            while pygame.mixer.music.get_busy() and not self.stop_playback.is_set():
                time.sleep(0.1)
                
            pygame.mixer.music.stop()
            
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
        finally:
            self.is_playing = False
            # Clean up the temporary file
            if os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                except Exception as e:
                    logger.warning(f"Could not delete temp file {file_path}: {e}")
    
    def stop(self):
        """Stop any currently playing speech."""
        if self.is_playing:
            self.stop_playback.set()
            pygame.mixer.music.stop()
            
            if self.playback_thread and self.playback_thread.is_alive():
                self.playback_thread.join(timeout=1.0)
    
    def __del__(self):
        """Clean up resources."""
        self.stop()
        if hasattr(pygame, 'mixer') and pygame.mixer.get_init() is not None:
            pygame.mixer.quit()


# Global instance for easy access
tts_manager = TTSManager(lang='en', slow=False)


def speak(text: str, block: bool = False):
    """Speak the given text using the global TTS manager.
    
    Args:
        text: The text to speak
        block: If True, block until speech is finished
    """
    tts_manager.speak(text, block)


if __name__ == "__main__":
    # Test the TTS functionality
    print("Testing TTS...")
    speak("Hello, this is a test of the text-to-speech system.", block=True)
    print("Done.")
