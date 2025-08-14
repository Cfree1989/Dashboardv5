import React from 'react';
import type { StaffPerformanceData } from '../../types/analytics';
import { Calendar, Clock, CheckCircle, XCircle, Activity } from 'lucide-react';

type Props = { data: StaffPerformanceData };

function formatNumber(num: number): string {
  return num.toLocaleString();
}

function formatPercentage(percent: number): string {
  return `${percent.toFixed(1)}%`;
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString();
}

function formatTime(timestamp: string): string {
  return new Date(timestamp).toLocaleTimeString();
}

export function StaffPerformanceDetail({ data }: Props) {
  const { staffName, dailyActivity, performanceTrends, qualityMetrics } = data;
  const activityDates = Object.keys(dailyActivity).sort();

  return (
    <div className="space-y-6">
      {/* Staff Header */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
            <span className="text-blue-600 font-semibold text-lg">
              {staffName.charAt(0).toUpperCase()}
            </span>
          </div>
          <div>
            <h2 className="text-xl font-semibold text-gray-900">{staffName}</h2>
            <p className="text-gray-600">Individual Performance Analysis</p>
          </div>
        </div>

        {/* Quality Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="rounded-lg border border-gray-200 p-3 text-center">
            <div className="flex items-center justify-center mb-2">
              <Activity size={16} className="text-blue-600" />
            </div>
            <div className="text-xl font-semibold text-gray-900">{formatNumber(qualityMetrics.totalReviewed)}</div>
            <div className="text-xs text-gray-600">Jobs Reviewed</div>
          </div>
          
          <div className="rounded-lg border border-gray-200 p-3 text-center">
            <div className="flex items-center justify-center mb-2">
              <CheckCircle size={16} className="text-green-600" />
            </div>
            <div className="text-xl font-semibold text-green-600">{formatNumber(qualityMetrics.approvals)}</div>
            <div className="text-xs text-gray-600">Approvals</div>
          </div>
          
          <div className="rounded-lg border border-gray-200 p-3 text-center">
            <div className="flex items-center justify-center mb-2">
              <XCircle size={16} className="text-red-600" />
            </div>
            <div className="text-xl font-semibold text-red-600">{formatNumber(qualityMetrics.rejections)}</div>
            <div className="text-xs text-gray-600">Rejections</div>
          </div>
          
          <div className="rounded-lg border border-gray-200 p-3 text-center">
            <div className="flex items-center justify-center mb-2">
              <Clock size={16} className="text-purple-600" />
            </div>
            <div className="text-xl font-semibold text-purple-600">{formatPercentage(qualityMetrics.approvalRatePercent)}</div>
            <div className="text-xs text-gray-600">Approval Rate</div>
          </div>
        </div>
      </div>

      {/* Performance Trends */}
      {performanceTrends.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Trends</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-2 font-medium text-gray-900">Date</th>
                  <th className="text-right py-2 font-medium text-gray-900">Total Actions</th>
                  <th className="text-right py-2 font-medium text-gray-900">Approvals</th>
                  <th className="text-right py-2 font-medium text-gray-900">Rejections</th>
                  <th className="text-right py-2 font-medium text-gray-900">Completions</th>
                </tr>
              </thead>
              <tbody>
                {performanceTrends.map((trend) => (
                  <tr key={trend.date} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 font-medium text-gray-900">
                      {formatDate(trend.date)}
                    </td>
                    <td className="py-3 text-right text-gray-900">
                      {formatNumber(trend.totalActions)}
                    </td>
                    <td className="py-3 text-right text-green-600">
                      {formatNumber(trend.approvals)}
                    </td>
                    <td className="py-3 text-right text-red-600">
                      {formatNumber(trend.rejections)}
                    </td>
                    <td className="py-3 text-right text-blue-600">
                      {formatNumber(trend.completions)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Daily Activity Timeline */}
      {activityDates.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Daily Activity Timeline</h3>
          <div className="space-y-4">
            {activityDates.map((date) => {
              const activities = dailyActivity[date];
              
              return (
                <div key={date} className="border-l-4 border-blue-200 pl-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Calendar size={14} className="text-gray-500" />
                    <span className="font-medium text-gray-900">{formatDate(date)}</span>
                    <span className="text-sm text-gray-500">({activities.length} actions)</span>
                  </div>
                  
                  <div className="space-y-2 ml-6">
                    {activities.map((activity, index) => (
                      <div key={index} className="flex items-center gap-3 text-sm">
                        <div className="w-2 h-2 rounded-full bg-blue-400"></div>
                        <span className="text-gray-500">{formatTime(activity.timestamp)}</span>
                        <span className="font-medium text-gray-900">
                          {activity.eventType.replace(/([A-Z])/g, ' $1').trim()}
                        </span>
                        {activity.jobId && (
                          <span className="text-gray-500 text-xs">Job: {activity.jobId}</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Performance Summary */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Summary</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium text-gray-900 mb-2">Quality Metrics</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Total Jobs Reviewed:</span>
                <span className="font-medium">{formatNumber(qualityMetrics.totalReviewed)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Approval Rate:</span>
                <span className="font-medium text-green-600">{formatPercentage(qualityMetrics.approvalRatePercent)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Rejection Rate:</span>
                <span className="font-medium text-red-600">
                  {formatPercentage(100 - qualityMetrics.approvalRatePercent)}
                </span>
              </div>
            </div>
          </div>
          
          <div>
            <h4 className="font-medium text-gray-900 mb-2">Activity Summary</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Active Days:</span>
                <span className="font-medium">{activityDates.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Total Actions:</span>
                <span className="font-medium">
                  {formatNumber(performanceTrends.reduce((sum, t) => sum + t.totalActions, 0))}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Average Actions/Day:</span>
                <span className="font-medium">
                  {activityDates.length > 0 
                    ? formatNumber(Math.round(performanceTrends.reduce((sum, t) => sum + t.totalActions, 0) / activityDates.length))
                    : '0'
                  }
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
