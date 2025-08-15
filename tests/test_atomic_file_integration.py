"""
Integration tests for atomic file operations with database transactions.

This test suite covers:
- Integration between atomic file operations and database transactions
- End-to-end job lifecycle with atomic guarantees
- Database rollback when file operations fail
- File rollback when database operations fail
- Complete atomicity across the entire system
"""

import pytest
import tempfile
import json
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from app.services.atomic_file_service import get_atomic_file_service
from app.services.db_transaction_service import get_db_transaction_service
from app.services.file_lock_service import get_file_lock_service
from app.models.job import Job
from app.models.event import Event
from app import db


class TestAtomicFileDatabaseIntegration:
    """Integration tests for atomic file operations with database transactions."""
    
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
    def db_transaction_service(self):
        """Get database transaction service instance."""
        return get_db_transaction_service()
    
    @pytest.fixture
    def file_lock_service(self):
        """Get file lock service instance."""
        return get_file_lock_service()
    
    def create_test_job(self, temp_dir, status="UPLOADED"):
        """Create a test job with associated files."""
        # Create test file
        file_path = temp_dir / "test_job.stl"
        metadata_path = temp_dir / "test_job_metadata.json"
        
        with open(file_path, 'w') as f:
            f.write("Test job content")
        
        metadata = {
            "status": status,
            "file_path": str(file_path),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "job_id": "test_job_123"
        }
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)
        
        # Create job in database
        job = Job(
            id="test_job_123",
            student_name="Test Student",
            student_email="test@example.com",
            file_path=str(file_path),
            metadata_path=str(metadata_path),
            status=status,
            display_name="test_job.stl",
            original_filename="test_job.stl"
        )
        
        return job, file_path, metadata_path
    
    def test_integration_job_approval_workflow(self, temp_dir, atomic_service, db_transaction_service, file_lock_service):
        """Test complete job approval workflow with atomic guarantees."""
        # Create test job
        job, file_path, metadata_path = self.create_test_job(temp_dir, "UPLOADED")
        
        # Add job to database
        db.session.add(job)
        db.session.commit()
        
        # Simulate job approval workflow
        target_dir = temp_dir / "ReadyToPrint"
        target_dir.mkdir()
        target_path = target_dir / file_path.name
        target_metadata_path = target_dir / metadata_path.name
        
        try:
            with db_transaction_service.transaction() as db_txn:
                # Update job status in database
                job.status = "READYTOPRINT"
                job.weight_g = 50.0
                job.time_hours = 2.5
                job.cost_usd = 5.00
                job.last_updated_by = "test_staff"
                db.session.add(job)
                
                # Create approval event
                event = Event(
                    job_id=job.id,
                    event_type="StaffApproved",
                    details={"weight_g": 50.0, "time_hours": 2.5, "cost_usd": 5.00},
                    triggered_by="test_staff",
                    workstation_id="test_workstation"
                )
                db.session.add(event)
                
                # Perform atomic file move
                with atomic_service.move_file(
                    source_path=str(file_path),
                    target_path=str(target_path),
                    metadata_path=str(metadata_path),
                    target_metadata_path=str(target_metadata_path),
                    job_id=job.id
                ) as file_op:
                    # Update metadata during move
                    updated_metadata = {
                        "status": "READYTOPRINT",
                        "file_path": str(target_path),
                        "created_at": metadata["created_at"],
                        "job_id": job.id,
                        "weight_g": 50.0,
                        "time_hours": 2.5,
                        "cost_usd": 5.00,
                        "approved_by": "test_staff"
                    }
                    with open(target_metadata_path, 'w') as f:
                        json.dump(updated_metadata, f)
                    
                    # Update job file paths
                    job.file_path = str(target_path)
                    job.metadata_path = str(target_metadata_path)
                    db.session.add(job)
                
                # Commit both database and file operations
                db_txn.commit()
        
        except Exception as e:
            # Both database and file operations should be rolled back
            db_txn.rollback()
            raise
        
        # Verify final state
        # Database state
        db.session.refresh(job)
        assert job.status == "READYTOPRINT"
        assert job.file_path == str(target_path)
        assert job.metadata_path == str(target_metadata_path)
        assert job.weight_g == 50.0
        
        # File state
        assert not file_path.exists(), "Original file should be moved"
        assert not metadata_path.exists(), "Original metadata should be moved"
        assert target_path.exists(), "Target file should exist"
        assert target_metadata_path.exists(), "Target metadata should exist"
        
        # Event state
        events = Event.query.filter_by(job_id=job.id).all()
        assert len(events) == 1
        assert events[0].event_type == "StaffApproved"
    
    def test_integration_database_rollback_on_file_failure(self, temp_dir, atomic_service, db_transaction_service):
        """Test database rollback when file operations fail."""
        # Create test job
        job, file_path, metadata_path = self.create_test_job(temp_dir, "UPLOADED")
        
        # Add job to database
        db.session.add(job)
        db.session.commit()
        
        # Create target directory with no write permissions to cause file operation failure
        target_dir = temp_dir / "no_write"
        target_dir.mkdir()
        import os
        os.chmod(target_dir, 0o444)  # Read-only
        
        target_path = target_dir / file_path.name
        target_metadata_path = target_dir / metadata_path.name
        
        try:
            with db_transaction_service.transaction() as db_txn:
                # Update job status in database
                job.status = "READYTOPRINT"
                job.last_updated_by = "test_staff"
                db.session.add(job)
                
                # Create event
                event = Event(
                    job_id=job.id,
                    event_type="StaffApproved",
                    details={},
                    triggered_by="test_staff",
                    workstation_id="test_workstation"
                )
                db.session.add(event)
                
                # This should fail due to permission error
                with pytest.raises(PermissionError):
                    with atomic_service.move_file(
                        source_path=str(file_path),
                        target_path=str(target_path),
                        metadata_path=str(metadata_path),
                        target_metadata_path=str(target_metadata_path),
                        job_id=job.id
                    ) as file_op:
                        pass
                
                # Should not reach here, but if it does, commit should fail
                db_txn.commit()
        
        except Exception:
            # Database transaction should be rolled back
            db_txn.rollback()
        
        finally:
            # Restore permissions for cleanup
            os.chmod(target_dir, 0o755)
        
        # Verify database state was rolled back
        db.session.refresh(job)
        assert job.status == "UPLOADED", "Job status should be rolled back"
        assert job.last_updated_by is None, "Job last_updated_by should be rolled back"
        
        # Verify no events were created
        events = Event.query.filter_by(job_id=job.id).all()
        assert len(events) == 0, "No events should be created"
        
        # Verify file state is unchanged
        assert file_path.exists(), "Original file should still exist"
        assert metadata_path.exists(), "Original metadata should still exist"
        assert not target_path.exists(), "Target file should not exist"
    
    def test_integration_file_rollback_on_database_failure(self, temp_dir, atomic_service, db_transaction_service):
        """Test file rollback when database operations fail."""
        # Create test job
        job, file_path, metadata_path = self.create_test_job(temp_dir, "UPLOADED")
        
        # Add job to database
        db.session.add(job)
        db.session.commit()
        
        target_dir = temp_dir / "ReadyToPrint"
        target_dir.mkdir()
        target_path = target_dir / file_path.name
        target_metadata_path = target_dir / metadata_path.name
        
        try:
            with db_transaction_service.transaction() as db_txn:
                # Perform atomic file move first
                with atomic_service.move_file(
                    source_path=str(file_path),
                    target_path=str(target_path),
                    metadata_path=str(metadata_path),
                    target_metadata_path=str(target_metadata_path),
                    job_id=job.id
                ) as file_op:
                    # Update metadata
                    updated_metadata = {
                        "status": "READYTOPRINT",
                        "file_path": str(target_path),
                        "created_at": metadata["created_at"],
                        "job_id": job.id
                    }
                    with open(target_metadata_path, 'w') as f:
                        json.dump(updated_metadata, f)
                
                # Update job status in database
                job.status = "READYTOPRINT"
                job.file_path = str(target_path)
                job.metadata_path = str(target_metadata_path)
                db.session.add(job)
                
                # Create event with invalid data to cause database failure
                event = Event(
                    job_id=job.id,
                    event_type="StaffApproved",
                    details={"invalid_field": "x" * 10000},  # Too long for database
                    triggered_by="test_staff",
                    workstation_id="test_workstation"
                )
                db.session.add(event)
                
                # This should fail due to database constraint
                with pytest.raises(Exception):
                    db_txn.commit()
        
        except Exception:
            # Database transaction should be rolled back
            db_txn.rollback()
        
        # Verify database state was rolled back
        db.session.refresh(job)
        assert job.status == "UPLOADED", "Job status should be rolled back"
        assert job.file_path == str(file_path), "Job file_path should be rolled back"
        
        # Verify no events were created
        events = Event.query.filter_by(job_id=job.id).all()
        assert len(events) == 0, "No events should be created"
        
        # Verify file state is unchanged (file operations should be rolled back)
        assert file_path.exists(), "Original file should still exist"
        assert metadata_path.exists(), "Original metadata should still exist"
        assert not target_path.exists(), "Target file should not exist"
        assert not target_metadata_path.exists(), "Target metadata should not exist"
    
    def test_integration_concurrent_job_operations(self, temp_dir, atomic_service, db_transaction_service, file_lock_service):
        """Test concurrent job operations with proper locking and atomicity."""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import time
        import random
        
        # Create multiple test jobs
        jobs = []
        for i in range(5):
            job, file_path, metadata_path = self.create_test_job(temp_dir, "UPLOADED")
            job.id = f"test_job_{i}"
            jobs.append((job, file_path, metadata_path))
            
            # Add job to database
            db.session.add(job)
        db.session.commit()
        
        results = []
        
        def process_job(job_info):
            """Process a single job with atomic operations."""
            job, file_path, metadata_path = job_info
            
            # Try to acquire file lock
            lock_acquired = file_lock_service.acquire_lock(
                str(file_path), 
                timeout=2.0,
                lock_id=f"lock_{job.id}"
            )
            
            if not lock_acquired:
                return f"lock_failed_{job.id}"
            
            try:
                target_dir = temp_dir / f"target_{random.randint(1, 3)}"
                target_dir.mkdir(exist_ok=True)
                target_path = target_dir / file_path.name
                target_metadata_path = target_dir / metadata_path.name
                
                with db_transaction_service.transaction() as db_txn:
                    # Update job status
                    job.status = "READYTOPRINT"
                    job.last_updated_by = f"staff_{random.randint(1, 3)}"
                    db.session.add(job)
                    
                    # Create event
                    event = Event(
                        job_id=job.id,
                        event_type="StaffApproved",
                        details={"processed_by": f"staff_{random.randint(1, 3)}"},
                        triggered_by=f"staff_{random.randint(1, 3)}",
                        workstation_id="test_workstation"
                    )
                    db.session.add(event)
                    
                    # Perform atomic file move
                    with atomic_service.move_file(
                        source_path=str(file_path),
                        target_path=str(target_path),
                        metadata_path=str(metadata_path),
                        target_metadata_path=str(target_metadata_path),
                        job_id=job.id
                    ) as file_op:
                        # Update metadata
                        updated_metadata = {
                            "status": "READYTOPRINT",
                            "file_path": str(target_path),
                            "created_at": metadata["created_at"],
                            "job_id": job.id,
                            "processed_by": f"staff_{random.randint(1, 3)}"
                        }
                        with open(target_metadata_path, 'w') as f:
                            json.dump(updated_metadata, f)
                        
                        # Update job file paths
                        job.file_path = str(target_path)
                        job.metadata_path = str(target_metadata_path)
                        db.session.add(job)
                    
                    # Simulate some processing time
                    time.sleep(random.uniform(0.01, 0.05))
                    
                    # Commit transaction
                    db_txn.commit()
                
                return f"success_{job.id}"
                
            except Exception as e:
                return f"error_{job.id}: {str(e)}"
            finally:
                file_lock_service.release_lock(str(file_path), f"lock_{job.id}")
        
        # Execute concurrent job processing
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(process_job, job_info) for job_info in jobs]
            results = [future.result() for future in as_completed(futures)]
        
        # Verify results
        successful_ops = [r for r in results if r.startswith("success_")]
        assert len(successful_ops) == 5, f"Expected 5 successful operations, got {len(successful_ops)}"
        
        # Verify all jobs were processed correctly
        for job, file_path, metadata_path in jobs:
            db.session.refresh(job)
            assert job.status == "READYTOPRINT", f"Job {job.id} should be READYTOPRINT"
            assert job.last_updated_by is not None, f"Job {job.id} should have last_updated_by set"
            
            # Verify events were created
            events = Event.query.filter_by(job_id=job.id).all()
            assert len(events) == 1, f"Job {job.id} should have one event"
            assert events[0].event_type == "StaffApproved", f"Job {job.id} should have StaffApproved event"
    
    def test_integration_complete_job_lifecycle(self, temp_dir, atomic_service, db_transaction_service):
        """Test complete job lifecycle with atomic guarantees."""
        # Create test job
        job, file_path, metadata_path = self.create_test_job(temp_dir, "UPLOADED")
        
        # Add job to database
        db.session.add(job)
        db.session.commit()
        
        # Step 1: UPLOADED -> PENDING (status change only)
        with db_transaction_service.transaction() as db_txn:
            job.status = "PENDING"
            job.last_updated_by = "test_staff"
            db.session.add(job)
            
            event = Event(
                job_id=job.id,
                event_type="JobStatusChanged",
                details={"from": "UPLOADED", "to": "PENDING"},
                triggered_by="test_staff",
                workstation_id="test_workstation"
            )
            db.session.add(event)
            
            db_txn.commit()
        
        # Step 2: PENDING -> READYTOPRINT (file move)
        target_dir = temp_dir / "ReadyToPrint"
        target_dir.mkdir()
        target_path = target_dir / file_path.name
        target_metadata_path = target_dir / metadata_path.name
        
        with db_transaction_service.transaction() as db_txn:
            job.status = "READYTOPRINT"
            job.last_updated_by = "test_staff"
            db.session.add(job)
            
            event = Event(
                job_id=job.id,
                event_type="StaffApproved",
                details={"weight_g": 50.0, "time_hours": 2.5},
                triggered_by="test_staff",
                workstation_id="test_workstation"
            )
            db.session.add(event)
            
            with atomic_service.move_file(
                source_path=str(file_path),
                target_path=str(target_path),
                metadata_path=str(metadata_path),
                target_metadata_path=str(target_metadata_path),
                job_id=job.id
            ) as file_op:
                updated_metadata = {
                    "status": "READYTOPRINT",
                    "file_path": str(target_path),
                    "created_at": metadata["created_at"],
                    "job_id": job.id,
                    "weight_g": 50.0,
                    "time_hours": 2.5
                }
                with open(target_metadata_path, 'w') as f:
                    json.dump(updated_metadata, f)
                
                job.file_path = str(target_path)
                job.metadata_path = str(target_metadata_path)
                db.session.add(job)
            
            db_txn.commit()
        
        # Step 3: READYTOPRINT -> PRINTING (file move)
        current_file_path = target_path
        current_metadata_path = target_metadata_path
        
        target_dir = temp_dir / "Printing"
        target_dir.mkdir()
        target_path = target_dir / file_path.name
        target_metadata_path = target_dir / metadata_path.name
        
        with db_transaction_service.transaction() as db_txn:
            job.status = "PRINTING"
            job.last_updated_by = "test_staff"
            db.session.add(job)
            
            event = Event(
                job_id=job.id,
                event_type="JobMarkedPrinting",
                details={},
                triggered_by="test_staff",
                workstation_id="test_workstation"
            )
            db.session.add(event)
            
            with atomic_service.move_file(
                source_path=str(current_file_path),
                target_path=str(target_path),
                metadata_path=str(current_metadata_path),
                target_metadata_path=str(target_metadata_path),
                job_id=job.id
            ) as file_op:
                updated_metadata = {
                    "status": "PRINTING",
                    "file_path": str(target_path),
                    "created_at": metadata["created_at"],
                    "job_id": job.id,
                    "weight_g": 50.0,
                    "time_hours": 2.5
                }
                with open(target_metadata_path, 'w') as f:
                    json.dump(updated_metadata, f)
                
                job.file_path = str(target_path)
                job.metadata_path = str(target_metadata_path)
                db.session.add(job)
            
            db_txn.commit()
        
        # Step 4: PRINTING -> COMPLETED (file move)
        current_file_path = target_path
        current_metadata_path = target_metadata_path
        
        target_dir = temp_dir / "Completed"
        target_dir.mkdir()
        target_path = target_dir / file_path.name
        target_metadata_path = target_dir / metadata_path.name
        
        with db_transaction_service.transaction() as db_txn:
            job.status = "COMPLETED"
            job.last_updated_by = "test_staff"
            db.session.add(job)
            
            event = Event(
                job_id=job.id,
                event_type="JobMarkedComplete",
                details={},
                triggered_by="test_staff",
                workstation_id="test_workstation"
            )
            db.session.add(event)
            
            with atomic_service.move_file(
                source_path=str(current_file_path),
                target_path=str(target_path),
                metadata_path=str(current_metadata_path),
                target_metadata_path=str(target_metadata_path),
                job_id=job.id
            ) as file_op:
                updated_metadata = {
                    "status": "COMPLETED",
                    "file_path": str(target_path),
                    "created_at": metadata["created_at"],
                    "job_id": job.id,
                    "weight_g": 50.0,
                    "time_hours": 2.5
                }
                with open(target_metadata_path, 'w') as f:
                    json.dump(updated_metadata, f)
                
                job.file_path = str(target_path)
                job.metadata_path = str(target_metadata_path)
                db.session.add(job)
            
            db_txn.commit()
        
        # Step 5: COMPLETED -> PAIDPICKEDUP (file move)
        current_file_path = target_path
        current_metadata_path = target_metadata_path
        
        target_dir = temp_dir / "PaidPickedUp"
        target_dir.mkdir()
        target_path = target_dir / file_path.name
        target_metadata_path = target_dir / metadata_path.name
        
        with db_transaction_service.transaction() as db_txn:
            job.status = "PAIDPICKEDUP"
            job.last_updated_by = "test_staff"
            db.session.add(job)
            
            event = Event(
                job_id=job.id,
                event_type="JobMarkedPickedUp",
                details={},
                triggered_by="test_staff",
                workstation_id="test_workstation"
            )
            db.session.add(event)
            
            with atomic_service.move_file(
                source_path=str(current_file_path),
                target_path=str(target_path),
                metadata_path=str(current_metadata_path),
                target_metadata_path=str(target_metadata_path),
                job_id=job.id
            ) as file_op:
                updated_metadata = {
                    "status": "PAIDPICKEDUP",
                    "file_path": str(target_path),
                    "created_at": metadata["created_at"],
                    "job_id": job.id,
                    "weight_g": 50.0,
                    "time_hours": 2.5
                }
                with open(target_metadata_path, 'w') as f:
                    json.dump(updated_metadata, f)
                
                job.file_path = str(target_path)
                job.metadata_path = str(target_metadata_path)
                db.session.add(job)
            
            db_txn.commit()
        
        # Verify final state
        db.session.refresh(job)
        assert job.status == "PAIDPICKEDUP"
        assert job.file_path == str(target_path)
        assert job.metadata_path == str(target_metadata_path)
        
        # Verify all events were created
        events = Event.query.filter_by(job_id=job.id).order_by(Event.created_at).all()
        assert len(events) == 5
        event_types = [e.event_type for e in events]
        assert event_types == [
            "JobStatusChanged",
            "StaffApproved", 
            "JobMarkedPrinting",
            "JobMarkedComplete",
            "JobMarkedPickedUp"
        ]
        
        # Verify file state
        assert target_path.exists(), "Final file should exist"
        assert target_metadata_path.exists(), "Final metadata should exist"
        
        with open(target_path, 'r') as f:
            content = f.read()
        assert content == "Test job content", "File content should be preserved"
        
        # Verify intermediate directories are empty
        for step_dir in ["ReadyToPrint", "Printing", "Completed"]:
            step_path = temp_dir / step_dir
            if step_path.exists():
                files_in_dir = list(step_path.iterdir())
                assert len(files_in_dir) == 0, f"Directory {step_dir} should be empty after move"
