// API Caching Service for intelligent caching and request deduplication
// This service provides request deduplication, intelligent caching, and performance optimization

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

interface PendingRequest<T> {
  promise: Promise<T>;
  timestamp: number;
}

class ApiCacheService {
  private cache = new Map<string, CacheEntry<any>>();
  private pendingRequests = new Map<string, PendingRequest<any>>();
  private requestCounts = new Map<string, number>();
  private lastActivity = new Map<string, number>();

  // Default TTL values (in milliseconds)
  private static readonly DEFAULT_TTL = 5 * 60 * 1000; // 5 minutes
  private static readonly SHORT_TTL = 30 * 1000; // 30 seconds
  private static readonly LONG_TTL = 15 * 60 * 1000; // 15 minutes
  private static readonly PENDING_TIMEOUT = 10 * 1000; // 10 seconds

  /**
   * Get cached data if available and not expired
   */
  private getCached<T>(key: string): T | null {
    const entry = this.cache.get(key);
    if (!entry) return null;

    const now = Date.now();
    if (now - entry.timestamp > entry.ttl) {
      this.cache.delete(key);
      return null;
    }

    return entry.data;
  }

  /**
   * Set cached data with TTL
   */
  private setCached<T>(key: string, data: T, ttl: number = ApiCacheService.DEFAULT_TTL): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl,
    });
  }

  /**
   * Check if there's a pending request for the same key
   */
  private getPendingRequest<T>(key: string): Promise<T> | null {
    const pending = this.pendingRequests.get(key);
    if (!pending) return null;

    const now = Date.now();
    if (now - pending.timestamp > ApiCacheService.PENDING_TIMEOUT) {
      this.pendingRequests.delete(key);
      return null;
    }

    return pending.promise;
  }

  /**
   * Set a pending request to prevent duplicate requests
   */
  private setPendingRequest<T>(key: string, promise: Promise<T>): void {
    this.pendingRequests.set(key, {
      promise,
      timestamp: Date.now(),
    });
  }

  /**
   * Remove pending request after completion
   */
  private removePendingRequest(key: string): void {
    this.pendingRequests.delete(key);
  }

  /**
   * Track request frequency for adaptive caching
   */
  private trackRequest(key: string): void {
    const now = Date.now();
    const count = this.requestCounts.get(key) || 0;
    this.requestCounts.set(key, count + 1);
    this.lastActivity.set(key, now);
  }

  /**
   * Get adaptive TTL based on request frequency and type
   */
  private getAdaptiveTTL(key: string, baseTTL: number): number {
    const count = this.requestCounts.get(key) || 0;
    const lastActivity = this.lastActivity.get(key) || 0;
    const now = Date.now();
    const timeSinceLastActivity = now - lastActivity;

    // High-frequency requests get shorter TTL
    if (count > 10 && timeSinceLastActivity < 5 * 60 * 1000) {
      return Math.min(baseTTL, ApiCacheService.SHORT_TTL);
    }

    // Low-frequency requests get longer TTL
    if (count < 3 && timeSinceLastActivity > 10 * 60 * 1000) {
      return Math.max(baseTTL, ApiCacheService.LONG_TTL);
    }

    return baseTTL;
  }

  /**
   * Generate cache key from URL and options
   */
  private generateKey(url: string, options?: RequestInit): string {
    const method = options?.method || 'GET';
    const body = options?.body ? JSON.stringify(options.body) : '';
    return `${method}:${url}:${body}`;
  }

  /**
   * Cached API request with deduplication and intelligent TTL
   */
  async cachedRequest<T>(
    url: string,
    options: RequestInit = {},
    ttl: number = ApiCacheService.DEFAULT_TTL
  ): Promise<T> {
    const key = this.generateKey(url, options);
    this.trackRequest(key);

    // Check cache first
    const cached = this.getCached<T>(key);
    if (cached) {
      return cached;
    }

    // Check for pending request
    const pending = this.getPendingRequest<T>(key);
    if (pending) {
      return pending;
    }

    // Make new request
    const adaptiveTTL = this.getAdaptiveTTL(key, ttl);
    const promise = this.makeRequest<T>(url, options, key, adaptiveTTL);
    this.setPendingRequest(key, promise);

    try {
      const result = await promise;
      return result;
    } finally {
      this.removePendingRequest(key);
    }
  }

  /**
   * Make the actual API request and cache the result
   */
  private async makeRequest<T>(
    url: string,
    options: RequestInit,
    key: string,
    ttl: number
  ): Promise<T> {
    try {
      const response = await fetch(url, {
        ...options,
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status} - ${response.statusText}`);
      }

      const data = await response.json();
      this.setCached(key, data, ttl);
      return data;
    } catch (error) {
      // Don't cache errors
      throw error;
    }
  }

  /**
   * Batch multiple requests into a single call where possible
   */
  async batchRequests<T extends Record<string, any>>(
    requests: Array<{ key: string; url: string; options?: RequestInit; ttl?: number }>
  ): Promise<T> {
    const results: T = {} as T;
    const promises: Array<Promise<{ key: string; data: any }>> = [];

    for (const request of requests) {
      const promise = this.cachedRequest(request.url, request.options, request.ttl)
        .then(data => ({ key: request.key, data }));
      promises.push(promise);
    }

    const batchResults = await Promise.all(promises);
    for (const result of batchResults) {
      results[result.key as keyof T] = result.data;
    }

    return results;
  }

  /**
   * Clear cache for specific URL pattern
   */
  clearCache(pattern?: string): void {
    if (!pattern) {
      this.cache.clear();
      return;
    }

    for (const key of this.cache.keys()) {
      if (key.includes(pattern)) {
        this.cache.delete(key);
      }
    }
  }

  /**
   * Get cache statistics for monitoring
   */
  getStats(): {
    cacheSize: number;
    pendingRequests: number;
    requestCounts: Record<string, number>;
  } {
    return {
      cacheSize: this.cache.size,
      pendingRequests: this.pendingRequests.size,
      requestCounts: Object.fromEntries(this.requestCounts),
    };
  }

  /**
   * Preload data for common requests
   */
  async preload<T>(url: string, options?: RequestInit, ttl?: number): Promise<void> {
    try {
      await this.cachedRequest<T>(url, options, ttl);
    } catch (error) {
      // Silently fail preload requests
    }
  }
}

// Export singleton instance
export const apiCache = new ApiCacheService();

// Export types for external use
export type { CacheEntry, PendingRequest };
