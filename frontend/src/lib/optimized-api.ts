// Optimized API request wrapper with intelligent caching and polling
// This provides request deduplication, adaptive polling, and performance optimization

import { apiCache } from './api-cache';

interface PollingConfig {
  enabled: boolean;
  interval: number;
  maxInterval: number;
  backoffMultiplier: number;
  activityThreshold: number;
}

interface RequestConfig {
  ttl?: number;
  polling?: Partial<PollingConfig>;
  priority?: 'high' | 'normal' | 'low';
}

class OptimizedApiService {
  private activePolling = new Map<string, NodeJS.Timeout>();
  private lastActivity = new Map<string, number>();
  private pollingConfigs = new Map<string, PollingConfig>();

  // Default polling configuration
  private static readonly DEFAULT_POLLING: PollingConfig = {
    enabled: false,
    interval: 45000, // 45 seconds
    maxInterval: 300000, // 5 minutes
    backoffMultiplier: 1.5,
    activityThreshold: 300000, // 5 minutes
  };

  // TTL values for different request types
  private static readonly TTL_VALUES = {
    counts: 30 * 1000, // 30 seconds
    jobs: 60 * 1000, // 1 minute
    analytics: 5 * 60 * 1000, // 5 minutes
    catalog: 15 * 60 * 1000, // 15 minutes
    staff: 2 * 60 * 1000, // 2 minutes
  };

  /**
   * Optimized API request with caching and intelligent polling
   */
  async request<T>(
    url: string,
    options: RequestInit = {},
    config: RequestConfig = {}
  ): Promise<T> {
    const ttl = config.ttl || this.getDefaultTTL(url);
    
    // Use cached request with deduplication
    const result = await apiCache.cachedRequest<T>(url, options, ttl);
    
    // Set up polling if configured
    if (config.polling?.enabled) {
      this.setupPolling(url, options, config.polling);
    }
    
    return result;
  }

  /**
   * Get default TTL based on URL pattern
   */
  private getDefaultTTL(url: string): number {
    if (url.includes('/counts')) return OptimizedApiService.TTL_VALUES.counts;
    if (url.includes('/jobs')) return OptimizedApiService.TTL_VALUES.jobs;
    if (url.includes('/analytics')) return OptimizedApiService.TTL_VALUES.analytics;
    if (url.includes('/catalog')) return OptimizedApiService.TTL_VALUES.catalog;
    if (url.includes('/staff')) return OptimizedApiService.TTL_VALUES.staff;
    return 5 * 60 * 1000; // Default 5 minutes
  }

  /**
   * Set up intelligent polling for a request
   */
  private setupPolling(
    url: string,
    options: RequestInit,
    pollingConfig: Partial<PollingConfig>
  ): void {
    const key = this.generateKey(url, options);
    const config = { ...OptimizedApiService.DEFAULT_POLLING, ...pollingConfig };
    
    // Clear existing polling
    this.stopPolling(key);
    
    // Store configuration
    this.pollingConfigs.set(key, config);
    
    // Start polling
    this.startPolling(key, url, options, config);
  }

  /**
   * Start polling with adaptive intervals
   */
  private startPolling(
    key: string,
    url: string,
    options: RequestInit,
    config: PollingConfig
  ): void {
    const poll = async () => {
      try {
        const lastActivity = this.lastActivity.get(key) || 0;
        const now = Date.now();
        const timeSinceActivity = now - lastActivity;
        
        // Skip polling if no recent activity
        if (timeSinceActivity > config.activityThreshold) {
          this.stopPolling(key);
          return;
        }
        
        // Make request and update activity
        await apiCache.cachedRequest(url, options, this.getDefaultTTL(url));
        this.lastActivity.set(key, now);
        
        // Continue polling with current interval
        const timeout = setTimeout(() => poll(), config.interval);
        this.activePolling.set(key, timeout);
        
      } catch (error) {
        // On error, increase interval with backoff
        const newInterval = Math.min(
          config.interval * config.backoffMultiplier,
          config.maxInterval
        );
        
        const timeout = setTimeout(() => poll(), newInterval);
        this.activePolling.set(key, timeout);
      }
    };
    
    // Start initial poll
    const timeout = setTimeout(() => poll(), config.interval);
    this.activePolling.set(key, timeout);
  }

  /**
   * Stop polling for a specific request
   */
  stopPolling(key: string): void {
    const timeout = this.activePolling.get(key);
    if (timeout) {
      clearTimeout(timeout);
      this.activePolling.delete(key);
    }
    this.pollingConfigs.delete(key);
  }

  /**
   * Update activity for a request (used to keep polling active)
   */
  updateActivity(url: string, options: RequestInit = {}): void {
    const key = this.generateKey(url, options);
    this.lastActivity.set(key, Date.now());
  }

  /**
   * Generate unique key for request
   */
  private generateKey(url: string, options: RequestInit): string {
    const method = options.method || 'GET';
    const body = options.body ? JSON.stringify(options.body) : '';
    return `${method}:${url}:${body}`;
  }

  /**
   * Batch multiple requests efficiently
   */
  async batchRequests<T extends Record<string, any>>(
    requests: Array<{
      key: string;
      url: string;
      options?: RequestInit;
      config?: RequestConfig;
    }>
  ): Promise<T> {
    const batchRequests = requests.map(req => ({
      key: req.key,
      url: req.url,
      options: req.options,
      ttl: req.config?.ttl || this.getDefaultTTL(req.url),
    }));

    return apiCache.batchRequests(batchRequests);
  }

  /**
   * Preload common data for better performance
   */
  async preloadCommonData(): Promise<void> {
    const preloadRequests = [
      { url: '/api/v1/jobs/counts', ttl: OptimizedApiService.TTL_VALUES.counts },
      { url: '/api/v1/catalog', ttl: OptimizedApiService.TTL_VALUES.catalog },
    ];

    for (const req of preloadRequests) {
      await apiCache.preload(req.url, {}, req.ttl);
    }
  }

  /**
   * Clear cache for specific patterns
   */
  clearCache(pattern?: string): void {
    apiCache.clearCache(pattern);
  }

  /**
   * Get performance statistics
   */
  getStats(): {
    cacheStats: ReturnType<typeof apiCache.getStats>;
    activePolling: number;
    pollingConfigs: number;
  } {
    return {
      cacheStats: apiCache.getStats(),
      activePolling: this.activePolling.size,
      pollingConfigs: this.pollingConfigs.size,
    };
  }

  /**
   * Stop all polling
   */
  stopAllPolling(): void {
    for (const timeout of Array.from(this.activePolling.values())) {
      clearTimeout(timeout);
    }
    this.activePolling.clear();
    this.pollingConfigs.clear();
  }
}

// Export singleton instance
export const optimizedApi = new OptimizedApiService();

// Export types for external use
export type { PollingConfig, RequestConfig };
