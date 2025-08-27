import React from 'react';
import type { OverviewData } from '../../types/analytics';
import { BarChart3, Clock, Inbox, AlertTriangle } from 'lucide-react';
import { ErrorBoundary } from '../error-boundary';
import { JobStatus } from '../../types';

type Props = { data: OverviewData };

// Define the workflow order for status display

const STATUS_ORDER = Object.values(JobStatus);

export function OverviewCards({ data }: Props) {
  // Sort status entries by workflow order
  const sortedStatusEntries = Object.entries(data.byStatus || {})
    .sort(([a], [b]) => {
      const aIndex = STATUS_ORDER.indexOf(a as JobStatus);
      const bIndex = STATUS_ORDER.indexOf(b as JobStatus);
      return aIndex - bIndex;
    });

  return (
    <ErrorBoundary title="Overview cards error">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 mb-6">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-semibold">Overview</h2>
          {data.dateRange && (
            <div className="text-xs text-gray-500">
              {new Date(data.dateRange.start).toLocaleDateString()} - {new Date(data.dateRange.end).toLocaleDateString()}
            </div>
          )}
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Kpi label="Total Submissions" value={formatNumber(data.totalSubmissions)} icon={<BarChart3 size={16} />} />
          <Kpi label="In Queue" value={formatNumber(data.inQueue)} icon={<Inbox size={16} />} />
          <Kpi label="Avg Turnaround (h)" value={data.avgTurnaroundHours != null ? String(data.avgTurnaroundHours) : '--'} icon={<Clock size={16} />} />
          <Kpi label="Recent Rejections" value={formatNumber(data.recentRejections)} icon={<AlertTriangle size={16} />} />
        </div>
        
        {sortedStatusEntries.length > 0 && (
          <div className="mt-5">
            <div className="text-sm font-medium text-gray-700 mb-2">Queue by Status</div>
            <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
              {sortedStatusEntries.map(([status, count]) => (
                <div key={status} className="rounded-lg border border-gray-200 p-3 text-center">
                  <div className="text-xl font-semibold text-gray-900">{count as number}</div>
                  <div className="text-xs text-gray-600 break-words">{status}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
}

function Kpi({ label, value, icon }: { label: string; value: string; icon?: React.ReactNode }) {
  return (
    <div className="text-center rounded-lg border border-gray-200 p-3">
      {icon && <div className="mx-auto mb-1 text-gray-600 w-5 h-5 flex items-center justify-center">{icon}</div>}
      <div className="text-2xl font-bold text-gray-900">{value}</div>
      <div className="text-xs text-gray-600 mt-1">{label}</div>
    </div>
  );
}

function formatNumber(n: number) {
  try { return new Intl.NumberFormat().format(n); } catch { return String(n); }
}


