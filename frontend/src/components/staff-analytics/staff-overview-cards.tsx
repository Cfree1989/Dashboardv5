import React from 'react';
import type { StaffOverviewData } from '../../types/analytics';
import { Users, CheckCircle, XCircle, Clock, TrendingUp } from 'lucide-react';

type Props = { data: StaffOverviewData };

function formatNumber(num: number): string {
  return num.toLocaleString();
}

function formatHours(hours: number | null): string {
  if (hours === null) return '--';
  return `${hours.toFixed(1)}h`;
}

function formatPercentage(percent: number): string {
  return `${percent.toFixed(1)}%`;
}

export function StaffOverviewCards({ data }: Props) {
  const { staffPerformance, teamMetrics, workloadDistribution } = data;
  const staffNames = Object.keys(staffPerformance);

  return (
    <div className="space-y-6">
      {/* Team Overview Cards */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Team Overview</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="rounded-lg border border-gray-200 p-3 text-center">
            <div className="flex items-center justify-center mb-2">
              <Users size={16} className="text-blue-600" />
            </div>
            <div className="text-xl font-semibold text-gray-900">{teamMetrics.activeStaffCount}</div>
            <div className="text-xs text-gray-600">Active Staff</div>
          </div>
          
          <div className="rounded-lg border border-gray-200 p-3 text-center">
            <div className="flex items-center justify-center mb-2">
              <TrendingUp size={16} className="text-green-600" />
            </div>
            <div className="text-xl font-semibold text-gray-900">{formatNumber(teamMetrics.totalActions)}</div>
            <div className="text-xs text-gray-600">Total Actions</div>
          </div>
          
          <div className="rounded-lg border border-gray-200 p-3 text-center">
            <div className="flex items-center justify-center mb-2">
              <CheckCircle size={16} className="text-green-600" />
            </div>
            <div className="text-xl font-semibold text-gray-900">{formatNumber(teamMetrics.totalApprovals)}</div>
            <div className="text-xs text-gray-600">Approvals</div>
          </div>
          
          <div className="rounded-lg border border-gray-200 p-3 text-center">
            <div className="flex items-center justify-center mb-2">
              <XCircle size={16} className="text-red-600" />
            </div>
            <div className="text-xl font-semibold text-gray-900">{formatNumber(teamMetrics.totalRejections)}</div>
            <div className="text-xs text-gray-600">Rejections</div>
          </div>
        </div>
      </div>

      {/* Individual Staff Performance */}
      {staffNames.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Staff Performance</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {staffNames.map((staffName) => {
              const perf = staffPerformance[staffName];
              const workloadPercent = workloadDistribution[staffName] || 0;
              
              return (
                <div key={staffName} className="rounded-lg border border-gray-200 p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-medium text-gray-900">{staffName}</h3>
                    <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                      {formatPercentage(workloadPercent)} workload
                    </span>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Total Actions:</span>
                      <span className="font-medium">{formatNumber(perf.totalActions)}</span>
                    </div>
                    
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Approvals:</span>
                      <span className="font-medium text-green-600">{formatNumber(perf.approvals)}</span>
                    </div>
                    
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Rejections:</span>
                      <span className="font-medium text-red-600">{formatNumber(perf.rejections)}</span>
                    </div>
                    
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Completions:</span>
                      <span className="font-medium text-blue-600">{formatNumber(perf.completions)}</span>
                    </div>
                    
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Avg Response:</span>
                      <span className="font-medium">{formatHours(perf.avgResponseTimeHours)}</span>
                    </div>
                    
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Completion Rate:</span>
                      <span className="font-medium">{formatPercentage(perf.completionRatePercent)}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Workload Distribution */}
      {Object.keys(workloadDistribution).length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Workload Distribution</h2>
          <div className="space-y-3">
            {Object.entries(workloadDistribution)
              .sort(([, a], [, b]) => b - a)
              .map(([staffName, percentage]) => (
                <div key={staffName} className="flex items-center gap-3">
                  <div className="w-32 text-sm font-medium text-gray-700">{staffName}</div>
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                  <div className="w-16 text-sm text-gray-600 text-right">{formatPercentage(percentage)}</div>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
