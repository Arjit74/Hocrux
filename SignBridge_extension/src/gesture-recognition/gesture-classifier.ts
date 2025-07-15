import * as tf from '@tensorflow/tfjs';

export class GestureClassifier {
    private model: tf.LayersModel | null = null;
    private labels: string[] = [];

    constructor() {
        // Initialize labels for ASL alphabet
        this.labels = Array.from({ length: 26 }, (_, i) => String.fromCharCode(65 + i));
    }

    async loadModel() {
        try {
            this.model = await tf.loadLayersModel('model/gesture_model.json');
            console.log('Gesture recognition model loaded successfully');
        } catch (error) {
            console.error('Failed to load gesture recognition model:', error);
            throw new Error('Failed to load gesture recognition model');
        }
    }

    async classifyGesture(landmarks: Array<{ x: number; y: number; z: number }>): Promise<string> {
        if (!this.model) {
            throw new Error('Model not loaded');
        }
    
        if (!landmarks || landmarks.length === 0) {
            throw new Error('No landmarks provided');
        }
    
        try {
            const normalized = this.normalizeLandmarks(landmarks);
            const input = tf.tensor([normalized]);
    
            const prediction = this.model.predict(input);
            const predictionTensor = Array.isArray(prediction) ? prediction[0] : prediction as tf.Tensor;
    
            const predictedClass = predictionTensor.argMax(-1).dataSync()[0];
    
            input.dispose();
            predictionTensor.dispose();
    
            return this.labels[predictedClass];
        } catch (error) {
            console.error('Error during gesture classification:', error);
            throw error;
        }
    }

    private normalizeLandmarks(landmarks: Array<{ x: number; y: number; z: number }>): number[][] {
        // Get wrist position as reference
        const wrist = landmarks[0];
        
        // Normalize landmarks relative to wrist
        return landmarks.map(point => [
            point.x - wrist.x,
            point.y - wrist.y,
            point.z - wrist.z
        ]);
    }
}
