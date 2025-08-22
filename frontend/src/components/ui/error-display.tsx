/**
 * Reusable Error Display Component
 * 
 * Provides consistent error display across the application with:
 * - User-friendly error messages
 * - Retry functionality
 * - Error categorization
 * - Dismissible errors
 * - Expandable error details
 */

import React, { useState } from 'react';
import { AlertTriangle, X, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react';
import { ErrorState, getErrorIcon, getErrorTitle } from '../../lib/error-handling';
import { getErrorStyling } from '../../lib/api-error-handling';

interface ErrorDisplayProps {
  error: ErrorState;
  onRetry?: () => void;
  onDismiss?: () => void;
  showDetails?: boolean;
  className?: string;
  variant?: 'inline' | 'card' | 'banner';
  size?: 'sm' | 'md' | 'lg';
}

export default function ErrorDisplay({
  error,
  onRetry,
  onDismiss,
  showDetails = false,
  className = '',
  variant = 'card',
  size = 'md'
}: ErrorDisplayProps) {
  const [expanded, setExpanded] = useState(showDetails);
  
  if (!error.hasError) {
    return null;
  }

  const errorIcon = getErrorIcon(error.category);
  const errorTitle = getErrorTitle(error.category);
  const styling = getErrorStyling(error.category);
  
  const baseClasses = 'rounded-lg border p-4';
  const sizeClasses = {
    sm: 'text-sm p-2',
    md: 'text-base p-4',
    lg: 'text-lg p-6'
  };
  
  const variantClasses = {
    inline: 'inline-flex items-center gap-2',
    card: 'shadow-sm',
    banner: 'w-full'
  };

  const containerClasses = `${baseClasses} ${sizeClasses[size]} ${variantClasses[variant]} ${styling} ${className}`;

  return (
    <div className={containerClasses} role="alert">
      <div className="flex items-start gap-3">
        {/* Error Icon */}
        <div className="flex-shrink-0 mt-0.5">
          <span className="text-lg" role="img" aria-label={`${errorTitle} icon`}>
            {errorIcon}
          </span>
        </div>

        {/* Error Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1">
              <h3 className="font-medium text-current mb-1">
                {errorTitle}
              </h3>
              <p className="text-current opacity-90">
                {error.message}
              </p>
              
              {/* Error Details */}
              {expanded && (
                <div className="mt-3 text-sm opacity-75">
                  <div className="space-y-1">
                    <div>
                      <span className="font-medium">Category:</span> {error.category}
                    </div>
                    <div>
                      <span className="font-medium">Retryable:</span> {error.isRetryable ? 'Yes' : 'No'}
                    </div>
                    {error.retryCount > 0 && (
                      <div>
                        <span className="font-medium">Retry Count:</span> {error.retryCount}
                      </div>
                    )}
                    <div>
                      <span className="font-medium">Time:</span> {error.timestamp.toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex items-center gap-1 flex-shrink-0">
              {/* Expand/Collapse Button */}
              <button
                onClick={() => setExpanded(!expanded)}
                className="p-1 hover:bg-black/10 rounded transition-colors"
                aria-label={expanded ? 'Hide error details' : 'Show error details'}
              >
                {expanded ? (
                  <ChevronUp className="w-4 h-4" />
                ) : (
                  <ChevronDown className="w-4 h-4" />
                )}
              </button>

              {/* Retry Button */}
              {onRetry && error.isRetryable && (
                <button
                  onClick={onRetry}
                  className="p-1 hover:bg-black/10 rounded transition-colors"
                  aria-label="Retry operation"
                  title="Retry operation"
                >
                  <RefreshCw className="w-4 h-4" />
                </button>
              )}

              {/* Dismiss Button */}
              {onDismiss && (
                <button
                  onClick={onDismiss}
                  className="p-1 hover:bg-black/10 rounded transition-colors"
                  aria-label="Dismiss error"
                  title="Dismiss error"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// Specialized Error Display Components
// ============================================================================

/**
 * Inline error display for forms and small areas
 */
export function InlineError({ error, className = '' }: { error: ErrorState; className?: string }) {
  if (!error.hasError) return null;
  
  return (
    <div className={`text-red-600 text-sm flex items-center gap-1 ${className}`}>
      <AlertTriangle className="w-3 h-3 flex-shrink-0" />
      <span>{error.message}</span>
    </div>
  );
}

/**
 * Banner error display for page-level errors
 */
export function ErrorBanner({ 
  error, 
  onRetry, 
  onDismiss, 
  className = '' 
}: { 
  error: ErrorState; 
  onRetry?: () => void; 
  onDismiss?: () => void; 
  className?: string; 
}) {
  return (
    <ErrorDisplay
      error={error}
      onRetry={onRetry}
      onDismiss={onDismiss}
      variant="banner"
      size="lg"
      className={className}
    />
  );
}

/**
 * Card error display for component-level errors
 */
export function ErrorCard({ 
  error, 
  onRetry, 
  onDismiss, 
  className = '' 
}: { 
  error: ErrorState; 
  onRetry?: () => void; 
  onDismiss?: () => void; 
  className?: string; 
}) {
  return (
    <ErrorDisplay
      error={error}
      onRetry={onRetry}
      onDismiss={onDismiss}
      variant="card"
      size="md"
      className={className}
    />
  );
}

/**
 * Loading error display for async operations
 */
export function LoadingError({ 
  error, 
  onRetry, 
  className = '' 
}: { 
  error: ErrorState; 
  onRetry?: () => void; 
  className?: string; 
}) {
  if (!error.hasError) return null;
  
  return (
    <div className={`text-center py-8 ${className}`}>
      <div className="text-red-600 mb-4">
        <AlertTriangle className="w-12 h-12 mx-auto mb-2" />
        <h3 className="text-lg font-medium mb-2">Failed to Load</h3>
        <p className="text-sm opacity-75">{error.message}</p>
      </div>
      
      {onRetry && error.isRetryable && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Try Again
        </button>
      )}
    </div>
  );
}

/**
 * Empty state error display
 */
export function EmptyStateError({ 
  error, 
  onRetry, 
  className = '' 
}: { 
  error: ErrorState; 
  onRetry?: () => void; 
  className?: string; 
}) {
  if (!error.hasError) return null;
  
  return (
    <div className={`text-center py-12 ${className}`}>
      <div className="text-gray-500 mb-4">
        <AlertTriangle className="w-16 h-16 mx-auto mb-4 opacity-50" />
        <h3 className="text-xl font-medium mb-2">Something went wrong</h3>
        <p className="text-sm opacity-75 max-w-md mx-auto">{error.message}</p>
      </div>
      
      {onRetry && error.isRetryable && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Try Again
        </button>
      )}
    </div>
  );
}
