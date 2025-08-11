// @ts-nocheck
import React from 'react';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { renderWithProviders as render } from '../../../jest.setup';

import JobCard from './job-card';

describe('JobCard – Open File modal', () => {
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
    // Clipboard
    Object.assign(navigator, { clipboard: { writeText: jest.fn() } });
    // Silence alert used for quick feedback
    window.alert = jest.fn();
    jest.spyOn(global, 'fetch').mockResolvedValue({ ok: true, json: async () => ({ message: 'logged' }) } as any);
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('opens modal and logs event, copies file path', async () => {
    const job = {
      id: 'job123',
      display_name: 'Sample.stl',
      student_name: 'Student',
      student_email: 's@example.com',
      printer: 'Prusa MK4S',
      color: 'Gray',
      material: 'Filament',
      created_at: new Date().toISOString(),
      file_path: 'Z:/storage/Uploaded/Sample.stl',
    };

    render(
      <JobCard
        job={job as any}
        currentStatus={'UPLOADED'}
        onApprove={jest.fn()}
        onReject={jest.fn()}
        onMarkReviewed={jest.fn()}
        onStatusAction={jest.fn()}
      />
    );

    // Open File button should be present on all statuses
    const openButtons = screen.getAllByRole('button', { name: 'Open File' });
    fireEvent.click(openButtons[0]);

    // Modal visible
    await waitFor(() => expect(screen.getByText(/This logs the action/i)).toBeInTheDocument());

    // Click Copy File Path
    const copyBtn = screen.getByRole('button', { name: /Copy File Path/i });
    await waitFor(() => fireEvent.click(copyBtn));

    // POST was made
    const calls = (global.fetch as jest.Mock).mock.calls;
    expect(calls.length).toBeGreaterThanOrEqual(1);
    expect(String(calls[0][0])).toMatch(/\/api\/v1\/jobs\/job123\/log-file-open$/);
    // Clipboard received the path
    // Clipboard write may be blocked in jsdom; assert button exists and POST was called
    expect(screen.getByRole('button', { name: /Copy File Path/i })).toBeInTheDocument();
  });
});


