// Assuming EventEmitter is globally available or imported
class GestureRecognizer extends EventEmitter {
    constructor() {
        super();
        this.hands = null;
        this.isInitialized = false;
        this.gestureMap = this.createGestureMap();
        this.lastDetectedGesture = null;
        this.detectionBuffer = [];
        this.bufferSize = 10;
        this.confidenceThreshold = 0.3; // Lower threshold for better detection
        this.detectionCooldown = 500; // Reduce cooldown to 0.5 seconds
        this.bufferSize = 10; // Increase buffer size for smoother detection
        this.gestureBuffer = [];
        this.gestureBufferSize = 10;
        this.frameRateControl = {
            lastFrameTime: 0,
            targetFPS: 30,
            frameInterval: 1000 / 30
        };
        this.calibration = {
            isCalibrating: false,
            samples: [],
            lightingThreshold: 0.5
        };
        this.userPreferences = this.loadUserPreferences();
    }

    createGestureMap() {
        return {
            'open_hand': { text: 'Hello', confidence: 0.8 },
            'thumbs_up': { text: 'Good', confidence: 0.8 },
            'peace_sign': { text: 'Peace/Two', confidence: 0.8 },
            'fist': { text: 'Stop', confidence: 0.8 },
            'pointing_up': { text: 'One', confidence: 0.8 }
        };
    }

    // Implement proper MediaPipe integration
    async processWithMediaPipe(imageData) {
        if (!this.shouldProcessFrame()) return null;
        
        try {
            const results = await this.hands.send({image: imageData});
            
            if (results.multiHandLandmarks) {
                for (const landmarks of results.multiHandLandmarks) {
                    const gesture = this.classifyGesture(landmarks);
                    if (gesture) {
                        this.addToGestureBuffer(gesture);
                        return this.getSmoothedGesture();
                    }
                }
            }
            return null;
        } catch (error) {
            this.handleError(error, 'processWithMediaPipe');
            return null;
        }
    }

    async initHands() {
        // Load MediaPipe Hands script
        await new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js';
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });

        // Initialize MediaPipe Hands
        const hands = new window.Hands({
            locateFile: file => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`
        });

        hands.setOptions({
            maxNumHands: 1,
            modelComplexity: 1,
            minDetectionConfidence: 0.7,
            minTrackingConfidence: 0.7
        });

        hands.onResults(results => this.onHandsResults(results));

        await hands.initialize();
        this.hands = hands;
        this.isInitialized = true;
        this.emit('initialized');
    }

    async processFrame(imageData) {
        if (!this.shouldProcessFrame() || !this.hands) return;
        await this.hands.send({ image: imageData });
    }

    onHandsResults(results) {
        if (!results.multiHandLandmarks || results.multiHandLandmarks.length === 0) {
            this.currentGesture = null;
            return;
        }

        const now = Date.now();
        if (this.lastDetection && (now - this.lastDetection) < this.detectionCooldown) return;

        const landmarks = results.multiHandLandmarks[0];
        const gesture = this.classifyGesture(landmarks);

        if (gesture) {
            this.currentGesture = {
                gesture,
                translation: this.gestureMap[gesture]?.text || gesture,
                confidence: this.gestureMap[gesture]?.confidence || 1.0,
                landmarks,
                timestamp: now
            };
            this.lastDetection = now;
            this.emit('gesture', this.currentGesture);
        }
    }

    classifyGesture(landmarks) {
        const wrist = landmarks[0];
        const fingers = {
            thumb: { base: landmarks[2], mid: landmarks[3], tip: landmarks[4] },
            index: { base: landmarks[5], mid: landmarks[6], tip: landmarks[8] },
            middle: { base: landmarks[9], mid: landmarks[10], tip: landmarks[12] },
            ring: { base: landmarks[13], mid: landmarks[14], tip: landmarks[16] },
            pinky: { base: landmarks[17], mid: landmarks[18], tip: landmarks[20] }
        };

        const states = {
            thumb: this.calculateFingerState(fingers.thumb.tip, fingers.thumb.mid, fingers.thumb.base, wrist, true),
            index: this.calculateFingerState(fingers.index.tip, fingers.index.mid, fingers.index.base, wrist),
            middle: this.calculateFingerState(fingers.middle.tip, fingers.middle.mid, fingers.middle.base, wrist),
            ring: this.calculateFingerState(fingers.ring.tip, fingers.ring.mid, fingers.ring.base, wrist),
            pinky: this.calculateFingerState(fingers.pinky.tip, fingers.pinky.mid, fingers.pinky.base, wrist)
        };

        const angles = {
            thumbIndex: this.calculateAngle(fingers.thumb.tip, fingers.index.tip, wrist),
            indexMiddle: this.calculateAngle(fingers.index.tip, fingers.middle.tip, wrist),
            middleRing: this.calculateAngle(fingers.middle.tip, fingers.ring.tip, wrist),
            ringPinky: this.calculateAngle(fingers.ring.tip, fingers.pinky.tip, wrist)
        };

        if (this.isOpenHand(states)) return 'open_hand';
        if (this.isThumbsUp(states, angles)) return 'thumbs_up';
        if (this.isPeaceSign(states, angles)) return 'peace_sign';
        if (this.isFist(states)) return 'fist';
        if (this.isPointingUp(states)) return 'pointing_up';

        return null;
    }

    calculateFingerState(tip, mid, base, wrist, isThumb = false) {
        const angle1 = this.calculateAngle(tip, mid, base);
        const angle2 = this.calculateAngle(mid, base, wrist);
        const threshold = isThumb ? 0.3 : 0.7;

        return {
            extended: angle1 > threshold && angle2 > threshold
        };
    }

    calculateAngle(p1, p2, p3) {
        const v1 = { x: p1.x - p2.x, y: p1.y - p2.y, z: p1.z - p2.z };
        const v2 = { x: p3.x - p2.x, y: p3.y - p2.y, z: p3.z - p2.z };
        const dot = v1.x * v2.x + v1.y * v2.y + v1.z * v2.z;
        const mag1 = Math.sqrt(v1.x ** 2 + v1.y ** 2 + v1.z ** 2);
        const mag2 = Math.sqrt(v2.x ** 2 + v2.y ** 2 + v2.z ** 2);
        return Math.acos(dot / (mag1 * mag2)) * (180 / Math.PI);
    }

    isOpenHand(states) {
        return Object.values(states).every(f => f.extended);
    }

    isThumbsUp(states, angles) {
        return states.thumb.extended &&
               !states.index.extended &&
               !states.middle.extended &&
               !states.ring.extended &&
               !states.pinky.extended &&
               angles.thumbIndex > 45;
    }

    isPeaceSign(states, angles) {
        return !states.thumb.extended &&
               states.index.extended &&
               states.middle.extended &&
               !states.ring.extended &&
               !states.pinky.extended &&
               angles.indexMiddle < 30;
    }

    isFist(states) {
        return Object.values(states).every(f => !f.extended);
    }

    isPointingUp(states) {
        return states.index.extended &&
               !states.thumb.extended &&
               !states.middle.extended &&
               !states.ring.extended &&
               !states.pinky.extended;
    }

    shouldProcessFrame() {
        const now = performance.now();
        if (now - this.frameRateControl.lastFrameTime < this.frameRateControl.frameInterval) {
            return false;
        }
        this.frameRateControl.lastFrameTime = now;
        return true;
    }

    loadUserPreferences() {
        try {
            return JSON.parse(localStorage.getItem('signbridge_preferences')) || {
                confidenceThreshold: 0.5,
                detectionCooldown: 1000,
                customGestures: {}
            };
        } catch {
            return {};
        }
    }

    handleError(error, context) {
        const errorLog = {
            timestamp: new Date().toISOString(),
            context,
            error: error.message,
            stack: error.stack
        };
        console.error("GestureRecognizer Error:", errorLog);
        this.emit("error", errorLog);
    }
}

// Export for use in content script
window.GestureRecognizer = GestureRecognizer;
