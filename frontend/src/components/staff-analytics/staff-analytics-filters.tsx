import React, { useState } from 'react';
import type { StaffAnalyticsFilters } from '../../types/analytics';

type Props = {
  filters: StaffAnalyticsFilters;
  onFiltersChange: (next: StaffAnalyticsFilters) => void;
};

export function StaffAnalyticsFilters({ filters, onFiltersChange }: Props) {
  const [useCustomRange, setUseCustomRange] = useState(false);
  
  const periodOptions: { value: 7 | 30 | 90; label: string }[] = [
    { value: 7, label: '7 days' },
    { value: 30, label: '30 days' },
    { value: 90, label: '90 days' },
  ];



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
    <div className="flex flex-wrap items-center gap-3">
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
     </div>
   );
 }
