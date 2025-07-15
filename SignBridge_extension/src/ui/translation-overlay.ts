export class TranslationOverlay {
    private overlayElement: HTMLElement;
    private textElement: HTMLElement;
    private isEnabled: boolean = false;

    constructor() {
        this.createOverlay();
    }

    private createOverlay() {
        // Create overlay container
        this.overlayElement = document.createElement('div');
        this.overlayElement.id = 'signbridge-overlay';
        this.overlayElement.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 15px;
            border-radius: 8px;
            font-family: Arial, sans-serif;
            font-size: 20px;
            z-index: 99999;
            pointer-events: none;
        `;

        // Create text element
        this.textElement = document.createElement('div');
        this.textElement.id = 'translation-text';
        this.textElement.style.cssText = 'font-size: 24px;';

        // Add elements to overlay
        this.overlayElement.appendChild(this.textElement);
        document.body.appendChild(this.overlayElement);
    }

    public updateTranslation(text: string) {
        if (!this.isEnabled) return;
        
        this.textElement.textContent = text;
    }

    public toggleVisibility(enabled: boolean) {
        this.isEnabled = enabled;
        if (enabled) {
            this.overlayElement.style.display = 'block';
        } else {
            this.overlayElement.style.display = 'none';
        }
    }

    public cleanup() {
        this.overlayElement.remove();
    }
}
