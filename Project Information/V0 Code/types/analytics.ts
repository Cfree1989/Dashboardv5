export interface OverviewData {
  totalSubmissions: number
  inQueueByStatus: {
    uploaded: number
    pending: number
    readyToPrint: number
    printing: number
    completed: number
  }
  averageTurnaround: number // in hours
  storageUsed: number
  storageLimit: number
  recentRejections: number
}

export interface TrendData {
  submissionsOverTime: Array<{ date: string; submissions: number; approvals: number }>
  printingThroughput: Array<{ date: string; completed: number }>
  averageLeadTime: Array<{ date: string; hours: number }>
}

export interface ResourceData {
  printerUtilization: Array<{
    printer: string
    utilization: Array<{ date: string; hours: number }>
  }>
  materialConsumption: {
    filament: number // grams
    resin: number // grams
  }
  queueAgeDistribution: Array<{ ageRange: string; count: number }>
}

export interface FinancialData {
  revenueByPeriod: Array<{ period: string; revenue: number }>
  averageTicketSize: number
  paymentCounts: {
    paid: number
    unpaid: number
  }
}

export interface AnalyticsData {
  overview: OverviewData
  trends: TrendData
  resources: ResourceData
  financial: FinancialData
}

export interface AnalyticsFilters {
  period: 7 | 30 | 90
  discipline: string
  printer: string
}
