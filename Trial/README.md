# ASL Translation Pipeline

A real-time American Sign Language (ASL) translation system that captures hand gestures via webcam, processes them using MediaPipe, converts them to text and speech, and displays the results through OBS overlays.

## ✨ Features

- **Real-time Hand Tracking**: Uses MediaPipe for accurate hand landmark detection
- **Gesture Recognition**: Converts hand gestures to text
- **Text-to-Speech**: Speaks out the translated text
- **OBS Integration**: Displays translations as an overlay in OBS
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Customizable**: Easy to configure via YAML config file

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Webcam
- [OBS Studio](https://obsproject.com/) (for overlay display)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/asl-translator.git
   cd asl-translator
   ```

2. **Run the setup script**
   ```bash
   # Linux/macOS
   chmod +x scripts/*.sh
   ./scripts/install.sh
   
   # Windows
   .\scripts\install.bat
   ```

3. **Activate the virtual environment**
   ```bash
   # Linux/macOS
   source venv/bin/activate
   
   # Windows
   .\venv\Scripts\activate
   ```

## 🎮 Usage

### Running the Application

```bash
# Start the ASL Translator
./scripts/run.sh

# Or run directly
python src/main.py
```

### OBS Setup

1. In OBS, add a new **Browser Source**
2. Check "Local file" and browse to `obs_overlay/overlay.html`
3. Set width to 1920 and height to 1080 (or your canvas size)
4. Check "Shutdown source when not visible" and "Refresh browser when scene becomes active"

### Keyboard Controls

- `Q` or `ESC`: Exit the application
- `Space`: Toggle OBS overlay visibility
- `P`: Pause/Resume translation
- `S`: Save current frame
- `C`: Clear translation history

## 🛠 Configuration

Edit `config/config.yaml` to customize the application behavior. Key settings include:

```yaml
# Camera settings
camera:
  device_id: 0
  width: 1280
  height: 720
  fps: 30

# Gesture recognition
gesture_recognizer:
  min_confidence: 0.7
  max_num_hands: 2

# Text-to-Speech
tts:
  enabled: true
  engine: "pyttsx3"  # or "gtts"
  rate: 150

# OBS integration
obs:
  enabled: true
  overlay_position: "bottom"
```

## 📁 Project Structure

```
asl-translator/
├── config/               # Configuration files
├── docs/                 # Documentation
├── logs/                 # Log files
├── models/               # Trained models
├── obs_overlay/          # OBS overlay files
├── output/               # Output files
├── scripts/              # Utility scripts
├── src/                  # Source code
│   ├── main.py           # Main application
│   ├── gesture_recognizer.py
│   ├── text_processor.py
│   ├── tts_engine.py
│   └── obs_integration.py
├── tests/                # Unit tests
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [MediaPipe](https://mediapipe.dev/) for hand tracking
- [OpenCV](https://opencv.org/) for computer vision
- [OBS Studio](https://obsproject.com/) for overlay display
- [gTTS](https://gtts.readthedocs.io/) for Google Text-to-Speech
- [pyttsx3](https://pyttsx3.readthedocs.io/) for offline text-to-speech

---

<div align="center">
  Made with ❤️ by Your Name
</div>
