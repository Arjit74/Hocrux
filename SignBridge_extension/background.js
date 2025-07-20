// Service worker for SignBridge extension
chrome.runtime.onInstalled.addListener(() => {
  console.log('SignBridge extension installed');
  
  // Initialize default settings
  chrome.storage.local.get(['ttsEnabled', 'autoSpeak', 'overlayEnabled'], (result) => {
    const defaults = {
      ttsEnabled: result.ttsEnabled ?? true,
      autoSpeak: result.autoSpeak ?? true,
      overlayEnabled: result.overlayEnabled ?? true
    };
    chrome.storage.local.set(defaults);
  });
});

// Handle messages from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // Keep service worker alive for async operations
  sendResponse({ received: true });
  return true;
});