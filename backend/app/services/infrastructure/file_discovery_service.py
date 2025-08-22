"""
File Discovery Service

Handles complex file discovery logic for job candidate files.
Extracted from routes/jobs.py candidate_files function for Phase 3 route simplification.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from app.models.job import Job
from app.services.infrastructure.file_configuration_service import get_file_configuration_service


class CandidateFileResult:
    """Result object for candidate file discovery"""
    def __init__(self, files: List[str], files_detailed: List[Dict[str, Any]], recommended: Optional[str] = None):
        self.files = files
        self.files_detailed = files_detailed
        self.recommended = recommended
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'files': self.files,
            'files_detailed': self.files_detailed,
            'recommended': self.recommended
        }


class FileDiscoveryService:
    """Service for discovering candidate files for jobs"""
    
    def __init__(self):
        # Use centralized file configuration service
        self.file_config = get_file_configuration_service()
    
    @property
    def allowed_extensions(self) -> Set[str]:
        """Get allowed file extensions from centralized configuration"""
        return self.file_config.allowed_extensions
    
    @property
    def extension_priority(self) -> Dict[str, int]:
        """Get extension priority from centralized configuration"""
        return self.file_config.extension_priority
    
    def _build_relevance_tokens(self, job: Job) -> Set[str]:
        """Build relevance tokens to identify files related to this specific job"""
        tokens = set()
        
        if getattr(job, 'short_id', None):
            tokens.add(str(job.short_id).lower())
        
        if getattr(job, 'id', None):
            tokens.add(str(job.id)[:8].lower())
        
        if getattr(job, 'display_name', None):
            tokens.add(Path(str(job.display_name)).stem.lower())
        
        return tokens
    
    def _get_file_rank(self, filename: str) -> int:
        """Get priority rank for file extension (lower is better)"""
        return self.file_config.get_extension_priority(filename)
    
    def _is_file_related_to_job(self, filename: str, tokens: Set[str], job: Job) -> bool:
        """Check if a file is related to the specific job"""
        name_lower = filename.lower()
        
        # Check if any relevance token matches
        if any(tok and tok in name_lower for tok in tokens):
            return True
        
        # Always allow exact original filename if present
        if job.original_filename and filename == job.original_filename:
            return True
        
        return False
    
    def _scan_directory_for_candidates(self, directory: Path, tokens: Set[str], job: Job) -> List[Dict[str, Any]]:
        """Scan directory for candidate files related to the job"""
        candidates = []
        
        if not (directory.exists() and directory.is_dir()):
            return candidates
        
        for entry in directory.iterdir():
            if not (entry.is_file() and entry.suffix.lower() in self.allowed_extensions):
                continue
            
            if not self._is_file_related_to_job(entry.name, tokens, job):
                continue
            
            # Enhanced file validation
            try:
                # Validate filename security
                is_valid_filename, filename_error = self.file_config.validate_filename_security(entry.name)
                if not is_valid_filename:
                    continue  # Skip files with security issues
                
                # Validate file size
                stat = entry.stat()
                if not self.file_config.validate_file_size(stat.st_size):
                    continue  # Skip files with invalid size
                
                # Validate file header (content validation)
                try:
                    with open(entry, 'rb') as f:
                        file_content = f.read(2048)  # Read first 2KB for header validation
                    
                    is_valid_header, header_error = self.file_config.validate_file_header(file_content, entry.name)
                    if not is_valid_header:
                        continue  # Skip files with invalid content
                except (OSError, IOError):
                    continue  # Skip files that can't be read
                
                candidates.append({
                    'name': entry.name, 
                    'mtime': int(stat.st_mtime),
                    'size': stat.st_size
                })
            except OSError:
                continue
        
        return candidates
    
    def _ensure_original_filename_included(self, candidates: List[Dict[str, Any]], job: Job) -> List[Dict[str, Any]]:
        """Ensure original filename is included even if not present on disk"""
        if job.original_filename and not any(c['name'] == job.original_filename for c in candidates):
            candidates.append({
                'name': job.original_filename, 
                'mtime': 0
            })
        
        return candidates
    
    def _sort_candidates_by_priority(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort candidates by extension priority, then modification time, then name"""
        def sort_key(candidate: Dict[str, Any]) -> tuple:
            return (
                self._get_file_rank(candidate['name']),  # Priority rank (lower is better)
                -candidate['mtime'],                      # Modification time (newer first)
                candidate['name'].lower()                 # Name (alphabetical)
            )
        
        return sorted(candidates, key=sort_key)
    
    def discover_candidate_files(self, job: Job) -> CandidateFileResult:
        """
        Discover candidate files for a job
        
        Returns backward-compatible result with 'files' list and 'files_detailed' list.
        """
        try:
            file_path = Path(job.file_path)
            directory = file_path.parent
            
            # Build relevance tokens
            tokens = self._build_relevance_tokens(job)
            
            # Scan directory for candidates
            candidates = self._scan_directory_for_candidates(directory, tokens, job)
            
            # Ensure original filename is included
            candidates = self._ensure_original_filename_included(candidates, job)
            
            # Sort by priority
            candidates = self._sort_candidates_by_priority(candidates)
            
            # Extract file names for backward compatibility
            file_names = [c['name'] for c in candidates]
            recommended = file_names[0] if file_names else None
            
            return CandidateFileResult(
                files=file_names,
                files_detailed=candidates,
                recommended=recommended
            )
        
        except Exception as e:
            # On error, return fallback payload with original filename if available
            fallback_name = job.original_filename if job and job.original_filename else None
            
            if fallback_name:
                files = [fallback_name]
                files_detailed = [{'name': fallback_name, 'mtime': 0}]
            else:
                files = []
                files_detailed = []
            
            return CandidateFileResult(
                files=files,
                files_detailed=files_detailed,
                recommended=fallback_name
            )
