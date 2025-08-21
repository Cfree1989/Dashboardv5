from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import os

# Import foundation services
from app.services.validation_service import ValidationService
from app.services.response_service import ResponseService

# Import models and services
from app.models.job import Job
from app.models.staff import Staff
from app.models.event import Event
from app.services.token_service import generate_confirmation_token
from app.services.email_service import send_approval_email, send_rejection_email
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
