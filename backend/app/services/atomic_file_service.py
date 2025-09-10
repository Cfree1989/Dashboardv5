"""
Compatibility shims for atomic file operations expected by tests.

This module provides lightweight implementations matching the constructor
and method semantics used in the test suite, while delegating locking to
the file lock service exposed at this module path for easy patching.
"""

from __future__ import annotations

import os
import json
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone

from .file_lock_service import get_file_lock_service


class AtomicFileOperation:
    """Test-facing base class for atomic operations."""

    def __init__(self, operation_id: str, job_id: str, operation_type: str):
        self.operation_id = operation_id
        self.job_id = job_id
        self.operation_type = operation_type
        self.prepared: bool = False
        self.committed: bool = False
        self.rolled_back: bool = False
        self._staging_dir: Optional[Path] = None
        self.staged_files: List[Tuple[Path, Path]] = []
        self.staged_metadata: List[Tuple[Path, Dict[str, Any]]] = []
        self.original_paths: Dict[str, str] = {}
        self._file_target_path: Optional[Path] = None
        self._metadata_target_path: Optional[Path] = None

    def _create_staging_directory(self) -> Path:
        if self._staging_dir is None:
            self._staging_dir = Path(
                tempfile.mkdtemp(prefix=f"atomic_{self.operation_id}_")
            )
        return self._staging_dir

    def _generate_staging_path(self, original_path: Path) -> Path:
        staging_dir = self._create_staging_directory()
        name = f"{original_path.stem}_{self.operation_id}{original_path.suffix}"
        return staging_dir / name

    def _backup_metadata(self, metadata_path: Path) -> Dict[str, Any]:
        if not metadata_path or not metadata_path.exists():
            return {}
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def _restore_metadata(self, metadata_path: Path, metadata: Dict[str, Any]) -> bool:
        try:
            metadata_path.parent.mkdir(parents=True, exist_ok=True)
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f)
            return True
        except Exception:
            return False

    def prepare_move_operation(
        self,
        source_path: Path,
        target_path: Path,
        metadata_path: Optional[Path] = None,
        target_metadata_path: Optional[Path] = None,
        metadata_updates: Optional[Dict[str, Any]] = None,
    ) -> bool:
        self.original_paths['file_path'] = str(source_path)
        if metadata_path:
            self.original_paths['metadata_path'] = str(metadata_path)

        try:
            if source_path and source_path.exists():
                staging_file = self._generate_staging_path(source_path)
                staging_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(source_path), str(staging_file))
                self.staged_files.append((source_path, staging_file))
            if metadata_path and metadata_path.exists():
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                except Exception:
                    self.prepared = False
                    return False
                if metadata_updates:
                    try:
                        merged = dict(meta)
                        merged.update(metadata_updates)
                    except Exception:
                        merged = meta
                else:
                    merged = meta
                staging_meta_file = self._generate_staging_path(metadata_path)
                staging_meta_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(metadata_path), str(staging_meta_file))
                self.staged_files.append((metadata_path, staging_meta_file))
                if target_metadata_path is not None:
                    self.staged_metadata.append((Path(target_metadata_path), merged))
                else:
                    self.staged_metadata.append((Path(str(target_path) + '.json'), merged))
            self._file_target_path = Path(target_path) if target_path else None
            self._metadata_target_path = (
                Path(target_metadata_path) if target_metadata_path else None
            )
            self.prepared = True
            return True
        except Exception:
            self.prepared = False
            return False

    def commit(self) -> bool:
        if self.committed:
            return True
        if not self.prepared:
            return False
        self.committed = True
        return True

    def rollback(self) -> bool:
        try:
            if self._staging_dir and self._staging_dir.exists():
                shutil.rmtree(self._staging_dir, ignore_errors=True)
        finally:
            self.rolled_back = True
        return True

    def __enter__(self) -> "AtomicFileOperation":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if not self.committed:
            self.rollback()


class AtomicFileMoveOperation(AtomicFileOperation):
    def __init__(self, operation_id: str, job_id: str, source_path: Path, target_path: Path):
        super().__init__(operation_id, job_id, 'move')
        self.source_file: Path = Path(source_path)
        self.dest_file: Path = Path(target_path)
        self._destination_mapping: Dict[Path, Path] = {self.source_file: self.dest_file}

    def _get_destination_path(self, file_path: Path) -> Optional[Path]:
        return self._destination_mapping.get(Path(file_path))

    def commit(self) -> bool:
        if not super().commit():
            return False
        for original_path, staging_path in list(self.staged_files):
            if not staging_path.exists():
                continue
            dest = self._get_destination_path(original_path)
            if dest is None and original_path == self.source_file:
                dest = self.dest_file
            if dest is None:
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(staging_path), str(dest))
        for dest_meta_path, metadata in list(self.staged_metadata):
            dest_meta_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dest_meta_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f)
        return True


class AtomicFileService:
    def __init__(self) -> None:
        self.lock_service = get_file_lock_service()

    def _status_dir_name(self, status: str) -> str:
        parts = status.strip().lower().split('_')
        return ''.join(p.capitalize() for p in parts)

    def _storage_root_from_path(self, path: Path) -> Path:
        storage_override = os.environ.get('STORAGE_PATH')
        if storage_override:
            return Path(storage_override)
        statuses = {
            'uploaded', 'pending', 'readytoprint', 'printing',
            'completed', 'rejected', 'archived', 'paidpickedup'
        }
        for parent in path.parents:
            if parent.name.lower() in statuses:
                return parent.parent
        return path.parent

    def atomic_move_authoritative(self, job, target_status: str) -> bool:
        file_path = Path(job.file_path) if getattr(job, 'file_path', None) else None
        metadata_path = Path(job.metadata_path) if getattr(job, 'metadata_path', None) else None
        if not file_path:
            return False
        operation_id = f"move_{job.id}_{target_status}_{datetime.now(timezone.utc).timestamp()}"
        try:
            self.lock_service.acquire_lock(str(file_path), operation_id)
            if metadata_path:
                self.lock_service.acquire_lock(str(metadata_path), operation_id)
            root = self._storage_root_from_path(file_path)
            dest_dir = root / self._status_dir_name(target_status)
            dest_file = dest_dir / file_path.name
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(file_path), str(dest_file))
            if metadata_path:
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                except Exception:
                    return False
                dest_meta = dest_dir / metadata_path.name
                updated_meta = dict(meta)
                updated_meta['status'] = target_status
                updated_meta['file_path'] = str(dest_file.resolve())
                dest_meta.parent.mkdir(parents=True, exist_ok=True)
                with open(dest_meta, 'w', encoding='utf-8') as f:
                    json.dump(updated_meta, f)
                job.metadata_path = str(dest_meta.resolve())
            job.file_path = str(dest_file.resolve())
            job.status = target_status
            return True
        finally:
            try:
                self.lock_service.release_lock(str(file_path), operation_id)
            except Exception:
                pass
            if metadata_path:
                try:
                    self.lock_service.release_lock(str(metadata_path), operation_id)
                except Exception:
                    pass


_atomic_service_singleton: Optional[AtomicFileService] = None


def get_atomic_file_service() -> AtomicFileService:
    global _atomic_service_singleton
    if _atomic_service_singleton is None:
        _atomic_service_singleton = AtomicFileService()
    return _atomic_service_singleton


__all__ = [
    'AtomicFileService',
    'AtomicFileOperation',
    'AtomicFileMoveOperation',
    'get_atomic_file_service',
]
