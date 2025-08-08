from flask import Blueprint
from flask import request, jsonify, abort, g
from app import db
from app.models.job import Job
from app.utils.decorators import token_required
from app.models.event import Event
from app.models.payment import Payment
from app.services.token_service import generate_confirmation_token
from app.services.email_service import send_approval_email
from app.services.event_service import log_event
from app.models.staff import Staff
from datetime import datetime
import json
import os
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP

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


# --- Metadata helpers ---
def _load_metadata(job: Job) -> dict:
    try:
        with open(job.metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _save_metadata(job: Job, data: dict) -> None:
    try:
        meta_path = Path(job.metadata_path)
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception:
        # Non-fatal: metadata sync should not block workflow
        pass


def _sync_authoritative_metadata(job: Job, authoritative_filename: str, staff_name: str | None, event_type: str) -> None:
    try:
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
    except Exception:
        # Non-fatal
        pass

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
    events = job.events
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
        candidates.sort(key=lambda x: (_rank(x['name']), -x['mtime']))
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
    Body: { "staff_name": "Optional Staff" }
    """
    job = Job.query.get(job_id)
    if not job:
        abort(404, description='Job not found')
    data = request.get_json(silent=True) or {}
    staff_name = (data.get('staff_name') or '').strip() or None
    # Validate staff if provided; otherwise allow None to represent unknown
    if staff_name:
        staff = Staff.query.get(staff_name)
        if not staff or not staff.is_active:
            # Ignore invalid names in stub; do not block logging
            staff_name = None
    evt = Event(
        job_id=job.id,
        event_type='FileOpenedInSlicer',
        details={'file_path': job.file_path},
        triggered_by=staff_name,
        workstation_id=getattr(g, 'workstation_id', None),
    )
    db.session.add(evt)
    db.session.commit()
    return jsonify({'message': 'logged'}), 200

@bp.route('/<job_id>', methods=['DELETE'])
@token_required
def delete_job(job_id):
    job = Job.query.get(job_id)
    if not job:
        abort(404, description='Job not found')
    if job.status not in ('UPLOADED', 'PENDING'):
        return jsonify({'message': 'Job cannot be deleted in its current status'}), 403
    db.session.delete(job)
    db.session.commit()
    return '', 204 


@bp.route('/<job_id>/approve', methods=['POST'])
@token_required
def approve_job(job_id):
    job = Job.query.get(job_id)
    if not job:
        abort(404, description='Job not found')

    if job.status != 'UPLOADED':
        return jsonify({'message': 'Job cannot be approved in its current status'}), 400

    # Parse and validate payload
    data = request.get_json(silent=True) or {}
    staff_name = data.get('staff_name')
    weight_g = data.get('weight_g')
    time_hours = data.get('time_hours')
    authoritative_filename = (data.get('authoritative_filename') or '').strip()

    if not staff_name:
        return jsonify({'message': 'staff_name is required'}), 400

    staff = Staff.query.get(staff_name)
    if not staff or not staff.is_active:
        return jsonify({'message': 'Invalid or inactive staff_name'}), 400

    # Validate numeric inputs
    try:
        weight_val = float(weight_g)
        time_val = float(time_hours)
    except (TypeError, ValueError):
        return jsonify({'message': 'weight_g and time_hours must be numbers'}), 400
    if weight_val <= 0 or time_val <= 0:
        return jsonify({'message': 'weight_g and time_hours must be greater than 0'}), 400

    # Determine material rate
    material = (job.material or '').strip().lower()
    if material == 'filament':
        rate = 0.10
    elif material == 'resin':
        rate = 0.20
    else:
        # Default to filament pricing if unknown, to avoid blocking
        rate = 0.10

    # Compute cost with minimum $3.00
    raw_cost = weight_val * rate
    min_cost = 3.00
    final_cost = max(raw_cost, min_cost)
    # Round to 2 decimals using bankers rounding to HALF_UP
    final_cost_decimal = Decimal(str(final_cost)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    # Update job fields
    job.weight_g = weight_val
    job.time_hours = time_val
    job.cost_usd = final_cost_decimal
    job.last_updated_by = staff_name
    # Mark as reviewed to clear "NEW" indicator across statuses
    job.staff_viewed_at = datetime.utcnow()
    # Optionally set authoritative file within same directory
    if authoritative_filename:
        try:
            current_dir = Path(job.file_path).parent
            candidate_path = (current_dir / authoritative_filename).resolve()
            # Guard: candidate must be inside the same directory
            if candidate_path.parent == current_dir and candidate_path.suffix.lower() in {'.stl', '.obj', '.3mf'}:
                job.file_path = str(candidate_path)
                job.display_name = authoritative_filename
        except Exception:
            pass
    job.status = 'PENDING'
    db.session.add(job)
    db.session.commit()

    # Generate confirmation token and send email
    token = generate_confirmation_token(job.id)
    base_url = request.host_url.rstrip('/')
    confirmation_url = f"{base_url}/confirm/{token}"
    send_approval_email(job, confirmation_url)

    # Log events with proper attribution
    log_event(job.id, 'StaffApproved', {
        'confirmation_url': confirmation_url,
        'weight_g': weight_val,
        'time_hours': time_val,
        'cost_usd': float(final_cost_decimal),
        'authoritative_filename': authoritative_filename or job.display_name,
    })
    log_event(job.id, 'ApprovalEmailSent', {})

    # Sync metadata with chosen authoritative file
    _sync_authoritative_metadata(job, authoritative_filename or job.display_name, staff_name, 'StaffApproved')

    return jsonify(job.to_dict()), 200


def _validate_staff_and_body(data):
    staff_name = data.get('staff_name')
    if not staff_name:
        return None, jsonify({'message': 'staff_name is required'}), 400
    staff = Staff.query.get(staff_name)
    if not staff or not staff.is_active:
        return None, jsonify({'message': 'Invalid or inactive staff_name'}), 400
    return staff_name, None, None


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
    db.session.add(job)
    db.session.commit()
    evt = Event(job_id=job.id, event_type='JobMarkedComplete', details={}, triggered_by=staff_name, workstation_id=g.workstation_id)
    db.session.add(evt)
    db.session.commit()
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

    # Compute price from job.cost_usd if present; fallback to grams at $0.10/g (min $3)
    if job.cost_usd is not None:
        price_cents = int(Decimal(str(float(job.cost_usd))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) * 100)
    else:
        raw_cost = max(3.0, grams * (0.20 if (job.material or '').lower() == 'resin' else 0.10))
        price_cents = int(Decimal(str(raw_cost)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) * 100)

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

    return jsonify(job.to_dict()), 200