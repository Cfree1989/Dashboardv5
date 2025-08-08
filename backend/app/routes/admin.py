from __future__ import annotations
from flask import Blueprint, jsonify
from app.utils.decorators import token_required
from app import db
from app.models.job import Job
from app.services.file_service import STATUS_TO_DIR
from pathlib import Path
import os
import json
from datetime import datetime


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
    for dirname in set(STATUS_TO_DIR.values()):
        d = root / dirname
        if not d.exists() or not d.is_dir():
            continue
        for p in d.iterdir():
            if p.is_file():
                files.append(p)
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
        'report_generated_at': datetime.utcnow().isoformat(),
        'orphaned_files': orphaned_files,
        'broken_links': broken_links,
        'stale_files': sorted(stale_files),
    }
    return report


@bp.route('/audit/report', methods=['GET'])
@token_required
def audit_report():
    return jsonify(perform_audit()), 200


