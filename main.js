class GestureRecognizer {
    constructor() {
        this.video = document.getElementById('video');
        this.statusElement = document.getElementById('status');
        this.hands = null;
        this.detectedGesture = null;
        this.lastGestureTime = 0;
        this.gestureCooldown = 500; // ms
        
        this.initializeCamera();
        this.initializeHands();
    }

    async initializeCamera() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: 'user'
                },
                audio: false
            });
            this.video.srcObject = stream;
            this.updateStatus('Camera initialized');
        } catch (error) {
            this.updateStatus(`Camera error: ${error.message}`, true);
            console.error('Camera initialization error:', error);
        }
    }

    initializeHands() {
        this.hands = new Hands({
            locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`
        });

        this.hands.setOptions({
            maxNumHands: 1,
            modelComplexity: 1,
            minDetectionConfidence: 0.7,
            minTrackingConfidence: 0.5
        });

        this.hands.onResults(this.onHandsResults.bind(this));
        
        this.updateStatus('Gesture model loading...');
        this.hands.initialize().then(() => {
            this.updateStatus('Gesture model ready!');
            this.startDetection();
        }).catch(error => {
            this.updateStatus(`Model error: ${error.message}`, true);
            console.error('Model initialization error:', error);
        });
    }

    onHandsResults(results) {
        const now = Date.now();
        if (now - this.lastGestureTime < this.gestureCooldown) {
            return;
        }

        if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
            const landmarks = results.multiHandLandmarks[0];
            const gesture = this.classifyGesture(landmarks);
            
            if (gesture && gesture !== this.detectedGesture) {
                this.detectedGesture = gesture;
                this.lastGestureTime = now;
                this.handleGesture(gesture);
            }
        } else if (this.detectedGesture !== 'no_hands') {
            this.detectedGesture = 'no_hands';
            this.updateStatus('No hands detected');
        }
    }

    classifyGesture(landmarks) {
        // Simple gesture classification based on finger states
        const fingerStates = this.getFingerStates(landmarks);
        const isThumbsUp = this.isThumbsUp(fingerStates);
        const isVictory = this.isVictory(fingerStates);
        const isOpenHand = this.isOpenHand(fingerStates);
        const isFist = this.isFist(fingerStates);
        const isPointing = this.isPointing(fingerStates);

        if (isThumbsUp) return 'thumbs_up';
        if (isVictory) return 'victory';
        if (isOpenHand) return 'open_hand';
        if (isFist) return 'fist';
        if (isPointing) return 'pointing';
        
        return null;
    }

    getFingerStates(landmarks) {
        // Simplified finger state detection
        // Returns an object with finger states (0 = closed, 1 = open)
        const fingerTips = [4, 8, 12, 16, 20]; // Thumb, Index, Middle, Ring, Pinky
        const fingerJoints = [2, 5, 9, 13, 17]; // Base of each finger
        
        return fingerTips.map((tip, i) => {
            const tipY = landmarks[tip].y;
            const jointY = landmarks[fingerJoints[i]].y;
            return tipY < jointY ? 1 : 0; // 1 = open, 0 = closed
        });
    }

    isThumbsUp(fingerStates) {
        // Thumb up: only thumb is extended
        return fingerStates[0] === 1 && 
               fingerStates.slice(1).every(state => state === 0);
    }

    isVictory(fingerStates) {
        // Victory sign: index and middle fingers up, others down
        return fingerStates[1] === 1 && // Index
               fingerStates[2] === 1 && // Middle
               fingerStates[0] === 0 && // Thumb
               fingerStates[3] === 0 && // Ring
               fingerStates[4] === 0;   // Pinky
    }

    isOpenHand(fingerStates) {
        // All fingers extended
        return fingerStates.every(state => state === 1);
    }

    isFist(fingerStates) {
        // All fingers closed
        return fingerStates.every(state => state === 0);
    }

    isPointing(fingerStates) {
        // Only index finger extended
        return fingerStates[1] === 1 && 
               fingerStates[0] === 0 && 
               fingerStates.slice(2).every(state => state === 0);
    }

    handleGesture(gesture) {
        const gestureNames = {
            'thumbs_up': '👍 Thumbs Up',
            'victory': '✌️ Victory',
            'open_hand': '🖐️ Open Hand',
            'fist': '✊ Fist',
            'pointing': '👆 Pointing',
            'no_hands': 'No hands detected'
        };

        const gestureName = gestureNames[gesture] || 'Unknown gesture';
        this.updateStatus(`Detected: ${gestureName}`);
        console.log(`Gesture detected: ${gesture}`);
    }

    updateStatus(message, isError = false) {
        this.statusElement.textContent = message;
        this.statusElement.style.color = isError ? '#d32f2f' : '#333';
    }

    startDetection() {
        const sendToNet = async () => {
            if (this.video.readyState >= 2) { // HAVE_CURRENT_DATA
                await this.hands.send({ image: this.video });
            }
            requestAnimationFrame(sendToNet);
        };
        sendToNet();
    }
}

// Initialize when the page loads
window.addEventListener('load', () => {
    const gestureRecognizer = new GestureRecognizer();
    
    // Handle page visibility changes
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') {
            gestureRecognizer.startDetection();
        }
    });
});