from typing import Optional
from pathlib import Path

# Import foundation services
from app.business_logic.shared_services.validation_service import ValidationService
from app.business_logic.shared_services.response_service import ResponseService

# Import models and services
from app.models.job import Job
from app.models.event import Event
from app.services.infrastructure.atomic_file_service import get_atomic_file_service
# Import moved to method level to avoid circular imports
from app import db

class JobTransitionService:
    """Service for managing job status transitions and validation"""
    
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
    
    def transition_status(self, job_id: str, new_status: str, staff_name: str, 
                         workstation_id: str = None, **kwargs) -> Job:
        """Transition job to a new status with validation and business logic"""
        # Use ValidationService for all validation
        job_result = self.validation.validate_job_exists(job_id)
        if not job_result.is_valid:
            raise ValueError(job_result.error_message)
        
        job = job_result.data
        
        # Validate status transition
        transition_result = self.validation.validate_status_transition(job.status, new_status)
        if not transition_result.is_valid:
            raise ValueError(transition_result.error_message)
        
        staff_result = self.validation.validate_staff(staff_name)
        if not staff_result.is_valid:
            raise ValueError(staff_result.error_message)
        
        # Store previous status for event logging
        previous_status = job.status
        
        # Update job
        job.status = new_status
        job.last_updated_by = staff_name
        # Auto flag rules for unreviewed when crossing Uploaded boundary
        try:
            if hasattr(job, 'is_unreviewed'):
                if new_status == 'UPLOADED':
                    job.is_unreviewed = True
                elif previous_status == 'UPLOADED' and new_status != 'UPLOADED':
                    job.is_unreviewed = False
        except Exception:
            pass
        
        # Handle status-specific logic
        if new_status in ['PRINTING', 'COMPLETED', 'PAIDPICKEDUP']:
            atomic_service = get_atomic_file_service()
            success = atomic_service.atomic_move_authoritative(job, new_status)
            if not success:
                raise RuntimeError(f'File operation failed during status transition to {new_status}')
        
        # Save job changes
        db.session.add(job)
        db.session.commit()
        
        # Log event
        workstation_id = workstation_id or self._get_workstation_id()
        evt = Event(
            job_id=job.id,
            event_type=f'StatusChangedTo{new_status}',
            details={'from': previous_status, 'to': new_status},
            triggered_by=staff_name,
            workstation_id=workstation_id,
        )
        db.session.add(evt)
        db.session.commit()
        
        # Handle status-specific side effects
        if new_status in ['COMPLETED', 'PAIDPICKEDUP']:
            self._sync_authoritative_metadata(job, Path(job.file_path).name, staff_name, 
                                            f'StatusChangedTo{new_status}')
        
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
