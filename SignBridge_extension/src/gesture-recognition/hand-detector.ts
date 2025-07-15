import { Hands, Results } from '@mediapipe/hands';
import { Camera } from '@mediapipe/camera_utils';

export class HandDetector {
    private hands: Hands | null = null;
    private camera: Camera | null = null;
    private videoElement: HTMLVideoElement;
    private isInitialized = false;
    private isRunning = false;
    private latestLandmarks: number[][] | null = null;

    constructor() {
        this.videoElement = document.createElement('video');
        this.videoElement.style.display = 'none';
        document.body.appendChild(this.videoElement);
    }

    async initialize() {
        if (this.isInitialized) return;

        try {
            this.hands = new Hands({
                locateFile: (file) =>
                    `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`
            });

            this.hands.setOptions({
                maxNumHands: 1,
                modelComplexity: 1,
                minDetectionConfidence: 0.5,
                minTrackingConfidence: 0.5
            });

            // Setup the onResults callback
            this.hands.onResults((results: Results) => {
                if (results.multiHandLandmarks?.length) {
                    this.latestLandmarks = results.multiHandLandmarks[0].map(
                        point => [point.x, point.y, point.z]
                    );
                } else {
                    this.latestLandmarks = null;
                }
            });

            this.camera = new Camera(this.videoElement, {
                onFrame: async () => {
                    if (this.hands && this.isRunning) {
                        await this.hands.send({ image: this.videoElement });
                    }
                },
                width: 640,
                height: 480
            });

            await this.camera.start();
            this.isInitialized = true;
        } catch (error) {
            console.error('Failed to initialize hand detector:', error);
            this.cleanup();
            throw error;
        }
    }

    async getHandLandmarks(): Promise<number[][] | null> {
        return this.latestLandmarks;
    }

    async start() {
        this.isRunning = true;
    }

    async stop() {
        this.isRunning = false;
        await this.cleanup();
    }

    private cleanup() {
        if (this.camera) {
            this.camera.stop();
            this.camera = null;
        }
        if (this.hands) {
            this.hands.close();
            this.hands = null;
        }
        this.videoElement.remove();
        this.videoElement = document.createElement('video');
        this.isInitialized = false;
    }
}