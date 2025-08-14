import React, { useState, useEffect } from 'react';
import type { StaffAnalyticsFilters } from '../../types/analytics';

type StaffMember = {
  name: string;
  is_active: boolean;
};

type Props = {
  filters: StaffAnalyticsFilters;
  onFiltersChange: (next: StaffAnalyticsFilters) => void;
};

export function StaffAnalyticsFilters({ filters, onFiltersChange }: Props) {
  const [useCustomRange, setUseCustomRange] = useState(false);
  const [staffList, setStaffList] = useState<StaffMember[]>([]);
  const [loadingStaff, setLoadingStaff] = useState(false);
  
  const periodOptions: { value: 7 | 30 | 90; label: string }[] = [
    { value: 7, label: '7 days' },
    { value: 30, label: '30 days' },
    { value: 90, label: '90 days' },
  ];

  // Fetch staff list on component mount
  useEffect(() => {
    async function fetchStaff() {
      try {
        setLoadingStaff(true);
        const token = localStorage.getItem('token');
        const response = await fetch('/api/v1/staff?include_inactive=true', {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        });
        if (response.ok) {
          const data = await response.json();
          setStaffList(data.staff || []);
        }
      } catch (error) {
        console.error('Failed to fetch staff list:', error);
      } finally {
        setLoadingStaff(false);
      }
    }
    fetchStaff();
  }, []);

  const handlePeriodChange = (period: 7 | 30 | 90) => {
    setUseCustomRange(false);
    onFiltersChange({ 
      ...filters, 
      period, 
      startDate: undefined, 
      endDate: undefined 
    });
  };

  const handleCustomRangeChange = () => {
    setUseCustomRange(true);
    onFiltersChange({ 
      ...filters, 
      period: 7, // Reset to default when using custom range
      startDate: filters.startDate || new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      endDate: filters.endDate || new Date().toISOString().split('T')[0]
    });
  };

  const handleDateChange = (field: 'startDate' | 'endDate', value: string) => {
    onFiltersChange({ ...filters, [field]: value });
  };

  return (
    <div className="flex flex-wrap items-center gap-3 mb-4">
      <div className="flex items-center gap-2">
        <label className="text-sm text-gray-700">Period:</label>
        <div className="inline-flex overflow-hidden rounded-md border border-gray-200">
          {periodOptions.map((opt) => {
            const active = !useCustomRange && Number(filters.period) === Number(opt.value);
            return (
              <button
                type="button"
                key={opt.value}
                className={
                  'px-2 py-1 text-sm transition-colors ' +
                  (active
                    ? 'bg-gray-800 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50')
                }
                onClick={() => handlePeriodChange(opt.value)}
              >
                {opt.label}
              </button>
            );
          })}
          <button
            type="button"
            className={
              'px-2 py-1 text-sm transition-colors ' +
              (useCustomRange
                ? 'bg-gray-800 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-50')
            }
            onClick={handleCustomRangeChange}
          >
            Custom
          </button>
        </div>
      </div>

      {useCustomRange && (
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-700">Date Range:</label>
          <input
            type="date"
            className="border border-gray-300 rounded-md px-2 py-1 text-sm"
            value={filters.startDate || ''}
            onChange={(e) => handleDateChange('startDate', e.target.value)}
          />
          <span className="text-sm text-gray-500">to</span>
          <input
            type="date"
            className="border border-gray-300 rounded-md px-2 py-1 text-sm"
            value={filters.endDate || ''}
            onChange={(e) => handleDateChange('endDate', e.target.value)}
          />
        </div>
      )}

      <div className="flex items-center gap-2">
        <label className="text-sm text-gray-700">Staff Member:</label>
        <select
          aria-label="Staff Member"
          className="border border-gray-300 rounded-md px-2 py-1 text-sm"
          value={filters.staff || 'all'}
          onChange={(e) => onFiltersChange({ ...filters, staff: e.target.value === 'all' ? undefined : e.target.value })}
          disabled={loadingStaff}
        >
          <option value="all">All Staff</option>
          {staffList.map((staff) => (
            <option key={staff.name} value={staff.name}>
              {staff.name} {!staff.is_active && '(Inactive)'}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
