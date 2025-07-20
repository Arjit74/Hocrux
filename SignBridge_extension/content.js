class SignBridgeController {
    constructor() {
        this.isActive = false;
        this.settings = {
            ttsEnabled: true,
            autoSpeak: true,
            overlayEnabled: true
        };
        this.init();
    }

    async loadScripts() {
        const scriptUrls = [
            chrome.runtime.getURL('model/mediapipe_hands.js'),  // Use local file
            chrome.runtime.getURL('model/eventemitter.js'),
            chrome.runtime.getURL('model/gesture.js'),
            chrome.runtime.getURL('overlay.js'),
            chrome.runtime.getURL('tts.js')
        ];

        const loadScript = (src) => new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.onload = resolve;
            script.onerror = () => {
                console.error(`Failed to load: ${src}`);
                reject(new Error(`Script load failed: ${src}`));
            };
            document.head.appendChild(script);
        });

        // Load MediaPipe first with a longer delay to ensure initialization
        await loadScript(scriptUrls[0]);
        await new Promise(res => setTimeout(res, 1000));

        // Load remaining scripts with shorter delays
        for (let i = 1; i < scriptUrls.length; i++) {
            await loadScript(scriptUrls[i]);
            await new Promise(res => setTimeout(res, 100));
        }

        // Wait until GestureRecognizer is definitely ready
        let attempts = 0;
        while (typeof window.GestureRecognizer === 'undefined' && attempts < 10) {
            await new Promise(resolve => setTimeout(resolve, 500));
            attempts++;
        }

        if (typeof window.GestureRecognizer === 'undefined') {
            throw new Error('GestureRecognizer failed to load after multiple attempts');
        }
    }

    async init() {
        console.log('SignBridge: Initializing...');
        
        try {
            // Load required scripts
            await this.loadScripts();
            
            // Verify GestureRecognizer is available
            let attempts = 0;
            const maxAttempts = 10;
            
            while (typeof window.GestureRecognizer === 'undefined' && attempts < maxAttempts) {
                await new Promise(resolve => setTimeout(resolve, 500));
                attempts++;
            }
            
            if (typeof window.GestureRecognizer === 'undefined') {
                throw new Error('GestureRecognizer failed to load after multiple attempts');
            }
            
            // Initialize components
            this.gestureRecognizer = new window.GestureRecognizer();
            await this.gestureRecognizer.initHands();
            this.overlay = new TextOverlay();
            this.tts = new TTSController();
            
            // Load saved state
            await this.loadSettings();
            
            console.log('SignBridge: Ready');
        } catch (error) {
            console.error('SignBridge: Initialization error:', error);
            this.sendError(`Failed to initialize: ${error.message}`);
        }
    }

    async loadSettings() {
        try {
            const result = await chrome.storage.local.get([
                'isActive', 'ttsEnabled', 'autoSpeak', 'overlayEnabled'
            ]);

            this.settings = {
                ttsEnabled: result.ttsEnabled !== false,
                autoSpeak: result.autoSpeak !== false,
                overlayEnabled: result.overlayEnabled !== false
            };

            if (result.isActive) {
                this.startDetection();
            }
        } catch (error) {
            console.error('SignBridge: Error loading settings:', error);
        }
    }

    handleMessage(message, sendResponse) {
        switch (message.action) {
            case 'startDetection':
                this.settings = { ...this.settings, ...message.settings };
                this.startDetection();
                sendResponse({ success: true });
                break;

            case 'stopDetection':
                this.stopDetection();
                sendResponse({ success: true });
                break;

            case 'updateSettings':
                this.settings = { ...this.settings, ...message.settings };
                this.applySettings();
                sendResponse({ success: true });
                break;

            case 'speak':
                if (this.tts) {
                    this.tts.speak(message.text);
                }
                sendResponse({ success: true });
                break;

            case 'getHistory':
                this.sendHistoryUpdate();
                sendResponse({ success: true });
                break;

            default:
                sendResponse({ success: false, error: 'Unknown action' });
        }
    }

    async startDetection() {
        if (this.isActive) return;

        try {
            console.log('SignBridge: Starting detection...');

            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('Your browser does not support video capture');
            }

            if (!window.isSecureContext) {
                throw new Error('Camera access requires a secure context (HTTPS)');
            }

            this.videoStream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640, min: 320 },
                    height: { ideal: 480, min: 240 },
                    frameRate: { ideal: 30, min: 15 },
                    facingMode: 'user'
                }
            }).catch(async (err) => {
                if (err.name === 'OverconstrainedError') {
                    return await navigator.mediaDevices.getUserMedia({ video: true });
                }
                throw err;
            });

            if (!this.videoStream || !this.videoStream.active) {
                throw new Error('Failed to initialize video stream');
            }

            await this.createVideoCanvas();

            await new Promise((resolve) => {
                this.video.onloadedmetadata = resolve;
            });

            await this.gestureRecognizer.initialize();

            this.isActive = true;
            this.processVideoFrame();

            if (this.settings.overlayEnabled) {
                this.overlay.show();
            }

            this.sendStatusUpdate('active');
            console.log('SignBridge: Detection started');
        } catch (error) {
            console.error('SignBridge: Error starting detection:', error);
            this.sendError(`Failed to start detection: ${error.message}`);
            this.cleanup();
        }
    }

    cleanup() {
        if (this.videoStream) {
            this.videoStream.getTracks().forEach(track => track.stop());
            this.videoStream = null;
        }

        if (this.video) {
            this.video.remove();
            this.video = null;
        }

        if (this.canvas) {
            this.canvas.remove();
            this.canvas = null;
            this.context = null;
        }

        this.isActive = false;
        this.overlay?.hide();
    }

    stopDetection() {
        if (!this.isActive) return;

        console.log('SignBridge: Stopping detection...');

        this.isActive = false;

        if (this.videoStream) {
            this.videoStream.getTracks().forEach(track => track.stop());
            this.videoStream = null;
        }

        if (this.canvas) {
            this.canvas.remove();
            this.canvas = null;
            this.context = null;
        }

        this.overlay.hide();

        this.sendStatusUpdate('inactive');
        console.log('SignBridge: Detection stopped');
    }

    async createVideoCanvas() {
        this.video = document.createElement('video');
        this.video.srcObject = this.videoStream;
        this.video.autoplay = true;
        this.video.muted = true;
        this.video.style.display = 'none';
        document.body.appendChild(this.video);

        this.canvas = document.createElement('canvas');
        this.canvas.width = 640;
        this.canvas.height = 480;
        this.canvas.style.display = 'none';
        this.context = this.canvas.getContext('2d');
        document.body.appendChild(this.canvas);
    }

    async processVideoFrame() {
        if (!this.isActive || !this.video || !this.canvas || !this.context) return;

        this.context.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
        const imageData = this.context.getImageData(0, 0, this.canvas.width, this.canvas.height);

        if (this.gestureRecognizer && this.gestureRecognizer.isInitialized) {
            const gesture = await this.gestureRecognizer.processWithMediaPipe(imageData);
            if (gesture) {
                this.handleDetectedGesture(gesture);
            }
        }

        requestAnimationFrame(() => this.processVideoFrame());
    }

    handleDetectedGesture(result) {
        const translatedText = result.translation;

        if (translatedText === this.lastTranslation) return;

        this.lastTranslation = translatedText;

        console.log('SignBridge: Detected gesture:', translatedText);

        if (this.settings.overlayEnabled) {
            this.overlay.updateText(translatedText);
        }

        if (this.settings.autoSpeak && this.settings.ttsEnabled) {
            this.tts.speak(translatedText);
        }

        this.sendTranslationUpdate(translatedText);
        this.saveToHistory(translatedText);
    }

    async saveToHistory(text) {
        try {
            const result = await chrome.storage.local.get(['translationHistory']);
            const history = result.translationHistory || [];

            const newEntry = {
                text: text,
                timestamp: new Date().toISOString(),
                id: Date.now()
            };

            history.unshift(newEntry);
            if (history.length > 50) {
                history.splice(50);
            }

            await chrome.storage.local.set({ translationHistory: history });
        } catch (error) {
            console.error('SignBridge: Error saving to history:', error);
        }
    }

    applySettings() {
        if (this.overlay) {
            if (this.settings.overlayEnabled && this.isActive) {
                this.overlay.show();
            } else {
                this.overlay.hide();
            }
        }

        if (this.tts) {
            this.tts.setEnabled(this.settings.ttsEnabled);
        }
    }

    // Update all sendMessage calls with proper error handling
    sendStatusUpdate(status) {
        try {
            chrome.runtime.sendMessage({
                action: 'statusUpdate',
                status: status
            }).catch(() => {});
        } catch (error) {
            console.log('Extension context invalidated');
        }
    }

    sendTranslationUpdate(text) {
        try {
            chrome.runtime.sendMessage({
                action: 'translationUpdate',
                text: text
            }).catch(() => {});
        } catch (error) {
            console.log('Extension context invalidated');
        }
    }

    sendError(message) {
        try {
            chrome.runtime.sendMessage({
                action: 'error',
                message: message
            }).catch(() => {});
        } catch (error) {
            console.log('Extension context invalidated');
        }
    }

    sendHistoryUpdate() {
        try {
            chrome.storage.local.get(['translationHistory']).then(result => {
                chrome.runtime.sendMessage({
                    action: 'historyUpdate',
                    history: result.translationHistory || []
                }).catch(() => {});
            });
        } catch (error) {
            console.log('Extension context invalidated');
        }
    }
}

// Initialize when page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.signBridge = new SignBridgeController();
    });
} else {
    window.signBridge = new SignBridgeController();
}
