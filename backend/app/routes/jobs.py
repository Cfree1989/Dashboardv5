from flask import Blueprint
from flask import request, jsonify, abort, g
from app import db
from app.models.job import Job
from app.utils.decorators import token_required
from app.models.event import Event
from app.services.token_service import generate_confirmation_token
from app.services.email_service import send_approval_email
from app.models.staff import Staff
from datetime import datetime
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
    # Stub implementation: return at least the originally uploaded filename
    files = []
    if job.original_filename:
        files.append(job.original_filename)
    return jsonify({ 'files': files }), 200

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
    job.status = 'PENDING'
    db.session.add(job)
    db.session.commit()

    # Generate confirmation token and send email
    token = generate_confirmation_token(job.id)
    base_url = request.host_url.rstrip('/')
    confirmation_url = f"{base_url}/confirm/{token}"
    send_approval_email(job, confirmation_url)

    # Log events with proper attribution
    approval_event = Event(
        job_id=job.id,
        event_type='StaffApproved',
        details={
            'confirmation_url': confirmation_url,
            'weight_g': weight_val,
            'time_hours': time_val,
            'cost_usd': float(final_cost_decimal),
        },
        triggered_by=staff_name,
        workstation_id=g.workstation_id,
    )
    email_event = Event(
        job_id=job.id,
        event_type='ApprovalEmailSent',
        details={},
        triggered_by=staff_name,
        workstation_id=g.workstation_id,
    )
    db.session.add(approval_event)
    db.session.add(email_event)
    db.session.commit()

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