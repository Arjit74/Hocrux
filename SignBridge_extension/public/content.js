class SignBridgeController {
    constructor() {
        this.isActive = false;
        this.settings = {
            ttsEnabled: true,
            autoSpeak: true,
            overlayEnabled: true
        };
        
        this.gestureRecognizer = null;
        this.videoStream = null;
        this.canvas = null;
        this.context = null;
        this.overlay = null;
        this.tts = null;
        
        this.lastTranslation = '';
        this.translationBuffer = '';
        this.confidenceThreshold = 0.7;
        
        this.init();
    }

    async init() {
        console.log('SignBridge: Initializing...');
        
        // Load required scripts
        await this.loadScripts();
        
        // Initialize components
        this.gestureRecognizer = new GestureRecognizer();
        this.overlay = new TextOverlay();
        this.tts = new TTSController();
        
        // Listen for messages from popup
        chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
            this.handleMessage(message, sendResponse);
        });
        
        // Load saved state
        await this.loadSettings();
        
        console.log('SignBridge: Ready');
    }

    async loadScripts() {
        const scripts = [
            chrome.runtime.getURL('overlay.js'),
            chrome.runtime.getURL('tts.js'),
            chrome.runtime.getURL('model/gesture.js')
        ];

        for (const script of scripts) {
            await this.injectScript(script);
        }
    }

    injectScript(src) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
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
                
            default:
                sendResponse({ success: false, error: 'Unknown action' });
        }
    }

    async startDetection() {
        if (this.isActive) return;
        
        try {
            console.log('SignBridge: Starting detection...');
            
            // Request camera permission
            this.videoStream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    frameRate: { ideal: 30 }
                }
            });

            // Create hidden video element
            this.createVideoCanvas();
            
            // Initialize gesture recognition
            await this.gestureRecognizer.initialize();
            
            // Start processing loop
            this.isActive = true;
            this.processVideoFrame();
            
            // Show overlay if enabled
            if (this.settings.overlayEnabled) {
                this.overlay.show();
            }
            
            this.sendStatusUpdate('active');
            console.log('SignBridge: Detection started');
            
        } catch (error) {
            console.error('SignBridge: Error starting detection:', error);
            this.sendError('Failed to access camera. Please check permissions.');
        }
    }

    stopDetection() {
        if (!this.isActive) return;
        
        console.log('SignBridge: Stopping detection...');
        
        this.isActive = false;
        
        // Stop video stream
        if (this.videoStream) {
            this.videoStream.getTracks().forEach(track => track.stop());
            this.videoStream = null;
        }
        
        // Clean up canvas
        if (this.canvas) {
            this.canvas.remove();
            this.canvas = null;
            this.context = null;
        }
        
        // Hide overlay
        this.overlay.hide();
        
        this.sendStatusUpdate('inactive');
        console.log('SignBridge: Detection stopped');
    }

    createVideoCanvas() {
        // Create hidden video element
        this.video = document.createElement('video');
        this.video.srcObject = this.videoStream;
        this.video.autoplay = true;
        this.video.muted = true;
        this.video.style.display = 'none';
        document.body.appendChild(this.video);

        // Create canvas for processing
        this.canvas = document.createElement('canvas');
        this.canvas.width = 640;
        this.canvas.height = 480;
        this.canvas.style.display = 'none';
        this.context = this.canvas.getContext('2d');
        document.body.appendChild(this.canvas);
    }

    async processVideoFrame() {
        if (!this.isActive || !this.video || !this.gestureRecognizer) return;

        try {
            // Draw video frame to canvas
            this.context.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
            
            // Get image data
            const imageData = this.context.getImageData(0, 0, this.canvas.width, this.canvas.height);
            
            // Process with gesture recognition
            const result = await this.gestureRecognizer.processFrame(imageData);
            
            if (result && result.confidence > this.confidenceThreshold) {
                this.handleDetectedGesture(result);
            }
            
            // Continue processing
            requestAnimationFrame(() => this.processVideoFrame());
            
        } catch (error) {
            console.error('SignBridge: Error processing frame:', error);
            
            // Continue processing even on errors
            setTimeout(() => this.processVideoFrame(), 100);
        }
    }

    handleDetectedGesture(result) {
        const translatedText = result.translation;
        
        // Avoid duplicate translations
        if (translatedText === this.lastTranslation) return;
        
        this.lastTranslation = translatedText;
        
        console.log('SignBridge: Detected gesture:', translatedText);
        
        // Update overlay
        if (this.settings.overlayEnabled) {
            this.overlay.updateText(translatedText);
        }
        
        // Speak if auto-speak is enabled
        if (this.settings.autoSpeak && this.settings.ttsEnabled) {
            this.tts.speak(translatedText);
        }
        
        // Send to popup
        this.sendTranslationUpdate(translatedText);
        
        // Store in history
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
            
            // Keep only last 50 entries
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

    sendStatusUpdate(status) {
        chrome.runtime.sendMessage({
            action: 'statusUpdate',
            status: status
        }).catch(() => {
            // Popup might be closed, ignore error
        });
    }

    sendTranslationUpdate(text) {
        chrome.runtime.sendMessage({
            action: 'translationUpdate',
            text: text
        }).catch(() => {
            // Popup might be closed, ignore error
        });
    }

    sendError(message) {
        chrome.runtime.sendMessage({
            action: 'error',
            message: message
        }).catch(() => {
            // Popup might be closed, ignore error
        });
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
