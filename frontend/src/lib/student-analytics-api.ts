import type { StudentAnalyticsData, StudentAnalyticsFilters } from '../types/analytics';
import { apiRequest } from './auth';

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

  // Fetch all student analytics data using apiRequest
  const [overviewJson, performanceJson, trendsJson] = await Promise.all([
    apiRequest<any>(`/api/v1/analytics/student/overview?${qp.toString()}`),
    apiRequest<any>(`/api/v1/analytics/student/performance?${qp.toString()}`),
    apiRequest<any>(`/api/v1/analytics/student/trends?${qp.toString()}`),
  ]);
  
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
