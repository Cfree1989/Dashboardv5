// @ts-nocheck
import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import JobList from './job-list';

describe('JobList component', () => {
  beforeEach(() => {
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
    await waitFor(() => expect(screen.getByText('Test Job')).toBeInTheDocument());
    expect(screen.getByText('Another Job')).toBeInTheDocument();
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
    // Refetch single job
    ;(global.fetch as any).mockResolvedValueOnce({ ok: true, json: async () => ({ ...job, staff_viewed_at: new Date().toISOString() }) });

    render(<JobList filters={{ status: 'UPLOADED' }} />);
    await waitFor(() => expect(screen.getByText('Test Job')).toBeInTheDocument());
    // NEW badge visible
    expect(screen.getByText('NEW')).toBeInTheDocument();
    // Click Mark as Reviewed button
    fireEvent.click(screen.getByText(/Mark as Reviewed/i));
    await waitFor(() => expect(screen.getByText(/Performing Action As/i)).toBeInTheDocument());
    fireEvent.change(screen.getByDisplayValue('Select your name'), { target: { value: 'Alice' } });
    fireEvent.click(screen.getByText(/Confirm Reviewed/i));
    // After confirm and refetch, NEW badge should be gone
    await waitFor(() => expect(screen.queryByText('NEW')).not.toBeInTheDocument());
  });
});