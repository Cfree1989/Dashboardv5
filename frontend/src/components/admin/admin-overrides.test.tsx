// @ts-nocheck
import React from 'react';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { renderWithProviders as render } from '../../../jest.setup';
import { AdminOverridesPanel } from './admin-overrides';

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn() })
}));

describe('AdminOverridesPanel', () => {
  beforeEach(() => {
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn(() => 'test-token'),
        setItem: jest.fn(),
        removeItem: jest.fn(),
        clear: jest.fn(),
      },
      writable: true,
    });
    jest.spyOn(global, 'fetch').mockReset();
  });

  it('executes force unlock with confirmation and shows success', async () => {
    (global.fetch as any).mockResolvedValueOnce({ ok: true, text: async () => '' });

    render(<AdminOverridesPanel />);

    // Fill required fields
    fireEvent.change(screen.getByLabelText(/Job ID/i), { target: { value: 'abc' } });
    fireEvent.change(screen.getByLabelText(/Performing Action As/i), { target: { value: 'Admin User' } });
    fireEvent.change(screen.getByLabelText(/^Action$/i), { target: { value: 'unlock' } });
    fireEvent.change(screen.getByLabelText(/Reason/i), { target: { value: 'Browser crashed' } });

    // Submit opens confirm
    fireEvent.click(screen.getByRole('button', { name: /Execute Override/i }));
    await waitFor(() => expect(screen.getByText(/Confirm Admin Override/i)).toBeInTheDocument());

    // Confirm triggers POST
    fireEvent.click(screen.getByRole('button', { name: /Confirm Override/i }));
    await waitFor(() => expect(screen.queryByText(/Confirm Admin Override/i)).not.toBeInTheDocument());

    // Verify endpoint
    const [url, init] = (global.fetch as jest.Mock).mock.calls[0];
    expect(url).toMatch(/\/api\/v1\/jobs\/abc\/admin\/force-unlock$/);
    expect(init.method).toBe('POST');
    const body = JSON.parse(init.body as string);
    expect(body.staff_name).toBe('Admin User');
    expect(body.reason).toBe('Browser crashed');
  });

  it('executes change-status requires new status and posts correct payload', async () => {
    (global.fetch as any).mockResolvedValueOnce({ ok: true, text: async () => '' });
    render(<AdminOverridesPanel />);

    fireEvent.change(screen.getByLabelText(/Job ID/i), { target: { value: 'j1' } });
    fireEvent.change(screen.getByLabelText(/Performing Action As/i), { target: { value: 'Admin User' } });
    fireEvent.change(screen.getByLabelText(/^Action$/i), { target: { value: 'change_status' } });
    // Requires New Status
    fireEvent.change(screen.getByLabelText(/New Status/i), { target: { value: 'READYTOPRINT' } });
    fireEvent.change(screen.getByLabelText(/Reason/i), { target: { value: 'Manual correction' } });

    fireEvent.click(screen.getByRole('button', { name: /Execute Override/i }));
    await waitFor(() => expect(screen.getByText(/Confirm Admin Override/i)).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /Confirm Override/i }));

    await waitFor(() => expect((global.fetch as jest.Mock).mock.calls.length).toBeGreaterThan(0));
    const [url, init] = (global.fetch as jest.Mock).mock.calls[0];
    expect(url).toMatch(/\/api\/v1\/jobs\/j1\/admin\/change-status$/);
    const body = JSON.parse(init.body as string);
    expect(body.new_status).toBe('READYTOPRINT');
    expect(body.staff_name).toBe('Admin User');
  });

  it('executes mark-failed requires reason and shows error on failure', async () => {
    (global.fetch as any)
      .mockResolvedValueOnce({ ok: false, text: async () => 'Validation error' });

    render(<AdminOverridesPanel />);

    fireEvent.change(screen.getByLabelText(/Job ID/i), { target: { value: 'p1' } });
    fireEvent.change(screen.getByLabelText(/Performing Action As/i), { target: { value: 'Admin User' } });
    fireEvent.change(screen.getByLabelText(/^Action$/i), { target: { value: 'mark_failed' } });
    fireEvent.change(screen.getByLabelText(/Reason/i), { target: { value: 'No adhesion' } });

    fireEvent.click(screen.getByRole('button', { name: /Execute Override/i }));
    await waitFor(() => expect(screen.getByText(/Confirm Admin Override/i)).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /Confirm Override/i }));

    // Error should show inside confirm modal and modal should remain open
    await waitFor(() => {
      const alerts = screen.getAllByRole('alert');
      expect(alerts.some(a => /Validation error/i.test(a.textContent || ''))).toBe(true);
    });
    expect(screen.getByText(/Confirm Admin Override/i)).toBeInTheDocument();
  });
});


