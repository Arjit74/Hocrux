class TextOverlay {
    constructor() {
        this.overlay = null;
        this.textElement = null;
        this.isVisible = false;
        this.currentText = '';
        this.fadeTimeout = null;
        
        this.createOverlay();
    }

    createOverlay() {
        // Create overlay container
        this.overlay = document.createElement('div');
        this.overlay.id = 'signbridge-overlay';
        this.overlay.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            width: 300px;
            max-width: 90vw;
            background: linear-gradient(135deg, rgba(0, 0, 0, 0.9), rgba(30, 30, 30, 0.95));
            color: white;
            padding: 16px 20px;
            border-radius: 12px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            font-size: 16px;
            font-weight: 500;
            line-height: 1.4;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            z-index: 999999;
            transform: translateX(100%);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            pointer-events: none;
            user-select: none;
        `;

        // Create header
        const header = document.createElement('div');
        header.style.cssText = `
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;
            padding-bottom: 8px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            font-size: 12px;
            font-weight: 600;
            color: rgba(255, 255, 255, 0.7);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        `;
        
        const icon = document.createElement('span');
        icon.textContent = '👋';
        icon.style.fontSize = '14px';
        
        const title = document.createElement('span');
        title.textContent = 'SignBridge Translation';
        
        header.appendChild(icon);
        header.appendChild(title);

        // Create text content
        this.textElement = document.createElement('div');
        this.textElement.style.cssText = `
            font-size: 16px;
            font-weight: 500;
            line-height: 1.4;
            color: white;
            min-height: 20px;
            word-wrap: break-word;
        `;
        this.textElement.textContent = 'Ready to translate...';

        // Create confidence indicator
        this.confidenceBar = document.createElement('div');
        this.confidenceBar.style.cssText = `
            width: 100%;
            height: 3px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 2px;
            margin-top: 12px;
            overflow: hidden;
        `;

        this.confidenceFill = document.createElement('div');
        this.confidenceFill.style.cssText = `
            height: 100%;
            background: linear-gradient(90deg, #22c55e, #16a34a);
            border-radius: 2px;
            width: 0%;
            transition: width 0.3s ease;
        `;

        this.confidenceBar.appendChild(this.confidenceFill);

        // Assemble overlay
        this.overlay.appendChild(header);
        this.overlay.appendChild(this.textElement);
        this.overlay.appendChild(this.confidenceBar);

        // Add to page
        document.body.appendChild(this.overlay);

        // Add event listeners for interaction
        this.addEventListeners();
    }

    addEventListeners() {
        // Allow clicking to dismiss temporarily
        this.overlay.addEventListener('click', () => {
            this.temporarilyHide();
        });

        // Auto-hide on page navigation
        window.addEventListener('beforeunload', () => {
            this.hide();
        });

        // Reposition on window resize
        window.addEventListener('resize', () => {
            this.adjustPosition();
        });
    }

    show() {
        if (this.isVisible) return;
        
        this.isVisible = true;
        this.overlay.style.transform = 'translateX(0)';
        this.overlay.style.opacity = '1';
        
        // Add subtle entrance animation
        setTimeout(() => {
            this.overlay.style.transform = 'translateX(0) scale(1)';
        }, 100);
    }

    hide() {
        if (!this.isVisible) return;
        
        this.isVisible = false;
        this.overlay.style.transform = 'translateX(100%)';
        this.overlay.style.opacity = '0';
    }

    temporarilyHide() {
        this.overlay.style.opacity = '0.3';
        
        setTimeout(() => {
            if (this.isVisible) {
                this.overlay.style.opacity = '1';
            }
        }, 3000);
    }

    updateText(text, confidence = 0.8) {
        if (!text || text === this.currentText) return;
        
        this.currentText = text;
        
        // Clear previous fade timeout
        if (this.fadeTimeout) {
            clearTimeout(this.fadeTimeout);
        }
        
        // Add typing animation
        this.animateTextUpdate(text);
        
        // Update confidence indicator
        this.updateConfidence(confidence);
        
        // Auto-fade after delay
        this.fadeTimeout = setTimeout(() => {
            this.fadeText();
        }, 4000);
        
        // Show overlay if hidden
        if (!this.isVisible) {
            this.show();
        }
    }

    animateTextUpdate(newText) {
        // Fade out current text
        this.textElement.style.opacity = '0.5';
        this.textElement.style.transform = 'translateY(-5px)';
        
        setTimeout(() => {
            this.textElement.textContent = newText;
            this.textElement.style.opacity = '1';
            this.textElement.style.transform = 'translateY(0)';
            
            // Add highlight effect
            this.textElement.style.background = 'linear-gradient(90deg, rgba(59, 130, 246, 0.1), transparent)';
            
            setTimeout(() => {
                this.textElement.style.background = 'transparent';
            }, 500);
        }, 150);
    }

    updateConfidence(confidence) {
        const percentage = Math.round(confidence * 100);
        this.confidenceFill.style.width = `${percentage}%`;
        
        // Change color based on confidence
        if (confidence > 0.8) {
            this.confidenceFill.style.background = 'linear-gradient(90deg, #22c55e, #16a34a)';
        } else if (confidence > 0.6) {
            this.confidenceFill.style.background = 'linear-gradient(90deg, #f59e0b, #d97706)';
        } else {
            this.confidenceFill.style.background = 'linear-gradient(90deg, #ef4444, #dc2626)';
        }
    }

    fadeText() {
        this.textElement.style.opacity = '0.6';
        this.confidenceBar.style.opacity = '0.3';
    }

    adjustPosition() {
        // Adjust position based on screen size
        const screenWidth = window.innerWidth;
        
        if (screenWidth < 768) {
            this.overlay.style.top = '10px';
            this.overlay.style.right = '10px';
            this.overlay.style.left = '10px';
            this.overlay.style.width = 'auto';
            this.overlay.style.maxWidth = 'none';
        } else {
            this.overlay.style.top = '20px';
            this.overlay.style.right = '20px';
            this.overlay.style.left = 'auto';
            this.overlay.style.width = '300px';
            this.overlay.style.maxWidth = '90vw';
        }
    }

    setTheme(theme = 'dark') {
        if (theme === 'light') {
            this.overlay.style.background = 'linear-gradient(135deg, rgba(255, 255, 255, 0.95), rgba(248, 250, 252, 0.98))';
            this.overlay.style.color = '#1f2937';
            this.overlay.style.border = '1px solid rgba(0, 0, 0, 0.1)';
        } else {
            this.overlay.style.background = 'linear-gradient(135deg, rgba(0, 0, 0, 0.9), rgba(30, 30, 30, 0.95))';
            this.overlay.style.color = 'white';
            this.overlay.style.border = '1px solid rgba(255, 255, 255, 0.1)';
        }
    }

    destroy() {
        if (this.overlay && this.overlay.parentNode) {
            this.overlay.parentNode.removeChild(this.overlay);
        }
        
        if (this.fadeTimeout) {
            clearTimeout(this.fadeTimeout);
        }
    }
}

// Export for use in content script
window.TextOverlay = TextOverlay;