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
from .job_utils import _validate_staff_and_body, _validate_reason, _sync_authoritative_metadata

logger = logging.getLogger(__name__)

bp = Blueprint('jobs', __name__, url_prefix='/api/v1/jobs')

# TODO: Implement job management routes 

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

@bp.route('/<job_id>/mark-printing', methods=['POST'])
@token_required
def mark_printing(job_id):
    job = Job.query.get(job_id)
    if not job:
        abort(404, description='Job not found')
    if job.status != 'READYTOPRINT':
        return jsonify({'message': 'Job must be in READYTOPRINT to mark printing'}), 400
    data = request.get_json(silent=True) or {}
    staff_name, err_resp, err_code = _validate_staff_and_body(data)
    if err_resp:
        return err_resp, err_code
    job.status = 'PRINTING'
    job.last_updated_by = staff_name
    # Move file/metadata to Printing
    move_authoritative(job, 'PRINTING')
    db.session.add(job)
    db.session.commit()
    evt = Event(job_id=job.id, event_type='JobMarkedPrinting', details={}, triggered_by=staff_name, workstation_id=g.workstation_id)
    db.session.add(evt)
    db.session.commit()
    _sync_authoritative_metadata(job, Path(job.file_path).name, staff_name, 'JobMarkedPrinting')
    return jsonify(job.to_dict()), 200


@bp.route('/<job_id>/mark-complete', methods=['POST'])
@token_required
def mark_complete(job_id):
    job = Job.query.get(job_id)
    if not job:
        abort(404, description='Job not found')
    if job.status != 'PRINTING':
        return jsonify({'message': 'Job must be in PRINTING to mark complete'}), 400
    data = request.get_json(silent=True) or {}
    staff_name, err_resp, err_code = _validate_staff_and_body(data)
    if err_resp:
        return err_resp, err_code
    job.status = 'COMPLETED'
    job.last_updated_by = staff_name
    # Move file/metadata to Completed
    move_authoritative(job, 'COMPLETED')
    db.session.add(job)
    db.session.commit()
    evt = Event(job_id=job.id, event_type='JobMarkedComplete', details={}, triggered_by=staff_name, workstation_id=g.workstation_id)
    db.session.add(evt)
    db.session.commit()
    # Attempt completion email (best-effort)
    try:
        send_completion_email(job)
        email_evt = Event(job_id=job.id, event_type='CompletionEmailSent', details={}, triggered_by=staff_name, workstation_id=g.workstation_id)
        db.session.add(email_evt)
        db.session.commit()
    except Exception:
        pass
    _sync_authoritative_metadata(job, Path(job.file_path).name, staff_name, 'JobMarkedComplete')
    return jsonify(job.to_dict()), 200


@bp.route('/<job_id>/mark-picked-up', methods=['POST'])
@token_required
def mark_picked_up(job_id):
    job = Job.query.get(job_id)
    if not job:
        abort(404, description='Job not found')
    if job.status != 'COMPLETED':
        return jsonify({'message': 'Job must be in COMPLETED to mark picked up'}), 400
    data = request.get_json(silent=True) or {}
    staff_name, err_resp, err_code = _validate_staff_and_body(data)
    if err_resp:
        return err_resp, err_code
    job.status = 'PAIDPICKEDUP'
    job.last_updated_by = staff_name
    # Move file/metadata to PaidPickedUp
    move_authoritative(job, 'PAIDPICKEDUP')
    db.session.add(job)
    db.session.commit()
    evt = Event(job_id=job.id, event_type='JobMarkedPickedUp', details={}, triggered_by=staff_name, workstation_id=g.workstation_id)
    db.session.add(evt)
    db.session.commit()
    _sync_authoritative_metadata(job, Path(job.file_path).name, staff_name, 'JobMarkedPickedUp')
    return jsonify(job.to_dict()), 200


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
    job = Job.query.get(job_id)
    if not job:
        abort(404, description='Job not found')
    if job.status != 'COMPLETED':
        return jsonify({'message': 'Job must be in COMPLETED to revert to PRINTING'}), 400
    data = request.get_json(silent=True) or {}
    staff_name, err_resp, err_code = _validate_staff_and_body(data)
    if err_resp:
        return err_resp, err_code
    before = job.status
    job.status = 'PRINTING'
    job.last_updated_by = staff_name
    move_authoritative(job, 'PRINTING')
    db.session.add(job)
    db.session.commit()
    evt = Event(job_id=job.id, event_type='JobRevertedToPrinting', details={'from': before, 'to': 'PRINTING'}, triggered_by=staff_name, workstation_id=g.workstation_id)
    db.session.add(evt)
    db.session.commit()
    _sync_authoritative_metadata(job, Path(job.file_path).name, staff_name, 'JobRevertedToPrinting')
    return jsonify(job.to_dict()), 200


@bp.route('/<job_id>/revert-pickup', methods=['POST'])
@token_required
def revert_pickup(job_id):
    job = Job.query.get(job_id)
    if not job:
        abort(404, description='Job not found')
    if job.status != 'PAIDPICKEDUP':
        return jsonify({'message': 'Job must be in PAIDPICKEDUP to revert to COMPLETED'}), 400
    data = request.get_json(silent=True) or {}
    staff_name, err_resp, err_code = _validate_staff_and_body(data)
    if err_resp:
        return err_resp, err_code
    before = job.status
    job.status = 'COMPLETED'
    job.last_updated_by = staff_name
    move_authoritative(job, 'COMPLETED')
    db.session.add(job)
    db.session.commit()
    evt = Event(job_id=job.id, event_type='JobRevertedToCompleted', details={'from': before, 'to': 'COMPLETED'}, triggered_by=staff_name, workstation_id=g.workstation_id)
    db.session.add(evt)
    db.session.commit()
    _sync_authoritative_metadata(job, Path(job.file_path).name, staff_name, 'JobRevertedToCompleted')
    return jsonify(job.to_dict()), 200

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