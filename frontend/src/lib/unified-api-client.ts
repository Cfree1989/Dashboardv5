/**
 * Unified API Client - Single API pattern for all frontend requests
 * Combines optimized caching, standardized error handling, and authentication
 * Replaces: auth.ts apiRequest(), optimized-api.ts, and direct fetch() calls
 */

import { apiCache } from './api-cache';
import { 
  ApiError, 
  isApiError, 
  getUserFriendlyMessage, 
  isRetryableError, 
  getErrorCategory 
} from './api-error-handling';

// Re-export types for components
export type { ApiError } from './api-error-handling';

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
  skipErrorHandling?: boolean; // For auth endpoints that handle errors differently
  retries?: number;
}

interface BatchRequest {
  key: string;
  url: string;
  options?: RequestInit;
  config?: RequestConfig;
}

class UnifiedApiClient {
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
    auth: 0, // No caching for auth requests
  };

  /**
   * Unified API request method with caching, error handling, and authentication
   */
  async request<T>(
    url: string,
    options: RequestInit = {},
    config: RequestConfig = {}
  ): Promise<T> {
    const ttl = config.ttl || this.getDefaultTTL(url);
    const maxRetries = config.retries || 0;
    
    // For cached requests with deduplication
    if (ttl > 0 && options.method !== 'POST' && options.method !== 'PUT' && options.method !== 'DELETE') {
      return this.performCachedRequest<T>(url, options, config, ttl, maxRetries);
    }
    
    // For non-cached requests (mutations)
    return this.performDirectRequest<T>(url, options, config, maxRetries);
  }

  /**
   * Perform cached request with deduplication
   */
  private async performCachedRequest<T>(
    url: string,
    options: RequestInit,
    config: RequestConfig,
    ttl: number,
    maxRetries: number
  ): Promise<T> {
    try {
      const result = await apiCache.cachedRequest<T>(url, this.addAuthHeaders(options), ttl);
      
      // Set up polling if configured
      if (config.polling?.enabled) {
        this.setupPolling(url, options, config.polling);
      }
      
      return result;
    } catch (error) {
      return this.handleRequestError<T>(url, options, config, maxRetries, error);
    }
  }

  /**
   * Perform direct request for mutations
   */
  private async performDirectRequest<T>(
    url: string,
    options: RequestInit,
    config: RequestConfig,
    maxRetries: number
  ): Promise<T> {
    let lastError: any;
    
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        const response = await fetch(url, this.addAuthHeaders(options));
        return await this.processResponse<T>(response, config);
      } catch (error) {
        lastError = error;
        
        // Don't retry on final attempt or non-retryable errors
        if (attempt === maxRetries || !this.isRetryableRequest(error)) {
          break;
        }
        
        // Wait before retry with exponential backoff
        await this.delay(Math.pow(2, attempt) * 1000);
      }
    }
    
    throw lastError;
  }

  /**
   * Add authentication headers and default options
   */
  private addAuthHeaders(options: RequestInit): RequestInit {
    return {
      ...options,
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    };
  }

  /**
   * Process response with standardized error handling
   */
  private async processResponse<T>(response: Response, config: RequestConfig): Promise<T> {
    // Handle authentication errors
    if (response.status === 401 && !config.skipErrorHandling) {
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
      throw new Error('Unauthorized');
    }

    // Parse response
    const data = await response.json();

    // Check if response contains standardized error
    if (isApiError(data)) {
      const error = data.error;
      const userMessage = getUserFriendlyMessage(error);
      
      // Create enhanced error with additional context
      const enhancedError = new Error(userMessage);
      (enhancedError as any).apiError = error;
      (enhancedError as any).isRetryable = isRetryableError(error);
      (enhancedError as any).category = getErrorCategory(error);
      
      throw enhancedError;
    }

    // Handle non-standardized errors
    if (!response.ok) {
      if (config.skipErrorHandling) {
        // Return raw data to caller when caller explicitly wants to ignore errors
        return data as unknown as T;
      }
      throw new Error(`API Error: ${response.status} - ${data.message || 'Unknown error'}`);
    }

    return data;
  }

  /**
   * Handle request errors with retry logic
   */
  private async handleRequestError<T>(
    url: string,
    options: RequestInit,
    config: RequestConfig,
    maxRetries: number,
    error: any
  ): Promise<T> {
    if (maxRetries > 0 && this.isRetryableRequest(error)) {
      // Try direct request as fallback
      return this.performDirectRequest<T>(url, options, config, maxRetries - 1);
    }
    throw error;
  }

  /**
   * Check if an error/request is retryable
   */
  private isRetryableRequest(error: any): boolean {
    if (error.apiError) {
      return isRetryableError(error.apiError);
    }
    // Network errors, timeouts, and 5xx errors are retryable
    return error.name === 'TypeError' || error.message.includes('fetch');
  }

  /**
   * Get default TTL based on URL pattern
   */
  private getDefaultTTL(url: string): number {
    if (url.includes('/auth/')) return UnifiedApiClient.TTL_VALUES.auth;
    if (url.includes('/counts')) return UnifiedApiClient.TTL_VALUES.counts;
    if (url.includes('/jobs')) return UnifiedApiClient.TTL_VALUES.jobs;
    if (url.includes('/analytics')) return UnifiedApiClient.TTL_VALUES.analytics;
    if (url.includes('/catalog')) return UnifiedApiClient.TTL_VALUES.catalog;
    if (url.includes('/staff')) return UnifiedApiClient.TTL_VALUES.staff;
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
    const config = { ...UnifiedApiClient.DEFAULT_POLLING, ...pollingConfig };
    
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
        await apiCache.cachedRequest(url, this.addAuthHeaders(options), this.getDefaultTTL(url));
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
    requests: BatchRequest[]
  ): Promise<T> {
    const batchRequests = requests.map(req => ({
      key: req.key,
      url: req.url,
      options: this.addAuthHeaders(req.options || {}),
      ttl: req.config?.ttl || this.getDefaultTTL(req.url),
    }));

    return apiCache.batchRequests(batchRequests);
  }

  /**
   * Preload common data for better performance
   */
  async preloadCommonData(): Promise<void> {
    const preloadRequests = [
      { url: '/api/v1/jobs/counts', ttl: UnifiedApiClient.TTL_VALUES.counts },
      { url: '/api/v1/catalog', ttl: UnifiedApiClient.TTL_VALUES.catalog },
    ];

    for (const req of preloadRequests) {
      try {
        await apiCache.preload(req.url, this.addAuthHeaders({}), req.ttl);
      } catch (error) {
        // Silently ignore preload errors
      }
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

  /**
   * Delay utility for retry logic
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Convenience methods for common HTTP operations

  /**
   * GET request with default caching
   */
  async get<T>(url: string, config?: RequestConfig): Promise<T> {
    return this.request<T>(url, { method: 'GET' }, config);
  }

  /**
   * POST request (no caching)
   */
  async post<T>(url: string, data?: any, config?: RequestConfig): Promise<T> {
    return this.request<T>(url, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    }, config);
  }

  /**
   * PUT request (no caching)
   */
  async put<T>(url: string, data?: any, config?: RequestConfig): Promise<T> {
    return this.request<T>(url, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    }, config);
  }

  /**
   * DELETE request (no caching)
   */
  async delete<T>(url: string, data?: any, config?: RequestConfig): Promise<T> {
    return this.request<T>(url, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: data ? JSON.stringify(data) : undefined,
    }, config);
  }
}

// Export singleton instance
export const apiClient = new UnifiedApiClient();

// Export types for external use
export type { RequestConfig, PollingConfig, BatchRequest };

// All components now use unified API client - legacy compatibility removed
