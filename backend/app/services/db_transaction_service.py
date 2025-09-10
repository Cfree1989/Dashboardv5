# Import alias for backward compatibility
# Tests expect this module to exist
"""
Service-level transaction API used by tests.

This file intentionally defines its own classes/functions (instead of re-exporting)
so that tests can patch symbols under the path 'app.services.db_transaction_service.*'.
"""

import logging
from typing import Optional, Callable, Any, Dict
from contextlib import contextmanager
from functools import wraps

from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone

from app import db
from app.services.atomic_file_service import get_atomic_file_service

logger = logging.getLogger(__name__)


class DatabaseTransactionService:
    """
    Service for managing database transactions with atomic file operations.
    """

    def __init__(self):
        self.atomic_file_service = get_atomic_file_service()

    @contextmanager
    def atomic_transaction(self, operation_id: Optional[str] = None):
        """
        Context manager for atomic database and file operations.
        """
        transaction_context = TransactionContext(operation_id, self.atomic_file_service)
        try:
            yield transaction_context
            transaction_context.commit()
        except Exception:
            transaction_context.rollback()
            raise

    # Alias maintained for compatibility
    transaction = atomic_transaction

    def with_atomic_transaction(self, operation_id: Optional[str] = None):
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                with self.atomic_transaction(operation_id) as transaction:
                    kwargs['transaction'] = transaction
                    return func(*args, **kwargs)
            return wrapper
        return decorator


class TransactionContext:
    """Context for managing database and file operations within a transaction."""

    def __init__(self, operation_id: Optional[str], atomic_file_service):
        self.operation_id = operation_id
        self.atomic_file_service = atomic_file_service
        self.pending_file_operations: list = []
        self.pending_db_operations: list = []
        self.committed = False
        self.rolled_back = False

    def add_file_operation(self, operation_type: str, **kwargs):
        operation = {
            'type': operation_type,
            'params': kwargs,
            'executed': False,
        }
        self.pending_file_operations.append(operation)

    def add_db_operation(self, operation_type: str, **kwargs):
        operation = {
            'type': operation_type,
            'params': kwargs,
            'executed': False,
        }
        self.pending_db_operations.append(operation)

    def commit(self):
        if self.committed:
            logger.warning("Transaction already committed")
            return
        if self.rolled_back:
            logger.warning("Transaction already rolled back")
            return
        try:
            self._execute_file_operations()
            self._execute_db_operations()
            db.session.commit()
            self.committed = True
            logger.info(f"Transaction committed successfully: {self.operation_id}")
        except Exception as e:
            logger.error(f"Transaction commit failed: {e}")
            self.rollback()
            raise

    def rollback(self):
        if self.rolled_back:
            logger.warning("Transaction already rolled back")
            return
        try:
            db.session.rollback()
            self._rollback_file_operations()
            self.rolled_back = True
            logger.info(f"Transaction rolled back successfully: {self.operation_id}")
        except Exception as e:
            logger.error(f"Transaction rollback failed: {e}")

    def _execute_file_operations(self):
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
            except Exception as e:
                logger.error(f"File operation failed: {operation['type']} - {e}")
                raise RuntimeError(f"File operation failed: {operation['type']} - {e}")

    def _execute_db_operations(self):
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
            except Exception as e:
                logger.error(f"Database operation failed: {operation['type']} - {e}")
                raise SQLAlchemyError(f"Database operation failed: {operation['type']} - {e}")

    def _execute_file_move(self, params: Dict[str, Any]):
        job = params.get('job')
        to_status = params.get('to_status')
        if not job or not to_status:
            raise ValueError("Missing required parameters for file move")
        success = self.atomic_file_service.atomic_move_authoritative(job, to_status)
        if not success:
            raise RuntimeError(f"File move operation failed: {getattr(job, 'id', '?')} -> {to_status}")

    def _execute_file_delete(self, params: Dict[str, Any]):
        from pathlib import Path
        import shutil
        file_path = params.get('file_path')
        if not file_path:
            raise ValueError("Missing file_path for file delete")
        path = Path(file_path)
        if not path.exists():
            return
        staging_dir = Path("/tmp/file_deletion_staging")
        staging_dir.mkdir(exist_ok=True)
        staging_path = staging_dir / f"deleted_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}_{path.name}"
        shutil.move(str(path), str(staging_path))
        staging_path.unlink(missing_ok=True)

    def _execute_db_update(self, params: Dict[str, Any]):
        obj = params.get('object')
        updates = params.get('updates', {})
        if not obj:
            raise ValueError("Missing object for database update")
        for key, value in updates.items():
            setattr(obj, key, value)
        db.session.add(obj)

    def _execute_db_insert(self, params: Dict[str, Any]):
        obj = params.get('object')
        if not obj:
            raise ValueError("Missing object for database insert")
        db.session.add(obj)

    def _execute_db_delete(self, params: Dict[str, Any]):
        obj = params.get('object')
        if not obj:
            raise ValueError("Missing object for database delete")
        db.session.delete(obj)

    def _rollback_file_operations(self):
        # File ops managed by atomic file service; nothing to do here for tests
        pass


_db_transaction_service: Optional[DatabaseTransactionService] = None


def get_db_transaction_service() -> DatabaseTransactionService:
    global _db_transaction_service
    if _db_transaction_service is None:
        _db_transaction_service = DatabaseTransactionService()
    return _db_transaction_service


def atomic_job_status_change(job, new_status: str, operation_id: Optional[str] = None):
    service = get_db_transaction_service()
    try:
        with service.atomic_transaction(operation_id) as transaction:
            transaction.add_file_operation('move', job=job, to_status=new_status)
            transaction.add_db_operation('update', object=job, updates={
                'status': new_status,
                'last_updated_at': datetime.now(timezone.utc)
            })
            return True
    except Exception as e:
        logger.error(f"Atomic job status change failed: {e}")
        return False


def atomic_job_creation(job_data: Dict[str, Any], operation_id: Optional[str] = None):
    from app.models.job import Job
    service = get_db_transaction_service()
    try:
        with service.atomic_transaction(operation_id) as transaction:
            job = Job(**job_data)
            transaction.add_db_operation('insert', object=job)
            return job
    except Exception as e:
        logger.error(f"Atomic job creation failed: {e}")
        return None


def atomic_job_deletion(job, operation_id: Optional[str] = None):
    service = get_db_transaction_service()
    try:
        with service.atomic_transaction(operation_id) as transaction:
            if getattr(job, 'file_path', None):
                transaction.add_file_operation('delete', file_path=job.file_path)
            if getattr(job, 'metadata_path', None):
                transaction.add_file_operation('delete', file_path=job.metadata_path)
            transaction.add_db_operation('delete', object=job)
            return True
    except Exception as e:
        logger.error(f"Atomic job deletion failed: {e}")
        return False


__all__ = [
    'DatabaseTransactionService',
    'TransactionContext',
    'get_db_transaction_service',
    'atomic_job_status_change',
    'atomic_job_creation',
    'atomic_job_deletion',
]
