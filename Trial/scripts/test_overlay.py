#!/usr/bin/env python3
"""
ASL Translator - OBS Overlay Tester

This script provides a simple web server to test the OBS overlay locally.
It serves the overlay files and provides an API to update the overlay text.
"""

import os
import sys
import json
import time
import random
import threading
import webbrowser
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OBS_OVERLAY_DIR = os.path.join(PROJECT_ROOT, 'obs_overlay')


class OverlayRequestHandler(SimpleHTTPRequestHandler):
    """Custom request handler to serve files and handle API requests."""

    def __init__(self, *args, **kwargs):
        self.directory = OBS_OVERLAY_DIR
        super().__init__(*args, directory=self.directory, **kwargs)

    def do_GET(self):
        """Handle GET requests."""
        parsed_url = urlparse(self.path)
        path = parsed_url.path.lstrip('/')

        if path == '' or path == 'index.html':
            self.path = 'overlay.html'

        if path == 'api/update':
            self.handle_api_update(parsed_url.query)
            return

        return SimpleHTTPRequestHandler.do_GET(self)

    def do_POST(self):
        if self.path != '/api/update':
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)

        try:
            data = json.loads(post_data.decode('utf-8'))
            text = data.get('text', '')
            confidence = float(data.get('confidence', 0.0))

            print(f"[POST] Updating overlay: '{text}' (confidence: {confidence:.2f})")

            response = {
                'status': 'success',
                'message': 'Overlay updated successfully via POST',
                'data': {
                    'text': text,
                    'confidence': confidence,
                    'timestamp': time.time()
                }
            }

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))

        except Exception as e:
            self.send_response(400)
            self.end_headers()
            error_msg = {
                'status': 'error',
                'message': f'Invalid JSON: {str(e)}'
            }
            self.wfile.write(json.dumps(error_msg).encode('utf-8'))

    def handle_api_update(self, query):
        """Handle API update requests."""
        params = parse_qs(query)
        text = params.get('text', [''])[0]
        confidence = float(params.get('confidence', [0.0])[0])

        print(f"Updating overlay: '{text}' (confidence: {confidence:.2f})")

        response = {
            'status': 'success',
            'message': 'Overlay updated successfully',
            'data': {
                'text': text,
                'confidence': confidence,
                'timestamp': time.time()
            }
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def log_message(self, format, *args):
        """Override to disable logging for cleaner output."""
        return


def start_server(port=8000, open_browser=False):
    """Start the web server."""
    server_address = ('', port)
    httpd = HTTPServer(server_address, OverlayRequestHandler)

    print(f"Serving OBS overlay at http://localhost:{port}")
    print("Press Ctrl+C to stop the server")

    if open_browser:
        webbrowser.open(f'http://localhost:{port}/overlay.html')

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down the server...")
        httpd.server_close()
        sys.exit(0)


def update_overlay(text, confidence=1.0, port=8000):
    """Update the overlay with new text and confidence."""
    import requests
    encoded_text = urllib.parse.quote(text)
    url = f'http://localhost:{port}/api/update?text={encoded_text}&confidence={confidence}'

    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error updating overlay: {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None


def test_overlay_updates(port=8000):
    """Test the overlay by sending periodic updates."""
    test_phrases = [
        {"text": "Hello!", "confidence": 0.95},
        {"text": "How are you today?", "confidence": 0.85},
        {"text": "My name is ASL Translator", "confidence": 0.92},
        {"text": "This is a test of the overlay system", "confidence": 0.78},
        {"text": "Testing different confidence levels", "confidence": 0.65},
        {"text": "Low confidence example", "confidence": 0.35},
        {"text": "Thank you!", "confidence": 0.98}
    ]

    print("Starting overlay update test...")
    print("Sending updates to the overlay every 3 seconds")
    print("Open http://localhost:8000/overlay.html in OBS to see the updates")

    try:
        while True:
            for phrase in test_phrases:
                update_overlay(
                    text=phrase["text"],
                    confidence=phrase["confidence"]
                )
                time.sleep(3)
    except KeyboardInterrupt:
        print("\nStopping overlay test...")
        sys.exit(0)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Test the ASL Translator OBS Overlay')
    parser.add_argument('--port', type=int, default=8000, help='Port to run the server on')
    parser.add_argument('--test', action='store_true', help='Run the overlay update test')
    parser.add_argument('--browser', action='store_true', help='Open in default browser')

    args = parser.parse_args()

    os.chdir(OBS_OVERLAY_DIR)

    if args.test:
        test_thread = threading.Thread(
            target=test_overlay_updates,
            args=(args.port,),
            daemon=True
        )
        test_thread.start()

    start_server(port=args.port, open_browser=args.browser)
