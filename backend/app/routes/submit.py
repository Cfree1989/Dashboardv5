from flask import Blueprint, request, jsonify, abort
from app import db
from app.models.job import Job
import os, hashlib, json
from datetime import datetime
from uuid import uuid4
from app.services.event_service import log_event

bp = Blueprint('submit', __name__, url_prefix='/api/v1/submit')

ALLOWED_EXTENSIONS = {'stl', 'obj', '3mf'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
        standardized_name = f"{new_id}.{ext}"
        file_path = os.path.join(storage_dir, standardized_name)

        # Save file
        with open(file_path, 'wb') as out_f:
            out_f.write(file_bytes)

        # Combine separate first and last name fields into student_name
        first_name = request.form.get('student_first_name')
        last_name = request.form.get('student_last_name')
        student_name = f"{first_name or ''} {last_name or ''}".strip()

        # Create metadata JSON
        metadata = {
            'student_name': student_name,
            'student_email': request.form.get('student_email'),
            'discipline': request.form.get('discipline'),
            'class_number': request.form.get('class_number'),
            'printer': request.form.get('printer'),
            'color': request.form.get('color'),
            'material': request.form.get('print_method'),
            'status': 'UPLOADED',
            'created_at': datetime.utcnow().isoformat()
        }
        metadata_path = os.path.join(storage_dir, f"{new_id}_metadata.json")
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
            display_name=standardized_name,
            file_path=file_path,
            metadata_path=metadata_path,
            file_hash=file_hash,
            printer=request.form.get('printer'),
            color=request.form.get('color'),
            material=request.form.get('print_method')
        )
        db.session.add(job)
        db.session.commit()

        # Event logging
        log_event(job.id, 'JobCreated', {'original_filename': job.original_filename})

        return jsonify(job.to_dict()), 201
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(tb)
        return jsonify({'error': str(e), 'traceback': tb}), 500 