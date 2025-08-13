// @ts-nocheck
import React from 'react';
import { screen, waitFor, fireEvent } from '@testing-library/react';
import { renderWithProviders as render } from '../../../jest.setup';
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

  // TODO: Add Open File modal tests (render + POST `/log-file-open`) once test helpers are refactored

  it('adds a new note with staff attribution (append via POST)', async () => {
    // 1) Jobs fetch (UPLOADED)
    (global.fetch as any)
      .mockResolvedValueOnce({ ok: true, json: async () => ({ jobs: [{ id: 'n1', display_name: 'Note Job', notes: 'old' }] }) })
      // 2) Staff list for edit notes
      .mockResolvedValueOnce({ ok: true, json: async () => ({ staff: [{ name: 'Alice', is_active: true }] }) })
      // 3) POST append note
      .mockResolvedValueOnce({ ok: true, json: async () => ({ id: 'n1', notes: 'old\nAlice - new notes' }) });

    render(<JobList filters={{ status: 'UPLOADED' }} />);

    await waitFor(() => expect(screen.getAllByText('Note Job').length).toBeGreaterThan(0));
    // Expand card (toggle now uses an icon-only button with accessible label)
    fireEvent.click(screen.getByRole('button', { name: /Expand details/i }));
    // Begin edit by clicking the notes area
    // If placeholder is present, click it; otherwise click the clickable notes container
    const placeholder = screen.queryByText(/No notes added yet/i);
    if (placeholder) {
      fireEvent.click(placeholder);
    } else {
      fireEvent.click(screen.getByLabelText(/Click to add or edit note/i));
    }
    await waitFor(() => expect(screen.queryByText('Loading staff...')).not.toBeInTheDocument());
    // Enter note
    const textarea = screen.getByLabelText(/Add a new note/i);
    fireEvent.change(textarea, { target: { value: 'new notes' } });
    // Select staff
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'Alice' } });
    // Save and close editor
    fireEvent.click(screen.getByRole('button', { name: 'Save Notes' }));
    await waitFor(() => expect(screen.queryByRole('button', { name: 'Save Notes' })).not.toBeInTheDocument());
    expect(screen.getByText(/Has notes/i)).toBeInTheDocument();
  });

  it('opens payment modal for COMPLETED job and removes card on success', async () => {
    // 1) Initial jobs fetch (COMPLETED)
    (global.fetch as any)
      .mockResolvedValueOnce({ ok: true, json: async () => ({ jobs: [{ id: 'c1', display_name: 'Completed Job' }] }) })
      // 2) Staff list for PaymentModal
      .mockResolvedValueOnce({ ok: true, json: async () => ({ staff: [{ name: 'Bob', is_active: true }] }) })
      // 3) Payment POST
      .mockResolvedValueOnce({ ok: true, json: async () => ({}) });

    const onJobsMutated = jest.fn();
    render(<JobList filters={{ status: 'COMPLETED' }} onJobsMutated={onJobsMutated} />);

    // Wait for action button to appear (ensures job rendered)
    await waitFor(() => expect(screen.getByRole('button', { name: 'Mark Paid/Picked Up' })).toBeInTheDocument());
    // Open payment modal
    const payBtn = screen.getByText('Mark Paid/Picked Up');
    fireEvent.click(payBtn);

    // Wait for modal and staff to load
    await waitFor(() => expect(screen.getByText('Record Payment & Pickup')).toBeInTheDocument());
    await waitFor(() => expect(screen.queryByText('Loading staff...')).not.toBeInTheDocument());

    // Fill fields
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'Bob' } });
    fireEvent.change(screen.getByLabelText(/Weight \(grams\)/i), { target: { value: '10.5' } });
    fireEvent.change(screen.getByLabelText(/Txn Number/i), { target: { value: 'TXN-1' } });
    fireEvent.change(screen.getByLabelText(/Picked up by/i), { target: { value: 'Student' } });

    // Submit and confirm
    fireEvent.click(screen.getByRole('button', { name: /Record & Mark Picked Up/i }));
    await waitFor(() => expect(screen.getByText('Confirm Payment')).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: 'Confirm' }));

    // Job removed and counts refresh requested
    await waitFor(() => expect(screen.queryByText('Completed Job')).not.toBeInTheDocument());
    expect(onJobsMutated).toHaveBeenCalled();
  });

  it('shows error toast/message if payment fails and keeps modal open', async () => {
    // 1) Initial jobs fetch (COMPLETED)
    (global.fetch as any)
      .mockResolvedValueOnce({ ok: true, json: async () => ({ jobs: [{ id: 'c2', display_name: 'Completed Err Job' }] }) })
      // 2) Staff list for PaymentModal
      .mockResolvedValueOnce({ ok: true, json: async () => ({ staff: [{ name: 'Alice', is_active: true }] }) })
      // 3) Payment POST fails
      .mockResolvedValueOnce({ ok: false, text: async () => 'Bad Request' });

    render(<JobList filters={{ status: 'COMPLETED' }} />);

    await waitFor(() => expect(screen.getByRole('button', { name: 'Mark Paid/Picked Up' })).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: 'Mark Paid/Picked Up' }));

    await waitFor(() => expect(screen.getByText('Record Payment & Pickup')).toBeInTheDocument());
    await waitFor(() => expect(screen.queryByText('Loading staff...')).not.toBeInTheDocument());

    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'Alice' } });
    fireEvent.change(screen.getByLabelText(/Weight \(grams\)/i), { target: { value: '5' } });
    fireEvent.change(screen.getByLabelText(/Txn Number/i), { target: { value: 'TXN-ERR' } });
    fireEvent.change(screen.getByLabelText(/Picked up by/i), { target: { value: 'Student' } });

    fireEvent.click(screen.getByRole('button', { name: /Record & Mark Picked Up/i }));
    await waitFor(() => expect(screen.getByText('Confirm Payment')).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: 'Confirm' }));

    // Error message appears, modal remains
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent(/Payment failed/i));
    expect(screen.getByText('Record Payment & Pickup')).toBeInTheDocument();
    // Job list still present (button remains available)
    expect(screen.getByRole('button', { name: 'Record & Mark Picked Up' })).toBeInTheDocument();
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
    // Click Reviewed button (renamed from "Mark as Reviewed")
    fireEvent.click(screen.getByText(/Reviewed/i));
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