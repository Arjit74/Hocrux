"""
OBS Overlay Server for ASL Translator

This server provides a web-based overlay that can be captured by OBS.
It receives gesture detection updates via HTTP and displays them in a styled overlay.
"""

from flask import Flask, render_template_string, jsonify, request
import threading
import time
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global state to store the latest detection
current_detection: Dict[str, Any] = {
    'text': '',
    'confidence': 0.0,
    'status': 'waiting',
    'last_updated': 0,
    'detection': {
        'gesture': '',
        'confidence': 0.0,
        'time_held': 0.0
    }
}

# HTML template for the overlay
OVERLAY_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>ASL Translator Overlay</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: 'Arial', sans-serif;
            color: white;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8);
            background: transparent;
            overflow: hidden;
        }
        .container {
            padding: 15px;
            text-align: center;
        }
        .gesture {
            font-size: 64px;
            font-weight: bold;
            margin: 10px 0;
            text-transform: uppercase;
            animation: fadeIn 0.5s;
        }
        .confidence {
            font-size: 24px;
            color: #4CAF50;
            margin-bottom: 10px;
        }
        .status {
            font-size: 18px;
            color: #2196F3;
            margin-top: 10px;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
    <script>
        let currentGesture = '';
        
        function updateOverlay(data) {
            if (data && data.detection) {
                document.getElementById('gesture').textContent = data.detection.gesture || '';
                document.getElementById('confidence').textContent = 
                    data.detection.confidence ? `${Math.round(data.detection.confidence * 100)}%` : '';
                document.getElementById('status').textContent = 
                    data.detection.gesture ? `Detected: ${data.detection.gesture}` : 'Waiting for gesture...';
                
                // Add animation class
                const gestureEl = document.getElementById('gesture');
                gestureEl.classList.remove('animate');
                void gestureEl.offsetWidth; // Trigger reflow
                gestureEl.classList.add('animate');
            }
        }
        
        // Check for updates every 100ms
        setInterval(() => {
            fetch('/api/current')
                .then(response => response.json())
                .then(updateOverlay)
                .catch(console.error);
        }, 100);
    </script>
</head>
<body>
    <div class="container">
        <div id="gesture" class="gesture"></div>
        <div id="confidence" class="confidence"></div>
        <div id="status" class="status">Waiting for gesture...</div>
    </div>
</body>
</html>
"""

@app.route('/')
def overlay():
    """Render the overlay HTML."""
    return render_template_string(OVERLAY_TEMPLATE)

@app.route('/api/update', methods=['POST'])
def update_detection():
    """Update the current detection data."""
    global current_detection
    
    try:
        data = request.get_json()
        if data:
            current_detection.update({
                'text': data.get('text', ''),
                'confidence': float(data.get('confidence', 0.0)),
                'status': data.get('status', 'waiting'),
                'last_updated': time.time(),
                'detection': {
                    'gesture': data.get('text', ''),
                    'confidence': float(data.get('confidence', 0.0)),
                    'time_held': float(data.get('detection', {}).get('time_held', 0.0))
                }
            })
            return jsonify({'status': 'success'})
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400
    except Exception as e:
        logger.error(f"Error updating detection: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/current')
def get_current_detection():
    """Get the current detection data."""
    return jsonify(current_detection)

def start_server(host: str = '0.0.0.0', port: int = 8000, debug: bool = False):
    """Start the overlay server."""
    logger.info(f"Starting overlay server at http://{host}:{port}")
    app.run(host=host, port=port, debug=debug, use_reloader=False, threaded=True)

if __name__ == "__main__":
    start_server()
