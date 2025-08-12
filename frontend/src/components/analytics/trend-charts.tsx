import React from 'react';
import type { TrendData } from '../../types/analytics';
import type { ResourcesData } from '../../types/analytics';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  BarChart,
  Bar,
} from 'recharts';

type Props = { trends: TrendData; resources: ResourcesData; period?: number };

export function TrendCharts({ trends, resources, period }: Props) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <div className="flex items-baseline justify-between mb-3">
          <h2 className="text-base font-semibold">Submissions & Approvals Over Time</h2>
          {period ? <span className="text-xs text-gray-500">Last {period} days</span> : null}
        </div>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={mergeSeries(trends)} margin={{ left: 8, right: 8, top: 8, bottom: 8 }} key="subs-approvals">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="submissions" name="Submissions" stroke="#2563eb" strokeWidth={2} dot={false} isAnimationActive animationDuration={600} animationEasing="ease-in-out" />
              <Line type="monotone" dataKey="approvals" name="Approvals" stroke="#10b981" strokeWidth={2} dot={false} isAnimationActive animationDuration={600} animationEasing="ease-in-out" />
            </LineChart>
          </ResponsiveContainer>
        </div>
        {trends.submissions.length === 0 && (
          <div className="text-gray-500 text-sm mt-3">No data in range.</div>
        )}
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <h3 className="text-base font-semibold mb-3">Printing Throughput</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={resources.printingThroughput} margin={{ left: 8, right: 8, top: 8, bottom: 8 }} key="throughput">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" name="Completed Jobs" fill="#8b5cf6" isAnimationActive animationDuration={600} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        {resources.printingThroughput.length === 0 && <div className="text-gray-500 text-sm mt-3">No data</div>}
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 lg:col-span-2">
        <h3 className="text-base font-semibold mb-3">Average Lead Time</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={resources.averageLeadTime} margin={{ left: 8, right: 8, top: 8, bottom: 8 }} key="lead-time">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="hours" name="Hours" stroke="#f59e0b" strokeWidth={2} dot={false} isAnimationActive animationDuration={600} animationEasing="ease-in-out" />
            </LineChart>
          </ResponsiveContainer>
        </div>
        {resources.averageLeadTime.length === 0 && <div className="text-gray-500 text-sm mt-3">No data</div>}
      </div>
    </div>
  );
}

function mergeSeries(data: TrendData) {
  const map = new Map<string, { date: string; submissions: number; approvals: number }>();
  for (const p of data.submissions) {
    map.set(p.date, { date: p.date, submissions: p.count, approvals: 0 });
  }
  for (const p of data.approvals) {
    const row = map.get(p.date) || { date: p.date, submissions: 0, approvals: 0 };
    row.approvals = p.count;
    map.set(p.date, row);
  }
  return Array.from(map.values()).sort((a, b) => a.date.localeCompare(b.date));
}


