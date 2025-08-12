import { renderWithProviders } from '../../../jest.setup';
import { SystemHealthPanel } from './system-health';
import { screen, waitFor } from '@testing-library/react';

describe('SystemHealthPanel', () => {
  beforeEach(() => {
    (global as any).fetch = jest.fn((url: string) => {
      if (url.endsWith('/api/v1/_diag')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ db_engine: 'postgresql', email_configured: false }) });
      }
      if (url.endsWith('/api/v1/health')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ status: 'ok', components: { database: 'ok' } }) });
      }
      if (url.endsWith('/api/v1/admin/audit/report')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ report_generated_at: new Date().toISOString(), orphaned_files: [], broken_links: [], stale_files: [] }) });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });
    localStorage.setItem('token', 'test');
  });

  it('renders health and db info', async () => {
    renderWithProviders(<SystemHealthPanel />);
    await waitFor(() => {
      expect(screen.getByText(/Health/i)).toBeInTheDocument();
      expect(screen.getByText(/DB Engine/i)).toBeInTheDocument();
    });
  });
});


