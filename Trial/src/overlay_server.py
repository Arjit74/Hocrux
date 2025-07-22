"""
OBS Overlay Server for ASL Translator

This server provides a web-based overlay that can be captured by OBS.
It receives gesture detection updates via HTTP and displays them in a styled overlay.
"""

from flask import Flask, render_template_string, jsonify, request, make_response
import threading
import time
import logging
from typing import Dict, Any, Optional
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiting
RATE_LIMIT = 30  # requests per second
RATE_WINDOW = 1.0  # seconds

class RateLimiter:
    def __init__(self):
        self.requests = {}
    
    def check_rate_limit(self, ip):
        current_time = time.time()
        if ip not in self.requests:
            self.requests[ip] = []
        
        # Remove old requests outside the time window
        self.requests[ip] = [t for t in self.requests[ip] if current_time - t < RATE_WINDOW]
        
        if len(self.requests[ip]) >= RATE_LIMIT:
            return False
        
        self.requests[ip].append(current_time)
        return True

limiter = RateLimiter()

def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip = request.remote_addr
        if not limiter.check_rate_limit(ip):
            return jsonify({
                'status': 'error',
                'message': 'Too many requests',
                'retry_after': RATE_WINDOW
            }), 429
        return f(*args, **kwargs)
    return decorated_function

app = Flask(__name__)

# Global state to store the latest detection
current_detection: Dict[str, Any] = {
    'text': 'No gesture detected',
    'confidence': 0.0,
    'status': 'waiting',
    'last_updated': 0,
    'detection': {
        'gesture': '',
        'confidence': 0.0,
        'time_held': 0.0,
        'timestamp': 0,
        'is_new': False
    },
    'last_valid_gesture': None  # Store the last valid gesture
}

# Thread lock for thread-safe updates
detection_lock = threading.Lock()

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
    """
    Update the current detection data.
    Only updates if the new detection is valid (has text and sufficient confidence).
    Maintains the last valid gesture state.
    """
    global current_detection
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
            
        # Get detection data with defaults
        text = str(data.get('text', '')).strip()
        confidence = float(data.get('confidence', 0.0))
        min_confidence = float(data.get('min_confidence', 0.7))
        timestamp = time.time()
        
        # Check if this is a valid gesture update
        is_valid_gesture = bool(text and confidence >= min_confidence)
        
        # Prepare the detection update
        with detection_lock:
            # Only update if we have a valid gesture or we're explicitly clearing the state
            if is_valid_gesture or (not text and confidence == 0):
                # Calculate time held for this gesture
                time_held = float(data.get('detection', {}).get('time_held', 0.0))
                is_new = data.get('detection', {}).get('is_new', False)
                
                # Update the last valid gesture if this is a new valid gesture
                if is_valid_gesture and (is_new or not current_detection['last_valid_gesture']):
                    current_detection['last_valid_gesture'] = {
                        'text': text,
                        'confidence': confidence,
                        'timestamp': timestamp
                    }
                
                # Update the current detection
                current_detection.update({
                    'text': text if is_valid_gesture else 'No gesture detected',
                    'confidence': confidence,
                    'status': 'active' if is_valid_gesture else 'waiting',
                    'last_updated': timestamp,
                    'detection': {
                        'gesture': text if is_valid_gesture else '',
                        'confidence': confidence,
                        'time_held': time_held,
                        'timestamp': timestamp,
                        'is_new': is_new
                    }
                })
                
                logger.debug(f"Updated detection: {text if is_valid_gesture else 'No gesture'} "
                           f"(Confidence: {confidence:.1%})")
            
            return jsonify({
                'status': 'success', 
                'timestamp': timestamp,
                'is_valid': is_valid_gesture
            })
            
    except Exception as e:
        logger.error(f"Error updating detection: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/current', methods=['GET'])
@rate_limit
def get_current_detection():
    """Get the current detection status."""
    global current_detection
    
    try:
        # Get the current timestamp
        current_time = time.time()
        
        # Prepare the response data
        if current_detection and current_detection.get('status') == 'active':
            # If we have a current active detection, use it
            response_data = {
                'status': 'active',
                'gesture': current_detection.get('text', ''),
                'confidence': float(current_detection.get('confidence', 0)),
                'timestamp': current_time,
                'detection': {
                    'gesture': current_detection.get('text', ''),
                    'confidence': float(current_detection.get('confidence', 0)),
                    'is_new': True
                }
            }
        # Otherwise, use the last valid detection if it's recent (within 2 seconds)
        elif current_detection.get('last_valid_gesture') and (current_time - current_detection['last_valid_gesture'].get('timestamp', 0) < 2.0):
            response_data = dict(current_detection['last_valid_gesture'])  # Make a copy
            response_data['detection'] = {
                'gesture': response_data.get('text', ''),
                'confidence': float(response_data.get('confidence', 0)),
                'is_new': False
            }
            response_data['timestamp'] = current_time
        else:
            response_data = {
                'status': 'waiting',
                'gesture': '',
                'confidence': 0.0,
                'timestamp': current_time,
                'detection': {
                    'gesture': '',
                    'confidence': 0.0,
                    'is_new': False
                }
            }
        
        # Create response with cache control headers
        response = make_response(jsonify(response_data))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        response.headers['X-RateLimit-Limit'] = str(RATE_LIMIT)
        response.headers['X-RateLimit-Remaining'] = str(RATE_LIMIT - len(limiter.requests.get(request.remote_addr, [])))
        
        return response
        
    except Exception as e:
        logger.error(f"Error in get_current_detection: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': str(e),
            'gesture': '',
            'confidence': 0.0,
            'timestamp': time.time()
        }), 500

def start_server(host: str = '0.0.0.0', port: int = 8000, debug: bool = False):
    """Start the overlay server."""
    logger.info(f"Starting overlay server at http://{host}:{port}")
    app.run(host=host, port=port, debug=debug, use_reloader=False, threaded=True)

if __name__ == "__main__":
    start_server()
