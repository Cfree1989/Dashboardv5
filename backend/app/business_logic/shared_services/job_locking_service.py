from typing import Optional
from datetime import datetime, timedelta

# Import foundation services
from app.business_logic.shared_services.validation_service import ValidationService
from app.business_logic.shared_services.response_service import ResponseService

# Import models and services
from app.models.job import Job
from app import db

class JobLockData:
    """Data class for job lock parameters"""
    def __init__(self, workstation_id: str, lock_duration_minutes: int = 5):
        self.workstation_id = workstation_id
        self.lock_duration_minutes = lock_duration_minutes

class JobLockingService:
    """Service for managing job locking operations"""
    
    def __init__(self, validation_service=None, response_service=None):
        """Use dependency injection for testability"""
        self.validation = validation_service or ValidationService
        self.response = response_service or ResponseService
    
    def lock_job(self, job_id: str, lock_data: JobLockData) -> Job:
        """Lock a job with comprehensive validation and business logic"""
        # Use ValidationService for all validation
        job_result = self.validation.validate_job_exists(job_id)
        if not job_result.is_valid:
            raise ValueError(job_result.error_message)
        
        job = job_result.data
        
        # Check if job is already locked
        now = datetime.utcnow()
        if job.locked_by and job.locked_until and job.locked_until > now:
            raise ValueError('Job is already locked')
        
        # Lock the job
        job.locked_by = lock_data.workstation_id
        job.locked_until = now + timedelta(minutes=lock_data.lock_duration_minutes)
        
        db.session.add(job)
        db.session.commit()
        
        return job
    
    def unlock_job(self, job_id: str, lock_data: JobLockData) -> Job:
        """Unlock a job with comprehensive validation and business logic"""
        # Use ValidationService for all validation
        job_result = self.validation.validate_job_exists(job_id)
        if not job_result.is_valid:
            raise ValueError(job_result.error_message)
        
        job = job_result.data
        
        from datetime import datetime, timezone

        # Graceful unlock rules:
        # 1. If job has no lock, succeed silently
        # 2. If we do not own the lock but it is expired, clear it and succeed
        # 3. If we do not own the lock and it is still active, keep it but return success (no error cascade)

        if job.locked_by is None:
            return job

        if job.locked_by != lock_data.workstation_id:
            now = datetime.now(timezone.utc)
            if job.locked_until and now > job.locked_until.replace(tzinfo=timezone.utc):
                # Lock expired – clear it
                job.locked_by = None
                job.locked_until = None
            # Either way, return job without error
            db.session.add(job)
            db.session.commit()
            return job

        # We own the lock – clear it normally
        job.locked_by = None
        job.locked_until = None
        
        db.session.add(job)
        db.session.commit()
        
        return job
    
    def extend_job_lock(self, job_id: str, lock_data: JobLockData) -> Job:
        """Extend a job lock with comprehensive validation and business logic"""
        # Use ValidationService for all validation
        job_result = self.validation.validate_job_exists(job_id)
        if not job_result.is_valid:
            raise ValueError(job_result.error_message)
        
        job = job_result.data
        
        # Check if current workstation owns the lock
        if job.locked_by != lock_data.workstation_id:
            raise ValueError('Not lock owner')
        
        # Extend the lock
        job.locked_until = datetime.utcnow() + timedelta(minutes=lock_data.lock_duration_minutes)
        
        db.session.add(job)
        db.session.commit()
        
        return job
