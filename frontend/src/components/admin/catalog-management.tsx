'use client';

import { useState, useEffect } from 'react';
import { useCatalog } from '../../lib/use-catalog';
import { apiClient } from '../../lib/unified-api-client';
import { useToast } from '../ui/toast';
import { Plus, Edit2, Trash2, Package, Settings, Palette } from 'lucide-react';

interface Printer {
  id: string;
  name: string;
  supported_methods: string[];
  is_active: boolean;
}

interface Material {
  id: string;
  method: string;
  name: string;
  unit_cost_per_g_cents: number;
  colors: string[];
  is_active: boolean;
}

type EditingMode = 'printer' | 'material' | 'color' | null;

export function CatalogManagement() {
  const { catalog, version, isLoading, error, mutate } = useCatalog();
  const [activeTab, setActiveTab] = useState<'printers' | 'materials'>('printers');
  const [editingMode, setEditingMode] = useState<EditingMode>(null);
  const [isUpdating, setIsUpdating] = useState(false);
  const { show } = useToast();

  // Printer editing state
  const [newPrinter, setNewPrinter] = useState({
    id: '',
    name: '',
    supported_methods: [] as string[],
    is_active: true
  });

  // Material editing state  
  const [newMaterial, setNewMaterial] = useState({
    id: '',
    method: '',
    name: '',
    unit_cost_per_g_cents: 10,
    colors: [] as string[],
    is_active: true
  });

  const [newColor, setNewColor] = useState('');
  const [editingMaterial, setEditingMaterial] = useState<string | null>(null);

  const resetForms = () => {
    setNewPrinter({ id: '', name: '', supported_methods: [], is_active: true });
    setNewMaterial({ id: '', method: '', name: '', unit_cost_per_g_cents: 10, colors: [], is_active: true });
    setNewColor('');
    setEditingMode(null);
    setEditingMaterial(null);
  };

  const updateCatalog = async (updatedData: any) => {
    try {
      setIsUpdating(true);
      await apiClient.put('/api/v1/catalog', { data: updatedData });
      await mutate();
      show('Catalog updated successfully!');
      resetForms();
    } catch (err) {
      show('Failed to update catalog');
      console.error('Catalog update error:', err);
    } finally {
      setIsUpdating(false);
    }
  };

  const addPrinter = async () => {
    if (!newPrinter.name || !newPrinter.id || newPrinter.supported_methods.length === 0) {
      show('Please fill all printer fields');
      return;
    }

    const updatedCatalog = {
      ...catalog,
      printers: [
        ...catalog!.printers,
        { ...newPrinter }
      ]
    };

    await updateCatalog(updatedCatalog);
  };

  const togglePrinterActive = async (printerId: string) => {
    const updatedCatalog = {
      ...catalog,
      printers: catalog!.printers.map(p => 
        p.id === printerId ? { ...p, is_active: !p.is_active } : p
      )
    };
    await updateCatalog(updatedCatalog);
  };

  const addMaterial = async () => {
    if (!newMaterial.name || !newMaterial.id || !newMaterial.method) {
      show('Please fill all material fields');
      return;
    }

    const updatedCatalog = {
      ...catalog,
      materials: [
        ...catalog!.materials,
        { ...newMaterial }
      ]
    };

    await updateCatalog(updatedCatalog);
  };

  const toggleMaterialActive = async (materialId: string) => {
    const updatedCatalog = {
      ...catalog,
      materials: catalog!.materials.map(m => 
        m.id === materialId ? { ...m, is_active: !m.is_active } : m
      )
    };
    await updateCatalog(updatedCatalog);
  };

  const addColorToMaterial = async (materialId: string) => {
    if (!newColor.trim()) {
      show('Please enter a color name');
      return;
    }

    const updatedCatalog = {
      ...catalog,
      materials: catalog!.materials.map(m => 
        m.id === materialId 
          ? { ...m, colors: [...m.colors, newColor.trim()] }
          : m
      )
    };

    await updateCatalog(updatedCatalog);
  };

  const removeColorFromMaterial = async (materialId: string, colorToRemove: string) => {
    const updatedCatalog = {
      ...catalog,
      materials: catalog!.materials.map(m => 
        m.id === materialId 
          ? { ...m, colors: m.colors.filter(c => c !== colorToRemove) }
          : m
      )
    };

    await updateCatalog(updatedCatalog);
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="text-base font-semibold text-gray-900">Catalog Management</h2>
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
          <h2 className="text-base font-semibold text-gray-900">Catalog Management</h2>
        </div>
        <div className="p-5">
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <p className="text-sm text-red-800">Failed to load catalog: {error.message}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200">
      <div className="px-5 py-4 border-b border-gray-100">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-gray-900 flex items-center gap-2">
              <Package className="w-5 h-5" />
              Catalog Management
              <span className="text-sm font-normal text-gray-500">(Version {version})</span>
            </h2>
            <p className="text-sm text-gray-600">Manage printers, materials, and colors for the submission form</p>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8 px-5">
          <button
            onClick={() => setActiveTab('printers')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'printers'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Settings className="w-4 h-4 inline mr-1" />
            Printers
          </button>
          <button
            onClick={() => setActiveTab('materials')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'materials'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <Palette className="w-4 h-4 inline mr-1" />
            Materials & Colors
          </button>
        </nav>
      </div>

      <div className="p-5">
        {activeTab === 'printers' && (
          <div className="space-y-4">
            {/* Add New Printer */}
            <div className="border rounded-lg p-4 bg-gray-50">
              <h3 className="font-medium text-gray-900 mb-3">Add New Printer</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Printer ID</label>
                  <input
                    type="text"
                    value={newPrinter.id}
                    onChange={(e) => setNewPrinter(prev => ({ ...prev, id: e.target.value }))}
                    placeholder="e.g., prusa-mk4s"
                    className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Display Name</label>
                  <input
                    type="text"
                    value={newPrinter.name}
                    onChange={(e) => setNewPrinter(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="e.g., Prusa MK4S"
                    className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Supported Methods</label>
                  <div className="flex gap-2">
                    {catalog?.methods.map(method => (
                      <label key={method} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={newPrinter.supported_methods.includes(method)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setNewPrinter(prev => ({
                                ...prev,
                                supported_methods: [...prev.supported_methods, method]
                              }));
                            } else {
                              setNewPrinter(prev => ({
                                ...prev,
                                supported_methods: prev.supported_methods.filter(m => m !== method)
                              }));
                            }
                          }}
                          className="mr-1"
                        />
                        <span className="text-sm">{method}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
              <button
                onClick={addPrinter}
                disabled={isUpdating}
                className="mt-3 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                <Plus className="w-4 h-4 inline mr-1" />
                Add Printer
              </button>
            </div>

            {/* Existing Printers */}
            <div>
              <h3 className="font-medium text-gray-900 mb-3">Current Printers</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-gray-500 border-b">
                      <th className="py-2">Name</th>
                      <th className="py-2">ID</th>
                      <th className="py-2">Methods</th>
                      <th className="py-2">Status</th>
                      <th className="py-2">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {catalog?.printers.map((printer) => (
                      <tr key={printer.id} className="border-b last:border-b-0">
                        <td className="py-2">{printer.name}</td>
                        <td className="py-2 text-gray-500">{printer.id}</td>
                        <td className="py-2">
                          <div className="flex gap-1">
                            {printer.supported_methods.map(method => (
                              <span key={method} className="px-2 py-1 text-xs rounded bg-blue-100 text-blue-800">
                                {method}
                              </span>
                            ))}
                          </div>
                        </td>
                        <td className="py-2">
                          {printer.is_active ? (
                            <span className="px-2 py-1 text-xs rounded bg-green-100 text-green-800">Active</span>
                          ) : (
                            <span className="px-2 py-1 text-xs rounded bg-gray-100 text-gray-700">Inactive</span>
                          )}
                        </td>
                        <td className="py-2">
                          <button
                            onClick={() => togglePrinterActive(printer.id)}
                            disabled={isUpdating}
                            className="px-2 py-1 text-xs rounded bg-gray-800 text-white hover:bg-black disabled:opacity-50"
                          >
                            {printer.is_active ? "Deactivate" : "Activate"}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'materials' && (
          <div className="space-y-4">
            {/* Add New Material */}
            <div className="border rounded-lg p-4 bg-gray-50">
              <h3 className="font-medium text-gray-900 mb-3">Add New Material</h3>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Material ID</label>
                  <input
                    type="text"
                    value={newMaterial.id}
                    onChange={(e) => setNewMaterial(prev => ({ ...prev, id: e.target.value }))}
                    placeholder="e.g., pla-plus"
                    className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Display Name</label>
                  <input
                    type="text"
                    value={newMaterial.name}
                    onChange={(e) => setNewMaterial(prev => ({ ...prev, name: e.target.value }))}
                    placeholder="e.g., PLA+"
                    className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Method</label>
                  <select
                    value={newMaterial.method}
                    onChange={(e) => setNewMaterial(prev => ({ ...prev, method: e.target.value }))}
                    className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                  >
                    <option value="">Select method</option>
                    {catalog?.methods.map(method => (
                      <option key={method} value={method}>{method}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Cost (cents/gram)</label>
                  <input
                    type="number"
                    value={newMaterial.unit_cost_per_g_cents}
                    onChange={(e) => setNewMaterial(prev => ({ ...prev, unit_cost_per_g_cents: parseInt(e.target.value) || 0 }))}
                    min="1"
                    className="w-full border border-gray-300 rounded px-3 py-2 text-sm"
                  />
                </div>
              </div>
              <button
                onClick={addMaterial}
                disabled={isUpdating}
                className="mt-3 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                <Plus className="w-4 h-4 inline mr-1" />
                Add Material
              </button>
            </div>

            {/* Existing Materials */}
            <div>
              <h3 className="font-medium text-gray-900 mb-3">Current Materials</h3>
              <div className="space-y-4">
                {catalog?.materials.map((material) => (
                  <div key={material.id} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <h4 className="font-medium text-gray-900">{material.name}</h4>
                        <p className="text-sm text-gray-500">
                          {material.method} • ${(material.unit_cost_per_g_cents / 100).toFixed(2)}/gram • ID: {material.id}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        {material.is_active ? (
                          <span className="px-2 py-1 text-xs rounded bg-green-100 text-green-800">Active</span>
                        ) : (
                          <span className="px-2 py-1 text-xs rounded bg-gray-100 text-gray-700">Inactive</span>
                        )}
                        <button
                          onClick={() => toggleMaterialActive(material.id)}
                          disabled={isUpdating}
                          className="px-2 py-1 text-xs rounded bg-gray-800 text-white hover:bg-black disabled:opacity-50"
                        >
                          {material.is_active ? "Deactivate" : "Activate"}
                        </button>
                      </div>
                    </div>

                    {/* Colors Management */}
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <h5 className="text-sm font-medium text-gray-700">Available Colors</h5>
                        <button
                          onClick={() => setEditingMaterial(editingMaterial === material.id ? null : material.id)}
                          className="text-sm text-blue-600 hover:text-blue-800"
                        >
                          {editingMaterial === material.id ? 'Cancel' : 'Manage Colors'}
                        </button>
                      </div>

                      <div className="flex flex-wrap gap-2 mb-2">
                        {material.colors.map(color => (
                          <div key={color} className="flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-700 rounded text-sm">
                            <span>{color}</span>
                            {editingMaterial === material.id && (
                              <button
                                onClick={() => removeColorFromMaterial(material.id, color)}
                                disabled={isUpdating}
                                className="text-red-600 hover:text-red-800 ml-1"
                              >
                                <Trash2 className="w-3 h-3" />
                              </button>
                            )}
                          </div>
                        ))}
                        {material.colors.length === 0 && (
                          <span className="text-sm text-gray-500 italic">No colors defined</span>
                        )}
                      </div>

                      {editingMaterial === material.id && (
                        <div className="flex gap-2">
                          <input
                            type="text"
                            value={newColor}
                            onChange={(e) => setNewColor(e.target.value)}
                            placeholder="Enter color name"
                            className="flex-1 border border-gray-300 rounded px-3 py-2 text-sm"
                            onKeyPress={(e) => {
                              if (e.key === 'Enter') {
                                addColorToMaterial(material.id);
                              }
                            }}
                          />
                          <button
                            onClick={() => addColorToMaterial(material.id)}
                            disabled={isUpdating || !newColor.trim()}
                            className="px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                          >
                            <Plus className="w-4 h-4" />
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
