from flask import Blueprint
from flask import request, abort, g
from app import db, limiter
from app.models.job import Job
from app.utils.decorators import token_required
from app.models.event import Event
from app.models.payment import Payment
from app.business_logic.shared_services import token_service
from app.business_logic.shared_services import email_service
from app.business_logic.shared_services import event_service
from app.models.staff import Staff
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import shutil
from decimal import Decimal, ROUND_HALF_UP
from app.services.infrastructure.atomic_file_service import get_atomic_file_service
from app.business_logic.shared_services.catalog_service import CatalogService
from app.business_logic.shared_services.error_handling_service import get_error_handling_service
from app.services.infrastructure.file_discovery_service import FileDiscoveryService
from app.business_logic.shared_services.validation_service import ValidationService
from app.business_logic.shared_services.response_service import ResponseService
from app.services.orchestration.job_orchestration_service import JobOrchestrationService
from app.routes.jobs import _sync_authoritative_metadata
import logging
from sqlalchemy import or_

logger = logging.getLogger(__name__)

def _validate_staff_and_body(data):
    """Helper function to validate staff and request body"""
    if not data:
        return None, ResponseService.validation_error('Request body required')
    
    staff_name = data.get('staff_name', '').strip()
    if not staff_name:
        return None, ResponseService.validation_error('staff_name is required')
    
    staff_result = ValidationService.validate_staff(staff_name)
    if not staff_result.is_valid:
        return None, ResponseService.validation_error(staff_result.message)
    
    return staff_name, None

bp = Blueprint('jobs', __name__, url_prefix='/api/v1/jobs')

# Create orchestration service instance
orchestration_service = JobOrchestrationService()

# Job management routes implemented using new service architecture
# All routes use JobOrchestrationService, ValidationService, and ResponseService 

@bp.route('', methods=['GET'])
@token_required
def list_jobs():
    status = request.args.get('status')
    search = request.args.get('search')
    printer = request.args.get('printer')
    discipline = request.args.get('discipline')
    query = Job.query
    if status:
        query = query.filter_by(status=status)
    if printer:
        query = query.filter_by(printer=printer)
    if discipline:
        query = query.filter_by(discipline=discipline)
    jobs = query.all()
    if search:
        jobs = [job for job in jobs if search.lower() in job.student_name.lower() or search.lower() in job.student_email.lower()]
    return ResponseService.success([job.to_dict() for job in jobs])


@bp.route('/counts', methods=['GET'])
@token_required
def get_job_counts():
    """Get job counts by status for dashboard tabs."""
    try:
        from sqlalchemy import func
        search = request.args.get('search')
        
        query = Job.query
        if search:
            # Filter jobs by search term
            query = query.filter(
                or_(
                    Job.student_name.ilike(f'%{search}%'),
                    Job.student_email.ilike(f'%{search}%')
                )
            )
        
        rows = query.with_entities(Job.status, func.count()).group_by(Job.status).all()
        counts = {status: int(count) for status, count in rows}
        return ResponseService.success(counts)
    except Exception as e:
        logger.error(f"Failed to get job counts: {e}")
        return ResponseService.server_error('Failed to get job counts')



# --- Metadata helpers ---
@bp.route('/<job_id>', methods=['GET'])
@token_required
def get_job(job_id):
    job = orchestration_service.get_job_by_id(job_id)
    if not job:
        return ResponseService.not_found('Job')
    return ResponseService.success(job.to_dict())

@bp.route('/<job_id>/events', methods=['GET'])
@token_required
def get_job_events(job_id):
    events = orchestration_service.get_job_events(job_id)
    return ResponseService.success([e.to_dict() for e in events])


@bp.route('/<job_id>/candidate-files', methods=['GET'])
@token_required
def candidate_files(job_id):
    job = orchestration_service.get_job_by_id(job_id)
    if not job:
        return ResponseService.not_found('Job')

    try:
        # Use the centralized file discovery service
        discovery_service = FileDiscoveryService()
        result = discovery_service.discover_candidate_files(job)
        return ResponseService.success(result.to_dict())
    except Exception as e:
        # On error, return legacy-compatible minimal payload
        fallback_name = job.original_filename if job and job.original_filename else None
        payload = { 'files': ([fallback_name] if fallback_name else []) }
        if fallback_name:
            payload['files_detailed'] = [{ 'name': fallback_name, 'mtime': 0 }]
        else:
            payload['files_detailed'] = []
        return ResponseService.success(payload)


@bp.route('/<job_id>/log-file-open', methods=['POST'])
@token_required
def log_file_open(job_id):
    """Stub endpoint for protocol handler touchpoint. Logs FileOpenedInSlicer.
    Body: { } (staff_name no longer required)
    """
    job = orchestration_service.get_job_by_id(job_id)
    if not job:
        return ResponseService.not_found('Job')
    
    try:
        orchestration_service.log_event(
            job_id, 
            'FileOpenedInSlicer',
            {'file_path': job.file_path},
            'file-open-action'  # System action, not staff-attributed
        )
        return ResponseService.success({'message': 'logged'})
    except Exception as e:
        logger.error(f"Failed to log file open event: {e}")
        return ResponseService.server_error('Failed to log file open event')


@bp.route('/<job_id>/notes', methods=['PATCH'])
@token_required
def update_notes(job_id):
    data = request.get_json(silent=True) or {}
    staff_name = data.get('staff_name')
    
    if not staff_name:
        return ResponseService.validation_error('staff_name is required')
        
    if 'notes' not in data:
        return ResponseService.validation_error('notes field is required')
    notes_val = data.get('notes')
    
    try:
        job = orchestration_service.update_job_notes(job_id, notes_val, staff_name)
        return ResponseService.success(job.to_dict())
    except ValueError as e:
        return ResponseService.validation_error(str(e))
    except Exception as e:
        logger.error(f"Failed to update notes: {e}")
        return ResponseService.server_error('Failed to update notes')

@bp.route('/<job_id>/mark-printing', methods=['POST'])
@token_required
def mark_printing(job_id):
    data = request.get_json(silent=True) or {}
    staff_name, err_resp = _validate_staff_and_body(data)
    if err_resp:
        return err_resp
    
    try:
        # Check current status before transition
        job = orchestration_service.get_job_by_id(job_id)
        if not job:
            return ResponseService.not_found('Job')
        if job.status != 'READYTOPRINT':
            return ResponseService.validation_error('Job must be in READYTOPRINT to mark printing')
        
        job = orchestration_service.transition_job_with_file_move(
            job_id, 'PRINTING', staff_name, 'JobMarkedPrinting'
        )
        return ResponseService.success(job.to_dict())
    except ValueError as e:
        return ResponseService.validation_error(str(e))
    except RuntimeError as e:
        return ResponseService.server_error(str(e))
    except Exception as e:
        logger.error(f"Failed to mark printing: {e}")
        return ResponseService.server_error('Failed to mark printing')


@bp.route('/<job_id>/mark-complete', methods=['POST'])
@token_required
def mark_complete(job_id):
    data = request.get_json(silent=True) or {}
    staff_name, err_resp = _validate_staff_and_body(data)
    if err_resp:
        return err_resp
    
    try:
        # Check current status before transition
        job = orchestration_service.get_job_by_id(job_id)
        if not job:
            return ResponseService.not_found('Job')
        if job.status != 'PRINTING':
            return ResponseService.validation_error('Job must be in PRINTING to mark complete')
        
        job = orchestration_service.transition_job_with_file_move(
            job_id, 'COMPLETED', staff_name, 'JobMarkedComplete'
        )
        
        # Attempt completion email (best-effort)
        try:
            send_completion_email(job)
            orchestration_service.log_event(job_id, 'CompletionEmailSent', {}, staff_name)
        except Exception:
            pass
            
        return ResponseService.success(job.to_dict())
    except ValueError as e:
        return ResponseService.validation_error(str(e))
    except RuntimeError as e:
        return ResponseService.server_error(str(e))
    except Exception as e:
        logger.error(f"Failed to mark complete: {e}")
        return ResponseService.server_error('Failed to mark complete')


@bp.route('/<job_id>/mark-picked-up', methods=['POST'])
@token_required
def mark_picked_up(job_id):
    data = request.get_json(silent=True) or {}
    staff_name, err_resp = _validate_staff_and_body(data)
    if err_resp:
        return err_resp
    
    try:
        # Check current status before transition
        job = orchestration_service.get_job_by_id(job_id)
        if not job:
            return ResponseService.not_found('Job')
        if job.status != 'COMPLETED':
            return ResponseService.validation_error('Job must be in COMPLETED to mark picked up')
        
        job = orchestration_service.transition_job_with_file_move(
            job_id, 'PAIDPICKEDUP', staff_name, 'JobMarkedPickedUp'
        )
        return ResponseService.success(job.to_dict())
    except ValueError as e:
        return ResponseService.validation_error(str(e))
    except RuntimeError as e:
        return ResponseService.server_error(str(e))
    except Exception as e:
        logger.error(f"Failed to mark picked up: {e}")
        return ResponseService.server_error('Failed to mark picked up')


@bp.route('/<job_id>/payment', methods=['POST'])
@token_required
def record_payment(job_id):
    data = request.get_json(silent=True) or {}
    staff_name, err_resp = _validate_staff_and_body(data)
    if err_resp:
        return err_resp

    try:
        grams = float(data.get('grams'))
    except (TypeError, ValueError):
        return ResponseService.validation_error('grams must be a number')
    
    txn_no = (data.get('txn_no') or '').strip()
    picked_up_by = (data.get('picked_up_by') or '').strip()
    if grams <= 0 or not txn_no or not picked_up_by:
        return ResponseService.validation_error('grams > 0, txn_no and picked_up_by are required')

    try:
        job, payment = orchestration_service.record_job_payment(
            job_id, grams, txn_no, picked_up_by, staff_name
        )
        return ResponseService.success(job.to_dict())
    except ValueError as e:
        return ResponseService.validation_error(str(e))
    except RuntimeError as e:
        return ResponseService.server_error(str(e))
    except Exception as e:
        logger.error(f"Failed to record payment: {e}")
        return ResponseService.server_error('Failed to record payment')


@bp.route('/<job_id>/review', methods=['POST'])
@token_required
def review_job(job_id):
    data = request.get_json(silent=True) or {}
    staff_name = data.get('staff_name')
    reviewed = data.get('reviewed')

    if staff_name is None:
        return ResponseService.validation_error('staff_name is required')
        
    if not isinstance(reviewed, bool):
        return ResponseService.validation_error('reviewed must be a boolean')

    try:
        # Check job exists and status
        job = orchestration_service.get_job_by_id(job_id)
        if not job:
            return ResponseService.not_found('Job')
            
        if job.status != 'UPLOADED':
            return ResponseService.validation_error('Job review state can only be changed in UPLOADED status')

        # Validate staff
        is_valid, error_msg = orchestration_service.validate_staff_exists_and_active(staff_name)
        if not is_valid:
            return ResponseService.validation_error(error_msg)

        # Apply state change
        if reviewed:
            job.staff_viewed_at = datetime.utcnow()
            event_type = 'JobReviewed'
        else:
            job.staff_viewed_at = None
            event_type = 'JobReviewCleared'

        # Update job and log event
        job = orchestration_service.update_job_status(
            job_id, job.status, staff_name, event_type, {}, sync_metadata=False
        )
        
        # Apply additional fields (staff_viewed_at is not handled by standard update)
        from app import db
        if reviewed:
            job.staff_viewed_at = datetime.utcnow()
        else:
            job.staff_viewed_at = None
        db.session.add(job)
        db.session.commit()

        return ResponseService.success(job.to_dict())
    except ValueError as e:
        return ResponseService.validation_error(str(e))
    except Exception as e:
        logger.error(f"Failed to review job: {e}")
        return ResponseService.server_error('Failed to review job')


@bp.route('/<job_id>/reject', methods=['POST'])
@token_required
def reject_job(job_id):
    job = Job.query.get(job_id)
    if not job:
        abort(404, description='Job not found')

    if job.status != 'UPLOADED':
        return ResponseService.validation_error('Job cannot be rejected in its current status')

    data = request.get_json(silent=True) or {}
    staff_name = data.get('staff_name')
    reasons = data.get('reasons') or []
    custom_reason = (data.get('custom_reason') or '').strip()

    if not staff_name:
        return ResponseService.validation_error('staff_name is required')
    staff = Staff.query.get(staff_name)
    if not staff or not staff.is_active:
        return ResponseService.validation_error('Invalid or inactive staff_name')

    # Normalize reasons
    if not isinstance(reasons, list):
        return ResponseService.validation_error('reasons must be an array of strings')
    reasons = [str(r) for r in reasons if str(r).strip()]
    if custom_reason:
        reasons.append(custom_reason)
    if not reasons:
        return ResponseService.validation_error('At least one reason or a custom_reason is required')

    # Update job
    job.status = 'REJECTED'
    job.reject_reasons = reasons
    job.last_updated_by = staff_name
    db.session.add(job)
    db.session.commit()

    # Log event
    evt = Event(
        job_id=job.id,
        event_type='StaffRejected',
        details={'reasons': reasons},
        triggered_by=staff_name,
        workstation_id=g.workstation_id,
    )
    db.session.add(evt)
    db.session.commit()
    # Attempt rejection email (best-effort)
    try:
        send_rejection_email(job)
        email_evt = Event(job_id=job.id, event_type='RejectionEmailSent', details={'reasons': reasons}, triggered_by=staff_name, workstation_id=g.workstation_id)
        db.session.add(email_evt)
        db.session.commit()
    except Exception:
        pass

    return ResponseService.success(job.to_dict())


@bp.route('/<job_id>/revert-completion', methods=['POST'])
@token_required
def revert_completion(job_id):
    job = Job.query.get(job_id)
    if not job:
        abort(404, description='Job not found')
    if job.status != 'COMPLETED':
        return ResponseService.validation_error('Job must be in COMPLETED to revert to PRINTING')
    data = request.get_json(silent=True) or {}
    staff_name, err_resp = _validate_staff_and_body(data)
    if err_resp:
        return err_resp
    before = job.status
    job.status = 'PRINTING'
    job.last_updated_by = staff_name
    atomic_service = get_atomic_file_service()
    success = atomic_service.atomic_move_authoritative(job, 'PRINTING')
    if not success:
        return ResponseService.server_error('File operation failed during revert to printing')
    db.session.add(job)
    db.session.commit()
    evt = Event(job_id=job.id, event_type='JobRevertedToPrinting', details={'from': before, 'to': 'PRINTING'}, triggered_by=staff_name, workstation_id=g.workstation_id)
    db.session.add(evt)
    db.session.commit()
    _sync_authoritative_metadata(job, Path(job.file_path).name, staff_name, 'JobRevertedToPrinting')
    return ResponseService.success(job.to_dict())


@bp.route('/<job_id>/revert-pickup', methods=['POST'])
@token_required
def revert_pickup(job_id):
    job = Job.query.get(job_id)
    if not job:
        abort(404, description='Job not found')
    if job.status != 'PAIDPICKEDUP':
        return ResponseService.validation_error('Job must be in PAIDPICKEDUP to revert to COMPLETED')
    data = request.get_json(silent=True) or {}
    staff_name, err_resp = _validate_staff_and_body(data)
    if err_resp:
        return err_resp
    before = job.status
    job.status = 'COMPLETED'
    job.last_updated_by = staff_name
    atomic_service = get_atomic_file_service()
    success = atomic_service.atomic_move_authoritative(job, 'COMPLETED')
    if not success:
        return ResponseService.server_error('File operation failed during revert to completed')
    db.session.add(job)
    db.session.commit()
    evt = Event(job_id=job.id, event_type='JobRevertedToCompleted', details={'from': before, 'to': 'COMPLETED'}, triggered_by=staff_name, workstation_id=g.workstation_id)
    db.session.add(evt)
    db.session.commit()
    _sync_authoritative_metadata(job, Path(job.file_path).name, staff_name, 'JobRevertedToCompleted')
    return ResponseService.success(job.to_dict())

@bp.route('/<job_id>/lock', methods=['POST'])
@token_required
def lock_job(job_id):
    try:
        job = orchestration_service.lock_job(job_id)
        return ResponseService.success(job.to_dict())
    except ValueError as e:
        if 'not found' in str(e).lower():
            return ResponseService.not_found('Job')
        elif 'locked' in str(e).lower():
            return ResponseService.conflict(str(e))
        else:
            return ResponseService.validation_error(str(e))
    except Exception as e:
        logger.error(f"Failed to lock job: {e}")
        return ResponseService.server_error('Failed to lock job')

@bp.route('/<job_id>/unlock', methods=['POST'])
@token_required
def unlock_job(job_id):
    try:
        job = orchestration_service.unlock_job(job_id)
        return ResponseService.success(job.to_dict())
    except ValueError as e:
        if 'not found' in str(e).lower():
            return ResponseService.not_found('Job')
        elif 'not lock owner' in str(e).lower():
            return ResponseService.forbidden(str(e))
        else:
            return ResponseService.validation_error(str(e))
    except Exception as e:
        logger.error(f"Failed to unlock job: {e}")
        return ResponseService.server_error('Failed to unlock job')

@bp.route('/<job_id>/extend', methods=['POST'])
@token_required
def extend_job_lock(job_id):
    try:
        job = orchestration_service.extend_job_lock(job_id)
        return ResponseService.success(job.to_dict())
    except ValueError as e:
        if 'not found' in str(e).lower():
            return ResponseService.not_found('Job')
        elif 'not lock owner' in str(e).lower():
            return ResponseService.forbidden(str(e))
        else:
            return ResponseService.validation_error(str(e))
    except Exception as e:
        logger.error(f"Failed to extend job lock: {e}")
        return ResponseService.server_error('Failed to extend job lock')