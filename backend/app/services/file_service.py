from __future__ import annotations
import os
from pathlib import Path
import shutil
from typing import Optional


STATUS_TO_DIR = {
    'UPLOADED': 'Uploaded',
    'PENDING': 'Pending',
    'READYTOPRINT': 'ReadyToPrint',
    'PRINTING': 'Printing',
    'COMPLETED': 'Completed',
    'PAIDPICKEDUP': 'PaidPickedUp',
}


def _storage_root_from_path(file_path: Path) -> Path:
    """Infer storage root from an existing file path. Fallback to STORAGE_PATH env."""
    parent = file_path.parent
    if parent.name in STATUS_TO_DIR.values():
        return parent.parent
    # Fallback to env or current parent
    return Path(os.environ.get('STORAGE_PATH', parent.as_posix()))


def move_authoritative(job, to_status: str) -> None:
    """Copy authoritative file + metadata.json to the destination status directory and update job paths.
    Non-fatal if any filesystem step fails; best-effort copy-then-delete.
    """
    try:
        current_file = Path(job.file_path)
        current_meta = Path(job.metadata_path) if getattr(job, 'metadata_path', None) else None
        root = _storage_root_from_path(current_file)
        dest_dirname = STATUS_TO_DIR.get(to_status, STATUS_TO_DIR.get(job.status, 'Uploaded'))
        dest_dir = (root / dest_dirname)
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Compute destination file paths
        dest_file = dest_dir / current_file.name
        # Copy file if it exists
        if current_file.exists():
            shutil.copy2(current_file, dest_file)
            try:
                current_file.unlink(missing_ok=True)
            except Exception:
                pass
        # Update job.file_path regardless; audit can fix if missing
        job.file_path = str(dest_file.resolve())

        # Metadata
        if current_meta is not None:
            dest_meta = dest_dir / current_meta.name
            if current_meta.exists():
                shutil.copy2(current_meta, dest_meta)
                try:
                    current_meta.unlink(missing_ok=True)
                except Exception:
                    pass
            job.metadata_path = str(dest_meta.resolve())
    except Exception:
        # Non-fatal
        pass


