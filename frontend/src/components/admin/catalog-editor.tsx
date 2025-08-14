'use client';

import { useState, useEffect } from 'react';
import { useCatalog } from '../../lib/use-catalog';

interface CatalogEditorProps {
  featureFlag?: boolean;
}

export function CatalogEditor({ featureFlag = false }: CatalogEditorProps) {
  const { catalog, version, isLoading, error, mutate } = useCatalog();
  const [jsonInput, setJsonInput] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);
  const [updateStatus, setUpdateStatus] = useState<{
    type: 'success' | 'error' | null;
    message: string;
  }>({ type: null, message: '' });

  // Update JSON input when catalog data changes
  useEffect(() => {
    if (catalog) {
      setJsonInput(JSON.stringify(catalog, null, 2));
    }
  }, [catalog]);

  const handleUpdate = async () => {
    if (!jsonInput.trim()) {
      setUpdateStatus({
        type: 'error',
        message: 'Please enter valid JSON data'
      });
      return;
    }

    try {
      // Validate JSON
      const parsedData = JSON.parse(jsonInput);
      
      setIsUpdating(true);
      setUpdateStatus({ type: null, message: '' });

      const response = await fetch('/api/v1/catalog', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ data: parsedData })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to update catalog');
      }

      const result = await response.json();
      
      setUpdateStatus({
        type: 'success',
        message: `Catalog updated successfully! New version: ${result.version}`
      });

      // Refresh the catalog data
      await mutate();
      
      // Clear success message after 3 seconds
      setTimeout(() => {
        setUpdateStatus({ type: null, message: '' });
      }, 3000);

    } catch (err) {
      setUpdateStatus({
        type: 'error',
        message: err instanceof Error ? err.message : 'Failed to update catalog'
      });
    } finally {
      setIsUpdating(false);
    }
  };

  if (!featureFlag) {
    return null;
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="text-base font-semibold text-gray-900">Catalog Editor</h2>
          <p className="text-sm text-gray-600">Manage printers, materials, and colors</p>
        </div>
        <div className="p-5">
          <div className="flex items-center justify-center p-8">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            <span className="ml-2 text-gray-600">Loading catalog...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="text-base font-semibold text-gray-900">Catalog Editor</h2>
          <p className="text-sm text-gray-600">Manage printers, materials, and colors</p>
        </div>
        <div className="p-5">
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-800">
                  Failed to load catalog: {error.message}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      <div className="px-5 py-4 border-b border-gray-100">
        <h2 className="text-base font-semibold text-gray-900 flex items-center gap-2">
          Catalog Editor
          <span className="text-sm font-normal text-gray-500">
            (Version {version})
          </span>
        </h2>
        <p className="text-sm text-gray-600">
          Edit the catalog configuration. Changes will be applied immediately to all forms.
        </p>
      </div>
      <div className="p-5 space-y-4">
        {updateStatus.type && (
          <div className={`border rounded-md p-4 ${
            updateStatus.type === 'error' 
              ? 'bg-red-50 border-red-200' 
              : 'bg-green-50 border-green-200'
          }`}>
            <div className="flex">
              <div className="flex-shrink-0">
                {updateStatus.type === 'error' ? (
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" clipRule="evenodd" />
                  </svg>
                )}
              </div>
              <div className="ml-3">
                <p className={`text-sm ${
                  updateStatus.type === 'error' ? 'text-red-800' : 'text-green-800'
                }`}>
                  {updateStatus.message}
                </p>
              </div>
            </div>
          </div>
        )}

        <div className="space-y-2">
          <label htmlFor="catalog-json" className="text-sm font-medium text-gray-700">
            Catalog Configuration (JSON)
          </label>
          <textarea
            id="catalog-json"
            value={jsonInput}
            onChange={(e) => setJsonInput(e.target.value)}
            placeholder="Enter catalog JSON configuration..."
            className="w-full border border-gray-300 rounded px-3 py-2 text-sm font-mono h-96 resize-none"
          />
          <p className="text-xs text-gray-500">
            Edit the JSON configuration below. Make sure to maintain the correct structure with methods, printers, and materials.
          </p>
        </div>

        <div className="flex gap-2">
          <button 
            onClick={handleUpdate} 
            disabled={isUpdating}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isUpdating ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            ) : (
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
              </svg>
            )}
            {isUpdating ? 'Updating...' : 'Update Catalog'}
          </button>
          
          <button 
            onClick={() => setJsonInput(JSON.stringify(catalog, null, 2))}
            disabled={isUpdating}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Reset to Current
          </button>
        </div>

        <div className="text-xs text-gray-500 space-y-1">
          <p><strong>Note:</strong> This feature is behind a feature flag and only available to administrators.</p>
          <p><strong>Validation:</strong> The system will validate your JSON before applying changes.</p>
          <p><strong>Versioning:</strong> Each update increments the version number for tracking changes.</p>
        </div>
      </div>
    </div>
  );
}
