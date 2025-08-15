"""
Test suite for atomic file operation service.

Tests cover the prepare/commit/rollback pattern, staging operations,
metadata handling, and integration with file locking.
"""

import pytest
import tempfile
import json
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from app.services.atomic_file_service import (
    AtomicFileOperation, 
    AtomicFileMoveOperation, 
    AtomicFileService,
    get_atomic_file_service
)


class TestAtomicFileOperation:
    """Test cases for AtomicFileOperation base class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def atomic_op(self):
        """Create an atomic file operation instance."""
        return AtomicFileOperation("test_op_123", "job_456", "move")
    
    def test_initialization(self, atomic_op):
        """Test atomic operation initialization."""
        assert atomic_op.operation_id == "test_op_123"
        assert atomic_op.job_id == "job_456"
        assert atomic_op.operation_type == "move"
        assert atomic_op.prepared is False
        assert atomic_op.committed is False
        assert atomic_op.rolled_back is False
        assert len(atomic_op.staged_files) == 0
        assert len(atomic_op.staged_metadata) == 0
    
    def test_create_staging_directory(self, atomic_op):
        """Test staging directory creation."""
        staging_dir = atomic_op._create_staging_directory()
        assert staging_dir.exists()
        assert staging_dir.is_dir()
        assert "atomic_test_op_123" in str(staging_dir)
        
        # Should return same directory on subsequent calls
        staging_dir2 = atomic_op._create_staging_directory()
        assert staging_dir == staging_dir2
    
    def test_generate_staging_path(self, atomic_op, temp_dir):
        """Test staging path generation."""
        original_path = temp_dir / "test_file.txt"
        staging_path = atomic_op._generate_staging_path(original_path)
        
        assert staging_path.parent == atomic_op._create_staging_directory()
        assert "test_file_test_op_123.txt" in str(staging_path)
    
    def test_backup_metadata(self, atomic_op, temp_dir):
        """Test metadata backup functionality."""
        # Create test metadata file
        metadata_path = temp_dir / "test_metadata.json"
        test_metadata = {"status": "UPLOADED", "file_path": "/test/path"}
        
        with open(metadata_path, 'w') as f:
            json.dump(test_metadata, f)
        
        # Test backup
        backed_up = atomic_op._backup_metadata(metadata_path)
        assert backed_up == test_metadata
    
    def test_backup_nonexistent_metadata(self, atomic_op, temp_dir):
        """Test backup of non-existent metadata file."""
        metadata_path = temp_dir / "nonexistent.json"
        backed_up = atomic_op._backup_metadata(metadata_path)
        assert backed_up == {}
    
    def test_restore_metadata(self, atomic_op, temp_dir):
        """Test metadata restoration."""
        metadata_path = temp_dir / "restore_test.json"
        test_metadata = {"status": "COMPLETED", "updated_at": "2024-01-01T12:00:00Z"}
        
        # Test restore
        result = atomic_op._restore_metadata(metadata_path, test_metadata)
        assert result is True
        assert metadata_path.exists()
        
        # Verify content
        with open(metadata_path, 'r') as f:
            restored = json.load(f)
        assert restored == test_metadata
    
    def test_prepare_move_operation_success(self, atomic_op, temp_dir):
        """Test successful move operation preparation."""
        # Create test files
        source_file = temp_dir / "source.txt"
        dest_file = temp_dir / "dest.txt"
        source_metadata = temp_dir / "source_metadata.json"
        
        source_file.write_text("test content")
        with open(source_metadata, 'w') as f:
            json.dump({"status": "UPLOADED"}, f)
        
        metadata_updates = {"status": "COMPLETED"}
        
        # Prepare operation
        result = atomic_op.prepare_move_operation(
            source_file, dest_file, source_metadata, dest_file.with_suffix('.json'), metadata_updates
        )
        
        assert result is True
        assert atomic_op.prepared is True
        assert len(atomic_op.staged_files) == 2  # file + metadata
        assert len(atomic_op.staged_metadata) == 1
        assert atomic_op.original_paths['file_path'] == str(source_file)
        assert atomic_op.original_paths['metadata_path'] == str(source_metadata)
    
    def test_prepare_move_operation_file_not_exists(self, atomic_op, temp_dir):
        """Test move operation preparation with non-existent file."""
        source_file = temp_dir / "nonexistent.txt"
        dest_file = temp_dir / "dest.txt"
        
        result = atomic_op.prepare_move_operation(source_file, dest_file)
        
        assert result is True  # Should succeed even if file doesn't exist
        assert atomic_op.prepared is True
        assert len(atomic_op.staged_files) == 0  # No files to stage
    
    def test_prepare_move_operation_metadata_error(self, atomic_op, temp_dir):
        """Test move operation preparation with metadata error."""
        # Create test files
        source_file = temp_dir / "source.txt"
        dest_file = temp_dir / "dest.txt"
        source_metadata = temp_dir / "source_metadata.json"
        
        source_file.write_text("test content")
        # Create invalid JSON
        source_metadata.write_text("{invalid json")
        
        metadata_updates = {"status": "COMPLETED"}
        
        # Prepare operation should fail due to invalid JSON
        result = atomic_op.prepare_move_operation(
            source_file, dest_file, source_metadata, dest_file.with_suffix('.json'), metadata_updates
        )
        
        assert result is False
        assert atomic_op.prepared is False
    
    def test_commit_unprepared_operation(self, atomic_op):
        """Test commit of unprepared operation."""
        result = atomic_op.commit()
        assert result is False
    
    def test_commit_already_committed(self, atomic_op):
        """Test commit of already committed operation."""
        atomic_op.prepared = True
        atomic_op.committed = True
        
        result = atomic_op.commit()
        assert result is True
    
    def test_rollback_uncommitted_operation(self, atomic_op):
        """Test rollback of uncommitted operation."""
        result = atomic_op.rollback()
        assert result is True
        assert atomic_op.rolled_back is True
    
    def test_rollback_already_rolled_back(self, atomic_op):
        """Test rollback of already rolled back operation."""
        atomic_op.rolled_back = True
        
        result = atomic_op.rollback()
        assert result is True
    
    def test_context_manager_success(self, temp_dir):
        """Test context manager with successful operation."""
        source_file = temp_dir / "source.txt"
        dest_file = temp_dir / "dest.txt"
        source_file.write_text("test content")
        
        with AtomicFileMoveOperation("test_op", "job_123", source_file, dest_file) as op:
            op.prepare_move_operation(source_file, dest_file)
            op.commit()
        
        # Operation should be committed
        assert op.committed is True
        assert op.rolled_back is False
    
    def test_context_manager_exception(self, temp_dir):
        """Test context manager with exception."""
        source_file = temp_dir / "source.txt"
        dest_file = temp_dir / "dest.txt"
        source_file.write_text("test content")
        
        with pytest.raises(ValueError):
            with AtomicFileMoveOperation("test_op", "job_123", source_file, dest_file) as op:
                op.prepare_move_operation(source_file, dest_file)
                op.commit()
                raise ValueError("Test exception")
        
        # Operation should be rolled back due to exception
        assert op.rolled_back is True
    
    def test_context_manager_no_commit(self, temp_dir):
        """Test context manager without commit."""
        source_file = temp_dir / "source.txt"
        dest_file = temp_dir / "dest.txt"
        source_file.write_text("test content")
        
        with AtomicFileMoveOperation("test_op", "job_123", source_file, dest_file) as op:
            op.prepare_move_operation(source_file, dest_file)
            # No commit called
        
        # Operation should be rolled back
        assert op.rolled_back is True


class TestAtomicFileMoveOperation:
    """Test cases for AtomicFileMoveOperation."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_initialization(self, temp_dir):
        """Test move operation initialization."""
        source_file = temp_dir / "source.txt"
        dest_file = temp_dir / "dest.txt"
        
        op = AtomicFileMoveOperation("test_op", "job_123", source_file, dest_file)
        
        assert op.operation_type == "move"
        assert op.source_file == source_file
        assert op.dest_file == dest_file
        assert op._destination_mapping[source_file] == dest_file
    
    def test_get_destination_path(self, temp_dir):
        """Test destination path mapping."""
        source_file = temp_dir / "source.txt"
        dest_file = temp_dir / "dest.txt"
        
        op = AtomicFileMoveOperation("test_op", "job_123", source_file, dest_file)
        
        # Test mapped path
        result = op._get_destination_path(source_file)
        assert result == dest_file
        
        # Test unmapped path
        other_file = temp_dir / "other.txt"
        result = op._get_destination_path(other_file)
        assert result is None


class TestAtomicFileService:
    """Test cases for AtomicFileService."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def mock_job(self, temp_dir):
        """Create a mock job object."""
        job = MagicMock()
        job.id = "test_job_123"
        job.file_path = str(temp_dir / "test_file.txt")
        job.metadata_path = str(temp_dir / "test_metadata.json")
        job.status = "UPLOADED"
        return job
    
    @pytest.fixture
    def atomic_service(self):
        """Create atomic file service instance."""
        return AtomicFileService()
    
    def test_initialization(self, atomic_service):
        """Test service initialization."""
        assert atomic_service.lock_service is not None
    
    def test_storage_root_from_path(self, atomic_service, temp_dir):
        """Test storage root inference."""
        # Create a path that looks like it's in a status directory
        status_path = temp_dir / "Uploaded" / "test_file.txt"
        status_path.parent.mkdir(parents=True, exist_ok=True)
        
        root = atomic_service._storage_root_from_path(status_path)
        assert root == temp_dir
    
    def test_storage_root_from_path_fallback(self, atomic_service, temp_dir):
        """Test storage root fallback to environment variable."""
        with patch.dict('os.environ', {'STORAGE_PATH': '/custom/storage'}):
            test_path = temp_dir / "test_file.txt"
            root = atomic_service._storage_root_from_path(test_path)
            assert root == Path("/custom/storage")
    
    @patch('app.services.atomic_file_service.get_file_lock_service')
    def test_atomic_move_authoritative_success(self, mock_lock_service, atomic_service, mock_job, temp_dir):
        """Test successful atomic move operation."""
        # Setup mock lock service
        mock_lock = MagicMock()
        mock_lock.acquire_lock.return_value = True
        mock_lock.release_lock.return_value = True
        mock_lock_service.return_value = mock_lock
        
        # Replace the service's lock service with our mock
        atomic_service.lock_service = mock_lock
        
        # Create test files
        source_file = Path(mock_job.file_path)
        source_metadata = Path(mock_job.metadata_path)
        
        source_file.parent.mkdir(parents=True, exist_ok=True)
        source_file.write_text("test content")
        
        source_metadata.parent.mkdir(parents=True, exist_ok=True)
        with open(source_metadata, 'w') as f:
            json.dump({"status": "UPLOADED"}, f)
        
        # Perform atomic move
        result = atomic_service.atomic_move_authoritative(mock_job, "COMPLETED")
        
        assert result is True
        
        # Verify locks were acquired and released
        assert mock_lock.acquire_lock.call_count == 2  # file + metadata
        assert mock_lock.release_lock.call_count == 2
        
        # Verify job paths were updated
        assert "Completed" in mock_job.file_path
        assert "Completed" in mock_job.metadata_path
    
    @patch('app.services.atomic_file_service.get_file_lock_service')
    def test_atomic_move_authoritative_lock_failure(self, mock_lock_service, atomic_service, mock_job):
        """Test atomic move operation with lock acquisition failure."""
        # Setup mock lock service to fail
        mock_lock = MagicMock()
        mock_lock.acquire_lock.return_value = False
        mock_lock_service.return_value = mock_lock
        
        # Replace the service's lock service with our mock
        atomic_service.lock_service = mock_lock
        
        # Perform atomic move
        result = atomic_service.atomic_move_authoritative(mock_job, "COMPLETED")
        
        assert result is False
        
        # Verify locks were attempted to be released (in finally block)
        assert mock_lock.release_lock.call_count == 2
    
    @patch('app.services.atomic_file_service.get_file_lock_service')
    def test_atomic_move_authoritative_operation_failure(self, mock_lock_service, atomic_service, mock_job, temp_dir):
        """Test atomic move operation with operation failure."""
        # Setup mock lock service
        mock_lock = MagicMock()
        mock_lock.acquire_lock.return_value = True
        mock_lock.release_lock.return_value = True
        mock_lock_service.return_value = mock_lock
        
        # Replace the service's lock service with our mock
        atomic_service.lock_service = mock_lock
        
        # Create test files with invalid metadata to cause operation failure
        source_file = Path(mock_job.file_path)
        source_metadata = Path(mock_job.metadata_path)
        
        source_file.parent.mkdir(parents=True, exist_ok=True)
        source_file.write_text("test content")
        
        source_metadata.parent.mkdir(parents=True, exist_ok=True)
        source_metadata.write_text("{invalid json")  # Invalid JSON
        
        # Perform atomic move
        result = atomic_service.atomic_move_authoritative(mock_job, "COMPLETED")
        
        assert result is False
        
        # Verify locks were released even on failure
        assert mock_lock.release_lock.call_count == 2
    
    def test_atomic_move_authoritative_no_metadata(self, atomic_service, temp_dir):
        """Test atomic move operation without metadata file."""
        # Create mock job without metadata
        job = MagicMock()
        job.id = "test_job_123"
        job.file_path = str(temp_dir / "test_file.txt")
        job.metadata_path = None
        job.status = "UPLOADED"
        
        # Create test file
        source_file = Path(job.file_path)
        source_file.parent.mkdir(parents=True, exist_ok=True)
        source_file.write_text("test content")
        
        with patch('app.services.atomic_file_service.get_file_lock_service') as mock_lock_service:
            mock_lock = MagicMock()
            mock_lock.acquire_lock.return_value = True
            mock_lock.release_lock.return_value = True
            mock_lock_service.return_value = mock_lock
            
            # Replace the service's lock service with our mock
            atomic_service.lock_service = mock_lock
            
            # Perform atomic move
            result = atomic_service.atomic_move_authoritative(job, "COMPLETED")
            
            assert result is True
            
            # Verify only file lock was acquired (no metadata)
            assert mock_lock.acquire_lock.call_count == 1
            assert mock_lock.release_lock.call_count == 1
    
    def test_operation_id_generation(self, atomic_service, mock_job):
        """Test automatic operation ID generation."""
        with patch('app.services.atomic_file_service.get_file_lock_service') as mock_lock_service:
            mock_lock = MagicMock()
            mock_lock.acquire_lock.return_value = True
            mock_lock.release_lock.return_value = True
            mock_lock_service.return_value = mock_lock
            
            # Replace the service's lock service with our mock
            atomic_service.lock_service = mock_lock
            
            # Perform atomic move without operation_id
            result = atomic_service.atomic_move_authoritative(mock_job, "COMPLETED")
            
            # Verify operation ID was generated
            assert mock_lock.acquire_lock.call_count > 0
            call_args = mock_lock.acquire_lock.call_args
            operation_id = call_args[0][1]  # Second argument is operation_id
            assert operation_id.startswith("move_test_job_123_COMPLETED_")


class TestGlobalService:
    """Test cases for global service instance."""
    
    def test_get_atomic_file_service_singleton(self):
        """Test that global service returns singleton instance."""
        service1 = get_atomic_file_service()
        service2 = get_atomic_file_service()
        
        assert service1 is service2
    
    def test_service_has_lock_service(self):
        """Test that global service has lock service."""
        service = get_atomic_file_service()
        assert service.lock_service is not None


class TestIntegration:
    """Integration tests for atomic file operations."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_full_move_operation_integration(self, temp_dir):
        """Test complete move operation integration."""
        # Create test files
        source_file = temp_dir / "source.txt"
        dest_file = temp_dir / "Completed" / "source.txt"
        source_metadata = temp_dir / "source_metadata.json"
        dest_metadata = temp_dir / "Completed" / "source_metadata.json"
        
        source_file.write_text("test content")
        with open(source_metadata, 'w') as f:
            json.dump({"status": "UPLOADED", "file_path": str(source_file)}, f)
        
        # Create mock job
        job = MagicMock()
        job.id = "test_job_123"
        job.file_path = str(source_file)
        job.metadata_path = str(source_metadata)
        job.status = "UPLOADED"
        
        with patch('app.services.atomic_file_service.get_file_lock_service') as mock_lock_service:
            mock_lock = MagicMock()
            mock_lock.acquire_lock.return_value = True
            mock_lock.release_lock.return_value = True
            mock_lock_service.return_value = mock_lock
            
            # Perform atomic move
            service = get_atomic_file_service()
            service.lock_service = mock_lock  # Replace with mock
            result = service.atomic_move_authoritative(job, "COMPLETED")
            
            assert result is True
            
            # Verify files were moved
            assert dest_file.exists()
            assert dest_file.read_text() == "test content"
            assert dest_metadata.exists()
            
            # Verify metadata was updated
            with open(dest_metadata, 'r') as f:
                metadata = json.load(f)
            assert metadata["status"] == "COMPLETED"
            assert metadata["file_path"] == str(dest_file.resolve())
            
            # Verify job paths were updated
            assert job.file_path == str(dest_file.resolve())
            assert job.metadata_path == str(dest_metadata.resolve())
    
    def test_rollback_on_failure_integration(self, temp_dir):
        """Test rollback behavior on operation failure."""
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
        
        with patch('app.services.atomic_file_service.get_file_lock_service') as mock_lock_service:
            mock_lock = MagicMock()
            mock_lock.acquire_lock.return_value = True
            mock_lock.release_lock.return_value = True
            mock_lock_service.return_value = mock_lock
            
            # Perform atomic move that will fail due to invalid metadata
            service = get_atomic_file_service()
            service.lock_service = mock_lock  # Replace with mock
            
            # Corrupt metadata to cause failure
            source_metadata.write_text("{invalid json")
            
            result = service.atomic_move_authoritative(job, "COMPLETED")
            
            assert result is False
            
            # Verify original files still exist
            assert source_file.exists()
            assert source_file.read_text() == "test content"
            assert source_metadata.exists()
            
            # Verify job paths were not updated
            assert job.file_path == str(source_file)
            assert job.metadata_path == str(source_metadata)
