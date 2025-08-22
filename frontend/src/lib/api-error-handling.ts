/**
 * Standardized API error handling utilities for consistent error handling across the frontend.
 * This module provides utilities to handle the new standardized error response format from the backend.
 */

export interface ApiError {
  error: {
    message: string;
    code: string;
    category: string;
    timestamp: string;
    status: number;
    field?: string;
    details?: any;
  };
}

export interface ErrorCategory {
  VALIDATION: 'validation';
  AUTHENTICATION: 'authentication';
  AUTHORIZATION: 'authorization';
  BUSINESS_LOGIC: 'business_logic';
  SYSTEM: 'system';
  FILE_OPERATION: 'file_operation';
  DATABASE: 'database';
  NETWORK: 'network';
}

export interface ErrorCode {
  // Validation errors (400)
  INVALID_INPUT: 'INVALID_INPUT';
  MISSING_REQUIRED_FIELD: 'MISSING_REQUIRED_FIELD';
  INVALID_FORMAT: 'INVALID_FORMAT';
  INVALID_VALUE: 'INVALID_VALUE';
  
  // Authentication errors (401)
  UNAUTHORIZED: 'UNAUTHORIZED';
  INVALID_TOKEN: 'INVALID_TOKEN';
  TOKEN_EXPIRED: 'TOKEN_EXPIRED';
  
  // Authorization errors (403)
  FORBIDDEN: 'FORBIDDEN';
  INSUFFICIENT_PERMISSIONS: 'INSUFFICIENT_PERMISSIONS';
  
  // Not found errors (404)
  RESOURCE_NOT_FOUND: 'RESOURCE_NOT_FOUND';
  JOB_NOT_FOUND: 'JOB_NOT_FOUND';
  FILE_NOT_FOUND: 'FILE_NOT_FOUND';
  
  // Conflict errors (409)
  RESOURCE_CONFLICT: 'RESOURCE_CONFLICT';
  JOB_ALREADY_LOCKED: 'JOB_ALREADY_LOCKED';
  DUPLICATE_SUBMISSION: 'DUPLICATE_SUBMISSION';
  
  // Business logic errors (422)
  INVALID_STATUS_TRANSITION: 'INVALID_STATUS_TRANSITION';
  BUSINESS_RULE_VIOLATION: 'BUSINESS_RULE_VIOLATION';
  
  // System errors (500)
  INTERNAL_SERVER_ERROR: 'INTERNAL_SERVER_ERROR';
  DATABASE_ERROR: 'DATABASE_ERROR';
  FILE_OPERATION_ERROR: 'FILE_OPERATION_ERROR';
  EXTERNAL_SERVICE_ERROR: 'EXTERNAL_SERVICE_ERROR';
}

/**
 * Check if a response contains a standardized API error
 */
export function isApiError(response: any): response is ApiError {
  return response && typeof response === 'object' && 'error' in response;
}

/**
 * Extract error information from an API response
 */
export function extractApiError(response: any): ApiError['error'] | null {
  if (isApiError(response)) {
    return response.error;
  }
  return null;
}

/**
 * Get user-friendly error message based on error code
 */
export function getUserFriendlyMessage(error: ApiError['error']): string {
  const { code, message, field } = error;
  
  // Provide specific user-friendly messages for common error codes
  switch (code) {
    case 'MISSING_REQUIRED_FIELD':
      return field ? `${field} is required` : 'Required field is missing';
    
    case 'INVALID_FORMAT':
      return field ? `${field} has an invalid format` : 'Invalid format provided';
    
    case 'INVALID_VALUE':
      return field ? `${field} has an invalid value` : 'Invalid value provided';
    
    case 'UNAUTHORIZED':
      return 'Please log in to continue';
    
    case 'FORBIDDEN':
      return 'You do not have permission to perform this action';
    
    case 'RESOURCE_NOT_FOUND':
    case 'JOB_NOT_FOUND':
      return 'The requested resource was not found';
    
    case 'RESOURCE_CONFLICT':
    case 'JOB_ALREADY_LOCKED':
      return 'This resource is currently in use by another user';
    
    case 'DUPLICATE_SUBMISSION':
      return 'This submission appears to be a duplicate';
    
    case 'INVALID_STATUS_TRANSITION':
      return 'This action cannot be performed in the current state';
    
    case 'BUSINESS_RULE_VIOLATION':
      return 'This action violates a business rule';
    
    case 'FILE_OPERATION_ERROR':
      return 'There was an error processing your file';
    
    case 'DATABASE_ERROR':
      return 'There was an error accessing the database';
    
    case 'EXTERNAL_SERVICE_ERROR':
      return 'There was an error with an external service';
    
    case 'INTERNAL_SERVER_ERROR':
      return 'An unexpected error occurred. Please try again later';
    
    default:
      return message || 'An error occurred';
  }
}

/**
 * Get error category for styling/UI decisions
 */
export function getErrorCategory(error: ApiError['error']): string {
  return error.category || 'system';
}

/**
 * Check if error is retryable
 */
export function isRetryableError(error: ApiError['error']): boolean {
  const retryableCodes = [
    'INTERNAL_SERVER_ERROR',
    'DATABASE_ERROR',
    'FILE_OPERATION_ERROR',
    'EXTERNAL_SERVICE_ERROR'
  ];
  
  return retryableCodes.includes(error.code);
}

/**
 * Enhanced fetch wrapper with standardized error handling
 */
export async function apiRequestWithErrorHandling<T>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(url, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  // Handle authentication errors
  if (response.status === 401) {
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
    throw new Error(`API Error: ${response.status} - ${data.message || 'Unknown error'}`);
  }

  return data;
}

/**
 * Handle API errors in components with consistent UI feedback
 */
export function handleApiError(error: any, setError: (message: string) => void): void {
  if (error.apiError) {
    // Standardized API error
    setError(error.message);
  } else if (error.message) {
    // Regular error
    setError(error.message);
  } else {
    // Fallback
    setError('An unexpected error occurred');
  }
}

/**
 * Get error styling classes based on error category
 */
export function getErrorStyling(category: string): string {
  switch (category) {
    case 'validation':
      return 'text-red-600 bg-red-50 border-red-200';
    case 'authentication':
      return 'text-orange-600 bg-orange-50 border-orange-200';
    case 'authorization':
      return 'text-red-600 bg-red-50 border-red-200';
    case 'business_logic':
      return 'text-blue-600 bg-blue-50 border-blue-200';
    case 'system':
    case 'database':
    case 'file_operation':
      return 'text-red-600 bg-red-50 border-red-200';
    default:
      return 'text-gray-600 bg-gray-50 border-gray-200';
  }
}
