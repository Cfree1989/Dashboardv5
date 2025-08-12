import React from 'react';

type Props = {
  period: number;
  onChange: (next: { period: number }) => void;
};

export function AnalyticsFilters({ period, onChange }: Props) {
  return (
    <div className="flex items-center gap-2 mb-4">
      <label className="text-sm text-gray-700">Period:</label>
      <select
        aria-label="Period"
        className="border border-gray-300 rounded-md px-2 py-1 text-sm"
        value={period}
        onChange={(e) => onChange({ period: Number(e.target.value) })}
      >
        <option value={7}>7 days</option>
        <option value={30}>30 days</option>
        <option value={90}>90 days</option>
      </select>
    </div>
  );
}


