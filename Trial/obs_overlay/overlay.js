/**
 * ASL Translator - OBS Overlay
 * Handles real-time updates and animations for the translation overlay
 */

class ASLOverlay {
    constructor() {
        // DOM Elements
        this.translationElement = document.getElementById('translation-text');
        this.confidenceMeter = document.getElementById('confidence-meter');
        this.overlayContainer = document.getElementById('overlay-container');
        
        // State management
        this.lastUpdateTime = 0;
        this.updateInterval = 16; // ~60fps for smooth animations
        this.autoHideTimer = null;
        this.autoHideTimeout = 5000; // 5 seconds
        this.isVisible = true;
        this.currentText = '';
        this.currentConfidence = 0;
        
        // API polling
        this.lastApiCheck = 0;
        this.apiCheckInterval = 250; // ms between API checks (4x per second)
        this.serverUrl = window.location.origin;
        this.consecutiveErrors = 0;
        this.maxConsecutiveErrors = 3;
        
        // Gesture tracking
        this.lastGestureTime = 0;
        this.gestureCooldown = 300; // ms to debounce gesture updates
        
        // Initialize the overlay
        this.initialize();
    }

    initialize() {
        this.setupEventListeners();
        this.showOverlay();
        this.updateOverlay('ASL Translator Ready', 0);
        this.lastUpdateTime = performance.now();
        this.lastApiCheck = this.lastUpdateTime;
        this.checkForUpdates();
        this.updateLoop();
        console.log('ASL Translator Overlay initialized');
    }

    setupEventListeners() {
        window.addEventListener('message', (event) => {
            try {
                const data = typeof event.data === 'string' ? JSON.parse(event.data) : event.data;
                this.handleMessage(data);
            } catch (e) {
                console.error('Error parsing message:', e);
            }
        });
        this.handleUrlParameters();
    }

    handleUrlParameters() {
        const params = new URLSearchParams(window.location.search);
        const position = params.get('position') || 'bottom';
        this.setPosition(position);

        const hideTimeout = params.get('hideTimeout');
        if (hideTimeout) {
            this.autoHideTimeout = parseInt(hideTimeout, 10) || 5000;
        }

        if (params.get('debug') === 'true') {
            document.body.classList.add('debug');
        }
    }

    handleMessage(data) {
        if (data.type === 'update' || data.text !== undefined) {
            const text = data.text || data.message || '';
            const confidence = parseFloat(data.confidence) || 1.0;
            this.updateOverlay(text, confidence);
            if (data.autoHide) this.scheduleAutoHide();
        } else if (data.type === 'show') {
            this.showOverlay();
        } else if (data.type === 'hide') {
            this.hideOverlay();
        } else if (data.type === 'position') {
            this.setPosition(data.position);
        } else if (data.type === 'style') {
            this.updateStyle(data.style);
        }
    }

    updateOverlay(text, confidence = 0.0) {
        const wasNoGesture = this.currentText === 'No gesture detected' || !this.currentText;
        const isNoGesture = text === 'No gesture detected' || !text || confidence < 0.5;

        const confidenceChanged = Math.abs(confidence - this.currentConfidence) > 0.1;
        const textChanged = text !== this.currentText;

        if (textChanged || confidenceChanged || wasNoGesture !== isNoGesture) {
            this.currentText = text;
            this.currentConfidence = confidence;
            this.lastGestureTime = performance.now();

            const displayText = isNoGesture ? 'No gesture detected' : text;
            const shouldShowConfidence = !isNoGesture && confidence > 0;

            if (displayText !== this.translationElement.textContent) {
                this.translationElement.textContent = displayText;

                if (shouldShowConfidence) {
                    const confidencePercent = Math.round(confidence * 100);
                    this.confidenceMeter.textContent = `${confidencePercent}%`;
                    this.confidenceMeter.style.display = 'block';

                    if (confidence > 0.8) {
                        this.confidenceMeter.style.color = '#4CAF50';
                    } else if (confidence > 0.5) {
                        this.confidenceMeter.style.color = '#FFC107';
                    } else {
                        this.confidenceMeter.style.color = '#F44336';
                    }
                } else {
                    this.confidenceMeter.style.display = 'none';
                }

                if (!isNoGesture) {
                    this.translationElement.classList.remove('new-text');
                    void this.translationElement.offsetWidth;
                    this.translationElement.classList.add('new-text');
                    this.showOverlay();
                }
            }

            const confidencePercent = Math.round(this.currentConfidence * 100);
            this.confidenceMeter.style.width = `${confidencePercent}%`;
            if (this.currentConfidence > 0.7) {
                this.confidenceMeter.style.backgroundColor = '#4CAF50';
            } else if (this.currentConfidence > 0.4) {
                this.confidenceMeter.style.backgroundColor = '#FFC107';
            } else {
                this.confidenceMeter.style.backgroundColor = '#F44336';
            }

            this.translationElement.classList.add('visible');
        }
    }

    showOverlay() {
        if (!this.isVisible) {
            this.overlayContainer.style.opacity = '1';
            this.isVisible = true;
        }
        this.cancelAutoHide();
    }

    hideOverlay() {
        if (this.isVisible) {
            this.overlayContainer.style.opacity = '0';
            this.isVisible = false;
        }
        this.cancelAutoHide();
    }

    scheduleAutoHide() {
        this.cancelAutoHide();
        if (this.autoHideTimeout > 0) {
            this.autoHideTimer = setTimeout(() => {
                this.hideOverlay();
            }, this.autoHideTimeout);
        }
    }

    cancelAutoHide() {
        if (this.autoHideTimer) {
            clearTimeout(this.autoHideTimer);
            this.autoHideTimer = null;
        }
    }

    setPosition(position) {
        const positions = ['top', 'bottom', 'left', 'right'];
        this.overlayContainer.classList.remove(...positions.map(p => `overlay-${p}`));

        if (position && positions.includes(position)) {
            this.overlayContainer.classList.add(`overlay-${position}`);
        } else {
            this.overlayContainer.classList.add('overlay-bottom');
        }
    }

    updateStyle(style) {
        if (style.backgroundColor) {
            this.translationElement.style.backgroundColor = style.backgroundColor;
        }
        if (style.textColor) {
            this.translationElement.style.color = style.textColor;
        }
        if (style.fontSize) {
            this.translationElement.style.fontSize = style.fontSize;
        }
        if (style.opacity !== undefined) {
            this.overlayContainer.style.opacity = style.opacity;
        }
    }

    async checkForUpdates() {
        const now = performance.now();
        if (now - this.lastApiCheck < this.apiCheckInterval) return;
        this.lastApiCheck = now;

        try {
            // Add a cache-busting parameter
            const timestamp = new Date().getTime();
            const response = await fetch(`${this.serverUrl}/api/current?_=${timestamp}`, {
                method: 'GET',
                cache: 'no-store',
                headers: {
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                }
            });

            if (!response.ok) {
                if (response.status === 429) {
                    // Rate limited - back off
                    console.warn('Rate limited - backing off');
                    this.apiCheckInterval = Math.min(2000, this.apiCheckInterval * 2);
                } else {
                    console.error('API error:', response.status, response.statusText);
                    this.consecutiveErrors++;
                    if (this.consecutiveErrors > this.maxConsecutiveErrors) {
                        this.updateOverlay('Connection error', 0);
                    }
                }
                return;
            }

            // Reset error counter on successful response
            this.consecutiveErrors = 0;
            this.apiCheckInterval = 250; // Reset to default interval

            const data = await response.json();
            
            // Extract gesture and confidence from response
            const gesture = data.gesture || (data.detection && data.detection.gesture) || '';
            let confidence = parseFloat(data.confidence || (data.detection && data.detection.confidence) || 0);
            const status = data.status || 'waiting';

            if (isNaN(confidence)) {
                console.warn('Invalid confidence value received:', data.confidence);
                confidence = 0;
            }

            // Only update if we have a valid gesture with sufficient confidence
            if (status === 'active' && confidence > 0.5) {
                this.updateOverlay(gesture, confidence);
                
                // Speak the gesture if it's new and has high confidence
                if (data.detection && data.detection.is_new && confidence > 0.8) {
                    this.speakGesture(gesture);
                }
            } else {
                this.updateOverlay('', 0);
            }
        } catch (error) {
            console.error('Error checking for updates:', error);
            this.consecutiveErrors++;
            if (this.consecutiveErrors > this.maxConsecutiveErrors) {
                this.updateOverlay('Connection lost', 0);
            }
        }
    }

    // Text-to-speech for gestures
    speakGesture(text) {
        if (!text || !window.speechSynthesis) return;
        
        // Cancel any ongoing speech
        window.speechSynthesis.cancel();
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 0.9;
        utterance.pitch = 1.0;
        utterance.volume = 1.0;
        
        // Try to find a good voice
        const voices = window.speechSynthesis.getVoices();
        const preferredVoices = ['Google UK English Female', 'Microsoft Zira Desktop', 'Alex'];
        
        for (const voiceName of preferredVoices) {
            const voice = voices.find(v => v.name === voiceName);
            if (voice) {
                utterance.voice = voice;
                break;
            }
        }
        
        window.speechSynthesis.speak(utterance);
    }

    updateLoop() {
        const now = performance.now();
        
        // Check for updates if enough time has passed
        if (now - this.lastApiCheck >= this.apiCheckInterval) {
            this.checkForUpdates();
        }
        
        // Continue the loop
        requestAnimationFrame(() => this.updateLoop());
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.aslOverlay = new ASLOverlay();
    window.aslOverlay.updateLoop();
});
