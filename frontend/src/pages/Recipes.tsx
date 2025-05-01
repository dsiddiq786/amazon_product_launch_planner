import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import api from '../utils/api';
import { formatDate } from '../utils/date';

interface Recipe {
  id: string;
  project_id: string;
  user_id: string;
  product_id: string | null;
  category: string;
  subcategory: string;
  content: any; // Content can be either string or object
  title?: string; // Title is required in the model but may not be in the data
  is_master: boolean;
  created_at: string;
  updated_at: string;
  prompt_block_id?: string; // ID of the prompt block used to generate this recipe
}

interface CategoryGroup {
  category: string;
  subcategory: string;
  recipe: Recipe;
}

interface Prompt {
  id: string;
  block_title: string;
  input_prompt: string;
  output_example: string;
  prompt_category: string;
  is_active: boolean;
  created_at: string;
  master_recipe_prompt?: string;
}

const Recipes: React.FC = () => {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
  const [formData, setFormData] = useState({
    category: '',
    subcategory: '',
    content: '',
    is_master: false
  });
  const [groupedRecipes, setGroupedRecipes] = useState<CategoryGroup[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<{category: string, subcategory: string} | null>(null);
  const [filteredRecipes, setFilteredRecipes] = useState<Recipe[]>([]);
  const [viewMode, setViewMode] = useState<'grouped' | 'filtered' | 'single'>('grouped');
  const [singleRecipe, setSingleRecipe] = useState<Recipe | null>(null);
  const [recipePrompts, setRecipePrompts] = useState<Prompt[]>([]);
  const [activePromptTab, setActivePromptTab] = useState<string | null>(null);
  const [loadingPrompts, setLoadingPrompts] = useState(false);

  const fetchRecipes = async () => {
    try {
      setLoading(true);
      // Use the new grouped endpoint to get one recipe per category/subcategory
      const response = await api.get('/recipes/master/grouped');
      console.log('Grouped recipes response:', response.data);
      setGroupedRecipes(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to fetch recipes');
      console.error('Error fetching recipes:', err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch prompts that match the recipe category
  const fetchRecipePrompts = async (category: string) => {
    try {
      setLoadingPrompts(true);
      
      // First fetch all active prompts regardless of category to find prompt_block_id matches
      const allPromptsResponse = await api.get('/prompts/', {
        params: { active_only: true }
      });
      
      // Then fetch category-specific prompts
      const categoryPromptsResponse = await api.get('/prompts/', {
        params: { 
          category: category,
          active_only: true 
        }
      });
      
      console.log('Recipe prompts response:', categoryPromptsResponse.data);
      
      // Get all prompts
      const allPrompts = allPromptsResponse.data || [];
      
      // Get category-specific prompts
      const categoryPrompts = categoryPromptsResponse.data || [];
      
      // Combine and deduplicate prompts
      const combinedPrompts = [...categoryPrompts];
      
      // Add any prompts that match the recipe's prompt_block_id but aren't already in the list
      if (singleRecipe?.prompt_block_id) {
        const matchingPrompt = allPrompts.find((prompt: Prompt) => 
          prompt.id === singleRecipe.prompt_block_id && 
          !combinedPrompts.some(p => p.id === prompt.id)
        );
        
        if (matchingPrompt) {
          combinedPrompts.push(matchingPrompt);
        }
      }
      
      // Filter prompts that have a master_recipe_prompt
      const promptsWithRecipes = combinedPrompts.filter((prompt: Prompt) => 
        prompt.master_recipe_prompt && prompt.master_recipe_prompt.trim() !== ''
      );
      
      setRecipePrompts(promptsWithRecipes);
      
      // Set active tab to first prompt if available
      if (promptsWithRecipes.length > 0 && !activePromptTab) {
        setActivePromptTab(promptsWithRecipes[0].block_title);
      }
      
      // If the single recipe has a prompt_block_id, update its title using the prompt block name
      if (singleRecipe?.prompt_block_id) {
        // Find the prompt block that matches the recipe's prompt_block_id
        const matchingPrompt = allPrompts.find((prompt: Prompt) => 
          prompt.id === singleRecipe.prompt_block_id
        );
        
        if (matchingPrompt) {
          // Update the recipe with the prompt block title
          setSingleRecipe(prev => {
            if (!prev) return prev;
            return {
              ...prev,
              title: matchingPrompt.block_title || prev.title
            };
          });
        }
      }
    } catch (err: any) {
      console.error('Error fetching recipe prompts:', err);
      
      // Enhanced error handling for prompts fetching
      let errorMessage = 'Failed to fetch recipe prompts';
      
      if (err.response) {
        console.error('Prompts response status:', err.response.status);
        console.error('Prompts response data:', err.response.data);
        
        if (err.response.data?.detail) {
          errorMessage = `Prompts error: ${err.response.data.detail}`;
        }
      } else if (err.request) {
        console.error('No prompts response received:', err.request);
        errorMessage = 'No response received from prompts server. Check your connection.';
      } else {
        console.error('Prompts request error:', err.message);
        errorMessage = `Prompts request error: ${err.message}`;
      }
      
      setError(errorMessage);
    } finally {
      setLoadingPrompts(false);
    }
  };

  useEffect(() => {
    fetchRecipes();
  }, []);

  // When a single recipe is loaded, fetch related prompts
  useEffect(() => {
    if (singleRecipe) {
      fetchRecipePrompts(singleRecipe.category);
    }
  }, [singleRecipe]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (selectedRecipe) {
        await api.put(`/recipes/${selectedRecipe.id}`, formData);
      } else {
        await api.post('/recipes', formData);
      }
      setShowForm(false);
      setSelectedRecipe(null);
      setFormData({
        category: '',
        subcategory: '',
        content: '',
        is_master: false
      });
      fetchRecipes();
    } catch (err) {
      setError('Failed to save recipe');
      console.error('Error saving recipe:', err);
    }
  };

  const handleEdit = (recipe: Recipe) => {
    setSelectedRecipe(recipe);
    setFormData({
      category: recipe.category,
      subcategory: recipe.subcategory,
      content: recipe.content,
      is_master: recipe.is_master
    });
    setShowForm(true);
  };

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this recipe? This will also delete all related analysis and logs for this category and subcategory.')) {
      try {
        setLoading(true);
        await api.delete(`/recipes/${id}`);
        // Show success message
        setError(null);
        // Refresh the recipes list
        await fetchRecipes();
        // If in filtered view, update the filtered recipes
        if (viewMode === 'filtered') {
          setFilteredRecipes(prev => prev.filter(recipe => recipe.id !== id));
        }
      } catch (err: any) {
        let errorMessage = 'Failed to delete recipe';
        if (err.response?.data?.detail) {
          errorMessage = err.response.data.detail;
        }
        setError(errorMessage);
        console.error('Error deleting recipe:', err);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleCategoryClick = async (category: string, subcategory: string) => {
    try {
      setLoading(true);
      // Use the new category-specific endpoint
      const response = await api.get(`/recipes/master/${category}/${subcategory}`);
      console.log('Category recipes response:', response.data);
      setFilteredRecipes(response.data);
      setSelectedCategory({ category, subcategory });
      setViewMode('filtered');
    } catch (err) {
      setError(`Failed to fetch recipes for ${category}/${subcategory}`);
      console.error('Error fetching category recipes:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleViewSingleRecipe = async (category: string, subcategory: string) => {
    try {
      setLoading(true);
      setError(null); // Clear previous errors
      
      // Use the new single master recipe endpoint
      const response = await api.get(`/recipes/master/single/${category}/${subcategory}`);
      console.log('Single master recipe response:', response.data);
      
      // Process the recipe to ensure it's compatible with our interface
      const recipeData = response.data;
      
      // If content is an object, extract the string response from it
      if (typeof recipeData.content === 'object' && recipeData.content !== null) {
        if (recipeData.content.response) {
          recipeData.content = recipeData.content.response;
        } else {
          recipeData.content = JSON.stringify(recipeData.content);
        }
      }
      
      // If title is missing, use the prompt block id or category/subcategory as fallback
      if (!recipeData.title) {
        if (recipeData.prompt_block_id) {
          // We'll try to get the prompt block name later after loading the recipe
          recipeData.title = `Recipe for ${category}/${subcategory}`;
        } else {
          recipeData.title = `${category} - ${subcategory}`;
        }
      }
      
      setSingleRecipe(recipeData);
      setSelectedCategory({ category, subcategory });
      setViewMode('single');
    } catch (err: any) {
      console.error('Error fetching single master recipe:', err);
      
      // Enhanced error handling with detailed information
      let errorMessage = `Failed to fetch single master recipe for ${category}/${subcategory}`;
      
      if (err.response) {
        console.error('Response status:', err.response.status);
        console.error('Response data:', err.response.data);
        
        if (err.response.data?.detail) {
          errorMessage = `Error (${err.response.status}): ${err.response.data.detail}`;
        } else if (err.response.status) {
          errorMessage = `Server error (${err.response.status}) when fetching recipe`;
        }
      } else if (err.request) {
        // Request was made but no response received
        console.error('No response received:', err.request);
        errorMessage = 'No response received from server. Please check your connection.';
      } else {
        // Error setting up the request
        console.error('Request error:', err.message);
        errorMessage = `Request error: ${err.message}`;
      }
      
      setError(errorMessage);
      
      // Reset view mode to grouped if we couldn't load the single recipe
      setViewMode('grouped');
    } finally {
      setLoading(false);
    }
  };

  const handleBackToCategories = () => {
    setSelectedCategory(null);
    setFilteredRecipes([]);
    setSingleRecipe(null);
    setViewMode('grouped');
  };

  const categoryColors = {
    product_recipe: 'text-blue-700 bg-blue-50',
    category_recipe: 'text-green-700 bg-green-50'
  };

  const renderGroupedView = () => {
    return (
      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Category
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Subcategory
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Master
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Created
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {groupedRecipes.map((group) => (
              <tr 
                key={`${group.category}-${group.subcategory}`} 
                className="cursor-pointer hover:bg-gray-50"
                onClick={() => handleViewSingleRecipe(group.category, group.subcategory)}
              >
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                    categoryColors[group.category as keyof typeof categoryColors] || 'text-gray-700 bg-gray-50'
                  }`}>
                    {group.category.replace('_', ' ').toUpperCase()}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {group.subcategory}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="px-2 py-1 rounded-full text-xs font-semibold bg-green-100 text-green-800">
                    Yes
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {formatDate(group.recipe.created_at)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium" onClick={e => e.stopPropagation()}>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleCategoryClick(group.category, group.subcategory);
                    }}
                    className="text-blue-600 hover:text-blue-900 mr-3"
                  >
                    View All
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleEdit(group.recipe);
                    }}
                    className="text-blue-600 hover:text-blue-900 mr-3"
                  >
                    Edit
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(group.recipe.id);
                    }}
                    className="text-red-600 hover:text-red-900"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderFilteredView = () => {
    if (!selectedCategory) return null;
    
    return (
      <div>
        <div className="flex items-center mb-4">
          <button
            onClick={handleBackToCategories}
            className="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded inline-flex items-center mr-3"
          >
            <i className="fas fa-arrow-left mr-1"></i> Back
          </button>
          <h2 className="text-lg font-semibold">
            Master Recipes: {selectedCategory.category.replace('_', ' ').toUpperCase()} / {selectedCategory.subcategory}
          </h2>
        </div>
        
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Category
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Subcategory
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredRecipes.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                    No master recipes found for this category and subcategory
                  </td>
                </tr>
              ) : (
                filteredRecipes.map((recipe) => (
                  <tr key={recipe.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {recipe.id.substring(0, 8)}...
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                        categoryColors[recipe.category as keyof typeof categoryColors] || 'text-gray-700 bg-gray-50'
                      }`}>
                        {recipe.category.replace('_', ' ').toUpperCase()}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {recipe.subcategory}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(recipe.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => handleEdit(recipe)}
                        className="text-blue-600 hover:text-blue-900 mr-3"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(recipe.id)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Recipe Content Preview Section */}
        {filteredRecipes.length > 0 && (
          <div className="mt-6 bg-white rounded-lg shadow-md overflow-hidden">
            <div className="p-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold">Recipe Content Preview</h3>
            </div>
            <div className="p-4">
              {filteredRecipes.map((recipe) => (
                <div key={recipe.id} className="mb-4 pb-4 border-b border-gray-200 last:border-b-0 last:mb-0 last:pb-0">
                  <h4 className="font-medium mb-2">Recipe ID: {recipe.id.substring(0, 8)}...</h4>
                  <div className="bg-gray-50 p-3 rounded">
                    <pre className="text-sm whitespace-pre-wrap">{recipe.content}</pre>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderSingleRecipeView = () => {
    if (!singleRecipe || !selectedCategory) return null;
    
    // Find the prompt block name if it exists
    const getPromptBlockName = () => {
      if (!singleRecipe.prompt_block_id) return null;
      
      const matchingPrompt = recipePrompts.find(prompt => 
        prompt.id === singleRecipe.prompt_block_id
      );
      
      return matchingPrompt ? matchingPrompt.block_title : null;
    };
    
    const promptBlockName = getPromptBlockName();
    
    // Function to render prompt tabs and content
    const renderPromptTabs = () => {
      if (loadingPrompts) {
        return (
          <div className="py-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-500">Loading prompts...</p>
          </div>
        );
      }
      
      if (recipePrompts.length === 0) {
        return (
          <div className="py-8 text-center text-gray-500">
            No prompt blocks available for this recipe category.
          </div>
        );
      }
      
      // Create tabs from prompts
      const tabs = recipePrompts.map((prompt) => (
        <button
          key={prompt.id}
          className={`px-4 py-2 font-medium text-sm rounded-t-lg ${
            activePromptTab === prompt.block_title
              ? 'bg-white text-blue-600 border-t border-l border-r border-gray-200'
              : 'bg-gray-100 text-gray-700 hover:text-gray-900'
          }`}
          onClick={() => setActivePromptTab(prompt.block_title)}
        >
          {prompt.block_title}
        </button>
      ));
      
      // Find the active prompt
      const activePrompt = recipePrompts.find((prompt) => prompt.block_title === activePromptTab);
      
      // Render the active tab content
      const renderPromptContent = () => {
        if (!activePrompt) return null;
        
        return (
          <div className="bg-white p-6 border border-gray-200 rounded-b-lg rounded-tr-lg">
            <h4 className="font-medium mb-2 text-gray-700">{activePrompt.block_title}</h4>
            <pre className="whitespace-pre-wrap bg-gray-50 p-4 rounded-lg text-sm">
              {activePrompt.master_recipe_prompt || 'No content available'}
            </pre>
          </div>
        );
      };
      
      return (
        <div className="mt-6">
          <div className="flex space-x-2 overflow-x-auto pb-2">
            {tabs}
          </div>
          {renderPromptContent()}
        </div>
      );
    };
    
    return (
      <div>
        <div className="flex items-center mb-4">
          <button
            onClick={handleBackToCategories}
            className="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded inline-flex items-center mr-3"
          >
            <i className="fas fa-arrow-left mr-1"></i> Back
          </button>
          <h2 className="text-lg font-semibold">
            {singleRecipe.title || `Master Recipe: ${selectedCategory.category.replace('_', ' ').toUpperCase()} / ${selectedCategory.subcategory}`}
          </h2>
        </div>
        
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="p-4 border-b border-gray-200">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold">Recipe Details</h3>
              <div>
                <button
                  onClick={() => handleEdit(singleRecipe)}
                  className="bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700 mr-2"
                >
                  Edit
                </button>
                <button
                  onClick={() => handleDelete(singleRecipe.id)}
                  className="bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700"
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
          
          <div className="p-4">
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <p className="text-sm text-gray-500">ID</p>
                <p className="font-medium">{singleRecipe.id}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Created</p>
                <p className="font-medium">{formatDate(singleRecipe.created_at)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Category</p>
                <p className="font-medium">
                  <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                    categoryColors[singleRecipe.category as keyof typeof categoryColors] || 'text-gray-700 bg-gray-50'
                  }`}>
                    {singleRecipe.category.replace('_', ' ').toUpperCase()}
                  </span>
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Subcategory</p>
                <p className="font-medium">{singleRecipe.subcategory}</p>
              </div>
              {promptBlockName && (
                <div>
                  <p className="text-sm text-gray-500">Prompt Block</p>
                  <p className="font-medium">{promptBlockName}</p>
                </div>
              )}
            </div>
            
            <div className="mt-4">
              <h4 className="text-md font-medium mb-2">Recipe Content</h4>
              <div className="bg-gray-50 p-4 rounded">
                <pre className="text-sm whitespace-pre-wrap">{singleRecipe.content}</pre>
              </div>
            </div>
          </div>
        </div>
        
        {/* Prompt Blocks Section */}
        <div className="mt-6 bg-white rounded-lg shadow-md overflow-hidden">
          <div className="p-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold">Prompt Blocks</h3>
          </div>
          <div className="p-4">
            {renderPromptTabs()}
          </div>
        </div>
        
        <div className="mt-4 flex justify-end">
          <button
            onClick={() => handleCategoryClick(selectedCategory.category, selectedCategory.subcategory)}
            className="bg-gray-200 text-gray-700 px-4 py-2 rounded hover:bg-gray-300"
          >
            View All Recipes in This Category
          </button>
        </div>
      </div>
    );
  };

  return (
    <Layout>
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-gray-800">
            {viewMode === 'grouped' ? 'Master Recipes by Category' : viewMode === 'filtered' ? 'Master Recipes' : 'Single Master Recipe'}
          </h1>
          <button
            onClick={() => {
              setSelectedRecipe(null);
              setFormData({
                category: '',
                subcategory: '',
                content: '',
                is_master: false
              });
              setShowForm(true);
            }}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Add Recipe
          </button>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4 flex justify-between items-center">
            <div>{error}</div>
            <button 
              onClick={() => {
                setError(null);
                if (viewMode === 'grouped') {
                  fetchRecipes();
                } else if (viewMode === 'filtered' && selectedCategory) {
                  handleCategoryClick(selectedCategory.category, selectedCategory.subcategory);
                } else if (viewMode === 'single' && selectedCategory) {
                  handleViewSingleRecipe(selectedCategory.category, selectedCategory.subcategory);
                }
              }}
              className="bg-red-700 text-white px-3 py-1 rounded hover:bg-red-800 text-sm ml-4"
            >
              Retry
            </button>
          </div>
        )}

        {showForm && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">
              {selectedRecipe ? 'Edit Recipe' : 'Add Recipe'}
            </h2>
            <form onSubmit={handleSubmit}>
              <div className="mb-4">
                <label className="block text-gray-700 text-sm font-bold mb-2">
                  Category
                </label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="w-full px-3 py-2 border rounded"
                  required
                >
                  <option value="">Select Category</option>
                  <option value="product_recipe">Product Recipe</option>
                  <option value="category_recipe">Category Recipe</option>
                </select>
              </div>

              <div className="mb-4">
                <label className="block text-gray-700 text-sm font-bold mb-2">
                  Subcategory
                </label>
                <input
                  type="text"
                  value={formData.subcategory}
                  onChange={(e) => setFormData({ ...formData, subcategory: e.target.value })}
                  className="w-full px-3 py-2 border rounded"
                  required
                />
              </div>

              <div className="mb-4">
                <label className="block text-gray-700 text-sm font-bold mb-2">
                  Content
                </label>
                <textarea
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  className="w-full px-3 py-2 border rounded"
                  rows={5}
                  required
                />
              </div>

              <div className="mb-4">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={formData.is_master}
                    onChange={(e) => setFormData({ ...formData, is_master: e.target.checked })}
                    className="mr-2"
                  />
                  <span className="text-gray-700">Master Recipe</span>
                </label>
              </div>

              <div className="flex justify-end">
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="bg-gray-300 text-gray-700 px-4 py-2 rounded mr-2 hover:bg-gray-400"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                >
                  {selectedRecipe ? 'Update' : 'Save'}
                </button>
              </div>
            </form>
          </div>
        )}

        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          viewMode === 'grouped' ? renderGroupedView() : 
          viewMode === 'filtered' ? renderFilteredView() : 
          renderSingleRecipeView()
        )}
      </div>
    </Layout>
  );
};

export default Recipes; 