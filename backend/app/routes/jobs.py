from flask import Blueprint
from flask import request, jsonify, abort, g
from app import db, limiter
from app.models.job import Job
from app.utils.decorators import token_required
from app.models.event import Event
from app.models.payment import Payment
from app.services.token_service import generate_confirmation_token
from app.services.email_service import send_approval_email
from app.services.email_service import send_rejection_email, send_completion_email
from app.services.event_service import log_event
from app.models.staff import Staff
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import shutil
from decimal import Decimal, ROUND_HALF_UP
from app.services.file_service import move_authoritative
from app.services.file_service import STATUS_TO_DIR
from app.services.catalog_service import CatalogService
from app.services.error_handling_service import get_error_handling_service
import logging
from sqlalchemy import or_
from app.services.validation_service import ValidationService
from app.services.response_service import ResponseService
from app.services.job_lifecycle_service import JobLifecycleService, JobApprovalData

logger = logging.getLogger(__name__)

bp = Blueprint('jobs', __name__, url_prefix='/api/v1/jobs')

# Create service instance
lifecycle_service = JobLifecycleService()

# TODO: Implement job management routes 

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
    return jsonify([job.to_dict() for job in jobs]), 200


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
        return jsonify(counts), 200
    except Exception as e:
        logger.error(f"Failed to get job counts: {e}")
        return jsonify({'error': 'Failed to get job counts'}), 500



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
            'ts': datetime.utcnow().isoformat(),
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
    
    meta['updated_at'] = datetime.utcnow().isoformat()
    
    if changed:
        _save_metadata(job, meta)

@bp.route('/<job_id>', methods=['GET'])
@token_required
def get_job(job_id):
    job = Job.query.get(job_id)
    if not job:
        abort(404, description='Job not found')
    return jsonify(job.to_dict()), 200

@bp.route('/<job_id>/events', methods=['GET'])
@token_required
def get_job_events(job_id):
    job = Job.query.get(job_id)
    if not job:
        abort(404, description='Job not found')
    events = Event.query.filter(Event.job_id == job_id).order_by(Event.timestamp).all()
    return jsonify([e.to_dict() for e in events]), 200


@bp.route('/<job_id>/candidate-files', methods=['GET'])
@token_required
def candidate_files(job_id):
    job = Job.query.get(job_id)
    if not job:
        abort(404, description='Job not found')

    try:
        file_path = Path(job.file_path)
        directory = file_path.parent
        # Allow configurable extensions via env (e.g., ".stl,.obj,.3mf,.form,.idea")
        exts_env = os.environ.get('ALLOWED_MODEL_EXTS', '.stl,.obj,.3mf,.form,.idea')
        allowed_exts = {
            (ext if ext.strip().startswith('.') else f'.{ext.strip()}').lower()
            for ext in exts_env.split(',') if ext.strip()
        }
        # Extension priority ranking (lower is better) via env, default prefers slicer project files
        priority_env = os.environ.get('AUTHORITATIVE_EXT_PRIORITY', '.3mf,.form,.idea,.stl,.obj')
        prio_list = [e if e.strip().startswith('.') else f'.{e.strip()}' for e in priority_env.split(',') if e.strip()]
        ext_rank = {ext.lower(): idx for idx, ext in enumerate(prio_list)}
        candidates = []
        # Build relevance tokens to restrict to this job only
        tokens = set()
        if getattr(job, 'short_id', None):
            tokens.add(str(job.short_id).lower())
        if getattr(job, 'id', None):
            tokens.add(str(job.id)[:8].lower())
        if getattr(job, 'display_name', None):
            tokens.add(Path(str(job.display_name)).stem.lower())

        if directory.exists() and directory.is_dir():
            for entry in directory.iterdir():
                if not (entry.is_file() and entry.suffix.lower() in allowed_exts):
                    continue
                name_lower = entry.name.lower()
                # Keep only files that look related to this job
                related = any(tok and tok in name_lower for tok in tokens)
                if not related:
                    # Always allow exact original filename if present
                    if job.original_filename and entry.name == job.original_filename:
                        related = True
                if not related:
                    continue
                try:
                    stat = entry.stat()
                    candidates.append({'name': entry.name, 'mtime': int(stat.st_mtime)})
                except OSError:
                    continue
        # Ensure original filename is included (even if not present on disk)
        if job.original_filename and not any(c['name'] == job.original_filename for c in candidates):
            candidates.append({'name': job.original_filename, 'mtime': 0})
        # Sort by (rank asc if known, else large), then mtime desc
        def _rank(name: str) -> int:
            return ext_rank.get(Path(name).suffix.lower(), len(ext_rank) + 1)
        candidates.sort(key=lambda x: (_rank(x['name']), -x['mtime'], x['name'].lower()))
        # Backward-compatible shape: 'files' is list of strings for legacy callers/tests
        files_strings = [c['name'] for c in candidates]
        return jsonify({ 'files': files_strings, 'files_detailed': candidates, 'recommended': files_strings[0] if files_strings else None }), 200
    except Exception as e:
        # On error, return legacy-compatible minimal payload
        fallback_name = job.original_filename if job and job.original_filename else None
        payload = { 'files': ([fallback_name] if fallback_name else []) }
        if fallback_name:
            payload['files_detailed'] = [{ 'name': fallback_name, 'mtime': 0 }]
        else:
            payload['files_detailed'] = []
        return jsonify(payload), 200


@bp.route('/<job_id>/log-file-open', methods=['POST'])
@token_required
def log_file_open(job_id):
    """Stub endpoint for protocol handler touchpoint. Logs FileOpenedInSlicer.
    Body: { } (staff_name no longer required)
    """
    job = Job.query.get(job_id)
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
    job = Job.query.get(job_id)
    if not job:
        abort(404, description='Job not found')

    data = request.get_json(silent=True) or {}
    staff_name = data.get('staff_name')
    if not staff_name:
        return jsonify({'message': 'staff_name is required'}), 400
    staff = Staff.query.get(staff_name)
    if not staff or not staff.is_active:
        return jsonify({'message': 'Invalid or inactive staff_name'}), 400

    if 'notes' not in data:
        return jsonify({'message': 'notes field is required'}), 400
    notes_val = data.get('notes')
    if not isinstance(notes_val, str):
        return jsonify({'message': 'notes must be a string'}), 400
    if len(notes_val) > 5000:
        return jsonify({'message': 'notes must be at most 5000 characters'}), 400

    job.notes = notes_val
    job.last_updated_by = staff_name
    db.session.add(job)
    db.session.commit()

    # Log event with length only (avoid storing full notes in event log)
    evt = Event(
        job_id=job.id,
        event_type='NotesUpdated',
        details={'notes_len': len(notes_val)},
        triggered_by=staff_name,
        workstation_id=getattr(g, 'workstation_id', None),
    )
    db.session.add(evt)
    db.session.commit()

    return jsonify(job.to_dict()), 200

@bp.route('/<job_id>', methods=['DELETE'])
@token_required
def delete_job(job_id):
    job = Job.query.get(job_id)
    if not job:
        abort(404, description='Job not found')
    # Allow soft-delete primarily for early statuses; keep guard as-is for now
    if job.status not in ('UPLOADED', 'PENDING'):
        return jsonify({'message': 'Job cannot be deleted in its current status'}), 403
    before = job.status
    job.status = 'ARCHIVED'
    # Move file/metadata to Archived and sync metadata
    move_authoritative(job, 'ARCHIVED')
    db.session.add(job)
    db.session.commit()
    # Log event
    evt = Event(job_id=job.id, event_type='JobArchived', details={'from': before, 'to': 'ARCHIVED'}, triggered_by=getattr(g, 'workstation_id', 'system'), workstation_id=getattr(g, 'workstation_id', 'system'))
    db.session.add(evt)
    db.session.commit()
    _sync_authoritative_metadata(job, Path(job.file_path).name, None, 'JobArchived')
    return jsonify(job.to_dict()), 200


@bp.route('/<job_id>/hard-delete', methods=['POST'])
@token_required
def hard_delete_job(job_id):
    job = Job.query.get(job_id)
    if not job:
        abort(404, description='Job not found')
    data = request.get_json(silent=True) or {}
    staff_name = (data.get('staff_name') or '').strip()
    if not staff_name:
        return jsonify({'message': 'staff_name is required'}), 400
    # Best-effort remove files
    try:
        p = Path(job.file_path)
        if p.exists():
            p.unlink(missing_ok=True)
        mp = Path(job.metadata_path) if getattr(job, 'metadata_path', None) else None
        if mp and mp.exists():
            mp.unlink(missing_ok=True)
    except Exception:
        pass
    db.session.delete(job)
    db.session.commit()
    evt = Event(job_id=job_id, event_type='JobHardDeleted', details={}, triggered_by=staff_name, workstation_id=getattr(g, 'workstation_id', 'system'))
    db.session.add(evt)
    db.session.commit()
    return jsonify({'message': 'deleted'}), 200


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
        
        job = lifecycle_service.approve_job(job_id, approval_data)
        return ResponseService.success(job.to_dict())
        
    except ValueError as e:
        return ResponseService.error(str(e))


@bp.route('/<job_id>/notes', methods=['POST'])
@token_required
def append_note(job_id):
    job = Job.query.get(job_id)
    if not job:
        abort(404, description='Job not found')

    data = request.get_json(silent=True) or {}
    staff_name = (data.get('staff_name') or '').strip()
    if not staff_name:
        return jsonify({'message': 'staff_name is required'}), 400
    staff = Staff.query.get(staff_name)
    if not staff or not staff.is_active:
        return jsonify({'message': 'Invalid or inactive staff_name'}), 400

    text = data.get('text')
    if not isinstance(text, str):
        return jsonify({'message': 'text must be a string'}), 400
    text = text.strip()
    if not text:
        return jsonify({'message': 'text is required'}), 400

    per_entry_limit = 1000
    total_limit = 5000
    if len(text) > per_entry_limit:
        return jsonify({'message': f'text must be at most {per_entry_limit} characters'}), 400

    # Build the new line to append
    new_line = f"{staff_name} - {text}"
    current = job.notes or ''
    # Compute resulting total length with newline if needed
    separator = ('\n' if current else '')
    proposed = current + separator + new_line
    if len(proposed) > total_limit:
        return jsonify({'message': 'total notes length exceeded'}), 400

    job.notes = proposed
    job.last_updated_by = staff_name
    db.session.add(job)
    db.session.commit()

    evt = Event(
        job_id=job.id,
        event_type='NoteAdded',
        details={'text_len': len(text)},
        triggered_by=staff_name,
        workstation_id=getattr(g, 'workstation_id', None),
    )
    db.session.add(evt)
    db.session.commit()

    return jsonify(job.to_dict()), 200

def _validate_staff_and_body(data):
    staff_name = data.get('staff_name')
    if not staff_name:
        return None, jsonify({'message': 'staff_name is required'}), 400
    staff = Staff.query.get(staff_name)
    if not staff or not staff.is_active:
        return None, jsonify({'message': 'Invalid or inactive staff_name'}), 400
    return staff_name, None, None


# Duplicate update_notes route removed (consolidated above)


@bp.route('/<job_id>/mark-printing', methods=['POST'])
@token_required
def mark_printing(job_id):
    data = request.get_json(silent=True) or {}
    staff_name, err_resp, err_code = _validate_staff_and_body(data)
    if err_resp:
        return err_resp, err_code
    
    try:
        from app.services.job_lifecycle_service import JobStatusTransitionData
        transition_data = JobStatusTransitionData(staff_name=staff_name)
        job = lifecycle_service.mark_printing(job_id, transition_data)
        return ResponseService.success(job.to_dict())
    except ValueError as e:
        return ResponseService.error(str(e))


# --- Admin Overrides ---

def _validate_reason(data):
    reason = (data.get('reason') or '').strip()
    if not reason:
        return None, jsonify({'message': 'reason is required'}), 400
    return reason, None, None


@bp.route('/<job_id>/admin/force-unlock', methods=['POST'])
@token_required
def admin_force_unlock(job_id):
    job = Job.query.get(job_id)
    if not job:
        abort(404, description='Job not found')
    data = request.get_json(silent=True) or {}
    staff_name, err_resp, err_code = _validate_staff_and_body(data)
    if err_resp:
        return err_resp, err_code
    reason, err_resp, err_code = _validate_reason(data)
    if err_resp:
        return err_resp, err_code
    # No lock fields yet; log action for audit
    evt = Event(
        job_id=job.id,
        event_type='AdminAction',
        details={'action': 'force_unlock', 'reason': reason, 'note': 'No server-side lock fields present'},
        triggered_by=staff_name,
        workstation_id=g.workstation_id,
    )
    db.session.add(evt)
    db.session.commit()
    return jsonify({'message': 'unlock processed', 'lock_support': 'not_implemented'}), 200


@bp.route('/<job_id>/admin/force-confirm', methods=['POST'])
@token_required
def admin_force_confirm(job_id):
    data = request.get_json(silent=True) or {}
    staff_name, err_resp, err_code = _validate_staff_and_body(data)
    if err_resp:
        return err_resp, err_code
    reason, err_resp, err_code = _validate_reason(data)
    if err_resp:
        return err_resp, err_code
    
    try:
        from app.services.job_lifecycle_service import JobStatusTransitionData
        transition_data = JobStatusTransitionData(staff_name=staff_name, reason=reason)
        job = lifecycle_service.admin_force_confirm(job_id, transition_data)
        return ResponseService.success(job.to_dict())
    except ValueError as e:
        return ResponseService.error(str(e))


@bp.route('/<job_id>/admin/change-status', methods=['POST'])
@token_required
def admin_change_status(job_id):
    job = Job.query.get(job_id)
    if not job:
        abort(404, description='Job not found')
    data = request.get_json(silent=True) or {}
    staff_name, err_resp, err_code = _validate_staff_and_body(data)
    if err_resp:
        return err_resp, err_code
    reason, err_resp, err_code = _validate_reason(data)
    if err_resp:
        return err_resp, err_code
    new_status = (data.get('new_status') or '').strip().upper()
    if not new_status:
        return jsonify({'message': 'new_status is required'}), 400
    allowed_statuses = set(list(STATUS_TO_DIR.keys()) + ['REJECTED'])
    if new_status not in allowed_statuses:
        return jsonify({'message': 'Invalid new_status'}), 400
    before = job.status
    job.status = new_status
    job.last_updated_by = staff_name
    # Move files only if mapping exists for the target status
    if new_status in STATUS_TO_DIR:
        move_authoritative(job, new_status)
    db.session.add(job)
    db.session.commit()
    # Log events
    evt = Event(job_id=job.id, event_type='AdminStatusChanged', details={'from': before, 'to': new_status, 'reason': reason}, triggered_by=staff_name, workstation_id=g.workstation_id)
    db.session.add(evt)
    db.session.commit()
    evt2 = Event(job_id=job.id, event_type='AdminAction', details={'action': 'change_status', 'from': before, 'to': new_status, 'reason': reason}, triggered_by=staff_name, workstation_id=g.workstation_id)
    db.session.add(evt2)
    db.session.commit()
    return jsonify(job.to_dict()), 200


@bp.route('/<job_id>/admin/resend-email', methods=['POST'])
@token_required
@limiter.limit("1 per hour")
def admin_resend_email(job_id):
    job = Job.query.get(job_id)
    if not job:
        abort(404, description='Job not found')
    data = request.get_json(silent=True) or {}
    staff_name, err_resp, err_code = _validate_staff_and_body(data)
    if err_resp:
        return err_resp, err_code
    if job.student_confirmed:
        return jsonify({'message': 'Job already confirmed'}), 400

    # Generate fresh token and send approval email
    token = generate_confirmation_token(job.id)
    frontend_url = os.environ.get('FRONTEND_PUBLIC_URL', 'http://localhost:3000')
    confirmation_url = f"{frontend_url}/confirm/{token}"
    sent = False
    try:
        send_approval_email(job, confirmation_url)
        sent = True
    except Exception:
        sent = False

    # Update last sent timestamp
    try:
        job.confirmation_last_sent_at = datetime.utcnow()
        db.session.add(job)
        db.session.commit()
    except Exception:
        pass

    # Log events with staff attribution
    evt1 = Event(
        job_id=job.id,
        event_type='ApprovalEmailResentByStaff',
        details={'confirmation_url': confirmation_url, 'sent': bool(sent)},
        triggered_by=staff_name,
        workstation_id=getattr(g, 'workstation_id', None),
    )
    db.session.add(evt1)
    db.session.commit()

    # Also record a generic admin action for audit grouping
    evt2 = Event(
        job_id=job.id,
        event_type='AdminAction',
        details={'action': 'resend_email'},
        triggered_by=staff_name,
        workstation_id=getattr(g, 'workstation_id', None),
    )
    db.session.add(evt2)
    db.session.commit()

    return jsonify({'message': 'Confirmation email resent', 'job_id': job.id}), 200

@bp.route('/<job_id>/admin/mark-failed', methods=['POST'])
@token_required
def admin_mark_failed(job_id):
    data = request.get_json(silent=True) or {}
    staff_name, err_resp, err_code = _validate_staff_and_body(data)
    if err_resp:
        return err_resp, err_code
    reason, err_resp, err_code = _validate_reason(data)
    if err_resp:
        return err_resp, err_code
    
    try:
        from app.services.job_lifecycle_service import JobStatusTransitionData
        transition_data = JobStatusTransitionData(staff_name=staff_name, reason=reason)
        job = lifecycle_service.mark_failed(job_id, transition_data)
        return ResponseService.success(job.to_dict())
    except ValueError as e:
        return ResponseService.error(str(e))


@bp.route('/<job_id>/mark-complete', methods=['POST'])
@token_required
def mark_complete(job_id):
    data = request.get_json(silent=True) or {}
    staff_name, err_resp, err_code = _validate_staff_and_body(data)
    if err_resp:
        return err_resp, err_code
    
    try:
        from app.services.job_lifecycle_service import JobStatusTransitionData
        transition_data = JobStatusTransitionData(staff_name=staff_name)
        job = lifecycle_service.mark_complete(job_id, transition_data)
        return ResponseService.success(job.to_dict())
    except ValueError as e:
        return ResponseService.error(str(e))


@bp.route('/<job_id>/mark-picked-up', methods=['POST'])
@token_required
def mark_picked_up(job_id):
    data = request.get_json(silent=True) or {}
    staff_name, err_resp, err_code = _validate_staff_and_body(data)
    if err_resp:
        return err_resp, err_code
    
    try:
        from app.services.job_lifecycle_service import JobStatusTransitionData
        transition_data = JobStatusTransitionData(staff_name=staff_name)
        job = lifecycle_service.mark_picked_up(job_id, transition_data)
        return ResponseService.success(job.to_dict())
    except ValueError as e:
        return ResponseService.error(str(e))


@bp.route('/<job_id>/payment', methods=['POST'])
@token_required
def record_payment(job_id):
    job = Job.query.get(job_id)
    if not job:
        abort(404, description='Job not found')
    if job.status != 'COMPLETED':
        return jsonify({'message': 'Job must be in COMPLETED to record payment'}), 400

    data = request.get_json(silent=True) or {}
    staff_name, err_resp, err_code = _validate_staff_and_body(data)
    if err_resp:
        return err_resp, err_code

    try:
        grams = float(data.get('grams'))
    except (TypeError, ValueError):
        return jsonify({'message': 'grams must be a number'}), 400
    txn_no = (data.get('txn_no') or '').strip()
    picked_up_by = (data.get('picked_up_by') or '').strip()
    if grams <= 0 or not txn_no or not picked_up_by:
        return jsonify({'message': 'grams > 0, txn_no and picked_up_by are required'}), 400

    # Compute final price from actual pickup weight (grams) with material-specific rate and $3 minimum
    # Note: job.cost_usd is the estimate from approval; actual price is calculated from pickup weight
    material_rate = 0.20 if (job.material or '').lower() == 'resin' else 0.10
    raw_cost = grams * material_rate
    final_cost = max(3.0, raw_cost)  # $3.00 minimum charge
    price_cents = int(Decimal(str(final_cost)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) * 100)

    payment = Payment(
        job_id=job.id,
        grams=grams,
        price_cents=price_cents,
        txn_no=txn_no,
        picked_up_by=picked_up_by,
        paid_by_staff=staff_name,
    )
    db.session.add(payment)

    # Transition to PAIDPICKEDUP
    job.status = 'PAIDPICKEDUP'
    job.last_updated_by = staff_name
    # Move file/metadata to PaidPickedUp
    move_authoritative(job, 'PAIDPICKEDUP')
    db.session.add(job)
    db.session.commit()

    evt = Event(job_id=job.id, event_type='PaymentRecorded', details={'price_cents': price_cents}, triggered_by=staff_name, workstation_id=g.workstation_id)
    db.session.add(evt)
    db.session.commit()
    _sync_authoritative_metadata(job, Path(job.file_path).name, staff_name, 'PaymentRecorded')
    return jsonify(job.to_dict()), 200


@bp.route('/<job_id>/review', methods=['POST'])
@token_required
def review_job(job_id):
    job = Job.query.get(job_id)
    if not job:
        abort(404, description='Job not found')

    # Only allow review state on UPLOADED jobs
    if job.status != 'UPLOADED':
        return jsonify({'message': 'Job review state can only be changed in UPLOADED status'}), 400

    data = request.get_json(silent=True) or {}
    staff_name = data.get('staff_name')
    reviewed = data.get('reviewed')

    if staff_name is None:
        return jsonify({'message': 'staff_name is required'}), 400

    staff = Staff.query.get(staff_name)
    if not staff or not staff.is_active:
        return jsonify({'message': 'Invalid or inactive staff_name'}), 400

    if not isinstance(reviewed, bool):
        return jsonify({'message': 'reviewed must be a boolean'}), 400

    # Apply state change
    if reviewed:
        job.staff_viewed_at = datetime.utcnow()
        event_type = 'JobReviewed'
    else:
        job.staff_viewed_at = None
        event_type = 'JobReviewCleared'

    job.last_updated_by = staff_name
    db.session.add(job)
    db.session.commit()

    # Log event with attribution
    evt = Event(
        job_id=job.id,
        event_type=event_type,
        details={},
        triggered_by=staff_name,
        workstation_id=g.workstation_id,
    )
    db.session.add(evt)
    db.session.commit()

    return jsonify(job.to_dict()), 200


@bp.route('/<job_id>/reject', methods=['POST'])
@token_required
def reject_job(job_id):
    job = Job.query.get(job_id)
    if not job:
        abort(404, description='Job not found')

    if job.status != 'UPLOADED':
        return jsonify({'message': 'Job cannot be rejected in its current status'}), 400

    data = request.get_json(silent=True) or {}
    staff_name = data.get('staff_name')
    reasons = data.get('reasons') or []
    custom_reason = (data.get('custom_reason') or '').strip()

    if not staff_name:
        return jsonify({'message': 'staff_name is required'}), 400
    staff = Staff.query.get(staff_name)
    if not staff or not staff.is_active:
        return jsonify({'message': 'Invalid or inactive staff_name'}), 400

    # Normalize reasons
    if not isinstance(reasons, list):
        return jsonify({'message': 'reasons must be an array of strings'}), 400
    reasons = [str(r) for r in reasons if str(r).strip()]
    if custom_reason:
        reasons.append(custom_reason)
    if not reasons:
        return jsonify({'message': 'At least one reason or a custom_reason is required'}), 400

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

    return jsonify(job.to_dict()), 200


@bp.route('/<job_id>/revert-completion', methods=['POST'])
@token_required
def revert_completion(job_id):
    data = request.get_json(silent=True) or {}
    staff_name, err_resp, err_code = _validate_staff_and_body(data)
    if err_resp:
        return err_resp, err_code
    
    try:
        from app.services.job_lifecycle_service import JobStatusTransitionData
        transition_data = JobStatusTransitionData(staff_name=staff_name)
        job = lifecycle_service.revert_to_printing(job_id, transition_data)
        return ResponseService.success(job.to_dict())
    except ValueError as e:
        return ResponseService.error(str(e))


@bp.route('/<job_id>/revert-pickup', methods=['POST'])
@token_required
def revert_pickup(job_id):
    data = request.get_json(silent=True) or {}
    staff_name, err_resp, err_code = _validate_staff_and_body(data)
    if err_resp:
        return err_resp, err_code
    
    try:
        from app.services.job_lifecycle_service import JobStatusTransitionData
        transition_data = JobStatusTransitionData(staff_name=staff_name)
        job = lifecycle_service.revert_to_completed(job_id, transition_data)
        return ResponseService.success(job.to_dict())
    except ValueError as e:
        return ResponseService.error(str(e))

@bp.route('/<job_id>/lock', methods=['POST'])
@token_required
def lock_job(job_id):
    job = Job.query.get(job_id)
    if not job:
        abort(404, description='Job not found')
    now = datetime.utcnow()
    if job.locked_by and job.locked_until and job.locked_until > now:
        return jsonify(job.to_dict()), 409
    job.locked_by = g.workstation_id
    job.locked_until = now + timedelta(minutes=5)
    db.session.commit()
    return jsonify(job.to_dict()), 200

@bp.route('/<job_id>/unlock', methods=['POST'])
@token_required
def unlock_job(job_id):
    job = Job.query.get(job_id)
    if not job:
        abort(404, description='Job not found')
    if job.locked_by != g.workstation_id:
        return jsonify({'message': 'Not lock owner'}), 403
    job.locked_by = None
    job.locked_until = None
    db.session.commit()
    return jsonify(job.to_dict()), 200

@bp.route('/<job_id>/extend', methods=['POST'])
@token_required
def extend_job_lock(job_id):
    job = Job.query.get(job_id)
    if not job:
        abort(404, description='Job not found')
    if job.locked_by != g.workstation_id:
        return jsonify({'message': 'Not lock owner'}), 403
    job.locked_until = datetime.utcnow() + timedelta(minutes=5)
    db.session.commit()
    return jsonify(job.to_dict()), 200