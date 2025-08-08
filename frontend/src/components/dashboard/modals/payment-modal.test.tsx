// @ts-nocheck
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import PaymentModal from './payment-modal';
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn() })
}));

describe('PaymentModal', () => {
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
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('validates inputs and posts payment with attribution', async () => {
    // Mock: staff list then payment POST
    jest.spyOn(global, 'fetch')
      .mockResolvedValueOnce({ ok: true, json: async () => ({ staff: [{ name: 'Bob', is_active: true }] }) } as any)
      .mockResolvedValueOnce({ ok: true, json: async () => ({}) } as any);

    const onClose = jest.fn();
    const onSuccess = jest.fn();

    render(<PaymentModal jobId="abc" onClose={onClose} onSuccess={onSuccess} />);

    await waitFor(() => expect(screen.getByText('Record Payment & Pickup')).toBeInTheDocument());
    await waitFor(() => expect(screen.queryByText('Loading staff...')).not.toBeInTheDocument());

    // Initially submit disabled
    const submitBtn = screen.getByRole('button', { name: /Record & Mark Picked Up/i });
    expect(submitBtn).toBeDisabled();

    // Fill fields
    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'Bob' } });
    fireEvent.change(screen.getByLabelText(/Weight \(grams\)/i), { target: { value: '42.5' } });
    fireEvent.change(screen.getByLabelText(/Txn Number/i), { target: { value: 'TC123' } });
    fireEvent.change(screen.getByLabelText(/Picked up by/i), { target: { value: 'Student Name' } });
    expect(submitBtn).not.toBeDisabled();

    // Submit opens confirm
    fireEvent.click(submitBtn);
    await waitFor(() => expect(screen.getByText('Confirm Payment')).toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: 'Confirm' }));

    await waitFor(() => expect(onSuccess).toHaveBeenCalled());
    expect(onClose).toHaveBeenCalled();

    const calls = (global.fetch as jest.Mock).mock.calls;
    expect(calls.length).toBeGreaterThanOrEqual(2);
    const [url, init] = calls[1];
    expect(url).toMatch(/\/api\/v1\/jobs\/abc\/payment$/);
    expect(init.method).toBe('POST');
    const body = JSON.parse(init.body as string);
    expect(body.staff_name).toBe('Bob');
    expect(body.grams).toBe(42.5);
    expect(body.txn_no).toBe('TC123');
    expect(body.picked_up_by).toBe('Student Name');
  });
});


