import { renderWithProviders } from '../../../jest.setup';
import AnalyticsPage from './page';
import { screen, waitFor } from '@testing-library/react';

describe('/analytics page', () => {
  beforeEach(() => {
    (global as any).fetch = jest.fn((url: string) => {
      if (url.includes('/api/v1/analytics/overview')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({
          total_submissions: 10,
          in_queue: 4,
          avg_turnaround_hours: 18.5,
          storage_usage_percent: 45.2,
          by_status: { UPLOADED: 3, PENDING: 1 },
          recent_rejections_30d: 1,
        }) });
      }
      if (url.includes('/api/v1/analytics/trends')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({
          series: [{ date: '2025-08-01', count: 2 }], approvals: [{ date: '2025-08-01', count: 1 }], metric: 'submissions'
        }) });
      }
      if (url.includes('/api/v1/analytics/resources')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({
          printing_throughput: [], average_lead_time: [], printer_utilization: [], material_consumption_g: { filament: 0, resin: 0 }, queue_age_buckets: {}, revenue_over_time: [], total_revenue_cents: 0, avg_ticket_usd: 0, payment_count: 0,
        }) });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });
    localStorage.setItem('token', 'test');
  });

  it('renders overview and trends', async () => {
    renderWithProviders(<AnalyticsPage />);
    await waitFor(() => {
      // Header is handled globally; just verify core sections render
      expect(screen.getByText(/Overview/)).toBeInTheDocument();
      expect(screen.getByText(/UPLOADED/)).toBeInTheDocument();
      expect(screen.getByText(/Submissions & Approvals/)).toBeInTheDocument();
      expect(screen.getByText(/Printer Utilization/)).toBeInTheDocument();
      expect(screen.getByText(/Revenue Over Time/)).toBeInTheDocument();
    });
  });
});


