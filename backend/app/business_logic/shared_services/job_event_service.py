from typing import Optional, Dict, Any
from pathlib import Path

# Import foundation services
from app.services.validation_service import ValidationService
from app.services.response_service import ResponseService

# Import models and services
from app.models.job import Job
from app.models.event import Event
from app import db

class JobEventService:
    """Service for managing job event logging patterns"""
    
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
    
    def log_event(self, job_id: str, event_type: str, details: Dict[str, Any], 
                  triggered_by: str, workstation_id: str = None) -> Event:
        """Log a job event with proper attribution"""
        workstation_id = workstation_id or self._get_workstation_id()
        
        evt = Event(
            job_id=job_id,
            event_type=event_type,
            details=details,
            triggered_by=triggered_by,
            workstation_id=workstation_id,
        )
        db.session.add(evt)
        db.session.commit()
        
        return evt
    
    def log_admin_action(self, job_id: str, action: str, details: Dict[str, Any], 
                        triggered_by: str, workstation_id: str = None) -> Event:
        """Log an admin action event with standardized format"""
        admin_details = {'action': action, **details}
        return self.log_event(job_id, 'AdminAction', admin_details, triggered_by, workstation_id)
    
    def sync_authoritative_metadata(self, job: Job, filename: str, staff_name: str, event_type: str) -> None:
        """Sync metadata with authoritative file"""
        try:
            from app.services.error_handling_service import get_error_handling_service
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
