"use client";
import React, { useEffect, useMemo, useState } from 'react';
import { RefreshCcw } from 'lucide-react';
import { fetchAnalyticsData } from '../../lib/analytics-api';
import type { AnalyticsData } from '../../types/analytics';
import { OverviewCards } from '../../components/analytics/overview-cards';
import { TrendCharts } from '../../components/analytics/trend-charts';
import { ResourceMetrics } from '../../components/analytics/resource-metrics';
import { FinancialSummary } from '../../components/analytics/financial-summary';
import { AnalyticsFilters, AnalyticsFilterState } from '../../components/analytics/analytics-filters';
import { useReducedMotion } from '../../lib/use-reduced-motion';

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [error, setError] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [filters, setFilters] = useState<AnalyticsFilterState>({ period: 7, printer: 'all', discipline: 'all' });
  const [refreshedAt, setRefreshedAt] = useState<Date | null>(null);
  const reduceMotion = useReducedMotion();
  const refreshKey = useMemo(() => JSON.stringify(filters), [filters]);

  async function load() {
    try {
      setLoading(true);
      const d = await fetchAnalyticsData({ period: Number(filters.period) || 7, printer: filters.printer, discipline: filters.discipline });
        setData(d);
        const now = new Date();
        setRefreshedAt(now);
        try { localStorage.setItem('lastUpdated', now.toLocaleTimeString()); } catch {}
    } catch {
      setError('Failed to load analytics');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters]);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* Global header provides title/actions; keep local filters and status only */}
        {error && <div className="text-red-600 text-sm mb-4" role="alert">{error}</div>}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4">
            <AnalyticsFilters filters={filters} onFiltersChange={setFilters} />
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
        {data && (
          <div className={`transition-opacity duration-300 ${loading || reduceMotion ? '' : 'opacity-100'}`}>
            <OverviewCards data={data.overview} />
          </div>
        )}

        {data && (
          <div className={`transition-opacity duration-300 ${loading || reduceMotion ? '' : 'opacity-100'}`}>
            <TrendCharts trends={data.trends} resources={data.resources} period={Number(filters.period) || 7} key={refreshKey} />
          </div>
        )}

        {data && (
          <div className={`grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6 transition-opacity duration-300 ${loading || reduceMotion ? '' : 'opacity-100'}`}>
            {/* Left 2/3: Utilization + Material + Queue Pie stacked vertically */}
            <div className="lg:col-span-2 space-y-6">
              <ResourceMetrics data={data.resources} />
            </div>
            {/* Right 1/3: Financial metrics */}
            <div>
              <FinancialSummary data={data} />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}


