from typing import Optional
from datetime import datetime
from pathlib import Path

# Import foundation services
from app.business_logic.shared_services.validation_service import ValidationService
from app.business_logic.shared_services.response_service import ResponseService

# Import models and services
from app.models.job import Job
from app.models.event import Event
from app.business_logic.shared_services.email_service import send_completion_email
from app.services.infrastructure.atomic_file_service import get_atomic_file_service
# Import moved to method level to avoid circular imports
from app import db

class JobStatusTransitionData:
    """Data class for job status transition parameters"""
    def __init__(self, staff_name: str, workstation_id: Optional[str] = None, **kwargs):
        self.staff_name = staff_name
        self.workstation_id = workstation_id
        self.additional_data = kwargs

class JobStatusService:
    """Service for managing job status transitions and lifecycle operations"""
    
    def __init__(self, validation_service=None, response_service=None):
        """Use dependency injection for testability"""
        self.validation = validation_service or ValidationService
        self.response = response_service or ResponseService
    
    def _get_workstation_id(self) -> Optional[str]:
        """Get workstation ID from request context if available"""
        try:
            from flask import request
            return request.headers.get('X-Workstation-ID')
        except RuntimeError:
            # Not in request context (e.g., during testing)
            return None
    
    def mark_printing(self, job_id: str, transition_data: JobStatusTransitionData) -> Job:
        """Mark job as printing (READYTOPRINT -> PRINTING)"""
        job_result = self.validation.validate_job_exists(job_id)
        if not job_result.is_valid:
            raise ValueError(job_result.error_message)
        
        job = job_result.data
        if job.status != 'READYTOPRINT':
            raise ValueError('Job must be in READYTOPRINT to mark printing')
        
        staff_result = self.validation.validate_staff(transition_data.staff_name)
        if not staff_result.is_valid:
            raise ValueError(staff_result.error_message)
        
        # Update job
        job.status = 'PRINTING'
        job.last_updated_by = transition_data.staff_name
        
        # Move file/metadata to Printing
        atomic_service = get_atomic_file_service()
        success = atomic_service.atomic_move_authoritative(job, 'PRINTING')
        if not success:
            return ResponseService.error('File operation failed during printing status update')
        db.session.add(job)
        db.session.commit()
        
        # Log event
        workstation_id = transition_data.workstation_id or self._get_workstation_id() or 'unknown'
        evt = Event(
            job_id=job.id, 
            event_type='JobMarkedPrinting', 
            details={}, 
            triggered_by=transition_data.staff_name, 
            workstation_id=workstation_id
        )
        db.session.add(evt)
        db.session.commit()
        
        # Sync metadata
        self._sync_authoritative_metadata(job, Path(job.file_path).name, transition_data.staff_name, 'JobMarkedPrinting')
        
        return job
    
    def mark_complete(self, job_id: str, transition_data: JobStatusTransitionData) -> Job:
        """Mark job as complete (PRINTING -> COMPLETED)"""
        job_result = self.validation.validate_job_exists(job_id)
        if not job_result.is_valid:
            raise ValueError(job_result.error_message)
        
        job = job_result.data
        if job.status != 'PRINTING':
            raise ValueError('Job must be in PRINTING to mark complete')
        
        staff_result = self.validation.validate_staff(transition_data.staff_name)
        if not staff_result.is_valid:
            raise ValueError(staff_result.error_message)
        
        # Update job
        job.status = 'COMPLETED'
        job.last_updated_by = transition_data.staff_name
        
        # Move file/metadata to Completed
        atomic_service = get_atomic_file_service()
        success = atomic_service.atomic_move_authoritative(job, 'COMPLETED')
        if not success:
            return ResponseService.error('File operation failed during completion status update')
        db.session.add(job)
        db.session.commit()
        
        # Log event
        workstation_id = transition_data.workstation_id or self._get_workstation_id() or 'unknown'
        evt = Event(
            job_id=job.id, 
            event_type='JobMarkedComplete', 
            details={}, 
            triggered_by=transition_data.staff_name, 
            workstation_id=workstation_id
        )
        db.session.add(evt)
        db.session.commit()
        
        # Attempt completion email (best-effort)
        try:
            send_completion_email(job)
            email_evt = Event(
                job_id=job.id, 
                event_type='CompletionEmailSent', 
                details={}, 
                triggered_by=transition_data.staff_name, 
                workstation_id=workstation_id
            )
            db.session.add(email_evt)
            db.session.commit()
        except Exception:
            pass  # Best-effort email sending
        
        # Sync metadata
        self._sync_authoritative_metadata(job, Path(job.file_path).name, transition_data.staff_name, 'JobMarkedComplete')
        
        return job
    
    def mark_picked_up(self, job_id: str, transition_data: JobStatusTransitionData) -> Job:
        """Mark job as picked up (COMPLETED -> PAIDPICKEDUP)"""
        job_result = self.validation.validate_job_exists(job_id)
        if not job_result.is_valid:
            raise ValueError(job_result.error_message)
        
        job = job_result.data
        if job.status != 'COMPLETED':
            raise ValueError('Job must be in COMPLETED to mark picked up')
        
        staff_result = self.validation.validate_staff(transition_data.staff_name)
        if not staff_result.is_valid:
            raise ValueError(staff_result.error_message)
        
        # Update job
        job.status = 'PAIDPICKEDUP'
        job.last_updated_by = transition_data.staff_name
        
        # Move file/metadata to PaidPickedUp
        atomic_service = get_atomic_file_service()
        success = atomic_service.atomic_move_authoritative(job, 'PAIDPICKEDUP')
        if not success:
            return ResponseService.error('File operation failed during pickup status update')
        db.session.add(job)
        db.session.commit()
        
        # Log event
        workstation_id = transition_data.workstation_id or self._get_workstation_id() or 'unknown'
        evt = Event(
            job_id=job.id, 
            event_type='JobMarkedPickedUp', 
            details={}, 
            triggered_by=transition_data.staff_name, 
            workstation_id=workstation_id
        )
        db.session.add(evt)
        db.session.commit()
        
        # Sync metadata
        self._sync_authoritative_metadata(job, Path(job.file_path).name, transition_data.staff_name, 'JobMarkedPickedUp')
        
        return job
    
    def mark_failed(self, job_id: str, transition_data: JobStatusTransitionData) -> Job:
        """Mark job as failed (PRINTING -> READYTOPRINT)"""
        job_result = self.validation.validate_job_exists(job_id)
        if not job_result.is_valid:
            raise ValueError(job_result.error_message)
        
        job = job_result.data
        if job.status != 'PRINTING':
            raise ValueError('Job must be in PRINTING to mark failed')
        
        staff_result = self.validation.validate_staff(transition_data.staff_name)
        if not staff_result.is_valid:
            raise ValueError(staff_result.error_message)
        
        reason = transition_data.additional_data.get('reason', '')
        if not reason:
            raise ValueError('reason is required for marking job as failed')
        
        # Move back to READYTOPRINT
        job.status = 'READYTOPRINT'
        job.last_updated_by = transition_data.staff_name
        atomic_service = get_atomic_file_service()
        success = atomic_service.atomic_move_authoritative(job, 'READYTOPRINT')
        if not success:
            return ResponseService.error('File operation failed during failure marking')
        db.session.add(job)
        db.session.commit()
        
        # Log failure and admin action
        workstation_id = transition_data.workstation_id or self._get_workstation_id() or 'unknown'
        evt = Event(
            job_id=job.id, 
            event_type='PrintFailed', 
            details={'reason': reason}, 
            triggered_by=transition_data.staff_name, 
            workstation_id=workstation_id
        )
        db.session.add(evt)
        db.session.commit()
        
        evt2 = Event(
            job_id=job.id, 
            event_type='AdminAction', 
            details={'action': 'mark_failed', 'reason': reason}, 
            triggered_by=transition_data.staff_name, 
            workstation_id=workstation_id
        )
        db.session.add(evt2)
        db.session.commit()
        
        return job
    
    def admin_force_confirm(self, job_id: str, transition_data: JobStatusTransitionData) -> Job:
        """Admin force confirm job (PENDING -> READYTOPRINT)"""
        job_result = self.validation.validate_job_exists(job_id)
        if not job_result.is_valid:
            raise ValueError(job_result.error_message)
        
        job = job_result.data
        if job.status != 'PENDING':
            raise ValueError('Job must be in PENDING to force confirm')
        
        staff_result = self.validation.validate_staff(transition_data.staff_name)
        if not staff_result.is_valid:
            raise ValueError(staff_result.error_message)
        
        reason = transition_data.additional_data.get('reason', '')
        if not reason:
            raise ValueError('reason is required for admin force confirm')
        
        # Transition to READYTOPRINT and move files
        job.status = 'READYTOPRINT'
        job.last_updated_by = transition_data.staff_name
        atomic_service = get_atomic_file_service()
        success = atomic_service.atomic_move_authoritative(job, 'READYTOPRINT')
        if not success:
            return ResponseService.error('File operation failed during admin force confirm')
        db.session.add(job)
        db.session.commit()
        
        # Log specific and admin events
        workstation_id = transition_data.workstation_id or self._get_workstation_id() or 'system'
        evt1 = Event(
            job_id=job.id, 
            event_type='AdminForceConfirm', 
            details={'reason': reason}, 
            triggered_by=transition_data.staff_name, 
            workstation_id=workstation_id
        )
        db.session.add(evt1)
        db.session.commit()
        
        evt2 = Event(
            job_id=job.id, 
            event_type='AdminAction', 
            details={'action': 'force_confirm', 'reason': reason}, 
            triggered_by=transition_data.staff_name, 
            workstation_id=workstation_id
        )
        db.session.add(evt2)
        db.session.commit()
        
        return job
    
    def revert_to_printing(self, job_id: str, transition_data: JobStatusTransitionData) -> Job:
        """Revert job to printing (COMPLETED -> PRINTING)"""
        job_result = self.validation.validate_job_exists(job_id)
        if not job_result.is_valid:
            raise ValueError(job_result.error_message)
        
        job = job_result.data
        if job.status != 'COMPLETED':
            raise ValueError('Job must be in COMPLETED to revert to PRINTING')
        
        staff_result = self.validation.validate_staff(transition_data.staff_name)
        if not staff_result.is_valid:
            raise ValueError(staff_result.error_message)
        
        # Store previous status for event logging
        before = job.status
        
        # Update job
        job.status = 'PRINTING'
        job.last_updated_by = transition_data.staff_name
        atomic_service = get_atomic_file_service()
        success = atomic_service.atomic_move_authoritative(job, 'PRINTING')
        if not success:
            return ResponseService.error('File operation failed during revert to printing')
        db.session.add(job)
        db.session.commit()
        
        # Log event
        workstation_id = transition_data.workstation_id or self._get_workstation_id() or 'system'
        evt = Event(
            job_id=job.id, 
            event_type='JobRevertedToPrinting', 
            details={'from': before, 'to': 'PRINTING'}, 
            triggered_by=transition_data.staff_name, 
            workstation_id=workstation_id
        )
        db.session.add(evt)
        db.session.commit()
        
        # Sync metadata
        self._sync_authoritative_metadata(job, Path(job.file_path).name, transition_data.staff_name, 'JobRevertedToPrinting')
        
        return job
    
    def revert_to_completed(self, job_id: str, transition_data: JobStatusTransitionData) -> Job:
        """Revert job to completed (PAIDPICKEDUP -> COMPLETED)"""
        job_result = self.validation.validate_job_exists(job_id)
        if not job_result.is_valid:
            raise ValueError(job_result.error_message)
        
        job = job_result.data
        if job.status != 'PAIDPICKEDUP':
            raise ValueError('Job must be in PAIDPICKEDUP to revert to COMPLETED')
        
        staff_result = self.validation.validate_staff(transition_data.staff_name)
        if not staff_result.is_valid:
            raise ValueError(staff_result.error_message)
        
        # Store previous status for event logging
        before = job.status
        
        # Update job
        job.status = 'COMPLETED'
        job.last_updated_by = transition_data.staff_name
        atomic_service = get_atomic_file_service()
        success = atomic_service.atomic_move_authoritative(job, 'COMPLETED')
        if not success:
            return ResponseService.error('File operation failed during revert to completed')
        db.session.add(job)
        db.session.commit()
        
        # Log event
        workstation_id = transition_data.workstation_id or self._get_workstation_id() or 'system'
        evt = Event(
            job_id=job.id, 
            event_type='JobRevertedToCompleted', 
            details={'from': before, 'to': 'COMPLETED'}, 
            triggered_by=transition_data.staff_name, 
            workstation_id=workstation_id
        )
        db.session.add(evt)
        db.session.commit()
        
        # Sync metadata
        self._sync_authoritative_metadata(job, Path(job.file_path).name, transition_data.staff_name, 'JobRevertedToCompleted')
        
        return job
    
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
