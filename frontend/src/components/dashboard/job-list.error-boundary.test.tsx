import React from 'react';
import { render, screen } from '@testing-library/react';
import JobList from './job-list';

jest.mock('./job-card', () => ({
  __esModule: true,
  default: () => { throw new Error('job card boom'); },
}));

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn() }),
}));

jest.mock('../../lib/auth', () => ({
  apiRequest: async () => ([{ id: 'j1', created_at: new Date().toISOString() }]),
}));

describe('JobList ErrorBoundary', () => {
  it('renders section fallback when a job card throws', async () => {
    render(<JobList filters={{ status: 'UPLOADED' }} />);
    expect(await screen.findByText(/Job list error/i)).toBeInTheDocument();
  });
});
