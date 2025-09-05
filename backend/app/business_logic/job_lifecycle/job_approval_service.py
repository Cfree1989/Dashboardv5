from typing import Optional
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import os

# Import foundation services
from app.business_logic.shared_services.validation_service import ValidationService
from app.business_logic.shared_services.response_service import ResponseService
from app.services.infrastructure.file_configuration_service import get_file_configuration_service

# Import models and services
from app.models.job import Job
from app.models.event import Event
from app.business_logic.shared_services.token_service import generate_confirmation_token
from app.business_logic.shared_services.email_service import send_approval_email, send_rejection_email
from app.business_logic.shared_services.catalog_service import CatalogService
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
    def __init__(self, staff_name: str, reasons: list, custom_reason: Optional[str] = None):
        self.staff_name = staff_name
        self.reasons = reasons
        self.custom_reason = custom_reason

class JobReviewData:
    """Data class for job review parameters"""
    def __init__(self, staff_name: str, reviewed: bool):
        self.staff_name = staff_name
        self.reviewed = reviewed

class JobApprovalService:
    """Service for managing job approval, rejection, and review operations"""
    
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
        
        # Perform atomic file move from Uploaded to Pending before updating status
        from app.services.infrastructure.atomic_file_service import get_atomic_file_service
        atomic_service = get_atomic_file_service()
        file_move_success = atomic_service.atomic_move_authoritative(job, 'PENDING')
        
        if not file_move_success:
            # Log the error but continue with the approval - file can be fixed later via admin tools
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"File move failed during approval for job {job.id}, continuing with status update")
        
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
        
        # Send rejection email
        send_rejection_email(job)
        
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
        
        # Use centralized file configuration
        file_config = get_file_configuration_service()
        allowed_exts = file_config.allowed_extensions
        
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
        # Provide fallback for workstation_id to prevent constraint violations
        safe_workstation_id = workstation_id or 'unknown'
        
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
            workstation_id=safe_workstation_id,
        )
        db.session.add(evt1)
        db.session.commit()
        
        evt2 = Event(
            job_id=job.id,
            event_type='ApprovalEmailSent',
            details={},
            triggered_by=approval_data.staff_name,
            workstation_id=safe_workstation_id,
        )
        db.session.add(evt2)
        db.session.commit()
    
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
