# Inside src/Apoorv_gesture_recognizer.py

import numpy as np
import cv2
from tensorflow.keras.models import load_model

class GestureRecognizer:
    def __init__(self, model_path='E:/AMoney/Hocrux/Trial/Model/sign_model.h5', label_map_path='E:/AMoney/Hocrux/Trial/Model/label_map.npy'):
        # Load model with custom objects if needed
        self.model = load_model(model_path, compile=False)
        
        # Load and process label map
        label_map = np.load(label_map_path, allow_pickle=True).item()
        
        # Create two-way mapping
        self.label_to_idx = label_map  # {'A': 0, 'B': 1, ...}
        self.idx_to_label = {v: k for k, v in label_map.items()}  # {0: 'A', 1: 'B', ...}
        
        print("\nLabel map loaded successfully:")
        print("-" * 30)
        for idx, label in sorted(self.idx_to_label.items()):
            print(f"{idx}: {label}")
    
    def predict(self, frame, debug=False):
        """
        Predict gesture from a frame.
        
        Args:
            frame: Input frame (BGR or RGB)
            debug: If True, returns additional debug information
            
        Returns:
            If debug=False: (predicted_label, confidence)
            If debug=True: tuple of (predicted_label, confidence, debug_info)
        """
        debug_info = {}
        try:
            # Store original frame for debugging
            debug_info['original_shape'] = frame.shape
            
            # Convert to grayscale if needed
            if len(frame.shape) == 3:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                debug_info['converted_to_grayscale'] = True
            else:
                debug_info['converted_to_grayscale'] = False
            
            # Store grayscale frame for debugging
            debug_frame = frame.copy()
            
            # Resize and normalize
            img = cv2.resize(frame, (64, 64))  # Match training resolution
            debug_info['resized_shape'] = img.shape
            
            # Add channel dimension if needed (for grayscale)
            if len(img.shape) == 2:
                img = np.expand_dims(img, axis=-1)
                debug_info['added_channel_dim'] = True
            else:
                debug_info['added_channel_dim'] = False
            
            # Normalize
            img = img.astype('float32') / 255.0
            debug_info['normalized'] = True
            
            # Add batch dimension
            img_batch = np.expand_dims(img, axis=0)
            debug_info['batch_shape'] = img_batch.shape

            # Make prediction
            pred = self.model.predict(img_batch, verbose=0)[0]
            predicted_index = int(np.argmax(pred))
            confidence = float(pred[predicted_index])
            
            # Map index to label
            predicted_label = self.idx_to_label.get(predicted_index, "Unknown")
            
            # Debug: Print top predictions
            top_indices = np.argsort(pred)[::-1][:3]  # Get top 3 predictions
            print("\nTop predictions:")
            for i, idx in enumerate(top_indices):
                label = self.idx_to_label.get(int(idx), "Unknown")
                print(f"  {i+1}. {label} (index {idx}): {pred[idx]:.4f}")
            
            debug_info.update({
                'prediction_shape': pred.shape,
                'top_predictions': sorted([(str(k), float(v)) for k, v in enumerate(pred)], 
                                       key=lambda x: x[1], reverse=True)[:3],
                'final_prediction': (predicted_label, confidence)
            })
            
            if debug:
                return predicted_label, confidence, debug_info
            return predicted_label, confidence
            
        except Exception as e:
            error_msg = f"Error in predict: {str(e)}"
            print(error_msg)
            debug_info['error'] = error_msg
            if debug:
                return "Error", 0.0, debug_info
            return "Error", 0.0