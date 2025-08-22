/**
 * Tests for error handling utilities
 */

import {
  createErrorState,
  updateErrorState,
  clearErrorState,
  getErrorIcon,
  getErrorTitle,
  isNetworkError,
  formatErrorForDisplay,
  shouldShowErrorToUser,
  getErrorSeverity,
  retryWithBackoff,
  createDebouncedRetry
} from './error-handling';

// Mock the dependencies
jest.mock('./error-reporting', () => ({
  reportError: jest.fn(),
}));

jest.mock('./api-error-handling', () => ({
  extractApiError: jest.fn(),
  getUserFriendlyMessage: jest.fn(),
  getErrorCategory: jest.fn(),
  isRetryableError: jest.fn(),
}));

describe('Error Handling Utilities', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Error State Management', () => {
    test('createErrorState returns initial error state', () => {
      const state = createErrorState();
      
      expect(state).toEqual({
        hasError: false,
        message: '',
        category: 'system',
        isRetryable: false,
        retryCount: 0,
        timestamp: expect.any(Date),
      });
    });

    test('updateErrorState updates state with error', () => {
      const currentState = createErrorState();
      const error = new Error('Test error');
      
      const { extractApiError, getUserFriendlyMessage, getErrorCategory, isRetryableError } = require('./api-error-handling');
      extractApiError.mockReturnValue(null);
      
      const newState = updateErrorState(currentState, error);
      
      expect(newState).toEqual({
        hasError: true,
        message: 'Test error',
        category: 'system',
        isRetryable: false,
        retryCount: 0,
        timestamp: expect.any(Date),
      });
    });

    test('updateErrorState with API error', () => {
      const currentState = createErrorState();
      const error = new Error('API error');
      
      const { extractApiError, getUserFriendlyMessage, getErrorCategory, isRetryableError } = require('./api-error-handling');
      extractApiError.mockReturnValue({
        code: 'VALIDATION_ERROR',
        message: 'Invalid input',
        category: 'validation'
      });
      getUserFriendlyMessage.mockReturnValue('Please check your input');
      getErrorCategory.mockReturnValue('validation');
      isRetryableError.mockReturnValue(false);
      
      const newState = updateErrorState(currentState, error);
      
      expect(newState).toEqual({
        hasError: true,
        message: 'Please check your input',
        category: 'validation',
        isRetryable: false,
        retryCount: 0,
        timestamp: expect.any(Date),
      });
    });

    test('updateErrorState increments retry count', () => {
      const currentState = {
        ...createErrorState(),
        retryCount: 2,
      };
      const error = new Error('Test error');
      
      const { extractApiError } = require('./api-error-handling');
      extractApiError.mockReturnValue(null);
      
      const newState = updateErrorState(currentState, error, true);
      
      expect(newState.retryCount).toBe(3);
    });

    test('clearErrorState resets to initial state', () => {
      const currentState = {
        hasError: true,
        message: 'Test error',
        category: 'validation',
        isRetryable: true,
        retryCount: 3,
        timestamp: new Date(),
      };
      
      const clearedState = clearErrorState();
      
      expect(clearedState).toEqual(createErrorState());
    });
  });

  describe('Error Display Utilities', () => {
    test('getErrorIcon returns correct icons', () => {
      expect(getErrorIcon('validation')).toBe('⚠️');
      expect(getErrorIcon('authentication')).toBe('🔐');
      expect(getErrorIcon('authorization')).toBe('🚫');
      expect(getErrorIcon('business_logic')).toBe('ℹ️');
      expect(getErrorIcon('system')).toBe('❌');
      expect(getErrorIcon('database')).toBe('❌');
      expect(getErrorIcon('file_operation')).toBe('❌');
      expect(getErrorIcon('unknown')).toBe('⚠️');
    });

    test('getErrorTitle returns correct titles', () => {
      expect(getErrorTitle('validation')).toBe('Validation Error');
      expect(getErrorTitle('authentication')).toBe('Authentication Required');
      expect(getErrorTitle('authorization')).toBe('Access Denied');
      expect(getErrorTitle('business_logic')).toBe('Business Rule Violation');
      expect(getErrorTitle('system')).toBe('System Error');
      expect(getErrorTitle('database')).toBe('Database Error');
      expect(getErrorTitle('file_operation')).toBe('File Operation Error');
      expect(getErrorTitle('unknown')).toBe('Error');
    });
  });

  describe('Network Error Detection', () => {
    test('isNetworkError detects network errors', () => {
      const networkError = new TypeError('Failed to fetch');
      const apiError = new Error('API Error');
      const validationError = new Error('Validation failed');
      
      expect(isNetworkError(networkError)).toBe(true);
      expect(isNetworkError({ name: 'TypeError', message: 'fetch failed' })).toBe(true);
      expect(isNetworkError({ message: 'network error' })).toBe(true);
      expect(isNetworkError({ message: 'Failed to fetch' })).toBe(true);
      expect(isNetworkError(apiError)).toBe(false);
      expect(isNetworkError(validationError)).toBe(false);
    });
  });

  describe('Error Formatting', () => {
    test('formatErrorForDisplay handles different error types', () => {
      expect(formatErrorForDisplay('String error')).toBe('String error');
      expect(formatErrorForDisplay(new Error('Error object'))).toBe('Error object');
      expect(formatErrorForDisplay({ toString: () => 'Custom error' })).toBe('Custom error');
      expect(formatErrorForDisplay(null)).toBe('An unexpected error occurred');
      expect(formatErrorForDisplay(undefined)).toBe('An unexpected error occurred');
    });
  });

  describe('Error Visibility', () => {
    test('shouldShowErrorToUser filters appropriate errors', () => {
      expect(shouldShowErrorToUser({ message: 'Internal Server Error' })).toBe(false);
      expect(shouldShowErrorToUser({ message: 'fetch failed' })).toBe(false);
      expect(shouldShowErrorToUser({ message: 'network error' })).toBe(false);
      expect(shouldShowErrorToUser({ message: 'Validation failed' })).toBe(true);
      expect(shouldShowErrorToUser({ message: 'User not found' })).toBe(true);
    });
  });

  describe('Error Severity', () => {
    test('getErrorSeverity returns correct severity levels', () => {
      const { extractApiError } = require('./api-error-handling');
      
      extractApiError.mockReturnValue({ category: 'validation' });
      expect(getErrorSeverity(new Error('test'))).toBe('low');
      
      extractApiError.mockReturnValue({ category: 'authentication' });
      expect(getErrorSeverity(new Error('test'))).toBe('medium');
      
      extractApiError.mockReturnValue({ category: 'system' });
      expect(getErrorSeverity(new Error('test'))).toBe('high');
      
      extractApiError.mockReturnValue(null);
      expect(getErrorSeverity(new Error('test'))).toBe('medium');
    });
  });

  describe('Retry Utilities', () => {
    test('retryWithBackoff retries on failure', async () => {
      let attempts = 0;
      const failingFn = jest.fn().mockImplementation(() => {
        attempts++;
        throw new Error(`Attempt ${attempts}`);
      });
      
      await expect(retryWithBackoff(failingFn, 2, 10)).rejects.toThrow('Attempt 3');
      expect(failingFn).toHaveBeenCalledTimes(3);
    });

    test('retryWithBackoff succeeds on retry', async () => {
      let attempts = 0;
      const eventuallySucceedingFn = jest.fn().mockImplementation(() => {
        attempts++;
        if (attempts < 2) {
          throw new Error('Temporary failure');
        }
        return 'success';
      });
      
      const result = await retryWithBackoff(eventuallySucceedingFn, 3, 10);
      expect(result).toBe('success');
      expect(eventuallySucceedingFn).toHaveBeenCalledTimes(2);
    });

    test('createDebouncedRetry creates debounced function', () => {
      jest.useFakeTimers();
      
      const fn = jest.fn();
      const debouncedFn = createDebouncedRetry(fn, 1000);
      
      debouncedFn();
      debouncedFn();
      debouncedFn();
      
      expect(fn).not.toHaveBeenCalled();
      
      jest.advanceTimersByTime(1000);
      
      expect(fn).toHaveBeenCalledTimes(1);
      
      jest.useRealTimers();
    });
  });
});
