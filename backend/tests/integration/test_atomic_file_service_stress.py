"""
Stress tests for atomic file operation service.

This test suite covers:
- Concurrent file operations
- Chaos engineering (simulated failures)
- Performance testing under load
- Rollback mechanisms under failure scenarios
- Integration tests for full file lifecycle
"""

import pytest
import tempfile
import json
import shutil
import time
import threading
import random
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch, MagicMock, call
import os
import platform

from app.services.atomic_file_service import (
    AtomicFileOperation, 
    AtomicFileMoveOperation, 
    AtomicFileService,
    get_atomic_file_service
)
from app.services.file_lock_service import get_file_lock_service


class TestAtomicFileServiceStress:
    """Stress tests for atomic file operations."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def atomic_service(self):
        """Get atomic file service instance."""
        return get_atomic_file_service()
    
    @pytest.fixture
    def file_lock_service(self):
        """Get file lock service instance."""
        return get_file_lock_service()
    
    def create_test_files(self, temp_dir, num_files=10):
        """Create test files for stress testing."""
        files = []
        for i in range(num_files):
            file_path = temp_dir / f"test_file_{i}.txt"
            metadata_path = temp_dir / f"test_file_{i}_metadata.json"
            
            # Create test file
            with open(file_path, 'w') as f:
                f.write(f"Test content for file {i}")
            
            # Create metadata file
            metadata = {
                "status": "UPLOADED",
                "file_path": str(file_path),
                "created_at": "2024-01-01T12:00:00Z",
                "size": len(f"Test content for file {i}")
            }
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)
            
            files.append((file_path, metadata_path))
        
        return files
    
    def test_concurrent_file_moves(self, temp_dir, atomic_service):
        """Test concurrent file move operations using AtomicFileMoveOperation directly."""
        # Create test files
        test_files = self.create_test_files(temp_dir, 20)
        
        def move_file(file_info):
            """Move a single file using AtomicFileMoveOperation."""
            file_path, metadata_path = file_info
            target_dir = temp_dir / f"target_{random.randint(1, 5)}"
            target_dir.mkdir(exist_ok=True)
            
            target_path = target_dir / file_path.name
            target_metadata_path = target_dir / metadata_path.name
            
            try:
                # Use AtomicFileMoveOperation directly
                operation = AtomicFileMoveOperation(
                    f"move_{file_path.stem}_{random.randint(1, 1000)}",
                    f"job_{file_path.stem}",
                    file_path,
                    target_path
                )
                
                with operation as op:
                    # Prepare the move operation
                    if not op.prepare_move_operation(
                        file_path,
                        target_path,
                        metadata_path,
                        target_metadata_path,
                        {"status": "READYTOPRINT"}
                    ):
                        return f"error: prepare failed"
                    
                    # Simulate some processing time
                    time.sleep(random.uniform(0.01, 0.05))
                    
                    # Commit the operation
                    if not op.commit():
                        return f"error: commit failed"
                    
                    return op.operation_id
            except Exception as e:
                return f"error: {str(e)}"
        
        # Execute concurrent moves
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(move_file, file_info) for file_info in test_files]
            results = [future.result() for future in as_completed(futures)]
        
        # Verify results
        successful_moves = [r for r in results if not r.startswith("error:")]
        assert len(successful_moves) == len(test_files), f"Expected {len(test_files)} successful moves, got {len(successful_moves)}"
        
        # Verify all files were moved correctly
        for file_path, metadata_path in test_files:
            # Find where the file was moved
            found = False
            for target_dir in temp_dir.iterdir():
                if target_dir.is_dir() and target_dir.name.startswith("target_"):
                    if (target_dir / file_path.name).exists():
                        found = True
                        break
            assert found, f"File {file_path.name} was not moved successfully"
    
    def test_concurrent_operations_with_locking(self, temp_dir, atomic_service, file_lock_service):
        """Test concurrent operations with file locking."""
        # Create a single file that multiple operations will try to access
        file_path = temp_dir / "contested_file.txt"
        metadata_path = temp_dir / "contested_file_metadata.json"
        
        with open(file_path, 'w') as f:
            f.write("Contested content")
        
        metadata = {"status": "UPLOADED", "file_path": str(file_path)}
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
        
        results = []
        locks_acquired = []
        
        def contested_operation(operation_id):
            """Operation that tries to move the contested file."""
            target_dir = temp_dir / f"target_{operation_id}"
            target_dir.mkdir(exist_ok=True)
            
            target_path = target_dir / file_path.name
            target_metadata_path = target_dir / metadata_path.name
            
            try:
                # Try to acquire lock
                lock_acquired = file_lock_service.acquire_lock(
                    str(file_path), 
                    timeout=1.0,
                    lock_id=f"lock_{operation_id}"
                )
                locks_acquired.append(lock_acquired)
                
                if lock_acquired:
                    with atomic_service.move_file(
                        source_path=str(file_path),
                        target_path=str(target_path),
                        metadata_path=str(metadata_path),
                        target_metadata_path=str(target_metadata_path),
                        job_id=f"job_{operation_id}"
                    ) as operation:
                        time.sleep(0.1)  # Simulate processing
                        return f"success_{operation_id}"
                else:
                    return f"lock_failed_{operation_id}"
                    
            except Exception as e:
                return f"error_{operation_id}: {str(e)}"
            finally:
                if lock_acquired:
                    file_lock_service.release_lock(str(file_path), f"lock_{operation_id}")
        
        # Execute concurrent operations
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(contested_operation, i) for i in range(5)]
            results = [future.result() for future in as_completed(futures)]
        
        # Verify only one operation succeeded
        successful_ops = [r for r in results if r.startswith("success_")]
        lock_failures = [r for r in results if r.startswith("lock_failed_")]
        
        assert len(successful_ops) == 1, f"Expected 1 successful operation, got {len(successful_ops)}"
        assert len(lock_failures) == 4, f"Expected 4 lock failures, got {len(lock_failures)}"
    
    def test_chaos_engineering_disk_full(self, temp_dir, atomic_service):
        """Test behavior when disk becomes full during operation."""
        # Create test file
        file_path = temp_dir / "chaos_test.txt"
        metadata_path = temp_dir / "chaos_test_metadata.json"
        
        with open(file_path, 'w') as f:
            f.write("Chaos test content")
        
        metadata = {"status": "UPLOADED", "file_path": str(file_path)}
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
        
        target_path = temp_dir / "target" / file_path.name
        target_metadata_path = temp_dir / "target" / metadata_path.name
        
        # Mock disk full error during file copy
        with patch('shutil.copy2') as mock_copy:
            mock_copy.side_effect = OSError("No space left on device")
            
            with pytest.raises(OSError, match="No space left on device"):
                operation = AtomicFileMoveOperation("chaos_test", "chaos_job", file_path, target_path)
                with operation as op:
                    op.prepare_move_operation(
                        file_path,
                        target_path,
                        metadata_path,
                        target_metadata_path,
                        {"status": "READYTOPRINT"}
                    )
        
        # Verify original file is still intact
        assert file_path.exists(), "Original file should still exist after rollback"
        assert metadata_path.exists(), "Original metadata should still exist after rollback"
        
        # Verify target file was not created
        assert not target_path.exists(), "Target file should not exist after rollback"
        assert not target_metadata_path.exists(), "Target metadata should not exist after rollback"
    
    @pytest.mark.skipif(platform.system() == 'Windows', reason="Windows chmod does not reliably block writes; permission model differs")
    def test_chaos_engineering_permission_denied(self, temp_dir, atomic_service):
        """Test behavior when permission is denied during operation."""
        # Create test file
        file_path = temp_dir / "permission_test.txt"
        metadata_path = temp_dir / "permission_test_metadata.json"
        
        with open(file_path, 'w') as f:
            f.write("Permission test content")
        
        metadata = {"status": "UPLOADED", "file_path": str(file_path)}
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
        
        # Create target directory with no write permissions
        target_dir = temp_dir / "no_write"
        target_dir.mkdir()
        os.chmod(target_dir, 0o444)  # Read-only
        
        target_path = target_dir / file_path.name
        target_metadata_path = target_dir / metadata_path.name
        
        try:
            with pytest.raises(PermissionError):
                with atomic_service.move_file(
                    source_path=str(file_path),
                    target_path=str(target_path),
                    metadata_path=str(metadata_path),
                    target_metadata_path=str(target_metadata_path),
                    job_id="permission_test"
                ) as operation:
                    pass  # Should fail during prepare phase
            
            # Verify original file is still intact
            assert file_path.exists(), "Original file should still exist after rollback"
            assert metadata_path.exists(), "Original metadata should still exist after rollback"
            
        finally:
            # Restore permissions for cleanup
            os.chmod(target_dir, 0o755)
    
    def test_chaos_engineering_network_failure(self, temp_dir, atomic_service):
        """Test behavior when network operations fail (simulated)."""
        # Create test file
        file_path = temp_dir / "network_test.txt"
        metadata_path = temp_dir / "network_test_metadata.json"
        
        with open(file_path, 'w') as f:
            f.write("Network test content")
        
        metadata = {"status": "UPLOADED", "file_path": str(file_path)}
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
        
        target_path = temp_dir / "target" / file_path.name
        target_metadata_path = temp_dir / "target" / metadata_path.name
        
        # Mock network failure during operation
        with patch('pathlib.Path.exists') as mock_exists:
            # Simulate network failure during commit phase
            mock_exists.side_effect = [True, True, False, False]  # Source exists, staging exists, target doesn't exist
            
            with pytest.raises(FileNotFoundError):
                with atomic_service.move_file(
                    source_path=str(file_path),
                    target_path=str(target_path),
                    metadata_path=str(metadata_path),
                    target_metadata_path=str(target_metadata_path),
                    job_id="network_test"
                ) as operation:
                    pass  # Should fail during commit phase
        
        # Verify original file is still intact
        assert file_path.exists(), "Original file should still exist after rollback"
        assert metadata_path.exists(), "Original metadata should still exist after rollback"
    
    def test_performance_under_load(self, temp_dir, atomic_service):
        """Test performance of atomic operations under load."""
        # Create many test files
        test_files = self.create_test_files(temp_dir, 100)
        
        start_time = time.time()
        
        def perform_move(file_info):
            """Perform a single move operation."""
            file_path, metadata_path = file_info
            target_dir = temp_dir / f"perf_target_{file_path.stem[-2:]}"
            target_dir.mkdir(exist_ok=True)
            
            target_path = target_dir / file_path.name
            target_metadata_path = target_dir / metadata_path.name
            
            operation = AtomicFileMoveOperation(
                f"perf_move_{file_path.stem}",
                f"perf_job_{file_path.stem}",
                file_path,
                target_path
            )
            
            with operation as op:
                if not op.prepare_move_operation(
                    file_path,
                    target_path,
                    metadata_path,
                    target_metadata_path,
                    {"status": "READYTOPRINT"}
                ):
                    return None
                
                if not op.commit():
                    return None
                
                return op.operation_id
        
        # Execute operations sequentially to measure performance
        results = []
        for file_info in test_files:
            result = perform_move(file_info)
            results.append(result)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify all operations succeeded
        successful_results = [r for r in results if r is not None]
        assert len(successful_results) == 100, f"Expected 100 successful operations, got {len(successful_results)}"
        
        # Performance assertions (adjust based on system capabilities)
        assert total_time < 30.0, f"Operations took too long: {total_time:.2f} seconds"
        avg_time_per_op = total_time / 100
        assert avg_time_per_op < 0.3, f"Average time per operation too high: {avg_time_per_op:.3f} seconds"
        
        print(f"Performance test completed: {total_time:.2f}s for 100 operations ({avg_time_per_op:.3f}s avg)")
    
    def test_rollback_mechanisms_under_failure(self, temp_dir, atomic_service):
        """Test rollback mechanisms under various failure scenarios."""
        # Create test file
        file_path = temp_dir / "rollback_test.txt"
        metadata_path = temp_dir / "rollback_test_metadata.json"
        
        with open(file_path, 'w') as f:
            f.write("Rollback test content")
        
        metadata = {"status": "UPLOADED", "file_path": str(file_path), "test_data": "original"}
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
        
        target_path = temp_dir / "target" / file_path.name
        target_metadata_path = temp_dir / "target" / metadata_path.name
        
        # Test 1: Failure during prepare phase
        mock_copy = patch('shutil.copy2')
        mock_copy_obj = mock_copy.start()
        mock_copy_obj.side_effect = OSError("Prepare phase failure")
        
        try:
            with pytest.raises(OSError):
                with atomic_service.move_file(
                    source_path=str(file_path),
                    target_path=str(target_path),
                    metadata_path=str(metadata_path),
                    target_metadata_path=str(target_metadata_path),
                    job_id="rollback_test_1"
                ) as operation:
                    pass
        finally:
            mock_copy.stop()
        
        # Verify rollback worked
        assert file_path.exists(), "Original file should exist after prepare failure"
        assert metadata_path.exists(), "Original metadata should exist after prepare failure"
        assert not target_path.exists(), "Target file should not exist after prepare failure"
        
        # Test 2: Failure during commit phase
        # Recreate files for this test to ensure clean state
        with open(file_path, 'w') as f:
            f.write("Rollback test content 2")
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
        
        with patch('pathlib.Path.unlink') as mock_unlink:
            mock_unlink.side_effect = OSError("Commit phase failure")
            
            with pytest.raises(OSError):
                with atomic_service.move_file(
                    source_path=str(file_path),
                    target_path=str(target_path),
                    metadata_path=str(metadata_path),
                    target_metadata_path=str(target_metadata_path),
                    job_id="rollback_test_2"
                ) as operation:
                    pass
        
        # Verify rollback worked
        assert file_path.exists(), "Original file should exist after commit failure"
        assert metadata_path.exists(), "Original metadata should exist after commit failure"
        
        # Test 3: Failure during cleanup phase
        with patch('shutil.rmtree') as mock_rmtree:
            mock_rmtree.side_effect = OSError("Cleanup phase failure")
            
            # This should not raise an exception as cleanup failures are non-critical
            with atomic_service.move_file(
                source_path=str(file_path),
                target_path=str(target_path),
                metadata_path=str(metadata_path),
                target_metadata_path=str(target_metadata_path),
                job_id="rollback_test_3"
            ) as operation:
                pass
        
        # Verify operation succeeded despite cleanup failure
        assert not file_path.exists(), "Original file should be moved"
        assert not metadata_path.exists(), "Original metadata should be moved"
        assert target_path.exists(), "Target file should exist"
        assert target_metadata_path.exists(), "Target metadata should exist"
    
    def test_integration_full_file_lifecycle(self, temp_dir, atomic_service):
        """Test complete file lifecycle with atomic operations."""
        # Simulate a complete job lifecycle: UPLOADED -> PENDING -> READYTOPRINT -> PRINTING -> COMPLETED -> PAIDPICKEDUP
        
        # Initial file
        file_path = temp_dir / "lifecycle_test.txt"
        metadata_path = temp_dir / "lifecycle_test_metadata.json"
        
        with open(file_path, 'w') as f:
            f.write("Lifecycle test content")
        
        initial_metadata = {
            "status": "UPLOADED",
            "file_path": str(file_path),
            "created_at": "2024-01-01T12:00:00Z",
            "lifecycle_step": 0
        }
        with open(metadata_path, 'w') as f:
            json.dump(initial_metadata, f)
        
        # Step 1: UPLOADED -> PENDING (status change only, no file move)
        current_file_path = file_path
        current_metadata_path = metadata_path
        
        # Step 2: PENDING -> READYTOPRINT
        target_dir = temp_dir / "ReadyToPrint"
        target_dir.mkdir()
        target_path = target_dir / file_path.name
        target_metadata_path = target_dir / metadata_path.name
        
        with atomic_service.move_file(
            source_path=str(current_file_path),
            target_path=str(target_path),
            metadata_path=str(current_metadata_path),
            target_metadata_path=str(target_metadata_path),
            job_id="lifecycle_test"
        ) as operation:
            # Update metadata during move
            updated_metadata = {
                "status": "READYTOPRINT",
                "file_path": str(target_path),
                "created_at": "2024-01-01T12:00:00Z",
                "lifecycle_step": 2
            }
            with open(target_metadata_path, 'w') as f:
                json.dump(updated_metadata, f)
        
        current_file_path = target_path
        current_metadata_path = target_metadata_path
        
        # Step 3: READYTOPRINT -> PRINTING
        target_dir = temp_dir / "Printing"
        target_dir.mkdir()
        target_path = target_dir / file_path.name
        target_metadata_path = target_dir / metadata_path.name
        
        with atomic_service.move_file(
            source_path=str(current_file_path),
            target_path=str(target_path),
            metadata_path=str(current_metadata_path),
            target_metadata_path=str(target_metadata_path),
            job_id="lifecycle_test"
        ) as operation:
            updated_metadata = {
                "status": "PRINTING",
                "file_path": str(target_path),
                "created_at": "2024-01-01T12:00:00Z",
                "lifecycle_step": 3
            }
            with open(target_metadata_path, 'w') as f:
                json.dump(updated_metadata, f)
        
        current_file_path = target_path
        current_metadata_path = target_metadata_path
        
        # Step 4: PRINTING -> COMPLETED
        target_dir = temp_dir / "Completed"
        target_dir.mkdir()
        target_path = target_dir / file_path.name
        target_metadata_path = target_dir / metadata_path.name
        
        with atomic_service.move_file(
            source_path=str(current_file_path),
            target_path=str(target_path),
            metadata_path=str(current_metadata_path),
            target_metadata_path=str(target_metadata_path),
            job_id="lifecycle_test"
        ) as operation:
            updated_metadata = {
                "status": "COMPLETED",
                "file_path": str(target_path),
                "created_at": "2024-01-01T12:00:00Z",
                "lifecycle_step": 4
            }
            with open(target_metadata_path, 'w') as f:
                json.dump(updated_metadata, f)
        
        current_file_path = target_path
        current_metadata_path = target_metadata_path
        
        # Step 5: COMPLETED -> PAIDPICKEDUP
        target_dir = temp_dir / "PaidPickedUp"
        target_dir.mkdir()
        target_path = target_dir / file_path.name
        target_metadata_path = target_dir / metadata_path.name
        
        with atomic_service.move_file(
            source_path=str(current_file_path),
            target_path=str(target_path),
            metadata_path=str(current_metadata_path),
            target_metadata_path=str(target_metadata_path),
            job_id="lifecycle_test"
        ) as operation:
            updated_metadata = {
                "status": "PAIDPICKEDUP",
                "file_path": str(target_path),
                "created_at": "2024-01-01T12:00:00Z",
                "lifecycle_step": 5
            }
            with open(target_metadata_path, 'w') as f:
                json.dump(updated_metadata, f)
        
        # Verify final state
        assert target_path.exists(), "Final file should exist"
        assert target_metadata_path.exists(), "Final metadata should exist"
        
        with open(target_path, 'r') as f:
            content = f.read()
        assert content == "Lifecycle test content", "File content should be preserved"
        
        with open(target_metadata_path, 'r') as f:
            final_metadata = json.load(f)
        assert final_metadata["status"] == "PAIDPICKEDUP", "Final status should be PAIDPICKEDUP"
        assert final_metadata["lifecycle_step"] == 5, "Final lifecycle step should be 5"
        
        # Verify intermediate directories are empty (files were moved, not copied)
        for step_dir in ["ReadyToPrint", "Printing", "Completed"]:
            step_path = temp_dir / step_dir
            if step_path.exists():
                files_in_dir = list(step_path.iterdir())
                assert len(files_in_dir) == 0, f"Directory {step_dir} should be empty after move"
