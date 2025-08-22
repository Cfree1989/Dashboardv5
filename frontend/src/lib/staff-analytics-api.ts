import type { StaffAnalyticsData, StaffAnalyticsFilters, StaffOverviewData, StaffPerformanceData, StaffComparisonResult, StaffPerformance } from '../types/analytics';
import { apiRequest } from './auth';

export async function fetchStaffAnalyticsData(params: StaffAnalyticsFilters): Promise<StaffAnalyticsData> {
  // Build query parameters
  const qp = new URLSearchParams();
  
  // Use date range if provided, otherwise fall back to days
  if (params.startDate && params.endDate) {
    qp.set('start_date', params.startDate);
    qp.set('end_date', params.endDate);
  } else {
    const days = params.period || 7;
    qp.set('days', String(days));
  }
  
  if (params.staff) qp.set('staff', params.staff);

  // Fetch all staff analytics data
  const [overviewJson, comparisonJson] = await Promise.all([
    apiRequest<any>(`/api/v1/analytics/staff/overview?${qp.toString()}`),
    apiRequest<any>(`/api/v1/analytics/staff/comparison?${qp.toString()}`),
  ]);

  // Parse overview data and map staff_performance to camelCase
  const rawStaffPerf: Record<string, any> = overviewJson.staff_performance ?? {};
  const staffPerformance: Record<string, StaffPerformance> = {};
  for (const [name, perf] of Object.entries(rawStaffPerf)) {
    staffPerformance[name] = {
      totalActions: perf.total_actions ?? 0,
      approvals: perf.approvals ?? 0,
      rejections: perf.rejections ?? 0,
      completions: perf.completions ?? 0,
      payments: perf.payments ?? 0,
      avgResponseTimeHours: perf.avg_response_time_hours ?? null,
      completionRatePercent: perf.completion_rate_percent ?? 0,
      actionBreakdown: perf.action_breakdown ?? {},
    };
  }
  const overview: StaffOverviewData = {
    staffPerformance,
    teamMetrics: {
      totalActions: overviewJson.team_metrics?.total_actions ?? 0,
      totalApprovals: overviewJson.team_metrics?.total_approvals ?? 0,
      totalRejections: overviewJson.team_metrics?.total_rejections ?? 0,
      activeStaffCount: overviewJson.team_metrics?.active_staff_count ?? 0,
    },
    workloadDistribution: overviewJson.workload_distribution ?? {},
    dateRange: overviewJson.date_range ?? { start: '', end: '' },
  };

  // Parse comparison data
  const comparison: StaffComparisonResult = {
    comparisonData: comparisonJson.comparison_data ?? {},
    rankings: {
      productivity: comparisonJson.rankings?.productivity ?? [],
      quality: comparisonJson.rankings?.quality ?? [],
    },
    dateRange: comparisonJson.date_range ?? { start: '', end: '' },
  };

  // Fetch individual staff performance if staff is specified
  let performance: StaffPerformanceData | undefined;
  if (params.staff) {
    try {
      const performanceJson = await apiRequest<any>(`/api/v1/analytics/staff/performance?${qp.toString()}`);
      
      performance = {
        staffName: performanceJson.staff_name ?? '',
        dailyActivity: performanceJson.daily_activity ?? {},
        performanceTrends: performanceJson.performance_trends ?? [],
        qualityMetrics: {
          totalReviewed: performanceJson.quality_metrics?.total_reviewed ?? 0,
          approvals: performanceJson.quality_metrics?.approvals ?? 0,
          rejections: performanceJson.quality_metrics?.rejections ?? 0,
          approvalRatePercent: performanceJson.quality_metrics?.approval_rate_percent ?? 0,
        },
        dateRange: performanceJson.date_range ?? { start: '', end: '' },
      };
    } catch (error) {
      // Silently handle staff performance fetch failures
    }
  }

  return { overview, performance, comparison };
}
