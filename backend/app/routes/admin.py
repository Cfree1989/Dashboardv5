from __future__ import annotations
from flask import Blueprint, jsonify, request, g, abort, current_app
from app.utils.decorators import token_required
from app import db, limiter
from app.models.job import Job
from app.models.event import Event
from app.models.payment import Payment
from app.models.staff import Staff
from app.services.event_service import log_event
from app.services.file_service import move_authoritative
from app.services.email_service import send_approval_email, send_rejection_email, send_completion_email
from app.services.token_service import generate_confirmation_token
from app.services.mock_job_service import MockJobService
from pathlib import Path
import os
import json
from datetime import datetime, timezone
from datetime import timedelta
import shutil


bp = Blueprint('admin', __name__, url_prefix='/api/v1/admin')


def _safe_read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return {}


def _storage_root() -> Path:
    root = os.environ.get('STORAGE_PATH', 'storage')
    return Path(root)


def _list_all_storage_files(root: Path) -> list[Path]:
    files: list[Path] = []
    # Include all status directories plus any extra content under root for completeness
    status_dirs = set(STATUS_TO_DIR.values()) | { 'Uploaded', 'Pending', 'ReadyToPrint', 'Printing', 'Completed', 'PaidPickedUp', 'Archived' }
    for dirname in status_dirs:
        d = root / dirname
        if not d.exists() or not d.is_dir():
            continue
        for p in d.iterdir():
            if p.is_file():
                files.append(p)
    # Also include top-level files directly under root (if any)
    try:
        for p in root.iterdir():
            if p.is_file():
                files.append(p)
    except Exception:
        pass
    return files


def _expected_dir_for_status(status: str) -> str:
    return STATUS_TO_DIR.get(status, 'Uploaded')


def perform_audit() -> dict:
    root = _storage_root()
    all_files = _list_all_storage_files(root)
    all_files_set = {str(p.resolve()) for p in all_files}

    # Collect known paths from DB
    jobs: list[Job] = Job.query.all()
    known_paths: set[str] = set()
    for j in jobs:
        if j.file_path:
            known_paths.add(str(Path(j.file_path).resolve()))
        if j.metadata_path:
            known_paths.add(str(Path(j.metadata_path).resolve()))

    # Orphans: files present on disk but not referenced in DB
    orphaned_files: list[str] = sorted(p for p in all_files_set if p not in known_paths)

    # Broken links: per job issues
    broken_links: list[dict] = []
    stale_files: set[str] = set()

    # Index files by basename across all status dirs to detect duplicates
    from collections import defaultdict
    by_name: dict[str, list[Path]] = defaultdict(list)
    for p in all_files:
        by_name[p.name].append(p)

    for j in jobs:
        issues: list[str] = []
        file_path = Path(j.file_path) if j.file_path else None
        meta_path = Path(j.metadata_path) if j.metadata_path else None
        # Existence
        if file_path is None or not file_path.exists():
            issues.append('file_missing')
        if meta_path is None or not meta_path.exists():
            issues.append('metadata_missing')

        # Directory/status match
        expected_dir = _expected_dir_for_status(j.status)
        actual_dir = file_path.parent.name if file_path else None
        if file_path and file_path.exists() and actual_dir != expected_dir:
            issues.append('dir_status_mismatch')

        # Metadata parity
        if meta_path and meta_path.exists():
            meta = _safe_read_json(meta_path)
            if meta.get('status') != j.status or meta.get('file_path') != str(Path(j.file_path).resolve()):
                issues.append('metadata_mismatch')

        if issues:
            broken_links.append({
                'job_id': j.id,
                'issues': issues,
                'file_path': str(file_path) if file_path else None,
                'metadata_path': str(meta_path) if meta_path else None,
                'expected_dir': expected_dir,
                'actual_dir': actual_dir,
            })

        # Stale duplicates of authoritative file/metadata in other status dirs
        if file_path:
            name = file_path.name
            for p in by_name.get(name, []):
                if str(p.resolve()) != str(file_path.resolve()):
                    stale_files.add(str(p.resolve()))
        if meta_path:
            mname = meta_path.name
            for p in by_name.get(mname, []):
                if str(p.resolve()) != str(meta_path.resolve()):
                    stale_files.add(str(p.resolve()))

    report = {
        'report_generated_at': datetime.now(timezone.utc).isoformat(),
        'orphaned_files': orphaned_files,
        'broken_links': broken_links,
        'stale_files': sorted(stale_files),
        'files_scanned': len(all_files_set),
    }
    return report


@bp.route('/audit/report', methods=['GET'])
@token_required
def audit_report():
    return jsonify(perform_audit()), 200


@bp.route('/audit/orphaned-file', methods=['DELETE'])
@token_required
def delete_orphaned_file():
    data = request.get_json(silent=True) or {}
    file_path = (data.get('file_path') or '').strip()
    staff_name = (data.get('staff_name') or '').strip()
    if not file_path or not staff_name:
        return jsonify({'message': 'file_path and staff_name are required'}), 400
    # Security: restrict deletions to STORAGE_PATH
    root = _storage_root().resolve()
    target = Path(file_path).resolve()
    if not str(target).startswith(str(root)):
        return jsonify({'message': 'file_path must be within STORAGE_PATH'}), 400
    # Ensure not referenced by DB
    ref = db.session.query(Job).filter((Job.file_path == str(target)) | (Job.metadata_path == str(target))).first()
    if ref:
        return jsonify({'message': 'file is referenced by a job; not an orphan'}), 409
    try:
        if target.exists() and target.is_file():
            target.unlink()
    except Exception:
        abort(500, description='Failed to delete file')
    # Log event (system-level; no job)
    evt = Event(job_id='system', event_type='OrphanedFileDeleted', details={'file_path': str(target)}, triggered_by=staff_name, workstation_id=getattr(g, 'workstation_id', 'unknown'))
    db.session.add(evt)
    db.session.commit()
    return jsonify({'message': 'deleted'}), 200


@bp.route('/audit/stale-file', methods=['DELETE'])
@token_required
def delete_stale_file():
    data = request.get_json(silent=True) or {}
    file_path = (data.get('file_path') or '').strip()
    staff_name = (data.get('staff_name') or '').strip()
    if not file_path or not staff_name:
        return jsonify({'message': 'file_path and staff_name are required'}), 400
    root = _storage_root().resolve()
    target = Path(file_path).resolve()
    if not str(target).startswith(str(root)):
        return jsonify({'message': 'file_path must be within STORAGE_PATH'}), 400
    # Ensure not authoritative reference by DB
    ref = db.session.query(Job).filter((Job.file_path == str(target)) | (Job.metadata_path == str(target))).first()
    if ref:
        return jsonify({'message': 'file is referenced by a job; cannot delete'}), 409
    try:
        if target.exists() and target.is_file():
            target.unlink()
    except Exception:
        abort(500, description='Failed to delete file')
    evt = Event(job_id='system', event_type='StaleFileDeleted', details={'file_path': str(target)}, triggered_by=staff_name, workstation_id=getattr(g, 'workstation_id', 'unknown'))
    db.session.add(evt)
    db.session.commit()
    return jsonify({'message': 'deleted'}), 200


@bp.route('/audit/mark-reviewed', methods=['POST'])
@token_required
def mark_reviewed():
    data = request.get_json(silent=True) or {}
    job_id = (data.get('job_id') or '').strip()
    staff_name = (data.get('staff_name') or '').strip()
    issues = data.get('issues') or []
    if not job_id or not staff_name:
        return jsonify({'message': 'job_id and staff_name are required'}), 400
    job = Job.query.get(job_id)
    if not job:
        return jsonify({'message': 'Job not found'}), 404
    evt = Event(job_id=job.id, event_type='AuditIssueReviewed', details={'issues': issues}, triggered_by=staff_name, workstation_id=getattr(g, 'workstation_id', 'unknown'))
    db.session.add(evt)
    db.session.commit()
    return jsonify({'message': 'reviewed'}), 200


@bp.route('/audit/repair-metadata', methods=['POST'])
@token_required
def repair_metadata():
    data = request.get_json(silent=True) or {}
    job_id = (data.get('job_id') or '').strip()
    staff_name = (data.get('staff_name') or '').strip()
    if not job_id or not staff_name:
        return jsonify({'message': 'job_id and staff_name are required'}), 400
    job = Job.query.get(job_id)
    if not job:
        return jsonify({'message': 'Job not found'}), 404
    try:
        meta_path = Path(job.metadata_path) if getattr(job, 'metadata_path', None) else None
        if not meta_path or not meta_path.exists():
            meta_path = _metadata_path_for_job(job)
            _write_metadata_for_job(job, meta_path)
            job.metadata_path = str(meta_path.resolve())
            db.session.add(job)
            db.session.commit()
        _update_metadata_status(meta_path, job.status, job.file_path)
        evt = Event(job_id=job.id, event_type='AuditMetadataRepaired', details={'metadata_path': str(meta_path) if meta_path else None}, triggered_by=staff_name, workstation_id=getattr(g, 'workstation_id', 'unknown'))
        db.session.add(evt)
        db.session.commit()
        return jsonify({'message': 'metadata repaired'}), 200
    except Exception:
        abort(500, description='Failed to repair metadata')


@bp.route('/audit/repair-location', methods=['POST'])
@token_required
def repair_location():
    data = request.get_json(silent=True) or {}
    job_id = (data.get('job_id') or '').strip()
    staff_name = (data.get('staff_name') or '').strip()
    if not job_id or not staff_name:
        return jsonify({'message': 'job_id and staff_name are required'}), 400
    job = Job.query.get(job_id)
    if not job:
        return jsonify({'message': 'Job not found'}), 404
    try:
        # Move file/metadata into the directory that matches the current status
        move_authoritative(job, job.status)
        db.session.add(job)
        db.session.commit()
        # Update metadata.json to reflect new location/status
        meta_path = Path(job.metadata_path) if getattr(job, 'metadata_path', None) else None
        if meta_path:
            _update_metadata_status(meta_path, job.status, job.file_path)
        evt = Event(job_id=job.id, event_type='AuditLocationRepaired', details={'status': job.status}, triggered_by=staff_name, workstation_id=getattr(g, 'workstation_id', 'unknown'))
        db.session.add(evt)
        db.session.commit()
        return jsonify({'message': 'location repaired', 'status': job.status, 'file_path': job.file_path, 'metadata_path': job.metadata_path}), 200
    except Exception:
        abort(500, description='Failed to repair location')


@bp.route('/audit/relink-file', methods=['POST'])
@token_required
def relink_file():
    data = request.get_json(silent=True) or {}
    job_id = (data.get('job_id') or '').strip()
    file_path = (data.get('file_path') or '').strip()
    staff_name = (data.get('staff_name') or '').strip()
    if not job_id or not staff_name or not file_path:
        return jsonify({'message': 'job_id, file_path and staff_name are required'}), 400
    job = Job.query.get(job_id)
    if not job:
        return jsonify({'message': 'Job not found'}), 404
    # Validate target path
    root = _storage_root().resolve()
    target = Path(file_path).resolve()
    if not str(target).startswith(str(root)):
        return jsonify({'message': 'file_path must be within STORAGE_PATH'}), 400
    if not target.exists() or not target.is_file():
        return jsonify({'message': 'file_path does not exist or is not a file'}), 400
    try:
        # Point job to provided file, then normalize to status directory
        job.file_path = str(target)
        job.display_name = target.name
        db.session.add(job)
        db.session.commit()
        # Move into correct status folder
        move_authoritative(job, job.status)
        db.session.add(job)
        db.session.commit()
        # Ensure metadata exists and synced
        meta_path = Path(job.metadata_path) if getattr(job, 'metadata_path', None) else _metadata_path_for_job(job)
        if not meta_path.exists():
            _write_metadata_for_job(job, meta_path)
            job.metadata_path = str(meta_path.resolve())
            db.session.add(job)
            db.session.commit()
        _update_metadata_status(meta_path, job.status, job.file_path)
        evt = Event(job_id=job.id, event_type='AuditFileRelinked', details={'file_path': job.file_path}, triggered_by=staff_name, workstation_id=getattr(g, 'workstation_id', 'unknown'))
        db.session.add(evt)
        db.session.commit()
        return jsonify({'message': 'file relinked', 'file_path': job.file_path, 'metadata_path': job.metadata_path}), 200
    except Exception:
        abort(500, description='Failed to relink file')

def _update_metadata_status(meta_path: Path, new_status: str, new_file_path: str | None = None) -> None:
    try:
        if not meta_path.exists():
            return
        data = _safe_read_json(meta_path)
        data['status'] = new_status
        if new_file_path:
            try:
                resolved = str(Path(new_file_path).resolve())
            except Exception:
                resolved = new_file_path
            data['file_path'] = resolved
        meta_path.write_text(json.dumps(data, indent=2), encoding='utf-8')
    except Exception:
        # Non-fatal metadata sync
        pass

def _metadata_path_for_job(job: Job) -> Path:
    try:
        file_dir = Path(job.file_path).parent
        base = Path(job.file_path).stem
        return file_dir / f"{base}_metadata.json"
    except Exception:
        return Path(job.metadata_path) if getattr(job, 'metadata_path', None) else Path('')

def _write_metadata_for_job(job: Job, target_meta: Path) -> None:
    try:
        target_meta.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            'student_name': job.student_name,
            'student_email': job.student_email,
            'discipline': job.discipline,
            'class_number': job.class_number,
            'printer': job.printer,
            'color': getattr(job, 'color', None),
            'material': getattr(job, 'material', None),
            'status': job.status,
            'display_name': job.display_name,
            'authoritative_filename': Path(job.file_path).name if getattr(job, 'file_path', None) else None,
            'file_path': str(Path(job.file_path).resolve()) if getattr(job, 'file_path', None) else None,
        }
        target_meta.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    except Exception:
        pass


@bp.route('/archive', methods=['POST'])
@token_required
def archive_jobs():
    data = request.get_json(silent=True) or {}
    staff_name = (data.get('staff_name') or '').strip()
    if not staff_name:
        return jsonify({'message': 'staff_name is required'}), 400
    try:
        retention_days = int(data.get('retention_days') or 45)
    except Exception:
        return jsonify({'message': 'retention_days must be an integer'}), 400
    if retention_days < 0:
        return jsonify({'message': 'retention_days must be non-negative'}), 400
    cutoff = datetime.utcnow() - timedelta(days=retention_days)
    # Eligible: PaidPickedUp or Rejected older than cutoff
    eligible = Job.query.filter(
        Job.status.in_(['PAIDPICKEDUP', 'REJECTED']),
    ).all()
    count = 0
    for job in eligible:
        try:
            if job.created_at and job.created_at > cutoff:
                continue
        except Exception:
            pass
        # Move to Archived and update status
        try:
            from app.services.file_service import move_authoritative
            move_authoritative(job, 'ARCHIVED')
        except Exception:
            pass
        job.status = 'ARCHIVED'
        db.session.add(job)
        db.session.commit()
        # Sync metadata fields minimally
        try:
            _update_metadata_status(Path(job.metadata_path), 'ARCHIVED', job.file_path)
        except Exception:
            pass
        # Log per-job event
        evt = Event(job_id=job.id, event_type='JobArchived', details={'retention_days': retention_days}, triggered_by=staff_name, workstation_id=getattr(g, 'workstation_id', 'unknown'))
        db.session.add(evt)
        db.session.commit()
        count += 1
    # Batch admin action event (system-level)
    batch_evt = Event(job_id='system', event_type='AdminAction', details={'action': 'archive', 'jobs_archived': count, 'retention_days': retention_days}, triggered_by=staff_name, workstation_id=getattr(g, 'workstation_id', 'unknown'))
    db.session.add(batch_evt)
    db.session.commit()
    return jsonify({'message': 'Archival process completed', 'jobs_archived': count}), 200


@bp.route('/prune', methods=['POST'])
@token_required
def prune_jobs():
    data = request.get_json(silent=True) or {}
    staff_name = (data.get('staff_name') or '').strip()
    if not staff_name:
        return jsonify({'message': 'staff_name is required'}), 400
    try:
        retention_days = int(data.get('retention_days') or 365)
    except Exception:
        return jsonify({'message': 'retention_days must be an integer'}), 400
    if retention_days < 0:
        return jsonify({'message': 'retention_days must be non-negative'}), 400
    cutoff = datetime.utcnow() - timedelta(days=retention_days)
    archived = Job.query.filter(Job.status == 'ARCHIVED').all()
    deleted = 0
    for job in archived:
        try:
            if job.created_at and job.created_at > cutoff:
                continue
        except Exception:
            pass
        # Delete files best-effort
        try:
            fp = Path(job.file_path) if getattr(job, 'file_path', None) else None
            mp = Path(job.metadata_path) if getattr(job, 'metadata_path', None) else None
            if fp and fp.exists():
                fp.unlink(missing_ok=True)
            if mp and mp.exists():
                mp.unlink(missing_ok=True)
        except Exception:
            pass
        # Log per-job deletion (system-level note: will be cascaded with job)
        try:
            evt = Event(job_id=job.id, event_type='JobDeleted', details={'retention_days': retention_days}, triggered_by=staff_name, workstation_id=getattr(g, 'workstation_id', 'unknown'))
            db.session.add(evt)
            db.session.commit()
        except Exception:
            pass
        # Delete job
        try:
            db.session.delete(job)
            db.session.commit()
            deleted += 1
        except Exception:
            db.session.rollback()
            continue
    batch_evt = Event(job_id='system', event_type='AdminAction', details={'action': 'prune', 'jobs_deleted': deleted, 'retention_days': retention_days}, triggered_by=staff_name, workstation_id=getattr(g, 'workstation_id', 'unknown'))
    db.session.add(batch_evt)
    db.session.commit()
    return jsonify({'message': 'Pruning process completed', 'jobs_deleted': deleted}), 200


@bp.route('/mock-jobs', methods=['POST'])
@token_required
@limiter.limit("30 per minute")
def generate_mock_jobs():
    """Generate mock jobs for testing purposes."""
    # Development-only safety check
    if not current_app.config.get('DEBUG', False):
        return jsonify({'message': 'Mock job generation is only allowed in development mode'}), 403
    
    # Validate admin access
    staff_name = getattr(g, 'staff_name', None) or getattr(g, 'workstation_id', None) or 'Admin'
    staff = Staff.query.get(staff_name)
    if not staff:
        # Dev-only: auto-create active staff record if missing
        if current_app.config.get('DEBUG', False):
            staff = Staff(name=staff_name, is_active=True)
            db.session.add(staff)
            db.session.commit()
        else:
            return jsonify({'message': 'Invalid staff member'}), 403
    if not staff.is_active:
        return jsonify({'message': 'Inactive staff member'}), 403
    
    data = request.get_json(silent=True) or {}
    
    # Validate required fields
    counts = data.get('counts', {})
    if not isinstance(counts, dict):
        return jsonify({'message': 'counts must be a dictionary'}), 400
    
    # Validate status counts
    valid_statuses = ['UPLOADED', 'PENDING', 'READYTOPRINT', 'PRINTING', 'COMPLETED', 'PAIDPICKEDUP']
    for status, count in counts.items():
        if status not in valid_statuses:
            return jsonify({'message': f'Invalid status: {status}'}), 400
        if not isinstance(count, int) or count < 0:
            return jsonify({'message': f'Invalid count for {status}: must be non-negative integer'}), 400
        if count > 50:  # Limit to prevent abuse
            return jsonify({'message': f'Count for {status} too high: maximum 50'}), 400
    
    # Get optional parameters
    student_email = data.get('email', 'cfree3@lsu.edu')
    add_notes = data.get('addNotes', True)
    seed = data.get('seed')
    
    # Validate email
    if not isinstance(student_email, str) or '@' not in student_email:
        return jsonify({'message': 'Invalid email address'}), 400
    
    # Validate seed
    if seed is not None and not isinstance(seed, int):
        return jsonify({'message': 'seed must be an integer'}), 400
    
    try:
        # Generate mock jobs
        created_counts = MockJobService.generate_mock_jobs(
            counts=counts,
            student_email=student_email,
            add_notes=add_notes,
            seed=seed
        )
        
        # Log the event (temporarily disabled: system-level events without job_id cause DB constraint errors)
        # total_created = sum(created_counts.values())
        # log_event(
        #     event_type='MockJobsGenerated',
        #     details={
        #         'counts': created_counts,
        #         'total_created': total_created,
        #         'student_email': student_email,
        #         'add_notes': add_notes,
        #         'seed': seed
        #     },
        #     triggered_by=staff_name,
        #     workstation_id=g.workstation_id
        # )
        
        return jsonify({
            'message': f'Successfully generated {total_created} mock jobs',
            'created_counts': created_counts,
            'student_email': student_email,
            'add_notes': add_notes,
            'seed': seed
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error generating mock jobs: {str(e)}'}), 500


@bp.route('/delete-all-jobs', methods=['POST'])
@token_required
@limiter.limit("30 per minute")
def delete_all_jobs():
    """Delete ALL jobs from the entire system (development only)."""
    # Development-only safety check
    if not current_app.config.get('DEBUG', False):
        return jsonify({'message': 'Mass job deletion is only allowed in development mode'}), 403
    
    # Validate admin access
    staff_name = getattr(g, 'staff_name', None) or getattr(g, 'workstation_id', None) or 'Admin'
    staff = Staff.query.get(staff_name)
    if not staff:
        # Dev-only: auto-create active staff record if missing
        if current_app.config.get('DEBUG', False):
            staff = Staff(name=staff_name, is_active=True)
            db.session.add(staff)
            db.session.commit()
        else:
            return jsonify({'message': 'Invalid staff member'}), 403
    if not staff.is_active:
        return jsonify({'message': 'Inactive staff member'}), 403
    
    data = request.get_json(silent=True) or {}
    confirm = data.get('confirm', False)
    
    if not confirm:
        return jsonify({'message': 'Confirmation required. Set confirm: true in request body.'}), 400
    
    try:
        # Get counts before deletion for logging
        total_jobs = Job.query.count()
        total_events = Event.query.count()
        total_payments = Payment.query.count()
        
        # Delete all jobs
        deleted_counts = MockJobService.delete_all_jobs()
        
        # Log the event (temporarily disabled: system-level events without job_id cause DB constraint errors)
        # log_event(
        #     event_type='AllJobsDeleted',
        #     details={
        #         'jobs_deleted': deleted_counts['jobs_deleted'],
        #         'events_deleted': deleted_counts['events_deleted'],
        #         'payments_deleted': deleted_counts['payments_deleted'],
        #         'total_before': {
        #             'jobs': total_jobs,
        #             'events': total_events,
        #             'payments': total_payments
        #         }
        #     },
        #     triggered_by=staff_name,
        #     workstation_id=g.workstation_id
        # )
        
        return jsonify({
            'message': f'Successfully deleted all {deleted_counts["jobs_deleted"]} jobs from the system',
            'deleted_counts': deleted_counts,
            'total_before': {
                'jobs': total_jobs,
                'events': total_events,
                'payments': total_payments
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error deleting all jobs: {str(e)}'}), 500

