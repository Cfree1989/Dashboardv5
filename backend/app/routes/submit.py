from flask import Blueprint, request, jsonify, abort
from app import db
from app.models.job import Job
import os, hashlib, json
from datetime import datetime
from uuid import uuid4
from app.services.event_service import log_event
from app.services.email_service import send_status_update_email, send_approval_email
from app.services.token_service import generate_confirmation_token, verify_confirmation_token

bp = Blueprint('submit', __name__, url_prefix='/api/v1/submit')

ALLOWED_EXTENSIONS = {'stl', 'obj', '3mf'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
        if request.content_length and request.content_length > MAX_FILE_SIZE:
            return jsonify({'error': 'file too large'}), 413

        # Read file for hash and saving
        file_bytes = file.read()
        file_hash = hashlib.sha256(file_bytes).hexdigest()

        # Duplicate detection in active statuses
        active_statuses = ['UPLOADED', 'PENDING', 'READYTOPRINT']
        existing = Job.query.filter(
            Job.file_hash == file_hash,
            Job.student_email == request.form.get('student_email'),
            Job.status.in_(active_statuses)
        ).first()
        if existing:
            return jsonify({'message': 'duplicate active job exists', 'existing_job_id': existing.id}), 409

        # Prepare storage directory
        storage_dir = os.environ.get('STORAGE_PATH', 'storage/Uploaded')
        os.makedirs(storage_dir, exist_ok=True)

        # Generate job ID and standardized filenames
        new_id = uuid4().hex
        ext = file.filename.rsplit('.', 1)[1].lower()
        # Determine student name: prefer single field, else combine first/last
        student_name = request.form.get('student_name')
        if not student_name:
            first_name = request.form.get('student_first_name')
            last_name = request.form.get('student_last_name')
            student_name = f"{first_name or ''} {last_name or ''}".strip()
        normalized_student = _normalize_name_for_filename(student_name or 'Student')

        # Derive print method/material and color
        raw_method = request.form.get('material') or request.form.get('print_method') or ''
        raw_color = request.form.get('color') or ''
        normalized_method = _normalize_simple_label(raw_method or 'Method')
        normalized_color = _normalize_simple_label(raw_color or 'Color')

        # Short/simple Job ID
        simple_id = new_id[:6]
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
        metadata = {
            'student_name': student_name,
            'student_email': request.form.get('student_email'),
            'discipline': request.form.get('discipline'),
            'class_number': request.form.get('class_number'),
            'printer': request.form.get('printer'),
            'color': raw_color,
            'material': raw_method,
            'status': 'UPLOADED',
            'created_at': datetime.utcnow().isoformat()
        }
        metadata_base = base_name if counter == 1 else f"{base_name}_{counter-1}"
        metadata_path = os.path.join(storage_dir, f"{metadata_base}_metadata.json")
        with open(metadata_path, 'w') as meta_f:
            json.dump(metadata, meta_f)

        # Persist job record
        job = Job(
            id=new_id,
            student_name=student_name,
            student_email=request.form.get('student_email'),
            discipline=request.form.get('discipline'),
            class_number=request.form.get('class_number'),
            original_filename=file.filename,
            display_name=candidate_name,
            file_path=candidate_path,
            metadata_path=metadata_path,
            file_hash=file_hash,
            printer=request.form.get('printer'),
            color=raw_color,
            material=raw_method
        )
        db.session.add(job)
        db.session.commit()

        # Event logging
        log_event(job.id, 'JobCreated', {'original_filename': job.original_filename})

        # Fire-and-forget best-effort notification (optional)
        try:
            send_status_update_email(job, 'UPLOADED')
        except Exception:
            pass

        return jsonify(job.to_dict()), 201
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(tb)
        return jsonify({'error': str(e), 'traceback': tb}), 500 


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

    # Transition to READYTOPRINT
    job.student_confirmed = True
    job.status = 'READYTOPRINT'
    db.session.commit()
    log_event(job.id, 'StudentConfirmed', {'status': job.status})
    return jsonify(job.to_dict()), 200