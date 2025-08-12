import React from 'react';

export type AnalyticsFilterState = {
  period: 7 | 30 | 90 | number;
  discipline: string;
  printer: string;
};

type Props = {
  filters: AnalyticsFilterState;
  onFiltersChange: (next: AnalyticsFilterState) => void;
};

export function AnalyticsFilters({ filters, onFiltersChange }: Props) {
  const periodOptions: { value: 7 | 30 | 90; label: string }[] = [
    { value: 7, label: '7 days' },
    { value: 30, label: '30 days' },
    { value: 90, label: '90 days' },
  ];

  return (
    <div className="flex flex-wrap items-center gap-3 mb-4">
      <div className="flex items-center gap-2">
        <label className="text-sm text-gray-700">Period:</label>
        <div className="inline-flex overflow-hidden rounded-md border border-gray-200">
          {periodOptions.map((opt) => {
            const active = Number(filters.period) === Number(opt.value);
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
                onClick={() => onFiltersChange({ ...filters, period: opt.value })}
              >
                {opt.label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="flex items-center gap-2">
        <label className="text-sm text-gray-700">Discipline:</label>
        <select
          aria-label="Discipline"
          className="border border-gray-300 rounded-md px-2 py-1 text-sm"
          value={filters.discipline}
          onChange={(e) => onFiltersChange({ ...filters, discipline: e.target.value })}
        >
          <option value="all">All</option>
          <option value="Art">Art</option>
          <option value="Architecture">Architecture</option>
          <option value="Landscape Architecture">Landscape Architecture</option>
          <option value="Interior Design">Interior Design</option>
          <option value="Engineering">Engineering</option>
          <option value="Hobby/Personal">Hobby/Personal</option>
          <option value="Other">Other</option>
        </select>
      </div>

      <div className="flex items-center gap-2">
        <label className="text-sm text-gray-700">Printer:</label>
        <select
          aria-label="Printer"
          className="border border-gray-300 rounded-md px-2 py-1 text-sm"
          value={filters.printer}
          onChange={(e) => onFiltersChange({ ...filters, printer: e.target.value })}
        >
          <option value="all">All</option>
          <option value="Prusa MK4S">Prusa MK4S</option>
          <option value="Prusa XL">Prusa XL</option>
          <option value="Raise3D Pro 2 Plus">Raise3D Pro 2 Plus</option>
          <option value="Formlabs Form 3">Formlabs Form 3</option>
        </select>
      </div>
    </div>
  );
}


