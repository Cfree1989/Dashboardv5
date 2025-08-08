// @ts-nocheck
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import StatusChangeModal from './status-change-modal';
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn() })
}));

describe('StatusChangeModal', () => {
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
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('requires staff attribution, confirms, then posts to correct endpoint', async () => {
    // Mock fetch: staff list, then action POST
    jest.spyOn(global, 'fetch')
      // Staff list
      .mockResolvedValueOnce({ ok: true, json: async () => ({ staff: [{ name: 'Alice', is_active: true }] }) } as any)
      // Action POST
      .mockResolvedValueOnce({ ok: true, json: async () => ({}) } as any);

    const onClose = jest.fn();
    const onSuccess = jest.fn();

    render(
      <StatusChangeModal
        jobId="123"
        action="mark-printing"
        title="Mark as Printing"
        description="This will move the job into Printing."
        confirmVerb="Mark Printing"
        onClose={onClose}
        onSuccess={onSuccess}
      />
    );

    // Wait for staff to load
    await waitFor(() => expect(screen.getByText('Mark as Printing')).toBeInTheDocument());
    await waitFor(() => expect(screen.queryByText('Loading staff...')).not.toBeInTheDocument());
    const submitBtn = screen.getByRole('button', { name: /Mark Printing/i });
    expect(submitBtn).toBeDisabled();

    // Select staff
    const staffSelect = screen.getByRole('combobox');
    fireEvent.change(staffSelect, { target: { value: 'Alice' } });
    // allow a tick for state to update
    await waitFor(() => expect(submitBtn).not.toBeDisabled());

    // Submit -> opens confirm dialog
    fireEvent.click(submitBtn);
    await waitFor(() => expect(screen.getByText('Are you sure?')).toBeInTheDocument());

    // Confirm -> triggers POST
    const confirmBtn = screen.getAllByRole('button', { name: /Mark Printing/i }).pop() as HTMLButtonElement;
    fireEvent.click(confirmBtn);

    await waitFor(() => expect(onSuccess).toHaveBeenCalled());
    expect(onClose).toHaveBeenCalled();

    // Verify POST call
    const calls = (global.fetch as jest.Mock).mock.calls;
    expect(calls.length).toBeGreaterThanOrEqual(2);
    const [url, init] = calls[1];
    expect(url).toMatch(/\/api\/v1\/jobs\/123\/mark-printing$/);
    expect(init.method).toBe('POST');
    const body = JSON.parse(init.body as string);
    expect(body.staff_name).toBe('Alice');
  });
});


