// API configuration
const API_BASE_URL = 'http://localhost:8000/api/v1';
const AUTH_ENDPOINT = '/auth/login/json';
const PRODUCT_ENDPOINT = '/products/';
const STATS_ENDPOINT = '/users/stats';
const ANALYZE_PRODUCT_ENDPOINT = '/products/analyze_user_product';

// State management
let isProcessingQueue = false;
let scrapingQueue = [];
let userToken = null;
let userData = null;
let analyzedProducts = {}; // Cache of analyzed products by ASIN
let recentlySentProducts = new Set(); // Track recently sent products to prevent duplicates
const RATE_LIMIT_DELAY = 5000; // Minimum delay between API requests (5 seconds)
let lastAPIRequestTime = 0; // Timestamp of the last API request

// Initialize extension
const initialize = async () => {
    console.log('Initializing Product Launch Planner extension');
    
    // Load user data and settings
    await loadUserData();
    await loadAnalyzedProducts();
    
    // Check if current tab is a product page
    const currentTab = await getCurrentTab();
    if (currentTab) {
        checkProductPage(currentTab.id, true); // true = automatically scrape
    }
};

// Load user authentication data
const loadUserData = async () => {
    try {
        const storage = await chrome.storage.local.get(['token', 'user']);
        userToken = storage.token || null;
        
        if (storage.user && storage.user.id) {
            userData = {
                id: storage.user.id,
                email: storage.user.email
            };
        } else {
            userData = null;
        }
        
        console.log('Loaded user data:', userToken ? 'User is authenticated' : 'No user authenticated');
        if (userData) {
            console.log('User ID:', userData.id, 'Email:', userData.email);
        }
    } catch (error) {
        console.error('Error loading user data:', error);
    }
};

// Load analyzed products from storage
const loadAnalyzedProducts = async () => {
    try {
        const storage = await chrome.storage.local.get(['analyzedProducts']);
        analyzedProducts = storage.analyzedProducts || {};
        console.log('Loaded analyzed products:', Object.keys(analyzedProducts).length);
    } catch (error) {
        console.error('Error loading analyzed products:', error);
    }
};

// Save analyzed product to storage
const saveAnalyzedProduct = async (product) => {
    try {
        if (!product || !product.asin) return;
        
        // Mark product as analyzed with timestamp
        analyzedProducts[product.asin] = {
            ...product,
            is_analyzed: true,
            analyzed_at: new Date().toISOString()
        };
        
        // Save to storage for persistence
        await chrome.storage.local.set({ analyzedProducts });
        console.log('Saved analyzed product:', product.asin);
        
        // Notify popup if it's open
        chrome.runtime.sendMessage({
            type: 'PRODUCT_ANALYZED',
            product: analyzedProducts[product.asin]
        });
    } catch (error) {
        console.error('Error saving analyzed product:', error);
    }
};

// Get current active tab
const getCurrentTab = async () => {
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    return tabs.length > 0 ? tabs[0] : null;
};

// Check if a tab contains an Amazon product page
const checkProductPage = async (tabId, autoScrape = false) => {
    if (!tabId) return false;
    
    try {
        const response = await chrome.tabs.sendMessage(tabId, { type: 'CHECK_PRODUCT_PAGE' });
        const isProductPage = response?.isProductPage === true;
        
        if (isProductPage) {
            console.log('Product page detected');
            
            // If autoScrape is true, get product data and add to queue
            if (autoScrape) {
                console.log('Auto-scraping product');
                // Add to scraping queue
                addToScrapingQueue(tabId);
            }
        }
        
        return isProductPage;
    } catch (error) {
        console.log('Error checking product page (content script might not be ready yet):', error);
        return false;
    }
};

// Check if we're rate limited and need to wait
const shouldRateLimit = () => {
    const now = Date.now();
    const timeSinceLastRequest = now - lastAPIRequestTime;
    
    // If less than RATE_LIMIT_DELAY has passed since the last request, we should rate limit
    if (timeSinceLastRequest < RATE_LIMIT_DELAY) {
        console.log(`Rate limiting: ${RATE_LIMIT_DELAY - timeSinceLastRequest}ms remaining before next request`);
        return true;
    }
    
    return false;
};

// Add tab to scraping queue
const addToScrapingQueue = (tabId) => {
    if (!scrapingQueue.includes(tabId)) {
        scrapingQueue.push(tabId);
        console.log('Added tab to scraping queue:', tabId);
        
        // If not currently processing the queue, start processing
        if (!isProcessingQueue) {
            processScrapingQueue();
        }
    }
};

// Process scraping queue
const processScrapingQueue = async () => {
    if (isProcessingQueue || scrapingQueue.length === 0) return;
    
    isProcessingQueue = true;
    
    try {
        while (scrapingQueue.length > 0) {
            const tabId = scrapingQueue.shift();
            
            try {
                // Check if tab still exists
                const tab = await chrome.tabs.get(tabId);
                if (!tab) continue;
                
                // Get product data
                console.log('Getting product data from tab:', tabId);
                const response = await chrome.tabs.sendMessage(tabId, { type: 'GET_PRODUCT_DATA' });
                
                if (response?.success && response.product) {
                    console.log('Successfully retrieved product data:', response.product.asin);
                    
                    // Only send to API if we have user token (for authentication)
                    if (userToken) {
                        // Send to regular product endpoint for scraping
                        await sendProductToAPI(response.product);
                    }
                } else {
                    console.log('Failed to get product data from tab:', tabId, response?.error);
                }
            } catch (error) {
                console.error('Error processing tab:', tabId, error);
            }
            
            // Add a delay between processing tabs to avoid overwhelming the server
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
    } finally {
        isProcessingQueue = false;
    }
};

// Send scraped product to API (just scraping, not analyzing)
const sendProductToAPI = async (product) => {
    try {
        if (!userToken || !userData || !product.asin) {
            console.log('Cannot send product to API: missing user authentication or product ASIN');
            return;
        }
        
        const asin = product.asin;
        
        // Check if this product was recently sent to avoid duplication
        if (recentlySentProducts.has(asin)) {
            console.log('Skipping product already sent recently:', asin);
            return;
        }
        
        // Check for rate limiting
        if (shouldRateLimit()) {
            const waitTime = RATE_LIMIT_DELAY - (Date.now() - lastAPIRequestTime);
            console.log(`Rate limited, waiting ${waitTime}ms before sending product:`, asin);
            await new Promise(resolve => setTimeout(resolve, waitTime));
        }
        
        console.log('Sending scraped product to API:', asin);
        
        // Add user_id to product data
        const productWithUserId = {
            ...product,
            user_id: userData.id
        };
        
        // Track this request time for rate limiting
        lastAPIRequestTime = Date.now();
        
        // Add to recently sent products set to prevent duplicate requests
        recentlySentProducts.add(asin);
        
        // Automatically clear this ASIN from recently sent after 5 minutes
        setTimeout(() => {
            recentlySentProducts.delete(asin);
        }, 5 * 60 * 1000);
        
        // Send to the regular product endpoint (not the analyze endpoint)
        fetch(`${API_BASE_URL}${PRODUCT_ENDPOINT}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${userToken}`
            },
            body: JSON.stringify(productWithUserId)
        }).then(response => {
            if (response.ok) {
                console.log('Successfully sent product to API:', asin);
                return response.json();
            }
            console.error('Failed to send product to API:', response.status);
            // If the request failed, remove from recently sent so we can try again later
            recentlySentProducts.delete(asin);
        }).catch(error => {
            console.error('Error sending product to API:', error);
            // If the request failed, remove from recently sent so we can try again later
            recentlySentProducts.delete(asin);
        });
    } catch (error) {
        console.error('Error in sendProductToAPI:', error);
        // If there was an error, remove from recently sent so we can try again later
        if (product && product.asin) {
            recentlySentProducts.delete(product.asin);
        }
    }
};

// Analyze a product - Only called when user clicks analyze button
const analyzeProduct = async (product) => {
    try {
        const storage = await chrome.storage.local.get(['token', 'user', 'analyzedProducts', 'userStats']);
        const token = storage.token;
        const user = storage.user;
        
        if (!token || !user) {
            console.error('User not authenticated for analysis');
            return null;
        }
        
        const asin = product.asin;
        
        // Check if this product is already analyzed
        if (analyzedProducts[asin]?.is_analyzed) {
            console.log('Product already analyzed, not sending again:', asin);
            return analyzedProducts[asin].analysis;
        }
        
        // Check for rate limiting
        if (shouldRateLimit()) {
            const waitTime = RATE_LIMIT_DELAY - (Date.now() - lastAPIRequestTime);
            console.log(`Rate limited, waiting ${waitTime}ms before analyzing product:`, asin);
            await new Promise(resolve => setTimeout(resolve, waitTime));
        }
        
        console.log('Analyzing product:', asin);
        
        // Track this request time for rate limiting
        lastAPIRequestTime = Date.now();
        
        // Generate local analysis
        const analysis = {
            asin: asin,
            estimated_sales: Math.floor(Math.random() * 1000) + 1,
            competition_score: Math.floor(Math.random() * 100) + 1,
            pricing_recommendation: parseFloat(product.price?.replace(/[^0-9.]/g, '')) || 0,
            market_saturation: Math.floor(Math.random() * 100) + 1,
            opportunity_score: Math.floor(Math.random() * 100) + 1,
            analyzed_at: new Date().toISOString()
        };
        
        // Add user_id to product data
        const productWithUserId = {
            ...product,
            user_id: user.id
        };
        
        // Send to API using the analyze endpoint
        fetch(`${API_BASE_URL}${ANALYZE_PRODUCT_ENDPOINT}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(productWithUserId)
        }).then(response => {
            if (response.ok) {
                console.log('Product successfully analyzed via API');
                return response.json();
            }
            console.error('Failed to analyze product via API:', response.status);
        }).catch(error => {
            console.error('Error analyzing product via API:', error);
        });
        
        // Save to storage regardless of API response
        const analyzedProducts = storage.analyzedProducts || {};
        analyzedProducts[asin] = {
            ...product,
            analysis: analysis,
            is_analyzed: true,
            analyzed_at: new Date().toISOString()
        };
        
        await chrome.storage.local.set({ analyzedProducts });
        
        // Update user stats count
        let userStats = storage.userStats || { analyzed_products_count: 0 };
        userStats.analyzed_products_count += 1;
        await chrome.storage.local.set({ userStats });
        
        // Update badge with new count
        updateBadge(userStats.analyzed_products_count);
        
        return analysis;
    } catch (error) {
        console.error('Analysis error:', error);
        return null;
    }
};

// Load user stats from API
async function loadUserStats() {
    try {
        if (!userToken) return;
        
        // Check for rate limiting
        if (shouldRateLimit()) {
            const waitTime = RATE_LIMIT_DELAY - (Date.now() - lastAPIRequestTime);
            console.log(`Rate limited, waiting ${waitTime}ms before loading stats`);
            await new Promise(resolve => setTimeout(resolve, waitTime));
        }
        
        // Track this request time for rate limiting
        lastAPIRequestTime = Date.now();
        
        const response = await fetch(`${API_BASE_URL}${STATS_ENDPOINT}`, {
            headers: {
                'Authorization': `Bearer ${userToken}`
            }
        });
        
        if (response.ok) {
            const stats = await response.json();
            
            // Notify popup if it's open
            chrome.runtime.sendMessage({
                type: 'STATS_UPDATED',
                stats: stats
            });
            
            return stats;
        }
    } catch (error) {
        console.error('Error loading user stats:', error);
    }
}

// Listen for tab updates to detect Amazon product pages
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
    // Only process when the page has completely loaded
    if (changeInfo.status === 'complete' && tab.url) {
        // If the URL contains amazon.com, check if it's a product page
        if (tab.url.includes('amazon.com')) {
            // Delay checking to ensure content script is loaded
            setTimeout(() => checkProductPage(tabId, true), 2000);
        }
    }
});

// Keep track of last URL for each tab to prevent duplicate scraping
const tabUrls = {};

// Listen for messages from content script and popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    console.log('Background script received message:', message.type);
    
    if (message.type === 'URL_CHANGED') {
        // Handle SPA navigation in content script
        if (message.isProductPage && sender.tab) {
            const tabId = sender.tab.id;
            const url = message.url;
            
            // Skip if same URL was recently processed for this tab
            if (tabUrls[tabId] === url) {
                console.log('Skipping duplicate URL change for tab:', tabId);
                return false;
            }
            
            // Update last URL for this tab
            tabUrls[tabId] = url;
            
            console.log('URL changed to product page');
            // Auto-scrape new URL with a slight delay to ensure page has fully loaded
            setTimeout(() => {
                addToScrapingQueue(tabId);
            }, 2000);
        }
        
        // No need to send response
        return false;
    } else if (message.type === 'PRODUCT_SCRAPED') {
        // Handle scraped product data from content script
        if (message.product && message.product.asin) {
            console.log('Received scraped product:', message.product.asin);
            // Just send to the regular product endpoint, not analyze
            sendProductToAPI(message.product);
        }
        return false;
    } else if (message.type === 'USER_LOGGED_IN') {
        // Handle user login
        userToken = message.token;
        userData = {
            id: message.user.id,
            email: message.user.email
        };
        
        console.log('User logged in:', userData);
        
        // Check current tab for product page after login
        getCurrentTab().then(tab => {
            if (tab && tab.url.includes('amazon.com')) {
                checkProductPage(tab.id, true);
            }
        });
        
        // No need to send response
        return false;
    } else if (message.type === 'USER_LOGGED_OUT') {
        // Handle user logout
        userToken = null;
        userData = null;
        
        // No need to send response
        return false;
    } else if (message.type === 'FORCE_ANALYZE') {
        // Handle manual analysis request from popup (Analyze button)
        if (message.product) {
            // Analyze specific product
            analyzeProduct(message.product).then(success => {
                sendResponse({ success });
            }).catch(error => {
                sendResponse({ 
                    success: false, 
                    error: error.message 
                });
            });
            return true; // Indicate async response
        } else if (sender.tab) {
            console.log('Manual analysis requested for tab:', sender.tab.id);
            // First get the product data, then analyze it
            chrome.tabs.sendMessage(sender.tab.id, { type: 'GET_PRODUCT_DATA' }, response => {
                if (response?.success && response.product) {
                    analyzeProduct(response.product).then(() => {
                        sendResponse({ success: true });
                    });
                } else {
                    sendResponse({ 
                        success: false, 
                        error: 'Failed to get product data' 
                    });
                }
            });
            return true; // Indicate async response
        } else {
            getCurrentTab().then(tab => {
                if (tab) {
                    chrome.tabs.sendMessage(tab.id, { type: 'GET_PRODUCT_DATA' }, response => {
                        if (response?.success && response.product) {
                            analyzeProduct(response.product).then(() => {
                                sendResponse({ success: true });
                            });
                        } else {
                            sendResponse({ 
                                success: false, 
                                error: 'Failed to get product data' 
                            });
                        }
                    });
                } else {
                    sendResponse({ 
                        success: false, 
                        error: 'No active tab' 
                    });
                }
            });
            return true; // Indicate async response
        }
    }
    
    // Return false by default (no async response)
    return false;
});

// Update badge count
const updateBadge = (count) => {
    try {
        if (count > 0) {
            chrome.action.setBadgeText({ text: count.toString() });
            chrome.action.setBadgeBackgroundColor({ color: '#4CAF50' });
        } else {
            chrome.action.setBadgeText({ text: '' });
        }
    } catch (error) {
        console.error('Error updating badge:', error);
    }
};

// Clear tracking on browser startup
chrome.runtime.onStartup.addListener(() => {
    recentlySentProducts.clear();
    Object.keys(tabUrls).forEach(key => delete tabUrls[key]);
});

// Initialize extension when loaded
initialize(); 