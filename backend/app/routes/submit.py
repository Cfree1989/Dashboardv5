from flask import Blueprint, request, jsonify, abort
from app import db, limiter
from app.models.job import Job
import os, hashlib, json
from datetime import datetime
from uuid import uuid4
from pathlib import Path
from app.business_logic.shared_services import event_service
from app.business_logic.shared_services import email_service
from app.business_logic.shared_services import token_service
from app.services.infrastructure.atomic_file_service import get_atomic_file_service
from app.routes.jobs import _sync_authoritative_metadata
from app.business_logic.shared_services.catalog_service import CatalogService
from app.business_logic.shared_services.error_handling_service import get_error_handling_service
from app.services.infrastructure.file_configuration_service import get_file_configuration_service
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('submit', __name__, url_prefix='/api/v1/submit')

# Get file configuration service instance
file_config = get_file_configuration_service()


def allowed_file(filename):
    return file_config.is_allowed_extension(filename)


def _normalize_name_for_filename(name: str) -> str:
    # Remove non-alphanumerics, collapse spaces, PascalCase words
    parts = [p for p in name.strip().replace('_', ' ').split() if p]
    joined = ''.join(w.capitalize() for w in parts)
    # Keep only alphanumerics
    return ''.join(ch for ch in joined if ch.isalnum()) or 'Student'


def _normalize_simple_label(value: str) -> str:
    # Convert to TitleCase words and remove spaces
    parts = [p for p in value.strip().replace('_', ' ').split() if p]
    labeled = ''.join(w.capitalize() for w in parts)
    return ''.join(ch for ch in labeled if ch.isalnum()) or 'Value'


@bp.route('', methods=['POST'])
@limiter.limit("5 per hour")
def submit_job():
    try:
        # Validate file presence
        if 'file' not in request.files:
            return jsonify({'error': 'file is required'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'no file selected'}), 400
        if not allowed_file(file.filename):
            return jsonify({'error': 'invalid file type'}), 400
        if request.content_length and not file_config.validate_file_size(request.content_length):
            return jsonify({'error': f'file too large (max {file_config.max_file_size_mb}MB)'}), 413

        # Read file for hash and saving
        file_bytes = file.read()
        file_hash = hashlib.sha256(file_bytes).hexdigest()

        # Duplicate detection in active statuses (only select id, avoid extra columns)
        active_statuses = ['UPLOADED', 'PENDING', 'READYTOPRINT']
        existing_record = db.session.query(Job.id).filter(
            Job.file_hash == file_hash,
            Job.student_email == request.form.get('student_email'),
            Job.status.in_(active_statuses)
        ).first()
        existing = existing_record[0] if existing_record else None
        if existing:
            return jsonify({'message': 'duplicate active job exists', 'existing_job_id': existing}), 409

        # Prepare storage directory
        # Use STORAGE_PATH root and ensure status subdir
        storage_root = os.environ.get('STORAGE_PATH', 'storage')
        storage_dir = os.path.join(storage_root, 'Uploaded')
        os.makedirs(storage_dir, exist_ok=True)

        # Generate job ID and standardized filenames
        new_id = uuid4().hex
        # Generate a human-friendly short id (ensure uniqueness by retrying with more chars if needed)
        for length in (6, 7, 8, 9, 10, 11, 12):
            candidate_short = new_id[:length]
            # Check only id to avoid selecting newly-added lock columns
            existing_short = db.session.query(Job.id).filter_by(short_id=candidate_short).first()
            if not existing_short:
                short_id = candidate_short
                break
        else:
            short_id = new_id[:12]
        ext = file.filename.rsplit('.', 1)[1].lower()
        # Determine student name: prefer single field, else combine first/last
        student_name = request.form.get('student_name')
        if not student_name:
            first_name = request.form.get('student_first_name')
            last_name = request.form.get('student_last_name')
            student_name = f"{first_name or ''} {last_name or ''}".strip()
        normalized_student = _normalize_name_for_filename(student_name or 'Student')

        # Derive print method/material and color
        raw_method = request.form.get('print_method') or ''
        raw_material = request.form.get('material') or ''
        raw_color = request.form.get('color') or ''
        raw_printer = request.form.get('printer') or ''
        normalized_method = _normalize_simple_label(raw_method or 'Method')
        normalized_color = _normalize_simple_label(raw_color or 'Color')
        
        # Validate job configuration against catalog
        is_valid, validation_errors = CatalogService.validate_job_configuration(
            method=raw_method,
            material=raw_material,
            color=raw_color,
            printer=raw_printer
        )
        
        if not is_valid:
            return jsonify({
                'error': 'Invalid job configuration',
                'details': validation_errors
            }), 400

        # Short/simple Job ID
        simple_id = short_id
        standardized_base = f"{normalized_student}_{normalized_method}_{normalized_color}_{simple_id}"
        standardized_name = f"{standardized_base}.{ext}"
        file_path = os.path.join(storage_dir, standardized_name)

        # Save file (ensure unique by appending counter if exists)
        base_name = standardized_base
        candidate_name = standardized_name
        candidate_path = file_path
        counter = 1
        while os.path.exists(candidate_path):
            candidate_name = f"{base_name}_{counter}.{ext}"
            candidate_path = os.path.join(storage_dir, candidate_name)
            counter += 1
        with open(candidate_path, 'wb') as out_f:
            out_f.write(file_bytes)

        # Create metadata JSON
        from pathlib import Path as _P
        metadata = {
            'student_name': student_name,
            'student_email': request.form.get('student_email'),
            'discipline': request.form.get('discipline'),
            'class_number': request.form.get('class_number'),
            'printer': request.form.get('printer'),
            'color': raw_color,
            'material': raw_method,
            'status': 'UPLOADED',
            'display_name': candidate_name,
            'authoritative_filename': candidate_name,
            'file_path': str(_P(candidate_path).resolve()),
            'created_at': datetime.utcnow().isoformat()
        }
        metadata_base = base_name if counter == 1 else f"{base_name}_{counter-1}"
        metadata_path = os.path.join(storage_dir, f"{metadata_base}_metadata.json")
        with open(metadata_path, 'w') as meta_f:
            json.dump(metadata, meta_f)

        # Persist job record
        job = Job(
            id=new_id,
            short_id=short_id,
            student_name=student_name,
            student_email=request.form.get('student_email'),
            discipline=request.form.get('discipline'),
            class_number=request.form.get('class_number'),
            original_filename=file.filename,
            display_name=candidate_name,
            file_path=str(Path(candidate_path).resolve()),
            metadata_path=str(Path(metadata_path).resolve()),
            file_hash=file_hash,
            printer=request.form.get('printer'),
            color=raw_color,
            material=raw_method
        )
        db.session.add(job)
        db.session.commit()

        # Event logging
        event_service.log_event('JobCreated', {'original_filename': job.original_filename}, job_id=job.id)

        # Fire-and-forget best-effort submission confirmation email
        try:
            send_submission_confirmation_email(job)
        except Exception as e:
            error_service = get_error_handling_service()
            error_service.log_file_operation_error(
                operation="send_submission_confirmation_email",
                error=e,
                job_id=str(job.id),
                context={'email_type': 'submission_confirmation'}
            )
            logger.warning(f"Failed to send submission confirmation email for job {job.id}: {e}")

        return jsonify(job.to_dict()), 201
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Job submission failed: {str(e)}\n{tb}")
        return jsonify({'error': str(e)}), 500 


@bp.route('/confirm/<token>', methods=['POST'])
def confirm_job(token: str):
    try:
        job_id = verify_confirmation_token(token)
    except ValueError as ve:
        reason = str(ve)
        if reason == 'expired':
            return jsonify({'message': 'Confirmation link expired', 'reason': 'expired'}), 410
        return jsonify({'message': 'Invalid confirmation token'}), 400

    job = Job.query.get(job_id)
    if not job:
        return jsonify({'message': 'Job not found'}), 404

    # Transition to READYTOPRINT + move file/metadata
    job.student_confirmed = True
    job.status = 'READYTOPRINT'
    
    # Use atomic file operations
    atomic_service = get_atomic_file_service()
    success = atomic_service.atomic_move_authoritative(job, 'READYTOPRINT')
    if not success:
        return jsonify({'message': 'File operation failed during confirmation'}), 500
    
    db.session.commit()
    
    # Sync metadata to reflect authoritative file and new status
    error_service = get_error_handling_service()
    try:
        _sync_authoritative_metadata(job, Path(job.file_path).name, None, 'StudentConfirmed')
    except Exception as e:
        error_service.log_metadata_sync_error(
            error=e,
            job_id=str(job.id),
            metadata_path=getattr(job, 'metadata_path', 'unknown'),
            context={'operation': 'confirm_job_metadata_sync'}
        )
        logger.warning(f"Failed to sync metadata during job confirmation for job {job.id}: {e}")
        # Non-fatal: do not block confirmation on metadata issues
    
    event_service.log_event('StudentConfirmed', {'status': job.status}, job_id=job.id)
    return jsonify(job.to_dict()), 200


@bp.route('/resend-confirmation', methods=['POST'])
@limiter.limit("1 per hour")
def resend_confirmation():
    """Resend approval confirmation email. Accepts JSON body with either 'token' (preferred) or 'job_id'."""
    data = request.get_json(silent=True) or {}
    token = (data.get('token') or '').strip()
    job_id = (data.get('job_id') or '').strip()

    if not token and not job_id:
        return jsonify({'message': 'token or job_id is required'}), 400

    # Resolve job_id from token if provided, ignoring expiration
    if token:
        try:
            payload = _serializer().loads(token)  # no max_age -> ignore expiration
            job_id = payload.get('job_id')
        except Exception:
            return jsonify({'message': 'Invalid token'}), 400

    job = Job.query.get(job_id)
    if not job:
        return jsonify({'message': 'Job not found'}), 404

    if job.student_confirmed:
        return jsonify({'message': 'Job already confirmed'}), 400

    # Generate fresh token and send email
    new_token = generate_confirmation_token(job.id)
    frontend_url = os.environ.get('FRONTEND_PUBLIC_URL', 'http://localhost:3000')
    confirmation_url = f"{frontend_url}/confirm/{new_token}"

    # Attempt send; do not fail the endpoint if email not configured
    sent = False
    error_service = get_error_handling_service()
    try:
        sent = send_approval_email(job, confirmation_url)
    except Exception as e:
        error_service.log_file_operation_error(
            operation="send_approval_email",
            error=e,
            job_id=str(job.id),
            context={'email_type': 'approval', 'confirmation_url': confirmation_url}
        )
        logger.warning(f"Failed to send approval email for job {job.id}: {e}")
        sent = False

    # Log events
    event_service.log_event('ResendConfirmationRequested', {'via': 'token' if token else 'job_id'}, job_id=job.id)
    event_service.log_event('ApprovalEmailResent', {'confirmation_url': confirmation_url, 'sent': bool(sent)}, job_id=job.id)

    # Update last sent timestamp
    try:
        job.confirmation_last_sent_at = datetime.utcnow()
        db.session.commit()
    except Exception as e:
        error_service.log_file_operation_error(
            operation="update_confirmation_timestamp",
            error=e,
            job_id=str(job.id),
            context={'operation': 'update_confirmation_timestamp'}
        )
        logger.warning(f"Failed to update confirmation timestamp for job {job.id}: {e}")

    return jsonify({'message': 'Confirmation email resent', 'job_id': job.id}), 200