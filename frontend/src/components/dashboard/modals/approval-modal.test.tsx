// @ts-nocheck
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn() })
}));
import ApprovalModal from './approval-modal';

describe('ApprovalModal', () => {
  beforeEach(() => {
    // Minimal localStorage mock
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn(() => 'test-token'),
        setItem: jest.fn(),
        removeItem: jest.fn(),
        clear: jest.fn(),
      },
      writable: true,
    });

    // Default fetch mocks: staff list then approve
    jest.spyOn(global, 'fetch')
      // Staff list
      .mockResolvedValueOnce({ ok: true, json: async () => ({ staff: [{ name: 'Alice', is_active: true }] }) } as any)
      // Candidate files
      .mockResolvedValueOnce({ ok: true, json: async () => ({ files: [] }) } as any)
      // Approve
      .mockResolvedValueOnce({ ok: true, json: async () => ({}) } as any);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('requires staff and valid inputs, then posts approval and calls callbacks', async () => {
    const onClose = jest.fn();
    const onApproved = jest.fn();

    render(
      <ApprovalModal
        jobId="1"
        material="Filament"
        onClose={onClose}
        onApproved={onApproved}
      />
    );

    // Wait for staff to load
    await waitFor(() => expect(screen.getByText('Approve Job')).toBeInTheDocument());
    await waitFor(() => expect(screen.queryByText('Loading staff...')).not.toBeInTheDocument());

    // Select staff
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'Alice' } });

    // Enter weight and time
    fireEvent.change(screen.getByLabelText(/Weight \(grams\)/i), { target: { value: '50' } });
    fireEvent.change(screen.getByLabelText(/Time \(hours\)/i), { target: { value: '2.5' } });

    // Submit
    fireEvent.click(screen.getByRole('button', { name: /Approve/i }));
    // confirm dialog
    await waitFor(() => expect(screen.getByText('Are you sure?')).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: /Yes, approve/i }));

    await waitFor(() => expect(onApproved).toHaveBeenCalled());
    expect(onClose).toHaveBeenCalled();

    // Ensure approval POST was called (third call after staff and candidate-files)
    const calls = (global.fetch as jest.Mock).mock.calls;
    expect(calls.length).toBeGreaterThanOrEqual(3);
    const [approveUrl, approveInit] = calls[2];
    expect(approveUrl).toMatch(/\/api\/v1\/jobs\/1\/approve$/);
    expect(approveInit.method).toBe('POST');
    const body = JSON.parse(approveInit.body as string);
    expect(body.staff_name).toBe('Alice');
    expect(body.weight_g).toBe(50);
    expect(body.time_hours).toBe(2.5);
  });
});


