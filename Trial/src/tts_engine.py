"""
Text-to-Speech Engine Module

This module provides text-to-speech functionality using multiple backends,
including pyttsx3 (offline) and gTTS (online). It handles speech synthesis,
voice selection, and audio playback.
"""

import os
import queue
import threading
import time
from typing import Dict, Any, Optional, List
import logging
from loguru import logger

# Try to import TTS libraries
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    logger.warning("pyttsx3 not available. Install with: pip install pyttsx3")

try:
    from gtts import gTTS
    import pygame
    pygame.mixer.init()
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    logger.warning("gTTS or pygame not available. Install with: pip install gtts pygame")

class TTSEngine:
    """Text-to-Speech engine with support for multiple backends."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the TTS engine with configuration."""
        self.config = config.get('tts', {})
        self.engine = None
        self.voices = []
        self.current_voice = None
        self.is_speaking = False
        self.audio_queue = queue.Queue()
        self.playback_thread = None
        self.stop_event = threading.Event()
        
        # Initialize the selected TTS engine
        self.engine_type = self.config.get('engine', 'pyttsx3' if PYTTSX3_AVAILABLE else 'gtts')
        self._init_engine()
        
        # Start the playback thread
        self._start_playback_thread()
    
    def _init_engine(self):
        """Initialize the selected TTS engine."""
        if self.engine_type == 'pyttsx3' and PYTTSX3_AVAILABLE:
            self._init_pyttsx3()
        elif self.engine_type == 'gtts' and GTTS_AVAILABLE:
            self._init_gtts()
        else:
            logger.warning(f"No suitable TTS engine available. TTS will be disabled.")
    
    def _init_pyttsx3(self):
        """Initialize the pyttsx3 TTS engine."""
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', self.config.get('rate', 150))
            self.engine.setProperty('volume', self.config.get('volume', 1.0))
            
            # Get available voices
            self.voices = self.engine.getProperty('voices')
            
            # Set voice if specified
            voice_id = self.config.get('voice')
            if voice_id and voice_id < len(self.voices):
                self.engine.setProperty('voice', self.voices[voice_id].id)
                self.current_voice = voice_id
            
            logger.info("Initialized pyttsx3 TTS engine")
            
        except Exception as e:
            logger.error(f"Failed to initialize pyttsx3: {e}")
            self.engine = None
    
    def _init_gtts(self):
        """Initialize the gTTS engine."""
        if not GTTS_AVAILABLE:
            logger.error("gTTS is not available")
            return
            
        # No initialization needed for gTTS
        logger.info("Initialized gTTS engine")
    
    def _start_playback_thread(self):
        """Start the audio playback thread."""
        if self.playback_thread and self.playback_thread.is_alive():
            return
            
        self.stop_event.clear()
        self.playback_thread = threading.Thread(
            target=self._playback_worker,
            daemon=True
        )
        self.playback_thread.start()
    
    def _playback_worker(self):
        """Worker thread for playing audio from the queue."""
        while not self.stop_event.is_set():
            try:
                # Get audio data from queue with timeout
                audio_data = self.audio_queue.get(timeout=0.1)
                
                if audio_data is None:  # Sentinel value to stop the thread
                    break
                    
                self._play_audio(audio_data)
                self.audio_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in playback worker: {e}")
    
    def _play_audio(self, audio_data):
        """Play audio data using the appropriate method."""
        if self.engine_type == 'pyttsx3' and self.engine:
            self._play_pyttsx3(audio_data)
        elif self.engine_type == 'gtts' and GTTS_AVAILABLE:
            self._play_gtts(audio_data)
    
    def _play_pyttsx3(self, text):
        """Play text using pyttsx3."""
        try:
            self.is_speaking = True
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            logger.error(f"Error in pyttsx3 playback: {e}")
        finally:
            self.is_speaking = False
    
    def _play_gtts(self, text):
        """Play text using gTTS with pygame."""
        try:
            # Create temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                temp_file = f.name
            
            # Generate speech
            tts = gTTS(text=text, lang='en')
            tts.save(temp_file)
            
            # Play with pygame
            self.is_speaking = True
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy() and not self.stop_event.is_set():
                time.sleep(0.1)
            
            # Clean up
            pygame.mixer.music.unload()
            if os.path.exists(temp_file):
                os.remove(temp_file)
                
        except Exception as e:
            logger.error(f"Error in gTTS playback: {e}")
        finally:
            self.is_speaking = False
    
    def speak(self, text: str, block: bool = False):
        """
        Convert text to speech and play it.
        
        Args:
            text: The text to speak
            block: If True, block until speech is complete
        """
        if not text.strip():
            return
            
        logger.debug(f"Speaking: {text}")
        
        if block:
            self._play_audio(text)
        else:
            self.audio_queue.put(text)
    
    def stop(self):
        """Stop any ongoing speech and clear the queue."""
        # Clear the queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
                self.audio_queue.task_done()
            except queue.Empty:
                break
        
        # Stop any ongoing playback
        if self.engine_type == 'gtts' and GTTS_AVAILABLE:
            try:
                pygame.mixer.music.stop()
            except:
                pass
        
        self.is_speaking = False
    
    def set_voice(self, voice_id: int):
        """Set the voice to use for speech synthesis."""
        if not self.engine or self.engine_type != 'pyttsx3':
            logger.warning("Voice selection is only supported with pyttsx3")
            return False
            
        if 0 <= voice_id < len(self.voices):
            self.engine.setProperty('voice', self.voices[voice_id].id)
            self.current_voice = voice_id
            return True
        return False
    
    def set_rate(self, rate: int):
        """Set the speech rate in words per minute."""
        if self.engine and self.engine_type == 'pyttsx3':
            self.engine.setProperty('rate', rate)
        self.config['rate'] = rate
    
    def set_volume(self, volume: float):
        """Set the volume (0.0 to 1.0)."""
        if self.engine and self.engine_type == 'pyttsx3':
            self.engine.setProperty('volume', volume)
        self.config['volume'] = volume
    
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get a list of available voices."""
        if not self.engine or self.engine_type != 'pyttsx3':
            return []
            
        return [
            {
                'id': i,
                'name': voice.name,
                'languages': voice.languages or [],
                'gender': 'male' if 'male' in str(voice.gender).lower() else 'female' if 'female' in str(voice.gender).lower() else 'unknown'
            }
            for i, voice in enumerate(self.voices)
        ]
    
    def is_busy(self) -> bool:
        """Check if the TTS engine is currently speaking."""
        return self.is_speaking or not self.audio_queue.empty()
    
    def __del__(self):
        """Clean up resources."""
        self.stop()
        self.stop_event.set()
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join(timeout=1.0)

# Example usage
if __name__ == "__main__":
    # Example configuration
    config = {
        'tts': {
            'engine': 'pyttsx3',  # or 'gtts'
            'rate': 150,
            'volume': 1.0,
            'voice': 0
        }
    }
    
    # Create TTS engine
    tts = TTSEngine(config)
    
    # List available voices (pyttsx3 only)
    if tts.engine_type == 'pyttsx3':
        print("Available voices:")
        for i, voice in enumerate(tts.get_available_voices()):
            print(f"{i}: {voice['name']} ({voice['gender']}) - {voice['languages']}")
    
    # Test speech
    print("Testing TTS...")
    tts.speak("Hello, this is a test of the text-to-speech engine.", block=True)
    print("Done.")
