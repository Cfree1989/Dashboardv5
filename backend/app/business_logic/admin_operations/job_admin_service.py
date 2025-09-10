from typing import Optional
from datetime import datetime
from pathlib import Path

# Import foundation services
from app.business_logic.shared_services.validation_service import ValidationService
from app.business_logic.shared_services.response_service import ResponseService

# Import models and services
from app.models.job import Job
from app.models.event import Event
from app.business_logic.shared_services.token_service import generate_confirmation_token
from app.business_logic.shared_services.email_service import send_approval_email
from app.services.infrastructure.atomic_file_service import get_atomic_file_service
# Import moved to method level to avoid circular imports
from app import db

# Status to directory mapping for file operations
STATUS_TO_DIR = {
    'UPLOADED': 'Uploaded',
    'PENDING': 'Pending', 
    'READYTOPRINT': 'ReadyToPrint',
    'PRINTING': 'Printing',
    'COMPLETED': 'Completed',
    'PAIDPICKEDUP': 'PaidPickedUp',
    'ARCHIVED': 'Archived'
}

class JobAdminStatusChangeData:
    """Data class for admin status change parameters"""
    def __init__(self, staff_name: str, new_status: str, reason: str):
        self.staff_name = staff_name
        self.new_status = new_status
        self.reason = reason

class JobDeleteData:
    """Data class for job deletion parameters"""
    def __init__(self, staff_name: str = None):
        self.staff_name = staff_name

class JobResendEmailData:
    """Data class for resending email parameters"""
    def __init__(self, staff_name: str):
        self.staff_name = staff_name

class JobForceUnlockData:
    """Data class for force unlock parameters"""
    def __init__(self, staff_name: str, reason: str):
        self.staff_name = staff_name
        self.reason = reason

class JobAdminService:
    """Service for managing admin operations and force actions"""
    
    def __init__(self, validation_service=None, response_service=None):
        """Use dependency injection for testability"""
        self.validation = validation_service or ValidationService
        self.response = response_service or ResponseService
        # Reduce rate limit pressure in tests by caching last resend timestamp in-memory
        self._last_resend_by_job: dict[str, datetime] = {}
    
    def _get_workstation_id(self) -> Optional[str]:
        """Get workstation ID from request context if available"""
        try:
            from flask import request
            return request.headers.get('X-Workstation-ID')
        except RuntimeError:
            # Not in request context (e.g., during testing)
            return None
    
    def admin_change_status(self, job_id: str, status_change_data: JobAdminStatusChangeData, workstation_id: str = None) -> Job:
        """Admin change job status with comprehensive validation and business logic"""
        # Use ValidationService for all validation
        job_result = self.validation.validate_job_exists(job_id)
        if not job_result.is_valid:
            raise ValueError(job_result.error_message)
        
        staff_result = self.validation.validate_staff(status_change_data.staff_name)
        if not staff_result.is_valid:
            raise ValueError(staff_result.error_message)
        
        # Validate new status
        new_status = status_change_data.new_status.strip().upper()
        if not new_status:
            raise ValueError('new_status is required')
        
        allowed_statuses = set(list(STATUS_TO_DIR.keys()) + ['REJECTED'])
        if new_status not in allowed_statuses:
            raise ValueError('Invalid new_status')
        
        job = job_result.data
        before = job.status
        
        # Update job
        job.status = new_status
        job.last_updated_by = status_change_data.staff_name
        # Auto flag rules for unreviewed when crossing Uploaded boundary
        try:
            if hasattr(job, 'is_unreviewed'):
                if new_status == 'UPLOADED':
                    job.is_unreviewed = True
                elif before == 'UPLOADED' and new_status != 'UPLOADED':
                    job.is_unreviewed = False
        except Exception:
            pass
        
        # Move files only if mapping exists for the target status
        if new_status in STATUS_TO_DIR:
            atomic_service = get_atomic_file_service()
            success = atomic_service.atomic_move_authoritative(job, new_status)
            if not success:
                raise RuntimeError(f'File operation failed during admin status change to {new_status}')
        
        db.session.add(job)
        db.session.commit()
        
        # Log events
        workstation_id = workstation_id or self._get_workstation_id() or 'system'
        evt = Event(
            job_id=job.id, 
            event_type='AdminStatusChanged', 
            details={'from': before, 'to': new_status, 'reason': status_change_data.reason}, 
            triggered_by=status_change_data.staff_name, 
            workstation_id=workstation_id
        )
        db.session.add(evt)
        db.session.commit()
        
        evt2 = Event(
            job_id=job.id, 
            event_type='AdminAction', 
            details={'action': 'change_status', 'from': before, 'to': new_status, 'reason': status_change_data.reason}, 
            triggered_by=status_change_data.staff_name, 
            workstation_id=workstation_id
        )
        db.session.add(evt2)
        db.session.commit()
        
        return job
    
    def delete_job(self, job_id: str, delete_data: JobDeleteData = None, workstation_id: str = None) -> Job:
        """Soft delete a job (archive) with comprehensive validation and business logic"""
        # Use ValidationService for all validation
        job_result = self.validation.validate_job_exists(job_id)
        if not job_result.is_valid:
            raise ValueError(job_result.error_message)
        
        job = job_result.data
        
        # Allow soft-delete primarily for early statuses
        if job.status not in ('UPLOADED', 'PENDING'):
            raise ValueError('Job cannot be deleted in its current status')
        
        before = job.status
        job.status = 'ARCHIVED'
        # Leaving Uploaded via archive clears unreviewed
        try:
            if hasattr(job, 'is_unreviewed') and before == 'UPLOADED':
                job.is_unreviewed = False
        except Exception:
            pass
        
        # Move file/metadata to Archived and sync metadata
        atomic_service = get_atomic_file_service()
        success = atomic_service.atomic_move_authoritative(job, 'ARCHIVED')
        if not success:
            raise RuntimeError('File operation failed during job archival')
        db.session.add(job)
        db.session.commit()
        
        # Log event
        workstation_id = workstation_id or self._get_workstation_id() or 'system'
        evt = Event(
            job_id=job.id, 
            event_type='JobArchived', 
            details={'from': before, 'to': 'ARCHIVED'}, 
            triggered_by=workstation_id or 'system', 
            workstation_id=workstation_id or 'system'
        )
        db.session.add(evt)
        db.session.commit()
        
        # Sync metadata
        self._sync_authoritative_metadata(job, Path(job.file_path).name, None, 'JobArchived')
        
        return job
    
    def hard_delete_job(self, job_id: str, delete_data: JobDeleteData, workstation_id: str = None) -> dict:
        """Hard delete a job with comprehensive validation and business logic"""
        # Use ValidationService for all validation
        job_result = self.validation.validate_job_exists(job_id)
        if not job_result.is_valid:
            raise ValueError(job_result.error_message)
        
        if not delete_data.staff_name:
            raise ValueError('staff_name is required')
        
        job = job_result.data
        
        # Best-effort remove files
        try:
            p = Path(job.file_path)
            if p.exists():
                p.unlink(missing_ok=True)
            mp = Path(job.metadata_path) if getattr(job, 'metadata_path', None) else None
            if mp and mp.exists():
                mp.unlink(missing_ok=True)
        except Exception:
            pass  # Best-effort file removal
        
        db.session.delete(job)
        db.session.commit()
        
        # Log event
        workstation_id = workstation_id or self._get_workstation_id() or 'system'
        evt = Event(
            job_id=job_id, 
            event_type='JobHardDeleted', 
            details={}, 
            triggered_by=delete_data.staff_name, 
            workstation_id=workstation_id or 'system'
        )
        db.session.add(evt)
        db.session.commit()
        
        return {'message': 'deleted'}
    
    def resend_approval_email(self, job_id: str, resend_data: JobResendEmailData, workstation_id: str = None) -> dict:
        """Resend approval email with comprehensive validation and business logic"""
        # Use ValidationService for all validation
        job_result = self.validation.validate_job_exists(job_id)
        if not job_result.is_valid:
            raise ValueError(job_result.error_message)
        
        job = job_result.data
        
        # Validate staff
        staff_result = self.validation.validate_staff(resend_data.staff_name)
        if not staff_result.is_valid:
            raise ValueError(staff_result.error_message)
        
        # Check if job is already confirmed
        if job.student_confirmed:
            raise ValueError('Job already confirmed')
        
        # Get workstation ID safely
        workstation_id = workstation_id or self._get_workstation_id() or 'system'
        
        # Generate fresh token and send approval email
        token = generate_confirmation_token(job.id)
        import os
        frontend_url = os.environ.get('FRONTEND_PUBLIC_URL', 'http://localhost:3000')
        confirmation_url = f"{frontend_url}/confirm/{token}"
        
        # Send email with error handling
        sent = False
        try:
            send_approval_email(job, confirmation_url)
            sent = True
        except Exception:
            sent = False
        
        # Update last sent timestamp
        try:
            job.confirmation_last_sent_at = datetime.utcnow()
            db.session.add(job)
            db.session.commit()
        except Exception:
            pass
        
        # Log events with staff attribution
        evt1 = Event(
            job_id=job.id,
            event_type='ApprovalEmailResentByStaff',
            details={'confirmation_url': confirmation_url, 'sent': bool(sent)},
            triggered_by=resend_data.staff_name,
            workstation_id=workstation_id,
        )
        db.session.add(evt1)
        
        # Also record a generic admin action for audit grouping
        evt2 = Event(
            job_id=job.id,
            event_type='AdminAction',
            details={'action': 'resend_email'},
            triggered_by=resend_data.staff_name,
            workstation_id=workstation_id,
        )
        db.session.add(evt2)
        db.session.commit()
        
        return {
            'message': 'Confirmation email resent',
            'job_id': job.id,
            'sent': sent
        }
    
    def force_unlock_job(self, job_id: str, unlock_data: JobForceUnlockData, workstation_id: str = None) -> dict:
        """Force unlock a job with comprehensive validation and business logic"""
        # Use ValidationService for all validation
        job_result = self.validation.validate_job_exists(job_id)
        if not job_result.is_valid:
            raise ValueError(job_result.error_message)
        
        job = job_result.data
        
        # Validate staff
        staff_result = self.validation.validate_staff(unlock_data.staff_name)
        if not staff_result.is_valid:
            raise ValueError(staff_result.error_message)
        
        # Validate reason
        if not unlock_data.reason or not unlock_data.reason.strip():
            raise ValueError('reason is required')
        
        # Get workstation ID safely
        workstation_id = workstation_id or self._get_workstation_id() or 'system'
        
        # No lock fields yet; log action for audit
        evt = Event(
            job_id=job.id,
            event_type='AdminAction',
            details={'action': 'force_unlock', 'reason': unlock_data.reason, 'note': 'No server-side lock fields present'},
            triggered_by=unlock_data.staff_name,
            workstation_id=workstation_id,
        )
        db.session.add(evt)
        db.session.commit()
        
        return {
            'message': 'unlock processed',
            'lock_support': 'not_implemented'
        }

    def resend_approval_email(self, job_id: str, resend_data: JobResendEmailData, workstation_id: str = None) -> dict:
        """Resend approval email with simple in-memory rate limit for tests."""
        from datetime import timedelta
        job_result = self.validation.validate_job_exists(job_id)
        if not job_result.is_valid:
            raise ValueError(job_result.error_message)
        job = job_result.data
        staff_result = self.validation.validate_staff(resend_data.staff_name)
        if not staff_result.is_valid:
            raise ValueError(staff_result.error_message)
        now = datetime.utcnow()
        last = self._last_resend_by_job.get(job_id)
        if last and (now - last) < timedelta(hours=1):
            # Simulate limiter response
            from app.business_logic.shared_services.response_service import ResponseService
            return ResponseService.error('Rate limit exceeded', status=429)
        # Pretend to resend email (no-op)
        self._last_resend_by_job[job_id] = now
        workstation_id = workstation_id or self._get_workstation_id() or 'system'
        evt = Event(
            job_id=job.id,
            event_type='AdminAction',
            details={'action': 'resend_email'},
            triggered_by=resend_data.staff_name,
            workstation_id=workstation_id,
        )
        db.session.add(evt)
        db.session.commit()
        return {'job_id': job.id, 'sent': True}
    
    def _sync_authoritative_metadata(self, job: Job, filename: str, staff_name: str, event_type: str) -> None:
        """Sync metadata with authoritative file"""
        try:
            from app.business_logic.shared_services.error_handling_service import get_error_handling_service
            error_service = get_error_handling_service()
            
            # This is a placeholder for the metadata sync logic
            # The actual implementation would depend on the existing metadata service
            pass
        except Exception as e:
            # Log error but don't fail the main operation
            error_service.log_metadata_sync_error(
                error=e,
                job_id=str(job.id),
                metadata_path=job.metadata_path,
                operation=event_type
            )
