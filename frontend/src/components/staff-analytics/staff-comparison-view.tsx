import React from 'react';
import type { StaffComparisonResult } from '../../types/analytics';
import { Trophy, TrendingUp, Award } from 'lucide-react';

type Props = { data: StaffComparisonResult };

function formatNumber(num: number | undefined | null): string {
  if (num === undefined || num === null) return '0';
  return num.toLocaleString();
}

function formatHours(hours: number | null | undefined): string {
  if (hours === null || hours === undefined) return '--';
  return `${hours.toFixed(1)}h`;
}

export function StaffComparisonView({ data }: Props) {
  const { comparisonData, rankings } = data;
  const staffNames = Object.keys(comparisonData);

  if (staffNames.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Staff Comparison</h2>
        <p className="text-gray-500 text-center py-8">No staff data available for comparison</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Rankings */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Performance Rankings</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Productivity Ranking */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp size={16} className="text-green-600" />
              <h3 className="font-medium text-gray-900">Productivity Ranking</h3>
            </div>
            <div className="space-y-2">
              {rankings.productivity.map((staffName, index) => (
                <div key={staffName} className="flex items-center gap-3 p-2 rounded-lg bg-gray-50">
                  <div className="flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 text-blue-600 text-xs font-medium">
                    {index + 1}
                  </div>
                  <span className="font-medium text-gray-900">{staffName}</span>
                  <span className="text-sm text-gray-600">
                    {formatNumber(comparisonData[staffName]?.totalActions || 0)} actions
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Quality Ranking */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Award size={16} className="text-purple-600" />
              <h3 className="font-medium text-gray-900">Quality Ranking</h3>
            </div>
            <div className="space-y-2">
              {rankings.quality.map((staffName, index) => (
                <div key={staffName} className="flex items-center gap-3 p-2 rounded-lg bg-gray-50">
                  <div className="flex items-center justify-center w-6 h-6 rounded-full bg-purple-100 text-purple-600 text-xs font-medium">
                    {index + 1}
                  </div>
                  <span className="font-medium text-gray-900">{staffName}</span>
                  <span className="text-sm text-gray-600">
                    Score: {comparisonData[staffName]?.qualityScore || 0}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Comparison Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Detailed Comparison</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-2 font-medium text-gray-900">Staff Member</th>
                <th className="text-right py-2 font-medium text-gray-900">Total Actions</th>
                <th className="text-right py-2 font-medium text-gray-900">Approvals</th>
                <th className="text-right py-2 font-medium text-gray-900">Rejections</th>
                <th className="text-right py-2 font-medium text-gray-900">Completions</th>
                <th className="text-right py-2 font-medium text-gray-900">Avg Response</th>
                <th className="text-right py-2 font-medium text-gray-900">Productivity Score</th>
                <th className="text-right py-2 font-medium text-gray-900">Quality Score</th>
              </tr>
            </thead>
            <tbody>
              {staffNames.map((staffName) => {
                const data = comparisonData[staffName];
                const isTopProductivity = rankings.productivity[0] === staffName;
                const isTopQuality = rankings.quality[0] === staffName;
                
                return (
                  <tr key={staffName} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 font-medium text-gray-900">
                      <div className="flex items-center gap-2">
                        {staffName}
                        {isTopProductivity && (
                          <div className="relative group">
                            <Trophy size={14} className="text-yellow-500" />
                            <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-1 px-2 py-1 text-xs text-white bg-gray-900 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">
                              Top Productivity
                            </div>
                          </div>
                        )}
                        {isTopQuality && (
                          <div className="relative group">
                            <Award size={14} className="text-purple-500" />
                            <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-1 px-2 py-1 text-xs text-white bg-gray-900 rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap">
                              Top Quality
                            </div>
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="py-3 text-right text-gray-900">
                      {formatNumber(data.totalActions)}
                    </td>
                    <td className="py-3 text-right text-green-600">
                      {formatNumber(data.approvals)}
                    </td>
                    <td className="py-3 text-right text-red-600">
                      {formatNumber(data.rejections)}
                    </td>
                    <td className="py-3 text-right text-blue-600">
                      {formatNumber(data.completions)}
                    </td>
                    <td className="py-3 text-right text-gray-900">
                      {formatHours(data.avgResponseTimeHours)}
                    </td>
                    <td className="py-3 text-right text-gray-900">
                      {formatNumber(data.productivityScore)}
                    </td>
                    <td className="py-3 text-right text-gray-900">
                      {formatNumber(data.qualityScore)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Performance Insights */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Performance Insights</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {rankings.productivity.length > 0 && (
            <div className="p-4 bg-green-50 rounded-lg border border-green-200">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp size={16} className="text-green-600" />
                <h3 className="font-medium text-green-900">Most Productive</h3>
              </div>
              <p className="text-green-800">
                <strong>{rankings.productivity[0]}</strong> completed the most actions with{' '}
                {formatNumber(comparisonData[rankings.productivity[0]]?.totalActions || 0)} total actions.
              </p>
            </div>
          )}
          
          {rankings.quality.length > 0 && (
            <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
              <div className="flex items-center gap-2 mb-2">
                <Award size={16} className="text-purple-600" />
                <h3 className="font-medium text-purple-900">Highest Quality</h3>
              </div>
              <p className="text-purple-800">
                <strong>{rankings.quality[0]}</strong> achieved the highest quality score with{' '}
                {formatNumber(comparisonData[rankings.quality[0]]?.qualityScore || 0)} points.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
