"use client";
import React, { useEffect, useState } from 'react';
import { RefreshCcw, LayoutDashboard, Shield, LogOut } from 'lucide-react';
import Link from 'next/link';
import { fetchAnalyticsData } from '../../lib/analytics-api';
import type { AnalyticsData } from '../../types/analytics';
import { OverviewCards } from '../../components/analytics/overview-cards';
import { TrendCharts } from '../../components/analytics/trend-charts';
import { ResourceMetrics } from '../../components/analytics/resource-metrics';
import { FinancialSummary } from '../../components/analytics/financial-summary';
import { AnalyticsFilters } from '../../components/analytics/analytics-filters';

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [error, setError] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [period, setPeriod] = useState<number>(7);
  const [printer, setPrinter] = useState<string>('all');
  const [discipline, setDiscipline] = useState<string>('all');
  const [refreshedAt, setRefreshedAt] = useState<Date | null>(null);

  async function load() {
    try {
      setLoading(true);
      const d = await fetchAnalyticsData({ period, printer, discipline });
      setData(d);
      setRefreshedAt(new Date());
    } catch {
      setError('Failed to load analytics');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [period, printer, discipline]);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold text-gray-900">Analytics</h1>
            <nav className="flex items-center gap-2 ml-4">
              <Link
                href="/dashboard"
                className="inline-flex items-center gap-1 rounded-md border border-gray-200 px-2 py-1 text-gray-700 hover:bg-gray-100"
              >
                <LayoutDashboard size={14} /> Dashboard
              </Link>
              <Link
                href="/admin"
                className="inline-flex items-center gap-1 rounded-md border border-gray-200 px-2 py-1 text-gray-700 hover:bg-gray-100"
              >
                <Shield size={14} /> Admin
              </Link>
            </nav>
          </div>
          <div className="flex items-center gap-2">
            {refreshedAt && (
              <span className="text-xs text-gray-500" aria-label="last-updated">Last updated {refreshedAt.toLocaleTimeString()}</span>
            )}
            <button
              type="button"
              className="inline-flex items-center gap-1 rounded-md border border-gray-200 px-2 py-1 text-gray-700 hover:bg-gray-100"
              onClick={() => void load()}
              title="Refresh"
            >
              <RefreshCcw size={14} />
              Refresh
            </button>
            <button
              type="button"
              className="inline-flex items-center gap-1 rounded-md border border-red-200 px-2 py-1 text-red-600 hover:bg-red-50"
              onClick={() => {
                try { localStorage.removeItem('token'); } catch {}
                if (typeof window !== 'undefined' && window?.location) {
                  try { window.location.assign('/login'); } catch { window.location.href = '/login'; }
                }
              }}
              title="Logout"
            >
              <LogOut size={14} /> Logout
            </button>
          </div>
        </div>
        {error && <div className="text-red-600 text-sm mb-4" role="alert">{error}</div>}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4">
            <AnalyticsFilters period={period} onChange={({ period }) => setPeriod(period)} />
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-700">Printer:</label>
              <select aria-label="Printer" className="border border-gray-300 rounded-md px-2 py-1 text-sm" value={printer} onChange={(e) => setPrinter(e.target.value)}>
                <option value="all">All</option>
                <option value="Prusa MK4S">Prusa MK4S</option>
                <option value="Prusa XL">Prusa XL</option>
                <option value="Raise3D Pro 2 Plus">Raise3D Pro 2 Plus</option>
                <option value="Formlabs Form 3">Formlabs Form 3</option>
              </select>
            </div>
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-700">Discipline:</label>
              <select aria-label="Discipline" className="border border-gray-300 rounded-md px-2 py-1 text-sm" value={discipline} onChange={(e) => setDiscipline(e.target.value)}>
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
          </div>
          {loading && <div className="text-xs text-gray-500">Loading…</div>}
        </div>
        {!data && loading && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 mb-6 animate-pulse">
            <div className="h-4 w-32 bg-gray-200 rounded mb-4" />
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="rounded-lg border border-gray-200 p-3">
                  <div className="h-6 bg-gray-200 rounded mb-2" />
                  <div className="h-3 bg-gray-100 rounded" />
                </div>
              ))}
            </div>
          </div>
        )}
        {data && <OverviewCards data={data.overview} />}

        {data && <TrendCharts data={data.trends} />}

        {data && <ResourceMetrics data={data.resources} />}
        {data && (
          <div className="mt-6">
            <FinancialSummary data={data} />
          </div>
        )}
      </div>
    </div>
  );
}


