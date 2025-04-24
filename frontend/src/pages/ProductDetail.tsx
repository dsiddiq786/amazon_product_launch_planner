import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { api } from '../utils/api';
import { formatDate } from '../utils/date';
import { useAuth } from '../contexts/AuthContext';

interface Product {
  id: string;
  project_id: string;
  asin: string;
  title: string;
  description: string;
  price: string;
  image_url: string;
  rating: string;
  review_count: string;
  best_sellers_rank: string;
  features: string[];
  brand: string;
  technical_details: Record<string, string>;
  customer_reviews: string[];
  created_at: string;
  updated_at: string;
  analysis_results?: Record<string, any>[];
}

const ProductDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('');
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    const fetchProductDetails = async () => {
      try {
        setLoading(true);
        
        console.log(`Fetching product details for ID: ${id}`);
        console.log(`Current user:`, user);
        console.log(`Retry count: ${retryCount}`);

        // Ensure auth token is set
        const token = localStorage.getItem('token');
        if (!token) {
          console.error("No authentication token found");
          setError('Authentication error. Please log in again.');
          setLoading(false);
          return;
        }

        // Make the API request with explicit headers to ensure token is sent
        const response = await api.get(`/products/${id}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });
        
        console.log('API Response status:', response.status);
        console.log('API Response data structure:', Object.keys(response.data));
        
        if (!response.data) {
          throw new Error('No data returned from API');
        }
        
        setProduct(response.data);
        
        // Log the full product data for debugging
        console.log('Product data:', response.data);
        
        // Set default active tab if analysis_results exist
        if (response.data.analysis_results && response.data.analysis_results.length > 0) {
          const firstKey = Object.keys(response.data.analysis_results[0])[0];
          console.log('Setting active tab to:', firstKey);
          setActiveTab(firstKey);
        }
        
        setError(null);
      } catch (err: any) {
        console.error('Error fetching product details:', err);
        
        // More detailed error logging
        if (err.response) {
          console.error('Response status:', err.response.status);
          console.error('Response data:', err.response.data);
          
          // Handle specific error cases
          if (err.response.status === 401) {
            setError('Your session has expired. Please log in again.');
            localStorage.removeItem('token');
            setTimeout(() => navigate('/login'), 2000);
          } else if (err.response.status === 403) {
            setError('You do not have permission to view this product.');
          } else if (err.response.status === 404) {
            setError('Product not found. It may have been deleted or you may not have access to it.');
          } else {
            setError(`Failed to fetch product details: ${err.response.data.detail || 'Unknown error'}`);
          }
          
          // Implement retry for fixable errors (like network issues)
          if (err.response.status >= 500 && retryCount < 3) {
            console.log(`Retrying API call (attempt ${retryCount + 1})...`);
            setRetryCount(prev => prev + 1);
            return; // Will trigger useEffect again due to retryCount change
          }
        } else if (err.request) {
          console.error('Request was made but no response received');
          setError('Network error. Please check your connection and try again.');
          
          // Retry network issues
          if (retryCount < 3) {
            console.log(`Retrying API call (attempt ${retryCount + 1})...`);
            setRetryCount(prev => prev + 1);
            return; // Will trigger useEffect again due to retryCount change
          }
        } else {
          setError(`Error: ${err.message || 'Unknown error'}`);
        }
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchProductDetails();
    }
  }, [id, retryCount, navigate, user]);

  const handleBackClick = () => {
    navigate('/products');
  };

  const handleRetry = () => {
    setError(null);
    setRetryCount(prev => prev + 1);
  };

  const renderTechnicalDetails = () => {
    if (!product?.technical_details || Object.keys(product.technical_details).length === 0) {
      return <p className="text-gray-500 italic">No technical details available</p>;
    }

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.entries(product.technical_details).map(([key, value]) => (
          <div key={key} className="border-b pb-2">
            <span className="font-medium text-gray-700">{key}: </span>
            <span className="text-gray-600">{value}</span>
          </div>
        ))}
      </div>
    );
  };

  const renderFeatures = () => {
    if (!product?.features || product.features.length === 0) {
      return <p className="text-gray-500 italic">No features available</p>;
    }

    return (
      <ul className="list-disc pl-5 space-y-2">
        {product.features.map((feature, index) => (
          <li key={index} className="text-gray-600">{feature}</li>
        ))}
      </ul>
    );
  };

  const renderCustomerReviews = () => {
    if (!product?.customer_reviews || product.customer_reviews.length === 0) {
      return <p className="text-gray-500 italic">No customer reviews available</p>;
    }

    return (
      <div className="space-y-4">
        {product.customer_reviews.map((review, index) => (
          <div key={index} className="bg-gray-50 p-4 rounded-lg">
            <p className="text-gray-600">{review}</p>
          </div>
        ))}
      </div>
    );
  };

  const renderAnalysisResults = () => {
    if (!product?.analysis_results) {
      return <p className="text-gray-500 italic">No analysis results available</p>;
    }

    console.log('Analysis results:', product.analysis_results);
    
    // Check if analysis_results is an object instead of an array
    if (!Array.isArray(product.analysis_results)) {
      // If it's an object, convert it to an array of key-value pairs
      const analysisArray = Object.entries(product.analysis_results).map(([key, value]) => {
        const result: Record<string, any> = {};
        result[key] = value;
        return result;
      });
      
      console.log('Converted analysis results to array:', analysisArray);
      
      if (analysisArray.length === 0) {
        return <p className="text-gray-500 italic">No analysis results available</p>;
      }
      
      // Set active tab if not set
      if (!activeTab && analysisArray.length > 0) {
        const firstKey = Object.keys(analysisArray[0])[0];
        setActiveTab(firstKey);
      }
      
      // Create tabs from analysis results
      const tabs = analysisArray.map((result, index) => {
        const tabName = Object.keys(result)[0];
        return (
          <button
            key={index}
            className={`px-4 py-2 font-medium text-sm rounded-t-lg ${
              activeTab === tabName
                ? 'bg-white text-blue-600 border-t border-l border-r border-gray-200'
                : 'bg-gray-100 text-gray-700 hover:text-gray-900'
            }`}
            onClick={() => setActiveTab(tabName)}
          >
            {tabName}
          </button>
        );
      });

      // Find the active analysis result
      const activeResult = analysisArray.find((result) => Object.keys(result)[0] === activeTab);
      
      console.log('Active tab:', activeTab);
      console.log('Active result:', activeResult);
      
      // Render the active tab content
      const renderTabContent = () => {
        if (!activeResult || !activeTab) return null;
        
        const content = activeResult[activeTab as keyof typeof activeResult]?.response || {};
        
        return (
          <div className="bg-white p-6 border border-gray-200 rounded-b-lg rounded-tr-lg">
            <pre className="whitespace-pre-wrap bg-gray-50 p-4 rounded-lg text-sm">
              {typeof content === 'object' 
                ? JSON.stringify(content, null, 2) 
                : content}
            </pre>
          </div>
        );
      };

      return (
        <div className="mt-6">
          <div className="flex space-x-2 overflow-x-auto pb-2">
            {tabs}
          </div>
          {renderTabContent()}
        </div>
      );
    }
    
    // If it's an array (the original implementation)
    if (product.analysis_results.length === 0) {
      return <p className="text-gray-500 italic">No analysis results available</p>;
    }

    // Create tabs from analysis results
    const tabs = product.analysis_results.map((result, index) => {
      const tabName = Object.keys(result)[0];
      return (
        <button
          key={index}
          className={`px-4 py-2 font-medium text-sm rounded-t-lg ${
            activeTab === tabName
              ? 'bg-white text-blue-600 border-t border-l border-r border-gray-200'
              : 'bg-gray-100 text-gray-700 hover:text-gray-900'
          }`}
          onClick={() => setActiveTab(tabName)}
        >
          {tabName}
        </button>
      );
    });

    // Find the active analysis result
    const activeResult = product.analysis_results.find((result) => Object.keys(result)[0] === activeTab);
    
    console.log('Active tab:', activeTab);
    console.log('Active result:', activeResult);
    
    // Render the active tab content
    const renderTabContent = () => {
      if (!activeResult || !activeTab) return null;
      
      const content = activeResult[activeTab as keyof typeof activeResult]?.response || {};
      
      return (
        <div className="bg-white p-6 border border-gray-200 rounded-b-lg rounded-tr-lg">
          <pre className="whitespace-pre-wrap bg-gray-50 p-4 rounded-lg text-sm">
            {typeof content === 'object' 
              ? JSON.stringify(content, null, 2) 
              : content}
          </pre>
        </div>
      );
    };

    return (
      <div className="mt-6">
        <div className="flex space-x-2 overflow-x-auto pb-2">
          {tabs}
        </div>
        {renderTabContent()}
      </div>
    );
  };

  if (loading) {
    return (
      <Layout>
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </Layout>
    );
  }

  if (error || !product) {
    return (
      <Layout>
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error || 'Product not found'}
        </div>
        <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
          <button
            onClick={handleBackClick}
            className="bg-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-400"
          >
            Back to Products
          </button>
          <button
            onClick={handleRetry}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center mb-6">
          <button
            onClick={handleBackClick}
            className="bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-2 px-4 rounded inline-flex items-center mr-4"
          >
            <i className="fas fa-arrow-left mr-2"></i>
            Back
          </button>
          <h1 className="text-2xl font-bold text-gray-800">Product Details</h1>
        </div>

        {/* Product Overview */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden mb-8">
          <div className="p-6">
            <div className="flex flex-col md:flex-row">
              <div className="md:w-1/3 flex justify-center mb-6 md:mb-0">
                <img
                  src={product.image_url}
                  alt={product.title}
                  className="w-48 h-48 object-contain"
                />
              </div>
              <div className="md:w-2/3 md:pl-8">
                <h2 className="text-xl font-semibold text-gray-900 mb-2">{product.title}</h2>
                <p className="text-sm text-gray-500 mb-4">ASIN: {product.asin}</p>
                
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <p className="text-sm text-gray-500">Brand</p>
                    <p className="font-medium">{product.brand}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Price</p>
                    <p className="font-medium">{product.price}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Rating</p>
                    <div className="flex items-center">
                      <span className="text-yellow-400">★</span>
                      <span className="ml-1 font-medium">
                        {product.rating} ({product.review_count} reviews)
                      </span>
                    </div>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Best Sellers Rank</p>
                    <p className="font-medium">{product.best_sellers_rank}</p>
                  </div>
                </div>
                
                <div className="mt-4">
                  <p className="text-sm text-gray-500 mb-1">Description</p>
                  <p className="text-gray-700">{product.description}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Product Details Sections */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden mb-8">
          <div className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Features</h3>
            {renderFeatures()}
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-md overflow-hidden mb-8">
          <div className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Technical Details</h3>
            {renderTechnicalDetails()}
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow-md overflow-hidden mb-8">
          <div className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Customer Reviews</h3>
            {renderCustomerReviews()}
          </div>
        </div>
        
        {/* Analysis Results */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Analysis Results</h3>
            {renderAnalysisResults()}
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default ProductDetail; 