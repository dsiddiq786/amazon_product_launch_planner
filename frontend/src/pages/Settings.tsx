import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import api from '../services/api';

interface Settings {
  website: {
    site_name: string;
    site_description: string;
    contact_email: string;
    support_email: string;
    logo_url: string;
    favicon_url: string;
  };
  admin: {
    admin_email: string;
    admin_phone: string;
    notification_email: string;
    maintenance_mode: boolean;
  };
  scraper: {
    max_concurrent_scrapes: number;
    scrape_timeout: number;
    retry_attempts: number;
    proxy_enabled: boolean;
    proxy_list: string;
    user_agent: string;
  };
  ai: {
    gemini_api_key: string;
    openai_api_key: string;
    max_tokens: number;
    temperature: number;
    model_name: string;
  };
}

const Settings: React.FC = () => {
  const [settings, setSettings] = useState<Settings>({
    website: {
      site_name: '',
      site_description: '',
      contact_email: '',
      support_email: '',
      logo_url: '',
      favicon_url: '',
    },
    admin: {
      admin_email: '',
      admin_phone: '',
      notification_email: '',
      maintenance_mode: false,
    },
    scraper: {
      max_concurrent_scrapes: 5,
      scrape_timeout: 30,
      retry_attempts: 3,
      proxy_enabled: false,
      proxy_list: '',
      user_agent: '',
    },
    ai: {
      gemini_api_key: '',
      openai_api_key: '',
      max_tokens: 1000,
      temperature: 0.7,
      model_name: 'gemini-pro',
    },
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      const response = await api.get('/settings/');
      setSettings(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      await api.put('/settings/', settings);
      setSuccess('Settings saved successfully');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (section: keyof Settings, field: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [field]: value
      }
    }));
  };

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-semibold text-gray-900">System Settings</h1>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md">
            {error}
          </div>
        )}

        {success && (
          <div className="mb-4 p-3 bg-green-50 text-green-700 rounded-md">
            {success}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Website Settings */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-medium mb-4">Website Settings</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Site Name</label>
                <input
                  type="text"
                  value={settings.website.site_name}
                  onChange={(e) => handleChange('website', 'site_name', e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Site Description</label>
                <input
                  type="text"
                  value={settings.website.site_description}
                  onChange={(e) => handleChange('website', 'site_description', e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Contact Email</label>
                <input
                  type="email"
                  value={settings.website.contact_email}
                  onChange={(e) => handleChange('website', 'contact_email', e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Support Email</label>
                <input
                  type="email"
                  value={settings.website.support_email}
                  onChange={(e) => handleChange('website', 'support_email', e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Logo URL</label>
                <input
                  type="url"
                  value={settings.website.logo_url}
                  onChange={(e) => handleChange('website', 'logo_url', e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Favicon URL</label>
                <input
                  type="url"
                  value={settings.website.favicon_url}
                  onChange={(e) => handleChange('website', 'favicon_url', e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Admin Panel Settings */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-medium mb-4">Admin Panel Settings</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Admin Email</label>
                <input
                  type="email"
                  value={settings.admin.admin_email}
                  onChange={(e) => handleChange('admin', 'admin_email', e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Admin Phone</label>
                <input
                  type="tel"
                  value={settings.admin.admin_phone}
                  onChange={(e) => handleChange('admin', 'admin_phone', e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Notification Email</label>
                <input
                  type="email"
                  value={settings.admin.notification_email}
                  onChange={(e) => handleChange('admin', 'notification_email', e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.admin.maintenance_mode}
                  onChange={(e) => handleChange('admin', 'maintenance_mode', e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label className="ml-2 block text-sm text-gray-700">Maintenance Mode</label>
              </div>
            </div>
          </div>

          {/* Scraper Settings */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-medium mb-4">Scraper Settings</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Max Concurrent Scrapes</label>
                <input
                  type="number"
                  value={settings.scraper.max_concurrent_scrapes}
                  onChange={(e) => handleChange('scraper', 'max_concurrent_scrapes', parseInt(e.target.value))}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Scrape Timeout (seconds)</label>
                <input
                  type="number"
                  value={settings.scraper.scrape_timeout}
                  onChange={(e) => handleChange('scraper', 'scrape_timeout', parseInt(e.target.value))}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Retry Attempts</label>
                <input
                  type="number"
                  value={settings.scraper.retry_attempts}
                  onChange={(e) => handleChange('scraper', 'retry_attempts', parseInt(e.target.value))}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.scraper.proxy_enabled}
                  onChange={(e) => handleChange('scraper', 'proxy_enabled', e.target.checked)}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label className="ml-2 block text-sm text-gray-700">Enable Proxy</label>
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700">Proxy List (one per line)</label>
                <textarea
                  value={settings.scraper.proxy_list}
                  onChange={(e) => handleChange('scraper', 'proxy_list', e.target.value)}
                  rows={3}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700">User Agent</label>
                <input
                  type="text"
                  value={settings.scraper.user_agent}
                  onChange={(e) => handleChange('scraper', 'user_agent', e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          {/* AI Tool Settings */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-medium mb-4">AI Tool Settings</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Gemini API Key</label>
                <input
                  type="password"
                  value={settings.ai.gemini_api_key}
                  onChange={(e) => handleChange('ai', 'gemini_api_key', e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">OpenAI API Key</label>
                <input
                  type="password"
                  value={settings.ai.openai_api_key}
                  onChange={(e) => handleChange('ai', 'openai_api_key', e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Max Tokens</label>
                <input
                  type="number"
                  value={settings.ai.max_tokens}
                  onChange={(e) => handleChange('ai', 'max_tokens', parseInt(e.target.value))}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Temperature</label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="1"
                  value={settings.ai.temperature}
                  onChange={(e) => handleChange('ai', 'temperature', parseFloat(e.target.value))}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Model Name</label>
                <input
                  type="text"
                  value={settings.ai.model_name}
                  onChange={(e) => handleChange('ai', 'model_name', e.target.value)}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
              </div>
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {loading ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
        </form>
      </div>
    </Layout>
  );
};

export default Settings; 