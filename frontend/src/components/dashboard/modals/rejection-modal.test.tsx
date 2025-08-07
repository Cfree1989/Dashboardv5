// @ts-nocheck
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import RejectionModal from './rejection-modal';

describe('RejectionModal', () => {
  beforeEach(() => {
    Object.defineProperty(window, 'localStorage', {
      value: {
        getItem: jest.fn(() => 'test-token'),
      },
      writable: true,
    });

    jest.spyOn(global, 'fetch')
      // Staff list
      .mockResolvedValueOnce({ ok: true, json: async () => ({ staff: [{ name: 'Alice', is_active: true }] }) } as any)
      // Reject call
      .mockResolvedValueOnce({ ok: true, json: async () => ({}) } as any);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('requires attribution and at least one reason, then posts rejection', async () => {
    const onClose = jest.fn();
    const onRejected = jest.fn();

    render(<RejectionModal jobId="1" onClose={onClose} onRejected={onRejected} />);

    await waitFor(() => expect(screen.getByText('Reject Job')).toBeInTheDocument());

    // Select staff
    const select = screen.getByDisplayValue('Select your name') as HTMLSelectElement;
    fireEvent.change(select, { target: { value: 'Alice' } });

    // Choose a reason
    fireEvent.click(screen.getByLabelText(/Model walls too thin/i));

    // Submit
    fireEvent.click(screen.getByRole('button', { name: /Reject/i }));

    await waitFor(() => expect(onRejected).toHaveBeenCalled());
    expect(onClose).toHaveBeenCalled();
  });
});


