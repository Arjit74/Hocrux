/// <reference types="chrome" />

import { SignBridgeExtension } from './index';

// Initialize the extension
const extension = new SignBridgeExtension();

// Initialize when the content script loads
window.addEventListener('load', async () => {
    try {
        await extension.initialize();
        console.log('SignBridge extension initialized');
    } catch (error) {
        console.error('Failed to initialize extension:', error);
    }
});

// Handle messages from popup
chrome.runtime.onMessage.addListener((request) => {
    switch (request.action) {
        case 'toggleOverlay':
            extension.toggleOverlay(request.enabled);
            break;
        case 'disable':
            // Cleanup when extension is disabled
            extension.toggleOverlay(false);
            break;
    }
});
