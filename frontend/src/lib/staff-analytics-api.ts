import type { StaffAnalyticsData, StaffAnalyticsFilters, StaffOverviewData, StaffPerformanceData, StaffComparisonResult, StaffPerformance } from '../types/analytics';

export async function fetchStaffAnalyticsData(params: StaffAnalyticsFilters): Promise<StaffAnalyticsData> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  const h: HeadersInit = token ? { Authorization: `Bearer ${token}` } : {};
  
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
  const [overviewRes, comparisonRes] = await Promise.all([
    fetch(`/api/v1/analytics/staff/overview?${qp.toString()}`, { headers: h }),
    fetch(`/api/v1/analytics/staff/comparison?${qp.toString()}`, { headers: h }),
  ]);

  const overviewJson = await overviewRes.json();
  const comparisonJson = await comparisonRes.json();

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
      const performanceRes = await fetch(`/api/v1/analytics/staff/performance?${qp.toString()}`, { headers: h });
      const performanceJson = await performanceRes.json();
      
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
      console.error('Failed to fetch staff performance:', error);
    }
  }

  return { overview, performance, comparison };
}
