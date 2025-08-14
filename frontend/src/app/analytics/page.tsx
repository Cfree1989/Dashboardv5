"use client";
import React, { useEffect, useMemo, useState } from 'react';
import { BarChart3, Users } from 'lucide-react';
import { fetchAnalyticsData } from '../../lib/analytics-api';
import { fetchStaffAnalyticsData } from '../../lib/staff-analytics-api';
import type { AnalyticsData, AnalyticsFilters, StaffAnalyticsData, StaffAnalyticsFilters } from '../../types/analytics';
import { OverviewCards } from '../../components/analytics/overview-cards';
import { TrendCharts } from '../../components/analytics/trend-charts';
import { ResourceMetrics } from '../../components/analytics/resource-metrics';
import { FinancialSummary } from '../../components/analytics/financial-summary';
import { AnalyticsFilters as AnalyticsFiltersComponent } from '../../components/analytics/analytics-filters';
import { StaffOverviewCards } from '../../components/staff-analytics/staff-overview-cards';
import { StaffComparisonView } from '../../components/staff-analytics/staff-comparison-view';
import { StaffPerformanceDetail } from '../../components/staff-analytics/staff-performance-detail';
import { StaffAnalyticsFilters as StaffAnalyticsFiltersComponent } from '../../components/staff-analytics/staff-analytics-filters';
import { useReducedMotion } from '../../lib/use-reduced-motion';

type AnalyticsSection = "system" | "staff";

export default function AnalyticsPage() {
  // System Analytics State
  const [systemData, setSystemData] = useState<AnalyticsData | null>(null);
  const [systemError, setSystemError] = useState<string>('');
  const [systemLoading, setSystemLoading] = useState<boolean>(false);
  const [systemFilters, setSystemFilters] = useState<AnalyticsFilters>({ 
    period: 7, 
    printer: 'all', 
    discipline: 'all',
    startDate: undefined,
    endDate: undefined
  });

  // Staff Analytics State
  const [staffData, setStaffData] = useState<StaffAnalyticsData | null>(null);
  const [staffError, setStaffError] = useState<string>('');
  const [staffLoading, setStaffLoading] = useState<boolean>(false);
  const [staffFilters, setStaffFilters] = useState<StaffAnalyticsFilters>({ 
    period: 7,
    staff: undefined,
    startDate: undefined,
    endDate: undefined
  });

  const [activeSection, setActiveSection] = useState<AnalyticsSection>("system");
  const [refreshedAt, setRefreshedAt] = useState<Date | null>(null);
  const reduceMotion = useReducedMotion();
  const systemRefreshKey = useMemo(() => JSON.stringify(systemFilters), [systemFilters]);
  const staffRefreshKey = useMemo(() => JSON.stringify(staffFilters), [staffFilters]);

  // Load system analytics data
  async function loadSystemData() {
    try {
      setSystemLoading(true);
      const d = await fetchAnalyticsData(systemFilters);
      setSystemData(d);
      const now = new Date();
      setRefreshedAt(now);
      try { localStorage.setItem('lastUpdated', now.toLocaleTimeString()); } catch {}
    } catch {
      setSystemError('Failed to load system analytics');
    } finally {
      setSystemLoading(false);
    }
  }

  // Load staff analytics data
  async function loadStaffData() {
    try {
      setStaffLoading(true);
      const d = await fetchStaffAnalyticsData(staffFilters);
      setStaffData(d);
      const now = new Date();
      setRefreshedAt(now);
      try { localStorage.setItem('lastUpdated', now.toLocaleTimeString()); } catch {}
    } catch {
      setStaffError('Failed to load staff analytics');
    } finally {
      setStaffLoading(false);
    }
  }

  // Load data when filters change
  useEffect(() => {
    if (activeSection === "system") {
      void loadSystemData();
    }
  }, [systemFilters, activeSection]);

  useEffect(() => {
    if (activeSection === "staff") {
      void loadStaffData();
    }
  }, [staffFilters, activeSection]);

  const sections: Array<{ id: AnalyticsSection; label: string; icon: React.ComponentType<any> }> = [
    { id: "system", label: "System Analytics", icon: BarChart3 },
    { id: "staff", label: "Staff Analytics", icon: Users },
  ];

  const renderSystemAnalytics = () => (
    <div>
      {systemError && <div className="text-red-600 text-sm mb-4" role="alert">{systemError}</div>}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4">
          <AnalyticsFiltersComponent filters={systemFilters} onFiltersChange={setSystemFilters} />
        </div>
        {systemLoading && <div className="text-xs text-gray-500">Loading…</div>}
      </div>
      
      {!systemData && systemLoading && (
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
      
      {systemData && (
        <div className={`transition-opacity duration-300 ${systemLoading || reduceMotion ? '' : 'opacity-100'}`}>
          <OverviewCards data={systemData.overview} />
        </div>
      )}

      {systemData && (
        <div className={`transition-opacity duration-300 ${systemLoading || reduceMotion ? '' : 'opacity-100'}`}>
          <TrendCharts trends={systemData.trends} resources={systemData.resources} period={Number(systemFilters.period) || 7} key={systemRefreshKey} />
        </div>
      )}

      {systemData && (
        <div className={`grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6 transition-opacity duration-300 ${systemLoading || reduceMotion ? '' : 'opacity-100'}`}>
          <div className="lg:col-span-2 space-y-6">
            <ResourceMetrics data={systemData.resources} />
          </div>
          <div>
            <FinancialSummary data={systemData} />
          </div>
        </div>
      )}
    </div>
  );

  const renderStaffAnalytics = () => (
    <div>
      {staffError && <div className="text-red-600 text-sm mb-4" role="alert">{staffError}</div>}
      
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4">
          <StaffAnalyticsFiltersComponent filters={staffFilters} onFiltersChange={setStaffFilters} />
        </div>
        {staffLoading && <div className="text-xs text-gray-500">Loading…</div>}
      </div>

      {!staffData && staffLoading && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 mb-6 animate-pulse">
          <div className="h-4 w-32 bg-gray-200 rounded mb-4" />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="rounded-lg border border-gray-200 p-3">
                <div className="h-6 bg-gray-200 rounded mb-2" />
                <div className="h-3 bg-gray-100 rounded" />
              </div>
            ))}
          </div>
        </div>
      )}

      {staffData && (
        <div className={`transition-opacity duration-300 ${staffLoading || reduceMotion ? '' : 'opacity-100'}`}>
          <StaffOverviewCards data={staffData.overview} />
        </div>
      )}

      {staffData && (
        <div className={`transition-opacity duration-300 ${staffLoading || reduceMotion ? '' : 'opacity-100'}`}>
          <StaffComparisonView data={staffData.comparison} />
        </div>
      )}

      {staffData && staffData.performance && (
        <div className={`transition-opacity duration-300 ${staffLoading || reduceMotion ? '' : 'opacity-100'}`}>
          <StaffPerformanceDetail data={staffData.performance} />
        </div>
      )}
    </div>
  );

  const renderSection = () => {
    switch (activeSection) {
      case "system":
        return renderSystemAnalytics();
      case "staff":
        return renderStaffAnalytics();
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col lg:flex-row gap-6 mt-6">
          {/* Sidebar Navigation */}
          <div className="lg:w-64 flex-shrink-0">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
              <nav className="space-y-2">
                {sections.map((section) => {
                  const Icon = section.icon as any;
                  const active = activeSection === section.id;
                  return (
                    <button
                      key={section.id}
                      onClick={() => setActiveSection(section.id)}
                      className={`w-full flex items-center px-3 py-2 rounded-lg text-left transition-colors ${
                        active ? "bg-blue-100 text-blue-700 border border-blue-200" : "text-gray-600 hover:bg-gray-100"
                      }`}
                    >
                      <Icon className="w-4 h-4 mr-3" />
                      {section.label}
                    </button>
                  );
                })}
              </nav>
            </div>
          </div>

          {/* Main Content */}
          <div className="flex-1">{renderSection()}</div>
        </div>
      </div>
    </div>
  );
}


