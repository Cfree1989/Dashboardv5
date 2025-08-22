// Test file for optimized API functionality
// This tests the caching, deduplication, and polling features

import { apiCache } from './api-cache';
import { optimizedApi } from './optimized-api';

// Mock fetch for testing
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('Optimized API Service', () => {
  beforeEach(() => {
    mockFetch.mockClear();
    // Clear cache before each test
    apiCache.clearCache();
  });

  describe('API Cache Service', () => {
    it('should cache successful requests', async () => {
      const mockResponse = { data: 'test' };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      // First request should hit the network
      const result1 = await apiCache.cachedRequest('/api/test');
      expect(result1).toEqual(mockResponse);
      expect(mockFetch).toHaveBeenCalledTimes(1);

      // Second request should use cache
      const result2 = await apiCache.cachedRequest('/api/test');
      expect(result2).toEqual(mockResponse);
      expect(mockFetch).toHaveBeenCalledTimes(1); // Still only 1 call
    });

    it('should deduplicate concurrent requests', async () => {
      const mockResponse = { data: 'test' };
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      // Make two concurrent requests
      const promise1 = apiCache.cachedRequest('/api/test');
      const promise2 = apiCache.cachedRequest('/api/test');

      const [result1, result2] = await Promise.all([promise1, promise2]);
      
      expect(result1).toEqual(mockResponse);
      expect(result2).toEqual(mockResponse);
      expect(mockFetch).toHaveBeenCalledTimes(1); // Only one network request
    });

    it('should respect TTL settings', async () => {
      const mockResponse = { data: 'test' };
      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      // First request
      await apiCache.cachedRequest('/api/test', {}, 100); // 100ms TTL
      expect(mockFetch).toHaveBeenCalledTimes(1);

      // Second request within TTL
      await apiCache.cachedRequest('/api/test', {}, 100);
      expect(mockFetch).toHaveBeenCalledTimes(1); // Still cached

      // Wait for TTL to expire
      await new Promise(resolve => setTimeout(resolve, 150));

      // Third request after TTL expires
      await apiCache.cachedRequest('/api/test', {}, 100);
      expect(mockFetch).toHaveBeenCalledTimes(2); // New network request
    });
  });

  describe('Optimized API Service', () => {
    it('should use appropriate TTL for different URL patterns', () => {
      const countsTTL = optimizedApi['getDefaultTTL']('/api/v1/jobs/counts');
      const jobsTTL = optimizedApi['getDefaultTTL']('/api/v1/jobs');
      const analyticsTTL = optimizedApi['getDefaultTTL']('/api/v1/analytics/overview');

      expect(countsTTL).toBe(30 * 1000); // 30 seconds
      expect(jobsTTL).toBe(60 * 1000); // 1 minute
      expect(analyticsTTL).toBe(5 * 60 * 1000); // 5 minutes
    });

    it('should batch multiple requests efficiently', async () => {
      const mockResponses = {
        overview: { data: 'overview' },
        trends: { data: 'trends' },
        resources: { data: 'resources' },
        financial: { data: 'financial' },
      };

      mockFetch.mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockResponses.overview),
      });

      const requests = [
        { key: 'overview', url: '/api/v1/analytics/overview' },
        { key: 'trends', url: '/api/v1/analytics/trends' },
        { key: 'resources', url: '/api/v1/analytics/resources' },
        { key: 'financial', url: '/api/v1/analytics/financial' },
      ];

      const results = await optimizedApi.batchRequests(requests);
      
      expect(results).toHaveProperty('overview');
      expect(results).toHaveProperty('trends');
      expect(results).toHaveProperty('resources');
      expect(results).toHaveProperty('financial');
    });

    it('should provide performance statistics', () => {
      const stats = optimizedApi.getStats();
      
      expect(stats).toHaveProperty('cacheStats');
      expect(stats).toHaveProperty('activePolling');
      expect(stats).toHaveProperty('pollingConfigs');
      expect(typeof stats.cacheStats.cacheSize).toBe('number');
      expect(typeof stats.activePolling).toBe('number');
      expect(typeof stats.pollingConfigs).toBe('number');
    });
  });

  describe('Error Handling', () => {
    it('should not cache error responses', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      // First request fails
      await expect(apiCache.cachedRequest('/api/test')).rejects.toThrow('Network error');

      // Second request should retry (not use cache)
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ data: 'success' }),
      });

      const result = await apiCache.cachedRequest('/api/test');
      expect(result).toEqual({ data: 'success' });
      expect(mockFetch).toHaveBeenCalledTimes(2); // Both requests hit network
    });

    it('should handle HTTP error responses', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      });

      await expect(apiCache.cachedRequest('/api/test')).rejects.toThrow('API Error: 500 - Internal Server Error');
    });
  });
});
