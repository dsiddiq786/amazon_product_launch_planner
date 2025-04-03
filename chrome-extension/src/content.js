// Check if current page is an Amazon product page
const isProductPage = () => {
    const path = window.location.pathname;
    return path.includes('/dp/') || path.includes('/gp/product/');
  };
  
  // Maximum number of retries for robust scraping
  const MAX_RETRIES = 3;
  
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
      const urlMatch = window.location.pathname.match(/\/([A-Z0-9]{10})(\/|$|\?)/);
      if (urlMatch && urlMatch[1]) {
        asin = urlMatch[1];
      } else {
        const asinEl = document.querySelector('[name="ASIN"], input[name="asin"], [data-asin]');
        asin = asinEl ? (asinEl.value || asinEl.getAttribute('data-asin')) : '';
      }
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
        '#detailBullets_feature_div li'
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
      const mainImageSelectors = ['#landingImage', '#imgBlkFront', '#main-image'];
      for (const sel of mainImageSelectors) {
        const img = document.querySelector(sel);
        if (img) {
          let url = img.getAttribute('data-old-hires') || img.getAttribute('src');
          if (url) {
            url = url.replace(/_S[0-9]+_/, '_SL1500_').replace(/_AC_[^.]+\./, '_AC_SL1500_.');
            imageUrls.add(url);
          }
          break;
        }
      }
      const thumbEls = document.querySelectorAll('#altImages .a-button-thumbnail img, #imageBlockThumbs img, .imageThumbnail img');
      thumbEls.forEach(img => {
        if (img && !img.src.includes('sprite') && !img.src.includes('gif') && !img.src.includes('play-icon')) {
          let url = img.getAttribute('src');
          if (url) {
            url = url.replace(/_S[0-9]+_/, '_SL1500_')
                     .replace(/_AC_[^.]+\./, '_AC_SL1500_.')
                     .replace(/\._SS\d+_/, '');
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
  
      return data;
    } catch (error) {
      console.error('Error extracting product data:', error);
      return null;
    }
  };
  
  // Robust scraping with retry mechanism if critical fields are missing
  const robustScrapeProduct = (retryCount = 0) => {
    const productData = extractProductData();
    // Check if critical fields (bestSellersRank and dateFirstAvailable) are non-empty
    if (
      productData &&
      (!productData.bestSellersRank || !productData.dateFirstAvailable) &&
      retryCount < MAX_RETRIES
    ) {
      console.warn(`Retry ${retryCount + 1}: Critical fields missing. Waiting and retrying...`);
      setTimeout(() => {
        robustScrapeProduct(retryCount + 1);
      }, 2000);
    } else if (productData) {
      chrome.runtime.sendMessage({
        type: 'PRODUCT_SCRAPED',
        product: productData
      });
    }
  };
  
  // Main scraping logic to run on product pages
  const scrapeProduct = () => {
    if (!isProductPage()) return;
    robustScrapeProduct();
  };
  
  // Run scraping when the page loads
  if (isProductPage()) {
    setTimeout(scrapeProduct, 2000);
  }
  
  // Listen for URL changes (for SPA navigation)
  let lastUrl = location.href;
  new MutationObserver(() => {
    const url = location.href;
    if (url !== lastUrl) {
      lastUrl = url;
      if (isProductPage()) {
        setTimeout(scrapeProduct, 2000);
      }
    }
  }).observe(document, { subtree: true, childList: true });
  



// WORKING CODE 
// // Check if current page is an Amazon product page
// const isProductPage = () => {
//     const path = window.location.pathname;
//     return path.includes('/dp/') || path.includes('/gp/product/');
//   };
  
//   // Main product data extraction function
//   const extractProductData = () => {
//     try {
//       const data = {};
  
//       // --- Title ---
//       const titleSelectors = ['#productTitle', '#title', '.product-title', 'h1.a-size-large'];
//       for (const sel of titleSelectors) {
//         const el = document.querySelector(sel);
//         if (el && el.textContent.trim()) {
//           data.title = el.textContent.trim();
//           break;
//         }
//       }
  
//       // --- Description ---
//       const descriptionSelectors = ['#productDescription', '#feature-bullets', '#aplus', '.a-expander-content'];
//       let description = '';
//       for (const sel of descriptionSelectors) {
//         const el = document.querySelector(sel);
//         if (el && el.textContent.trim()) {
//           description += el.textContent.trim() + ' ';
//         }
//       }
//       data.description = description.trim();
  
//       // --- ASIN ---
//       let asin = '';
//       const urlMatch = window.location.pathname.match(/\/([A-Z0-9]{10})(\/|$|\?)/);
//       if (urlMatch && urlMatch[1]) {
//         asin = urlMatch[1];
//       } else {
//         const asinEl = document.querySelector('[name="ASIN"], input[name="asin"], [data-asin]');
//         asin = asinEl ? (asinEl.value || asinEl.getAttribute('data-asin')) : '';
//       }
//       data.asin = asin;
  
//       // --- Price ---
//       const priceSelectors = [
//         '.a-price .a-offscreen',
//         '#priceblock_ourprice',
//         '#priceblock_dealprice',
//         '.a-price .a-price-whole',
//         '.priceToPay span.a-price-whole',
//         '.a-section .a-color-price'
//       ];
//       let price = '';
//       for (const sel of priceSelectors) {
//         const el = document.querySelector(sel);
//         if (el && el.textContent.trim()) {
//           price = el.textContent.trim();
//           break;
//         }
//       }
//       data.price = price;
  
//       // --- Rating ---
//       let rating = '';
//       const ratingSelectors = [
//         '#acrPopover',
//         '.a-icon-star',
//         '.reviewCountTextLinkedHistogram',
//         'span.a-size-base.a-color-base'
//       ];
//       for (const sel of ratingSelectors) {
//         const el = document.querySelector(sel);
//         if (el) {
//           const ratingText = el.textContent.trim();
//           const match = ratingText.match(/(\d+(\.\d+)?)/);
//           if (match) {
//             rating = match[0];
//             break;
//           } else {
//             rating = ratingText;
//             break;
//           }
//         }
//       }
//       data.rating = rating;
  
//       // --- Review Count ---
//       let reviewCount = '';
//       const reviewCountEl = document.querySelector('#acrCustomerReviewText');
//       if (reviewCountEl) {
//         reviewCount = reviewCountEl.textContent.replace(/[^0-9]/g, '');
//       }
//       data.reviewCount = reviewCount;
  
//       // --- Best Sellers Rank (capture complete string) ---
//       let bestSellersRank = '';
//       const rankLabels = ["Best Sellers Rank", "Best-sellers rank", "Bestsellers rank", "Amazon Best Sellers Rank"];
//       // Try table rows first
//       const tableRows = document.querySelectorAll('#productDetails_detailBullets_sections1 tr, #productDetails table tr');
//       for (const row of tableRows) {
//         const header = row.querySelector('th, .a-color-secondary');
//         if (header && rankLabels.some(label => header.textContent.includes(label))) {
//           const valueCell = row.querySelector('td, .a-color-base');
//           if (valueCell) {
//             bestSellersRank = valueCell.textContent.trim();
//             break;
//           }
//         }
//       }
//       // If not found, try detail bullets
//       if (!bestSellersRank) {
//         const detailItems = document.querySelectorAll('#detailBullets_feature_div li, .detail-bullet-list li');
//         for (const item of detailItems) {
//           const text = item.textContent.trim();
//           if (rankLabels.some(label => text.includes(label))) {
//             bestSellersRank = text;
//             break;
//           }
//         }
//       }
//       data.bestSellersRank = bestSellersRank;
  
//       // --- Bullet Points (Features) ---
//       let bulletPoints = [];
//       const bulletEls = document.querySelectorAll('#feature-bullets .a-list-item, .a-unordered-list .a-list-item');
//       bulletEls.forEach(li => {
//         const text = li.textContent.trim();
//         if (text && !text.toLowerCase().includes('warranty') && !bulletPoints.includes(text)) {
//           bulletPoints.push(text);
//         }
//       });
//       data.features = bulletPoints;  // Rename field to "features" per required data
  
//       // --- Brand ---
//       let brand = '';
//       const brandSelectors = ['#bylineInfo', '.contributorNameID', 'a#brand', '#brand'];
//       for (const sel of brandSelectors) {
//         const el = document.querySelector(sel);
//         if (el && el.textContent.trim()) {
//           brand = el.textContent
//             .replace(/^Brand:\s*/i, '')
//             .replace(/^Visit the\s*/i, '')
//             .replace(/\s*Store$/i, '')
//             .trim();
//           if (brand) break;
//         }
//       }
//       data.brand = brand;
  
//       // --- Technical Details ---
//       let technicalDetails = {};
//       const techDetailSelectors = [
//         '#productDetails_techSpec_section_1 tr',
//         '#productDetails_techSpec_section_2 tr',
//         '#technicalSpecifications_section_1 tr',
//         '#detailBullets_feature_div li'
//       ];
//       techDetailSelectors.forEach(selector => {
//         const elements = document.querySelectorAll(selector);
//         elements.forEach(element => {
//           let label, value;
//           if (element.tagName === 'TR') {
//             const th = element.querySelector('th');
//             const td = element.querySelector('td');
//             if (th && td) {
//               label = th.textContent.trim();
//               value = td.textContent.trim();
//             }
//           } else {
//             const text = element.textContent.trim();
//             const parts = text.split(':');
//             if (parts.length >= 2) {
//               label = parts.shift().trim();
//               value = parts.join(':').trim();
//             }
//           }
//           if (label && value) {
//             technicalDetails[label] = value;
//           }
//         });
//       });
//       data.technicalDetails = technicalDetails;
  
//       // --- Customer Reviews ---
//       let customerReviews = [];
//       const reviewEls = document.querySelectorAll('[data-hook="review"]');
//       reviewEls.forEach(review => {
//         const ratingEl = review.querySelector('[data-hook="review-star-rating"], [data-hook="rating-out-of-text"]');
//         const titleEl = review.querySelector('[data-hook="review-title"]');
//         const bodyEl = review.querySelector('[data-hook="review-body"]');
//         const dateEl = review.querySelector('[data-hook="review-date"]');
//         const verifiedEl = review.querySelector('[data-hook="avp-badge"]');
//         if (bodyEl) {
//           customerReviews.push({
//             title: titleEl ? titleEl.textContent.trim() : '',
//             rating: ratingEl ? ratingEl.textContent.replace(/[^0-9.]/g, '') : '',
//             content: bodyEl.textContent.trim(),
//             date: dateEl ? dateEl.textContent.trim() : '',
//             verified: !!verifiedEl
//           });
//         }
//       });
//       data.customerReviews = customerReviews;
  
//       // --- Customer Sayings ---
//       let customerSayings = [];
//       const sayingEls = document.querySelectorAll('.cr-lighthouse-term');
//       sayingEls.forEach(el => {
//         const topicEl = el.querySelector('.a-declarative');
//         const percentageEl = el.querySelector('.cr-lighthouse-term-percentage');
//         const topic = topicEl ? topicEl.textContent.trim() : '';
//         const percentage = percentageEl ? percentageEl.textContent.trim() : '';
//         if (topic && percentage) {
//           customerSayings.push({ topic, percentage });
//         }
//       });
//       data.customerSayings = customerSayings;
  
//       // --- Date First Available ---
//       let dateFirstAvailable = '';
//       const dateLabels = ["Date First Available", "Release date", "Publication date"];
//       // Try table rows first
//       const dateTableRows = document.querySelectorAll('#productDetails_detailBullets_sections1 tr, #productDetails table tr');
//       for (const row of dateTableRows) {
//         const header = row.querySelector('th, .a-color-secondary');
//         if (header && dateLabels.some(label => header.textContent.includes(label))) {
//           const valueCell = row.querySelector('td, .a-color-base');
//           if (valueCell) {
//             dateFirstAvailable = valueCell.textContent.trim();
//             break;
//           }
//         }
//       }
//       // If not found, try detail bullets
//       if (!dateFirstAvailable) {
//         const dateItems = document.querySelectorAll('#detailBullets_feature_div li, .detail-bullet-list li');
//         for (const item of dateItems) {
//           const text = item.textContent.trim();
//           if (dateLabels.some(label => text.includes(label))) {
//             dateFirstAvailable = text.replace(/(Date First Available|Release date|Publication date)\s*:\s*/i, '').trim();
//             break;
//           }
//         }
//       }
//       data.dateFirstAvailable = dateFirstAvailable;
  
//       // --- Image URLs ---
//       let imageUrls = new Set();
//       // Main image extraction
//       const mainImageSelectors = ['#landingImage', '#imgBlkFront', '#main-image'];
//       for (const sel of mainImageSelectors) {
//         const img = document.querySelector(sel);
//         if (img) {
//           let url = img.getAttribute('data-old-hires') || img.getAttribute('src');
//           if (url) {
//             url = url.replace(/_S[0-9]+_/, '_SL1500_').replace(/_AC_[^.]+\./, '_AC_SL1500_.');
//             imageUrls.add(url);
//           }
//           break;
//         }
//       }
//       // Additional images extraction
//       const thumbEls = document.querySelectorAll('#altImages .a-button-thumbnail img, #imageBlockThumbs img, .imageThumbnail img');
//       thumbEls.forEach(img => {
//         if (img && !img.src.includes('sprite') && !img.src.includes('gif') && !img.src.includes('play-icon')) {
//           let url = img.getAttribute('src');
//           if (url) {
//             url = url.replace(/_S[0-9]+_/, '_SL1500_')
//                      .replace(/_AC_[^.]+\./, '_AC_SL1500_.')
//                      .replace(/\._SS\d+_/, '');
//             imageUrls.add(url);
//           }
//         }
//       });
//       data.imageUrls = Array.from(imageUrls);
  
//       // --- Keywords (if available) ---
//       const metaKeywords = document.querySelector('meta[name="keywords"]');
//       data.keywords = metaKeywords
//         ? metaKeywords.getAttribute('content').split(',').map(k => k.trim())
//         : [];
  
//       // --- Additional Meta ---
//       data.url = window.location.href;
//       data.timestamp = new Date().toISOString();
  
//       return data;
//     } catch (error) {
//       console.error('Error extracting product data:', error);
//       return null;
//     }
//   };
  
//   // Main scraping logic to run on product pages
//   const scrapeProduct = () => {
//     if (!isProductPage()) return;
  
//     const productData = extractProductData();
//     if (productData) {
//       // Send the scraped product data to the extension's background or popup script
//       chrome.runtime.sendMessage({
//         type: 'PRODUCT_SCRAPED',
//         product: productData
//       });
//     }
//   };
  
//   // Run scraping when the page loads
//   if (isProductPage()) {
//     // Allow time for dynamic content to load
//     setTimeout(scrapeProduct, 2000);
//   }
  
//   // Listen for URL changes (for SPA navigation)
//   let lastUrl = location.href;
//   new MutationObserver(() => {
//     const url = location.href;
//     if (url !== lastUrl) {
//       lastUrl = url;
//       if (isProductPage()) {
//         setTimeout(scrapeProduct, 2000);
//       }
//     }
//   }).observe(document, { subtree: true, childList: true });
  

// // Product page detection
// const isProductPage = () => {
//     const path = window.location.pathname;
//     return path.includes('/dp/') || path.includes('/gp/product/');
// };

// // Product data extraction
// const extractProductData = () => {
//     try {
//         // Title
//         const titleElement = document.querySelector('#productTitle');
//         const title = titleElement ? titleElement.textContent.trim() : '';

//         // Description
//         let description = '';
//         const descriptionSelectors = [
//             '#productDescription p',
//             '#feature-bullets .a-list-item',
//             '#aplus',
//             '.a-expander-content'
//         ];
//         for (const selector of descriptionSelectors) {
//             const element = document.querySelector(selector);
//             if (element) {
//                 description += element.textContent.trim() + ' ';
//             }
//         }
//         description = description.trim();

//         // ASIN
//         let asin = '';
//         // Try URL first
//         const urlMatch = window.location.pathname.match(/\/([A-Z0-9]{10})(\/|$|\?)/);
//         if (urlMatch && urlMatch[1]) {
//             asin = urlMatch[1];
//         } else {
//             // Try page elements
//             const asinElement = document.querySelector('[name="ASIN"], #ASIN, [data-asin]');
//             asin = asinElement ? (asinElement.value || asinElement.getAttribute('data-asin')) : '';
//         }

//         // Price
//         const priceSelectors = [
//             '.a-price .a-offscreen',
//             '#priceblock_ourprice',
//             '#priceblock_dealprice',
//             '.a-price .a-price-whole',
//             '.priceToPay span.a-price-whole',
//             '.a-section .a-color-price'
//         ];
//         let price = '';
//         for (const selector of priceSelectors) {
//             const element = document.querySelector(selector);
//             if (element) {
//                 price = element.textContent.trim();
//                 break;
//             }
//         }

//         // Ratings and Review Count
//         const ratingsElement = document.querySelector('#acrPopover');
//         const ratings = ratingsElement ? ratingsElement.getAttribute('title').replace(' out of 5 stars', '') : '';
//         const reviewCountElement = document.querySelector('#acrCustomerReviewText');
//         const reviewCount = reviewCountElement ? reviewCountElement.textContent.replace(/[^0-9]/g, '') : '';

//         // Best Sellers Rank
//         let bestSellersRank = '';
//         const rankSelectors = [
//             '#productDetails_detailBullets_sections1 tr:has(th:contains("Best Sellers Rank"))',
//             '#detailBullets_feature_div li:has(span:contains("Best Sellers Rank"))',
//             '#SalesRank',
//             '.prodDetSectionEntry:contains("Best Sellers Rank")'
//         ];
//         for (const selector of rankSelectors) {
//             const element = document.querySelector(selector);
//             if (element) {
//                 bestSellersRank = element.textContent
//                     .replace(/Best Sellers Rank:|Amazon Best Sellers Rank:|#/g, '')
//                     .replace(/\s+/g, ' ')
//                     .trim();
//                 break;
//             }
//         }

//         // Bullet Points
//         const bulletPoints = [];
//         const featuresList = document.querySelectorAll('#feature-bullets .a-list-item');
//         featuresList.forEach(li => {
//             const text = li.textContent.trim();
//             if (text && !text.toLowerCase().includes('warranty')) {
//                 bulletPoints.push(text);
//             }
//         });

//         // Brand
//         const brandSelectors = [
//             '#bylineInfo',
//             '.po-brand .a-span9',
//             '.contributorNameID',
//             'a#brand',
//             '#brand'
//         ];
//         let brand = '';
//         for (const selector of brandSelectors) {
//             const element = document.querySelector(selector);
//             if (element) {
//                 brand = element.textContent.trim()
//                     .replace(/Brand:|Visit the|Store/gi, '')
//                     .trim();
//                 break;
//             }
//         }

//         // Technical Details
//         const technicalDetails = {};
//         const techDetailSelectors = [
//             '#productDetails_techSpec_section_1 tr',
//             '#productDetails_techSpec_section_2 tr',
//             '#technicalSpecifications_section_1 tr',
//             '#detailBullets_feature_div li'
//         ];
//         for (const selector of techDetailSelectors) {
//             const elements = document.querySelectorAll(selector);
//             elements.forEach(element => {
//                 let label, value;
//                 if (element.tagName === 'TR') {
//                     label = element.querySelector('th')?.textContent.trim();
//                     value = element.querySelector('td')?.textContent.trim();
//                 } else {
//                     const text = element.textContent.trim();
//                     const parts = text.split(':');
//                     if (parts.length === 2) {
//                         [label, value] = parts.map(p => p.trim());
//                     }
//                 }
//                 if (label && value) {
//                     technicalDetails[label] = value;
//                 }
//             });
//         }

//         // Customer Reviews
//         const reviews = [];
//         const reviewElements = document.querySelectorAll('[data-hook="review"]');
//         reviewElements.forEach(review => {
//             const ratingElement = review.querySelector('[data-hook="review-star-rating"], [data-hook="rating-out-of-text"]');
//             const titleElement = review.querySelector('[data-hook="review-title"]');
//             const bodyElement = review.querySelector('[data-hook="review-body"]');
//             const dateElement = review.querySelector('[data-hook="review-date"]');
//             const verifiedElement = review.querySelector('[data-hook="avp-badge"]');

//             if (bodyElement) {
//                 reviews.push({
//                     title: titleElement ? titleElement.textContent.trim() : '',
//                     rating: ratingElement ? ratingElement.textContent.replace(/[^0-9.]/g, '') : '',
//                     content: bodyElement.textContent.trim(),
//                     date: dateElement ? dateElement.textContent.trim() : '',
//                     verified: verifiedElement ? true : false
//                 });
//             }
//         });

//         // Date First Available
//         let dateFirstAvailable = '';
//         const dateSelectors = [
//             '#productDetails_detailBullets_sections1 tr:has(th:contains("Date First Available"))',
//             '#detailBullets_feature_div li:has(span:contains("Date First Available"))',
//             '.prodDetSectionEntry:contains("Date First Available")'
//         ];
//         for (const selector of dateSelectors) {
//             const element = document.querySelector(selector);
//             if (element) {
//                 dateFirstAvailable = element.textContent
//                     .replace(/Date First Available:?/g, '')
//                     .trim();
//                 break;
//             }
//         }

//         // Image URLs
//         const imageUrls = new Set();
//         // Main image
//         const mainImageSelectors = ['#landingImage', '#imgBlkFront', '#main-image'];
//         for (const selector of mainImageSelectors) {
//             const img = document.querySelector(selector);
//             if (img) {
//                 let url = img.getAttribute('data-old-hires') || img.getAttribute('src');
//                 if (url) {
//                     url = url.replace(/_S[0-9]+_/, '_SL1500_').replace(/_AC_[^.]+\./, '_AC_SL1500_.');
//                     imageUrls.add(url);
//                 }
//                 break;
//             }
//         }
//         // Additional images
//         const thumbnails = document.querySelectorAll('#altImages .a-button-thumbnail img, #imageBlockThumbs img, .imageThumbnail img');
//         thumbnails.forEach(img => {
//             if (img && !img.src.includes('sprite') && !img.src.includes('gif') && !img.src.includes('play-icon')) {
//                 let url = img.getAttribute('src');
//                 if (url) {
//                     url = url.replace(/_S[0-9]+_/, '_SL1500_')
//                            .replace(/_AC_[^.]+\./, '_AC_SL1500_.')
//                            .replace(/\._SS\d+_/, '');
//                     imageUrls.add(url);
//                 }
//             }
//         });

//         return {
//             title,
//             description,
//             asin,
//             price,
//             rating: ratings,
//             review_count: reviewCount,
//             bestSellersRank,
//             bulletPoints,
//             brand,
//             technicalDetails,
//             customerReviews: reviews,
//             imageUrls: Array.from(imageUrls),
//             dateFirstAvailable,
//             url: window.location.href,
//             timestamp: new Date().toISOString()
//         };
//     } catch (error) {
//         console.error('Error extracting product data:', error);
//         return null;
//     }
// };

// // Main scraping logic
// const scrapeProduct = () => {
//     if (!isProductPage()) return;

//     const productData = extractProductData();
//     if (productData) {
//         chrome.runtime.sendMessage({
//             type: 'PRODUCT_SCRAPED',
//             product: productData
//         });
//     }
// };

// // Run scraping when page loads
// if (isProductPage()) {
//     // Wait for dynamic content to load
//     setTimeout(scrapeProduct, 2000);
// }

// // Listen for URL changes (for SPA navigation)
// let lastUrl = location.href;
// new MutationObserver(() => {
//     const url = location.href;
//     if (url !== lastUrl) {
//         lastUrl = url;
//         if (isProductPage()) {
//             setTimeout(scrapeProduct, 2000);
//         }
//     }
// }).observe(document, { subtree: true, childList: true }); 