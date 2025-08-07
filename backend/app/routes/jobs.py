from flask import Blueprint
from flask import request, jsonify, abort, g
from app import db
from app.models.job import Job
from app.utils.decorators import token_required
from app.models.event import Event
from app.services.token_service import generate_confirmation_token
from app.services.email_service import send_approval_email

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

    # Basic approval: set PENDING and send confirmation email with token
    job.status = 'PENDING'
    db.session.commit()

    token = generate_confirmation_token(job.id)
    # Construct a basic confirmation URL; frontend route expected at /confirm/[token]
    base_url = request.host_url.rstrip('/')
    confirmation_url = f"{base_url}/confirm/{token}"
    send_approval_email(job, confirmation_url)

    Event(job_id=job.id, event_type='StaffApproved', details={'confirmation_url': confirmation_url}, triggered_by=g.workstation_id, workstation_id=g.workstation_id)
    db.session.add(Event(job_id=job.id, event_type='ApprovalEmailSent', details={}, triggered_by=g.workstation_id, workstation_id=g.workstation_id))
    db.session.commit()
    return jsonify(job.to_dict()), 200