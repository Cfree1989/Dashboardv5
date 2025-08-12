import React from 'react';
import type { ResourcesData } from '../../types/analytics';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Legend, LineChart, Line, ComposedChart, Area } from 'recharts';

type Props = { data: ResourcesData };

export function ResourceMetrics({ data }: Props) {
  return (
    <div className="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <h3 className="text-base font-semibold mb-3">Printing Throughput</h3>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={data.printingThroughput} margin={{ left: 8, right: 8, top: 8, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" name="Prints" fill="#0ea5e9" />
              <Line type="monotone" dataKey="count" name="Trend" stroke="#0369a1" dot={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
        {data.printingThroughput.length === 0 && <div className="text-gray-500 text-sm mt-2">No data</div>}
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <h3 className="text-base font-semibold mb-3">Average Lead Time (h)</h3>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data.averageLeadTime} margin={{ left: 8, right: 8, top: 8, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="hours" name="Hours" stroke="#f59e0b" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        {data.averageLeadTime.length === 0 && <div className="text-gray-500 text-sm mt-2">No data</div>}
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <h3 className="text-base font-semibold mb-3">Material Consumption</h3>
        <div className="text-sm text-gray-700">Filament: <span className="font-semibold">{data.materialConsumptionG.filament}g</span></div>
        <div className="text-sm text-gray-700">Resin: <span className="font-semibold">{data.materialConsumptionG.resin}g</span></div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 lg:col-span-2">
        <h3 className="text-base font-semibold mb-3">Queue Age Distribution</h3>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={Object.entries(data.queueAgeBuckets).map(([bucket, count]) => ({ bucket, count }))}
              margin={{ left: 8, right: 8, top: 8, bottom: 8 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="bucket" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" name="Jobs" fill="#22c55e" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        {Object.keys(data.queueAgeBuckets || {}).length === 0 && <div className="text-gray-500 text-sm mt-2">No data</div>}
      </div>
    </div>
  );
}


