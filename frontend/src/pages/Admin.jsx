import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import apiService from '../services/api';

const Admin = () => {
  const { isAdmin, isAuthenticated } = useAuth();
  const [configs, setConfigs] = useState([]);
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [datasetsLoading, setDatasetsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editingConfig, setEditingConfig] = useState(null);
  const [editValue, setEditValue] = useState('');
  const [uploadLoading, setUploadLoading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(null);
  const [includeInactive, setIncludeInactive] = useState(true); // Show inactive datasets by default in admin
  
  // Ranking configuration state
  const [rankingConfig, setRankingConfig] = useState({
    accuracy_min_cards: 5,
    speed_min_cards: 10,
    cards_answered_min_threshold: 20
  });
  const [rankingLoading, setRankingLoading] = useState(false);

  // FSRS Integration configuration state
  const [fsrsConfig, setFsrsConfig] = useState(null);
  const [fsrsLoading, setFsrsLoading] = useState(false);
  const [fsrsError, setFsrsError] = useState(null);

  useEffect(() => {
    if (isAuthenticated && isAdmin) {
      fetchConfigs();
      fetchDatasets();
      fetchRankingConfig();
      fetchFsrsConfig();
    }
  }, [isAuthenticated, isAdmin, includeInactive]);

  const fetchConfigs = async () => {
    try {
      setLoading(true);
      const response = await apiService.get('/admin/config');
      setConfigs(response);
      setError(null);
    } catch (err) {
      setError('Failed to fetch configurations');
      console.error('Error fetching configs:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchRankingConfig = async () => {
    try {
      const response = await apiService.get('/admin/config/ranking');
      setRankingConfig(response);
    } catch (err) {
      console.error('Error fetching ranking config:', err);
      // Initialize with defaults if API fails
      setRankingConfig({
        accuracy_min_cards: 5,
        speed_min_cards: 10,
        cards_answered_min_threshold: 20
      });
    }
  };

  const fetchFsrsConfig = async () => {
    try {
      setFsrsLoading(true);
      setFsrsError(null);
      const response = await apiService.get('/admin/config/integration');
      setFsrsConfig(response);
    } catch (err) {
      setFsrsError('Failed to fetch FSRS configuration');
      console.error('Error fetching FSRS config:', err);
    } finally {
      setFsrsLoading(false);
    }
  };

  const fetchDatasets = async () => {
    try {
      setDatasetsLoading(true);
      console.log('Fetching datasets with includeInactive:', includeInactive);
      const response = await apiService.getAllDatasets(includeInactive);
      console.log('Datasets response:', response);
      setDatasets(response);
    } catch (err) {
      setError('Failed to fetch datasets');
      console.error('Error fetching datasets:', err);
    } finally {
      setDatasetsLoading(false);
    }
  };

  const handleToggleDataset = async (datasetId) => {
    try {
      console.log('Toggling dataset:', datasetId);
      
      // Optimistic update - immediately update the UI
      setDatasets(prevDatasets => 
        prevDatasets.map(dataset => 
          dataset.id === datasetId 
            ? { ...dataset, is_active: !dataset.is_active }
            : dataset
        )
      );
      
      const result = await apiService.toggleDatasetStatus(datasetId);
      console.log('Toggle result:', result);
      
      // Clear any previous errors
      setError(null);
      
      // Refresh the list from server to ensure consistency
      await fetchDatasets();
    } catch (err) {
      setError(`Failed to toggle dataset status: ${err.message}`);
      console.error('Error toggling dataset:', err);
      
      // Revert the optimistic update on error
      await fetchDatasets();
    }
  };

  const handleDeleteDataset = async (datasetId, datasetName) => {
    if (!window.confirm(`Are you sure you want to delete the dataset "${datasetName}"? This action cannot be undone.`)) {
      return;
    }

    try {
      await apiService.deleteDataset(datasetId);
      fetchDatasets(); // Refresh the list
    } catch (err) {
      setError('Failed to delete dataset');
      console.error('Error deleting dataset:', err);
    }
  };

  const handleEdit = (config) => {
    setEditingConfig(config.key);
    setEditValue(config.value);
  };

  const handleSave = async (key) => {
    try {
      const config = configs.find(c => c.key === key);
      let parsedValue = editValue;
      
      // Parse value based on type
      if (config.type === 'integer') {
        parsedValue = parseInt(editValue);
      } else if (config.type === 'float') {
        parsedValue = parseFloat(editValue);
      } else if (config.type === 'boolean') {
        parsedValue = editValue === 'true';
      }

      await apiService.put(`/admin/config/${key}`, {
        value: parsedValue,
        description: config.description,
        category: config.category,
        type: config.type
      });

      setEditingConfig(null);
      setEditValue('');
      fetchConfigs(); // Refresh the list
    } catch (err) {
      setError('Failed to update configuration');
      console.error('Error updating config:', err);
    }
  };

  const handleCancel = () => {
    setEditingConfig(null);
    setEditValue('');
  };

  const resetLearningConfig = async () => {
    try {
      await apiService.post('/admin/config/learning/reset');
      fetchConfigs(); // Refresh the list
    } catch (err) {
      setError('Failed to reset learning configuration');
      console.error('Error resetting config:', err);
    }
  };

  const updateRankingConfig = async (updatedConfig) => {
    try {
      setRankingLoading(true);
      const response = await apiService.put('/admin/config/ranking', updatedConfig);
      setRankingConfig(response);
      setError(null);
    } catch (err) {
      setError('Failed to update ranking configuration');
      console.error('Error updating ranking config:', err);
    } finally {
      setRankingLoading(false);
    }
  };

  const resetRankingConfig = async () => {
    try {
      setRankingLoading(true);
      const response = await apiService.post('/admin/config/ranking/reset');
      setRankingConfig(response);
      setError(null);
    } catch (err) {
      setError('Failed to reset ranking configuration');
      console.error('Error resetting ranking config:', err);
    } finally {
      setRankingLoading(false);
    }
  };

  const handleRankingConfigChange = (field, value) => {
    const numValue = parseInt(value);
    if (isNaN(numValue) || numValue < 1) return;
    
    const updatedConfig = {
      ...rankingConfig,
      [field]: numValue
    };
    setRankingConfig(updatedConfig);
    updateRankingConfig({ [field]: numValue });
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.name.endsWith('.json')) {
      setError('Please select a JSON file');
      return;
    }

    try {
      setUploadLoading(true);
      setError(null);
      setUploadSuccess(null);

      const response = await apiService.uploadDataset(file);
      // Use the detailed upload summary if available, otherwise fallback to element count
      const message = response.upload_summary 
        ? `Dataset "${response.name}" uploaded successfully! ${response.upload_summary}`
        : `Dataset "${response.name}" uploaded successfully! Contains ${response.element_count || response.elements_created || 0} elements.`;
      setUploadSuccess(message);
      
      // Clear the file input
      event.target.value = '';
    } catch (err) {
      setError(`Upload failed: ${err.message || 'Unknown error'}`);
      console.error('Error uploading dataset:', err);
    } finally {
      setUploadLoading(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Access Denied</h2>
          <p className="text-gray-600">Please log in to access the admin panel.</p>
        </div>
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Admin Access Required</h2>
          <p className="text-gray-600">You need admin privileges to access this page.</p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600">Loading admin panel...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">System Administration</h1>
        <p className="text-gray-600">Manage system configurations and settings</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">{error}</div>
            </div>
          </div>
        </div>
      )}

      {uploadSuccess && (
        <div className="bg-green-50 border border-green-200 rounded-md p-4 mb-6">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-green-800">Success</h3>
              <div className="mt-2 text-sm text-green-700">{uploadSuccess}</div>
            </div>
          </div>
        </div>
      )}

      {/* Dataset Upload Section */}
      <div className="bg-white shadow rounded-lg mb-8">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Dataset Upload</h2>
          <p className="text-sm text-gray-600 mt-1">Upload flashcard datasets from JSON files</p>
        </div>
        
        <div className="p-6">
          <div className="flex items-center justify-center w-full">
            <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100 hover:border-gray-400 transition-colors">
              <div className="flex flex-col items-center justify-center pt-5 pb-6">
                <svg className="w-8 h-8 mb-4 text-gray-500" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 20 16">
                  <path stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 13h3a3 3 0 0 0 0-6h-.025A5.56 5.56 0 0 0 16 6.5 5.5 5.5 0 0 0 5.207 5.021C5.137 5.017 5.071 5 5 5a4 4 0 0 0 0 8h2.167M10 15V6m0 0L8 8m2-2 2 2"/>
                </svg>
                <p className="mb-2 text-sm text-gray-500">
                  <span className="font-semibold">Click to upload</span> or drag and drop
                </p>
                <p className="text-xs text-gray-500">JSON files only</p>
              </div>
              <input 
                type="file" 
                className="hidden" 
                accept=".json"
                onChange={handleFileUpload}
                disabled={uploadLoading}
              />
            </label>
          </div>
          
          {uploadLoading && (
            <div className="mt-4 flex items-center justify-center">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mr-3"></div>
              <span className="text-sm text-gray-600">Uploading dataset...</span>
            </div>
          )}
        </div>
      </div>

      {/* Enhanced Card-Based Configuration Interface */}
      <div className="bg-white shadow rounded-lg mb-8">
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">🎛️ Enhanced Configuration Panel</h2>
            <p className="text-sm text-gray-600 mt-1">User-friendly view of all system parameters organized by category</p>
          </div>
          <div className="flex items-center space-x-3">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
              ✨ New Interface
            </span>
          </div>
        </div>

        <div className="p-6">
          {/* Group configs by category */}
          {['learning', 'ranking', 'fsrs_integration', 'fsrs_mastery'].map((category) => {
            const categoryConfigs = configs.filter(config => config.category === category);
            if (categoryConfigs.length === 0) return null;

            const categoryInfo = {
              learning: { 
                name: 'Learning Parameters', 
                description: 'Core learning algorithm settings',
                color: 'blue',
                icon: '📚'
              },
              ranking: { 
                name: 'Ranking Settings', 
                description: 'Leaderboard and ranking thresholds',
                color: 'purple',
                icon: '🏆'
              },
              fsrs_integration: { 
                name: 'FSRS Integration', 
                description: 'Spaced repetition integration settings',
                color: 'green',
                icon: '🧠'
              },
              fsrs_mastery: { 
                name: 'FSRS Mastery', 
                description: 'Mastery calculation parameters',
                color: 'amber',
                icon: '⭐'
              }
            };

            const info = categoryInfo[category];
            const colorClasses = {
              blue: 'border-blue-200 bg-blue-50',
              purple: 'border-purple-200 bg-purple-50',
              green: 'border-green-200 bg-green-50',
              amber: 'border-amber-200 bg-amber-50'
            };

            return (
              <div key={category} className={`mb-8 border rounded-lg ${colorClasses[info.color]}`}>
                <div className="px-4 py-3 border-b border-gray-200 bg-white rounded-t-lg">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <span className="text-xl mr-3">{info.icon}</span>
                      <div>
                        <h3 className="text-lg font-medium text-gray-900">{info.name}</h3>
                        <p className="text-sm text-gray-600">{info.description}</p>
                      </div>
                    </div>
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                      {categoryConfigs.length} settings
                    </span>
                  </div>
                </div>
                
                <div className="p-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {categoryConfigs.map((config) => (
                      <div key={config.key} className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
                        <div className="flex justify-between items-start mb-3">
                          <div className="flex-1">
                            <h4 className="text-sm font-semibold text-gray-900 mb-1">
                              {config.key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                            </h4>
                            <p className="text-xs text-gray-500 mb-3 leading-relaxed">
                              {config.description}
                            </p>
                          </div>
                        </div>
                        
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center space-x-2">
                            {editingConfig === config.key ? (
                              <div className="flex items-center space-x-2">
                                <input
                                  type={config.type === 'boolean' ? 'text' : config.type === 'integer' ? 'number' : 'text'}
                                  value={editValue}
                                  onChange={(e) => setEditValue(e.target.value)}
                                  className="border border-gray-300 rounded-md px-3 py-1 text-sm w-24 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                  autoFocus
                                />
                                <button
                                  onClick={handleSave}
                                  className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded-md text-xs font-medium"
                                >
                                  ✓
                                </button>
                                <button
                                  onClick={handleCancel}
                                  className="bg-gray-500 hover:bg-gray-600 text-white px-3 py-1 rounded-md text-xs font-medium"
                                >
                                  ✕
                                </button>
                              </div>
                            ) : (
                              <>
                                <span className={`inline-flex px-3 py-1.5 text-sm font-medium rounded-full ${
                                  config.type === 'boolean' 
                                    ? config.value === 'true' || config.value === true
                                      ? 'bg-green-100 text-green-800' 
                                      : 'bg-red-100 text-red-800'
                                    : config.type === 'float'
                                    ? 'bg-blue-100 text-blue-800'
                                    : config.type === 'integer'
                                    ? 'bg-purple-100 text-purple-800'
                                    : 'bg-gray-100 text-gray-800'
                                }`}>
                                  {config.type === 'boolean' 
                                    ? (config.value === 'true' || config.value === true ? '✓ Enabled' : '✗ Disabled')
                                    : config.type === 'float' && config.key.includes('percentage')
                                    ? `${(parseFloat(config.value) * 100).toFixed(0)}%`
                                    : config.value?.toString()}
                                </span>
                                <button
                                  onClick={() => handleEdit(config)}
                                  className="text-blue-600 hover:text-blue-900 text-sm font-medium bg-blue-50 hover:bg-blue-100 px-3 py-1 rounded-md transition-colors"
                                >
                                  Edit
                                </button>
                              </>
                            )}
                          </div>
                        </div>
                        
                        <div className="flex items-center justify-between text-xs">
                          <span className={`px-2 py-1 rounded-full font-medium ${
                            config.type === 'boolean' ? 'bg-green-50 text-green-600' :
                            config.type === 'float' ? 'bg-blue-50 text-blue-600' :
                            config.type === 'integer' ? 'bg-purple-50 text-purple-600' :
                            'bg-gray-50 text-gray-600'
                          }`}>
                            {config.type}
                          </span>
                          <span className="text-gray-400">
                            {config.updated_at ? new Date(config.updated_at).toLocaleDateString() : 'Default'}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            );
          })}

          {/* Show uncategorized configs if any */}
          {(() => {
            const uncategorizedConfigs = configs.filter(config => 
              !['learning', 'ranking', 'fsrs_integration', 'fsrs_mastery'].includes(config.category)
            );
            
            if (uncategorizedConfigs.length === 0) return null;
            
            return (
              <div className="border border-gray-200 bg-gray-50 rounded-lg">
                <div className="px-4 py-3 border-b border-gray-200 bg-white rounded-t-lg">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <span className="text-xl mr-3">⚙️</span>
                      <div>
                        <h3 className="text-lg font-medium text-gray-900">Other Settings</h3>
                        <p className="text-sm text-gray-600">Miscellaneous configuration parameters</p>
                      </div>
                    </div>
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                      {uncategorizedConfigs.length} settings
                    </span>
                  </div>
                </div>
                
                <div className="p-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {uncategorizedConfigs.map((config) => (
                      <div key={config.key} className="bg-white rounded-lg p-4 border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
                        <div className="flex justify-between items-start mb-3">
                          <div className="flex-1">
                            <h4 className="text-sm font-semibold text-gray-900 mb-1">
                              {config.key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                            </h4>
                            <p className="text-xs text-gray-500 mb-3 leading-relaxed">
                              {config.description}
                            </p>
                          </div>
                        </div>
                        
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center space-x-2">
                            {editingConfig === config.key ? (
                              <div className="flex items-center space-x-2">
                                <input
                                  type={config.type === 'boolean' ? 'text' : config.type === 'integer' ? 'number' : 'text'}
                                  value={editValue}
                                  onChange={(e) => setEditValue(e.target.value)}
                                  className="border border-gray-300 rounded-md px-3 py-1 text-sm w-24 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                  autoFocus
                                />
                                <button
                                  onClick={handleSave}
                                  className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded-md text-xs font-medium"
                                >
                                  ✓
                                </button>
                                <button
                                  onClick={handleCancel}
                                  className="bg-gray-500 hover:bg-gray-600 text-white px-3 py-1 rounded-md text-xs font-medium"
                                >
                                  ✕
                                </button>
                              </div>
                            ) : (
                              <>
                                <span className={`inline-flex px-3 py-1.5 text-sm font-medium rounded-full ${
                                  config.type === 'boolean' 
                                    ? config.value === 'true' || config.value === true
                                      ? 'bg-green-100 text-green-800' 
                                      : 'bg-red-100 text-red-800'
                                    : config.type === 'float'
                                    ? 'bg-blue-100 text-blue-800'
                                    : config.type === 'integer'
                                    ? 'bg-purple-100 text-purple-800'
                                    : 'bg-gray-100 text-gray-800'
                                }`}>
                                  {config.type === 'boolean' 
                                    ? (config.value === 'true' || config.value === true ? '✓ Enabled' : '✗ Disabled')
                                    : config.type === 'float' && config.key.includes('percentage')
                                    ? `${(parseFloat(config.value) * 100).toFixed(0)}%`
                                    : config.value?.toString()}
                                </span>
                                <button
                                  onClick={() => handleEdit(config)}
                                  className="text-blue-600 hover:text-blue-900 text-sm font-medium bg-blue-50 hover:bg-blue-100 px-3 py-1 rounded-md transition-colors"
                                >
                                  Edit
                                </button>
                              </>
                            )}
                          </div>
                        </div>
                        
                        <div className="flex items-center justify-between text-xs">
                          <span className={`px-2 py-1 rounded-full font-medium ${
                            config.type === 'boolean' ? 'bg-green-50 text-green-600' :
                            config.type === 'float' ? 'bg-blue-50 text-blue-600' :
                            config.type === 'integer' ? 'bg-purple-50 text-purple-600' :
                            'bg-gray-50 text-gray-600'
                          }`}>
                            {config.type}
                          </span>
                          <span className="text-gray-400">
                            {config.updated_at ? new Date(config.updated_at).toLocaleDateString() : 'Default'}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            );
          })()}
        </div>
      </div>

      {/* Legacy Table View (for comparison) */}
      <div className="bg-white shadow rounded-lg mb-8">
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">📋 Legacy Table View</h2>
            <p className="text-sm text-gray-600 mt-1">Traditional table format (for technical reference)</p>
          </div>
        </div>
        <div className="p-4">
          <details className="cursor-pointer">
            <summary className="text-sm text-gray-600 hover:text-gray-800 font-medium">
              Click to show/hide detailed table view
            </summary>
            <div className="mt-4 overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Key</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Value</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Category</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {configs.map((config) => (
                    <tr key={`table-${config.key}`} className="hover:bg-gray-50">
                      <td className="px-3 py-2 text-xs font-mono text-gray-900">{config.key}</td>
                      <td className="px-3 py-2 text-xs text-gray-900">{config.value?.toString()}</td>
                      <td className="px-3 py-2 text-xs text-gray-500">{config.type}</td>
                      <td className="px-3 py-2 text-xs text-gray-500">{config.category}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        </div>
      </div>

      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-lg font-semibold text-gray-900">System Configurations</h2>
          <button
            onClick={resetLearningConfig}
            className="bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded-md text-sm font-medium"
          >
            Reset Learning Config
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Key
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Value
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Category
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Description
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {configs.map((config) => (
                <tr key={config.key}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {config.key}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {editingConfig === config.key ? (
                      <input
                        type={config.type === 'boolean' ? 'text' : config.type === 'integer' ? 'number' : 'text'}
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                        className="border border-gray-300 rounded px-2 py-1 text-sm w-24"
                        autoFocus
                      />
                    ) : (
                      <span className={`inline-flex px-2 py-1 text-xs rounded-full ${
                        config.type === 'boolean' 
                          ? config.value ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {config.value?.toString()}
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <span className="inline-flex px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
                      {config.type}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <span className="inline-flex px-2 py-1 text-xs rounded-full bg-purple-100 text-purple-800">
                      {config.category}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                    {config.description}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    {editingConfig === config.key ? (
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleSave(config.key)}
                          className="text-green-600 hover:text-green-900"
                        >
                          Save
                        </button>
                        <button
                          onClick={handleCancel}
                          className="text-gray-600 hover:text-gray-900"
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => handleEdit(config)}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        Edit
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Ranking Configuration Section */}
      <div className="bg-white shadow rounded-lg mb-8">
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Ranking Thresholds</h2>
            <p className="text-sm text-gray-600 mt-1">Configure minimum thresholds for leaderboard rankings</p>
          </div>
          <button
            onClick={resetRankingConfig}
            disabled={rankingLoading}
            className="bg-yellow-600 hover:bg-yellow-700 disabled:bg-yellow-400 text-white px-4 py-2 rounded-md text-sm font-medium flex items-center"
          >
            {rankingLoading && (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
            )}
            Reset Ranking Config
          </button>
        </div>

        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Accuracy Ranking Threshold */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">
                Accuracy Ranking Threshold
              </label>
              <p className="text-xs text-gray-500 mb-3">
                Minimum cards answered to appear in accuracy leaderboard
              </p>
              <div className="flex items-center space-x-3">
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={rankingConfig.accuracy_min_cards}
                  onChange={(e) => handleRankingConfigChange('accuracy_min_cards', e.target.value)}
                  disabled={rankingLoading}
                  className="block w-20 border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                />
                <span className="text-sm text-gray-600">cards minimum</span>
              </div>
            </div>

            {/* Speed Ranking Threshold */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">
                Speed Ranking Threshold
              </label>
              <p className="text-xs text-gray-500 mb-3">
                Minimum cards answered to appear in speed leaderboard
              </p>
              <div className="flex items-center space-x-3">
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={rankingConfig.speed_min_cards}
                  onChange={(e) => handleRankingConfigChange('speed_min_cards', e.target.value)}
                  disabled={rankingLoading}
                  className="block w-20 border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                />
                <span className="text-sm text-gray-600">cards minimum</span>
              </div>
            </div>

            {/* General Leaderboard Threshold */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">
                General Leaderboard Threshold
              </label>
              <p className="text-xs text-gray-500 mb-3">
                Minimum cards answered to appear in any leaderboard
              </p>
              <div className="flex items-center space-x-3">
                <input
                  type="number"
                  min="1"
                  max="1000"
                  value={rankingConfig.cards_answered_min_threshold}
                  onChange={(e) => handleRankingConfigChange('cards_answered_min_threshold', e.target.value)}
                  disabled={rankingLoading}
                  className="block w-20 border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                />
                <span className="text-sm text-gray-600">cards minimum</span>
              </div>
            </div>
          </div>

          <div className="mt-6 bg-blue-50 border border-blue-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-blue-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-blue-800">
                  Threshold Information
                </h3>
                <div className="mt-2 text-sm text-blue-700">
                  <p>These thresholds determine when users appear in rankings:</p>
                  <ul className="mt-1 list-disc list-inside">
                    <li><strong>Accuracy Ranking:</strong> Users need {rankingConfig.accuracy_min_cards} correct/incorrect answers</li>
                    <li><strong>Speed Ranking:</strong> Users need {rankingConfig.speed_min_cards} timed answers</li>
                    <li><strong>Cards Answered:</strong> Users need {rankingConfig.cards_answered_min_threshold} total answers</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* FSRS Integration Configuration Section */}
      <div className="bg-white shadow rounded-lg mb-8">
        <div className="px-6 py-4 border-b border-gray-200">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">FSRS Integration Configuration</h2>
            <p className="text-sm text-gray-600 mt-1">Configure Free Spaced Repetition Scheduler (FSRS) integration settings</p>
          </div>
        </div>

        {fsrsError && (
          <div className="m-6 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error</h3>
                <div className="mt-2 text-sm text-red-700">{fsrsError}</div>
              </div>
            </div>
          </div>
        )}

        {fsrsLoading ? (
          <div className="p-6 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading FSRS configuration...</p>
          </div>
        ) : fsrsConfig ? (
          <div className="p-6">
            {/* FSRS Integration Parameters */}
            <div className="mb-8">
              <h3 className="text-md font-medium text-gray-900 mb-4">Integration Parameters</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Integration Enabled
                  </label>
                  <div className="flex items-center">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      fsrsConfig.integration_enhancement_enabled 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {fsrsConfig.integration_enhancement_enabled ? 'Enabled' : 'Disabled'}
                    </span>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Integration Threshold
                  </label>
                  <div className="text-sm text-gray-900">
                    {(fsrsConfig.integration_confirmation_threshold * 100).toFixed(0)}%
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Max Attempts
                  </label>
                  <div className="text-sm text-gray-900">
                    {fsrsConfig.integration_max_attempts}
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Stability Boost Factor
                  </label>
                  <div className="text-sm text-gray-900">
                    {fsrsConfig.stability_boost_factor}x
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Reconsolidation Threshold
                  </label>
                  <div className="text-sm text-gray-900">
                    {fsrsConfig.reconsolidation_threshold} failures
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Max Stability Score
                  </label>
                  <div className="text-sm text-gray-900">
                    {fsrsConfig.stability_max_score}
                  </div>
                </div>
              </div>
            </div>

            {/* FSRS Mastery Parameters */}
            <div className="mb-6">
              <h3 className="text-md font-medium text-gray-900 mb-4">Mastery Parameters</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Integration Mastery Window
                  </label>
                  <div className="text-sm text-gray-900">
                    {fsrsConfig.integration_mastery_window} attempts
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Isolation Min Window
                  </label>
                  <div className="text-sm text-gray-900">
                    {fsrsConfig.isolation_min_mastery_window} attempts
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Isolation Max Window
                  </label>
                  <div className="text-sm text-gray-900">
                    {fsrsConfig.isolation_max_mastery_window} attempts
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Isolation Mastery %
                  </label>
                  <div className="text-sm text-gray-900">
                    {(fsrsConfig.isolation_mastery_percentage * 100).toFixed(0)}%
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Single Field Window
                  </label>
                  <div className="text-sm text-gray-900">
                    {fsrsConfig.single_field_mastery_window} attempts
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="block text-sm font-medium text-gray-700">
                    Two Field Window
                  </label>
                  <div className="text-sm text-gray-900">
                    {fsrsConfig.two_field_mastery_window} attempts
                  </div>
                </div>
              </div>
            </div>

            {/* Info Box */}
            <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-blue-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-blue-800">
                    FSRS Integration Information
                  </h3>
                  <div className="mt-2 text-sm text-blue-700">
                    <p>FSRS Integration solves the "re-mastery" problem by implementing intelligent card progression:</p>
                    <ul className="mt-1 list-disc list-inside">
                      <li><strong>Integration Phase:</strong> Previously mastered cards tested in mixed context</li>
                      <li><strong>Stability Scoring:</strong> Dynamic difficulty adjustment based on performance</li>
                      <li><strong>Graduated Mastery:</strong> Reduces redundant repetition of already learned cards</li>
                      <li><strong>Reconsolidation:</strong> Failed cards return to isolation for re-learning</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="p-6 text-center text-gray-500">
            Failed to load FSRS configuration
          </div>
        )}
      </div>

      {/* Dataset Management Section */}
      <div className="bg-white shadow rounded-lg mb-8">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Dataset Management</h2>
              <p className="text-sm text-gray-600 mt-1">Manage datasets, enable/disable, and delete</p>
            </div>
            <div className="flex items-center space-x-4">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={includeInactive}
                  onChange={(e) => {
                    setIncludeInactive(e.target.checked);
                    fetchDatasets();
                  }}
                  className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                />
                <span className="ml-2 text-sm text-gray-700">Show inactive</span>
              </label>
            </div>
          </div>
        </div>
        
        <div className="overflow-x-auto">
          {datasetsLoading ? (
            <div className="p-8 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading datasets...</p>
            </div>
          ) : datasets.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              No datasets found
            </div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Dataset
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Elements
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
                {datasets.map((dataset) => (
                  <tr key={dataset.id} className={!dataset.is_active ? 'bg-gray-50' : ''}>
                    <td className="px-6 py-4">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{dataset.name}</div>
                        {dataset.description && (
                          <div className="text-sm text-gray-500 truncate max-w-xs">{dataset.description}</div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs rounded-full ${
                        dataset.is_active 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {dataset.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {dataset.metadata.element_count}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(dataset.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex space-x-3">
                        <button
                          onClick={() => handleToggleDataset(dataset.id)}
                          className={`${
                            dataset.is_active 
                              ? 'text-orange-600 hover:text-orange-900' 
                              : 'text-green-600 hover:text-green-900'
                          }`}
                        >
                          {dataset.is_active ? 'Disable' : 'Enable'}
                        </button>
                        <button
                          onClick={() => handleDeleteDataset(dataset.id, dataset.name)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-md p-4">
        <h3 className="text-sm font-medium text-blue-800 mb-2">Configuration Help</h3>
        <ul className="text-sm text-blue-700 space-y-1">
          <li><strong>max_set_size:</strong> Maximum number of flashcards in a learning set</li>
          <li><strong>initial_set_size:</strong> Starting number of flashcards for new users</li>
          <li><strong>mastery_threshold:</strong> Number of consecutive correct answers needed to mark an element as mastered</li>
          <li><strong>stage_increment:</strong> How many cards to add when advancing to next stage</li>
        </ul>
      </div>
    </div>
  );
};

export default Admin;
