import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
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
    expect(screen.getByText(/Loading jobs/i)).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText('Test Job')).toBeInTheDocument());
    expect(screen.getByText('Another Job')).toBeInTheDocument();
  });

  it('shows error message on fetch failure', async () => {
    jest.spyOn(global, 'fetch').mockRejectedValue(new Error('Fetch error'));
    render(<JobList filters={{}} />);
    await waitFor(() => expect(screen.getByText(/Failed to load jobs/i)).toBeInTheDocument());
  });
});