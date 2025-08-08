import type { AnalyticsData, AnalyticsFilters } from "@/types/analytics"

// Mock analytics data
export async function fetchAnalyticsData(filters: AnalyticsFilters): Promise<AnalyticsData> {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 500))

  // Generate mock data based on filters
  const mockData: AnalyticsData = {
    overview: {
      totalSubmissions: 1247,
      inQueueByStatus: {
        uploaded: 12,
        pending: 8,
        readyToPrint: 5,
        printing: 3,
        completed: 15,
      },
      averageTurnaround: 18.5,
      storageUsed: 45.2,
      storageLimit: 100,
      recentRejections: 7,
    },
    trends: {
      submissionsOverTime: generateTimeSeriesData(filters.period, 'submissions'),
      printingThroughput: generateTimeSeriesData(filters.period, 'throughput'),
      averageLeadTime: generateTimeSeriesData(filters.period, 'leadtime'),
    },
    resources: {
      printerUtilization: [
        {
          printer: "Prusa MK4S",
          utilization: generateTimeSeriesData(filters.period, 'utilization'),
        },
        {
          printer: "Prusa XL",
          utilization: generateTimeSeriesData(filters.period, 'utilization'),
        },
        {
          printer: "Formlabs Form 3",
          utilization: generateTimeSeriesData(filters.period, 'utilization'),
        },
      ],
      materialConsumption: {
        filament: 2450, // grams
        resin: 890, // grams
      },
      queueAgeDistribution: [
        { ageRange: "0-24h", count: 15 },
        { ageRange: "1-3 days", count: 8 },
        { ageRange: "3-7 days", count: 4 },
        { ageRange: "7+ days", count: 2 },
      ],
    },
    financial: {
      revenueByPeriod: generateRevenueData(filters.period),
      averageTicketSize: 12.45,
      paymentCounts: {
        paid: 234,
        unpaid: 18,
      },
    },
  }

  return mockData
}

function generateTimeSeriesData(days: number, type: string) {
  const data = []
  const now = new Date()
  
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(now)
    date.setDate(date.getDate() - i)
    
    let value = 0
    switch (type) {
      case 'submissions':
        value = Math.floor(Math.random() * 20) + 5
        break
      case 'throughput':
        value = Math.floor(Math.random() * 15) + 3
        break
      case 'leadtime':
        value = Math.floor(Math.random() * 10) + 15
        break
      case 'utilization':
        value = Math.floor(Math.random() * 8) + 2
        break
    }
    
    if (type === 'submissions') {
      data.push({
        date: date.toISOString().split('T')[0],
        submissions: value,
        approvals: Math.floor(value * 0.85),
      })
    } else if (type === 'throughput') {
      data.push({
        date: date.toISOString().split('T')[0],
        completed: value,
      })
    } else if (type === 'leadtime') {
      data.push({
        date: date.toISOString().split('T')[0],
        hours: value,
      })
    } else if (type === 'utilization') {
      data.push({
        date: date.toISOString().split('T')[0],
        hours: value,
      })
    }
  }
  
  return data
}

function generateRevenueData(days: number) {
  const data = []
  const now = new Date()
  
  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(now)
    date.setDate(date.getDate() - i)
    
    data.push({
      period: date.toISOString().split('T')[0],
      revenue: Math.floor(Math.random() * 200) + 50,
    })
  }
  
  return data
}
