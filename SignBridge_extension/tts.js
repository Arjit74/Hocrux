class TTSController {
    constructor() {
        this.synth = window.speechSynthesis;
        this.isEnabled = true;
        this.currentVoice = null;
        this.settings = {
            rate: 1.0,
            pitch: 1.0,
            volume: 0.8,
            language: 'en-US'
        };
        
        this.queue = [];
        this.isSpeaking = false;
        this.lastSpokenText = '';
        this.speakingTimeout = null;
        
        this.initializeOnUserInteraction();
    }

    initializeOnUserInteraction() {
        const userInteractionEvents = ['click', 'touchstart', 'keydown'];
        const initializeAudio = () => {
            // Initialize audio context here
            this.synth = window.speechSynthesis;
            this.initializeVoices();
            
            // Remove event listeners after initialization
            userInteractionEvents.forEach(event => {
                document.removeEventListener(event, initializeAudio);
            });
        };

        // Add event listeners for user interaction
        userInteractionEvents.forEach(event => {
            document.addEventListener(event, initializeAudio, { once: true });
        });
    }

    initializeVoices() {
        // Wait for voices to load
        if (this.synth.getVoices().length === 0) {
            this.synth.addEventListener('voiceschanged', () => {
                this.selectBestVoice();
            });
        } else {
            this.selectBestVoice();
        }
    }

    selectBestVoice() {
        const voices = this.synth.getVoices();
        
        // Prefer high-quality voices
        const preferredVoices = [
            'Google US English',
            'Microsoft Zira',
            'Alex',
            'Samantha',
            'Daniel'
        ];
        
        for (const preferredName of preferredVoices) {
            const voice = voices.find(v => 
                v.name.includes(preferredName) && 
                v.lang.startsWith('en')
            );
            if (voice) {
                this.currentVoice = voice;
                console.log('SignBridge TTS: Selected voice:', voice.name);
                return;
            }
        }
        
        // Fallback to first English voice
        const englishVoice = voices.find(v => v.lang.startsWith('en'));
        if (englishVoice) {
            this.currentVoice = englishVoice;
            console.log('SignBridge TTS: Using fallback voice:', englishVoice.name);
        }
    }

    speak(text, options = {}) {
        if (!this.isEnabled || !text || text === this.lastSpokenText) {
            return;
        }
        
        // Clean and validate text
        const cleanText = this.cleanText(text);
        if (!cleanText || cleanText.length < 2) {
            return;
        }
        
        this.lastSpokenText = text;
        
        // Cancel current speech if needed
        if (this.isSpeaking && options.interrupt !== false) {
            this.stop();
        }
        
        // Create utterance
        const utterance = new SpeechSynthesisUtterance(cleanText);
        
        // Apply settings
        utterance.voice = this.currentVoice;
        utterance.rate = options.rate || this.settings.rate;
        utterance.pitch = options.pitch || this.settings.pitch;
        utterance.volume = options.volume || this.settings.volume;
        utterance.lang = options.language || this.settings.language;
        
        // Set up event handlers
        utterance.onstart = () => {
            this.isSpeaking = true;
            console.log('SignBridge TTS: Started speaking:', cleanText);
        };
        
        utterance.onend = () => {
            this.isSpeaking = false;
            this.processQueue();
        };
        
        utterance.onerror = (event) => {
            console.error('SignBridge TTS: Speech error:', event.error);
            this.isSpeaking = false;
            this.processQueue();
        };
        
        // Add visual feedback
        this.showSpeechIndicator(cleanText);
        
        // Speak or queue
        if (this.isSpeaking && options.queue !== false) {
            this.queue.push(utterance);
        } else {
            this.synth.speak(utterance);
        }
        
        // Set timeout to prevent stuck speech
        this.setSpeechTimeout(cleanText.length);
        
        // Listen for popup voice settings
        chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
            if (message.action === 'speak') {
                this.speak(message.text);
                sendResponse({ success: true });
            } else if (message.action === 'setVoiceSettings') {
                this.updateSettings(message.settings);
                sendResponse({ success: true });
            }
        });
    }

    updateSettings(settings) {
        if (settings.voice) this.setVoice(settings.voice);
        if (settings.rate) this.setRate(settings.rate);
        if (settings.pitch) this.setPitch(settings.pitch);
        if (settings.volume) this.setVolume(settings.volume);
    }

    cleanText(text) {
        return text
            .replace(/[^\w\s.,!?-]/g, '') // Remove special characters
            .replace(/\s+/g, ' ') // Normalize whitespace
            .trim()
            .substring(0, 200); // Limit length
    }

    setSpeechTimeout(textLength) {
        const estimatedDuration = (textLength * 100) + 2000; // ~100ms per character + buffer
        
        if (this.speakingTimeout) {
            clearTimeout(this.speakingTimeout);
        }
        
        this.speakingTimeout = setTimeout(() => {
            if (this.isSpeaking) {
                console.warn('SignBridge TTS: Speech timeout, stopping...');
                this.stop();
            }
        }, estimatedDuration);
    }

    showSpeechIndicator(text) {
        // Create temporary visual indicator
        const indicator = document.createElement('div');
        indicator.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 20px;
            background: linear-gradient(135deg, #3b82f6, #1d4ed8);
            color: white;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 500;
            z-index: 999998;
            opacity: 0;
            transform: translateY(20px);
            transition: all 0.3s ease;
            pointer-events: none;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        `;
        
        indicator.innerHTML = `
            <div style="display: flex; align-items: center; gap: 6px;">
                <span style="animation: pulse 1s infinite;">🔊</span>
                <span>Speaking...</span>
            </div>
        `;
        
        document.body.appendChild(indicator);
        
        // Animate in
        setTimeout(() => {
            indicator.style.opacity = '1';
            indicator.style.transform = 'translateY(0)';
        }, 10);
        
        // Remove after speech
        const removeIndicator = () => {
            indicator.style.opacity = '0';
            indicator.style.transform = 'translateY(20px)';
            
            setTimeout(() => {
                if (indicator.parentNode) {
                    indicator.parentNode.removeChild(indicator);
                }
            }, 300);
        };
        
        // Remove when speech ends or after timeout
        const checkSpeechEnd = () => {
            if (!this.isSpeaking) {
                removeIndicator();
            } else {
                setTimeout(checkSpeechEnd, 100);
            }
        };
        
        setTimeout(checkSpeechEnd, 100);
        setTimeout(removeIndicator, 5000); // Fallback timeout
    }

    processQueue() {
        if (this.queue.length > 0 && !this.isSpeaking) {
            const nextUtterance = this.queue.shift();
            this.synth.speak(nextUtterance);
        }
    }

    stop() {
        this.synth.cancel();
        this.isSpeaking = false;
        this.queue = [];
        
        if (this.speakingTimeout) {
            clearTimeout(this.speakingTimeout);
            this.speakingTimeout = null;
        }
    }

    setEnabled(enabled) {
        this.isEnabled = enabled;
        
        if (!enabled) {
            this.stop();
        }
    }

    setVoice(voiceName) {
        const voices = this.synth.getVoices();
        const voice = voices.find(v => v.name === voiceName);
        
        if (voice) {
            this.currentVoice = voice;
            console.log('SignBridge TTS: Voice changed to:', voice.name);
        }
    }

    setRate(rate) {
        this.settings.rate = Math.max(0.1, Math.min(2.0, rate));
    }

    setPitch(pitch) {
        this.settings.pitch = Math.max(0.0, Math.min(2.0, pitch));
    }

    setVolume(volume) {
        this.settings.volume = Math.max(0.0, Math.min(1.0, volume));
    }

    getAvailableVoices() {
        return this.synth.getVoices().filter(voice => voice.lang.startsWith('en'));
    }

    isSupported() {
        return 'speechSynthesis' in window;
    }

    getStatus() {
        return {
            isEnabled: this.isEnabled,
            isSpeaking: this.isSpeaking,
            queueLength: this.queue.length,
            currentVoice: this.currentVoice?.name || 'None',
            isSupported: this.isSupported()
        };
    }
}

// Export for use in content script
window.TTSController = TTSController;