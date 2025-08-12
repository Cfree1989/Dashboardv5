import React from 'react';
import type { TrendData } from '../../types/analytics';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from 'recharts';

type Props = { data: TrendData; period?: number };

export function TrendCharts({ data, period }: Props) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
      <div className="flex items-baseline justify-between mb-3">
        <h2 className="text-base font-semibold">Trends — submissions</h2>
        {period ? (
          <span className="text-xs text-gray-500">Last {period} days</span>
        ) : null}
      </div>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={mergeSeries(data)}
            margin={{ left: 8, right: 8, top: 8, bottom: 8 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="submissions" name="Submissions" stroke="#2563eb" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="approvals" name="Approvals" stroke="#10b981" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      {data.submissions.length === 0 && (
        <div className="text-gray-500 text-sm mt-3">No data in range.</div>
      )}
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


