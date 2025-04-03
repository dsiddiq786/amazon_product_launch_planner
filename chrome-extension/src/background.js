// Listen for messages from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'PRODUCT_SCRAPED') {
        // Forward the message to the popup
        chrome.runtime.sendMessage(message);
    }
});

// Handle extension installation
chrome.runtime.onInstalled.addListener(() => {
    // Clear any existing storage
    chrome.storage.local.clear();
});

// Handle tab updates to check for product pages
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.url) {
        const url = new URL(tab.url);
        if (url.hostname.includes('amazon.')) {
            chrome.tabs.sendMessage(tabId, { type: 'CHECK_PRODUCT_PAGE' });
        }
    }
}); 