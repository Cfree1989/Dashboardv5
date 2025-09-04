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
from app.models.staff import Staff
from app.models.payment import Payment
from typing import Dict, Any, Optional, List
from app import db
from datetime import datetime, timedelta
from flask import g
import logging

logger = logging.getLogger(__name__)


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
    
    def check_duplicate_active_job(self, file_hash: str, student_email: str) -> Optional[str]:
        """Check for duplicate active job - centralizes duplicate detection"""
        active_statuses = ['UPLOADED', 'PENDING', 'READYTOPRINT']
        existing_record = db.session.query(Job.id).filter(
            Job.file_hash == file_hash,
            Job.student_email == student_email,
            Job.status.in_(active_statuses)
        ).first()
        return existing_record[0] if existing_record else None
    
    def generate_unique_short_id(self, base_id: str) -> str:
        """Generate a unique short ID - centralizes short ID generation"""
        for length in (6, 7, 8, 9, 10, 11, 12):
            candidate_short = base_id[:length]
            existing_short = db.session.query(Job.id).filter_by(short_id=candidate_short).first()
            if not existing_short:
                return candidate_short
        return base_id[:12]  # Fallback
    
    def get_jobs_by_status(self, statuses: list[str]) -> list[Job]:
        """Get jobs filtered by status list - centralizes status filtering"""
        return Job.query.filter(Job.status.in_(statuses)).all()
    
    def get_archivable_jobs(self, cutoff_date: datetime) -> list[Job]:
        """Get jobs eligible for archiving (PAIDPICKEDUP or REJECTED older than cutoff)"""
        return Job.query.filter(
            Job.status.in_(['PAIDPICKEDUP', 'REJECTED']),
            Job.created_at < cutoff_date
        ).all()
    
    def archive_job(self, job_id: str, staff_name: str, retention_days: int) -> Job:
        """Archive a single job - centralizes archiving logic"""
        try:
            job = self.get_job_by_id(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            # Validate staff
            is_valid, error_msg = self.validate_staff_exists_and_active(staff_name)
            if not is_valid:
                raise ValueError(error_msg)
            
            # Perform atomic file move
            from app.services.infrastructure.atomic_file_service import get_atomic_file_service
            atomic_service = get_atomic_file_service()
            success = atomic_service.atomic_move_authoritative(job, 'ARCHIVED')
            
            # Update job status (continue even if file move fails)
            job.status = 'ARCHIVED'
            job.last_updated_by = staff_name
            
            db.session.add(job)
            db.session.commit()
            
            # Log event
            self.log_event(job_id, 'JobArchived', {'retention_days': retention_days}, staff_name)
            
            return job
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to archive job: {e}")
            raise
    
    # --- Job Submission Operations ---
    
    def create_job_from_form_data(self, file, form_data, file_bytes, file_hash, display_name) -> Job:
        """Create job from form submission - matches submit.py pattern exactly"""
        from app import db
        from uuid import uuid4
        from pathlib import Path
        import json
        import os
        
        # Generate job ID 
        new_id = uuid4().hex
        short_id = self.generate_unique_short_id(new_id)
        
        # Prepare storage directory
        from app.services.infrastructure.file_configuration_service import get_file_configuration_service
        file_config = get_file_configuration_service()
        storage_dir = file_config.get_status_directory('UPLOADED')
        os.makedirs(storage_dir, exist_ok=True)
        
        # Generate file paths using submit.py's exact pattern
        ext = file.filename.rsplit('.', 1)[1].lower()
        student_name = form_data.get('student_name')
        if not student_name:
            first_name = form_data.get('student_first_name')
            last_name = form_data.get('student_last_name')
            student_name = f"{first_name or ''} {last_name or ''}".strip()
            
        candidate_name = display_name
        candidate_path = os.path.join(storage_dir, f"{candidate_name}.{ext}")
        
        # Save the file
        with open(candidate_path, 'wb') as f:
            f.write(file_bytes)
        
        # Create metadata
        metadata = {
            'student_name': student_name,
            'student_email': form_data.get('student_email'),
            'discipline': form_data.get('discipline'),
            'class_number': form_data.get('class_number'),
            'printer': form_data.get('printer'),
            'color': form_data.get('color'),
            'material': form_data.get('print_method'),
            'original_filename': file.filename,
            'file_hash': file_hash,
            'display_name': display_name,
            'authoritative_filename': f"{candidate_name}.{ext}",
            'file_path': str(Path(candidate_path).resolve()),
            'status': 'UPLOADED'
        }
        
        # Save metadata
        base_filename = candidate_name.rsplit('.', 1)[0] if '.' in candidate_name else candidate_name
        metadata_path = file_config.get_job_metadata_path(base_filename, 'UPLOADED')
        with open(metadata_path, 'w') as meta_f:
            json.dump(metadata, meta_f)
        
        # Create job record
        job = Job(
            id=new_id,
            short_id=short_id,
            student_name=student_name,
            student_email=form_data.get('student_email'),
            discipline=form_data.get('discipline'),
            class_number=form_data.get('class_number'),
            original_filename=file.filename,
            display_name=candidate_name,
            file_path=str(Path(candidate_path).resolve()),
            metadata_path=str(Path(metadata_path).resolve()),
            file_hash=file_hash,
            printer=form_data.get('printer'),
            color=form_data.get('color'),
            material=form_data.get('print_method')
        )
        
        # Save to database
        db.session.add(job)
        db.session.commit()
        
        # Log event
        self.log_event(job.id, 'JobCreated', {'original_filename': job.original_filename}, 'system')
        
        return job
    
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
    
    def confirm_job_by_token(self, token: str) -> Job:
        """Confirm job by token - simpler interface for submit.py"""
        from app import db
        from app.services.infrastructure.atomic_file_service import get_atomic_file_service
        from app.business_logic.shared_services import token_service
        
        # Verify token and get job_id
        try:
            job_id = token_service.verify_confirmation_token(token)
        except ValueError as ve:
            raise ve  # Re-raise with original message (expired, invalid, etc.)
        
        job = self.get_job_by_id(job_id)
        if not job:
            raise ValueError("Job not found")
        
        # Transition to READYTOPRINT + move file/metadata
        atomic_service = get_atomic_file_service()
        success = atomic_service.atomic_move_authoritative(job, 'READYTOPRINT')
        
        if not success:
            raise RuntimeError("File operation failed during confirmation")
        
        # Update job status
        job.status = 'READYTOPRINT'
        job.student_confirmed = True
        
        db.session.commit()
        
        # Sync metadata and log event
        from app.routes.jobs import _sync_authoritative_metadata
        from pathlib import Path
        _sync_authoritative_metadata(job, Path(job.file_path).name, None, 'StudentConfirmed')
        self.log_event(job.id, 'StudentConfirmed', {'status': job.status}, 'system')
        
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
    
    # ========================================
    # STAFF OPERATIONS
    # ========================================
    
    def get_staff_by_name(self, staff_name: str) -> Optional[Staff]:
        """Get staff member by name - replaces Staff.query.get()"""
        return Staff.query.get(staff_name)
    
    def validate_staff_exists_and_active(self, staff_name: str) -> tuple[bool, Optional[str]]:
        """Validate staff exists and is active - centralized validation"""
        if not staff_name:
            return False, "staff_name is required"
            
        staff = Staff.query.get(staff_name)
        if not staff or not staff.is_active:
            return False, "Invalid or inactive staff_name"
            
        return True, None
    
    # ========================================
    # EVENT LOGGING OPERATIONS
    # ========================================
    
    def log_event(self, job_id: str, event_type: str, details: Optional[Dict[str, Any]] = None, 
                 triggered_by: str = 'system', workstation_id: Optional[str] = None) -> Event:
        """Log event - replaces direct Event() instantiation"""
        if workstation_id is None:
            workstation_id = getattr(g, 'workstation_id', 'unknown')
            
        event = Event(
            job_id=job_id,
            event_type=event_type,
            details=details or {},
            triggered_by=triggered_by,
            workstation_id=workstation_id
        )
        
        db.session.add(event)
        db.session.commit()
        
        return event
    
    # ========================================
    # JOB STATUS TRANSITION OPERATIONS
    # ========================================
    
    def update_job_status(self, job_id: str, new_status: str, staff_name: str, 
                         event_type: Optional[str] = None, details: Optional[Dict[str, Any]] = None,
                         sync_metadata: bool = True) -> Job:
        """Update job status with event logging and optional metadata sync"""
        try:
            job = self.get_job_by_id(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            # Validate staff
            is_valid, error_msg = self.validate_staff_exists_and_active(staff_name)
            if not is_valid:
                raise ValueError(error_msg)
            
            # Update job
            old_status = job.status
            job.status = new_status
            job.last_updated_by = staff_name
            
            db.session.add(job)
            db.session.commit()
            
            # Log event
            if event_type:
                event_details = details or {}
                if old_status != new_status:
                    event_details.update({'from': old_status, 'to': new_status})
                
                self.log_event(job_id, event_type, event_details, staff_name)
            
            # Sync metadata if requested
            if sync_metadata:
                from pathlib import Path
                from app.routes.jobs import _sync_authoritative_metadata
                filename = Path(job.file_path).name if job.file_path else job.original_filename
                _sync_authoritative_metadata(job, filename, staff_name, event_type or 'StatusUpdate')
            
            return job
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update job status: {e}")
            raise
    
    def transition_job_with_file_move(self, job_id: str, new_status: str, staff_name: str,
                                    event_type: str, details: Optional[Dict[str, Any]] = None) -> Job:
        """Update job status with atomic file operations"""
        try:
            job = self.get_job_by_id(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            # Validate staff
            is_valid, error_msg = self.validate_staff_exists_and_active(staff_name)
            if not is_valid:
                raise ValueError(error_msg)
                
            # Perform atomic file move
            from app.services.infrastructure.atomic_file_service import get_atomic_file_service
            atomic_service = get_atomic_file_service()
            success = atomic_service.atomic_move_authoritative(job, new_status)
            
            if not success:
                raise RuntimeError(f"File operation failed during {new_status} status update")
            
            # Update job status
            old_status = job.status
            job.status = new_status
            job.last_updated_by = staff_name
            
            db.session.add(job)
            db.session.commit()
            
            # Log event
            event_details = details or {}
            event_details.update({'from': old_status, 'to': new_status})
            self.log_event(job_id, event_type, event_details, staff_name)
            
            # Sync metadata
            from pathlib import Path
            from app.routes.jobs import _sync_authoritative_metadata
            filename = Path(job.file_path).name if job.file_path else job.original_filename
            _sync_authoritative_metadata(job, filename, staff_name, event_type)
            
            return job
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to transition job with file move: {e}")
            raise
    
    # ========================================
    # PAYMENT OPERATIONS
    # ========================================
    
    def record_job_payment(self, job_id: str, grams: float, txn_no: str, 
                          picked_up_by: str, staff_name: str) -> tuple[Job, Payment]:
        """Record payment and transition to PAIDPICKEDUP"""
        try:
            job = self.get_job_by_id(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            if job.status != 'COMPLETED':
                raise ValueError('Job must be in COMPLETED to record payment')
                
            # Validate staff
            is_valid, error_msg = self.validate_staff_exists_and_active(staff_name)
            if not is_valid:
                raise ValueError(error_msg)
            
            # Calculate payment
            from decimal import Decimal, ROUND_HALF_UP
            material_rate = 0.20 if (job.material or '').lower() == 'resin' else 0.10
            raw_cost = grams * material_rate
            final_cost = max(raw_cost, 3.0)  # $3 minimum
            price_cents = int(Decimal(str(final_cost)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) * 100)
            
            # Create payment record
            payment = Payment(
                job_id=job.id,
                grams=grams,
                price_cents=price_cents,
                txn_no=txn_no,
                picked_up_by=picked_up_by,
                paid_by_staff=staff_name,
            )
            db.session.add(payment)
            
            # Transition to PAIDPICKEDUP with file move
            job = self.transition_job_with_file_move(
                job_id, 'PAIDPICKEDUP', staff_name, 'PaymentRecorded', 
                {'price_cents': price_cents}
            )
            
            return job, payment
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to record job payment: {e}")
            raise
    
    # ========================================
    # JOB NOTES OPERATIONS  
    # ========================================
    
    def update_job_notes(self, job_id: str, notes: str, staff_name: str) -> Job:
        """Update job notes with validation and event logging"""
        try:
            job = self.get_job_by_id(job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")
            
            # Validate staff
            is_valid, error_msg = self.validate_staff_exists_and_active(staff_name)
            if not is_valid:
                raise ValueError(error_msg)
            
            # Validate notes
            if not isinstance(notes, str):
                raise ValueError('notes must be a string')
            if len(notes) > 5000:
                raise ValueError('notes must be at most 5000 characters')
            
            # Update job
            job.notes = notes
            job.last_updated_by = staff_name
            
            db.session.add(job)
            db.session.commit()
            
            # Log event (don't store full notes in event log for privacy)
            self.log_event(job_id, 'NotesUpdated', {'notes_length': len(notes)}, staff_name)
            
            return job
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update job notes: {e}")
            raise
    
    # ========================================
    # JOB LOCKING OPERATIONS
    # ========================================
    
    # (Removed legacy duplicate lock/unlock/extend methods that accepted workstation_id instead of JobLockData)