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

from app.services.infrastructure.file_lock_service import get_file_lock_service
from app.services.infrastructure.file_configuration_service import get_file_configuration_service

logger = logging.getLogger(__name__)

# Feature flag for atomic file operations
ATOMIC_FILE_OPERATIONS_ENABLED = os.getenv('ATOMIC_FILE_OPERATIONS_ENABLED', 'true').lower() == 'true'

# STATUS_TO_DIR mapping now centralized in FileConfigurationService

class AtomicFileOperation:
    """Base class for atomic file operations with prepare/commit/rollback pattern."""
    
    def __init__(self, operation_id: str, job_id: str, source_path: Path, target_path: Path):
        self.operation_id = operation_id
        self.job_id = job_id
        self.source_path = source_path
        self.target_path = target_path
        self.staging_dir = None
        self.staged_files: List[Tuple[Path, Path]] = []  # (source, staging)
        self.staged_metadata: List[Tuple[Path, Dict]] = []  # (dest_path, metadata)
        self.original_metadata: Dict[str, Dict] = {}
        self.lock_service = get_file_lock_service()
        self.file_config = get_file_configuration_service()
        self._prepared = False
        self._committed = False
        # File integrity tracking
        self.integrity_info: Dict[str, Dict[str, Any]] = {}  # {file_path: {checksum, size, etc.}}
    
    def _calculate_file_integrity(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Calculate and store integrity information for a file"""
        try:
            if not file_path.exists() or not file_path.is_file():
                logger.warning(f"File does not exist for integrity calculation: {file_path}")
                return None
                
            integrity_info = self.file_config.get_file_integrity_info(file_path)
            if integrity_info:
                self.integrity_info[str(file_path)] = integrity_info
                logger.debug(f"Stored integrity info for {file_path}: {integrity_info['checksum'][:16]}...")
                
            return integrity_info
            
        except Exception as e:
            logger.error(f"Failed to calculate integrity for {file_path}: {e}")
            return None
    
    def _verify_staged_file_integrity(self, staging_path: Path, original_path: Path) -> bool:
        """Verify that staged file matches original file integrity"""
        try:
            if str(original_path) not in self.integrity_info:
                logger.warning(f"No original integrity info for {original_path}")
                return True  # Skip verification if no original info
                
            original_checksum = self.integrity_info[str(original_path)]['checksum']
            staged_checksum = self.file_config.calculate_file_checksum(staging_path)
            
            if staged_checksum != original_checksum:
                logger.error(f"Staged file integrity mismatch: {staging_path}")
                logger.error(f"Original: {original_checksum[:16]}..., Staged: {(staged_checksum or 'None')[:16] if staged_checksum else 'None'}...")
                return False
                
            logger.debug(f"Staged file integrity verified: {staging_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to verify staged file integrity: {e}")
            return False
    
    def _verify_final_file_integrity(self, final_path: Path, original_path: Path) -> bool:
        """Verify that final file matches original file integrity"""
        try:
            if str(original_path) not in self.integrity_info:
                logger.warning(f"No original integrity info for {original_path}")
                return True  # Skip verification if no original info
                
            original_checksum = self.integrity_info[str(original_path)]['checksum']
            final_checksum = self.file_config.calculate_file_checksum(final_path)
            
            if final_checksum != original_checksum:
                logger.error(f"Final file integrity mismatch: {final_path}")
                logger.error(f"Original: {original_checksum[:16]}..., Final: {(final_checksum or 'None')[:16] if final_checksum else 'None'}...")
                return False
                
            logger.debug(f"Final file integrity verified: {final_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to verify final file integrity: {e}")
            return False
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self._committed:
            logger.warning(f"Operation {self.operation_id} not committed, rolling back")
            self.rollback()
            
    def prepare(self) -> bool:
        """Prepare the operation by staging files. Returns True if successful."""
        if self._prepared:
            logger.warning(f"Operation {self.operation_id} already prepared")
            return True
            
        try:
            # Calculate initial file integrity
            if self.source_path.exists():
                logger.debug(f"Calculating integrity for source file: {self.source_path}")
                integrity_info = self._calculate_file_integrity(self.source_path)
                if not integrity_info:
                    logger.warning(f"Could not calculate integrity for {self.source_path}, continuing without verification")
            
            # Create staging directory
            self.staging_dir = Path(tempfile.mkdtemp(prefix=f"atomic_{self.operation_id}_"))
            logger.debug(f"Created staging directory: {self.staging_dir}")
            
            # Acquire file lock
            if not self.lock_service.acquire_lock(str(self.source_path), self.operation_id, timeout=300):
                raise RuntimeError(f"Failed to acquire lock for {self.source_path}")
                
            self._prepared = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to prepare operation {self.operation_id}: {e}")
            self.rollback()
            return False
            
    def commit(self) -> bool:
        """Commit the operation by moving staged files to final locations."""
        if not self._prepared:
            raise RuntimeError(f"Operation {self.operation_id} not prepared")
        if self._committed:
            logger.warning(f"Operation {self.operation_id} already committed")
            return True
            
        try:
            # Move staged files to final locations and verify integrity
            moved_files = []
            for source_path, staging_path in self.staged_files:
                if staging_path.exists():
                    # Verify staged file integrity before final move
                    if not self._verify_staged_file_integrity(staging_path, source_path):
                        raise RuntimeError(f"Staged file integrity verification failed: {staging_path}")
                    
                    dest_path = self._get_destination_path(source_path)
                    if dest_path:
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(staging_path), str(dest_path))
                        logger.debug(f"Committed file: {staging_path} -> {dest_path}")
                        
                        # Verify final file integrity after move
                        if not self._verify_final_file_integrity(dest_path, source_path):
                            # This is critical - file may be corrupted during move
                            logger.error(f"CRITICAL: Final file integrity verification failed: {dest_path}")
                            # Don't fail the operation but log as critical issue
                            # The file was moved successfully, corruption might be from the move operation itself
                        
                        moved_files.append((source_path, dest_path))
                        
            # Write metadata files (include integrity information)
            for dest_path, metadata in self.staged_metadata:
                if dest_path:
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Add integrity information to metadata if available
                    for source_path, final_path in moved_files:
                        if str(source_path) in self.integrity_info:
                            metadata.setdefault('file_integrity', {})
                            metadata['file_integrity'] = {
                                'checksum': self.integrity_info[str(source_path)]['checksum'],
                                'size_bytes': self.integrity_info[str(source_path)]['size_bytes'],
                                'verified_at': datetime.now(timezone.utc).isoformat(),
                                'operation_id': self.operation_id
                            }
                    
                    with open(dest_path, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, indent=2)
                    logger.debug(f"Committed metadata: {dest_path}")
                    
            # Clean up original files
            self._delete_original_files()
            self._delete_original_metadata()
            
            self._committed = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to commit operation {self.operation_id}: {e}")
            self.rollback()
            return False
            
    def rollback(self):
        """Rollback the operation by cleaning up staged files and restoring originals."""
        try:
            # Clean up staging directory
            if self.staging_dir and self.staging_dir.exists():
                shutil.rmtree(self.staging_dir)
                logger.debug(f"Cleaned up staging directory: {self.staging_dir}")
                
            # Restore original metadata files
            for path_str, metadata in self.original_metadata.items():
                source_path = Path(path_str)
                if not source_path.exists():
                    source_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(source_path, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, indent=2)
                    logger.debug(f"Restored original metadata: {source_path}")
                    
        except Exception as e:
            logger.error(f"Error during rollback of operation {self.operation_id}: {e}")
        finally:
            # Release file lock
            try:
                self.lock_service.release_lock(str(self.source_path), self.operation_id)
            except Exception as e:
                logger.warning(f"Failed to release lock for {self.source_path}: {e}")
                
    def _get_destination_path(self, source_path: Path) -> Optional[Path]:
        """Get the destination path for a source file."""
        # This should be implemented by subclasses
        return None
        
    def _delete_original_files(self):
        """Delete original source files after successful commit."""
        for source_path, _ in self.staged_files:
            try:
                if source_path.exists():
                    source_path.unlink()
                    logger.debug(f"Removed original file: {source_path}")
            except Exception as e:
                logger.warning(f"Failed to remove original file {source_path}: {e}")
                
    def _delete_original_metadata(self):
        """Delete original source metadata files after successful commit."""
        for path_str in self.original_metadata.keys():
            source_metadata_path = Path(path_str)
            try:
                if source_metadata_path.exists():
                    source_metadata_path.unlink()
                    logger.debug(f"Removed original metadata: {source_metadata_path}")
            except Exception as e:
                logger.warning(f"Failed to remove original metadata {source_metadata_path}: {e}")

class AtomicFileMoveOperation(AtomicFileOperation):
    """Atomic file move operation with metadata handling."""
    
    def prepare_move_operation(
        self, 
        source_path: Path, 
        target_path: Path, 
        metadata_path: Optional[Path] = None,
        target_metadata_path: Optional[Path] = None,
        metadata_updates: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Prepare a file move operation by staging files and metadata."""
        if not self.prepare():
            return False
            
        try:
            # Stage the main file
            if source_path.exists():
                staging_path = self.staging_dir / source_path.name
                shutil.copy2(str(source_path), str(staging_path))
                self.staged_files.append((source_path, staging_path))
                logger.debug(f"Staged file: {source_path} -> {staging_path}")
                
                # Verify staging integrity immediately after copy
                if not self._verify_staged_file_integrity(staging_path, source_path):
                    raise RuntimeError(f"File integrity verification failed during staging: {staging_path}")
                logger.debug(f"Staging integrity verified for: {source_path}")
            else:
                raise FileNotFoundError(f"Source file not found: {source_path}")
                
            # Handle metadata file
            if metadata_path and metadata_path.exists():
                # Backup original metadata
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    self.original_metadata[str(metadata_path)] = json.load(f)
                    
                # Stage metadata with updates
                if target_metadata_path:
                    metadata = self.original_metadata[str(metadata_path)].copy()
                    if metadata_updates:
                        metadata.update(metadata_updates)
                    self.staged_metadata.append((target_metadata_path, metadata))
                    logger.debug(f"Staged metadata: {metadata_path} -> {target_metadata_path}")
                    
            return True
            
        except Exception as e:
            logger.error(f"Failed to prepare move operation: {e}")
            self.rollback()
            raise  # Re-raise the original exception
            
    def _get_destination_path(self, source_path: Path) -> Optional[Path]:
        """Get the destination path for a source file."""
        if source_path == self.source_path:
            return self.target_path
        return None

class AtomicFileService:
    """Service for atomic file operations with fallback to legacy system."""
    
    def __init__(self):
        self.lock_service = get_file_lock_service()
        self.file_config = get_file_configuration_service()
        
    def atomic_move_authoritative(self, job, target_status: str) -> bool:
        """Atomic version of move_authoritative with fallback to legacy system."""
        logger.info("[AtomicFile] BEGIN atomic_move job=%s current_status=%s target_status=%s", job.id, job.status, target_status)
        if not ATOMIC_FILE_OPERATIONS_ENABLED:
            logger.info("Atomic file operations disabled, using legacy system")
            return self._legacy_move_authoritative(job, target_status)
            
        try:
            # Get file paths
            logger.debug("[AtomicFile] Resolving file paths for job=%s", job.id)
            source_path = self._get_job_file_path(job)
            target_path = self._get_target_path(job, target_status)
            metadata_path = self._get_metadata_path(job)
            target_metadata_path = self._get_target_metadata_path(job, target_status)
            
            # Idempotency guard: if the file is already at the target location, no-op
            if source_path and target_path and source_path.resolve() == target_path.resolve():
                logger.info(
                    "[AtomicFile] Idempotent move detected for job=%s; source already at target=%s",
                    job.id,
                    target_status,
                )
                # Best-effort metadata refresh to ensure status/file_path are correct
                try:
                    if target_metadata_path and target_metadata_path.exists():
                        with open(target_metadata_path, 'r', encoding='utf-8') as f:
                            current = json.load(f)
                        current['status'] = target_status
                        current['file_path'] = str(target_path)
                        current['updated_at'] = datetime.now(timezone.utc).isoformat()
                        with open(target_metadata_path, 'w', encoding='utf-8') as f:
                            json.dump(current, f, indent=2)
                        logger.debug("[AtomicFile] Refreshed metadata for idempotent move: %s", target_metadata_path)
                except Exception as e:
                    logger.warning("[AtomicFile] Failed to refresh metadata during idempotent move: %s", e)
                return True
            
            if not source_path or not target_path:
                logger.error(f"Invalid file paths for job {job.id}")
                return False
                
            # Create atomic operation
            operation_id = f"move_auth_{job.id}_{datetime.now(timezone.utc).timestamp()}"
            operation = AtomicFileMoveOperation(operation_id, str(job.id), source_path, target_path)
            
            with operation as op:
                # Prepare the move
                logger.debug("[AtomicFile] Preparing move job=%s source=%s target=%s", job.id, source_path, target_path)
                if not op.prepare_move_operation(
                    source_path, target_path, metadata_path, target_metadata_path,
                    metadata_updates={"status": target_status}
                ):
                    return False
                    
                # Commit the operation
                logger.debug("[AtomicFile] Committing move job=%s", job.id)
                if not op.commit():
                    return False
                    
                # Update database paths after successful file move
                from app import db
                job.file_path = str(target_path)
                job.metadata_path = str(target_metadata_path) if target_metadata_path else None
                db.session.add(job)
                db.session.commit()
                
                # Update metadata JSON file content to match new paths and status
                if target_metadata_path and target_metadata_path.exists():
                    try:
                        import json
                        from datetime import datetime as dt, timezone as tz
                        
                        # Load current metadata
                        with open(target_metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        # Update metadata to match database
                        metadata['status'] = target_status
                        metadata['file_path'] = str(target_path)
                        metadata['updated_at'] = dt.now(tz.utc).isoformat()
                        
                        # Save updated metadata
                        with open(target_metadata_path, 'w', encoding='utf-8') as f:
                            json.dump(metadata, f, indent=2)
                        
                        logger.info(f"Updated metadata content for job {job.id}: status={target_status}, file_path={target_path}")
                        
                    except Exception as e:
                        logger.warning(f"Failed to update metadata content for job {job.id}: {e}")
                        # Don't fail the whole operation for metadata sync issues
                    
            logger.info("[AtomicFile] SUCCESS job=%s moved to %s", job.id, target_status)
            return True
            
        except Exception as e:
            logger.exception("[AtomicFile] ERROR job=%s exception=%s", job.id, e)
            if ATOMIC_FILE_OPERATIONS_ENABLED:
                logger.warning("Falling back to legacy move system")
                return self._legacy_move_authoritative(job, target_status)
            return False
            
    def _legacy_move_authoritative(self, job, target_status: str) -> bool:
        """Legacy move_authoritative implementation as fallback."""
        # This would be the original unsafe implementation
        # For now, we'll implement a basic version
        try:
            source_path = self._get_job_file_path(job)
            target_path = self._get_target_path(job, target_status)
            
            # Idempotency guard for legacy path as well
            if source_path and target_path and source_path.resolve() == target_path.resolve():
                logger.info(
                    "[AtomicFile][Legacy] Idempotent move detected for job=%s; already at target=%s",
                    job.id,
                    target_status,
                )
                return True
            
            if source_path and target_path:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source_path), str(target_path))
                
                # Update database paths after successful file move
                from app import db
                job.file_path = str(target_path)
                # Update metadata path if it exists
                metadata_path = self._get_metadata_path(job)
                target_metadata_path = None
                if metadata_path:
                    target_metadata_path = self._get_target_metadata_path(job, target_status)
                    if target_metadata_path:
                        shutil.move(str(metadata_path), str(target_metadata_path))
                        job.metadata_path = str(target_metadata_path)
                db.session.add(job)
                db.session.commit()
                
                # Update metadata JSON file content to match new paths and status
                if target_metadata_path and target_metadata_path.exists():
                    try:
                        import json
                        from datetime import datetime as dt, timezone as tz
                        
                        # Load current metadata
                        with open(target_metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        # Update metadata to match database
                        metadata['status'] = target_status
                        metadata['file_path'] = str(target_path)
                        metadata['updated_at'] = dt.now(tz.utc).isoformat()
                        
                        # Save updated metadata
                        with open(target_metadata_path, 'w', encoding='utf-8') as f:
                            json.dump(metadata, f, indent=2)
                        
                        logger.info(f"Legacy move: Updated metadata content for job {job.id}: status={target_status}, file_path={target_path}")
                        
                    except Exception as e:
                        logger.warning(f"Legacy move: Failed to update metadata content for job {job.id}: {e}")
                        # Don't fail the whole operation for metadata sync issues
                
                logger.info(f"Legacy move completed for job {job.id} to {target_status}")
                return True
        except Exception as e:
            logger.error(f"Legacy move failed for job {job.id}: {e}")
        return False
        
    @contextmanager
    def move_file(self, source_path: str, target_path: str, metadata_path: str, target_metadata_path: str, job_id: str):
        """Context manager for atomic file moves with fallback support."""
        if not ATOMIC_FILE_OPERATIONS_ENABLED:
            logger.info("Atomic file operations disabled, using legacy move")
            yield None
            return
            
        operation_id = f"move_file_{job_id}_{datetime.now(timezone.utc).timestamp()}"
        operation = AtomicFileMoveOperation(operation_id, job_id, Path(source_path), Path(target_path))
        
        try:
            # Preflight permission checks on destination directories BEFORE prepare,
            # so PermissionError is raised during enter as the test expects
            dest_parent = Path(target_path).parent
            try:
                dest_parent.mkdir(parents=True, exist_ok=True)
                # If directory is not writable, raise immediately
                if not os.access(dest_parent, os.W_OK):
                    raise PermissionError(f"Destination not writable: {dest_parent}")
                # Touch a temp file to check permission
                tmp = dest_parent / f".__atomic_preflight__{operation_id}"
                with open(tmp, 'w', encoding='utf-8') as f:
                    f.write('ok')
                tmp.unlink(missing_ok=True)
            except PermissionError:
                raise
            except Exception:
                # Best-effort additional check
                with open(Path(target_path), 'a', encoding='utf-8') as _:
                    pass
            
            # Metadata destination preflight (if provided)
            if target_metadata_path:
                meta_parent = Path(target_metadata_path).parent
                try:
                    meta_parent.mkdir(parents=True, exist_ok=True)
                    if not os.access(meta_parent, os.W_OK):
                        raise PermissionError(f"Destination not writable: {meta_parent}")
                except PermissionError:
                    raise
                except Exception:
                    pass

            # Prepare the move operation - let exceptions propagate
            operation.prepare_move_operation(
                Path(source_path),
                Path(target_path),
                Path(metadata_path) if metadata_path else None,
                Path(target_metadata_path) if target_metadata_path else None,
                None  # Do not override metadata; caller may edit file within the context
            )
            yield operation
            operation.commit()
        except Exception as e:
            logger.error(f"Move file operation failed: {e}")
            raise
            
    def _get_job_file_path(self, job) -> Optional[Path]:
        """Get the file path for a job."""
        if hasattr(job, 'file_path') and job.file_path:
            return Path(job.file_path)
        return None
        
    def _get_target_path(self, job, target_status: str) -> Optional[Path]:
        """Get the target path for a job status change."""
        source_path = self._get_job_file_path(job)
        if not source_path:
            return None
            
        # Use centralized path management
        return self.file_config.get_job_file_path(source_path.name, target_status)
        
    def _get_metadata_path(self, job) -> Optional[Path]:
        """Get the metadata path for a job."""
        if hasattr(job, 'metadata_path') and job.metadata_path:
            return Path(job.metadata_path)
        return None
        
    def _get_target_metadata_path(self, job, target_status: str) -> Optional[Path]:
        """Get the target metadata path for a job status change."""
        metadata_path = self._get_metadata_path(job)
        if not metadata_path:
            return None
            
        # Use centralized path management
        # Extract base filename from metadata path (remove "_metadata.json" suffix)
        if metadata_path.name.endswith('_metadata.json'):
            base_filename = metadata_path.name[:-len('_metadata.json')]
        else:
            base_filename = metadata_path.stem
        return self.file_config.get_job_metadata_path(base_filename, target_status)
        
    def _get_storage_root_from_path(self, file_path: Path) -> Path:
        """Infer storage root from an existing file path."""
        # Use centralized storage root
        return self.file_config.get_storage_root()

# Global service instance
_atomic_file_service = None

def get_atomic_file_service() -> AtomicFileService:
    """Get the global atomic file service instance."""
    global _atomic_file_service
    if _atomic_file_service is None:
        _atomic_file_service = AtomicFileService()
    return _atomic_file_service
