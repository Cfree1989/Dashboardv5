import React from 'react';
import { render, screen } from '@testing-library/react';
import { TrendCharts } from './trend-charts';

// Mock recharts to throw during render to trigger boundary
jest.mock('recharts', () => {
  const actual = jest.requireActual('recharts');
  return {
    ...actual,
    ResponsiveContainer: () => { throw new Error('chart boom'); },
  };
});

describe('TrendCharts ErrorBoundary', () => {
  const trends = { submissions: [], approvals: [] } as any;
  const resources = { printingThroughput: [], averageLeadTime: [] } as any;

  it('renders fallback for submissions chart when chart throws', async () => {
    render(<TrendCharts trends={trends} resources={resources} period={7} />);
    expect(await screen.findByText(/Submissions chart error/i)).toBeInTheDocument();
  });
});
