from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import os

# Import foundation services
from app.business_logic.shared_services.validation_service import ValidationService
from app.services.response_service import ResponseService

# Import models and services
from app.models.job import Job
from app.models.staff import Staff
from app.models.event import Event
from app.services.token_service import generate_confirmation_token
from app.services.email_service import send_approval_email, send_rejection_email, send_completion_email
from app.services.file_service import move_authoritative
from app.services.catalog_service import CatalogService
from app import db

class JobApprovalData:
    """Data class for job approval parameters"""
    def __init__(self, staff_name: str, weight_g: float, time_hours: float, 
                 authoritative_filename: Optional[str] = None, 
                 printer_override: Optional[str] = None):
        self.staff_name = staff_name
        self.weight_g = weight_g
        self.time_hours = time_hours
        self.authoritative_filename = authoritative_filename
        self.printer_override = printer_override

class JobRejectionData:
    """Data class for job rejection parameters"""
    def __init__(self, staff_name: str, reasons: List[str], custom_reason: Optional[str] = None):
        self.staff_name = staff_name
        self.reasons = reasons
        self.custom_reason = custom_reason

class JobReviewData:
    """Data class for job review parameters"""
    def __init__(self, staff_name: str, reviewed: bool):
        self.staff_name = staff_name
        self.reviewed = reviewed

class JobNoteData:
    """Data class for job note parameters"""
    def __init__(self, staff_name: str, text: str):
        self.staff_name = staff_name
        self.text = text

class JobUpdateNotesData:
    """Data class for updating notes parameters"""
    def __init__(self, staff_name: str, notes: str):
        self.staff_name = staff_name
        self.notes = notes

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

class JobLockData:
    """Data class for job lock parameters"""
    def __init__(self, workstation_id: str, lock_duration_minutes: int = 5):
        self.workstation_id = workstation_id
        self.lock_duration_minutes = lock_duration_minutes

class JobStatusTransitionData:
    """Data class for job status transition parameters"""
    def __init__(self, staff_name: str, workstation_id: Optional[str] = None, **kwargs):
        self.staff_name = staff_name
        self.workstation_id = workstation_id
        self.additional_data = kwargs

class JobLifecycleService:
    """Service for managing job lifecycle operations including approval, rejection, and status transitions"""
    
    def __init__(self, validation_service=None, response_service=None):
        """Use dependency injection for testability"""
        self.validation = validation_service or ValidationService
        self.response = response_service or ResponseService
    
    def _get_workstation_id(self) -> Optional[str]:
        """Get workstation ID safely for Flask context compatibility"""
        try:
            from flask import g
            return getattr(g, 'workstation_id', None)
        except (ImportError, RuntimeError):
            # Outside Flask context (e.g., in tests)
            return None
    
    def approve_job(self, job_id: str, approval_data: JobApprovalData, workstation_id: str = None) -> Job:
        """Approve a job with comprehensive validation and business logic"""
        # Use ValidationService for all validation
        job_result = self.validation.validate_job_exists(job_id)
        if not job_result.is_valid:
            raise ValueError(job_result.error_message)
        
        job = job_result.data
        if job.status != 'UPLOADED':
            raise ValueError('Job cannot be approved in its current status')
        
        staff_result = self.validation.validate_staff(approval_data.staff_name)
        if not staff_result.is_valid:
            raise ValueError(staff_result.error_message)
        
        # Validate numeric inputs
        if approval_data.weight_g <= 0 or approval_data.time_hours <= 0:
            raise ValueError('weight_g and time_hours must be greater than 0')
        
        # Calculate cost using existing logic
        cost = self._calculate_job_cost(job.material, approval_data.weight_g)
        
        # Update job with Flask context safety
        workstation_id = workstation_id or self._get_workstation_id()
        job.weight_g = approval_data.weight_g
        job.time_hours = approval_data.time_hours
        job.cost_usd = cost
        job.last_updated_by = approval_data.staff_name
        job.staff_viewed_at = datetime.utcnow()
        
        # Handle printer override if provided
        if approval_data.printer_override:
            self._apply_printer_override(job, approval_data.printer_override)
        
        # Handle authoritative filename if provided
        if approval_data.authoritative_filename:
            self._apply_authoritative_filename(job, approval_data.authoritative_filename)
        
        job.status = 'PENDING'
        
        # Save job changes
        db.session.add(job)
        db.session.commit()
        
        # Generate confirmation token and send email
        token = generate_confirmation_token(job.id)
        frontend_url = os.environ.get('FRONTEND_PUBLIC_URL', 'http://localhost:3000')
        confirmation_url = f"{frontend_url}/confirm/{token}"
        send_approval_email(job, confirmation_url)
        
        # Log events with proper attribution
        self._log_approval_events(job, approval_data, confirmation_url, workstation_id)
        
        # Sync metadata with chosen authoritative file
        self._sync_authoritative_metadata(job, approval_data.authoritative_filename or job.display_name, 
                                        approval_data.staff_name, 'StaffApproved')
        
        return job
    
    def reject_job(self, job_id: str, rejection_data: JobRejectionData, workstation_id: str = None) -> Job:
        """Reject a job with comprehensive validation and business logic"""
        # Use ValidationService for all validation
        job_result = self.validation.validate_job_exists(job_id)
        if not job_result.is_valid:
            raise ValueError(job_result.error_message)
        
        job = job_result.data
        if job.status != 'UPLOADED':
            raise ValueError('Job cannot be rejected in its current status')
        
        staff_result = self.validation.validate_staff(rejection_data.staff_name)
        if not staff_result.is_valid:
            raise ValueError(staff_result.error_message)
        
        # Normalize reasons
        reasons = [str(r) for r in rejection_data.reasons if str(r).strip()]
        if rejection_data.custom_reason:
            reasons.append(rejection_data.custom_reason)
        if not reasons:
            raise ValueError('At least one reason or a custom_reason is required')
        
        # Update job
        job.status = 'REJECTED'
        job.reject_reasons = reasons
        job.last_updated_by = rejection_data.staff_name
        
        # Save job changes
        db.session.add(job)
        db.session.commit()
        
        # Log event
        workstation_id = workstation_id or self._get_workstation_id()
        evt = Event(
            job_id=job.id,
            event_type='StaffRejected',
            details={'reasons': reasons},
            triggered_by=rejection_data.staff_name,
            workstation_id=workstation_id,
        )
        db.session.add(evt)
        db.session.commit()
        
        # Attempt rejection email (best-effort)
        try:
            send_rejection_email(job)
            email_evt = Event(
                job_id=job.id, 
                event_type='RejectionEmailSent', 
                details={'reasons': reasons}, 
                triggered_by=rejection_data.staff_name, 
                workstation_id=workstation_id
            )
            db.session.add(email_evt)
            db.session.commit()
        except Exception:
            pass  # Best-effort email sending
        
        return job
    
    def review_job(self, job_id: str, review_data: JobReviewData, workstation_id: str = None) -> Job:
        """Review a job with comprehensive validation and business logic"""
        # Use ValidationService for all validation
        job_result = self.validation.validate_job_exists(job_id)
        if not job_result.is_valid:
            raise ValueError(job_result.error_message)
        
        job = job_result.data
        if job.status != 'UPLOADED':
            raise ValueError('Job review state can only be changed in UPLOADED status')
        
        staff_result = self.validation.validate_staff(review_data.staff_name)
        if not staff_result.is_valid:
            raise ValueError(staff_result.error_message)
        
        # Apply state change
        if review_data.reviewed:
            job.staff_viewed_at = datetime.utcnow()
            event_type = 'JobReviewed'
        else:
            job.staff_viewed_at = None
            event_type = 'JobReviewCleared'
        
        job.last_updated_by = review_data.staff_name
        db.session.add(job)
        db.session.commit()
        
        # Log event with attribution
        workstation_id = workstation_id or self._get_workstation_id()
        evt = Event(
            job_id=job.id,
            event_type=event_type,
            details={},
            triggered_by=review_data.staff_name,
            workstation_id=workstation_id,
        )
        db.session.add(evt)
        db.session.commit()
        
        return job
    
    def append_note(self, job_id: str, note_data: JobNoteData, workstation_id: str = None) -> Job:
        """Append a note to a job with comprehensive validation and business logic"""
        # Use ValidationService for all validation
        job_result = self.validation.validate_job_exists(job_id)
        if not job_result.is_valid:
            raise ValueError(job_result.error_message)
        
        staff_result = self.validation.validate_staff(note_data.staff_name)
        if not staff_result.is_valid:
            raise ValueError(staff_result.error_message)
        
        # Validate text
        if not isinstance(note_data.text, str):
            raise ValueError('text must be a string')
        
        text = note_data.text.strip()
        if not text:
            raise ValueError('text is required')
        
        # Validate length limits
        per_entry_limit = 1000
        total_limit = 5000
        if len(text) > per_entry_limit:
            raise ValueError(f'text must be at most {per_entry_limit} characters')
        
        job = job_result.data
        
        # Build the new line to append
        new_line = f"{note_data.staff_name} - {text}"
        current = job.notes or ''
        # Compute resulting total length with newline if needed
        separator = ('\n' if current else '')
        proposed = current + separator + new_line
        if len(proposed) > total_limit:
            raise ValueError('total notes length exceeded')
        
        # Update job
        job.notes = proposed
        job.last_updated_by = note_data.staff_name
        db.session.add(job)
        db.session.commit()
        
        # Log event
        workstation_id = workstation_id or self._get_workstation_id()
        evt = Event(
            job_id=job.id,
            event_type='NoteAdded',
            details={'text_len': len(text)},
            triggered_by=note_data.staff_name,
            workstation_id=workstation_id,
        )
        db.session.add(evt)
        db.session.commit()
        
        return job
    
    def update_notes(self, job_id: str, notes_data: JobUpdateNotesData, workstation_id: str = None) -> Job:
        """Update job notes with comprehensive validation and business logic"""
        # Use ValidationService for all validation
        job_result = self.validation.validate_job_exists(job_id)
        if not job_result.is_valid:
            raise ValueError(job_result.error_message)
        
        staff_result = self.validation.validate_staff(notes_data.staff_name)
        if not staff_result.is_valid:
            raise ValueError(staff_result.error_message)
        
        # Validate notes
        if not isinstance(notes_data.notes, str):
            raise ValueError('notes must be a string')
        
        if len(notes_data.notes) > 5000:
            raise ValueError('notes must be at most 5000 characters')
        
        job = job_result.data
        
        # Update job
        job.notes = notes_data.notes
        job.last_updated_by = notes_data.staff_name
        db.session.add(job)
        db.session.commit()
        
        # Log event with length only (avoid storing full notes in event log)
        workstation_id = workstation_id or self._get_workstation_id()
        evt = Event(
            job_id=job.id,
            event_type='NotesUpdated',
            details={'notes_len': len(notes_data.notes)},
            triggered_by=notes_data.staff_name,
            workstation_id=workstation_id,
        )
        db.session.add(evt)
        db.session.commit()
        
        return job
    
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
        
        # Move files only if mapping exists for the target status
        if new_status in STATUS_TO_DIR:
            move_authoritative(job, new_status)
        
        db.session.add(job)
        db.session.commit()
        
        # Log events
        workstation_id = workstation_id or self._get_workstation_id()
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
        
        # Move file/metadata to Archived and sync metadata
        move_authoritative(job, 'ARCHIVED')
        db.session.add(job)
        db.session.commit()
        
        # Log event
        workstation_id = workstation_id or self._get_workstation_id()
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
        workstation_id = workstation_id or self._get_workstation_id()
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
        workstation_id = workstation_id or self._get_workstation_id()
        
        # Generate fresh token and send approval email
        from app.services.token_service import generate_confirmation_token
        from app.services.email_service import send_approval_email
        import os
        
        token = generate_confirmation_token(job.id)
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
        from datetime import datetime
        try:
            job.confirmation_last_sent_at = datetime.utcnow()
            from app import db
            db.session.add(job)
            db.session.commit()
        except Exception:
            pass
        
        # Log events with staff attribution
        from app.models.event import Event
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
        workstation_id = workstation_id or self._get_workstation_id()
        
        # No lock fields yet; log action for audit
        from app.models.event import Event
        evt = Event(
            job_id=job.id,
            event_type='AdminAction',
            details={'action': 'force_unlock', 'reason': unlock_data.reason, 'note': 'No server-side lock fields present'},
            triggered_by=unlock_data.staff_name,
            workstation_id=workstation_id,
        )
        from app import db
        db.session.add(evt)
        db.session.commit()
        
        return {
            'message': 'unlock processed',
            'lock_support': 'not_implemented'
        }
    
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
        
        # Check if current workstation owns the lock
        if job.locked_by != lock_data.workstation_id:
            raise ValueError('Not lock owner')
        
        # Unlock the job
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

    # --- Status Transition Methods ---
    
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
        move_authoritative(job, 'PRINTING')
        db.session.add(job)
        db.session.commit()
        
        # Log event
        workstation_id = transition_data.workstation_id or self._get_workstation_id()
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
        move_authoritative(job, 'COMPLETED')
        db.session.add(job)
        db.session.commit()
        
        # Log event
        workstation_id = transition_data.workstation_id or self._get_workstation_id()
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
        move_authoritative(job, 'PAIDPICKEDUP')
        db.session.add(job)
        db.session.commit()
        
        # Log event
        workstation_id = transition_data.workstation_id or self._get_workstation_id()
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
        move_authoritative(job, 'READYTOPRINT')
        db.session.add(job)
        db.session.commit()
        
        # Log failure and admin action
        workstation_id = transition_data.workstation_id or self._get_workstation_id()
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
        move_authoritative(job, 'READYTOPRINT')
        db.session.add(job)
        db.session.commit()
        
        # Log specific and admin events
        workstation_id = transition_data.workstation_id or self._get_workstation_id()
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
        move_authoritative(job, 'PRINTING')
        db.session.add(job)
        db.session.commit()
        
        # Log event
        workstation_id = transition_data.workstation_id or self._get_workstation_id()
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
        move_authoritative(job, 'COMPLETED')
        db.session.add(job)
        db.session.commit()
        
        # Log event
        workstation_id = transition_data.workstation_id or self._get_workstation_id()
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
        
        # Handle status-specific logic
        if new_status in ['PRINTING', 'COMPLETED', 'PAIDPICKEDUP']:
            move_authoritative(job, new_status)
        
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
    
    def _calculate_job_cost(self, material: str, weight_g: float) -> Decimal:
        """Calculate job cost based on material and weight"""
        material_lower = (material or '').strip().lower()
        if material_lower == 'resin':
            rate = 0.20
        else:
            # Default to filament pricing if unknown, to avoid blocking
            rate = 0.10
        
        # Compute cost with minimum $3.00
        raw_cost = weight_g * rate
        min_cost = 3.00
        final_cost = max(raw_cost, min_cost)
        
        # Round to 2 decimals using bankers rounding to HALF_UP
        return Decimal(str(final_cost)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def _apply_printer_override(self, job: Job, printer_override: str) -> None:
        """Apply printer override with validation"""
        # Determine method from material for validation
        method_for_validation = "Filament" if (job.material or '').lower() in ["pla", "abs"] else "Resin" if (job.material or '').lower() in ["resin", "standard resin"] else "Filament"
        
        # Validate printer override against catalog
        is_valid, validation_errors = CatalogService.validate_job_configuration(
            method=method_for_validation,
            material=job.material,
            color=job.color,
            printer=printer_override
        )
        
        if not is_valid:
            raise ValueError(f'Invalid printer override: {validation_errors}')
        
        previous_printer = job.printer
        if printer_override and printer_override != previous_printer:
            job.printer = printer_override
    
    def _apply_authoritative_filename(self, job: Job, authoritative_filename: str) -> None:
        """Apply authoritative filename with validation"""
        current_dir = Path(job.file_path).parent
        candidate_path = (current_dir / authoritative_filename)
        
        # Allowed extensions are driven by env
        exts_env = os.environ.get('ALLOWED_MODEL_EXTS', '.stl,.obj,.3mf,.form,.idea')
        allowed_exts = {
            (ext if ext.strip().startswith('.') else f'.{ext.strip()}').lower()
            for ext in exts_env.split(',') if ext.strip()
        }
        
        # Validate parent dir, extension, and existence
        if candidate_path.parent != current_dir:
            raise ValueError('authoritative_filename must be in the same directory as the current file')
        if candidate_path.suffix.lower() not in allowed_exts:
            raise ValueError(f'authoritative_filename has unsupported extension')
        if not candidate_path.exists():
            raise ValueError(f'authoritative file not found: {authoritative_filename}')
        
        # Accept switch
        job.file_path = str(candidate_path.resolve())
        job.display_name = authoritative_filename
    
    def _log_approval_events(self, job: Job, approval_data: JobApprovalData, 
                           confirmation_url: str, workstation_id: str) -> None:
        """Log approval-related events"""
        evt_details = {
            'confirmation_url': confirmation_url,
            'weight_g': approval_data.weight_g,
            'time_hours': approval_data.time_hours,
            'cost_usd': float(job.cost_usd),
            'authoritative_filename': approval_data.authoritative_filename or job.display_name,
        }
        
        # If printer changed, include before/after in event details
        if approval_data.printer_override:
            evt_details['printer_after'] = job.printer
        
        evt1 = Event(
            job_id=job.id,
            event_type='StaffApproved',
            details=evt_details,
            triggered_by=approval_data.staff_name,
            workstation_id=workstation_id,
        )
        db.session.add(evt1)
        db.session.commit()
        
        evt2 = Event(
            job_id=job.id,
            event_type='ApprovalEmailSent',
            details={},
            triggered_by=approval_data.staff_name,
            workstation_id=workstation_id,
        )
        db.session.add(evt2)
        db.session.commit()
    
    def _sync_authoritative_metadata(self, job: Job, filename: str, staff_name: str, event_type: str) -> None:
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
