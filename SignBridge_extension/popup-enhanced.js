class PopupController {
    constructor() {
        this.isActive = false;
        this.isTTSEnabled = true;
        this.isAutoSpeak = true;
        this.isOverlayEnabled = true;
        this.currentVoice = null;
        this.speechRate = 1.0;
        
        this.initializeElements();
        this.attachEventListeners();
        this.loadState();
        this.loadVoices();
        this.updateUI();
    }

    initializeElements() {
        this.statusDot = document.getElementById('statusDot');
        this.statusText = document.getElementById('statusText');
        this.detectedText = document.getElementById('detectedText');
        this.toggleBtn = document.getElementById('toggleBtn');
        this.ttsBtn = document.getElementById('ttsBtn');
        this.clearBtn = document.getElementById('clearBtn');
        this.autoSpeakToggle = document.getElementById('autoSpeakToggle');
        this.overlayToggle = document.getElementById('overlayToggle');
        this.historyList = document.getElementById('historyList');
        this.voiceSelect = document.getElementById('voiceSelect');
        this.rateSlider = document.getElementById('rateSlider');
        this.rateValue = document.getElementById('rateValue');
    }

    attachEventListeners() {
        this.toggleBtn.addEventListener('click', () => this.toggleDetection());
        this.ttsBtn.addEventListener('click', () => this.toggleTTS());
        this.clearBtn.addEventListener('click', () => this.clearHistory());
        this.autoSpeakToggle.addEventListener('click', () => this.toggleAutoSpeak());
        this.overlayToggle.addEventListener('click', () => this.toggleOverlay());

        // Voice controls
        if (this.voiceSelect) {
            this.voiceSelect.addEventListener('change', (e) => this.setVoice(e.target.value));
        }
        
        if (this.rateSlider) {
            this.rateSlider.addEventListener('input', (e) => this.setRate(e.target.value));
        }

        // Listen for messages from content script
        chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
            this.handleMessage(message);
        });
    }

    async loadVoices() {
        if (!this.voiceSelect) return;
        
        // Wait for voices to load
        const loadVoicesPromise = new Promise((resolve) => {
            const voices = speechSynthesis.getVoices();
            if (voices.length) {
                resolve(voices);
            } else {
                speechSynthesis.addEventListener('voiceschanged', () => {
                    resolve(speechSynthesis.getVoices());
                });
            }
        });

        const voices = await loadVoicesPromise;
        const englishVoices = voices.filter(voice => voice.lang.startsWith('en'));
        
        this.voiceSelect.innerHTML = '<option value="">Default Voice</option>';
        
        englishVoices.forEach(voice => {
            const option = document.createElement('option');
            option.value = voice.name;
            option.textContent = `${voice.name} (${voice.lang})`;
            this.voiceSelect.appendChild(option);
        });
    }

    setVoice(voiceName) {
        this.currentVoice = voiceName;
        this.saveState();
        this.sendVoiceUpdate();
    }

    setRate(rate) {
        this.speechRate = parseFloat(rate);
        if (this.rateValue) {
            this.rateValue.textContent = rate + 'x';
        }
        this.saveState();
        this.sendVoiceUpdate();
    }

    async sendVoiceUpdate() {
        try {
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            
            chrome.tabs.sendMessage(tab.id, {
                action: 'setVoiceSettings',
                settings: {
                    voice: this.currentVoice,
                    rate: this.speechRate
                }
            });
        } catch (error) {
            console.error('Error sending voice update:', error);
        }
    }

    async loadState() {
        try {
            const result = await chrome.storage.local.get([
                'isActive', 'isTTSEnabled', 'isAutoSpeak', 'isOverlayEnabled', 
                'translationHistory', 'currentVoice', 'speechRate'
            ]);
            
            this.isActive = result.isActive || false;
            this.isTTSEnabled = result.isTTSEnabled !== false;
            this.isAutoSpeak = result.isAutoSpeak !== false;
            this.isOverlayEnabled = result.isOverlayEnabled !== false;
            this.currentVoice = result.currentVoice || '';
            this.speechRate = result.speechRate || 1.0;
            
            // Update voice controls
            if (this.voiceSelect && this.currentVoice) {
                this.voiceSelect.value = this.currentVoice;
            }
            
            if (this.rateSlider) {
                this.rateSlider.value = this.speechRate;
                this.rateValue.textContent = this.speechRate + 'x';
            }
            
            if (result.translationHistory) {
                this.updateHistoryDisplay(result.translationHistory);
            }
            
            this.loadHistory();
        } catch (error) {
            console.error('Error loading state:', error);
        }
    }

    async saveState() {
        try {
            await chrome.storage.local.set({
                isActive: this.isActive,
                isTTSEnabled: this.isTTSEnabled,
                isAutoSpeak: this.isAutoSpeak,
                isOverlayEnabled: this.isOverlayEnabled,
                currentVoice: this.currentVoice,
                speechRate: this.speechRate
            });
        } catch (error) {
            console.error('Error saving state:', error);
        }
    }

    async loadHistory() {
        try {
            const result = await chrome.storage.local.get(['translationHistory']);
            const history = result.translationHistory || [];
            this.displayHistory(history);
        } catch (error) {
            console.error('Error loading history:', error);
        }
    }

    displayHistory(history) {
        if (!history || history.length === 0) {
            this.historyList.innerHTML = '<div class="history-empty">No translations yet</div>';
            return;
        }
        
        this.historyList.innerHTML = '';
        
        history.slice(0, 10).forEach(entry => {
            const historyItem = document.createElement('div');
            historyItem.className = 'history-item';
            
            const time = new Date(entry.timestamp).toLocaleTimeString();
            historyItem.innerHTML = `
                <div class="history-text">${entry.text}</div>
                <div class="history-time">${time}</div>
                <button class="speak-btn" data-text="${entry.text}">🔊</button>
            `;
            
            // Add speak functionality
            const speakBtn = historyItem.querySelector('.speak-btn');
            speakBtn.addEventListener('click', () => {
                this.speakText(entry.text);
            });
            
            this.historyList.appendChild(historyItem);
        });
    }

    async speakText(text) {
        try {
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            
            chrome.tabs.sendMessage(tab.id, {
                action: 'speak',
                text: text
            });
        } catch (error) {
            console.error('Error speaking text:', error);
        }
    }

    async toggleDetection() {
        this.isActive = !this.isActive;
        
        // Send message to content script
        try {
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            
            chrome.tabs.sendMessage(tab.id, {
                action: this.isActive ? 'startDetection' : 'stopDetection',
                settings: {
                    ttsEnabled: this.isTTSEnabled,
                    autoSpeak: this.isAutoSpeak,
                    overlayEnabled: this.isOverlayEnabled
                }
            });
            
            this.updateUI();
            this.saveState();
        } catch (error) {
            console.error('Error toggling detection:', error);
            this.showError('Please refresh the page and try again');
        }
    }

    toggleTTS() {
        this.isTTSEnabled = !this.isTTSEnabled;
        this.updateUI();
        this.saveState();
        this.sendSettingsUpdate();
    }

    toggleAutoSpeak() {
        this.isAutoSpeak = !this.isAutoSpeak;
        this.updateUI();
        this.saveState();
        this.sendSettingsUpdate();
    }

    toggleOverlay() {
        this.isOverlayEnabled = !this.isOverlayEnabled;
        this.updateUI();
        this.saveState();
        this.sendSettingsUpdate();
    }

    async sendSettingsUpdate() {
        try {
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            
            chrome.tabs.sendMessage(tab.id, {
                action: 'updateSettings',
                settings: {
                    ttsEnabled: this.isTTSEnabled,
                    autoSpeak: this.isAutoSpeak,
                    overlayEnabled: this.isOverlayEnabled
                }
            });
        } catch (error) {
            console.error('Error sending settings update:', error);
        }
    }

    async clearHistory() {
        try {
            await chrome.storage.local.set({ translationHistory: [] });
            this.historyList.innerHTML = '<div class="history-empty">No translations yet</div>';
        } catch (error) {
            console.error('Error clearing history:', error);
        }
    }

    handleMessage(message) {
        switch (message.action) {
            case 'translationUpdate':
                this.detectedText.textContent = message.text || 'Ready to translate...';
                this.addToHistory(message.text);
                break;
            case 'statusUpdate':
                this.updateStatus(message.status);
                break;
            case 'error':
                this.showError(message.message);
                break;
            case 'historyUpdate':
                this.displayHistory(message.history);
                break;
        }
    }

    async addToHistory(text) {
        if (!text || text === 'Ready to translate...') return;
        
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
            this.displayHistory(history);
        } catch (error) {
            console.error('Error adding to history:', error);
        }
    }

    updateHistoryDisplay(history) {
        this.displayHistory(history);
    }

    updateStatus(status) {
        // Update based on actual detection status
        if (status === 'detecting') {
            this.statusText.textContent = 'Detecting...';
            this.statusDot.classList.add('active');
        } else if (status === 'active') {
            this.statusText.textContent = 'Active';
            this.statusDot.classList.add('active');
        } else {
            this.statusText.textContent = 'Inactive';
            this.statusDot.classList.remove('active');
        }
    }

    updateUI() {
        // Update toggle button
        if (this.isActive) {
            this.toggleBtn.textContent = '⏹️ Stop Detection';
            this.toggleBtn.classList.add('active');
            this.statusText.textContent = 'Active';
            this.statusDot.classList.add('active');
        } else {
            this.toggleBtn.innerHTML = '<span>▶️</span> Start Detection';
            this.toggleBtn.classList.remove('active');
            this.statusText.textContent = 'Inactive';
            this.statusDot.classList.remove('active');
        }

        // Update TTS button
        this.ttsBtn.innerHTML = this.isTTSEnabled ? 
            '<span>🔊</span> TTS On' : 
            '<span>🔇</span> TTS Off';
        this.ttsBtn.classList.toggle('muted', !this.isTTSEnabled);

        // Update toggles
        this.autoSpeakToggle.classList.toggle('active', this.isAutoSpeak);
        this.overlayToggle.classList.toggle('active', this.isOverlayEnabled);
    }

    showError(message) {
        this.detectedText.textContent = `Error: ${message}`;
        this.detectedText.style.color = '#ef4444';
        
        setTimeout(() => {
            this.detectedText.style.color = '';
            this.detectedText.textContent = 'Ready to translate...';
        }, 3000);
    }
}

// Initialize popup when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new PopupController();
});
