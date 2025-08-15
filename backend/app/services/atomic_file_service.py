"""
Atomic file operation service with prepare/commit/rollback patterns.

This service provides atomic file operations that either complete fully
or rollback completely, preventing partial failures and data corruption.
"""

import os
import shutil
import json
import logging
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timezone
from contextlib import contextmanager

from app.services.file_lock_service import get_file_lock_service

logger = logging.getLogger(__name__)


class AtomicFileOperation:
    """
    Atomic file operation with prepare/commit/rollback pattern.
    
    This class ensures that file operations are atomic - either all steps
    succeed or all are rolled back, preventing partial failures and data
    corruption.
    """
    
    def __init__(self, operation_id: str, job_id: str, operation_type: str):
        """
        Initialize atomic file operation.
        
        Args:
            operation_id: Unique identifier for this operation
            job_id: ID of the job being operated on
            operation_type: Type of operation (e.g., 'move', 'copy', 'delete')
        """
        self.operation_id = operation_id
        self.job_id = job_id
        self.operation_type = operation_type
        self.lock_service = get_file_lock_service()
        
        # Staging area for file operations
        self.staging_dir = None
        self.staged_files: List[Tuple[Path, Path]] = []  # (source, staging_path)
        self.staged_metadata: List[Tuple[Path, Dict[str, Any]]] = []  # (path, metadata)
        
        # Rollback information
        self.original_paths: Dict[str, str] = {}  # file_path, metadata_path
        self.original_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Operation state
        self.prepared = False
        self.committed = False
        self.rolled_back = False
        
        logger.info(f"AtomicFileOperation initialized: {operation_id} for job {job_id}")
    
    def _create_staging_directory(self) -> Path:
        """Create a temporary staging directory for file operations."""
        if self.staging_dir is None:
            self.staging_dir = Path(tempfile.mkdtemp(prefix=f"atomic_{self.operation_id}_"))
            logger.debug(f"Created staging directory: {self.staging_dir}")
        return self.staging_dir
    
    def _generate_staging_path(self, original_path: Path) -> Path:
        """Generate a unique staging path for a file."""
        staging_dir = self._create_staging_directory()
        # Use original filename with operation ID to prevent conflicts
        staging_name = f"{original_path.stem}_{self.operation_id}{original_path.suffix}"
        return staging_dir / staging_name
    
    def _backup_metadata(self, metadata_path: Path) -> Dict[str, Any]:
        """Backup metadata file content for potential rollback."""
        try:
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to backup metadata {metadata_path}: {e}")
        return {}
    
    def _restore_metadata(self, metadata_path: Path, metadata: Dict[str, Any]) -> bool:
        """Restore metadata file content."""
        try:
            metadata_path.parent.mkdir(parents=True, exist_ok=True)
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to restore metadata {metadata_path}: {e}")
            return False
    
    def prepare_move_operation(
        self, 
        source_file: Path, 
        dest_file: Path,
        source_metadata: Optional[Path] = None,
        dest_metadata: Optional[Path] = None,
        metadata_updates: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Prepare a file move operation by staging files and metadata.
        
        Args:
            source_file: Source file path
            dest_file: Destination file path
            source_metadata: Source metadata file path (optional)
            dest_metadata: Destination metadata file path (optional)
            metadata_updates: Updates to apply to metadata (optional)
            
        Returns:
            True if preparation succeeded, False otherwise
        """
        try:
            # Store original paths for rollback
            self.original_paths['file_path'] = str(source_file)
            if source_metadata:
                self.original_paths['metadata_path'] = str(source_metadata)
            
            # Backup original metadata
            if source_metadata:
                self.original_metadata[str(source_metadata)] = self._backup_metadata(source_metadata)
            
            # Stage source file
            if source_file.exists():
                staging_path = self._generate_staging_path(source_file)
                shutil.copy2(source_file, staging_path)
                self.staged_files.append((source_file, staging_path))
                logger.debug(f"Staged file: {source_file} -> {staging_path}")
            
            # Stage metadata file
            if source_metadata and source_metadata.exists():
                staging_meta_path = self._generate_staging_path(source_metadata)
                shutil.copy2(source_metadata, staging_meta_path)
                self.staged_files.append((source_metadata, staging_meta_path))
                
                # Prepare metadata updates
                if metadata_updates:
                    try:
                        with open(staging_meta_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        metadata.update(metadata_updates)
                        metadata['updated_at'] = datetime.now(timezone.utc).isoformat()
                        with open(staging_meta_path, 'w', encoding='utf-8') as f:
                            json.dump(metadata, f, indent=2)
                        self.staged_metadata.append((dest_metadata or staging_meta_path, metadata))
                        logger.debug(f"Updated metadata: {metadata_updates}")
                    except Exception as e:
                        logger.error(f"Failed to update metadata: {e}")
                        return False
                
                logger.debug(f"Staged metadata: {source_metadata} -> {staging_meta_path}")
            
            self.prepared = True
            logger.info(f"Move operation prepared successfully: {source_file} -> {dest_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to prepare move operation: {e}")
            self._rollback_preparation()
            return False
    
    def commit(self) -> bool:
        """
        Commit the prepared file operations.
        
        Returns:
            True if commit succeeded, False otherwise
        """
        if not self.prepared:
            logger.error("Cannot commit unprepared operation")
            return False
        
        if self.committed:
            logger.warning("Operation already committed")
            return True
        
        try:
            # Ensure destination directories exist
            for source_path, staging_path in self.staged_files:
                dest_path = self._get_destination_path(source_path)
                if dest_path:
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Move staged files to final destinations
            for source_path, staging_path in self.staged_files:
                dest_path = self._get_destination_path(source_path)
                if dest_path and staging_path.exists():
                    shutil.move(str(staging_path), str(dest_path))
                    logger.debug(f"Committed file: {staging_path} -> {dest_path}")
            
            # Write updated metadata files
            for dest_path, metadata in self.staged_metadata:
                if dest_path:
                    self._restore_metadata(dest_path, metadata)
                    logger.debug(f"Committed metadata: {dest_path}")
            
            # Clean up staging directory
            self._cleanup_staging()
            
            self.committed = True
            logger.info(f"Atomic operation committed successfully: {self.operation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to commit operation: {e}")
            self.rollback()
            return False
    
    def rollback(self) -> bool:
        """
        Rollback the file operations to their original state.
        
        Returns:
            True if rollback succeeded, False otherwise
        """
        if self.rolled_back:
            logger.warning("Operation already rolled back")
            return True
        
        try:
            # Restore original files if they were moved
            if self.committed:
                for source_path, staging_path in self.staged_files:
                    dest_path = self._get_destination_path(source_path)
                    if dest_path and dest_path.exists():
                        if not source_path.exists():
                            shutil.move(str(dest_path), str(source_path))
                            logger.debug(f"Rolled back file: {dest_path} -> {source_path}")
                        else:
                            # Source still exists, just remove destination
                            dest_path.unlink()
                            logger.debug(f"Removed destination file: {dest_path}")
            
            # Restore original metadata
            for path_str, metadata in self.original_metadata.items():
                path = Path(path_str)
                if path.parent.exists():
                    self._restore_metadata(path, metadata)
                    logger.debug(f"Restored metadata: {path}")
            
            # Clean up staging directory
            self._cleanup_staging()
            
            self.rolled_back = True
            logger.info(f"Atomic operation rolled back successfully: {self.operation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback operation: {e}")
            return False
    
    def _rollback_preparation(self):
        """Rollback preparation phase if it fails."""
        try:
            self._cleanup_staging()
            logger.debug("Preparation rollback completed")
        except Exception as e:
            logger.error(f"Failed to rollback preparation: {e}")
    
    def _cleanup_staging(self):
        """Clean up staging directory and files."""
        try:
            if self.staging_dir and self.staging_dir.exists():
                shutil.rmtree(self.staging_dir)
                self.staging_dir = None
                logger.debug(f"Cleaned up staging directory")
        except Exception as e:
            logger.warning(f"Failed to cleanup staging directory: {e}")
    
    def _get_destination_path(self, source_path: Path) -> Optional[Path]:
        """Get the destination path for a source file (to be implemented by subclasses)."""
        # This should be overridden by specific operation types
        return None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic rollback on exception."""
        if exc_type is not None:
            logger.warning(f"Exception in atomic operation, rolling back: {exc_val}")
            self.rollback()
        elif not self.committed:
            logger.warning("Atomic operation not committed, rolling back")
            self.rollback()


class AtomicFileMoveOperation(AtomicFileOperation):
    """Atomic file move operation with specific destination handling."""
    
    def __init__(self, operation_id: str, job_id: str, source_file: Path, dest_file: Path):
        super().__init__(operation_id, job_id, 'move')
        self.source_file = source_file
        self.dest_file = dest_file
        self._destination_mapping = {source_file: dest_file}
    
    def _get_destination_path(self, source_path: Path) -> Optional[Path]:
        """Get the destination path for a source file."""
        return self._destination_mapping.get(source_path)


class AtomicFileService:
    """Service for performing atomic file operations."""
    
    def __init__(self):
        self.lock_service = get_file_lock_service()
    
    def atomic_move_authoritative(
        self, 
        job, 
        to_status: str, 
        operation_id: Optional[str] = None
    ) -> bool:
        """
        Atomically move authoritative file and metadata to destination status directory.
        
        Args:
            job: Job object with file_path and metadata_path
            to_status: Target status for the move operation
            operation_id: Optional operation ID (auto-generated if not provided)
            
        Returns:
            True if operation succeeded, False otherwise
        """
        if operation_id is None:
            operation_id = f"move_{job.id}_{to_status}_{datetime.now(timezone.utc).timestamp()}"
        
        current_file = Path(job.file_path)
        current_meta = Path(job.metadata_path) if getattr(job, 'metadata_path', None) else None
        
        # Determine destination paths
        root = self._storage_root_from_path(current_file)
        dest_dirname = STATUS_TO_DIR.get(to_status, STATUS_TO_DIR.get(job.status, 'Uploaded'))
        dest_dir = root / dest_dirname
        dest_file = dest_dir / current_file.name
        dest_meta = dest_dir / current_meta.name if current_meta else None
        
        # Prepare metadata updates
        metadata_updates = {
            'status': to_status,
            'file_path': str(dest_file.resolve()),
            'authoritative_filename': dest_file.name,
            'display_name': dest_file.name
        }
        
        # Acquire locks for all files involved
        files_to_lock = [current_file]
        if current_meta:
            files_to_lock.append(current_meta)
        
        try:
            # Acquire locks for all files
            for file_path in files_to_lock:
                if not self.lock_service.acquire_lock(
                    str(file_path), 
                    operation_id, 
                    timeout=300,
                    metadata={'operation': 'atomic_move', 'job_id': job.id, 'to_status': to_status}
                ):
                    logger.error(f"Failed to acquire lock for {file_path}")
                    return False
            
            # Perform atomic operation
            with AtomicFileMoveOperation(operation_id, job.id, current_file, dest_file) as op:
                # Prepare the move operation
                if not op.prepare_move_operation(
                    current_file, 
                    dest_file,
                    current_meta,
                    dest_meta,
                    metadata_updates
                ):
                    return False
                
                # Commit the operation
                if not op.commit():
                    return False
                
                # Update job paths
                job.file_path = str(dest_file.resolve())
                if dest_meta:
                    job.metadata_path = str(dest_meta.resolve())
                
                logger.info(f"Atomic move completed successfully: {operation_id}")
                return True
                
        except Exception as e:
            logger.error(f"Atomic move operation failed: {e}")
            return False
        finally:
            # Release locks
            for file_path in files_to_lock:
                self.lock_service.release_lock(str(file_path), operation_id)
    
    def _storage_root_from_path(self, file_path: Path) -> Path:
        """Infer storage root from an existing file path."""
        parent = file_path.parent
        if parent.name in STATUS_TO_DIR.values():
            return parent.parent
        return Path(os.environ.get('STORAGE_PATH', parent.as_posix()))


# Global instance for application use
_atomic_file_service = None

def get_atomic_file_service() -> AtomicFileService:
    """Get the global atomic file service instance."""
    global _atomic_file_service
    if _atomic_file_service is None:
        _atomic_file_service = AtomicFileService()
    return _atomic_file_service


# Status directory mapping (moved from file_service.py)
STATUS_TO_DIR = {
    'UPLOADED': 'Uploaded',
    'PENDING': 'Pending',
    'READYTOPRINT': 'ReadyToPrint',
    'PRINTING': 'Printing',
    'COMPLETED': 'Completed',
    'PAIDPICKEDUP': 'PaidPickedUp',
    'ARCHIVED': 'Archived',
}
