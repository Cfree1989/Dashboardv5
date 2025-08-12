import React from 'react';
import type { AnalyticsData } from '../../types/analytics';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

type Props = { data: AnalyticsData };

export function FinancialSummary({ data }: Props) {
  const f = data.financial;
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
      <h3 className="text-base font-semibold mb-3">Financial Summary</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Kpi label="Total Revenue" value={`$${formatMoney(f.totalRevenueUsd)}`} />
        <Kpi label="Avg Ticket" value={`$${formatMoney(f.averageTicketUsd)}`} />
        <Kpi label="Payment Rate" value={`${f.paymentRatePercent}%`} />
        <Kpi label="Payments" value={String(data.resources.paymentCount)} />
      </div>
      <div className="mt-4">
        <div className="font-medium text-gray-700 mb-2">Revenue Over Time</div>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={data.resources.revenueOverTime.map((p) => ({ date: p.date, revenue: p.cents / 100 }))}
              margin={{ left: 8, right: 8, top: 8, bottom: 8 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Area type="monotone" dataKey="revenue" stroke="#7c3aed" fill="#c4b5fd" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
        {data.resources.revenueOverTime.length === 0 && <div className="text-gray-500 text-sm mt-2">No data</div>}
      </div>
    </div>
  );
}

function Kpi({ label, value }: { label: string; value: string }) {
  return (
    <div className="text-center rounded-lg border border-gray-200 p-3">
      <div className="text-2xl font-bold text-gray-900">{value}</div>
      <div className="text-xs text-gray-600 mt-1">{label}</div>
    </div>
  );
}

function formatMoney(n: number) {
  try { return new Intl.NumberFormat(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(n); } catch { return n.toFixed(2); }
}


