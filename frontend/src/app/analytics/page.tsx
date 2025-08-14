"use client";
import React, { useEffect, useMemo, useState } from 'react';
import { BarChart3, DollarSign, Users, GraduationCap } from 'lucide-react';
import { fetchAnalyticsData } from '../../lib/analytics-api';
import { fetchStaffAnalyticsData } from '../../lib/staff-analytics-api';
import { fetchStudentAnalyticsData } from '../../lib/student-analytics-api';
import type { AnalyticsData, AnalyticsFilters, StaffAnalyticsData, StaffAnalyticsFilters, StudentAnalyticsData, StudentAnalyticsFilters } from '../../types/analytics';
import { OverviewCards } from '../../components/analytics/overview-cards';
import { TrendCharts } from '../../components/analytics/trend-charts';
import { ResourceMetrics } from '../../components/analytics/resource-metrics';
import { FinancialSummary } from '../../components/analytics/financial-summary';
import { AnalyticsFilters as AnalyticsFiltersComponent } from '../../components/analytics/analytics-filters';
import { StaffOverviewCards } from '../../components/staff-analytics/staff-overview-cards';
import { StaffComparisonView } from '../../components/staff-analytics/staff-comparison-view';
import { StaffPerformanceDetail } from '../../components/staff-analytics/staff-performance-detail';
import { StaffAnalyticsFilters as StaffAnalyticsFiltersComponent } from '../../components/staff-analytics/staff-analytics-filters';
import { StudentAnalyticsFilters as StudentAnalyticsFiltersComponent } from '../../components/student-analytics/student-analytics-filters';
import { useReducedMotion } from '../../lib/use-reduced-motion';

type AnalyticsSection = "operations" | "finance" | "staff" | "student";

export default function AnalyticsPage() {
  // System Analytics State (for Operations tab)
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

  // Student Analytics State
  const [studentData, setStudentData] = useState<StudentAnalyticsData | null>(null);
  const [studentError, setStudentError] = useState<string>('');
  const [studentLoading, setStudentLoading] = useState<boolean>(false);
  const [studentFilters, setStudentFilters] = useState<StudentAnalyticsFilters>({ 
    period: 7,
    startDate: undefined,
    endDate: undefined
  });

  const [activeSection, setActiveSection] = useState<AnalyticsSection>("operations");
  const [refreshedAt, setRefreshedAt] = useState<Date | null>(null);
  const reduceMotion = useReducedMotion();
  const systemRefreshKey = useMemo(() => JSON.stringify(systemFilters), [systemFilters]);
  const staffRefreshKey = useMemo(() => JSON.stringify(staffFilters), [staffFilters]);
  const studentRefreshKey = useMemo(() => JSON.stringify(studentFilters), [studentFilters]);

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

  // Load student analytics data
  async function loadStudentData() {
    try {
      setStudentLoading(true);
      const d = await fetchStudentAnalyticsData(studentFilters);
      setStudentData(d);
      const now = new Date();
      setRefreshedAt(now);
      try { localStorage.setItem('lastUpdated', now.toLocaleTimeString()); } catch {}
    } catch {
      setStudentError('Failed to load student analytics');
    } finally {
      setStudentLoading(false);
    }
  }

  // Load data when filters change
  useEffect(() => {
    if (activeSection === "operations") {
      void loadSystemData();
    }
  }, [systemFilters, activeSection]);

  useEffect(() => {
    if (activeSection === "staff") {
      void loadStaffData();
    }
  }, [staffFilters, activeSection]);

  useEffect(() => {
    if (activeSection === "student") {
      void loadStudentData();
    }
  }, [studentFilters, activeSection]);

  const sections: Array<{ id: AnalyticsSection; label: string; icon: React.ComponentType<any> }> = [
    { id: "operations", label: "Operations", icon: BarChart3 },
    { id: "finance", label: "Finance", icon: DollarSign },
    { id: "staff", label: "Staff Analytics", icon: Users },
    { id: "student", label: "Student Analytics", icon: GraduationCap },
  ];

  const renderOperationsAnalytics = () => (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      {systemError && <div className="text-red-600 text-sm mb-4" role="alert">{systemError}</div>}
      <div className="flex items-center justify-between mb-6">
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
        <div className={`transition-opacity duration-300 ${systemLoading || reduceMotion ? '' : 'opacity-100'}`}>
          <ResourceMetrics data={systemData.resources} />
        </div>
      )}
    </div>
  );

  const renderFinanceAnalytics = () => (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      {systemError && <div className="text-red-600 text-sm mb-4" role="alert">{systemError}</div>}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <AnalyticsFiltersComponent filters={systemFilters} onFiltersChange={setSystemFilters} />
        </div>
        {systemLoading && <div className="text-xs text-gray-500">Loading…</div>}
      </div>
      
      {!systemData && systemLoading && (
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
      
      {systemData && (
        <div className={`transition-opacity duration-300 ${systemLoading || reduceMotion ? '' : 'opacity-100'}`}>
          <FinancialSummary data={systemData} />
        </div>
      )}

      {systemData && (
        <div className={`mt-6 transition-opacity duration-300 ${systemLoading || reduceMotion ? '' : 'opacity-100'}`}>
          <div className="bg-blue-50 rounded-lg p-6 border border-blue-200">
            <h3 className="text-lg font-semibold text-blue-900 mb-4">Enhanced Financial Features</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-blue-800 mb-2">Cost Analysis by Material</h4>
                <p className="text-blue-700 text-sm">Detailed breakdown of costs by filament vs resin usage</p>
              </div>
              <div>
                <h4 className="font-medium text-blue-800 mb-2">Revenue Trends</h4>
                <p className="text-blue-700 text-sm">Historical revenue patterns and forecasting</p>
              </div>
              <div>
                <h4 className="font-medium text-blue-800 mb-2">Payment Processing</h4>
                <p className="text-blue-700 text-sm">Payment success rates and transaction tracking</p>
              </div>
              <div>
                <h4 className="font-medium text-blue-800 mb-2">Export Functionality</h4>
                <p className="text-blue-700 text-sm">Financial reports and data export capabilities</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderStaffAnalytics = () => (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      {staffError && <div className="text-red-600 text-sm mb-4" role="alert">{staffError}</div>}
      
      <div className="flex items-center justify-between mb-6">
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

  const renderStudentAnalytics = () => (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
      {studentError && <div className="text-red-600 text-sm mb-4" role="alert">{studentError}</div>}
      
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <StudentAnalyticsFiltersComponent filters={studentFilters} onFiltersChange={setStudentFilters} />
        </div>
        {studentLoading && <div className="text-xs text-gray-500">Loading…</div>}
      </div>

      {!studentData && studentLoading && (
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

      {studentData && (
        <div className={`transition-opacity duration-300 ${studentLoading || reduceMotion ? '' : 'opacity-100'}`}>
          {/* Student Overview Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
              <div className="text-sm text-blue-600 font-medium">Total Students</div>
              <div className="text-2xl font-bold text-blue-900">{studentData.overview.totalStudents}</div>
            </div>
            <div className="bg-green-50 rounded-lg p-4 border border-green-200">
              <div className="text-sm text-green-600 font-medium">Active Students</div>
              <div className="text-2xl font-bold text-green-900">{studentData.overview.activeStudents}</div>
            </div>
            <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
              <div className="text-sm text-purple-600 font-medium">Avg Jobs/Student</div>
              <div className="text-2xl font-bold text-purple-900">{studentData.overview.avgJobsPerStudent}</div>
            </div>
            <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
              <div className="text-sm text-orange-600 font-medium">Most Active</div>
              <div className="text-lg font-semibold text-orange-900 truncate">{studentData.overview.mostActiveStudent}</div>
            </div>
          </div>

          {/* Student Activity Trends */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 mb-6">
            <h3 className="text-base font-semibold mb-3">Student Activity Trends</h3>
            <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
              <div className="text-center text-gray-500">
                <p className="text-sm">Submissions by Day/Week/Month</p>
                <p className="text-xs mt-1">Peak usage times and seasonal patterns</p>
                {studentData.trends.submissionsByDay.length === 0 && (
                  <p className="text-xs mt-2">No data available</p>
                )}
              </div>
            </div>
          </div>

          {/* Student Performance Metrics */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 mb-6">
            <h3 className="text-base font-semibold mb-3">Student Performance Metrics</h3>
            <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
              <div className="text-center text-gray-500">
                <p className="text-sm">Approval Rates & Average Costs</p>
                <p className="text-xs mt-1">Learning curves and common rejection reasons</p>
                {Object.keys(studentData.performance.approvalRates).length === 0 && (
                  <p className="text-xs mt-2">No performance data available</p>
                )}
              </div>
            </div>
          </div>

          {/* Discipline Analysis */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 mb-6">
            <h3 className="text-base font-semibold mb-3">Discipline Analysis</h3>
            <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
              <div className="text-center text-gray-500">
                <p className="text-sm">Submissions by Discipline</p>
                <p className="text-xs mt-1">Success rates and popular printers by field</p>
                {Object.keys(studentData.trends.submissionsByDiscipline).length === 0 && (
                  <p className="text-xs mt-2">No discipline data available</p>
                )}
              </div>
            </div>
          </div>

          {/* Student Comparison Table */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
            <h3 className="text-base font-semibold mb-3">Student Comparison</h3>
            <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
              <div className="text-center text-gray-500">
                <p className="text-sm">Student Leaderboard</p>
                <p className="text-xs mt-1">Top students by submissions, spending, success rate</p>
                <p className="text-xs mt-2">Detailed student journey analysis</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderSection = () => {
    switch (activeSection) {
      case "operations":
        return renderOperationsAnalytics();
      case "finance":
        return renderFinanceAnalytics();
      case "staff":
        return renderStaffAnalytics();
      case "student":
        return renderStudentAnalytics();
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col lg:flex-row gap-6 mt-8">
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


