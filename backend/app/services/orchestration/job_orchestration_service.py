"""
Job Orchestration Service
Emergency Service Decomposition - Day 3

Thin coordination layer that composes the business logic services.
Provides a unified interface for route handlers while delegating to appropriate services.
"""

# Import all business logic services
from app.business_logic.job_lifecycle import JobApprovalService, JobStatusService, JobTransitionService
from app.business_logic.admin_operations import JobAdminService, JobNotesService
from app.business_logic.shared_services import JobLockingService, JobEventService

# Import data classes for type hints
from app.business_logic.job_lifecycle.job_approval_service import JobApprovalData, JobRejectionData, JobReviewData
from app.business_logic.job_lifecycle.job_status_service import JobStatusTransitionData
from app.business_logic.job_lifecycle.job_submission_data import JobSubmissionData, JobConfirmationData, JobResendConfirmationData
from app.business_logic.admin_operations.job_admin_service import JobAdminStatusChangeData, JobDeleteData, JobResendEmailData, JobForceUnlockData
from app.business_logic.admin_operations.job_notes_service import JobNoteData, JobUpdateNotesData
from app.business_logic.shared_services.job_locking_service import JobLockData

# Import models for return types
from app.models.job import Job
from app.models.event import Event
from typing import Dict, Any, Optional


class JobOrchestrationService:
    """
    Orchestration service that coordinates all job lifecycle operations.
    
    This service provides a unified interface for route handlers while delegating
    to appropriate business logic services based on the operation type.
    
    The orchestration service maintains API compatibility with existing routes
    while providing clean separation of concerns through service composition.
    """
    
    def __init__(self):
        """Initialize all business logic services"""
        # Core job lifecycle services
        self.approval = JobApprovalService()
        self.status = JobStatusService()
        self.transition = JobTransitionService()
        
        # Admin operations services
        self.admin = JobAdminService()
        self.notes = JobNotesService()
        
        # Shared services
        self.locking = JobLockingService()
        self.events = JobEventService()
    
    # --- Job Approval Operations ---
    
    def approve_job(self, job_id: str, approval_data: JobApprovalData, workstation_id: str = None) -> Job:
        """Approve a job - delegates to JobApprovalService"""
        return self.approval.approve_job(job_id, approval_data, workstation_id)
    
    def reject_job(self, job_id: str, rejection_data: JobRejectionData, workstation_id: str = None) -> Job:
        """Reject a job - delegates to JobApprovalService"""
        return self.approval.reject_job(job_id, rejection_data, workstation_id)
    
    def review_job(self, job_id: str, review_data: JobReviewData, workstation_id: str = None) -> Job:
        """Review a job - delegates to JobApprovalService"""
        return self.approval.review_job(job_id, review_data, workstation_id)
    
    # --- Job Status Operations ---
    
    def mark_printing(self, job_id: str, transition_data: JobStatusTransitionData) -> Job:
        """Mark job as printing - delegates to JobStatusService"""
        return self.status.mark_printing(job_id, transition_data)
    
    def mark_complete(self, job_id: str, transition_data: JobStatusTransitionData) -> Job:
        """Mark job as complete - delegates to JobStatusService"""
        return self.status.mark_complete(job_id, transition_data)
    
    def mark_picked_up(self, job_id: str, transition_data: JobStatusTransitionData) -> Job:
        """Mark job as picked up - delegates to JobStatusService"""
        return self.status.mark_picked_up(job_id, transition_data)
    
    def mark_failed(self, job_id: str, transition_data: JobStatusTransitionData) -> Job:
        """Mark job as failed - delegates to JobStatusService"""
        return self.status.mark_failed(job_id, transition_data)
    
    def admin_force_confirm(self, job_id: str, transition_data: JobStatusTransitionData) -> Job:
        """Admin force confirm job - delegates to JobStatusService"""
        return self.status.admin_force_confirm(job_id, transition_data)
    
    def revert_to_printing(self, job_id: str, transition_data: JobStatusTransitionData) -> Job:
        """Revert job to printing - delegates to JobStatusService"""
        return self.status.revert_to_printing(job_id, transition_data)
    
    def revert_to_completed(self, job_id: str, transition_data: JobStatusTransitionData) -> Job:
        """Revert job to completed - delegates to JobStatusService"""
        return self.status.revert_to_completed(job_id, transition_data)
    
    # --- Generic Status Transitions ---
    
    def transition_status(self, job_id: str, new_status: str, staff_name: str, 
                         workstation_id: str = None, **kwargs) -> Job:
        """Generic status transition - delegates to JobTransitionService"""
        return self.transition.transition_status(job_id, new_status, staff_name, workstation_id, **kwargs)
    
    # --- Admin Operations ---
    
    def admin_change_status(self, job_id: str, status_change_data: JobAdminStatusChangeData, 
                           workstation_id: str = None) -> Job:
        """Admin change job status - delegates to JobAdminService"""
        return self.admin.admin_change_status(job_id, status_change_data, workstation_id)
    
    def delete_job(self, job_id: str, delete_data: JobDeleteData = None, 
                   workstation_id: str = None) -> Job:
        """Soft delete a job - delegates to JobAdminService"""
        return self.admin.delete_job(job_id, delete_data, workstation_id)
    
    def hard_delete_job(self, job_id: str, delete_data: JobDeleteData, 
                        workstation_id: str = None) -> Dict[str, Any]:
        """Hard delete a job - delegates to JobAdminService"""
        return self.admin.hard_delete_job(job_id, delete_data, workstation_id)
    
    def resend_approval_email(self, job_id: str, resend_data: JobResendEmailData, 
                             workstation_id: str = None) -> Dict[str, Any]:
        """Resend approval email - delegates to JobAdminService"""
        return self.admin.resend_approval_email(job_id, resend_data, workstation_id)
    
    def force_unlock_job(self, job_id: str, unlock_data: JobForceUnlockData, 
                         workstation_id: str = None) -> Dict[str, Any]:
        """Force unlock a job - delegates to JobAdminService"""
        return self.admin.force_unlock_job(job_id, unlock_data, workstation_id)
    
    # --- Notes Operations ---
    
    def append_note(self, job_id: str, note_data: JobNoteData, 
                    workstation_id: str = None) -> Job:
        """Append a note to a job - delegates to JobNotesService"""
        return self.notes.append_note(job_id, note_data, workstation_id)
    
    def update_notes(self, job_id: str, notes_data: JobUpdateNotesData, 
                     workstation_id: str = None) -> Job:
        """Update job notes - delegates to JobNotesService"""
        return self.notes.update_notes(job_id, notes_data, workstation_id)
    
    # --- Locking Operations ---
    
    def lock_job(self, job_id: str, lock_data: JobLockData) -> Job:
        """Lock a job - delegates to JobLockingService"""
        return self.locking.lock_job(job_id, lock_data)
    
    def unlock_job(self, job_id: str, lock_data: JobLockData) -> Job:
        """Unlock a job - delegates to JobLockingService"""
        return self.locking.unlock_job(job_id, lock_data)
    
    def extend_job_lock(self, job_id: str, lock_data: JobLockData) -> Job:
        """Extend a job lock - delegates to JobLockingService"""
        return self.locking.extend_job_lock(job_id, lock_data)
    
    # --- Event Logging Operations ---
    
    def log_event(self, job_id: str, event_type: str, details: Dict[str, Any], 
                  triggered_by: str, workstation_id: str = None) -> Event:
        """Log a job event - delegates to JobEventService"""
        return self.events.log_event(job_id, event_type, details, triggered_by, workstation_id)
    
    def log_admin_action(self, job_id: str, action: str, details: Dict[str, Any], 
                         triggered_by: str, workstation_id: str = None) -> Event:
        """Log an admin action - delegates to JobEventService"""
        return self.events.log_admin_action(job_id, action, details, triggered_by, workstation_id)
    
    def sync_authoritative_metadata(self, job: Job, filename: str, staff_name: str, 
                                   event_type: str) -> None:
        """Sync metadata - delegates to JobEventService"""
        return self.events.sync_authoritative_metadata(job, filename, staff_name, event_type)
    
    # --- Query Operations ---
    
    def get_job_by_id(self, job_id: str) -> Optional[Job]:
        """Get a job by ID - centralizes Job.query.get() operations"""
        return Job.query.get(job_id)
    
    def get_all_jobs(self) -> list[Job]:
        """Get all jobs - centralizes Job.query.all() operations"""
        return Job.query.all()
    
    def get_job_events(self, job_id: str) -> list[Event]:
        """Get all events for a job - centralizes Event.query operations"""
        return Event.query.filter(Event.job_id == job_id).order_by(Event.timestamp).all()
    
    # --- Job Submission Operations ---
    
    def create_job_with_upload(self, submission_data: JobSubmissionData) -> Job:
        """Create a new job with file upload - centralizes job creation logic"""
        from app import db
        from uuid import uuid4
        from pathlib import Path
        from datetime import datetime
        import json
        
        # Generate IDs
        new_id = str(uuid4())
        
        # Generate unique short_id  
        short_id = None
        for attempt in range(100):
            candidate_short = str(uuid4())[:8]
            existing_short = db.session.query(Job.id).filter_by(short_id=candidate_short).first()
            if not existing_short:
                short_id = candidate_short
                break
        
        if not short_id:
            raise ValueError("Could not generate unique short_id after 100 attempts")
        
        # Setup file paths
        from app.services.infrastructure.file_configuration_service import get_file_configuration_service
        file_config = get_file_configuration_service()
        storage_root = file_config.get_storage_root()
        upload_dir = storage_root / "Uploaded"
        upload_dir.mkdir(exist_ok=True)
        
        # Generate file paths
        candidate_name = submission_data.display_name
        candidate_path = upload_dir / f"{candidate_name}_{submission_data.color}_{short_id}.{submission_data.file.filename.rsplit('.', 1)[1]}"
        metadata_path = upload_dir / f"{candidate_name}_{submission_data.color}_{short_id}_metadata.json"
        
        # Save file
        submission_data.file.save(candidate_path)
        
        # Save metadata
        with open(metadata_path, 'w') as meta_f:
            json.dump(submission_data.metadata, meta_f)
        
        # Create job record
        job = Job(
            id=new_id,
            short_id=short_id,
            student_name=submission_data.student_name,
            student_email=submission_data.student_email,
            discipline=submission_data.discipline,
            class_number=submission_data.class_number,
            original_filename=submission_data.file.filename,
            display_name=submission_data.display_name,
            file_path=str(Path(candidate_path).resolve()),
            metadata_path=str(Path(metadata_path).resolve()),
            file_hash=submission_data.file_hash,
            printer=submission_data.printer,
            color=submission_data.color,
            material=submission_data.material
        )
        
        # Save to database
        db.session.add(job)
        db.session.commit()
        
        # Log event
        self.log_event(job.id, 'JobCreated', {'original_filename': job.original_filename}, 'system')
        
        return job
    
    def confirm_job_submission(self, job_id: str, confirmation_data: JobConfirmationData) -> Job:
        """Confirm job submission and move files - centralizes confirmation logic"""
        from app import db
        from app.services.infrastructure.atomic_file_service import get_atomic_file_service
        from app.business_logic.shared_services import token_service
        
        job = self.get_job_by_id(job_id)
        if not job:
            raise ValueError("Job not found")
        
        # Verify token (allow expired for confirmation)
        token_valid, _ = token_service.verify_confirmation_token(confirmation_data.token)
        if not token_valid:
            raise ValueError("Invalid confirmation token")
        
        # Transition to READYTOPRINT + move file/metadata
        atomic_service = get_atomic_file_service()
        success = atomic_service.move_job_files(job.id, 'UPLOADED', 'READYTOPRINT')
        
        if not success:
            raise RuntimeError("File operation failed during confirmation")
        
        # Update job status
        job.status = 'READYTOPRINT'
        job.student_confirmed = True
        job.student_confirmed_at = db.func.now()
        
        db.session.commit()
        
        # Sync metadata and log event
        from app.routes.jobs import _sync_authoritative_metadata
        _sync_authoritative_metadata(job, job.original_filename, 'system', 'StudentConfirmed')
        self.log_event(job.id, 'StudentConfirmed', {'status': job.status}, 'system')
        
        return job
    
    def resend_confirmation_email(self, resend_data: JobResendConfirmationData) -> Job:
        """Resend confirmation email - centralizes resend logic"""
        from app import db
        from app.business_logic.shared_services import token_service, email_service
        from datetime import datetime
        
        # Resolve job_id from token if provided
        job_id = resend_data.job_id
        if resend_data.token and not job_id:
            try:
                job_id = token_service.get_job_id_from_token(resend_data.token)
            except Exception:
                raise ValueError("Invalid token")
        
        job = self.get_job_by_id(job_id)
        if not job:
            raise ValueError("Job not found")
        
        if job.student_confirmed:
            raise ValueError("Job already confirmed")
        
        # Generate fresh token and send email
        confirmation_token = token_service.generate_confirmation_token(job.id)
        email_result = email_service.send_confirmation_email(
            job.student_email,
            job.student_name,
            job.display_name,
            job.short_id,
            confirmation_token
        )
        
        if not email_result.success:
            raise RuntimeError(f"Failed to send confirmation email: {email_result.error}")
        
        # Update last sent timestamp
        job.confirmation_last_sent_at = datetime.utcnow()
        db.session.commit()
        
        return job