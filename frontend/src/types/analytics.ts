export type DateCount = { date: string; count: number };

export type StaffActivity = {
  name: string;
  action_count: number;
  is_active: boolean;
};

export type DateRange = {
  start: string;
  end: string;
};

export type OverviewData = {
  totalSubmissions: number;
  inQueue: number;
  avgTurnaroundHours: number | null;
  storageUsagePercent: number | null;
  byStatus: Record<string, number>;
  recentRejections: number;
  dateRange: DateRange;
};

export type TrendData = {
  submissions: DateCount[];
  approvals: DateCount[];
  staffSubmissions: Record<string, number>;
  staffApprovals: Record<string, number>;
  dateRange: DateRange;
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
  staffPrinting: Record<string, number>;
  staffPayments: Record<string, number>;
  dateRange: DateRange;
};

export type FinancialData = {
  totalRevenueCents: number;
  paymentCount: number;
  avgTicketUsd: number;
  revenueOverTime: RevenuePoint[];
  staffRevenue: Record<string, number>;
  dateRange: DateRange;
};

export type AnalyticsData = {
  overview: OverviewData;
  trends: TrendData;
  resources: ResourcesData;
  financial: FinancialData;
};

export type AnalyticsFilters = {
  period: 7 | 30 | 90 | number;
  discipline: string;
  printer: string;
  startDate?: string;
  endDate?: string;
};

// Staff Analytics Types
export type StaffPerformance = {
  totalActions: number;
  approvals: number;
  rejections: number;
  completions: number;
  payments: number;
  avgResponseTimeHours: number | null;
  completionRatePercent: number;
  actionBreakdown: Record<string, number>;
};

export type TeamMetrics = {
  totalActions: number;
  totalApprovals: number;
  totalRejections: number;
  activeStaffCount: number;
};

export type StaffOverviewData = {
  staffPerformance: Record<string, StaffPerformance>;
  teamMetrics: TeamMetrics;
  workloadDistribution: Record<string, number>;
  dateRange: DateRange;
};

export type StaffActivityEvent = {
  timestamp: string;
  eventType: string;
  jobId: string;
  details: any;
};

export type PerformanceTrend = {
  date: string;
  totalActions: number;
  approvals: number;
  rejections: number;
  completions: number;
};

export type QualityMetrics = {
  totalReviewed: number;
  approvals: number;
  rejections: number;
  approvalRatePercent: number;
};

export type StaffPerformanceData = {
  staffName: string;
  dailyActivity: Record<string, StaffActivityEvent[]>;
  performanceTrends: PerformanceTrend[];
  qualityMetrics: QualityMetrics;
  dateRange: DateRange;
};

export type StaffComparisonData = {
  totalActions: number;
  approvals: number;
  rejections: number;
  completions: number;
  avgResponseTimeHours: number | null;
  productivityScore: number;
  qualityScore: number;
};

export type StaffComparisonResult = {
  comparisonData: Record<string, StaffComparisonData>;
  rankings: {
    productivity: string[];
    quality: string[];
  };
  dateRange: DateRange;
};

export type StaffAnalyticsData = {
  overview: StaffOverviewData;
  performance?: StaffPerformanceData;
  comparison: StaffComparisonResult;
};

export type StaffAnalyticsFilters = {
  period: 7 | 30 | 90 | number;
  staff?: string;
  startDate?: string;
  endDate?: string;
};

// Student Analytics Types
export type StudentOverviewData = {
  totalStudents: number;
  activeStudents: number;
  avgJobsPerStudent: number;
  mostActiveStudent: string;
};

export type StudentPerformanceData = {
  approvalRates: Record<string, number>;
  avgCosts: Record<string, number>;
  jobCounts: Record<string, number>;
  totalCosts: Record<string, number>;
};

export type StudentTrendsData = {
  submissionsByDay: DateCount[];
  submissionsByDiscipline: Record<string, number>;
};

export type StudentAnalyticsData = {
  overview: StudentOverviewData;
  performance: StudentPerformanceData;
  trends: StudentTrendsData;
  dateRange: DateRange;
};

export type StudentAnalyticsFilters = {
  period: 7 | 30 | 90 | number;
  startDate?: string;
  endDate?: string;
};


