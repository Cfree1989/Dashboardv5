import type { StudentAnalyticsData, StudentAnalyticsFilters } from '../types/analytics';

export async function fetchStudentAnalyticsData(filters: StudentAnalyticsFilters): Promise<StudentAnalyticsData> {
  const qp = new URLSearchParams();
  
  if (filters.period) {
    qp.set('days', filters.period.toString());
  }
  
  if (filters.startDate) {
    qp.set('start_date', filters.startDate);
  }
  
  if (filters.endDate) {
    qp.set('end_date', filters.endDate);
  }

  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';
  
  // Fetch overview data
  const overviewResponse = await fetch(`${baseUrl}/api/v1/analytics/student/overview?${qp.toString()}`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
    },
  });
  
  if (!overviewResponse.ok) {
    throw new Error('Failed to fetch student overview data');
  }
  
  const overviewJson = await overviewResponse.json();
  
  // Fetch performance data
  const performanceResponse = await fetch(`${baseUrl}/api/v1/analytics/student/performance?${qp.toString()}`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
    },
  });
  
  if (!performanceResponse.ok) {
    throw new Error('Failed to fetch student performance data');
  }
  
  const performanceJson = await performanceResponse.json();
  
  // Fetch trends data
  const trendsResponse = await fetch(`${baseUrl}/api/v1/analytics/student/trends?${qp.toString()}`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('token')}`,
    },
  });
  
  if (!trendsResponse.ok) {
    throw new Error('Failed to fetch student trends data');
  }
  
  const trendsJson = await trendsResponse.json();
  
  // Map snake_case JSON to camelCase TypeScript types
  return {
    overview: {
      totalStudents: overviewJson.total_students ?? 0,
      activeStudents: overviewJson.active_students ?? 0,
      avgJobsPerStudent: overviewJson.avg_jobs_per_student ?? 0,
      mostActiveStudent: overviewJson.most_active_student ?? 'No data',
    },
    performance: {
      approvalRates: performanceJson.approval_rates ?? {},
      avgCosts: performanceJson.avg_costs ?? {},
      jobCounts: performanceJson.job_counts ?? {},
      totalCosts: performanceJson.total_costs ?? {},
    },
    trends: {
      submissionsByDay: trendsJson.submissions_by_day ?? [],
      submissionsByDiscipline: trendsJson.submissions_by_discipline ?? {},
    },
    dateRange: {
      start: overviewJson.date_range?.start ?? '',
      end: overviewJson.date_range?.end ?? '',
    },
  };
}
