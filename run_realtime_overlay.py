import cv2
import numpy as np
import time
from tensorflow.keras.models import load_model
from collections import deque
import mediapipe as mp

# Load model and label map
model = load_model('model/sign_model.h5')
label_map = np.load('model/label_map.npy', allow_pickle=True).item()
idx_to_label = {v: k for k, v in label_map.items()}
IMG_SIZE = 64

# Setup MediaPipe for hand detection
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1,
                       min_detection_confidence=0.7, min_tracking_confidence=0.7)

cap = cv2.VideoCapture(0)

# Caption management
current_word = ""
caption_words = []
next_caption_words = []
display_caption = ""
last_display_time = 0
display_interval = 2.5
max_caption_length = 35  # total characters before caption flush

# Prediction buffers
prediction_buffer = []
prev_prediction = ""
frame_threshold = 15
repeat_delay = 2
last_update_time = time.time()

print("\n🟢 Real-time sign detection running...")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    hand_roi = None

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            x_coords = [lm.x for lm in hand_landmarks.landmark]
            y_coords = [lm.y for lm in hand_landmarks.landmark]
            x_min = int(min(x_coords) * w) - 20
            x_max = int(max(x_coords) * w) + 20
            y_min = int(min(y_coords) * h) - 20
            y_max = int(max(y_coords) * h) + 20
            x_min, y_min = max(x_min, 0), max(y_min, 0)
            x_max, y_max = min(x_max, w), min(y_max, h)

            hand_roi = frame[y_min:y_max, x_min:x_max]
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (255, 0, 0), 2)
            break
    else:
        cv2.putText(frame, "Prediction: None (no hand)", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
        if display_caption:
            text_size = cv2.getTextSize(display_caption, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)[0]
            text_x = (frame.shape[1] - text_size[0]) // 2
            text_y = frame.shape[0] - 30
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, text_y - 35), (frame.shape[1], text_y + 10), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
            cv2.putText(frame, display_caption, (text_x, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        cv2.imshow("Real-Time Sign Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        continue

    # Preprocess hand ROI
    gray = cv2.cvtColor(hand_roi, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, (IMG_SIZE, IMG_SIZE))
    gray = gray / 255.0
    gray = gray.reshape(1, IMG_SIZE, IMG_SIZE, 1)

    # Predict
    prediction = model.predict(gray, verbose=0)
    pred_class = idx_to_label[np.argmax(prediction)]

    # Stabilization buffer
    prediction_buffer.append(pred_class)
    if len(prediction_buffer) > frame_threshold:
        prediction_buffer.pop(0)

    if prediction_buffer.count(pred_class) > frame_threshold * 0.8:
        current_time = time.time()
        if pred_class != prev_prediction or (current_time - last_update_time > repeat_delay):
            if pred_class in ["space", "nothing", "del"]:
                if current_word.strip():
                    end_char = {
                        "space": " ",
                        "nothing": ".",
                        "del": ","
                    }.get(pred_class, "")
                    next_caption_words.append(current_word + end_char)
                    current_word = ""
            else:
                current_word += pred_class  # Include letters, digits, etc.

            prev_prediction = pred_class
            last_update_time = current_time

    # Show captions more responsively (even for 1 word)
    time_elapsed = time.time() - last_display_time
    total_len = sum(len(w) for w in next_caption_words)
    if (total_len >= max_caption_length or len(next_caption_words) >= 1 or time_elapsed >= display_interval) and next_caption_words:
        caption_words = next_caption_words.copy()
        display_caption = "".join(caption_words).strip()
        next_caption_words.clear()
        last_display_time = time.time()

    # Clear old caption after interval
    if time.time() - last_display_time >= display_interval:
        display_caption = ""

    # Draw caption
    if display_caption:
        text_size = cv2.getTextSize(display_caption, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)[0]
        text_x = (frame.shape[1] - text_size[0]) // 2
        text_y = frame.shape[0] - 30
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, text_y - 35), (frame.shape[1], text_y + 10), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)
        cv2.putText(frame, display_caption, (text_x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

    # Show live prediction
    cv2.putText(frame, f"Prediction: {pred_class}", (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    cv2.imshow("Real-Time Sign Detection", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
