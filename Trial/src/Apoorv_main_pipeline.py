# Inside src/Apoorv_main_pipeline.py

from src.Apoorv_gesture_recognizer import GestureRecognizer
from pathlib import Path
class ASLProcessor:
    def __init__(self):
        self.recognizer = GestureRecognizer()

    def process_frame(self, frame):
        label, confidence = self.recognizer.predict(frame)
        print(f"Predicted: {label} ({confidence:.2f})")
        return label,confidence
