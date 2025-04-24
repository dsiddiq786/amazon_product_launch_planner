// Check if current page is an Amazon product page
const isProductPage = () => {
    // Check URL patterns
    const path = window.location.pathname;
    const isProductUrl = path.includes('/dp/') || 
                         path.includes('/gp/product/') || 
                         path.includes('/product/') ||
                         path.includes('/gp/offer-listing/');
    
    // Check for product-specific elements
    const hasProductTitle = !!document.querySelector('#productTitle, #title, .product-title, h1.a-size-large');
    const hasProductPrice = !!document.querySelector('.a-price .a-offscreen, #priceblock_ourprice, #priceblock_dealprice, span.a-price');
    
    // Additional checks for product elements that might be present
    const hasAddToCartButton = !!document.querySelector('#add-to-cart-button, #submit.add-to-cart');
    const hasBuyNowButton = !!document.querySelector('#buy-now-button');
    const hasProductDetail = !!document.querySelector('#productDetails, #detail-bullets, #detailBullets');
    
    // Look for any ASIN in the page - strong indicator of a product page
    const hasAsin = document.body.innerHTML.match(/[A-Z0-9]{10}/) !== null;
    
    // Debug
    console.log('isProductPage checks:', { 
        isProductUrl, 
        hasProductTitle, 
        hasProductPrice,
        hasAddToCartButton,
        hasBuyNowButton,
        hasProductDetail,
        hasAsin
    });
    
    // It's a product page if URL pattern matches OR if it has key product elements
    const isProduct = isProductUrl || 
                     (hasProductTitle && hasProductPrice) || 
                     (hasProductTitle && (hasAddToCartButton || hasBuyNowButton)) ||
                     (hasProductTitle && hasProductDetail);
    
    console.log('isProductPage result:', isProduct);
    
    return isProduct;
};

// Maximum number of retries for robust scraping
const MAX_RETRIES = 3;

// Extract category hierarchy from breadcrumbs
const extractCategoryHierarchy = () => {
    const breadcrumbs = [];
    const breadcrumbSelectors = [
        '#wayfinding-breadcrumbs_container ul li a',
        '#wayfinding-breadcrumbs_feature_div ul li a',
        '.a-breadcrumb li a',
        '.a-unordered-list.a-horizontal.a-size-small li a'
    ];

    // Try different selectors to find breadcrumbs
    for (const selector of breadcrumbSelectors) {
        const elements = document.querySelectorAll(selector);
        if (elements.length > 0) {
            elements.forEach(el => {
                const text = el.textContent.trim();
                // Only add non-empty text that's not a navigation symbol
                if (text && !text.includes('›') && !text.includes('>')) {
                    breadcrumbs.push(text);
                }
            });
            break;
        }
    }

    // If no breadcrumbs found with anchors, try text nodes
    if (breadcrumbs.length === 0) {
        const textSelectors = [
            '#wayfinding-breadcrumbs_container ul li',
            '#wayfinding-breadcrumbs_feature_div ul li',
            '.a-breadcrumb li'
        ];

        for (const selector of textSelectors) {
            const elements = document.querySelectorAll(selector);
            if (elements.length > 0) {
                elements.forEach(el => {
                    const text = el.textContent.trim();
                    // Only add non-empty text that's not a navigation symbol
                    if (text && !text.includes('›') && !text.includes('>')) {
                        breadcrumbs.push(text);
                    }
                });
                break;
            }
        }
    }

    console.log('Extracted breadcrumbs:', breadcrumbs);

    if (breadcrumbs.length > 0) {
        return {
            main_category: breadcrumbs[0],
            sub_categories: breadcrumbs.slice(1)
        };
    }
    
    // If no breadcrumbs found, try to extract from page metadata
    const categoryEl = document.querySelector('meta[name="keywords"]');
    if (categoryEl) {
        const categories = categoryEl.getAttribute('content').split(',');
        if (categories.length > 0) {
            return {
                main_category: categories[0].trim(),
                sub_categories: categories.slice(1).map(c => c.trim())
            };
        }
    }

    return {
        main_category: '',
        sub_categories: []
    };
};

// Main product data extraction function
const extractProductData = () => {
    try {
      const data = {};
  
      // --- Title ---
      const titleSelectors = ['#productTitle', '#title', '.product-title', 'h1.a-size-large'];
      for (const sel of titleSelectors) {
        const el = document.querySelector(sel);
        if (el && el.textContent.trim()) {
          data.title = el.textContent.trim();
          break;
        }
      }
  
      // --- Description ---
      const descriptionSelectors = ['#productDescription', '#feature-bullets', '#aplus', '.a-expander-content'];
      let description = '';
      for (const sel of descriptionSelectors) {
        const el = document.querySelector(sel);
        if (el && el.textContent.trim()) {
          description += el.textContent.trim() + ' ';
        }
      }
      data.description = description.trim();
  
      // --- ASIN ---
      let asin = '';
      
      // Method 1: URL pattern matching
      const urlMatch = window.location.pathname.match(/\/([A-Z0-9]{10})(\/|$|\?)/);
      if (urlMatch && urlMatch[1]) {
        asin = urlMatch[1];
      }
      
      // Method 2: Hidden ASIN input if not found in URL
      if (!asin) {
        const asinEl = document.querySelector('[name="ASIN"], input[name="asin"], [data-asin]');
        if (asinEl) {
          asin = asinEl.value || asinEl.getAttribute('data-asin') || '';
        }
      }
      
      // Method 3: Look for ASIN in detail bullets
      if (!asin) {
        const detailElements = document.querySelectorAll('#detailBullets_feature_div li, #productDetails tr');
        for (const el of detailElements) {
          const text = el.textContent;
          if (text.includes('ASIN') || text.includes('ISBN')) {
            const match = text.match(/[A-Z0-9]{10}/);
            if (match) {
              asin = match[0];
              break;
            }
          }
        }
      }
      
      // Method 4: Search in entire page body as last resort
      if (!asin) {
        const bodyText = document.body.innerHTML;
        const asinMatches = bodyText.match(/ASIN\s*:\s*([A-Z0-9]{10})/i) || 
                           bodyText.match(/ASIN[^\w]([A-Z0-9]{10})/i) ||
                           bodyText.match(/item model number[^\w]+([A-Z0-9]{10})/i);
        if (asinMatches && asinMatches[1]) {
          asin = asinMatches[1];
        }
      }
      
      console.log('Extracted ASIN:', asin);
      data.asin = asin;
  
      // --- Price ---
      const priceSelectors = [
        '.a-price .a-offscreen',
        '#priceblock_ourprice',
        '#priceblock_dealprice',
        '.a-price .a-price-whole',
        '.priceToPay span.a-price-whole',
        '.a-section .a-color-price'
      ];
      let price = '';
      for (const sel of priceSelectors) {
        const el = document.querySelector(sel);
        if (el && el.textContent.trim()) {
          price = el.textContent.trim();
          break;
        }
      }
      data.price = price;
  
      // --- Rating ---
      let rating = '';
      const ratingSelectors = [
        '#acrPopover',
        '.a-icon-star',
        '.reviewCountTextLinkedHistogram',
        'span.a-size-base.a-color-base'
      ];
      for (const sel of ratingSelectors) {
        const el = document.querySelector(sel);
        if (el) {
          const ratingText = el.textContent.trim();
          const match = ratingText.match(/(\d+(\.\d+)?)/);
          if (match) {
            rating = match[0];
            break;
          } else {
            rating = ratingText;
            break;
          }
        }
      }
      data.rating = rating;
  
      // --- Review Count ---
      let reviewCount = '';
      const reviewCountEl = document.querySelector('#acrCustomerReviewText');
      if (reviewCountEl) {
        reviewCount = reviewCountEl.textContent.replace(/[^0-9]/g, '');
      }
      data.reviewCount = reviewCount;
  
      // --- Best Sellers Rank (full string) ---
      let bestSellersRank = '';
      const rankLabels = ["Best Sellers Rank", "Best-sellers rank", "Bestsellers rank", "Amazon Best Sellers Rank"];
      const tableRows = document.querySelectorAll('#productDetails_detailBullets_sections1 tr, #productDetails table tr');
      for (const row of tableRows) {
        const header = row.querySelector('th, .a-color-secondary');
        if (header && rankLabels.some(label => header.textContent.includes(label))) {
          const valueCell = row.querySelector('td, .a-color-base');
          if (valueCell) {
            // Use innerText to capture all visible text (including line breaks)
            bestSellersRank = valueCell.innerText.trim();
            break;
          }
        }
      }
      // Fallback: try detail bullets by splitting text after label
      if (!bestSellersRank) {
        const detailItems = document.querySelectorAll('#detailBullets_feature_div li, .detail-bullet-list li');
        detailItems.forEach(item => {
          const text = item.textContent.trim();
          rankLabels.forEach(label => {
            if (text.includes(label)) {
              const parts = text.split(new RegExp(label + "[:\\-]?\\s*", "i"));
              if (parts.length > 1) {
                bestSellersRank = parts[1].trim();
              } else {
                bestSellersRank = text;
              }
            }
          });
        });
      }
      data.bestSellersRank = bestSellersRank;
  
      // --- Bullet Points (Features) ---
      let bulletPoints = [];
      const bulletEls = document.querySelectorAll('#feature-bullets .a-list-item, .a-unordered-list .a-list-item');
      bulletEls.forEach(li => {
        const text = li.textContent.trim();
        if (text && !text.toLowerCase().includes('warranty') && !bulletPoints.includes(text)) {
          bulletPoints.push(text);
        }
      });
      data.features = bulletPoints;
  
      // --- Brand ---
      let brand = '';
      const brandSelectors = ['#bylineInfo', '.contributorNameID', 'a#brand', '#brand'];
      for (const sel of brandSelectors) {
        const el = document.querySelector(sel);
        if (el && el.textContent.trim()) {
          brand = el.textContent
            .replace(/^Brand:\s*/i, '')
            .replace(/^Visit the\s*/i, '')
            .replace(/\s*Store$/i, '')
            .trim();
          if (brand) break;
        }
      }
      data.brand = brand;
  
      // --- Technical Details ---
      let technicalDetails = {};
      const techDetailSelectors = [
        '#productDetails_techSpec_section_1 tr',
        '#productDetails_techSpec_section_2 tr',
        '#technicalSpecifications_section_1 tr',
        '#detailBullets_feature_div li',
        '#productDetails_detailBullets_sections1 tr',
      ];
      techDetailSelectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        elements.forEach(element => {
          let label, value;
          if (element.tagName === 'TR') {
            const th = element.querySelector('th');
            const td = element.querySelector('td');
            if (th && td) {
              label = th.textContent.trim();
              value = td.textContent.trim();
            }
          } else {
            const text = element.textContent.trim();
            const colonIndex = text.indexOf(':');
            if (colonIndex !== -1) {
              label = text.substring(0, colonIndex).trim();
              value = text.substring(colonIndex + 1).trim();
            }
          }
          if (label && value) {
            technicalDetails[label] = value;
          }
        });
      });
      data.technicalDetails = technicalDetails;
  
      // --- Customer Reviews ---
      let customerReviews = [];
      const reviewEls = document.querySelectorAll('[data-hook="review"]');
      reviewEls.forEach(review => {
        const ratingEl = review.querySelector('[data-hook="review-star-rating"], [data-hook="rating-out-of-text"]');
        const titleEl = review.querySelector('[data-hook="review-title"]');
        const bodyEl = review.querySelector('[data-hook="review-body"]');
        const dateEl = review.querySelector('[data-hook="review-date"]');
        const verifiedEl = review.querySelector('[data-hook="avp-badge"]');
        if (bodyEl) {
          customerReviews.push({
            title: titleEl ? titleEl.textContent.trim() : '',
            rating: ratingEl ? ratingEl.textContent.replace(/[^0-9.]/g, '') : '',
            content: bodyEl.textContent.trim(),
            date: dateEl ? dateEl.textContent.trim() : '',
            verified: !!verifiedEl
          });
        }
      });
      data.customerReviews = customerReviews;
  
      // --- Customer Sayings ---
      let customerSayings = [];
      const sayingEls = document.querySelectorAll('.cr-lighthouse-term');
      sayingEls.forEach(el => {
        const topicEl = el.querySelector('.a-declarative');
        const percentageEl = el.querySelector('.cr-lighthouse-term-percentage');
        const topic = topicEl ? topicEl.textContent.trim() : '';
        const percentage = percentageEl ? percentageEl.textContent.trim() : '';
        if (topic && percentage) {
          customerSayings.push({ topic, percentage });
        }
      });
      data.customerSayings = customerSayings;
  
      // --- Date First Available ---
      let dateFirstAvailable = '';
      const dateLabels = ["Date First Available", "Release date", "Publication date"];
      const dateTableRows = document.querySelectorAll('#productDetails_detailBullets_sections1 tr, #productDetails table tr');
      for (const row of dateTableRows) {
        const header = row.querySelector('th, .a-color-secondary');
        if (header && dateLabels.some(label => header.textContent.includes(label))) {
          const valueCell = row.querySelector('td, .a-color-base');
          if (valueCell) {
            dateFirstAvailable = valueCell.textContent.trim();
            break;
          }
        }
      }
      if (!dateFirstAvailable) {
        const dateItems = document.querySelectorAll('#detailBullets_feature_div li, .detail-bullet-list li');
        dateItems.forEach(item => {
          const text = item.textContent;
          dateLabels.forEach(label => {
            if (text.includes(label)) {
              const parts = text.split(new RegExp(label + "[:\\-]?\\s*", "i"));
              if (parts.length > 1) {
                dateFirstAvailable = parts[1].trim();
              }
            }
          });
        });
      }
      data.dateFirstAvailable = dateFirstAvailable;
  
      // --- Image URLs ---
      let imageUrls = new Set();
      // Try various selectors to find the main product image
      const mainImageSelectors = [
        '#landingImage', 
        '#imgBlkFront', 
        '#main-image', 
        '.image.maintain-height',
        '.imgTagWrapper img',
        '#imageBlock img',
        '.a-dynamic-image'
      ];
      
      // First try to get high-resolution version
      for (const sel of mainImageSelectors) {
        const img = document.querySelector(sel);
        if (img) {
          // Try to get the highest resolution version
          let url = img.getAttribute('data-old-hires') || 
                   img.getAttribute('data-a-dynamic-image') || // This contains JSON with multiple sizes
                   img.src;
                   
          // Parse data-a-dynamic-image if available (it's a JSON string with URLs as keys)
          if (url && url.includes('{')) {
            try {
              const imgData = JSON.parse(url);
              // Get the URL with the highest resolution
              const urls = Object.keys(imgData);
              if (urls.length) {
                // Sort by resolution values and take the highest
                url = urls.sort((a, b) => imgData[b][0] * imgData[b][1] - imgData[a][0] * imgData[a][1])[0];
              }
            } catch (e) {
              console.error('Error parsing image data:', e);
            }
          }
          
          if (url) {
            // Clean up URL to get highest resolution version
            url = url.replace(/_S[0-9]+_/, '_SL1500_')
                    .replace(/_AC_[^.]+\./, '_AC_SL1500_.')
                    .replace(/\._.*_\./, '._SL1500_.');
            imageUrls.add(url);
          }
          
          data.image_url = url; // Set main image directly in data
          break;
        }
      }
      
      // Look for thumbnail images as well
      const thumbEls = document.querySelectorAll('#altImages .a-button-thumbnail img, #imageBlockThumbs img, .imageThumbnail img');
      thumbEls.forEach(img => {
        if (img && !img.src.includes('sprite') && !img.src.includes('gif') && !img.src.includes('play-icon')) {
          let url = img.getAttribute('src');
          if (url) {
            url = url.replace(/_S[0-9]+_/, '_SL1500_')
                     .replace(/_AC_[^.]+\./, '_AC_SL1500_.')
                     .replace(/\._SS\d+_/, '._SL1500_.');
            imageUrls.add(url);
          }
        }
      });
      
      data.imageUrls = Array.from(imageUrls);
  
      // --- Keywords ---
      const metaKeywords = document.querySelector('meta[name="keywords"]');
      data.keywords = metaKeywords
        ? metaKeywords.getAttribute('content').split(',').map(k => k.trim())
        : [];
  
      // --- Additional Meta ---
      data.url = window.location.href;
      data.timestamp = new Date().toISOString();
      // --- Category Hierarchy ---
      const categoryHierarchy = extractCategoryHierarchy();
      data.category_hierarchy = categoryHierarchy;
      data.main_category = categoryHierarchy.main_category;
      data.sub_categories = categoryHierarchy.sub_categories;
      data.sub_category = categoryHierarchy.sub_categories.slice(-1)[0];
      
      return data;
    } catch (error) {
      console.error('Error extracting product data:', error);
      return null;
    }
};

// Robust scraping with retries
const robustScrapeProduct = (retryCount = 0) => {
    try {
        const productData = extractProductData();
        if (productData && productData.title && productData.asin) {
            return productData;
        }
        
        if (retryCount < MAX_RETRIES) {
            // Use a promise to handle the asynchronous retry
            return new Promise((resolve) => {
                setTimeout(() => {
                    resolve(robustScrapeProduct(retryCount + 1));
                }, 1000);
            });
        }
    } catch (error) {
        console.error('Error in robust scraping:', error);
        if (retryCount < MAX_RETRIES) {
            // Use a promise to handle the asynchronous retry
            return new Promise((resolve) => {
                setTimeout(() => {
                    resolve(robustScrapeProduct(retryCount + 1));
                }, 1000);
            });
        }
    }
    return null;
};

// State tracking
let isScrapingProduct = false;
let lastScrapedAsin = '';
let lastScrapedUrl = '';
let lastScrapedTime = 0;
const MIN_SCRAPE_INTERVAL = 10000; // Minimum 10 seconds between scrapes

// Get product data without scraping
const getProductData = () => {
    try {
        // Check if we're on a product page
        if (!isProductPage()) {
            console.log("Not on a product page according to detection");
            return { success: false, error: 'Not a product page' };
        }
        
        console.log("On a product page, extracting data...");
        // Extract product data
        const productData = extractProductData();
        
        if (!productData) {
            console.log("Failed to extract product data");
            return { success: false, error: 'Failed to extract product data' };
        }
        
        // Validate the extracted data
        if (!productData.asin) {
            console.log("Missing ASIN in extracted data");
            // Still return partial data for debugging purposes
            return { 
                success: false, 
                error: 'Missing ASIN - required for analysis',
                product: productData 
            };
        }
        
        if (!productData.title) {
            console.log("Missing title in extracted data");
            // Not essential but helpful
            productData.title = document.title.replace(' - Amazon.com', '');
        }
        
        // Get image URL if missing
        if (!productData.image_url) {
            const mainImage = document.querySelector('#landingImage, #imgBlkFront, #main-image');
            if (mainImage) {
                productData.image_url = mainImage.src;
            }
        }
        
        console.log("Successfully extracted product data with ASIN:", productData.asin);
        return { success: true, product: productData };
    } catch (error) {
        console.error('Error getting product data:', error);
        return { success: false, error: error.message };
    }
};

// Listen for messages from popup or background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'CHECK_PRODUCT_PAGE') {
        // Check if current page is a product page
        sendResponse({ isProductPage: isProductPage() });
    } else if (message.type === 'SCRAPE_PRODUCT') {
        // Scrape product data
        scrapeProduct().then(result => {
            sendResponse(result);
        }).catch(error => {
            sendResponse({ success: false, error: error.message });
        });
        return true; // Indicate async response
    } else if (message.type === 'GET_PRODUCT_DATA') {
        // Get product data without scraping
        sendResponse(getProductData());
    }
});

// Main scraping function
const scrapeProduct = async () => {
    // Check if we're already scraping
    if (isScrapingProduct) {
        console.log('Already scraping, not starting another scrape');
        return false;
    }
    
    // Prevent scraping the same URL repeatedly in a short time
    const currentUrl = location.href;
    const now = Date.now();
    if (currentUrl === lastScrapedUrl && now - lastScrapedTime < MIN_SCRAPE_INTERVAL) {
        console.log(`Skipping scrape - same URL scraped ${(now - lastScrapedTime)/1000}s ago`);
        return false;
    }
    
    try {
        isScrapingProduct = true;
        lastScrapedUrl = currentUrl;
        lastScrapedTime = now;
        
        const productData = await robustScrapeProduct();
        if (productData) {
            // Check if this is the same ASIN we just scraped
            if (productData.asin === lastScrapedAsin) {
                console.log('Duplicate product ASIN detected, not sending again:', productData.asin);
                return false;
            }
            
            // Update last scraped ASIN
            lastScrapedAsin = productData.asin;
            
            // Send message to background script instead of popup
            chrome.runtime.sendMessage({
                type: 'PRODUCT_SCRAPED',
                product: productData
            });
            return true;
        }
        return false;
    } catch (error) {
        console.error('Error in scrapeProduct:', error);
        return false;
    } finally {
        isScrapingProduct = false;
    }
};

// Run scraping when the page loads if auto-scrape is enabled
if (isProductPage()) {
    // Automatically scrape after a delay to allow page to fully load
    // Use a random delay between 3-7 seconds to avoid all extensions sending requests at once
    const randomDelay = 3000 + Math.floor(Math.random() * 4000);
    setTimeout(() => {
        console.log(`Product page detected, automatically scraping after ${randomDelay}ms delay`);
        scrapeProduct();
    }, randomDelay);
}

// Detect URL changes for SPA navigation
let lastUrl = location.href;
new MutationObserver(() => {
    const url = location.href;
    if (url !== lastUrl) {
        lastUrl = url;
        const isProduct = isProductPage();
        
        // Notify background script about URL change
        chrome.runtime.sendMessage({
            type: 'URL_CHANGED',
            url: url,
            isProductPage: isProduct
        });
        
        // If it's a product page, automatically scrape after URL change
        // The background script will handle this instead of doing it here
        // to prevent duplicate scraping
    }
}).observe(document, { subtree: true, childList: true }); 