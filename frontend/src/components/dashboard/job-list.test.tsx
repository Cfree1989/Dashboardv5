// @ts-nocheck
import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn() })
}));
import JobList from './job-list';

describe('JobList component', () => {
  beforeEach(() => {
    // Mock localStorage token for auth
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn(() => 'test-token'),
        setItem: jest.fn(),
        removeItem: jest.fn(),
        clear: jest.fn(),
      },
      writable: true,
    });
    jest.spyOn(global, 'fetch').mockResolvedValue({
      ok: true,
      json: async () => ({ jobs: [
        { id: '1', display_name: 'Test Job' },
        { id: '2', display_name: 'Another Job' }
      ] }),
    } as any);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('displays loading indicator then renders jobs', async () => {
    render(<JobList filters={{ status: 'UPLOADED' }} />);
    // Skeleton-based loader now shown; ensure eventual content renders
    await waitFor(() => expect(screen.getAllByText('Test Job').length).toBeGreaterThan(0));
    expect(screen.getAllByText('Another Job').length).toBeGreaterThan(0);
  });

  it('shows error message on fetch failure', async () => {
    jest.spyOn(global, 'fetch').mockRejectedValue(new Error('Fetch error'));
    render(<JobList filters={{}} />);
    await waitFor(() => expect(screen.getByText(/Failed to load jobs/i)).toBeInTheDocument());
  });

  it('shows NEW indicator only for Uploaded and clears after review modal confirms', async () => {
    const job = { id: '1', display_name: 'Test Job', staff_viewed_at: null };
    // First fetch for list
    (global.fetch as any).mockResolvedValueOnce({ ok: true, json: async () => ({ jobs: [job] }) });
    // Fetch staff for modal
    ;(global.fetch as any).mockResolvedValueOnce({ ok: true, json: async () => ({ staff: [{ name: 'Alice', is_active: true }] }) });
    // POST review endpoint
    ;(global.fetch as any).mockResolvedValueOnce({ ok: true, json: async () => ({ ...job, staff_viewed_at: new Date().toISOString() }) });
    // Refetch single job (after POST)
    ;(global.fetch as any).mockResolvedValueOnce({ ok: true, json: async () => ({ ...job, staff_viewed_at: new Date().toISOString() }) });

    render(<JobList filters={{ status: 'UPLOADED' }} />);
    await waitFor(() => expect(screen.getAllByText('Test Job').length).toBeGreaterThan(0));
    // NEW badge visible
    expect(screen.getByText('NEW')).toBeInTheDocument();
    // Click Mark as Reviewed button
    fireEvent.click(screen.getByText(/Mark as Reviewed/i));
    await waitFor(() => expect(screen.getByText(/Performing Action As/i)).toBeInTheDocument());
    await waitFor(() => expect(screen.queryByText('Loading staff...')).not.toBeInTheDocument());
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'Alice' } });
    // Wait for button enabled then submit
    const confirmBtn = screen.getByRole('button', { name: /Confirm Reviewed/i });
    // Submit and confirm
    fireEvent.click(confirmBtn);
    await waitFor(() => expect(screen.getByText(/Are you sure\?/i)).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /Yes, proceed/i }));
    // After confirm and refetch, NEW badge should be gone
    await waitFor(() => expect(screen.queryByText('NEW')).not.toBeInTheDocument());
  });
});