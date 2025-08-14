import type { AnalyticsData, OverviewData, TrendData, ResourcesData, FinancialData, AnalyticsFilters } from '../types/analytics';

export async function fetchAnalyticsData(params: AnalyticsFilters): Promise<AnalyticsData> {
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
  
  if (params.printer && params.printer !== 'all') qp.set('printer', params.printer);
  if (params.discipline && params.discipline !== 'all') qp.set('discipline', params.discipline);

  // For trends, use a longer period if no specific date range is provided
  const qpTrends = new URLSearchParams(qp);
  if (!params.startDate || !params.endDate) {
    const days = Math.max(params.period || 7, 30);
    qpTrends.set('days', String(days));
  }

  const [oRes, tRes, rRes, fRes] = await Promise.all([
    fetch(`/api/v1/analytics/overview?${qp.toString()}`, { headers: h }),
    fetch(`/api/v1/analytics/trends?${qpTrends.toString()}`, { headers: h }),
    fetch(`/api/v1/analytics/resources?${qp.toString()}`, { headers: h }),
    fetch(`/api/v1/analytics/financial?${qp.toString()}`, { headers: h }),
  ]);

  const overviewJson = await oRes.json();
  const trendsJson = await tRes.json();
  const resourcesJson = await rRes.json();
  const financialJson = await fRes.json();

  const overview: OverviewData = {
    totalSubmissions: overviewJson.total_submissions ?? 0,
    inQueue: overviewJson.in_queue ?? 0,
    avgTurnaroundHours: overviewJson.avg_turnaround_hours ?? null,
    storageUsagePercent: overviewJson.storage_usage_percent ?? null,
    byStatus: overviewJson.by_status ?? {},
    recentRejections: overviewJson.recent_rejections ?? 0,
    dateRange: overviewJson.date_range ?? { start: '', end: '' },
  };

  const trends: TrendData = {
    submissions: trendsJson.series ?? [],
    approvals: trendsJson.approvals ?? [],
    staffSubmissions: trendsJson.staff_submissions ?? {},
    staffApprovals: trendsJson.staff_approvals ?? {},
    dateRange: trendsJson.date_range ?? { start: '', end: '' },
  };

  const resources: ResourcesData = {
    printingThroughput: resourcesJson.printing_throughput ?? [],
    averageLeadTime: resourcesJson.average_lead_time ?? [],
    printerUtilization: resourcesJson.printer_utilization ?? [],
    materialConsumptionG: resourcesJson.material_consumption_g ?? { filament: 0, resin: 0 },
    queueAgeBuckets: resourcesJson.queue_age_buckets ?? {},
    revenueOverTime: resourcesJson.revenue_over_time ?? [],
    totalRevenueCents: resourcesJson.total_revenue_cents ?? 0,
    avgTicketUsd: resourcesJson.avg_ticket_usd ?? 0,
    paymentCount: resourcesJson.payment_count ?? 0,
    staffPrinting: resourcesJson.staff_printing ?? {},
    staffPayments: resourcesJson.staff_payments ?? {},
    dateRange: resourcesJson.date_range ?? { start: '', end: '' },
  };

  const financial: FinancialData = {
    totalRevenueCents: financialJson.total_revenue_cents ?? 0,
    paymentCount: financialJson.payment_count ?? 0,
    avgTicketUsd: financialJson.avg_ticket_usd ?? 0,
    revenueOverTime: financialJson.revenue_over_time ?? [],
    staffRevenue: financialJson.staff_revenue ?? {},
    dateRange: financialJson.date_range ?? { start: '', end: '' },
  };

  return { overview, trends, resources, financial };
}


