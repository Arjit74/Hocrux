import os
import cv2
import numpy as np
from sklearn.model_selection import train_test_split
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense
from tensorflow.keras.optimizers import Adam

DATASET_DIR = 'dataset'
IMG_SIZE = 64

def load_images_from_folder(folder_path):
    images, labels = [], []
    class_names = sorted(os.listdir(folder_path))
    label_map = {name: idx for idx, name in enumerate(class_names)}

    for label in class_names:
        class_folder = os.path.join(folder_path, label)
        if not os.path.isdir(class_folder):
            continue
        for file in os.listdir(class_folder):
            img_path = os.path.join(class_folder, file)
            try:
                img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
                images.append(img)
                labels.append(label_map[label])
            except:
                print(f"Error reading: {img_path}")

    return np.array(images), np.array(labels), label_map

# Load data
X, y, label_map = load_images_from_folder(DATASET_DIR)

# Normalize & reshape
X = X / 255.0
X = X.reshape(-1, IMG_SIZE, IMG_SIZE, 1)
y_cat = to_categorical(y)

# Split (in case)
X_train, X_val, y_train, y_val = train_test_split(X, y_cat, test_size=0.2)

# Model
model = Sequential([
    Conv2D(32, (3,3), activation='relu', input_shape=(IMG_SIZE, IMG_SIZE, 1)),
    MaxPooling2D(2,2),
    Conv2D(64, (3,3), activation='relu'),
    MaxPooling2D(2,2),
    Flatten(),
    Dense(128, activation='relu'),
    Dense(len(label_map), activation='softmax')
])

model.compile(optimizer=Adam(), loss='categorical_crossentropy', metrics=['accuracy'])
model.fit(X_train, y_train, validation_data=(X_val, y_val), epochs=10)

# Save model & label map
model.save('model/sign_model.h5')
np.save('model/label_map.npy', label_map)
