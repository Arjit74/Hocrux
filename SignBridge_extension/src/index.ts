import { HandDetector } from './gesture-recognition/hand-detector';
import { GestureClassifier } from './gesture-recognition/gesture-classifier';
import { TranslationOverlay } from './ui/translation-overlay';

export class SignBridgeExtension {
    private handDetector: HandDetector;
    private gestureClassifier: GestureClassifier;
    private translationOverlay: TranslationOverlay;
    private isInitialized: boolean = false;

    constructor() {
        this.handDetector = new HandDetector();
        this.gestureClassifier = new GestureClassifier();
        this.translationOverlay = new TranslationOverlay();
    }

    async initialize() {
        try {
            // Initialize components
            await this.handDetector.initialize();
            await this.gestureClassifier.loadModel();

            // Start gesture recognition loop
            this.startRecognitionLoop();

            this.isInitialized = true;
            console.log('SignBridge extension initialized successfully');
        } catch (error) {
            console.error('Failed to initialize extension:', error);
            throw error;
        }
    }

    private async startRecognitionLoop() {
        if (!this.isInitialized) return;

        const interval = setInterval(async () => {
            try {
                // Get hand landmarks
                const rawLandmarks = await this.handDetector.getHandLandmarks();
                if (!rawLandmarks) return;

                // 🔧 Convert [[x, y, z], ...] to [{x, y, z}, ...]
                const convertedLandmarks = rawLandmarks.map(
                    ([x, y, z]) => ({ x, y, z })
                );

                // Classify gesture
                const gesture = await this.gestureClassifier.classifyGesture(convertedLandmarks);

                // Update translation overlay
                this.translationOverlay.updateTranslation(gesture);
            } catch (error) {
                console.error('Error in recognition loop:', error);
            }
        }, 100); // Check every 100ms

        // Cleanup when extension is disabled
        chrome.runtime.onMessage.addListener((request) => {
            if (request.action === 'disable') {
                clearInterval(interval);
                this.handDetector.stop();
                this.translationOverlay.cleanup();
            }
        });
    }

    public toggleOverlay(enabled: boolean) {
        this.translationOverlay.toggleVisibility(enabled);
    }
}