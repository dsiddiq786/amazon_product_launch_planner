// Configuration
const API_BASE_URL = "http://localhost:8000/api/v1";

// Create Extension Storage
const ExtensionStorage = {
    async get() {
        return new Promise((resolve) => {
            chrome.storage.local.get(null, (result) => {
                resolve(result);
            });
        });
    },
    
    async set(data) {
        return new Promise((resolve) => {
            chrome.storage.local.set(data, () => {
                resolve();
            });
        });
    },
    
    async getScrapedProducts() {
        const storage = await this.get();
        return storage.scrapedProducts || [];
    },
    
    async addScrapedProduct(product) {
        try {
            const products = await this.getScrapedProducts();
            const exists = products.some(p => p.asin === product.asin);
            
            if (!exists) {
                const newProduct = {
                    ...product,
                    saved: false,
                    timestamp: new Date().toISOString(),
                    id: `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
                };
                products.push(newProduct);
                await this.set({ scrapedProducts: products });
                return products;
            }
            return products;
        } catch (error) {
            console.error('Error adding scraped product:', error);
            throw error;
        }
    },
    
    async removeScrapedProduct(asin) {
        try {
            const products = await this.getScrapedProducts();
            const updatedProducts = products.filter(p => p.asin !== asin);
            await this.set({ scrapedProducts: updatedProducts });
            return updatedProducts;
        } catch (error) {
            console.error('Error removing scraped product:', error);
            throw error;
        }
    },
    
    async clearScrapedProducts() {
        try {
            await this.set({ scrapedProducts: [] });
        } catch (error) {
            console.error('Error clearing scraped products:', error);
            throw error;
        }
    },

    async updateScrapedProduct(asin, updates) {
        try {
            const products = await this.getScrapedProducts();
            const index = products.findIndex(p => p.asin === asin);
            if (index !== -1) {
                products[index] = { ...products[index], ...updates };
                await this.set({ scrapedProducts: products });
                return products;
            }
            return products;
        } catch (error) {
            console.error('Error updating scraped product:', error);
            throw error;
        }
    }
};

// State management
let currentState = {
    token: null,
    user: null,
    currentProject: null,
    scrapedProducts: [],
    savedProducts: []
};

// DOM Elements
const authSection = document.getElementById('authSection');
const mainSection = document.getElementById('mainSection');
const loginForm = document.getElementById('loginForm');
const loginMessage = document.getElementById('loginMessage');
const userAvatar = document.getElementById('userAvatar');
const userEmail = document.getElementById('userEmail');
const logoutBtn = document.getElementById('logoutBtn');
const projectSelect = document.getElementById('projectSelect');
const createProjectBtn = document.getElementById('createProjectBtn');
const newProjectForm = document.getElementById('newProjectForm');
const saveProjectBtn = document.getElementById('saveProjectBtn');
const cancelProjectBtn = document.getElementById('cancelProjectBtn');
const projectSection = document.getElementById('projectSection');
const productSection = document.getElementById('productSection');
const notProductPage = document.getElementById('notProductPage');
const productPage = document.getElementById('productPage');
const scrapeBtn = document.getElementById('scrapeBtn');
const statusMessage = document.getElementById('statusMessage');
const productInfo = document.getElementById('productInfo');
const saveProductBtn = document.getElementById('saveProductBtn');
const scrapedProductsList = document.getElementById('scrapedProductsList');
const clearScrapedDataBtn = document.getElementById('clearScrapedDataBtn');

// Add a default image constant at the top
const DEFAULT_IMAGE = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQiIGhlaWdodD0iNjQiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjY0IiBoZWlnaHQ9IjY0IiBmaWxsPSIjZWVlIi8+PHRleHQgeD0iMjAiIHk9IjM2IiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTIiIGZpbGw9IiNhYWEiPk5vIEltZzwvdGV4dD48L3N2Zz4=';

// Initialize popup
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Load auth state
        const storage = await ExtensionStorage.get();
        if (storage.authToken && storage.userData) {
            currentState.token = storage.authToken;
            currentState.user = storage.userData;
            currentState.currentProject = storage.currentProject;
            
            // Load scraped products from storage
            const scrapedProducts = await chrome.storage.local.get(['scrapedProducts']);
            currentState.scrapedProducts = scrapedProducts.scrapedProducts || [];
            console.log('Loaded scraped products:', currentState.scrapedProducts);
            
            showMainSection(storage.userData);
            await loadProjects();
            
            if (currentState.currentProject) {
                projectSelect.value = currentState.currentProject;
                productSection.classList.remove('hidden');
                // Force update product list
                updateProductsList();
            }
        } else {
            showAuthSection();
        }
    } catch (error) {
        console.error('Initialization error:', error);
        showAuthSection();
    }
});

// API Functions
async function makeApiRequest(endpoint, options = {}) {
    const headers = {
        'Content-Type': 'application/json',
        ...(currentState.token && { 'Authorization': `Bearer ${currentState.token}` }),
        ...options.headers
    };

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'API request failed');
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Authentication Functions
async function login(email, password) {
    try {
        const data = await makeApiRequest('/auth/login/json', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });

        currentState.token = data.access_token;
        currentState.user = {
            email: email,
            id: data.user_id
        };

        await chrome.storage.local.set({
            authToken: data.access_token,
            userData: currentState.user
        });

        return true;
    } catch (error) {
        throw new Error('Login failed: ' + error.message);
    }
}

// Project Management Functions
async function loadProjects() {
    try {
        const data = await makeApiRequest('/projects');
        currentState.projects = data.projects || [];
        updateProjectSelect(currentState.projects);
    } catch (error) {
        showMessage(statusMessage, 'Failed to load projects: ' + error.message, 'error');
    }
}

async function loadSavedProducts() {
    try {
        const data = await makeApiRequest(`/projects/${currentState.currentProject}/products`);
        currentState.savedProducts = data.products || [];
        updateProductsList();
    } catch (error) {
        console.error('Failed to load saved products:', error);
        currentState.savedProducts = [];
        updateProductsList();
    }
}

function updateProjectSelect(projects) {
    projectSelect.innerHTML = `
        <option value="">Select a project</option>
        ${projects.map(project => `
            <option value="${project.id}">${project.name}</option>
        `).join('')}
    `;
}

function updateProductsList() {
    if (!scrapedProductsList) {
        console.error('scrapedProductsList element not found');
        return;
    }
    
    const products = currentState.scrapedProducts || [];
    const tableBody = document.getElementById('productsTableBody');
    
    if (products.length === 0) {
        scrapedProductsList.classList.add('hidden');
        return;
    }

    scrapedProductsList.classList.remove('hidden');
    
    // Add or update the heading
    let headingDiv = document.querySelector('.scraped-products-heading');
    if (!headingDiv) {
        headingDiv = document.createElement('div');
        headingDiv.className = 'scraped-products-heading';
        scrapedProductsList.insertBefore(headingDiv, scrapedProductsList.firstChild);
    }
    headingDiv.innerHTML = `
        <h3 class="text-lg font-semibold text-gray-900 p-4">
            Scraped Products (${products.length})
        </h3>
    `;

    tableBody.innerHTML = '';

    products.forEach(product => {
        const row = document.createElement('tr');
        
        // Image cell
        const imageCell = document.createElement('td');
        imageCell.className = 'product-image-cell';
        const img = document.createElement('img');
        img.src = product.image_url || product.imageUrls?.[0] || DEFAULT_IMAGE;
        img.alt = product.title || 'Product Image';
        img.onerror = () => {
            img.src = DEFAULT_IMAGE;
            img.onerror = null;
        };
        imageCell.appendChild(img);
        
        // Basic Info cell
        const infoCell = document.createElement('td');
        infoCell.innerHTML = `
            <div class="product-meta">
                <div class="product-title">${product.title || 'N/A'}</div>
                <div class="product-info-text">Brand: ${product.brand || 'N/A'}</div>
                <div class="product-info-text">ASIN: ${product.asin || 'N/A'}</div>
                <div class="product-price">Price: ${product.price || 'N/A'}</div>
                <div class="product-rating">
                    Rating: ${product.rating || 'N/A'}
                    ${product.rating ? '⭐' : ''}
                </div>
            </div>
        `;
        
        // Rankings cell
        const rankingsCell = document.createElement('td');
        rankingsCell.innerHTML = `
            <div class="rankings-info">
                ${product.bestSellersRank ? `
                    <div class="rank-item">
                        Best Seller Rank: #${product.bestSellersRank}
                    </div>
                ` : ''}
                <div class="rank-item">
                    Date First Available:<br>
                    ${product.dateFirstAvailable || 'N/A'}
                </div>
            </div>
        `;
        
        // Description cell
        const descriptionCell = document.createElement('td');
        descriptionCell.innerHTML = `
            <div class="product-description">
                ${product.description || 'No description available'}
            </div>
        `;
        
        // Actions cell
        const actionsCell = document.createElement('td');
        actionsCell.innerHTML = `
            <div class="action-buttons">
                <button class="action-btn save-btn" data-asin="${product.asin}">Save</button>
                <button class="action-btn remove-btn" data-asin="${product.asin}">Remove</button>
            </div>
        `;
        
        // Append all cells
        row.appendChild(imageCell);
        row.appendChild(infoCell);
        row.appendChild(rankingsCell);
        row.appendChild(descriptionCell);
        row.appendChild(actionsCell);
        
        tableBody.appendChild(row);
    });

    setupEventListeners();
}

function setupEventListeners() {
    // Save product buttons
    document.querySelectorAll('.save-btn').forEach(button => {
        button.removeEventListener('click', handleSaveProduct);
        button.addEventListener('click', function(e) {
            const asin = e.target.dataset.asin;
            handleSaveProduct(asin);
        });
    });

    // Remove product buttons
    document.querySelectorAll('.remove-btn').forEach(button => {
        button.removeEventListener('click', handleRemoveProduct);
        button.addEventListener('click', function(e) {
            const asin = e.target.dataset.asin;
            handleRemoveProduct(asin);
        });
    });

    // Save all button
    const saveAllBtn = document.getElementById('saveAllBtn');
    if (saveAllBtn) {
        saveAllBtn.removeEventListener('click', handleSaveAllProducts);
        saveAllBtn.addEventListener('click', handleSaveAllProducts);
    }

    // Clear all button
    const clearBtn = document.getElementById('clearScrapedDataBtn');
    if (clearBtn) {
        clearBtn.removeEventListener('click', handleClearProducts);
        clearBtn.addEventListener('click', handleClearProducts);
    }
}

// Add save all products handler
async function handleSaveAllProducts() {
    const button = document.getElementById('saveAllBtn');
    if (!button) return;

    try {
        button.disabled = true;
        button.innerHTML = '<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>';

        for (const product of currentState.scrapedProducts) {
            try {
                const savedProduct = await saveProduct(product);
                currentState.savedProducts.push({ ...product, isSaved: true });
                await ExtensionStorage.updateScrapedProduct(product.asin, { saved: true });
            } catch (error) {
                console.error(`Failed to save product ${product.asin}:`, error);
            }
        }

        // Clear scraped products after saving all
        currentState.scrapedProducts = [];
        await ExtensionStorage.clearScrapedProducts();
        
        updateProductsList();
        showMessage(statusMessage, 'All products saved successfully!', 'success');
    } catch (error) {
        console.error('Save all products error:', error);
        showMessage(statusMessage, 'Failed to save all products', 'error');
    } finally {
        button.disabled = false;
        button.textContent = 'Save All';
    }
}

// Update the save product handler
async function handleSaveProduct(asin) {
    const product = currentState.scrapedProducts.find(p => p.asin === asin);
    if (!product) return;

    const button = document.querySelector(`.save-btn[data-asin="${asin}"]`);
    if (!button) return;

    try {
        button.disabled = true;
        button.innerHTML = '<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>';
        
        const savedProduct = await saveProduct(product);
        console.log('Product saved successfully:', savedProduct);
        
        // Remove from scraped products and add to saved products
        currentState.scrapedProducts = currentState.scrapedProducts.filter(p => p.asin !== asin);
        currentState.savedProducts.push({ ...product, isSaved: true });
        
        // Update storage
        await ExtensionStorage.removeScrapedProduct(asin);
        
        updateProductsList();
        showMessage(statusMessage, 'Product saved successfully!', 'success');
    } catch (error) {
        console.error('Save error:', error);
        showMessage(statusMessage, error.message, 'error');
        button.disabled = false;
        button.textContent = 'Save';
    }
}

// Update the clear products handler
async function handleClearProducts() {
    try {
        await ExtensionStorage.clearScrapedProducts();
        currentState.scrapedProducts = [];
        updateProductsList();
        showMessage(statusMessage, 'Scraped data cleared!', 'success');
    } catch (error) {
        console.error('Clear products error:', error);
        showMessage(statusMessage, 'Failed to clear scraped data', 'error');
    }
}

async function createProject(projectData) {
    try {
        const data = await makeApiRequest('/projects', {
            method: 'POST',
            body: JSON.stringify(projectData)
        });
        
        currentState.currentProject = data;
        await loadProjects();
        return data;
    } catch (error) {
        throw new Error('Failed to create project: ' + error.message);
    }
}

// Product Management Functions
async function saveProduct(product) {
    if (!currentState.token) {
        throw new Error('Not authenticated. Please log in.');
    }
    if (!currentState.currentProject) {
        throw new Error('No project selected. Please select a project first.');
    }

    try {
        console.log('Saving product with token:', currentState.token);
        console.log('Project ID:', currentState.currentProject);
        console.log('Product data:', product);

        // Lookup the selected project details from the stored project list
        let selectedProject = null;
        if (currentState.projects && Array.isArray(currentState.projects)) {
            selectedProject = currentState.projects.find(
                project => project.id == currentState.currentProject
            );
        }
        // Fallback in case selectedProject is not found
        if (!selectedProject) {
            selectedProject = { category: '', subcategory: '' };
        }

        // Build the payload using all scraped fields plus selected project details
        const payload = {
            project_id: currentState.currentProject,
            project_category: selectedProject.category || '',
            project_subcategory: selectedProject.subcategory || '',
            asin: product.asin,
            title: product.title,
            brand: product.brand,
            price: product.price,
            rating: product.rating,
            review_count: product.reviewCount,
            image_url: product.image_url || (product.imageUrls ? product.imageUrls[0] : null),
            description: product.description,
            bullet_points: product.features, // Using scraped features field
            best_sellers_rank: product.bestSellersRank,
            date_first_available: product.dateFirstAvailable,
            technical_details: product.technicalDetails,
            customer_reviews: product.customerReviews,
            customer_sayings: product.customerSayings,
            keywords: product.keywords,
            url: product.url,
            timestamp: product.timestamp
        };

        const response = await fetch(`${API_BASE_URL}/products/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${currentState.token}`
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errorData = await response.json();
            console.error('Save product response:', response.status, errorData);
            throw new Error(errorData.detail || `Failed to save product: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Save product error:', error);
        throw new Error(error.message || 'Failed to save product');
    }
}

// async function saveProduct(product) {
//     if (!currentState.token) {
//         throw new Error('Not authenticated. Please log in.');
//     }
//     if (!currentState.currentProject) {
//         throw new Error('No project selected. Please select a project first.');
//     }

//     try {
//         console.log('Saving product with token:', currentState.token);
//         console.log('Project ID:', currentState.currentProject);
//         console.log('Product data:', product);

//         const response = await fetch(`${API_BASE_URL}/products/`, {
//             method: 'POST',
//             headers: {
//                 'Content-Type': 'application/json',
//                 'Authorization': `Bearer ${currentState.token}`
//             },
//             body: JSON.stringify({
//                 project_id: currentState.currentProject,
//                 asin: product.asin,
//                 title: product.title,
//                 brand: product.brand,
//                 price: product.price,
//                 rating: product.rating,
//                 review_count: product.review_count,
//                 image_url: product.image_url || product.imageUrls?.[0],
//                 description: product.description,
//                 bullet_points: product.bulletPoints,
//                 best_sellers_rank: product.bestSellersRank,
//                 date_first_available: product.dateFirstAvailable
//             })
//         });

//         if (!response.ok) {
//             const errorData = await response.json();
//             console.error('Save product response:', response.status, errorData);
//             throw new Error(errorData.detail || `Failed to save product: ${response.status}`);
//         }

//         return await response.json();
//     } catch (error) {
//         console.error('Save product error:', error);
//         throw new Error(error.message || 'Failed to save product');
//     }
// }

// UI Functions
function showAuthSection() {
    authSection.classList.remove('hidden');
    mainSection.classList.add('hidden');
}

function showMainSection(userData) {
    authSection.classList.add('hidden');
    mainSection.classList.remove('hidden');
    userEmail.textContent = userData.email;
    userAvatar.textContent = userData.email[0].toUpperCase();
}

function showMessage(element, message, type) {
    element.textContent = message;
    element.className = `text-sm ${type === 'error' ? 'text-red-600' : 'text-green-600'}`;
    element.classList.remove('hidden');
    
    if (type === 'success') {
        setTimeout(() => {
            element.classList.add('hidden');
        }, 3000);
    }
}

// Event Listeners
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    const submitBtn = loginForm.querySelector('button');
    const originalBtnText = submitBtn.textContent;
    submitBtn.innerHTML = '<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>';
    submitBtn.disabled = true;
    
    try {
        await login(email, password);
        showMessage(loginMessage, 'Login successful!', 'success');
        setTimeout(() => {
            showMainSection(currentState.user);
            loadProjects();
        }, 1000);
    } catch (error) {
        showMessage(loginMessage, error.message, 'error');
    } finally {
        submitBtn.textContent = originalBtnText;
        submitBtn.disabled = false;
    }
});

logoutBtn.addEventListener('click', async () => {
    await chrome.storage.local.remove(['authToken', 'userData', 'currentProject', 'scrapedProducts']);
    currentState = {
        token: null,
        user: null,
        currentProject: null,
        scrapedProducts: [],
        savedProducts: []
    };
    showAuthSection();
});

projectSelect.addEventListener('change', async (e) => {
    currentState.currentProject = e.target.value;
    await ExtensionStorage.set({ currentProject: currentState.currentProject });
    
    if (currentState.currentProject) {
        productSection.classList.remove('hidden');
        // Force update product list
        updateProductsList();
    }
});

createProjectBtn.addEventListener('click', () => {
    newProjectForm.classList.remove('hidden');
    projectSection.classList.add('hidden');
});

saveProjectBtn.addEventListener('click', async () => {
    const projectName = document.getElementById('projectName').value;
    const projectCategory = document.getElementById('projectCategory').value;
    const projectSubcategory = document.getElementById('projectSubcategory').value;
    
    try {
        await createProject({
            name: projectName,
            category: projectCategory,
            subcategory: projectSubcategory
        });
        
        newProjectForm.classList.add('hidden');
        projectSection.classList.remove('hidden');
        showMessage(statusMessage, 'Project created successfully!', 'success');
    } catch (error) {
        showMessage(statusMessage, error.message, 'error');
    }
});

cancelProjectBtn.addEventListener('click', () => {
    newProjectForm.classList.add('hidden');
    projectSection.classList.remove('hidden');
});

function updateCurrentProductDisplay(product) {
    const productTitle = document.getElementById('productTitle');
    const productBrand = document.getElementById('productBrand');
    const productPrice = document.getElementById('productPrice');
    const productAsin = document.getElementById('productAsin');
    const productImage = document.getElementById('productImage');
    
    if (productTitle) productTitle.textContent = product.title || 'No title available';
    if (productBrand) productBrand.textContent = product.brand || 'N/A';
    if (productPrice) productPrice.textContent = product.price || 'N/A';
    if (productAsin) productAsin.textContent = `ASIN: ${product.asin || 'N/A'}`;
    if (productImage) {
        productImage.src = product.image_url || DEFAULT_IMAGE;
        productImage.onerror = function() {
            this.onerror = null;
            this.src = DEFAULT_IMAGE;
        };
    }
    
    if (productInfo) productInfo.classList.remove('hidden');
}

// Check if we're on a product page
chrome.tabs.query({active: true, currentWindow: true}, async (tabs) => {
    const url = tabs[0].url;
    if (url && (url.includes('amazon.com') || url.includes('amazon.co.uk'))) {
        notProductPage.classList.add('hidden');
        productPage.classList.remove('hidden');
    } else {
        notProductPage.classList.remove('hidden');
        productPage.classList.add('hidden');
    }
});

// Update the message listener
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'PRODUCT_SCRAPED') {
        console.log('Received scraped product:', message.product);
        
        if (!currentState.currentProject) {
            showMessage(statusMessage, 'Please select a project first', 'error');
            return;
        }

        handleScrapedProduct(message.product);
    }
});

// Add new function to handle scraped products
async function handleScrapedProduct(product) {
    try {
        // Add to state first
        const newProduct = {
            ...product,
            saved: false,
            timestamp: new Date().toISOString(),
            id: `temp_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
        };

        // Check if product already exists
        const existingProduct = currentState.scrapedProducts.find(p => p.asin === product.asin);
        if (!existingProduct) {
            // Update state
            currentState.scrapedProducts.push(newProduct);

            // Get existing products from storage
            const storage = await chrome.storage.local.get(['scrapedProducts']);
            const storedProducts = storage.scrapedProducts || [];
            
            // Add new product to storage
            storedProducts.push(newProduct);
            
            // Update storage
            await chrome.storage.local.set({ scrapedProducts: storedProducts });
            
            console.log('Updated storage with new product:', storedProducts);
            console.log('Current state products:', currentState.scrapedProducts);

            // Show product section
            if (productSection) {
                productSection.classList.remove('hidden');
            }

            // Update the UI
            updateProductsList();
            showMessage(statusMessage, 'Product scraped successfully!', 'success');
        } else {
            showMessage(statusMessage, 'Product already exists', 'info');
        }
    } catch (error) {
        console.error('Error handling scraped product:', error);
        showMessage(statusMessage, 'Error saving product', 'error');
    }
}

// Update the remove product handler
async function handleRemoveProduct(asin) {
    try {
        // Remove from state
        currentState.scrapedProducts = currentState.scrapedProducts.filter(p => p.asin !== asin);
        
        // Remove from storage
        await ExtensionStorage.removeScrapedProduct(asin);
        
        // Update UI
        updateProductsList();
        showMessage(statusMessage, 'Product removed successfully', 'success');
    } catch (error) {
        console.error('Error removing product:', error);
        showMessage(statusMessage, 'Error removing product', 'error');
    }
} 