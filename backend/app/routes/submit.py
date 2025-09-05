from flask import Blueprint, request, jsonify, abort
from app import db, limiter
from app.models.job import Job
from app.business_logic.shared_services.response_service import ResponseService
from app.services.orchestration.job_orchestration_service import JobOrchestrationService
from app.business_logic.job_lifecycle.job_submission_data import JobSubmissionData, JobConfirmationData, JobResendConfirmationData
import os, hashlib, json
from datetime import datetime
from uuid import uuid4
from pathlib import Path
from app.business_logic.shared_services import event_service
from app.business_logic.shared_services import email_service
from app.business_logic.shared_services import token_service
from app.business_logic.shared_services.email_service import send_submission_confirmation_email, send_approval_email
from app.business_logic.shared_services.token_service import generate_confirmation_token, verify_confirmation_token, _serializer
from app.services.infrastructure.atomic_file_service import get_atomic_file_service
from app.routes.jobs import _sync_authoritative_metadata
from app.business_logic.shared_services.catalog_service import CatalogService
from app.business_logic.shared_services.error_handling_service import get_error_handling_service
from app.services.infrastructure.file_configuration_service import get_file_configuration_service
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('submit', __name__, url_prefix='/api/v1/submit')

# Get service instances
file_config = get_file_configuration_service()
orchestration_service = JobOrchestrationService()


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
@limiter.limit("100 per minute")
def submit_job():
    try:
        # Validate file presence
        if 'file' not in request.files:
            return ResponseService.validation_error('file is required')
        file = request.files['file']
        if file.filename == '':
            return ResponseService.validation_error('no file selected')
        
        # Enhanced file validation
        # 1. Validate filename security
        is_valid_filename, filename_error = file_config.validate_filename_security(file.filename)
        if not is_valid_filename:
            return ResponseService.validation_error(f'Invalid filename: {filename_error}')
        
        # 2. Validate file extension
        if not allowed_file(file.filename):
            return ResponseService.validation_error('Invalid file type')
        
        # 3. Validate file size
        if request.content_length:
            size_error = file_config.get_file_size_validation_error(request.content_length)
            if size_error:
                return ResponseService.validation_error(size_error, status=413)

        # Read file for hash and saving
        file_bytes = file.read()
        file_hash = hashlib.sha256(file_bytes).hexdigest()
        
        # 4. Validate file header (content validation)
        is_valid_header, header_error = file_config.validate_file_header(file_bytes, file.filename)
        if not is_valid_header:
            return ResponseService.validation_error(f'Invalid file content: {header_error}')

        # Duplicate detection in active statuses (only select id, avoid extra columns)
        active_statuses = ['UPLOADED', 'PENDING', 'READYTOPRINT']
        existing_record = db.session.query(Job.id).filter(
            Job.file_hash == file_hash,
            Job.student_email == request.form.get('student_email'),
            Job.status.in_(active_statuses)
        ).first()
        existing = existing_record[0] if existing_record else None
        if existing:
            return ResponseService.conflict('duplicate active job exists', {'existing_job_id': existing})

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
            return ResponseService.validation_error('Invalid job configuration', {'details': validation_errors})

        # Create job using orchestration service
        candidate_name = f"{normalized_student}_{normalized_method}_{normalized_color}"
        job = orchestration_service.create_job_from_form_data(
            file, request.form, file_bytes, file_hash, candidate_name
        )

        # Event logging is handled by orchestration service

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

        return ResponseService.success(job.to_dict(), status=201)
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Job submission failed: {str(e)}\n{tb}")
        return ResponseService.error(f'Job submission failed: {str(e)}', status=500) 


@bp.route('/confirm/<token>', methods=['POST'])
def confirm_job(token: str):
    try:
        # Use orchestration service for confirmation
        job = orchestration_service.confirm_job_by_token(token)
        return ResponseService.success(job.to_dict())
    except ValueError as ve:
        reason = str(ve)
        if reason == 'expired':
            return ResponseService.error('Confirmation link expired', status=410, data={'reason': 'expired'})
        return ResponseService.validation_error('Invalid confirmation token')
    except Exception as e:
        logger.error(f"Job confirmation failed: {str(e)}")
        return ResponseService.error('Job confirmation failed', status=500)


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

    job = orchestration_service.get_job_by_id(job_id)
    if not job:
        return ResponseService.not_found('Job not found')

    if job.student_confirmed:
        return ResponseService.validation_error('Job already confirmed')

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