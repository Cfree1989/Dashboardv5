import React from 'react';
import type { ResourcesData } from '../../types/analytics';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Legend, PieChart, Pie, Cell } from 'recharts';

type Props = { data: ResourcesData };

export function ResourceMetrics({ data }: Props) {
  return (
    <div className="mt-6 space-y-6">
      {/* Printer Utilization (stacked) */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <h3 className="text-base font-semibold mb-3">Printer Utilization</h3>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={buildUtilizationData(data)}
              margin={{ left: 8, right: 8, top: 8, bottom: 8 }}
              key="utilization"
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
              <Tooltip />
              <Legend />
              {data.printerUtilization.map((u, idx) => (
                <Bar key={u.printer} dataKey={u.printer} stackId="util" fill={stackColor(idx)} isAnimationActive animationDuration={600} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
        {data.printerUtilization.length === 0 && <div className="text-gray-500 text-sm mt-2">No data</div>}
      </div>

      {/* Material Consumption */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <h3 className="text-base font-semibold mb-3">Material Consumption</h3>
        <div className="grid grid-cols-2 gap-4 mb-1">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{data.materialConsumptionG.filament}g</div>
            <div className="text-sm text-gray-500">Filament Used</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">{data.materialConsumptionG.resin}g</div>
            <div className="text-sm text-gray-500">Resin Used</div>
          </div>
        </div>
      </div>

      {/* Queue Age Distribution (pie) */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <h3 className="text-base font-semibold mb-3">Queue Age Distribution</h3>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart key="queue-pie">
              <Pie
                data={buildQueuePie(data)}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                outerRadius={80}
                isAnimationActive
              >
                {buildQueuePie(data).map((_, idx) => (
                  <Cell key={idx} fill={queueColor(idx)} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
        {Object.keys(data.queueAgeBuckets || {}).length === 0 && <div className="text-gray-500 text-sm mt-2">No data</div>}
      </div>
    </div>
  );
}

function buildUtilizationData(data: ResourcesData) {
  if (!data.printerUtilization || data.printerUtilization.length === 0) return [] as any[];
  // Assume each printer has a series of { date, count }
  const dateSet = new Set<string>();
  for (const u of data.printerUtilization) {
    for (const p of u.series || []) dateSet.add(p.date);
  }
  const dates = Array.from(dateSet.values()).sort();
  return dates.map((d) => {
    const row: any = { date: d };
    for (const u of data.printerUtilization) {
      const pt = (u.series || []).find((p) => p.date === d);
      row[u.printer] = pt ? pt.count : 0;
    }
    return row;
  });
}

function stackColor(i: number) {
  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#9333ea'];
  return colors[i % colors.length];
}

function buildQueuePie(data: ResourcesData) {
  const buckets = data.queueAgeBuckets || {} as Record<string, number>;
  // Map backend keys to friendly labels matching screenshot order and wording
  const order: Array<{ key: string; name: string }> = [
    { key: '0-2', name: '1-3 days' },
    { key: '3-7', name: '3-7 days' },
    { key: '7+', name: '7+ days' },
  ];
  return order
    .map(({ key, name }) => ({ name, value: Number((buckets as any)[key] || 0) }))
    .filter((d) => d.value > 0);
}

function queueColor(i: number) {
  // Match screenshot palette: blue, green, orange, red
  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'];
  return colors[i % colors.length];
}


