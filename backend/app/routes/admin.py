from __future__ import annotations
from flask import Blueprint, jsonify, request, g, abort, current_app
from app.utils.decorators import token_required
from app import db, limiter
from app.models.job import Job
from app.models.event import Event
from app.models.payment import Payment
from app.models.staff import Staff
from app.business_logic.shared_services import event_service
from app.services.infrastructure import file_service
from app.business_logic.shared_services import email_service
from app.business_logic.shared_services import token_service
from pathlib import Path
import os
import json
from datetime import datetime, timezone
from datetime import timedelta
import shutil
from app.business_logic.shared_services.error_handling_service import get_error_handling_service
from app.business_logic.shared_services.validation_service import ValidationService
import logging

logger = logging.getLogger(__name__)


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
    # Validate staff
    staff_res = ValidationService.validate_staff(staff_name)
    if not staff_res.is_valid:
        return jsonify({'message': staff_res.error_message}), 400
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
    log_event('OrphanedFileDeleted', {'file_path': str(target)}, triggered_by=staff_name)
    return jsonify({'message': 'deleted'}), 200


@bp.route('/audit/stale-file', methods=['DELETE'])
@token_required
def delete_stale_file():
    data = request.get_json(silent=True) or {}
    file_path = (data.get('file_path') or '').strip()
    staff_name = (data.get('staff_name') or '').strip()
    if not file_path or not staff_name:
        return jsonify({'message': 'file_path and staff_name are required'}), 400
    # Validate staff
    staff_res = ValidationService.validate_staff(staff_name)
    if not staff_res.is_valid:
        return jsonify({'message': staff_res.error_message}), 400
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
    log_event('StaleFileDeleted', {'file_path': str(target)}, triggered_by=staff_name)
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
    log_event('AuditIssueReviewed', {'issues': issues}, triggered_by=staff_name, job_id=job.id)
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
        log_event('AuditMetadataRepaired', {'metadata_path': str(meta_path) if meta_path else None}, triggered_by=staff_name, job_id=job.id)
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
        log_event('AuditLocationRepaired', {'status': job.status}, triggered_by=staff_name, job_id=job.id)
        return jsonify({'message': 'location repaired'}), 200
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
        job.file_path = str(target.resolve())
        db.session.add(job)
        db.session.commit()
        log_event('AuditFileRelinked', {'file_path': job.file_path}, triggered_by=staff_name, job_id=job.id)
        return jsonify({'message': 'file relinked'}), 200
    except Exception:
        abort(500, description='Failed to relink file')

def _update_metadata_status(meta_path: Path, new_status: str, new_file_path: str | None = None) -> None:
    error_service = get_error_handling_service()
    
    success, error_msg = error_service.handle_metadata_operation_with_error_handling(
        job_id="admin_operation",
        metadata_path=str(meta_path),
        operation_func=lambda: _update_metadata_file_content(meta_path, new_status, new_file_path)
    )
    
    if not success:
        logger.error(f"Failed to update metadata status for {meta_path}: {error_msg}")


def _update_metadata_file_content(meta_path: Path, new_status: str, new_file_path: str | None = None) -> None:
    """Update metadata file content with proper error handling."""
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


def _metadata_path_for_job(job: Job) -> Path:
    try:
        file_dir = Path(job.file_path).parent
        base = Path(job.file_path).stem
        return file_dir / f"{base}_metadata.json"
    except Exception as e:
        error_service = get_error_handling_service()
        error_service.log_metadata_sync_error(
            error=e,
            job_id=str(job.id),
            metadata_path=getattr(job, 'metadata_path', 'unknown'),
            context={'operation': 'metadata_path_for_job'}
        )
        logger.error(f"Failed to generate metadata path for job {job.id}: {e}")
        return Path(job.metadata_path) if getattr(job, 'metadata_path', None) else Path('')


def _write_metadata_for_job(job: Job, target_meta: Path) -> None:
    error_service = get_error_handling_service()
    
    success, error_msg = error_service.handle_metadata_operation_with_error_handling(
        job_id=str(job.id),
        metadata_path=str(target_meta),
        operation_func=lambda: _write_metadata_content(job, target_meta)
    )
    
    if not success:
        logger.error(f"Failed to write metadata for job {job.id}: {error_msg}")


def _write_metadata_content(job: Job, target_meta: Path) -> None:
    """Write metadata content with proper error handling."""
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
            from app.services.infrastructure import file_service
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
        log_event('JobArchived', {'retention_days': retention_days}, triggered_by=staff_name, job_id=job.id)
        count += 1
    # Batch admin action event (system-level)
    log_event('AdminAction', {'action': 'archive', 'jobs_archived': count, 'retention_days': retention_days}, triggered_by=staff_name)
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
            log_event('JobDeleted', {'retention_days': retention_days}, triggered_by=staff_name, job_id=job.id)
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
    log_event('AdminAction', {'action': 'prune', 'jobs_deleted': deleted, 'retention_days': retention_days}, triggered_by=staff_name)
    return jsonify({'message': 'Pruning process completed', 'jobs_deleted': deleted}), 200


## Removed: mock-jobs generation endpoint


## Removed: delete-all-jobs endpoint


@bp.route('/error-monitoring', methods=['GET'])
@token_required
def get_error_monitoring():
    """Get error monitoring statistics and recent errors."""
    data = request.get_json(silent=True) or {}
    staff_name = (data.get('staff_name') or '').strip()
    if not staff_name:
        return jsonify({'message': 'staff_name is required'}), 400
    
    error_service = get_error_handling_service()
    error_summary = error_service.get_error_summary()
    
    # Add recovery suggestions for recent errors
    recent_errors_with_suggestions = []
    for error_info in error_summary['recent_errors']:
        suggestions = error_service.get_recovery_suggestions(error_info)
        recent_errors_with_suggestions.append({
            **error_info,
            'recovery_suggestions': suggestions
        })
    
    return jsonify({
        'error_summary': {
            'total_errors': error_summary['total_errors'],
            'error_counts': error_summary['error_counts'],
            'critical_errors': error_summary['critical_errors'],
            'high_errors': error_summary['high_errors']
        },
        'recent_errors': recent_errors_with_suggestions,
        'monitoring_timestamp': datetime.now(timezone.utc).isoformat()
    }), 200


@bp.route('/error-monitoring/clear', methods=['POST'])
@token_required
def clear_error_monitoring():
    """Clear error monitoring data."""
    data = request.get_json(silent=True) or {}
    staff_name = (data.get('staff_name') or '').strip()
    if not staff_name:
        return jsonify({'message': 'staff_name is required'}), 400
    
    error_service = get_error_handling_service()
    error_service.recent_errors.clear()
    error_service.error_counts.clear()
    
    # Log the clearing action
    log_event('ErrorMonitoringCleared', {'cleared_by': staff_name}, triggered_by=staff_name)
    
    return jsonify({'message': 'Error monitoring data cleared'}), 200


