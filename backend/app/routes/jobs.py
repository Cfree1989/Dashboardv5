from flask import Blueprint
from flask import request, jsonify, abort, g
from app import db, limiter
from app.models.job import Job
from app.utils.decorators import token_required
from app.models.event import Event
from app.models.payment import Payment
from app.business_logic.shared_services import token_service
from app.business_logic.shared_services import email_service
from app.business_logic.shared_services import event_service
# Staff model queries replaced with ValidationService
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path  # Still used in metadata helpers
from decimal import Decimal, ROUND_HALF_UP

from app.business_logic.shared_services.catalog_service import CatalogService
from app.business_logic.shared_services.error_handling_service import get_error_handling_service
import logging
# sqlalchemy.or_ moved to JobQueryService
from app.business_logic.shared_services.validation_service import ValidationService
from app.business_logic.shared_services.response_service import ResponseService
from app.services.orchestration.job_orchestration_service import JobOrchestrationService
from app.business_logic.job_lifecycle.job_approval_service import JobApprovalData, JobRejectionData, JobReviewData
from app.business_logic.job_lifecycle.job_status_service import JobStatusTransitionData
from app.business_logic.admin_operations.job_notes_service import JobNoteData, JobUpdateNotesData
from app.business_logic.admin_operations.job_admin_service import JobAdminStatusChangeData, JobDeleteData, JobResendEmailData, JobForceUnlockData
from app.services.infrastructure.payment_service import PaymentService
from app.services.infrastructure.payment_service_interface import PaymentData
from app.services.infrastructure.file_discovery_service import FileDiscoveryService
from app.services.infrastructure.job_query_service import JobQueryService, JobFilters

logger = logging.getLogger(__name__)

bp = Blueprint('jobs', __name__, url_prefix='/api/v1/jobs')

# Create service instances
orchestration_service = JobOrchestrationService()
payment_service = PaymentService()
file_discovery_service = FileDiscoveryService()
job_query_service = JobQueryService()

# Job management routes implemented using new service architecture
# All routes use JobOrchestrationService, ValidationService, and ResponseService 


@bp.route('/<job_id>/validate', methods=['GET'])
@token_required
def validate_job(job_id):
    """Test endpoint to verify ValidationService and ResponseService work together"""
    result = ValidationService.validate_job_exists(job_id)
    if not result.is_valid:
        return ResponseService.not_found('Job')
    return ResponseService.success({'message': 'Job is valid', 'job_id': job_id})

@bp.route('', methods=['GET'])
@token_required
def list_jobs():
    """Get filtered list of jobs - simplified via JobQueryService"""
    # Build filters from query parameters
    filters = JobFilters(
        status=request.args.get('status'),
        search=request.args.get('search'),
        printer=request.args.get('printer'),
        discipline=request.args.get('discipline')
    )
    
    # Use JobQueryService to get filtered jobs
    jobs = job_query_service.list_jobs(filters)
    return ResponseService.success([job.to_dict() for job in jobs])


@bp.route('/counts', methods=['GET'])
@token_required
def get_job_counts():
    """Get job counts by status for dashboard tabs - simplified via JobQueryService"""
    try:
        search = request.args.get('search')
        counts = job_query_service.get_job_counts(search)
        return ResponseService.success(counts)
    except Exception as e:
        logger.error(f"Failed to get job counts: {e}")
        return ResponseService.error('Failed to get job counts', status=500)



# --- Metadata helpers ---
def _load_metadata(job: Job) -> dict:
    error_service = get_error_handling_service()
    
    try:
        return _load_metadata_file(job.metadata_path)
    except Exception as e:
        error_service.log_metadata_sync_error(
            error=e,
            job_id=str(job.id),
            metadata_path=job.metadata_path,
            context={'operation': 'load_metadata'}
        )
        logger.warning(f"Failed to load metadata for job {job.id}: {e}")
        return {}


def _load_metadata_file(metadata_path: str) -> dict:
    """Load metadata from file with proper error handling."""
    with open(metadata_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_metadata(job: Job, data: dict) -> None:
    error_service = get_error_handling_service()
    
    success, error_msg = error_service.handle_metadata_operation_with_error_handling(
        job_id=str(job.id),
        metadata_path=job.metadata_path,
        operation_func=lambda: _save_metadata_file(job.metadata_path, data)
    )
    
    if not success:
        logger.error(f"Failed to save metadata for job {job.id}: {error_msg}")
        # Don't raise here as metadata sync should not block workflow, but log the error


def _save_metadata_file(metadata_path: str, data: dict) -> None:
    """Save metadata to file with proper error handling."""
    meta_path = Path(metadata_path)
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def _sync_authoritative_metadata(job: Job, authoritative_filename: str, staff_name: str | None, event_type: str) -> None:
    error_service = get_error_handling_service()
    
    success, error_msg = error_service.handle_metadata_operation_with_error_handling(
        job_id=str(job.id),
        metadata_path=job.metadata_path,
        operation_func=lambda: _sync_metadata_content(job, authoritative_filename, staff_name, event_type)
    )
    
    if not success:
        logger.error(f"Failed to sync metadata for job {job.id}: {error_msg}")
        # Don't raise here as metadata sync should not block workflow, but log the error


def _sync_metadata_content(job: Job, authoritative_filename: str, staff_name: str | None, event_type: str) -> None:
    """Sync metadata content with proper error handling."""
    meta = _load_metadata(job)
    history = meta.get('authoritative_history', [])
    prev = meta.get('authoritative_filename')
    changed = False
    
    if authoritative_filename and authoritative_filename != prev:
        history.append({
            'ts': datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(),
            'by': staff_name,
            'event': event_type,
            'from': prev,
            'to': authoritative_filename,
        })
        meta['authoritative_history'] = history
        meta['authoritative_filename'] = authoritative_filename
        changed = True

    # Keep other fields in sync
    if meta.get('status') != job.status:
        meta['status'] = job.status
        changed = True
    if meta.get('display_name') != job.display_name:
        meta['display_name'] = job.display_name
        changed = True
    if meta.get('file_path') != job.file_path:
        meta['file_path'] = job.file_path
        changed = True
    
    meta['updated_at'] = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
    
    if changed:
        _save_metadata(job, meta)

@bp.route('/<job_id>', methods=['GET'])
@token_required
def get_job(job_id):
    job = orchestration_service.get_job_by_id(job_id)
    if not job:
        abort(404, description='Job not found')
    return jsonify(job.to_dict()), 200

@bp.route('/<job_id>/events', methods=['GET'])
@token_required
def get_job_events(job_id):
    job = orchestration_service.get_job_by_id(job_id)
    if not job:
        abort(404, description='Job not found')
    events = orchestration_service.get_job_events(job_id)
    return jsonify([e.to_dict() for e in events]), 200


@bp.route('/<job_id>/candidate-files', methods=['GET'])
@token_required
def candidate_files(job_id):
    """Get candidate files for a job - simplified via FileDiscoveryService"""
    # Validate job exists
    job_result = ValidationService.validate_job_exists(job_id)
    if not job_result.is_valid:
        return ResponseService.not_found('Job')
    
    # Use FileDiscoveryService to discover candidate files
    try:
        result = file_discovery_service.discover_candidate_files(job_result.data)
        return ResponseService.success(result.to_dict())
    except Exception as e:
        logger.error(f"Failed to discover candidate files for job {job_id}: {e}")
        return ResponseService.error('Failed to discover candidate files', status=500)


@bp.route('/<job_id>/log-file-open', methods=['POST'])
@token_required
def log_file_open(job_id):
    """Stub endpoint for protocol handler touchpoint. Logs FileOpenedInSlicer.
    Body: { } (staff_name no longer required)
    """
    job = orchestration_service.get_job_by_id(job_id)
    if not job:
        abort(404, description='Job not found')
    data = request.get_json(silent=True) or {}
    
    # Ensure non-null values for required Event fields
    workstation_id = getattr(g, 'workstation_id', 'unknown')
    if not workstation_id:
        workstation_id = 'unknown'
    
    evt = Event(
        job_id=job.id,
        event_type='FileOpenedInSlicer',
        details={'file_path': job.file_path},
        triggered_by='file-open-action',  # System action, not staff-attributed
        workstation_id=workstation_id,
    )
    db.session.add(evt)
    db.session.commit()
    return jsonify({'message': 'logged'}), 200


@bp.route('/<job_id>/notes', methods=['PATCH'])
@token_required
def update_notes(job_id):
    data = request.get_json(silent=True) or {}
    
    try:
        # Create update notes data object
        notes_data = JobUpdateNotesData(
            staff_name=data.get('staff_name'),
            notes=data.get('notes')
        )
        
        # Use JobLifecycleService to update notes
        job = orchestration_service.update_notes(job_id, notes_data)
        return ResponseService.success(job.to_dict())
        
    except ValueError as e:
        return ResponseService.error(str(e))

@bp.route('/<job_id>', methods=['DELETE'])
@token_required
def delete_job(job_id):
    data = request.get_json(silent=True) or {}
    
    try:
        # Create delete data object with staff attribution
        from app.business_logic.admin_operations.job_admin_service import JobDeleteData
        delete_data = JobDeleteData(
            staff_name=data.get('staff_name')
        )
        
        # Use JobOrchestrationService to delete job with staff attribution
        job = orchestration_service.delete_job(job_id, delete_data)
        return ResponseService.success(job.to_dict())
        
    except ValueError as e:
        return ResponseService.error(str(e), status=403)


@bp.route('/<job_id>/hard-delete', methods=['POST'])
@token_required
def hard_delete_job(job_id):
    data = request.get_json(silent=True) or {}
    
    try:
        # Create delete data object
        delete_data = JobDeleteData(
            staff_name=data.get('staff_name')
        )
        
        # Use JobLifecycleService to hard delete job
        result = orchestration_service.hard_delete_job(job_id, delete_data)
        return ResponseService.success(result)
        
    except ValueError as e:
        return ResponseService.error(str(e))


@bp.route('/<job_id>/approve', methods=['POST'])
@token_required
def approve_job(job_id):
    data = request.get_json(silent=True) or {}
    
    try:
        approval_data = JobApprovalData(
            staff_name=data.get('staff_name'),
            weight_g=float(data.get('weight_g', 0)),
            time_hours=float(data.get('time_hours', 0)),
            authoritative_filename=data.get('authoritative_filename'),
            printer_override=data.get('printer')
        )
        
        job = orchestration_service.approve_job(job_id, approval_data)
        return ResponseService.success(job.to_dict())
        
    except ValueError as e:
        return ResponseService.error(str(e))


@bp.route('/<job_id>/notes', methods=['POST'])
@token_required
def append_note(job_id):
    data = request.get_json(silent=True) or {}
    
    try:
        # Create note data object
        note_data = JobNoteData(
            staff_name=data.get('staff_name'),
            text=data.get('text')
        )
        
        # Use JobLifecycleService to append note
        job = orchestration_service.append_note(job_id, note_data)
        return ResponseService.success(job.to_dict())
        
    except ValueError as e:
        return ResponseService.error(str(e))

# Removed _validate_staff_and_body - replaced with ValidationService.validate_staff


# Duplicate update_notes route removed (consolidated above)


@bp.route('/<job_id>/mark-printing', methods=['POST'])
@token_required
def mark_printing(job_id):
    data = request.get_json(silent=True) or {}
    
    # Validate staff using ValidationService
    staff_result = ValidationService.validate_staff(data.get('staff_name'))
    if not staff_result.is_valid:
        return ResponseService.error(staff_result.error_message)
    
    try:

        transition_data = JobStatusTransitionData(staff_name=staff_result.data.name)
        job = orchestration_service.mark_printing(job_id, transition_data)
        return ResponseService.success(job.to_dict())
    except ValueError as e:
        return ResponseService.error(str(e))


# --- Admin Overrides ---

# Removed _validate_reason - replaced with inline validation using ResponseService


@bp.route('/<job_id>/admin/force-unlock', methods=['POST'])
@token_required
def admin_force_unlock(job_id):
    data = request.get_json(silent=True) or {}
    
    try:
        # Create force unlock data object
        unlock_data = JobForceUnlockData(
            staff_name=data.get('staff_name'),
            reason=data.get('reason')
        )
        
        # Use JobLifecycleService to force unlock
        result = orchestration_service.force_unlock_job(job_id, unlock_data)
        return ResponseService.success(result)
        
    except ValueError as e:
        return ResponseService.error(str(e))


@bp.route('/<job_id>/admin/force-confirm', methods=['POST'])
@token_required
def admin_force_confirm(job_id):
    data = request.get_json(silent=True) or {}
    
    # Validate staff using ValidationService
    staff_result = ValidationService.validate_staff(data.get('staff_name'))
    if not staff_result.is_valid:
        return ResponseService.error(staff_result.error_message)
    
    # Validate reason is provided
    reason = (data.get('reason') or '').strip()
    if not reason:
        return ResponseService.error('reason is required')
    
    try:

        transition_data = JobStatusTransitionData(staff_name=staff_result.data.name, reason=reason)
        job = orchestration_service.admin_force_confirm(job_id, transition_data)
        return ResponseService.success(job.to_dict())
    except ValueError as e:
        return ResponseService.error(str(e))


@bp.route('/<job_id>/admin/change-status', methods=['POST'])
@token_required
def admin_change_status(job_id):
    data = request.get_json(silent=True) or {}
    
    try:
        # Create status change data object
        status_change_data = JobAdminStatusChangeData(
            staff_name=data.get('staff_name'),
            new_status=data.get('new_status'),
            reason=data.get('reason')
        )
        
        # Use JobLifecycleService to change status
        job = orchestration_service.admin_change_status(job_id, status_change_data)
        return ResponseService.success(job.to_dict())
        
    except ValueError as e:
        return ResponseService.error(str(e))


@bp.route('/<job_id>/admin/resend-email', methods=['POST'])
@token_required
@limiter.limit("1 per hour")
def admin_resend_email(job_id):
    data = request.get_json(silent=True) or {}
    
    try:
        # Create resend email data object
        resend_data = JobResendEmailData(
            staff_name=data.get('staff_name')
        )
        
        # Use JobLifecycleService to resend email
        result = orchestration_service.resend_approval_email(job_id, resend_data)
        return ResponseService.success(result)
        
    except ValueError as e:
        return ResponseService.error(str(e))

@bp.route('/<job_id>/admin/mark-failed', methods=['POST'])
@token_required
def admin_mark_failed(job_id):
    data = request.get_json(silent=True) or {}
    
    # Validate staff using ValidationService
    staff_result = ValidationService.validate_staff(data.get('staff_name'))
    if not staff_result.is_valid:
        return ResponseService.error(staff_result.error_message)
    
    # Validate reason is provided
    reason = (data.get('reason') or '').strip()
    if not reason:
        return ResponseService.error('reason is required')
    
    try:

        transition_data = JobStatusTransitionData(staff_name=staff_result.data.name, reason=reason)
        job = orchestration_service.mark_failed(job_id, transition_data)
        return ResponseService.success(job.to_dict())
    except ValueError as e:
        return ResponseService.error(str(e))


@bp.route('/<job_id>/mark-complete', methods=['POST'])
@token_required
def mark_complete(job_id):
    data = request.get_json(silent=True) or {}
    
    # Validate staff using ValidationService
    staff_result = ValidationService.validate_staff(data.get('staff_name'))
    if not staff_result.is_valid:
        return ResponseService.error(staff_result.error_message)
    
    try:

        transition_data = JobStatusTransitionData(staff_name=staff_result.data.name)
        job = orchestration_service.mark_complete(job_id, transition_data)
        return ResponseService.success(job.to_dict())
    except ValueError as e:
        return ResponseService.error(str(e))


@bp.route('/<job_id>/mark-picked-up', methods=['POST'])
@token_required
def mark_picked_up(job_id):
    data = request.get_json(silent=True) or {}
    
    # Validate staff using ValidationService
    staff_result = ValidationService.validate_staff(data.get('staff_name'))
    if not staff_result.is_valid:
        return ResponseService.error(staff_result.error_message)
    
    try:

        transition_data = JobStatusTransitionData(staff_name=staff_result.data.name)
        job = orchestration_service.mark_picked_up(job_id, transition_data)
        return ResponseService.success(job.to_dict())
    except ValueError as e:
        return ResponseService.error(str(e))


@bp.route('/<job_id>/payment', methods=['POST'])
@token_required
def record_payment(job_id):
    data = request.get_json(silent=True) or {}
    
    try:
        # Parse and validate input data
        try:
            grams = float(data.get('grams'))
        except (TypeError, ValueError):
            return ResponseService.error('grams must be a number')
        
        txn_no = (data.get('txn_no') or '').strip()
        picked_up_by = (data.get('picked_up_by') or '').strip()
        
        # Create PaymentData object
        payment_data = PaymentData(
            grams=grams,
            txn_no=txn_no,
            picked_up_by=picked_up_by,
            staff_name=data.get('staff_name')
        )
        
        # Use PaymentService to record payment
        payment = payment_service.record_payment(job_id, payment_data)
        
        # Get the updated job data
        job = orchestration_service.get_job_by_id(job_id)
        return ResponseService.success(job.to_dict())
        
    except ValueError as e:
        return ResponseService.error(str(e))


@bp.route('/<job_id>/review', methods=['POST'])
@token_required
def review_job(job_id):
    data = request.get_json(silent=True) or {}
    
    try:
        # Create review data object
        review_data = JobReviewData(
            staff_name=data.get('staff_name'),
            reviewed=data.get('reviewed')
        )
        
        # Use JobLifecycleService to review job
        job = orchestration_service.review_job(job_id, review_data)
        return ResponseService.success(job.to_dict())
        
    except ValueError as e:
        return ResponseService.error(str(e))


@bp.route('/<job_id>/reject', methods=['POST'])
@token_required
def reject_job(job_id):
    data = request.get_json(silent=True) or {}
    
    try:
        # Create rejection data object
        rejection_data = JobRejectionData(
            staff_name=data.get('staff_name'),
            reasons=data.get('reasons') or [],
            custom_reason=data.get('custom_reason')
        )
        
        # Use JobLifecycleService to reject job
        job = orchestration_service.reject_job(job_id, rejection_data)
        return ResponseService.success(job.to_dict())
        
    except ValueError as e:
        return ResponseService.error(str(e))


@bp.route('/<job_id>/revert-completion', methods=['POST'])
@token_required
def revert_completion(job_id):
    data = request.get_json(silent=True) or {}
    
    # Validate staff using ValidationService
    staff_result = ValidationService.validate_staff(data.get('staff_name'))
    if not staff_result.is_valid:
        return ResponseService.error(staff_result.error_message)
    
    try:

        transition_data = JobStatusTransitionData(staff_name=staff_result.data.name)
        job = orchestration_service.revert_to_printing(job_id, transition_data)
        return ResponseService.success(job.to_dict())
    except ValueError as e:
        return ResponseService.error(str(e))


@bp.route('/<job_id>/revert-pickup', methods=['POST'])
@token_required
def revert_pickup(job_id):
    data = request.get_json(silent=True) or {}
    
    # Validate staff using ValidationService
    staff_result = ValidationService.validate_staff(data.get('staff_name'))
    if not staff_result.is_valid:
        return ResponseService.error(staff_result.error_message)
    
    try:

        transition_data = JobStatusTransitionData(staff_name=staff_result.data.name)
        job = orchestration_service.revert_to_completed(job_id, transition_data)
        return ResponseService.success(job.to_dict())
    except ValueError as e:
        return ResponseService.error(str(e))

@bp.route('/<job_id>/lock', methods=['POST'])
@token_required
def lock_job(job_id):
    try:
        # Get workstation ID for locking
        workstation_id = getattr(g, 'workstation_id', 'unknown')
        
        # Use JobOrchestrationService to lock job
        job = orchestration_service.lock_job(job_id, workstation_id)
        return ResponseService.success(job.to_dict())
        
    except ValueError as e:
        return ResponseService.error(str(e), status=409 if 'already locked' in str(e) else 400)

@bp.route('/<job_id>/unlock', methods=['POST'])
@token_required
def unlock_job(job_id):
    try:
        # Get workstation ID for unlocking
        workstation_id = getattr(g, 'workstation_id', 'unknown')
        
        # Use JobOrchestrationService to unlock job
        job = orchestration_service.unlock_job(job_id, workstation_id)
        return ResponseService.success(job.to_dict())
        
    except ValueError as e:
        return ResponseService.error(str(e), status=403 if 'Not lock owner' in str(e) else 400)

@bp.route('/<job_id>/extend', methods=['POST'])
@token_required
def extend_job_lock(job_id):
    try:
        # Get workstation ID for extending lock
        workstation_id = getattr(g, 'workstation_id', 'unknown')
        
        # Use JobOrchestrationService to extend job lock
        job = orchestration_service.extend_job_lock(job_id, workstation_id)
        return ResponseService.success(job.to_dict())
        
    except ValueError as e:
        return ResponseService.error(str(e), status=403 if 'Not lock owner' in str(e) else 400)