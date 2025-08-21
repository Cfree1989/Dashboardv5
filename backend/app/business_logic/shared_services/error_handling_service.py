"""
Error handling service for file operations and system-wide error management.

This service provides structured error handling, logging, and recovery mechanisms
to replace silent error handling patterns throughout the application.
"""

import logging
import traceback
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels for classification and alerting."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification and routing."""
    FILE_OPERATION = "file_operation"
    DATABASE_OPERATION = "database_operation"
    METADATA_SYNC = "metadata_sync"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    SYSTEM = "system"
    NETWORK = "network"
    PERMISSION = "permission"


class FileOperationError(Exception):
    """Custom exception for file operation errors with structured context."""
    
    def __init__(self, message: str, operation: str, file_path: Optional[str] = None, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM, 
                 category: ErrorCategory = ErrorCategory.FILE_OPERATION,
                 context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.operation = operation
        self.file_path = file_path
        self.severity = severity
        self.category = category
        self.context = context or {}
        self.timestamp = datetime.now(timezone.utc)
        self.traceback = traceback.format_exc()


class MetadataSyncError(Exception):
    """Custom exception for metadata synchronization errors."""
    
    def __init__(self, message: str, job_id: Optional[str] = None, 
                 metadata_path: Optional[str] = None,
                 context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.job_id = job_id
        self.metadata_path = metadata_path
        self.context = context or {}
        self.timestamp = datetime.now(timezone.utc)
        self.traceback = traceback.format_exc()


class ErrorHandlingService:
    """
    Centralized error handling service for structured error management.
    
    This service provides:
    - Structured error logging with context
    - Error classification and severity assessment
    - Recovery procedure suggestions
    - Error aggregation and reporting
    - Alerting for critical errors
    """
    
    def __init__(self):
        self.error_counts: Dict[str, int] = {}
        self.recent_errors: List[Dict[str, Any]] = []
        self.max_recent_errors = 100
        
    def log_file_operation_error(self, operation: str, error: Exception, 
                                file_path: Optional[str] = None,
                                job_id: Optional[str] = None,
                                context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log a file operation error with structured context.
        
        Args:
            operation: The file operation being performed
            error: The exception that occurred
            file_path: Path to the file being operated on
            job_id: ID of the job being processed
            context: Additional context information
        """
        severity = self._assess_file_error_severity(error, operation)
        error_info = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'operation': operation,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'file_path': file_path,
            'job_id': job_id,
            'context': context or {},
            'traceback': traceback.format_exc(),
            'severity': severity.value,
            'category': ErrorCategory.FILE_OPERATION.value
        }
        
        self._log_error(error_info)
        self._update_error_counts(error_info)
        self._add_to_recent_errors(error_info)
        
        # Log to appropriate level based on severity
        log_message = self._format_error_message(error_info)
        if error_info['severity'] == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif error_info['severity'] == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif error_info['severity'] == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def log_metadata_sync_error(self, error: Exception, job_id: Optional[str] = None,
                               metadata_path: Optional[str] = None,
                               context: Optional[Dict[str, Any]] = None) -> None:
        """
        Log a metadata synchronization error with structured context.
        
        Args:
            error: The exception that occurred
            job_id: ID of the job being processed
            metadata_path: Path to the metadata file
            context: Additional context information
        """
        severity = self._assess_metadata_error_severity(error)
        error_info = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'operation': 'metadata_sync',
            'error_type': type(error).__name__,
            'error_message': str(error),
            'job_id': job_id,
            'metadata_path': metadata_path,
            'context': context or {},
            'traceback': traceback.format_exc(),
            'severity': severity.value,
            'category': ErrorCategory.METADATA_SYNC.value
        }
        
        self._log_error(error_info)
        self._update_error_counts(error_info)
        self._add_to_recent_errors(error_info)
        
        log_message = self._format_error_message(error_info)
        if error_info['severity'] == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif error_info['severity'] == ErrorSeverity.HIGH:
            logger.error(log_message)
        else:
            logger.warning(log_message)
    
    def handle_file_operation_with_error_handling(self, operation: str, file_path: str,
                                                operation_func, *args, **kwargs) -> Tuple[bool, Optional[str]]:
        """
        Execute a file operation with proper error handling.
        
        Args:
            operation: Description of the operation being performed
            file_path: Path to the file being operated on
            operation_func: Function to execute
            *args, **kwargs: Arguments to pass to the operation function
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            result = operation_func(*args, **kwargs)
            return True, None
        except Exception as e:
            self.log_file_operation_error(
                operation=operation,
                error=e,
                file_path=file_path,
                context={'args': args, 'kwargs': kwargs}
            )
            return False, str(e)
    
    def handle_metadata_operation_with_error_handling(self, job_id: str, metadata_path: str,
                                                    operation_func, *args, **kwargs) -> Tuple[bool, Optional[str]]:
        """
        Execute a metadata operation with proper error handling.
        
        Args:
            job_id: ID of the job being processed
            metadata_path: Path to the metadata file
            operation_func: Function to execute
            *args, **kwargs: Arguments to pass to the operation function
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        try:
            result = operation_func(*args, **kwargs)
            return True, None
        except Exception as e:
            self.log_metadata_sync_error(
                error=e,
                job_id=job_id,
                metadata_path=metadata_path,
                context={'args': args, 'kwargs': kwargs}
            )
            return False, str(e)
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get a summary of recent errors for monitoring and alerting.
        
        Returns:
            Dictionary containing error statistics and recent errors
        """
        return {
            'total_errors': sum(self.error_counts.values()),
            'error_counts': self.error_counts.copy(),
            'recent_errors': self.recent_errors[-10:],  # Last 10 errors
            'critical_errors': len([e for e in self.recent_errors if e['severity'] == 'critical']),
            'high_errors': len([e for e in self.recent_errors if e['severity'] == 'high'])
        }
    
    def get_recovery_suggestions(self, error_info: Dict[str, Any]) -> List[str]:
        """
        Get recovery suggestions based on error type and context.
        
        Args:
            error_info: Error information dictionary
            
        Returns:
            List of recovery suggestions
        """
        suggestions = []
        
        if error_info['category'] == ErrorCategory.FILE_OPERATION.value:
            if 'Permission denied' in error_info['error_message']:
                suggestions.extend([
                    "Check file and directory permissions",
                    "Verify user has write access to the directory",
                    "Check if file is locked by another process"
                ])
            elif 'No such file or directory' in error_info['error_message']:
                suggestions.extend([
                    "Verify file exists at the specified path",
                    "Check if file was moved or deleted",
                    "Run file system audit to detect orphaned files"
                ])
            elif 'Disk full' in error_info['error_message']:
                suggestions.extend([
                    "Free up disk space",
                    "Check available storage",
                    "Consider archiving old files"
                ])
        
        elif error_info['category'] == ErrorCategory.METADATA_SYNC.value:
            suggestions.extend([
                "Verify metadata file exists and is readable",
                "Check JSON format validity",
                "Run metadata integrity check",
                "Consider regenerating metadata from job data"
            ])
        
        # Add general suggestions
        suggestions.extend([
            "Check system logs for additional context",
            "Verify file system integrity",
            "Consider running system health check"
        ])
        
        return suggestions
    
    def _assess_file_error_severity(self, error: Exception, operation: str) -> ErrorSeverity:
        """Assess the severity of a file operation error."""
        error_message = str(error).lower()
        
        # Critical errors that could cause data loss
        if any(phrase in error_message for phrase in ['disk full', 'no space left', 'corruption']):
            return ErrorSeverity.CRITICAL
        
        # High severity errors that affect workflow
        if any(phrase in error_message for phrase in ['permission denied', 'access denied', 'locked']):
            return ErrorSeverity.HIGH
        
        # Medium severity errors that are recoverable
        if any(phrase in error_message for phrase in ['no such file', 'not found', 'already exists']):
            return ErrorSeverity.MEDIUM
        
        # Low severity for other errors
        return ErrorSeverity.LOW
    
    def _assess_metadata_error_severity(self, error: Exception) -> ErrorSeverity:
        """Assess the severity of a metadata synchronization error."""
        error_message = str(error).lower()
        
        # Critical if metadata corruption detected
        if any(phrase in error_message for phrase in ['corruption', 'invalid json', 'malformed']):
            return ErrorSeverity.CRITICAL
        
        # High severity for write failures
        if any(phrase in error_message for phrase in ['permission denied', 'disk full']):
            return ErrorSeverity.HIGH
        
        # Medium severity for read failures
        if any(phrase in error_message for phrase in ['no such file', 'not found']):
            return ErrorSeverity.MEDIUM
        
        # Low severity for other errors
        return ErrorSeverity.LOW
    
    def _log_error(self, error_info: Dict[str, Any]) -> None:
        """Log error information to structured log."""
        logger.error(f"Structured error: {json.dumps(error_info, default=str)}")
    
    def _update_error_counts(self, error_info: Dict[str, Any]) -> None:
        """Update error count statistics."""
        error_key = f"{error_info['category']}:{error_info['error_type']}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
    
    def _add_to_recent_errors(self, error_info: Dict[str, Any]) -> None:
        """Add error to recent errors list."""
        self.recent_errors.append(error_info)
        if len(self.recent_errors) > self.max_recent_errors:
            self.recent_errors.pop(0)
    
    def _format_error_message(self, error_info: Dict[str, Any]) -> str:
        """Format error information into a readable log message."""
        return (f"{error_info['operation']} failed for "
                f"{error_info.get('file_path', error_info.get('metadata_path', 'unknown'))}: "
                f"{error_info['error_message']} "
                f"(Job: {error_info.get('job_id', 'unknown')})")


# Global error handling service instance
_error_handling_service = None


def get_error_handling_service() -> ErrorHandlingService:
    """Get the global error handling service instance."""
    global _error_handling_service
    if _error_handling_service is None:
        _error_handling_service = ErrorHandlingService()
    return _error_handling_service
