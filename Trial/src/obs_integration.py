"""
OBS Integration Module

This module provides functionality to integrate with OBS (Open Broadcaster Software)
for displaying the ASL translation overlay and managing virtual camera output.
"""

import os
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from loguru import logger

class OBSIntegration:
    """Handles OBS integration for displaying ASL translation overlay."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the OBS integration with configuration."""
        self.config = config.get('obs', {})
        self.overlay_file = self._get_overlay_path()
        self.overlay_data = {
            'text': '',
            'timestamp': 0,
            'show_overlay': False,
            'position': self.config.get('overlay_position', 'bottom')
        }
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(self.overlay_file), exist_ok=True)
        
        # Initialize the overlay file
        self._update_overlay_file()
        
        logger.info(f"OBS Integration initialized. Overlay file: {self.overlay_file}")
    
    def _get_overlay_path(self) -> str:
        """Get the path to the overlay data file."""
        output_dir = self.config.get('output_dir', 'output')
        return os.path.join(output_dir, 'obs_overlay.json')
    
    def _update_overlay_file(self):
        """Update the overlay JSON file with current data."""
        try:
            with open(self.overlay_file, 'w') as f:
                json.dump(self.overlay_data, f)
        except Exception as e:
            logger.error(f"Failed to update overlay file: {e}")
    
    def update_overlay(self, text: str, show: bool = True):
        """
        Update the overlay text and visibility.
        
        Args:
            text: The text to display in the overlay
            show: Whether to show the overlay
        """
        if not text:
            text = ''
            
        self.overlay_data.update({
            'text': text,
            'timestamp': time.time(),
            'show_overlay': show and bool(text)
        })
        
        self._update_overlay_file()
    
    def show_overlay(self, text: Optional[str] = None):
        """
        Show the overlay with optional text update.
        
        Args:
            text: Optional text to update before showing
        """
        if text is not None:
            self.overlay_data['text'] = text
        self.overlay_data['show_overlay'] = True
        self._update_overlay_file()
    
    def hide_overlay(self):
        """Hide the overlay."""
        self.overlay_data['show_overlay'] = False
        self._update_overlay_file()
    
    def set_position(self, position: str):
        """
        Set the overlay position.
        
        Args:
            position: Position of the overlay ('top', 'bottom', 'left', 'right')
        """
        if position in ['top', 'bottom', 'left', 'right']:
            self.overlay_data['position'] = position
            self._update_overlay_file()
    
    def get_overlay_html(self) -> str:
        """
        Generate the HTML content for the OBS browser source.
        
        Returns:
            str: HTML content for the OBS browser source
        """
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>ASL Translation Overlay</title>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    overflow: hidden;
                    font-family: 'Arial', sans-serif;
                }}
                #overlay {{
                    position: absolute;
                    color: white;
                    background-color: rgba(0, 0, 0, 0.7);
                    padding: 15px 25px;
                    border-radius: 10px;
                    font-size: 24px;
                    max-width: 90%;
                    text-align: center;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
                    opacity: 0;
                    transition: opacity 0.3s ease-in-out;
                    word-wrap: break-word;
                }}
                #overlay.visible {{
                    opacity: 1;
                }}
                #overlay.top {{
                    top: 20px;
                    left: 50%;
                    transform: translateX(-50%);
                }}
                #overlay.bottom {{
                    bottom: 20px;
                    left: 50%;
                    transform: translateX(-50%);
                }}
                #overlay.left {{
                    left: 20px;
                    top: 50%;
                    transform: translateY(-50%);
                }}
                #overlay.right {{
                    right: 20px;
                    top: 50%;
                    transform: translateY(-50%);
                }}
            </style>
        </head>
        <body>
            <div id="overlay" class=""></div>
            
            <script>
                const overlay = document.getElementById('overlay');
                let lastUpdate = 0;
                const TIMEOUT = 5000; // 5 seconds
                
                function updateOverlay() {{
                    fetch('{self.overlay_file}?t=' + new Date().getTime())
                        .then(response => response.json())
                        .then(data => {{
                            // Only update if the data is newer
                            if (data.timestamp > lastUpdate) {{
                                lastUpdate = data.timestamp;
                                overlay.textContent = data.text;
                                
                                // Update position class
                                overlay.className = '';
                                overlay.classList.add(data.position || 'bottom');
                                
                                // Show/hide overlay
                                if (data.show_overlay) {{
                                    overlay.classList.add('visible');
                                }} else {{
                                    overlay.classList.remove('visible');
                                }}
                                
                                // Auto-hide after timeout if enabled
                                if (data.show_overlay && {str(self.config.get('auto_hide', True)).lower()}) {{
                                    setTimeout(() => {{
                                        overlay.classList.remove('visible');
                                    }}, {self.config.get('auto_hide_timeout', TIMEOUT)});
                                }}
                            }}
                        }})
                        .catch(error => {{
                            console.error('Error fetching overlay data:', error);
                        }});
                }}
                
                // Update immediately and then every second
                updateOverlay();
                setInterval(updateOverlay, 1000);
            </script>
        </body>
        </html>
        """
    
    def save_overlay_html(self, path: Optional[str] = None):
        """
        Save the overlay HTML to a file.
        
        Args:
            path: Optional custom path to save the HTML file
        """
        if path is None:
            output_dir = self.config.get('output_dir', 'output')
            os.makedirs(output_dir, exist_ok=True)
            path = os.path.join(output_dir, 'asl_overlay.html')
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(self.get_overlay_html())
            logger.info(f"Saved OBS overlay HTML to: {path}")
            return path
        except Exception as e:
            logger.error(f"Failed to save overlay HTML: {e}")
            return None
    
    def get_obs_instructions(self) -> str:
        """
        Get instructions for setting up OBS with this overlay.
        
        Returns:
            str: Instructions for OBS setup
        """
        overlay_path = self.save_overlay_html()
        return f"""
        ===== OBS Setup Instructions =====
        
        1. In OBS, add a new Browser Source
        2. Set the URL to: file:///{os.path.abspath(overlay_path)}
        3. Set the width to 1920 and height to 1080 (or your canvas size)
        4. Check 'Shutdown source when not visible' and 'Refresh browser when scene becomes active'
        5. Click OK to add the source
        6. Position and resize the overlay as needed in your scene
        
        The overlay will automatically update with the latest translation text.
        """

# Example usage
if __name__ == "__main__":
    # Example configuration
    config = {
        'obs': {
            'output_dir': 'output',
            'overlay_position': 'bottom',
            'auto_hide': True,
            'auto_hide_timeout': 5000  # 5 seconds
        }
    }
    
    # Create OBS integration
    obs = OBSIntegration(config)
    
    # Update overlay with some text
    obs.update_overlay("Hello, this is a test message!")
    
    # Save the overlay HTML
    html_path = obs.save_overlay_html()
    
    # Print instructions
    print(obs.get_obs_instructions())
    print(f"\nOverlay HTML saved to: {html_path}")
    print("Use the OBS instructions above to set up the overlay in OBS.")
