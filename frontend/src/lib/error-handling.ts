/**
 * Standardized Error Handling Utilities
 * 
 * This module provides consistent error handling patterns across all frontend components.
 * It consolidates error handling logic and provides reusable utilities for:
 * - API error handling
 * - User-friendly error messages
 * - Error display components
 * - Error recovery patterns
 * - Error boundary utilities
 */

import { reportError } from './error-reporting';
import { 
  ApiError, 
  extractApiError,
  getUserFriendlyMessage,
  getErrorCategory, 
  getErrorStyling,
  isRetryableError,
  handleApiError as handleApiErrorBase
} from './api-error-handling';

// ============================================================================
// Error Types and Interfaces
// ============================================================================

export interface ErrorState {
  hasError: boolean;
  message: string;
  category: string;
  isRetryable: boolean;
  retryCount: number;
  timestamp: Date;
}

export interface ErrorDisplayProps {
  error: ErrorState;
  onRetry?: () => void;
  onDismiss?: () => void;
  showDetails?: boolean;
  className?: string;
}

export interface ErrorBoundaryConfig {
  title: string;
  fallback?: React.ComponentType<{ error: Error; reset: () => void }>;
  onError?: (error: Error, info: React.ErrorInfo) => void;
  retryLimit?: number;
}

// ============================================================================
// Error State Management
// ============================================================================

/**
 * Create initial error state
 */
export function createErrorState(): ErrorState {
  return {
    hasError: false,
    message: '',
    category: 'system',
    isRetryable: false,
    retryCount: 0,
    timestamp: new Date(),
  };
}

/**
 * Update error state with new error
 */
export function updateErrorState(
  currentState: ErrorState,
  error: any,
  incrementRetry: boolean = false
): ErrorState {
  const apiError = extractApiError(error);
  
  return {
    hasError: true,
    message: apiError ? getUserFriendlyMessage(apiError) : (error.message || 'An unexpected error occurred'),
    category: apiError ? getErrorCategory(apiError) : 'system',
    isRetryable: apiError ? isRetryableError(apiError) : false,
    retryCount: incrementRetry ? currentState.retryCount + 1 : currentState.retryCount,
    timestamp: new Date(),
  };
}

/**
 * Clear error state
 */
export function clearErrorState(): ErrorState {
  return createErrorState();
}

// ============================================================================
// Enhanced API Error Handling
// ============================================================================

/**
 * Enhanced API error handler with retry logic and user feedback
 */
export function handleApiError(
  error: any,
  setError: (message: string) => void,
  options: {
    showToast?: boolean;
    toast?: any;
    retryable?: boolean;
  } = {}
): void {
  const { showToast = false, toast, retryable = false } = options;
  
  // Use base API error handling
  handleApiErrorBase(error, setError);
  
  // Report error for debugging
  reportError(error, { context: 'API Error Handler' });
  
  // Show toast notification if requested
  if (showToast && toast) {
    const message = error.message || 'An error occurred';
    toast({
      title: 'Error',
      description: message,
      variant: 'destructive',
    });
  }
}

// API request functionality moved to unified-api-client.ts
// All error handling is now centralized in the unified client

// ============================================================================
// Error Display Components
// ============================================================================

/**
 * Get error icon based on category
 */
export function getErrorIcon(category: string): string {
  switch (category) {
    case 'validation':
      return '⚠️';
    case 'authentication':
      return '🔐';
    case 'authorization':
      return '🚫';
    case 'business_logic':
      return 'ℹ️';
    case 'system':
    case 'database':
    case 'file_operation':
      return '❌';
    default:
      return '⚠️';
  }
}

/**
 * Get error title based on category
 */
export function getErrorTitle(category: string): string {
  switch (category) {
    case 'validation':
      return 'Validation Error';
    case 'authentication':
      return 'Authentication Required';
    case 'authorization':
      return 'Access Denied';
    case 'business_logic':
      return 'Business Rule Violation';
    case 'system':
      return 'System Error';
    case 'database':
      return 'Database Error';
    case 'file_operation':
      return 'File Operation Error';
    default:
      return 'Error';
  }
}

// ============================================================================
// Error Recovery Patterns
// ============================================================================

/**
 * Retry function with exponential backoff
 */
export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000
): Promise<T> {
  let lastError: any;
  
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error;
      
      if (attempt === maxRetries) {
        break;
      }
      
      // Check if error is retryable
      const apiError = extractApiError(error);
      if (apiError && !isRetryableError(apiError)) {
        break;
      }
      
      // Wait with exponential backoff
      const delay = baseDelay * Math.pow(2, attempt);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
  
  throw lastError;
}

/**
 * Debounced retry function
 */
export function createDebouncedRetry(
  fn: () => Promise<any>,
  delay: number = 1000
): () => void {
  let timeoutId: NodeJS.Timeout;
  
  return () => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(fn, delay);
  };
}

// ============================================================================
// Error Boundary Utilities
// ============================================================================

/**
 * Create error boundary configuration
 */
export function createErrorBoundaryConfig(
  title: string,
  options: Partial<ErrorBoundaryConfig> = {}
): ErrorBoundaryConfig {
  return {
    title,
    retryLimit: 3,
    ...options,
  };
}

/**
 * Error boundary error handler
 */
export function handleErrorBoundaryError(
  error: Error,
  info: React.ErrorInfo,
  config: ErrorBoundaryConfig
): void {
  // Report error
  reportError(error, { 
    componentStack: info.componentStack,
    context: `ErrorBoundary: ${config.title}` 
  });
  
  // Call custom error handler if provided
  if (config.onError) {
    config.onError(error, info);
  }
}

// ============================================================================
// Form Error Handling
// ============================================================================

/**
 * Handle form validation errors
 */
export function handleFormErrors(
  errors: Record<string, string[]>,
  setFieldError: (field: string, message: string) => void,
  setGeneralError: (message: string) => void
): void {
  let hasGeneralError = false;
  
  Object.entries(errors).forEach(([field, messages]) => {
    if (field === 'general' || field === 'non_field_errors') {
      setGeneralError(messages[0] || 'Form validation failed');
      hasGeneralError = true;
    } else {
      setFieldError(field, messages[0] || 'Invalid value');
    }
  });
  
  if (!hasGeneralError && Object.keys(errors).length > 0) {
    setGeneralError('Please correct the errors above');
  }
}

/**
 * Clear form errors
 */
export function clearFormErrors(
  setFieldError: (field: string, message: string) => void,
  setGeneralError: (message: string) => void
): void {
  setGeneralError('');
  // Note: Field errors should be cleared individually by the form component
}

// ============================================================================
// Network Error Handling
// ============================================================================

/**
 * Check if error is a network error
 */
export function isNetworkError(error: any): boolean {
  return (
    error.name === 'TypeError' ||
    error.message?.includes('fetch') ||
    error.message?.includes('network') ||
    error.message?.includes('Failed to fetch')
  );
}

/**
 * Handle network errors with user-friendly messages
 */
export function handleNetworkError(error: any, setError: (message: string) => void): void {
  if (isNetworkError(error)) {
    setError('Network connection error. Please check your internet connection and try again.');
  } else {
    setError(error.message || 'An unexpected error occurred');
  }
  
  reportError(error, { context: 'Network Error Handler' });
}

// ============================================================================
// Error Logging and Analytics
// ============================================================================

/**
 * Log error with context for analytics
 */
export function logError(
  error: any,
  context: {
    component?: string;
    action?: string;
    userId?: string;
    additionalData?: any;
  } = {}
): void {
  const errorData = {
    message: error.message,
    stack: error.stack,
    timestamp: new Date().toISOString(),
    ...context,
  };
  
  // Report to error reporting service
  reportError(error, errorData);
  
  // Send to server error reporting endpoint (async, fire and forget)
  (async () => {
    try {
      await fetch('/api/v1/admin/error-reporting', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(errorData),
      });
    } catch (serverError) {
      console.warn('Server error reporting failed:', serverError);
    }
  })();
}

/**
 * Track error metrics
 */
export function trackErrorMetrics(
  error: any,
  metrics: {
    errorType: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    userImpact: 'none' | 'low' | 'medium' | 'high';
  }
): void {
  // Implement error metrics tracking
  const errorMetrics = {
    type: metrics.errorType,
    severity: metrics.severity,
    userImpact: metrics.userImpact,
    timestamp: new Date().toISOString(),
    error_message: error.message || 'Unknown error',
    error_stack: error.stack || '',
  };

  // Send to server error reporting endpoint (fire and forget)
  fetch('/api/v1/admin/error-reporting', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message: errorMetrics.error_message,
      stack: errorMetrics.error_stack,
      timestamp: errorMetrics.timestamp,
      component: 'error-metrics',
      action: 'track',
      additionalData: {
        errorType: errorMetrics.type,
        severity: errorMetrics.severity,
        userImpact: errorMetrics.userImpact
      }
    }),
  }).catch(serverError => {
    console.warn('Failed to send error metrics to server:', serverError);
  });
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Format error for display
 */
export function formatErrorForDisplay(error: any): string {
  if (typeof error === 'string') {
    return error;
  }
  
  if (error && error.message) {
    return error.message;
  }
  
  if (error && error.toString) {
    return error.toString();
  }
  
  return 'An unexpected error occurred';
}

/**
 * Check if error should be shown to user
 */
export function shouldShowErrorToUser(error: any): boolean {
  // Don't show internal errors to users
  if (error.message?.includes('Internal Server Error')) {
    return false;
  }
  
  // Don't show technical errors to users
  if (error.message?.includes('fetch') || error.message?.includes('network')) {
    return false;
  }
  
  return true;
}

/**
 * Get error severity level
 */
export function getErrorSeverity(error: any): 'low' | 'medium' | 'high' | 'critical' {
  const apiError = extractApiError(error);
  
  if (apiError) {
    switch (apiError.category) {
      case 'validation':
        return 'low';
      case 'authentication':
      case 'authorization':
        return 'medium';
      case 'business_logic':
        return 'medium';
      case 'system':
      case 'database':
      case 'file_operation':
        return 'high';
      default:
        return 'medium';
    }
  }
  
  // Default severity for unknown errors
  return 'medium';
}
