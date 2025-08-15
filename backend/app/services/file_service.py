from __future__ import annotations
import os
from pathlib import Path
import shutil
from typing import Optional
import logging

from app.services.error_handling_service import get_error_handling_service, FileOperationError

logger = logging.getLogger(__name__)

STATUS_TO_DIR = {
    'UPLOADED': 'Uploaded',
    'PENDING': 'Pending',
    'READYTOPRINT': 'ReadyToPrint',
    'PRINTING': 'Printing',
    'COMPLETED': 'Completed',
    'PAIDPICKEDUP': 'PaidPickedUp',
    'ARCHIVED': 'Archived',
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
    
    This function has been deprecated in favor of atomic file operations.
    It is kept for backward compatibility but should be replaced with atomic operations.
    
    WARNING: This function has multiple failure points and does not provide atomic guarantees.
    Use atomic_move_authoritative from atomic_file_service instead.
    """
    error_service = get_error_handling_service()
    
    try:
        current_file = Path(job.file_path)
        current_meta = Path(job.metadata_path) if getattr(job, 'metadata_path', None) else None
        root = _storage_root_from_path(current_file)
        dest_dirname = STATUS_TO_DIR.get(to_status, STATUS_TO_DIR.get(job.status, 'Uploaded'))
        dest_dir = (root / dest_dirname)
        
        # Create destination directory with error handling
        success, error_msg = error_service.handle_file_operation_with_error_handling(
            operation="create_directory",
            file_path=str(dest_dir),
            operation_func=lambda: dest_dir.mkdir(parents=True, exist_ok=True)
        )
        if not success:
            logger.error(f"Failed to create destination directory {dest_dir}: {error_msg}")
            raise FileOperationError(f"Failed to create destination directory: {error_msg}", "create_directory", str(dest_dir))

        # Compute destination file paths
        dest_file = dest_dir / current_file.name
        
        # Copy file if it exists with error handling
        if current_file.exists():
            success, error_msg = error_service.handle_file_operation_with_error_handling(
                operation="copy_file",
                file_path=str(current_file),
                operation_func=lambda: shutil.copy2(current_file, dest_file)
            )
            if not success:
                logger.error(f"Failed to copy file {current_file} to {dest_file}: {error_msg}")
                raise FileOperationError(f"Failed to copy file: {error_msg}", "copy_file", str(current_file))
            
            # Delete original file with error handling
            success, error_msg = error_service.handle_file_operation_with_error_handling(
                operation="delete_original_file",
                file_path=str(current_file),
                operation_func=lambda: current_file.unlink(missing_ok=True)
            )
            if not success:
                logger.warning(f"Failed to delete original file {current_file}: {error_msg}")
                # Don't raise here as the copy succeeded, just log the warning
        
        # Update job.file_path regardless; audit can fix if missing
        job.file_path = str(dest_file.resolve())

        # Handle metadata file operations
        if current_meta is not None:
            dest_meta = dest_dir / current_meta.name
            if current_meta.exists():
                success, error_msg = error_service.handle_file_operation_with_error_handling(
                    operation="copy_metadata",
                    file_path=str(current_meta),
                    operation_func=lambda: shutil.copy2(current_meta, dest_meta)
                )
                if not success:
                    logger.error(f"Failed to copy metadata {current_meta} to {dest_meta}: {error_msg}")
                    raise FileOperationError(f"Failed to copy metadata: {error_msg}", "copy_metadata", str(current_meta))
                
                # Delete original metadata with error handling
                success, error_msg = error_service.handle_file_operation_with_error_handling(
                    operation="delete_original_metadata",
                    file_path=str(current_meta),
                    operation_func=lambda: current_meta.unlink(missing_ok=True)
                )
                if not success:
                    logger.warning(f"Failed to delete original metadata {current_meta}: {error_msg}")
                    # Don't raise here as the copy succeeded, just log the warning
            
            job.metadata_path = str(dest_meta.resolve())
            
            # Keep metadata.json in sync: status, file_path, authoritative/display name
            success, error_msg = error_service.handle_metadata_operation_with_error_handling(
                job_id=str(job.id),
                metadata_path=str(dest_meta),
                operation_func=_update_metadata_file,
                dest_meta=dest_meta,
                to_status=to_status,
                dest_file=dest_file
            )
            if not success:
                logger.error(f"Failed to update metadata file {dest_meta}: {error_msg}")
                # Don't raise here as the file operations succeeded, just log the error
        
        logger.info(f"Successfully moved job {job.id} files to {to_status} status")
        
    except Exception as e:
        error_service.log_file_operation_error(
            operation="move_authoritative",
            error=e,
            file_path=getattr(job, 'file_path', 'unknown'),
            job_id=str(job.id),
            context={'to_status': to_status, 'current_status': getattr(job, 'status', 'unknown')}
        )
        # Re-raise the exception to ensure the calling code knows the operation failed
        raise


def _update_metadata_file(dest_meta: Path, to_status: str, dest_file: Path) -> None:
    """Update metadata file with new status and file path information."""
    import json
    
    data = {}
    if dest_meta.exists():
        with open(dest_meta, 'r', encoding='utf-8') as f:
            data = json.load(f)
    
    data['status'] = to_status
    data['file_path'] = str(dest_file.resolve())
    data['authoritative_filename'] = dest_file.name
    data['display_name'] = dest_file.name
    
    with open(dest_meta, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


