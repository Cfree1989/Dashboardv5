export type DateCount = { date: string; count: number };

export type OverviewData = {
  totalSubmissions: number;
  inQueue: number;
  avgTurnaroundHours: number | null;
  storageUsagePercent: number | null;
  byStatus: Record<string, number>;
  recentRejections30d: number;
};

export type TrendData = {
  submissions: DateCount[];
  approvals: DateCount[];
};

export type UtilizationSeries = { printer: string; series: DateCount[] };

export type RevenuePoint = { date: string; cents: number };

export type ResourcesData = {
  printingThroughput: DateCount[];
  averageLeadTime: { date: string; hours: number }[];
  printerUtilization: UtilizationSeries[];
  materialConsumptionG: { filament: number; resin: number };
  queueAgeBuckets: Record<string, number>;
  revenueOverTime: RevenuePoint[];
  totalRevenueCents: number;
  avgTicketUsd: number;
  paymentCount: number;
};

export type AnalyticsData = {
  overview: OverviewData;
  trends: TrendData;
  resources: ResourcesData;
  // Derived financial KPIs from resources + overview
  financial: {
    totalRevenueUsd: number;
    averageTicketUsd: number;
    paymentRatePercent: number; // paid picked up / (completed+paidpickedup) * 100
    revenueByPeriod: { period: string; revenueUsd: number }[];
  };
};


