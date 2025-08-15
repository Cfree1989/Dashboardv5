"""
Test suite for database transaction service.

Tests cover atomic database and file operations, transaction rollback,
and integration with atomic file operations.
"""

import pytest
import tempfile
import json
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.services.db_transaction_service import (
    DatabaseTransactionService,
    TransactionContext,
    get_db_transaction_service,
    atomic_job_status_change,
    atomic_job_creation,
    atomic_job_deletion
)


# Mock the atomic file service to avoid Redis connection issues
@pytest.fixture(autouse=True)
def mock_atomic_file_service():
    """Mock atomic file service to avoid Redis connection issues."""
    with patch('app.services.db_transaction_service.get_atomic_file_service') as mock:
        mock_service = MagicMock()
        mock_service.atomic_move_authoritative.return_value = True
        mock.return_value = mock_service
        yield mock


# Mock Flask app context
@pytest.fixture(autouse=True)
def mock_flask_context():
    """Mock Flask application context."""
    with patch('app.services.db_transaction_service.db') as mock_db:
        yield mock_db


class TestDatabaseTransactionService:
    """Test cases for DatabaseTransactionService."""
    
    @pytest.fixture
    def transaction_service(self):
        """Create a database transaction service instance."""
        return DatabaseTransactionService()
    
    def test_initialization(self, transaction_service):
        """Test service initialization."""
        assert transaction_service.atomic_file_service is not None
    
    def test_atomic_transaction_context_manager_success(self, transaction_service):
        """Test successful atomic transaction with context manager."""
        with transaction_service.atomic_transaction("test_op") as transaction:
            assert transaction.operation_id == "test_op"
            assert transaction.committed is False
            assert transaction.rolled_back is False
            
            # Add some operations
            transaction.add_db_operation('update', object=MagicMock(), updates={'status': 'COMPLETED'})
            transaction.add_file_operation('move', job=MagicMock(), to_status='COMPLETED')
        
        # Transaction should be committed on exit
        assert transaction.committed is True
        assert transaction.rolled_back is False
    
    def test_atomic_transaction_context_manager_exception(self, transaction_service):
        """Test atomic transaction rollback on exception."""
        with pytest.raises(ValueError):
            with transaction_service.atomic_transaction("test_op") as transaction:
                # Add some operations
                transaction.add_db_operation('update', object=MagicMock(), updates={'status': 'COMPLETED'})
                raise ValueError("Test exception")
        
        # Transaction should be rolled back on exception
        assert transaction.rolled_back is True
        assert transaction.committed is False
    
    def test_with_atomic_transaction_decorator(self, transaction_service):
        """Test atomic transaction decorator."""
        @transaction_service.with_atomic_transaction("test_op")
        def test_function(transaction):
            transaction.add_db_operation('update', object=MagicMock(), updates={'status': 'COMPLETED'})
            return "success"
        
        result = test_function()
        assert result == "success"
    
    def test_with_atomic_transaction_decorator_exception(self, transaction_service):
        """Test atomic transaction decorator with exception."""
        @transaction_service.with_atomic_transaction("test_op")
        def test_function(transaction):
            transaction.add_db_operation('update', object=MagicMock(), updates={'status': 'COMPLETED'})
            raise ValueError("Test exception")
        
        with pytest.raises(ValueError):
            test_function()


class TestTransactionContext:
    """Test cases for TransactionContext."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def transaction_context(self):
        """Create a transaction context instance."""
        mock_file_service = MagicMock()
        return TransactionContext("test_op", mock_file_service)
    
    def test_initialization(self, transaction_context):
        """Test transaction context initialization."""
        assert transaction_context.operation_id == "test_op"
        assert len(transaction_context.pending_file_operations) == 0
        assert len(transaction_context.pending_db_operations) == 0
        assert transaction_context.committed is False
        assert transaction_context.rolled_back is False
    
    def test_add_file_operation(self, transaction_context):
        """Test adding file operations."""
        transaction_context.add_file_operation('move', job=MagicMock(), to_status='COMPLETED')
        
        assert len(transaction_context.pending_file_operations) == 1
        operation = transaction_context.pending_file_operations[0]
        assert operation['type'] == 'move'
        assert operation['params']['to_status'] == 'COMPLETED'
        assert operation['executed'] is False
    
    def test_add_db_operation(self, transaction_context):
        """Test adding database operations."""
        mock_obj = MagicMock()
        transaction_context.add_db_operation('update', object=mock_obj, updates={'status': 'COMPLETED'})
        
        assert len(transaction_context.pending_db_operations) == 1
        operation = transaction_context.pending_db_operations[0]
        assert operation['type'] == 'update'
        assert operation['params']['object'] == mock_obj
        assert operation['params']['updates']['status'] == 'COMPLETED'
        assert operation['executed'] is False
    
    def test_commit_success(self, transaction_context):
        """Test successful commit."""
        # Mock atomic file service
        mock_job = MagicMock()
        mock_job.id = "test_job_123"
        transaction_context.atomic_file_service.atomic_move_authoritative.return_value = True
        
        # Add operations
        transaction_context.add_file_operation('move', job=mock_job, to_status='COMPLETED')
        transaction_context.add_db_operation('update', object=mock_job, updates={'status': 'COMPLETED'})
        
        with patch('app.services.db_transaction_service.db') as mock_db:
            transaction_context.commit()
            
            # Verify operations were executed
            assert transaction_context.committed is True
            assert transaction_context.rolled_back is False
            mock_db.session.commit.assert_called_once()
    
    def test_commit_file_operation_failure(self, transaction_context):
        """Test commit failure due to file operation."""
        # Mock atomic file service to fail
        mock_job = MagicMock()
        transaction_context.atomic_file_service.atomic_move_authoritative.return_value = False
        
        # Add file operation that will fail
        transaction_context.add_file_operation('move', job=mock_job, to_status='COMPLETED')
        
        with patch('app.services.db_transaction_service.db') as mock_db:
            with pytest.raises(RuntimeError, match="File move operation failed"):
                transaction_context.commit()
            
            # Verify rollback was called
            assert transaction_context.rolled_back is True
            assert transaction_context.committed is False
            mock_db.session.rollback.assert_called_once()
    
    def test_commit_db_operation_failure(self, transaction_context):
        """Test commit failure due to database operation."""
        # Mock atomic file service
        mock_job = MagicMock()
        transaction_context.atomic_file_service.atomic_move_authoritative.return_value = True
        
        # Add operations
        transaction_context.add_file_operation('move', job=mock_job, to_status='COMPLETED')
        transaction_context.add_db_operation('update', object=None, updates={})  # This will fail
        
        with patch('app.services.db_transaction_service.db') as mock_db:
            with pytest.raises(Exception, match="Missing object for database update"):
                transaction_context.commit()
            
            # Verify rollback was called
            assert transaction_context.rolled_back is True
            assert transaction_context.committed is False
            mock_db.session.rollback.assert_called_once()
    
    def test_rollback(self, transaction_context):
        """Test transaction rollback."""
        with patch('app.services.db_transaction_service.db') as mock_db:
            transaction_context.rollback()
            
            assert transaction_context.rolled_back is True
            assert transaction_context.committed is False
            mock_db.session.rollback.assert_called_once()
    
    def test_commit_already_committed(self, transaction_context):
        """Test commit when already committed."""
        transaction_context.committed = True
        
        transaction_context.commit()  # Should not raise exception
        assert transaction_context.committed is True
    
    def test_commit_already_rolled_back(self, transaction_context):
        """Test commit when already rolled back."""
        transaction_context.rolled_back = True
        
        transaction_context.commit()  # Should not raise exception
        assert transaction_context.rolled_back is True
    
    def test_rollback_already_rolled_back(self, transaction_context):
        """Test rollback when already rolled back."""
        transaction_context.rolled_back = True
        
        transaction_context.rollback()  # Should not raise exception
        assert transaction_context.rolled_back is True
    
    def test_execute_file_delete(self, transaction_context, temp_dir):
        """Test file delete operation execution."""
        # Create a test file
        test_file = temp_dir / "test_file.txt"
        test_file.write_text("test content")
        assert test_file.exists()
        
        # Execute delete operation
        transaction_context._execute_file_delete({'file_path': str(test_file)})
        
        # Verify file was deleted
        assert not test_file.exists()
    
    def test_execute_file_delete_nonexistent(self, transaction_context, temp_dir):
        """Test file delete operation with non-existent file."""
        nonexistent_file = temp_dir / "nonexistent.txt"
        
        # Should not raise exception
        transaction_context._execute_file_delete({'file_path': str(nonexistent_file)})
    
    def test_execute_db_update(self, transaction_context):
        """Test database update operation execution."""
        mock_obj = MagicMock()
        updates = {'status': 'COMPLETED', 'last_updated_by': 'test_user'}
        
        with patch('app.services.db_transaction_service.db') as mock_db:
            transaction_context._execute_db_update({
                'object': mock_obj,
                'updates': updates
            })
            
            # Verify object was updated
            assert mock_obj.status == 'COMPLETED'
            assert mock_obj.last_updated_by == 'test_user'
            mock_db.session.add.assert_called_once_with(mock_obj)
    
    def test_execute_db_insert(self, transaction_context):
        """Test database insert operation execution."""
        mock_obj = MagicMock()
        
        with patch('app.services.db_transaction_service.db') as mock_db:
            transaction_context._execute_db_insert({'object': mock_obj})
            
            mock_db.session.add.assert_called_once_with(mock_obj)
    
    def test_execute_db_delete(self, transaction_context):
        """Test database delete operation execution."""
        mock_obj = MagicMock()
        
        with patch('app.services.db_transaction_service.db') as mock_db:
            transaction_context._execute_db_delete({'object': mock_obj})
            
            mock_db.session.delete.assert_called_once_with(mock_obj)


class TestGlobalService:
    """Test cases for global service instance."""
    
    def test_get_db_transaction_service_singleton(self):
        """Test that global service returns singleton instance."""
        service1 = get_db_transaction_service()
        service2 = get_db_transaction_service()
        
        assert service1 is service2
    
    def test_service_has_atomic_file_service(self):
        """Test that global service has atomic file service."""
        service = get_db_transaction_service()
        assert service.atomic_file_service is not None


class TestConvenienceFunctions:
    """Test cases for convenience functions."""
    
    @pytest.fixture
    def mock_job(self):
        """Create a mock job object."""
        job = MagicMock()
        job.id = "test_job_123"
        job.status = "UPLOADED"
        job.file_path = "/test/path/file.txt"
        job.metadata_path = "/test/path/metadata.json"
        return job
    
    @patch('app.services.db_transaction_service.get_db_transaction_service')
    def test_atomic_job_status_change_success(self, mock_get_service, mock_job):
        """Test successful atomic job status change."""
        # Setup mock service
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        
        # Mock successful transaction
        mock_transaction = MagicMock()
        mock_service.atomic_transaction.return_value.__enter__.return_value = mock_transaction
        mock_service.atomic_transaction.return_value.__exit__.return_value = None
        
        # Test function
        result = atomic_job_status_change(mock_job, "COMPLETED", "test_op")
        
        assert result is True
        
        # Verify operations were added
        mock_transaction.add_file_operation.assert_called_once_with(
            'move', job=mock_job, to_status='COMPLETED'
        )
        # Check that add_db_operation was called with correct parameters (ignoring exact datetime)
        mock_transaction.add_db_operation.assert_called_once()
        call_args = mock_transaction.add_db_operation.call_args
        assert call_args[0][0] == 'update'  # operation type
        assert call_args[1]['object'] == mock_job  # object
        assert call_args[1]['updates']['status'] == 'COMPLETED'  # status update
        assert 'last_updated_at' in call_args[1]['updates']  # datetime field exists
    
    @patch('app.services.db_transaction_service.get_db_transaction_service')
    def test_atomic_job_status_change_failure(self, mock_get_service, mock_job):
        """Test atomic job status change failure."""
        # Setup mock service
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        
        # Mock failed transaction
        mock_service.atomic_transaction.return_value.__enter__.side_effect = Exception("Test error")
        
        # Test function
        result = atomic_job_status_change(mock_job, "COMPLETED", "test_op")
        
        assert result is False
    
    @patch('app.services.db_transaction_service.get_db_transaction_service')
    def test_atomic_job_creation_success(self, mock_get_service):
        """Test successful atomic job creation."""
        # Setup mock service
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        
        # Mock successful transaction
        mock_transaction = MagicMock()
        mock_service.atomic_transaction.return_value.__enter__.return_value = mock_transaction
        mock_service.atomic_transaction.return_value.__exit__.return_value = None
        
        # Mock job object
        mock_job = MagicMock()
        with patch('app.models.job.Job', return_value=mock_job):
            # Test function
            job_data = {'student_name': 'Test User', 'status': 'UPLOADED'}
            result = atomic_job_creation(job_data, "test_op")
            
            assert result == mock_job
            
            # Verify operations were added
            mock_transaction.add_db_operation.assert_called_once_with(
                'insert', object=mock_job
            )
    
    @patch('app.services.db_transaction_service.get_db_transaction_service')
    def test_atomic_job_creation_failure(self, mock_get_service):
        """Test atomic job creation failure."""
        # Setup mock service
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        
        # Mock failed transaction
        mock_service.atomic_transaction.return_value.__enter__.side_effect = Exception("Test error")
        
        # Test function
        job_data = {'student_name': 'Test User', 'status': 'UPLOADED'}
        result = atomic_job_creation(job_data, "test_op")
        
        assert result is None
    
    @patch('app.services.db_transaction_service.get_db_transaction_service')
    def test_atomic_job_deletion_success(self, mock_get_service, mock_job):
        """Test successful atomic job deletion."""
        # Setup mock service
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        
        # Mock successful transaction
        mock_transaction = MagicMock()
        mock_service.atomic_transaction.return_value.__enter__.return_value = mock_transaction
        mock_service.atomic_transaction.return_value.__exit__.return_value = None
        
        # Test function
        result = atomic_job_deletion(mock_job, "test_op")
        
        assert result is True
        
        # Verify operations were added
        assert mock_transaction.add_file_operation.call_count == 2  # file + metadata
        mock_transaction.add_db_operation.assert_called_once_with(
            'delete', object=mock_job
        )
    
    @patch('app.services.db_transaction_service.get_db_transaction_service')
    def test_atomic_job_deletion_failure(self, mock_get_service, mock_job):
        """Test atomic job deletion failure."""
        # Setup mock service
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        
        # Mock failed transaction
        mock_service.atomic_transaction.return_value.__enter__.side_effect = Exception("Test error")
        
        # Test function
        result = atomic_job_deletion(mock_job, "test_op")
        
        assert result is False


class TestIntegration:
    """Integration tests for database transaction service."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_full_transaction_integration(self, temp_dir):
        """Test complete transaction integration."""
        # Create test files
        source_file = temp_dir / "source.txt"
        source_metadata = temp_dir / "source_metadata.json"
        
        source_file.write_text("test content")
        with open(source_metadata, 'w') as f:
            json.dump({"status": "UPLOADED"}, f)
        
        # Create mock job
        job = MagicMock()
        job.id = "test_job_123"
        job.file_path = str(source_file)
        job.metadata_path = str(source_metadata)
        job.status = "UPLOADED"
        
        # Test transaction service
        transaction_service = get_db_transaction_service()
        
        with patch('app.services.db_transaction_service.db') as mock_db:
            with transaction_service.atomic_transaction("test_op") as transaction:
                # Add file operation
                transaction.add_file_operation('move', job=job, to_status='COMPLETED')
                
                # Add database operation
                transaction.add_db_operation('update', object=job, updates={
                    'status': 'COMPLETED',
                    'last_updated_by': 'test_user'
                })
            
            # Verify database commit was called
            mock_db.session.commit.assert_called_once()
            
            # Verify file operation was called (using the fixture mock)
            transaction_service.atomic_file_service.atomic_move_authoritative.assert_called_once_with(
                job, 'COMPLETED', 'test_op'
            )
    
    def test_transaction_rollback_integration(self, temp_dir):
        """Test transaction rollback integration."""
        # Setup mock to fail
        from app.services.db_transaction_service import get_db_transaction_service
        transaction_service = get_db_transaction_service()
        transaction_service.atomic_file_service.atomic_move_authoritative.return_value = False  # File operation fails
        
        # Create mock job
        job = MagicMock()
        job.id = "test_job_123"
        job.status = "UPLOADED"
        
        with patch('app.services.db_transaction_service.db') as mock_db:
            with pytest.raises(RuntimeError, match="File move operation failed"):
                with transaction_service.atomic_transaction("test_op") as transaction:
                    # Add file operation that will fail
                    transaction.add_file_operation('move', job=job, to_status='COMPLETED')
                    
                    # Add database operation
                    transaction.add_db_operation('update', object=job, updates={
                        'status': 'COMPLETED'
                    })
            
            # Verify database rollback was called
            mock_db.session.rollback.assert_called_once()
            
            # Verify database commit was NOT called
            mock_db.session.commit.assert_not_called()
