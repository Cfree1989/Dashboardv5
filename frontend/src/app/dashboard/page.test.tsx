/**
 * Tests for dashboard page sound integration
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { useRouter, useSearchParams } from 'next/navigation';
import DashboardPage from './page';
import * as soundUtils from '../../lib/sound-utils';

// Mock Next.js navigation
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  useSearchParams: jest.fn(),
}));

// Mock sound utilities
jest.mock('../../lib/sound-utils', () => ({
  playNewUploadSound: jest.fn(),
  canPlayAudio: jest.fn(),
}));

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
};
Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
});

// Mock fetch
global.fetch = jest.fn();

describe('DashboardPage Sound Integration', () => {
  const mockRouter = {
    push: jest.fn(),
    replace: jest.fn(),
  };

  const mockSearchParams = {
    get: jest.fn(() => 'UPLOADED'),
  };

  beforeEach(() => {
    jest.clearAllMocks();
    
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
    (useSearchParams as jest.Mock).mockReturnValue(mockSearchParams);
    
    mockLocalStorage.getItem.mockReturnValue('mock-token');
    (soundUtils.canPlayAudio as jest.Mock).mockReturnValue(true);
    
    // Mock successful API responses
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ jobs: [] }),
    });
  });

  it('should play sound when UPLOADED count increases', async () => {
    // First call returns 0 uploads
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ jobs: [] }), // 0 uploads
      })
      // Second call returns 2 uploads (increase detected)
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ jobs: [{ id: '1' }, { id: '2' }] }), // 2 uploads
      });

    render(<DashboardPage />);

    // Wait for initial fetch
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled();
    });

    // Trigger another fetch (simulating auto-refresh or manual refresh)
    await waitFor(() => {
      expect(soundUtils.playNewUploadSound).toHaveBeenCalled();
    });
  });

  it('should not play sound on initial load', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ jobs: [{ id: '1' }] }), // 1 upload
    });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled();
    });

    // Should not play sound on initial load
    expect(soundUtils.playNewUploadSound).not.toHaveBeenCalled();
  });

  it('should not play sound when count decreases', async () => {
    // First call returns 3 uploads
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ jobs: [{ id: '1' }, { id: '2' }, { id: '3' }] }), // 3 uploads
      })
      // Second call returns 1 upload (decrease, not increase)
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ jobs: [{ id: '1' }] }), // 1 upload
      });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled();
    });

    // Should not play sound when count decreases
    expect(soundUtils.playNewUploadSound).not.toHaveBeenCalled();
  });

  it('should not play sound when audio is not supported', async () => {
    (soundUtils.canPlayAudio as jest.Mock).mockReturnValue(false);

    // First call returns 0 uploads
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ jobs: [] }), // 0 uploads
      })
      // Second call returns 2 uploads
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ jobs: [{ id: '1' }, { id: '2' }] }), // 2 uploads
      });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled();
    });

    // Should not play sound when audio is not supported
    expect(soundUtils.playNewUploadSound).not.toHaveBeenCalled();
  });

  it('should handle API errors gracefully', async () => {
    (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

    render(<DashboardPage />);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled();
    });

    // Should not crash and should not play sound
    expect(soundUtils.playNewUploadSound).not.toHaveBeenCalled();
  });

  it('should handle 401 unauthorized responses', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: false,
      status: 401,
    });

    render(<DashboardPage />);

    await waitFor(() => {
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('token');
      expect(mockRouter.push).toHaveBeenCalledWith('/login');
    });
  });
});
