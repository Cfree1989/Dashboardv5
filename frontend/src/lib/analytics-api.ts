import type { AnalyticsData, OverviewData, TrendData, ResourcesData } from '../types/analytics';

export async function fetchAnalyticsData(params: { period: number; discipline?: string; printer?: string }): Promise<AnalyticsData> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  const h: HeadersInit = token ? { Authorization: `Bearer ${token}` } : {};
  const days = params.period || 7;

  const qp = new URLSearchParams();
  qp.set('days', String(days));
  if (params.printer && params.printer !== 'all') qp.set('printer', params.printer);
  if (params.discipline && params.discipline !== 'all') qp.set('discipline', params.discipline);

  const qp30 = new URLSearchParams(qp);
  qp30.set('days', String(Math.max(days, 30)));

  const [oRes, tRes, rRes, fRes] = await Promise.all([
    fetch(`/api/v1/analytics/overview?${qp.toString()}`, { headers: h }),
    fetch(`/api/v1/analytics/trends?${qp30.toString()}`, { headers: h }),
    fetch(`/api/v1/analytics/resources?${qp.toString()}`, { headers: h }),
    fetch(`/api/v1/analytics/financial?${qp.toString()}`, { headers: h }),
  ]);

  const overviewJson = await oRes.json();
  const trendsJson = await tRes.json();
  const resourcesJson = await rRes.json();
  const financialJson = await fRes.json();

  const totalSubs = (overviewJson.total_submissions ?? overviewJson.totalSubmissions ?? overviewJson.total) ?? 0;
  const overview: OverviewData = {
    totalSubmissions: totalSubs,
    inQueue: overviewJson.in_queue ?? 0,
    avgTurnaroundHours: overviewJson.avg_turnaround_hours ?? null,
    storageUsagePercent: overviewJson.storage_usage_percent ?? null,
    byStatus: overviewJson.by_status ?? {},
    recentRejections30d: overviewJson.recent_rejections_30d ?? 0,
  };

  const trends: TrendData = {
    submissions: trendsJson.series ?? [],
    approvals: trendsJson.approvals ?? [],
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
  };

  const financial = {
    totalRevenueUsd: (financialJson.total_revenue_cents ?? resources.totalRevenueCents ?? 0) / 100,
    averageTicketUsd: (financialJson.avg_ticket_usd ?? resources.avgTicketUsd ?? 0),
    paymentRatePercent: (() => {
      // Approximation: proportion of payments among completed+paidpickedup
      const completed = overview.byStatus?.COMPLETED ?? 0;
      const paid = overview.byStatus?.PAIDPICKEDUP ?? 0;
      const denom = completed + paid;
      const paymentsCount = (resources.paymentCount ?? financialJson.payment_count ?? 0);
      return denom > 0 ? Math.round((paymentsCount / denom) * 1000) / 10 : 0;
    })(),
    revenueByPeriod: (financialJson.revenue_over_time ?? resources.revenueOverTime ?? []).map((p: any) => ({ period: p.date, revenueUsd: (p.cents || 0) / 100 })),
    paymentsCount: (financialJson.payment_count ?? resources.paymentCount ?? 0)
  };

  return { overview, trends, resources, financial };
}


