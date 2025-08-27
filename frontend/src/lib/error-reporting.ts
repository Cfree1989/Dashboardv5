/**
 * Comprehensive error reporting system for the 3D Print Management System.
 * Provides centralized error tracking, reporting to backend, and error analytics.
 */

interface ErrorReport {
  component: string;
  action?: string;
  error: string;
  stack?: string;
  userAgent?: string;
  url?: string;
  timestamp: string;
  additionalData?: Record<string, any>;
}

interface ErrorMetrics {
  totalErrors: number;
  errorsByComponent: Record<string, number>;
  errorsByType: Record<string, number>;
  lastErrorTime?: string;
}

class ErrorReportingService {
  private errorQueue: ErrorReport[] = [];
  private maxQueueSize = 50;
  private reportEndpoint = '/api/v1/admin/error-reporting';
  private monitoringEndpoint = '/api/v1/monitoring/alerts';
  private metrics: ErrorMetrics = {
    totalErrors: 0,
    errorsByComponent: {},
    errorsByType: {}
  };

  constructor() {
    // Initialize error reporting only on client side
    if (typeof window !== 'undefined') {
      this.setupGlobalErrorHandlers();
      this.setupUnhandledRejectionHandler();
    }
  }

  /**
   * Report an error with comprehensive context
   */
  reportError(
    error: unknown, 
    component: string, 
    action?: string, 
    additionalData?: Record<string, any>
  ): void {
    try {
      const errorReport: ErrorReport = {
        component,
        action,
        error: this.formatError(error),
        stack: error instanceof Error ? error.stack : undefined,
        userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : undefined,
        url: typeof window !== 'undefined' ? window.location.href : undefined,
        timestamp: new Date().toISOString(),
        additionalData
      };

      // Update local metrics
      this.updateMetrics(errorReport);

      // Add to queue for batch reporting
      this.errorQueue.push(errorReport);
      if (this.errorQueue.length > this.maxQueueSize) {
        this.errorQueue.shift(); // Remove oldest error
      }

      // Log to console in development
      if (process.env.NODE_ENV === 'development') {
        console.warn('[ErrorReporting]', errorReport);
      }

      // Send to backend (non-blocking)
      this.sendErrorToBackend(errorReport).catch(() => {
        // Silently fail if backend is unavailable
      });

    } catch (reportingError) {
      // Fallback to console if error reporting fails
      console.error('Error reporting failed:', reportingError);
      console.error('Original error:', error);
    }
  }

  /**
   * Format error for reporting
   */
  private formatError(error: unknown): string {
    if (error instanceof Error) {
      return error.message;
    }
    if (typeof error === 'string') {
      return error;
    }
    if (error && typeof error === 'object' && 'message' in error) {
      return String((error as any).message);
    }
    return String(error);
  }

  /**
   * Update local error metrics
   */
  private updateMetrics(errorReport: ErrorReport): void {
    this.metrics.totalErrors++;
    this.metrics.lastErrorTime = errorReport.timestamp;

    // Update component metrics
    this.metrics.errorsByComponent[errorReport.component] = 
      (this.metrics.errorsByComponent[errorReport.component] || 0) + 1;

    // Update error type metrics
    const errorType = this.categorizeError(errorReport.error);
    this.metrics.errorsByType[errorType] = 
      (this.metrics.errorsByType[errorType] || 0) + 1;
  }

  /**
   * Categorize error type for metrics
   */
  private categorizeError(errorMessage: string): string {
    const message = errorMessage.toLowerCase();
    
    if (message.includes('network') || message.includes('fetch') || message.includes('http')) {
      return 'network';
    }
    if (message.includes('syntax') || message.includes('parse')) {
      return 'syntax';
    }
    if (message.includes('type') || message.includes('undefined') || message.includes('null')) {
      return 'type';
    }
    if (message.includes('permission') || message.includes('access')) {
      return 'permission';
    }
    if (message.includes('timeout') || message.includes('time out')) {
      return 'timeout';
    }
    
    return 'unknown';
  }

  /**
   * Send error to backend monitoring system
   */
  private async sendErrorToBackend(errorReport: ErrorReport): Promise<void> {
    try {
      const response = await fetch(this.reportEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          component: errorReport.component,
          action: errorReport.action,
          error_message: errorReport.error,
          error_stack: errorReport.stack,
          user_agent: errorReport.userAgent,
          url: errorReport.url,
          additional_data: errorReport.additionalData
        })
      });

      if (!response.ok) {
        throw new Error(`Backend error reporting failed: ${response.status}`);
      }
    } catch (error) {
      // Don't throw - this is non-critical
      console.warn('Failed to send error to backend:', error);
    }
  }

  /**
   * Setup global error handlers
   */
  private setupGlobalErrorHandlers(): void {
    if (typeof window === 'undefined') return;
    
    // Handle unhandled errors
    window.addEventListener('error', (event) => {
      this.reportError(
        event.error || event.message,
        'global',
        'unhandled_error',
        {
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno
        }
      );
    });

    // Handle resource loading errors
    window.addEventListener('error', (event) => {
      if (event.target !== window) {
        this.reportError(
          `Resource loading failed: ${event.target}`,
          'global',
          'resource_error',
          {
            target: (event.target as any)?.tagName,
            src: (event.target as any)?.src
          }
        );
      }
    }, true);
  }

  /**
   * Setup unhandled promise rejection handler
   */
  private setupUnhandledRejectionHandler(): void {
    if (typeof window === 'undefined') return;
    
    window.addEventListener('unhandledrejection', (event) => {
      this.reportError(
        event.reason,
        'global',
        'unhandled_rejection',
        {
          promise: event.promise
        }
      );
    });
  }

  /**
   * Get current error metrics
   */
  getMetrics(): ErrorMetrics {
    return { ...this.metrics };
  }

  /**
   * Get error queue for debugging
   */
  getErrorQueue(): ErrorReport[] {
    return [...this.errorQueue];
  }

  /**
   * Clear error queue
   */
  clearErrorQueue(): void {
    this.errorQueue = [];
  }

  /**
   * Check for performance alerts from backend
   */
  async checkPerformanceAlerts(): Promise<any[]> {
    try {
      const response = await fetch(this.monitoringEndpoint);
      if (response.ok) {
        const data = await response.json();
        return data.alerts || [];
      }
    } catch (error) {
      console.warn('Failed to check performance alerts:', error);
    }
    return [];
  }

  /**
   * Send batch error report
   */
  async sendBatchReport(): Promise<void> {
    if (this.errorQueue.length === 0) {
      return;
    }

    try {
      const batch = [...this.errorQueue];
      this.errorQueue = []; // Clear queue

      const response = await fetch(this.reportEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          batch: true,
          errors: batch.map(error => ({
            component: error.component,
            action: error.action,
            error_message: error.error,
            error_stack: error.stack,
            user_agent: error.userAgent,
            url: error.url,
            additional_data: error.additionalData
          }))
        })
      });

      if (!response.ok) {
        throw new Error(`Batch error reporting failed: ${response.status}`);
      }
    } catch (error) {
      console.warn('Failed to send batch error report:', error);
      // Re-add errors to queue for retry
      this.errorQueue.unshift(...this.errorQueue);
    }
  }
}

// Global error reporting service instance
const errorReportingService = new ErrorReportingService();

// Legacy function for backward compatibility
export function reportError(error: unknown, info?: any) {
  errorReportingService.reportError(
    error, 
    'unknown', 
    undefined, 
    info ? { info } : undefined
  );
}

// Export the service for direct use
export { errorReportingService };

// Setup periodic batch reporting
if (typeof window !== 'undefined') {
  // Send batch reports every 5 minutes
  setInterval(() => {
    errorReportingService.sendBatchReport();
  }, 5 * 60 * 1000);

  // Send batch report before page unload
  window.addEventListener('beforeunload', () => {
    errorReportingService.sendBatchReport();
  });
}


