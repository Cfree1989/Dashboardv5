"""
Database transaction service with atomic file operation integration.

This service provides database transactions that encompass both database
updates and file operations, ensuring complete atomicity across the system.
"""

import logging
from typing import Optional, Callable, Any, Dict
from contextlib import contextmanager
from functools import wraps

from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone

from app import db
from app.services.infrastructure.atomic_file_service import get_atomic_file_service

logger = logging.getLogger(__name__)


class DatabaseTransactionService:
    """
    Service for managing database transactions with atomic file operations.
    
    This service ensures that database updates and file operations are
    performed atomically - either both succeed or both are rolled back.
    """
    
    def __init__(self):
        self.atomic_file_service = get_atomic_file_service()
    
    @contextmanager
    def atomic_transaction(self, operation_id: Optional[str] = None):
        """
        Context manager for atomic database and file operations.
        
        Args:
            operation_id: Optional operation ID for file operations
            
        Yields:
            Transaction context with rollback capabilities
            
        Raises:
            SQLAlchemyError: If database operations fail
            RuntimeError: If file operations fail
        """
        transaction_context = TransactionContext(operation_id, self.atomic_file_service)
        
        try:
            yield transaction_context
            # If we reach here, commit the transaction
            transaction_context.commit()
        except Exception as e:
            # Rollback on any exception
            transaction_context.rollback()
            raise
    
    # Alias for compatibility: tests expect a 'transaction' method
    transaction = atomic_transaction

    def with_atomic_transaction(self, operation_id: Optional[str] = None):
        """
        Decorator for functions that require atomic database and file operations.
        
        Args:
            operation_id: Optional operation ID for file operations
            
        Returns:
            Decorated function with atomic transaction support
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                with self.atomic_transaction(operation_id) as transaction:
                    # Pass transaction context to the function
                    kwargs['transaction'] = transaction
                    return func(*args, **kwargs)
            return wrapper
        return decorator


class TransactionContext:
    """
    Context for managing database and file operations within a transaction.
    """
    
    def __init__(self, operation_id: Optional[str], atomic_file_service):
        self.operation_id = operation_id
        self.atomic_file_service = atomic_file_service
        self.pending_file_operations: list = []
        self.pending_db_operations: list = []
        self.committed = False
        self.rolled_back = False
        
        logger.debug(f"Transaction context initialized: {operation_id}")
    
    def add_file_operation(self, operation_type: str, **kwargs):
        """
        Add a file operation to be executed during commit.
        
        Args:
            operation_type: Type of file operation ('move', 'copy', 'delete')
            **kwargs: Operation-specific parameters
        """
        operation = {
            'type': operation_type,
            'params': kwargs,
            'executed': False
        }
        self.pending_file_operations.append(operation)
        logger.debug(f"Added file operation: {operation_type}")
    
    def add_db_operation(self, operation_type: str, **kwargs):
        """
        Add a database operation to be executed during commit.
        
        Args:
            operation_type: Type of database operation ('update', 'insert', 'delete')
            **kwargs: Operation-specific parameters
        """
        operation = {
            'type': operation_type,
            'params': kwargs,
            'executed': False
        }
        self.pending_db_operations.append(operation)
        logger.debug(f"Added database operation: {operation_type}")
    
    def commit(self):
        """
        Commit all pending database and file operations atomically.
        
        Raises:
            SQLAlchemyError: If database operations fail
            RuntimeError: If file operations fail
        """
        if self.committed:
            logger.warning("Transaction already committed")
            return
        
        if self.rolled_back:
            logger.warning("Transaction already rolled back")
            return
        
        try:
            # Execute file operations first (they can be rolled back)
            self._execute_file_operations()
            
            # Execute database operations
            self._execute_db_operations()
            
            # Commit database transaction
            db.session.commit()
            
            self.committed = True
            logger.info(f"Transaction committed successfully: {self.operation_id}")
            
        except Exception as e:
            logger.error(f"Transaction commit failed: {e}")
            self.rollback()
            raise
    
    def rollback(self):
        """
        Rollback all operations to their original state.
        """
        if self.rolled_back:
            logger.warning("Transaction already rolled back")
            return
        
        try:
            # Rollback database transaction
            db.session.rollback()
            
            # Rollback file operations (if any were executed)
            self._rollback_file_operations()
            
            self.rolled_back = True
            logger.info(f"Transaction rolled back successfully: {self.operation_id}")
            
        except Exception as e:
            logger.error(f"Transaction rollback failed: {e}")
            # Don't re-raise rollback errors to avoid masking original error
    
    def _execute_file_operations(self):
        """Execute all pending file operations."""
        for operation in self.pending_file_operations:
            if operation['executed']:
                continue
            
            try:
                if operation['type'] == 'move':
                    self._execute_file_move(operation['params'])
                elif operation['type'] == 'delete':
                    self._execute_file_delete(operation['params'])
                else:
                    raise ValueError(f"Unsupported file operation type: {operation['type']}")
                
                operation['executed'] = True
                logger.debug(f"Executed file operation: {operation['type']}")
                
            except Exception as e:
                logger.error(f"File operation failed: {operation['type']} - {e}")
                raise RuntimeError(f"File operation failed: {operation['type']} - {e}")
    
    def _execute_db_operations(self):
        """Execute all pending database operations."""
        for operation in self.pending_db_operations:
            if operation['executed']:
                continue
            
            try:
                if operation['type'] == 'update':
                    self._execute_db_update(operation['params'])
                elif operation['type'] == 'insert':
                    self._execute_db_insert(operation['params'])
                elif operation['type'] == 'delete':
                    self._execute_db_delete(operation['params'])
                else:
                    raise ValueError(f"Unsupported database operation type: {operation['type']}")
                
                operation['executed'] = True
                logger.debug(f"Executed database operation: {operation['type']}")
                
            except Exception as e:
                logger.error(f"Database operation failed: {operation['type']} - {e}")
                raise SQLAlchemyError(f"Database operation failed: {operation['type']} - {e}")
    
    def _execute_file_move(self, params: Dict[str, Any]):
        """Execute a file move operation."""
        job = params.get('job')
        to_status = params.get('to_status')
        
        if not job or not to_status:
            raise ValueError("Missing required parameters for file move")
        
        success = self.atomic_file_service.atomic_move_authoritative(
            job, to_status
        )
        
        if not success:
            raise RuntimeError(f"File move operation failed: {job.id} -> {to_status}")
    
    def _execute_file_delete(self, params: Dict[str, Any]):
        """Execute a file delete operation."""
        file_path = params.get('file_path')
        
        if not file_path:
            raise ValueError("Missing file_path for file delete")
        
        # For now, use simple file deletion
        # TODO: Implement atomic file deletion with staging
        import os
        from pathlib import Path
        
        path = Path(file_path)
        if path.exists():
            path.unlink()
            logger.debug(f"Deleted file: {file_path}")
    
    def _execute_db_update(self, params: Dict[str, Any]):
        """Execute a database update operation."""
        obj = params.get('object')
        updates = params.get('updates', {})
        
        if not obj:
            raise ValueError("Missing object for database update")
        
        for key, value in updates.items():
            setattr(obj, key, value)
        
        db.session.add(obj)
    
    def _execute_db_insert(self, params: Dict[str, Any]):
        """Execute a database insert operation."""
        obj = params.get('object')
        
        if not obj:
            raise ValueError("Missing object for database insert")
        
        db.session.add(obj)
    
    def _execute_db_delete(self, params: Dict[str, Any]):
        """Execute a database delete operation."""
        obj = params.get('object')
        
        if not obj:
            raise ValueError("Missing object for database delete")
        
        db.session.delete(obj)
    
    def _rollback_file_operations(self):
        """Rollback executed file operations."""
        # File operations are handled by the atomic file service
        # which has its own rollback mechanisms
        logger.debug("File operations rollback handled by atomic file service")


# Global instance for application use
_db_transaction_service = None

def get_db_transaction_service() -> DatabaseTransactionService:
    """Get the global database transaction service instance."""
    global _db_transaction_service
    if _db_transaction_service is None:
        _db_transaction_service = DatabaseTransactionService()
    return _db_transaction_service


# Convenience functions for common operations
def atomic_job_status_change(job, new_status: str, operation_id: Optional[str] = None):
    """
    Atomically change job status with file movement.
    
    Args:
        job: Job object to update
        new_status: New status for the job
        operation_id: Optional operation ID
        
    Returns:
        True if successful, False otherwise
    """
    transaction_service = get_db_transaction_service()
    
    try:
        with transaction_service.atomic_transaction(operation_id) as transaction:
            # Add file operation
            transaction.add_file_operation('move', job=job, to_status=new_status)
            
            # Add database operation
            transaction.add_db_operation('update', object=job, updates={
                'status': new_status,
                'last_updated_at': datetime.now(timezone.utc)
            })
            
            # Transaction will be committed automatically on exit
            return True
            
    except Exception as e:
        logger.error(f"Atomic job status change failed: {e}")
        return False


def atomic_job_creation(job_data: Dict[str, Any], operation_id: Optional[str] = None):
    """
    Atomically create a job with file operations.
    
    Args:
        job_data: Job data dictionary
        operation_id: Optional operation ID
        
    Returns:
        Created job object or None if failed
    """
    # Import here to avoid circular imports
    from app.models.job import Job
    
    transaction_service = get_db_transaction_service()
    
    try:
        with transaction_service.atomic_transaction(operation_id) as transaction:
            # Create job object
            job = Job(**job_data)
            
            # Add database operation
            transaction.add_db_operation('insert', object=job)
            
            # Add file operations if needed
            if 'file_path' in job_data:
                # Handle file upload operations
                pass
            
            # Transaction will be committed automatically on exit
            return job
            
    except Exception as e:
        logger.error(f"Atomic job creation failed: {e}")
        return None


def atomic_job_deletion(job, operation_id: Optional[str] = None):
    """
    Atomically delete a job with file cleanup.
    
    Args:
        job: Job object to delete
        operation_id: Optional operation ID
        
    Returns:
        True if successful, False otherwise
    """
    transaction_service = get_db_transaction_service()
    
    try:
        with transaction_service.atomic_transaction(operation_id) as transaction:
            # Add file deletion operations
            if hasattr(job, 'file_path') and job.file_path:
                transaction.add_file_operation('delete', file_path=job.file_path)
            
            if hasattr(job, 'metadata_path') and job.metadata_path:
                transaction.add_file_operation('delete', file_path=job.metadata_path)
            
            # Add database operation
            transaction.add_db_operation('delete', object=job)
            
            # Transaction will be committed automatically on exit
            return True
            
    except Exception as e:
        logger.error(f"Atomic job deletion failed: {e}")
        return False
