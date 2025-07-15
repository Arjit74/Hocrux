# 🌿 SignBridge – Making Gestures Accessible

<div align="center">
  <img src="https://raw.githubusercontent.com/Arjit74/Hocrux/main/assets/signbridge-logo.png" alt="SignBridge Logo" width="700"/>
</div>

---

## 📅 Project Overview

To build a cutting-edge Chrome browser extension that translates sign language into text and optionally voice in real-time during video conferencing. Designed for use with platforms like Google Meet, Zoom Web, and Microsoft Teams Web, SignBridge enhances accessibility by enabling seamless communication between sign language users and others.

---

## 🔧 Core Features

| Feature | Description |
|---------|-------------|
| 🤚 Live Gesture Capture | Access user's webcam to capture real-time hand gestures |
| ✋ Gesture Recognition | Use MediaPipe or TensorFlow.js to identify sign language gestures |
| 📝 Real-Time Translation Overlay | Display interpreted text over video call screens |
| 🔊 Text-to-Speech (TTS) | Optionally convert translated text to speech using native browser APIs |
| 🌐 Cross-Platform Support | Integrates with Google Meet, Zoom Web, Microsoft Teams Web |
| 🪩 One-Click Installation | Lightweight Chrome extension with intuitive UI |

---

## 🛏️ Project Architecture

```
chrome-extension/
├── manifest.json
├── content.js
├── overlay/
├── popup.html/.js
├── model/
├── tts.js
├── overlay.js
└── styles.css
```

---

## 🗓️ Timeline

### July 13 - Planning & Kickoff
- Set goals, clarify roles, share references, and finalize architecture

### July 14 - Project Setup
- Arjit: Initialize folder structure, build webcam prototype
- Sree: Setup manifest.json with permissions
- Apoorv: Test MediaPipe Hands functionality
- Ishita: Sketch popup.html wireframe

### July 15 - Gesture Recognition Core
- Apoorv: Integrate MediaPipe with live webcam
- Arjit: Sync MediaPipe outputs with UI overlay

### July 16 - Overlay + Text-to-Speech
- Arjit: Create tts.js, integrate TTS into recognition loop
- Ishita: Design on-screen text overlay components
- Sree: Add styling for overlays

---

## 🎯 Team & Roles

| Name | Role | Primary Tasks |
|------|------|---------------|
| Arjit | Core Developer | Chrome Extension environment, webcam streams, TTS integration |
| Apoorv | ML Engineer | MediaPipe Hands integration, gesture recognition pipeline |
| Ishita | UI/UX Designer | Popup.html UI, branding, presentation design |
| Sree | QA/Documentation | Manifest.json, testing, documentation |

---

## ✨ Bonus Features (Stretch Goals)

- 📝 Transcription log of all signs
- 🌎 Multi-language support for TTS
- 🧢 Whisper Mode (low-volume speech or text-only mode)
- 📊 Analytics for gesture recognition and frequency

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">
  <br/>
  <strong>Built with ❤️ for accessibility and inclusion</strong>
  <br/><br/>
  <img src="https://raw.githubusercontent.com/Arjit74/Hocrux/main/assets/signbridge-icon.png" width="160" alt="SignBridge Logo"/>
</div>
