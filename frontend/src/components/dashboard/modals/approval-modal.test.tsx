// @ts-nocheck
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
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

    // Select staff
    const select = screen.getByDisplayValue('Select your name') as HTMLSelectElement;
    fireEvent.change(select, { target: { value: 'Alice' } });

    // Enter weight and time
    fireEvent.change(screen.getByLabelText(/Weight \(grams\)/i), { target: { value: '50' } });
    fireEvent.change(screen.getByLabelText(/Time \(hours\)/i), { target: { value: '2.5' } });

    // Submit
    fireEvent.click(screen.getByRole('button', { name: /Approve/i }));

    await waitFor(() => expect(onApproved).toHaveBeenCalled());
    expect(onClose).toHaveBeenCalled();

    // Ensure second fetch was approval POST
    const calls = (global.fetch as jest.Mock).mock.calls;
    expect(calls.length).toBeGreaterThanOrEqual(2);
    const [approveUrl, approveInit] = calls[1];
    expect(approveUrl).toMatch(/\/api\/v1\/jobs\/1\/approve$/);
    expect(approveInit.method).toBe('POST');
    const body = JSON.parse(approveInit.body as string);
    expect(body.staff_name).toBe('Alice');
    expect(body.weight_g).toBe(50);
    expect(body.time_hours).toBe(2.5);
  });
});


