import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import api from '../services/api';

interface Prompt {
  id: string;
  block_title: string;
  input_prompt: string;
  output_example: string;
  prompt_category: string;
  is_active: boolean;
  rerun_on_existing: boolean;
  analyzed_products_count: number;
  created_at: string;
  updated_at: string;
  limit?: number;
  skip?: number;
  sort_field?: string;
  sort_order?: string;
  master_recipe_prompt?: string;
}

const categoryColors: Record<string, string> = {
  competitor_analysis: 'text-purple-700 bg-purple-50',
  launch_planner: 'text-blue-700 bg-blue-50',
  market_research: 'text-green-700 bg-green-50',
  product_analysis: 'text-orange-700 bg-orange-50',
  product_recipe: 'text-pink-700 bg-pink-50',
  category_recipe: 'text-indigo-700 bg-indigo-50',
  other: 'text-gray-700 bg-gray-50',
};

const Prompts: React.FC = () => {
  const [prompts, setPrompts] = useState<Prompt[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [selectedPrompt, setSelectedPrompt] = useState<Prompt | null>(null);
  const [showViewModal, setShowViewModal] = useState(false);
  const [formData, setFormData] = useState({
    block_title: '',
    input_prompt: '',
    output_example: '',
    prompt_category: '',
    is_active: true,
    rerun_on_existing: false,
    limit: 2000,
    skip: 0,
    sort_field: 'created_at',
    sort_order: 'desc',
    master_recipe_prompt: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [totalProducts, setTotalProducts] = useState<number>(0);

  const categories = [
    'competitor_analysis',
    'launch_planner',
    'market_research',
    'product_analysis',
    'product_recipe',
    'category_recipe',
    'other',
  ];

  const sortFields = [
    { value: 'created_at', label: 'Created Date' },
    { value: 'title', label: 'Product Title' },
    { value: 'price', label: 'Price' },
    { value: 'rating', label: 'Rating' },
    { value: 'review_count', label: 'Review Count' },
  ];

  const sortOrders = [
    { value: 'asc', label: 'Ascending' },
    { value: 'desc', label: 'Descending' },
  ];

  useEffect(() => {
    fetchPrompts();
    fetchTotalProducts();
  }, []);

  const fetchPrompts = async () => {
    try {
      setLoading(true);
      const response = await api.get('/prompts/');
      setPrompts(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const fetchTotalProducts = async () => {
    try {
      const response = await api.get('/products/count');
      setTotalProducts(response.data.count);
    } catch (err) {
      console.error('Error fetching product count:', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      const requestData = {
        block_title: formData.block_title,
        input_prompt: formData.input_prompt,
        output_example: formData.output_example,
        prompt_category: formData.prompt_category,
        is_active: formData.is_active,
        rerun_on_existing: formData.rerun_on_existing,
        limit: formData.rerun_on_existing ? formData.limit : undefined,
        skip: formData.rerun_on_existing ? formData.skip : undefined,
        sort_field: formData.rerun_on_existing ? formData.sort_field : undefined,
        sort_order: formData.rerun_on_existing ? formData.sort_order : undefined,
        master_recipe_prompt: formData.master_recipe_prompt || undefined,
      };

      if (selectedPrompt) {
        // Update existing prompt
        await api.put(`/prompts/${selectedPrompt.id}/`, requestData);
      } else {
        // Create new prompt
        await api.post('/prompts/', requestData);
      }
      await fetchPrompts();
      setShowForm(false);
      setSelectedPrompt(null);
      setFormData({
        block_title: '',
        input_prompt: '',
        output_example: '',
        prompt_category: '',
        is_active: true,
        rerun_on_existing: false,
        limit: 2000,
        skip: 0,
        sort_field: 'created_at',
        sort_order: 'desc',
        master_recipe_prompt: '',
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value,
    }));
  };

  const handleEdit = (prompt: Prompt) => {
    setSelectedPrompt(prompt);
    setFormData({
      block_title: prompt.block_title,
      input_prompt: prompt.input_prompt,
      output_example: prompt.output_example,
      prompt_category: prompt.prompt_category,
      is_active: prompt.is_active,
      rerun_on_existing: prompt.rerun_on_existing,
      limit: prompt.limit ?? 2000,
      skip: prompt.skip ?? 0,
      sort_field: prompt.sort_field ?? 'created_at',
      sort_order: prompt.sort_order ?? 'desc',
      master_recipe_prompt: prompt.master_recipe_prompt ?? '',
    });
    setShowForm(true);
  };

  const handleView = (prompt: Prompt) => {
    setSelectedPrompt(prompt);
    setShowViewModal(true);
  };

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to delete this prompt?')) {
      try {
        setLoading(true);
        await api.delete(`/prompts/${id}/`);
        await fetchPrompts();
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <Layout>
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-xl font-semibold text-gray-900">Prompts</h1>
        <div className="flex items-center">
          <span className="mr-4 text-sm text-gray-600">
            Total Products: <span className="font-semibold">{totalProducts}</span>
          </span>
          <button
            onClick={() => setShowForm(!showForm)}
            className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <i className="fas fa-plus mr-2"></i>
            Create New Prompt
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md">
          {error}
        </div>
      )}

      {/* Create/Edit Prompt Form */}
      {showForm && (
        <div className="mb-4 bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <h2 className="text-base font-medium text-gray-900 mb-4">
            {selectedPrompt ? 'Edit Prompt' : 'Create New Prompt'}
          </h2>
          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 gap-4">
              <div>
                <label htmlFor="block_title" className="block text-sm font-medium text-gray-700">
                  Title
                </label>
                <input
                  type="text"
                  id="block_title"
                  name="block_title"
                  value={formData.block_title}
                  onChange={handleInputChange}
                  required
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                />
              </div>

              <div>
                <label htmlFor="prompt_category" className="block text-sm font-medium text-gray-700">
                  Category
                </label>
                <select
                  id="prompt_category"
                  name="prompt_category"
                  value={formData.prompt_category}
                  onChange={handleInputChange}
                  required
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                >
                  <option value="">Select a category</option>
                  {categories.map((category) => (
                    <option key={category} value={category}>
                      {category.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="input_prompt" className="block text-sm font-medium text-gray-700">
                  Input Prompt
                </label>
                <textarea
                  id="input_prompt"
                  name="input_prompt"
                  value={formData.input_prompt}
                  onChange={handleInputChange}
                  required
                  rows={6}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  placeholder="Enter the prompt template with placeholders like {{product_data}}"
                />
              </div>

              <div>
                <label htmlFor="output_example" className="block text-sm font-medium text-gray-700">
                  Prompt Response Output
                </label>
                <textarea
                  id="output_example"
                  name="output_example"
                  value={formData.output_example}
                  onChange={handleInputChange}
                  required
                  rows={6}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  placeholder="Example of expected output format"
                />
              </div>

              <div>
                <label htmlFor="master_recipe_prompt" className="block text-sm font-medium text-gray-700">
                  Master Recipe (Optional)
                </label>
                <textarea
                  id="master_recipe_prompt"
                  name="master_recipe_prompt"
                  value={formData.master_recipe_prompt}
                  onChange={handleInputChange}
                  rows={4}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  placeholder="Enter the master recipe for this prompt block (optional)"
                />
              </div>

              <div className="flex items-center space-x-6">
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="is_active"
                    name="is_active"
                    checked={formData.is_active}
                    onChange={handleInputChange}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="is_active" className="ml-2 block text-sm text-gray-900">
                    Active
                  </label>
                </div>

                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="rerun_on_existing"
                    name="rerun_on_existing"
                    checked={formData.rerun_on_existing}
                    onChange={handleInputChange}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="rerun_on_existing" className="ml-2 block text-sm text-gray-900">
                    Rerun on existing products
                  </label>
                </div>
              </div>

              {formData.rerun_on_existing && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="limit" className="block text-sm font-medium text-gray-700">
                        Limit (max products)
                      </label>
                      <input
                        type="number"
                        id="limit"
                        name="limit"
                        value={formData.limit}
                        onChange={handleInputChange}
                        min="1"
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                      />
                    </div>
                    <div>
                      <label htmlFor="skip" className="block text-sm font-medium text-gray-700">
                        Skip (start from)
                      </label>
                      <input
                        type="number"
                        id="skip"
                        name="skip"
                        value={formData.skip}
                        onChange={handleInputChange}
                        min="0"
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label htmlFor="sort_field" className="block text-sm font-medium text-gray-700">
                        Sort By
                      </label>
                      <select
                        id="sort_field"
                        name="sort_field"
                        value={formData.sort_field}
                        onChange={handleInputChange}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                      >
                        {sortFields.map((field) => (
                          <option key={field.value} value={field.value}>
                            {field.label}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label htmlFor="sort_order" className="block text-sm font-medium text-gray-700">
                        Sort Order
                      </label>
                      <select
                        id="sort_order"
                        name="sort_order"
                        value={formData.sort_order}
                        onChange={handleInputChange}
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                      >
                        {sortOrders.map((order) => (
                          <option key={order.value} value={order.value}>
                            {order.label}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                </div>
              )}

              <div className="flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  {loading ? 'Saving...' : 'Save Prompt'}
                </button>
              </div>
            </div>
          </form>
        </div>
      )}

      {/* View Prompt Modal */}
      {showViewModal && selectedPrompt && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full mx-4 max-h-[90vh] overflow-hidden">
            <div className="flex justify-between items-center px-4 py-3 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">{selectedPrompt.block_title}</h3>
              <button
                onClick={() => setShowViewModal(false)}
                className="text-gray-400 hover:text-gray-500"
              >
                <i className="fas fa-times"></i>
              </button>
            </div>
            <div className="p-4 overflow-y-auto">
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-700 mb-1">Category</h4>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-medium ${categoryColors[selectedPrompt.prompt_category]}`}>
                  {selectedPrompt.prompt_category.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                </span>
              </div>
              
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-700 mb-1">Input Prompt</h4>
                <pre className="mt-1 text-sm text-gray-600 whitespace-pre-wrap bg-gray-50 rounded-md p-3 border border-gray-200">
                  {selectedPrompt.input_prompt}
                </pre>
              </div>
              
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-700 mb-1">Output Example</h4>
                <pre className="mt-1 text-sm text-gray-600 whitespace-pre-wrap bg-gray-50 rounded-md p-3 border border-gray-200">
                  {selectedPrompt.output_example}
                </pre>
              </div>
              
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-700 mb-1">Master Recipe</h4>
                <pre className="mt-1 text-sm text-gray-600 whitespace-pre-wrap bg-gray-50 rounded-md p-3 border border-gray-200">
                  {selectedPrompt.master_recipe_prompt || 'No master recipe defined'}
                </pre>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-1">Status</h4>
                  <span
                    className={`px-2 py-0.5 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      selectedPrompt.is_active
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {selectedPrompt.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
                
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-1">Rerun on Existing</h4>
                  <span
                    className={`px-2 py-0.5 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      selectedPrompt.rerun_on_existing
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-gray-100 text-gray-800'
                    }`}
                  >
                    {selectedPrompt.rerun_on_existing ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
              </div>
              
              {selectedPrompt.rerun_on_existing && (
                <div className="mt-4 grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-1">Product Range</h4>
                    <p className="text-sm text-gray-600">
                      Skip: {selectedPrompt.skip ?? 0}<br />
                      Limit: {selectedPrompt.limit ?? 2000}
                    </p>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-1">Sort Settings</h4>
                    <p className="text-sm text-gray-600">
                      Sort by: {sortFields.find(f => f.value === selectedPrompt.sort_field)?.label ?? 'Created Date'}<br />
                      Order: {sortOrders.find(o => o.value === selectedPrompt.sort_order)?.label ?? 'Descending'}
                    </p>
                  </div>
                </div>
              )}
              
              <div className="mt-4">
                <h4 className="text-sm font-medium text-gray-700 mb-1">Products Analyzed</h4>
                <p className="text-sm text-gray-600">{selectedPrompt.analyzed_products_count}</p>
              </div>
            </div>
            <div className="px-4 py-3 bg-gray-50 border-t border-gray-200 flex justify-end space-x-3">
              <button
                onClick={() => setShowViewModal(false)}
                className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Prompts Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th scope="col" className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Title
              </th>
              <th scope="col" className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Category
              </th>
              <th scope="col" className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th scope="col" className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Products Analyzed
              </th>
              <th scope="col" className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Created At
              </th>
              <th scope="col" className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {loading ? (
              <tr>
                <td colSpan={6} className="px-4 py-2 text-center">
                  <div className="flex justify-center">
                    <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-blue-500"></div>
                  </div>
                </td>
              </tr>
            ) : prompts.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-2 text-center text-gray-500">
                  No prompts found
                </td>
              </tr>
            ) : (
              prompts.map((prompt) => (
                <tr key={prompt.id} className="hover:bg-gray-50">
                  <td className="px-4 py-2">
                    <div className="text-sm font-medium text-gray-900">{prompt.block_title}</div>
                  </td>
                  <td className="px-4 py-2">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-sm font-medium ${categoryColors[prompt.prompt_category]}`}>
                      {prompt.prompt_category.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                    </span>
                  </td>
                  <td className="px-4 py-2">
                    <span
                      className={`px-2 py-0.5 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        prompt.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {prompt.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-sm text-gray-500">
                    {prompt.analyzed_products_count}
                  </td>
                  <td className="px-4 py-2 text-sm text-gray-500">
                    {new Date(prompt.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-2 text-sm font-medium">
                    <button
                      onClick={() => handleView(prompt)}
                      className="text-blue-600 hover:text-blue-900 mr-3"
                    >
                      View
                    </button>
                    <button
                      onClick={() => handleEdit(prompt)}
                      className="text-blue-600 hover:text-blue-900 mr-3"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(prompt.id)}
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
    </Layout>
  );
};

export default Prompts; 