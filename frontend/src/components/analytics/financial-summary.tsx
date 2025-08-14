import React from 'react';
import type { AnalyticsData } from '../../types/analytics';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid, LineChart, Line } from 'recharts';

type Props = { data: AnalyticsData };

export function FinancialSummary({ data }: Props) {
  const f = data.financial;
  const totalRevenueUsd = f.totalRevenueCents / 100;
  
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
      <h3 className="text-base font-semibold mb-3">Financial Summary</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Kpi label="Total Revenue" value={`$${formatMoney(totalRevenueUsd)}`} />
        <Kpi label="Avg Ticket" value={`$${formatMoney(f.avgTicketUsd)}`} />
        <Kpi label="Payment Rate" value={`${f.paymentCount > 0 ? Math.round((f.paymentCount / (data.overview.byStatus.COMPLETED || 0 + data.overview.byStatus.PAIDPICKEDUP || 0)) * 100) : 0}%`} />
        <Kpi label="Payments" value={String(f.paymentCount)} />
      </div>
      <div className="mt-4">
        <div className="font-medium text-gray-700 mb-2">Revenue Over Time</div>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={f.revenueOverTime.map((p) => ({ date: p.date, revenue: p.cents / 100 }))}
              margin={{ left: 8, right: 8, top: 8, bottom: 8 }}
              key="revenue"
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Line type="monotone" dataKey="revenue" stroke="#10b981" strokeWidth={2} dot={false} isAnimationActive animationDuration={600} animationEasing="ease-in-out" />
            </LineChart>
          </ResponsiveContainer>
        </div>
        {f.revenueOverTime.length === 0 && <div className="text-gray-500 text-sm mt-2">No data</div>}
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


