// Optimized Analytics API with request batching and intelligent caching
// This reduces 4 separate API calls to a single batched request

import { optimizedApi } from './optimized-api';
import type { AnalyticsData, OverviewData, TrendData, ResourcesData, FinancialData, AnalyticsFilters } from '../types/analytics';

interface BatchedAnalyticsResponse {
  overview: any;
  trends: any;
  resources: any;
  financial: any;
}

/**
 * Optimized analytics data fetching with request batching
 * Reduces 4 separate API calls to a single batched request
 */
export async function fetchOptimizedAnalyticsData(params: AnalyticsFilters): Promise<AnalyticsData> {
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

  // Batch all analytics requests into a single call
  const batchedResponse = await optimizedApi.batchRequests<BatchedAnalyticsResponse>([
    {
      key: 'overview',
      url: `/api/v1/analytics/overview?${qp.toString()}`,
      config: { ttl: 5 * 60 * 1000 } // 5 minutes
    },
    {
      key: 'trends', 
      url: `/api/v1/analytics/trends?${qpTrends.toString()}`,
      config: { ttl: 5 * 60 * 1000 } // 5 minutes
    },
    {
      key: 'resources',
      url: `/api/v1/analytics/resources?${qp.toString()}`,
      config: { ttl: 5 * 60 * 1000 } // 5 minutes
    },
    {
      key: 'financial',
      url: `/api/v1/analytics/financial?${qp.toString()}`,
      config: { ttl: 5 * 60 * 1000 } // 5 minutes
    }
  ]);

  // Transform batched response to match existing format
  const overview: OverviewData = {
    totalSubmissions: batchedResponse.overview.total_submissions ?? 0,
    inQueue: batchedResponse.overview.in_queue ?? 0,
    avgTurnaroundHours: batchedResponse.overview.avg_turnaround_hours ?? null,
    storageUsagePercent: batchedResponse.overview.storage_usage_percent ?? null,
    byStatus: batchedResponse.overview.by_status ?? {},
    recentRejections: batchedResponse.overview.recent_rejections ?? 0,
    dateRange: batchedResponse.overview.date_range ?? { start: '', end: '' },
  };

  const trends: TrendData = {
    submissions: batchedResponse.trends.series ?? [],
    approvals: batchedResponse.trends.approvals ?? [],
    staffSubmissions: batchedResponse.trends.staff_submissions ?? {},
    staffApprovals: batchedResponse.trends.staff_approvals ?? {},
    dateRange: batchedResponse.trends.date_range ?? { start: '', end: '' },
  };

  const resources: ResourcesData = {
    printingThroughput: batchedResponse.resources.printing_throughput ?? [],
    averageLeadTime: batchedResponse.resources.average_lead_time ?? [],
    printerUtilization: batchedResponse.resources.printer_utilization ?? [],
    materialConsumptionG: batchedResponse.resources.material_consumption_g ?? { filament: 0, resin: 0 },
    queueAgeBuckets: batchedResponse.resources.queue_age_buckets ?? {},
    revenueOverTime: batchedResponse.resources.revenue_over_time ?? [],
    totalRevenueCents: batchedResponse.resources.total_revenue_cents ?? 0,
    avgTicketUsd: batchedResponse.resources.avg_ticket_usd ?? 0,
    paymentCount: batchedResponse.resources.payment_count ?? 0,
    staffPrinting: batchedResponse.resources.staff_printing ?? {},
    staffPayments: batchedResponse.resources.staff_payments ?? {},
    dateRange: batchedResponse.resources.date_range ?? { start: '', end: '' },
  };

  const financial: FinancialData = {
    totalRevenueCents: batchedResponse.financial.total_revenue_cents ?? 0,
    paymentCount: batchedResponse.financial.payment_count ?? 0,
    avgTicketUsd: batchedResponse.financial.avg_ticket_usd ?? 0,
    revenueOverTime: batchedResponse.financial.revenue_over_time ?? [],
    staffRevenue: batchedResponse.financial.staff_revenue ?? {},
    estimatedRevenueCents: batchedResponse.financial.estimated_revenue_cents ?? 0,
    actualRevenueCents: batchedResponse.financial.actual_revenue_cents ?? 0,
    varianceCents: batchedResponse.financial.variance_cents ?? 0,
    dateRange: batchedResponse.financial.date_range ?? { start: '', end: '' },
  };

  return { overview, trends, resources, financial };
}

/**
 * Optimized staff analytics data fetching
 */
export async function fetchOptimizedStaffAnalyticsData(params: any): Promise<any> {
  const qp = new URLSearchParams();
  
  if (params.startDate && params.endDate) {
    qp.set('start_date', params.startDate);
    qp.set('end_date', params.endDate);
  } else {
    const days = params.period || 7;
    qp.set('days', String(days));
  }
  
  if (params.staff) qp.set('staff', params.staff);

  return optimizedApi.request(`/api/v1/analytics/staff?${qp.toString()}`, {}, {
    ttl: 2 * 60 * 1000, // 2 minutes
    polling: {
      enabled: false // Staff analytics don't need polling
    }
  });
}

/**
 * Optimized student analytics data fetching
 */
export async function fetchOptimizedStudentAnalyticsData(params: any): Promise<any> {
  const qp = new URLSearchParams();
  
  if (params.startDate && params.endDate) {
    qp.set('start_date', params.startDate);
    qp.set('end_date', params.endDate);
  } else {
    const days = params.period || 7;
    qp.set('days', String(days));
  }

  return optimizedApi.request(`/api/v1/analytics/student?${qp.toString()}`, {}, {
    ttl: 2 * 60 * 1000, // 2 minutes
    polling: {
      enabled: false // Student analytics don't need polling
    }
  });
}

/**
 * Preload analytics data for better performance
 */
export async function preloadAnalyticsData(): Promise<void> {
  const defaultFilters: AnalyticsFilters = {
    period: 7,
    printer: 'all',
    discipline: 'all'
  };

  try {
    // Preload common analytics data
    await fetchOptimizedAnalyticsData(defaultFilters);
  } catch (error) {
    // Silently fail preload requests
  }
}
