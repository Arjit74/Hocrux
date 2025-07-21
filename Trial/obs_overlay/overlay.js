/**
 * ASL Translator - OBS Overlay
 * Handles real-time updates and animations for the translation overlay
 */

class ASLOverlay {
    constructor() {
        this.translationElement = document.getElementById('translation-text');
        this.confidenceMeter = document.getElementById('confidence-meter');
        this.overlayContainer = document.getElementById('overlay-container');
        this.lastUpdateTime = 0;
        this.updateInterval = 100; // ms between updates
        this.autoHideTimer = null;
        this.autoHideTimeout = 5000; // 5 seconds
        this.isVisible = true;
        this.currentText = '';
        this.currentConfidence = 0;
        this.lastApiCheck = 0;
        this.apiCheckInterval = 100; // ms between API checks
        
        this.initialize();
    }

    initialize() {
        // Set up event listeners
        this.setupEventListeners();
        
        // Initial state
        this.showOverlay();
        this.updateOverlay('ASL Translator Ready', 0);
        
        // Start update loop
        this.lastUpdateTime = performance.now();
        this.lastApiCheck = this.lastUpdateTime;
        this.updateLoop();
        
        console.log('ASL Translator Overlay initialized');
    }

    setupEventListeners() {
        // Listen for messages from the parent window (if embedded)
        window.addEventListener('message', (event) => {
            try {
                const data = typeof event.data === 'string' ? JSON.parse(event.data) : event.data;
                this.handleMessage(data);
            } catch (e) {
                console.error('Error parsing message:', e);
            }
        });

        // Handle URL parameters for initial configuration
        this.handleUrlParameters();
    }

    handleUrlParameters() {
        const params = new URLSearchParams(window.location.search);
        
        // Set position from URL parameter
        const position = params.get('position') || 'bottom';
        this.setPosition(position);
        
        // Set auto-hide timeout if specified
        const hideTimeout = params.get('hideTimeout');
        if (hideTimeout) {
            this.autoHideTimeout = parseInt(hideTimeout, 10) || 5000;
        }
        
        // Set debug mode
        if (params.get('debug') === 'true') {
            document.body.classList.add('debug');
        }
    }

    handleMessage(data) {
        if (data.type === 'update' || data.text !== undefined) {
            const text = data.text || data.message || '';
            const confidence = parseFloat(data.confidence) || 1.0;
            this.updateOverlay(text, confidence);
            
            // Auto-hide after timeout if enabled
            if (data.autoHide) {
                this.scheduleAutoHide();
            }
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

    updateOverlay(text, confidence = 1.0) {
        if (text !== this.currentText) {
            this.currentText = text;
            this.translationElement.textContent = text;
            this.translationElement.classList.remove('new-text');
            // Force reflow to restart animation
            void this.translationElement.offsetWidth;
            this.translationElement.classList.add('new-text');
            
            // Make sure the overlay is visible when there's new text
            this.showOverlay();
        }
        
        // Update confidence meter
        this.currentConfidence = Math.max(0, Math.min(1, confidence));
        const confidencePercent = Math.round(this.currentConfidence * 100);
        this.confidenceMeter.style.width = `${confidencePercent}%`;
        
        // Update confidence meter color based on confidence level
        if (this.currentConfidence > 0.7) {
            this.confidenceMeter.style.backgroundColor = '#4CAF50'; // Green
        } else if (this.currentConfidence > 0.4) {
            this.confidenceMeter.style.backgroundColor = '#FFC107'; // Yellow
        } else {
            this.confidenceMeter.style.backgroundColor = '#F44336'; // Red
        }
        
        // Show the text if it was hidden
        this.translationElement.classList.add('visible');
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
        // Remove all position classes
        const positions = ['top', 'bottom', 'left', 'right'];
        this.overlayContainer.classList.remove(...positions.map(p => `overlay-${p}`));
        
        // Add the new position class
        if (position && positions.includes(position)) {
            this.overlayContainer.classList.add(`overlay-${position}`);
        } else {
            this.overlayContainer.classList.add('overlay-bottom');
        }
    }

    updateStyle(style) {
        // Apply custom styles from the message
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
        // This can be used for polling if needed
        // For now, we're using the message-based approach
    }

    updateLoop(timestamp) {
        const deltaTime = timestamp - this.lastUpdateTime;
        
        // Check for updates at regular intervals
        if (timestamp - this.lastApiCheck >= this.apiCheckInterval) {
            this.checkForUpdates();
            this.lastApiCheck = timestamp;
        }
        
        this.lastUpdateTime = timestamp;
        requestAnimationFrame((ts) => this.updateLoop(ts));
    }
}

// Initialize the overlay when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    window.aslOverlay = new ASLOverlay();
    
    // For testing without OBS
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        console.log('Running in development mode');
        
        // Example of how to test the overlay directly
        const testPhrases = [
            { text: 'Hello!', confidence: 0.95 },
            { text: 'How are you?', confidence: 0.85 },
            { text: 'This is a test', confidence: 0.75 },
            { text: 'ASL Translator', confidence: 0.9 },
            { text: 'Try it with OBS!', confidence: 0.8 }
        ];
        
        let index = 0;
        setInterval(() => {
            if (window.aslOverlay) {
                window.aslOverlay.updateOverlay(
                    testPhrases[index].text,
                    testPhrases[index].confidence
                );
                index = (index + 1) % testPhrases.length;
            }
        }, 3000);
    }
});
