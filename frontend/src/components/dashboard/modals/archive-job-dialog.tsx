"use client";
import React, { useState, useEffect } from "react";
import { apiClient } from "../../../lib/unified-api-client";

interface Staff {
  name: string;
}

export interface ArchiveJobDialogProps {
  jobShortId: string;
  onConfirm: (staffName: string) => void;
  onCancel: () => void;
}

export default function ArchiveJobDialog({ jobShortId, onConfirm, onCancel }: ArchiveJobDialogProps) {
  const [text, setText] = useState("");
  const [staffName, setStaffName] = useState("");
  const [staff, setStaff] = useState<Staff[]>([]);
  const [loadingStaff, setLoadingStaff] = useState(false);
  
  const textMatches = text.trim() === jobShortId.trim();
  const hasStaff = staffName.trim() !== "";
  const isValid = textMatches && hasStaff;

  // Load staff list on component mount
  useEffect(() => {
    const loadStaff = async () => {
      setLoadingStaff(true);
      try {
        const response = await apiClient.get<{staff: Staff[]}>('/api/v1/staff');
        setStaff(response?.staff || []);
      } catch (error) {
        console.error('Failed to load staff:', error);
        setStaff([]);
      } finally {
        setLoadingStaff(false);
      }
    };
    loadStaff();
  }, []);

  const handleConfirm = () => {
    if (isValid) {
      onConfirm(staffName.trim());
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40" onClick={onCancel} />
      <div className="relative bg-white w-full max-w-md rounded-xl shadow-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-1">Confirm Archive</h3>
        <p className="text-sm text-gray-600 mb-4">
          This will archive the job. You can later permanently delete it from the Admin area.
        </p>
        
        <div className="space-y-4 mb-4">
          {/* Staff Attribution */}
          <div>
            <label htmlFor="archive-staff" className="block text-sm font-medium text-gray-700 mb-1">
              Performing Action As
            </label>
            <select
              id="archive-staff"
              className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value={staffName}
              onChange={(e) => setStaffName(e.target.value)}
              disabled={loadingStaff}
              required
            >
              <option value="" disabled>
                {loadingStaff ? "Loading staff..." : "Select your name"}
              </option>
              {staff.map((s) => (
                <option key={s.name} value={s.name}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>

          {/* Text Confirmation */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Type the Job short ID to confirm
            </label>
            <input
              type="text"
              className="w-full border rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder={jobShortId}
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
          </div>
        </div>

        <div className="flex justify-end space-x-2">
          <button 
            onClick={onCancel} 
            className="px-4 py-2 rounded-lg border text-gray-700 hover:bg-gray-50 focus-ring btn-transition"
          >
            Cancel
          </button>
          <button 
            onClick={handleConfirm} 
            disabled={!isValid} 
            className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 focus-ring btn-transition"
          >
            Archive Job
          </button>
        </div>
      </div>
    </div>
  );
}
