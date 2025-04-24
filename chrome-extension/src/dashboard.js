// API configuration
const API_BASE_URL = 'http://localhost:8000/api/v1';
const USER_ANALYZED_PRODUCTS_ENDPOINT = '/products/user_analyzed_products';
const PRODUCT_REPORT_ENDPOINT = '/products/report/';

// DOM Elements
const userAvatar = document.getElementById('user-avatar');
const userName = document.getElementById('user-name');
const userEmail = document.getElementById('user-email');
const totalAnalyzed = document.getElementById('total-analyzed');
const avgPrice = document.getElementById('avg-price');
const avgRating = document.getElementById('avg-rating');
const productsContainer = document.getElementById('products-container');
const pagination = document.getElementById('pagination');
const searchInput = document.getElementById('search-input');
const reportModal = document.getElementById('report-modal');
const reportTitle = document.getElementById('report-title');
const reportContent = document.getElementById('report-content');
const closeModal = document.getElementById('close-modal');

// State
let userToken = null;
let userData = null;
let products = [];
let filteredProducts = [];
let currentPage = 1;
const itemsPerPage = 12;
let isLoading = true;

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Dashboard loaded');
    
    // Load auth data
    await loadAuthData();
    
    // Load products
    if (userToken) {
        await loadAnalyzedProducts();
    } else {
        // Redirect to extension popup if not logged in
        window.close();
    }
    
    // Set up event listeners
    setupEventListeners();
});

// Load authentication data from storage
const loadAuthData = async () => {
    try {
        const storage = await chrome.storage.local.get(['token', 'user']);
        
        if (storage.token && storage.user) {
            userToken = storage.token;
            userData = storage.user;
            
            // Update UI with user info
            userEmail.textContent = userData.email || 'No email';
            userName.textContent = userData.email.split('@')[0] || 'User';
            userAvatar.src = userData.avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(userData.email)}&background=random`;
            
            return true;
        } else {
            console.log('No auth data found');
            return false;
        }
    } catch (error) {
        console.error('Error loading auth data:', error);
        return false;
    }
};

// Load all analyzed products for the current user
const loadAnalyzedProducts = async () => {
    try {
        showLoading(true);
        
        // First try to fetch from API
        if (userToken) {
            try {
                const response = await fetch(`${API_BASE_URL}${USER_ANALYZED_PRODUCTS_ENDPOINT}`, {
                    headers: {
                        'Authorization': `Bearer ${userToken}`
                    }
                });
                
                if (response.ok) {
                    const data = await response.json();
                    console.log('Fetched analyzed products from API:', data);
                    
                    // If API returned products successfully, use them
                    if (data && Array.isArray(data.products) && data.products.length > 0) {
                        products = data.products
                            .filter(p => p && p.asin) // Ensure valid products
                            .sort((a, b) => {
                                const dateA = new Date(a.analyzed_at || a.created_at || 0);
                                const dateB = new Date(b.analyzed_at || b.created_at || 0);
                                return dateB - dateA; // Sort newest first
                            });
                        
                        // Update local storage with these products to keep in sync
                        const productsObj = {};
                        products.forEach(product => {
                            if (product.asin) {
                                productsObj[product.asin] = {
                                    ...product,
                                    is_analyzed: true
                                };
                            }
                        });
                        
                        // Save to storage but don't await it to not block rendering
                        chrome.storage.local.set({ analyzedProducts: productsObj });
                        
                        filteredProducts = [...products];
                        
                        // Update stats
                        updateStats(products);
                        
                        // Render products
                        renderProducts();
                        
                        showLoading(false);
                        return;
                    }
                } else {
                    console.error('API error when fetching analyzed products:', response.status);
                }
            } catch (apiError) {
                console.error('Failed to fetch from API, falling back to local storage:', apiError);
            }
        }
        
        // Fallback to local storage if API fails or returns no products
        console.log('Falling back to local storage for analyzed products');
        const storage = await chrome.storage.local.get(['analyzedProducts', 'userStats']);
        const analyzedProductsObj = storage.analyzedProducts || {};
        
        // Convert object to array and sort by date
        products = Object.values(analyzedProductsObj)
            .filter(p => p && p.asin) // Ensure valid products
            .sort((a, b) => {
                const dateA = new Date(a.analyzed_at || a.created_at || 0);
                const dateB = new Date(b.analyzed_at || b.created_at || 0);
                return dateB - dateA; // Sort newest first
            });
        
        filteredProducts = [...products];
        
        // Update stats
        updateStats(products);
        
        // Render products
        renderProducts();
        
        showLoading(false);
    } catch (error) {
        console.error('Error loading analyzed products:', error);
        showError('Failed to load products. Please try again later.');
        showLoading(false);
    }
};

// Update dashboard stats based on products
const updateStats = (productsData) => {
    // Total analyzed products
    totalAnalyzed.textContent = productsData.length;
    
    // Average price calculation
    if (productsData.length > 0) {
        const prices = productsData
            .map(p => extractNumericPrice(p.price))
            .filter(price => !isNaN(price) && price > 0);
            
        if (prices.length > 0) {
            const avgPriceValue = prices.reduce((sum, price) => sum + price, 0) / prices.length;
            avgPrice.textContent = `$${avgPriceValue.toFixed(2)}`;
        } else {
            avgPrice.textContent = 'N/A';
        }
        
        // Average rating calculation
        const ratings = productsData
            .map(p => parseFloat(p.rating))
            .filter(rating => !isNaN(rating) && rating > 0);
            
        if (ratings.length > 0) {
            const avgRatingValue = ratings.reduce((sum, rating) => sum + rating, 0) / ratings.length;
            avgRating.textContent = avgRatingValue.toFixed(1);
        } else {
            avgRating.textContent = 'N/A';
        }
    } else {
        avgPrice.textContent = 'N/A';
        avgRating.textContent = 'N/A';
    }
    
    // Update localStorage stats
    updateLocalStats(productsData);
};

// Update local storage stats
const updateLocalStats = async (productsData) => {
    try {
        const stats = {
            total_analyzed: productsData.length,
            last_analyzed_at: productsData.length > 0 ? 
                productsData[0].analyzed_at : null
        };
        
        await chrome.storage.local.set({ userStats: stats });
        console.log('Updated stats in local storage:', stats);
    } catch (error) {
        console.error('Error updating stats in storage:', error);
    }
};

// Extract numeric price from price string
const extractNumericPrice = (priceStr) => {
    if (!priceStr) return NaN;
    
    // Remove currency symbols and commas, then parse
    const numericStr = priceStr.replace(/[^0-9.]/g, '');
    return parseFloat(numericStr);
};

// Render products with pagination
const renderProducts = () => {
    // Calculate pagination
    const totalPages = Math.ceil(filteredProducts.length / itemsPerPage);
    const start = (currentPage - 1) * itemsPerPage;
    const end = start + itemsPerPage;
    const currentProducts = filteredProducts.slice(start, end);
    
    // Clear container
    productsContainer.innerHTML = '';
    
    // Show message if no products
    if (filteredProducts.length === 0) {
        productsContainer.innerHTML = `
            <div class="no-products">
                <i class="fas fa-box-open"></i>
                <h3>No Products Found</h3>
                <p>You haven't analyzed any products yet or no results match your search.</p>
            </div>
        `;
        pagination.innerHTML = '';
        return;
    }
    
    // Create grid for products
    const productsGrid = document.createElement('div');
    productsGrid.className = 'products-grid';
    
    // Add product cards
    currentProducts.forEach(product => {
        const card = createProductCard(product);
        productsGrid.appendChild(card);
    });
    
    productsContainer.appendChild(productsGrid);
    
    // Render pagination
    renderPagination(totalPages);
};

// Create a product card element
const createProductCard = (product) => {
    const card = document.createElement('div');
    card.className = 'product-card';
    
    // Format date - check multiple possible date fields
    const formattedDate = new Date(
        product.analyzed_at || product.created_at || product.updated_at || Date.now()
    ).toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
    
    // Safe access to nested properties
    const getImageUrl = () => {
        if (product.image_url) return product.image_url;
        if (product.images && product.images.length > 0) return product.images[0];
        if (product.imageUrls && product.imageUrls.length > 0) return product.imageUrls[0];
        return 'https://via.placeholder.com/300?text=No+Image';
    };
    
    // Use appropriate identifiers
    const productId = product.id || '';
    const productAsin = product.asin || '';
    
    card.innerHTML = `
        <div class="product-image">
            <img src="${getImageUrl()}" alt="${product.title || 'Product'}">
            <div class="product-badge">Analyzed</div>
        </div>
        <div class="product-details">
            <h3 class="product-title">${product.title || 'No Title'}</h3>
            <div class="product-meta">
                <span class="product-price">${product.price || 'No Price'}</span>
                <span>${product.rating ? `★ ${product.rating}` : 'No Rating'}</span>
            </div>
            <div class="product-asin">ASIN: ${productAsin || 'N/A'}</div>
            <div class="product-asin">Analyzed: ${formattedDate}</div>
            <div class="product-actions">
                <button class="btn btn-accent show-report-btn" data-id="${productId}" data-asin="${productAsin}">Show Report</button>
            </div>
        </div>
    `;
    
    // Add event listener to report button
    const reportBtn = card.querySelector('.show-report-btn');
    reportBtn.addEventListener('click', () => showProductReport(product));
    
    return card;
};

// Render pagination controls
const renderPagination = (totalPages) => {
    pagination.innerHTML = '';
    
    if (totalPages <= 1) {
        return;
    }
    
    // Previous button
    const prevBtn = document.createElement('button');
    prevBtn.textContent = '←';
    prevBtn.disabled = currentPage === 1;
    prevBtn.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            renderProducts();
        }
    });
    pagination.appendChild(prevBtn);
    
    // Page buttons
    let startPage = Math.max(1, currentPage - 2);
    let endPage = Math.min(totalPages, startPage + 4);
    
    if (endPage - startPage < 4) {
        startPage = Math.max(1, endPage - 4);
    }
    
    for (let i = startPage; i <= endPage; i++) {
        const pageBtn = document.createElement('button');
        pageBtn.textContent = i;
        pageBtn.classList.toggle('active', i === currentPage);
        pageBtn.addEventListener('click', () => {
            currentPage = i;
            renderProducts();
        });
        pagination.appendChild(pageBtn);
    }
    
    // Next button
    const nextBtn = document.createElement('button');
    nextBtn.textContent = '→';
    nextBtn.disabled = currentPage === totalPages;
    nextBtn.addEventListener('click', () => {
        if (currentPage < totalPages) {
            currentPage++;
            renderProducts();
        }
    });
    pagination.appendChild(nextBtn);
};

// Show product report in modal
const showProductReport = async (product) => {
    try {
        // Set title and show modal
        reportTitle.textContent = product.title || 'Product Analysis Report';
        reportModal.style.display = 'flex';
        
        // Show loading state
        reportContent.innerHTML = `
            <div class="loading">
                <i class="fas fa-spinner"></i>
            </div>
        `;
        
        // Determine the product identifier
        // Use ID for API-source products, ASIN for local storage as fallback
        const productIdentifier = product.id || product.asin;
        
        if (!productIdentifier) {
            throw new Error('No product ID or ASIN available');
        }
        
        // Fetch report
        const response = await fetch(`${API_BASE_URL}${PRODUCT_REPORT_ENDPOINT}${productIdentifier}`, {
            headers: {
                'Authorization': `Bearer ${userToken}`
            }
        });
        
        if (!response.ok) {
            throw new Error(`Failed to load report: ${response.status}`);
        }
        
        const report = await response.json();
        
        // Handle case where report might be in a nested format
        const reportData = report.report || report;
        
        // Check if we have analysis data directly in the product
        // This is for products that were loaded from local storage
        if (!reportData.analysis && product.analysis) {
            reportData.analysis = product.analysis;
        }
        
        // Render report
        renderReport(reportData, product);
    } catch (error) {
        console.error('Error showing product report:', error);
        reportContent.innerHTML = `
            <div class="report-section">
                <h4>Error</h4>
                <p>Failed to load the product report. Please try again later.</p>
                <p class="error-details">${error.message}</p>
            </div>
        `;
    }
};

// Render report content in modal
const renderReport = (report, product) => {
    reportContent.innerHTML = '';
    
    // Helper function to get image URL from various formats
    const getImageUrl = () => {
        if (product.image_url) return product.image_url;
        if (product.images && product.images.length > 0) return product.images[0];
        if (product.imageUrls && product.imageUrls.length > 0) return product.imageUrls[0];
        return 'https://via.placeholder.com/150?text=No+Image';
    };
    
    // Product Overview Section
    const overviewSection = document.createElement('div');
    overviewSection.className = 'report-section';
    overviewSection.innerHTML = `
        <h4>Product Overview</h4>
        <div style="display: flex; gap: 16px; align-items: flex-start;">
            <img src="${getImageUrl()}" 
                 alt="${product.title || 'Product'}" 
                 style="width: 100px; height: 100px; object-fit: contain; border: 1px solid #eee; border-radius: 4px;">
            <div>
                <p><strong>Title:</strong> ${product.title || 'N/A'}</p>
                <p><strong>ASIN:</strong> ${product.asin || 'N/A'}</p>
                <p><strong>Price:</strong> ${product.price || 'N/A'}</p>
                <p><strong>Rating:</strong> ${product.rating ? `${product.rating} / 5` : 'N/A'}</p>
                <p><strong>Amazon Link:</strong> <a href="https://www.amazon.com/dp/${product.asin}" target="_blank">View on Amazon</a></p>
            </div>
        </div>
    `;
    reportContent.appendChild(overviewSection);
    
    // Analysis data can be in different locations based on source
    const analysis = report.analysis || product.analysis || {};
    
    // If we have numerical metrics, show them
    if (analysis.estimated_sales || analysis.competition_score || 
        analysis.market_saturation || analysis.opportunity_score) {
        
        const metricsSection = document.createElement('div');
        metricsSection.className = 'report-section';
        metricsSection.innerHTML = `
            <h4>Key Metrics</h4>
            <div class="metrics-grid">
                ${analysis.estimated_sales ? 
                  `<div class="metric-card">
                      <div class="metric-value">${analysis.estimated_sales.toLocaleString()}</div>
                      <div class="metric-label">Est. Monthly Sales</div>
                  </div>` : ''}
                  
                ${analysis.competition_score ? 
                  `<div class="metric-card">
                      <div class="metric-value">${analysis.competition_score}/100</div>
                      <div class="metric-label">Competition Score</div>
                  </div>` : ''}
                  
                ${analysis.market_saturation ? 
                  `<div class="metric-card">
                      <div class="metric-value">${analysis.market_saturation}/100</div>
                      <div class="metric-label">Market Saturation</div>
                  </div>` : ''}
                  
                ${analysis.opportunity_score ? 
                  `<div class="metric-card">
                      <div class="metric-value">${analysis.opportunity_score}/100</div>
                      <div class="metric-label">Opportunity Score</div>
                  </div>` : ''}
                  
                ${analysis.pricing_recommendation ? 
                  `<div class="metric-card">
                      <div class="metric-value">$${parseFloat(analysis.pricing_recommendation).toFixed(2)}</div>
                      <div class="metric-label">Price Recommendation</div>
                  </div>` : ''}
            </div>
        `;
        reportContent.appendChild(metricsSection);
    }
    
    // Show analysis sections from the report
    if (analysis) {
        // Market Analysis
        if (analysis.market_analysis) {
            const marketSection = document.createElement('div');
            marketSection.className = 'report-section';
            marketSection.innerHTML = `
                <h4>Market Analysis</h4>
                <p>${analysis.market_analysis}</p>
            `;
            reportContent.appendChild(marketSection);
        }
        
        // Competition Analysis
        if (analysis.competition_analysis) {
            const competitionSection = document.createElement('div');
            competitionSection.className = 'report-section';
            competitionSection.innerHTML = `
                <h4>Competition Analysis</h4>
                <p>${analysis.competition_analysis}</p>
            `;
            reportContent.appendChild(competitionSection);
        }
        
        // Customer Analysis
        if (analysis.customer_analysis) {
            const customerSection = document.createElement('div');
            customerSection.className = 'report-section';
            customerSection.innerHTML = `
                <h4>Customer Analysis</h4>
                <p>${analysis.customer_analysis}</p>
            `;
            reportContent.appendChild(customerSection);
        }
        
        // Recommendations
        if (analysis.recommendations) {
            const recommendationsSection = document.createElement('div');
            recommendationsSection.className = 'report-section';
            recommendationsSection.innerHTML = `
                <h4>Recommendations</h4>
                <p>${analysis.recommendations}</p>
            `;
            reportContent.appendChild(recommendationsSection);
        }
        
        // Additional sections from API response
        for (const [key, value] of Object.entries(analysis)) {
            // Skip already rendered sections
            if (['market_analysis', 'competition_analysis', 'customer_analysis', 
                  'recommendations', 'estimated_sales', 'competition_score', 
                  'market_saturation', 'opportunity_score', 'pricing_recommendation', 
                  'analyzed_at'].includes(key)) {
                continue;
            }
            
            // Render additional sections
            if (typeof value === 'string' && value.trim()) {
                const section = document.createElement('div');
                section.className = 'report-section';
                section.innerHTML = `
                    <h4>${formatSectionTitle(key)}</h4>
                    <p>${value}</p>
                `;
                reportContent.appendChild(section);
            }
        }
    } else {
        // No analysis available
        const noAnalysisSection = document.createElement('div');
        noAnalysisSection.className = 'report-section';
        noAnalysisSection.innerHTML = `
            <h4>No Analysis Available</h4>
            <p>This product has been analyzed, but detailed analysis results are not available.</p>
        `;
        reportContent.appendChild(noAnalysisSection);
    }
};

// Format section title from snake_case to Title Case
const formatSectionTitle = (key) => {
    return key
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
};

// Show/hide loading indicator
const showLoading = (isLoading) => {
    if (isLoading) {
        productsContainer.innerHTML = `
            <div class="loading">
                <i class="fas fa-spinner"></i>
            </div>
        `;
    }
};

// Show error message
const showError = (message) => {
    productsContainer.innerHTML = `
        <div class="no-products">
            <i class="fas fa-exclamation-circle"></i>
            <h3>Error</h3>
            <p>${message}</p>
        </div>
    `;
};

// Set up event listeners
const setupEventListeners = () => {
    // Close modal
    closeModal.addEventListener('click', () => {
        reportModal.style.display = 'none';
    });
    
    // Click outside modal to close
    reportModal.addEventListener('click', (e) => {
        if (e.target === reportModal) {
            reportModal.style.display = 'none';
        }
    });
    
    // Search input
    searchInput.addEventListener('input', () => {
        const searchTerm = searchInput.value.toLowerCase().trim();
        
        if (searchTerm === '') {
            filteredProducts = [...products];
        } else {
            filteredProducts = products.filter(product => 
                (product.title && product.title.toLowerCase().includes(searchTerm)) ||
                (product.asin && product.asin.toLowerCase().includes(searchTerm)) ||
                (product.price && product.price.toLowerCase().includes(searchTerm))
            );
        }
        
        currentPage = 1;
        renderProducts();
    });
}; 