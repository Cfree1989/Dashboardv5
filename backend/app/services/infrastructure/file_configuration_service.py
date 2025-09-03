"""
File Configuration Service

Centralized configuration service for file handling operations.
Consolidates file type definitions, size limits, and validation rules
from across the application to provide a single source of truth.
"""

import os
import struct
from typing import Set, Dict, Optional, Tuple, Union, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class FileConfigurationService:
    """Centralized service for file handling configuration"""
    
    def __init__(self):
        self._allowed_extensions = self._load_allowed_extensions()
        self._extension_priority = self._load_extension_priority()
        self._max_file_size = self._load_max_file_size()
        self._storage_paths = self._load_storage_paths()
        self._min_file_size = self._load_min_file_size()
        self._status_to_dir = self._load_status_to_dir_mapping()
    
    def _load_allowed_extensions(self) -> Set[str]:
        """Load allowed file extensions from environment configuration"""
        # Default extensions for 3D printing files
        default_exts = 'stl,obj,3mf,form,idea'
        exts_env = os.environ.get('ALLOWED_FILE_EXTENSIONS', default_exts)
        
        extensions = set()
        for ext in exts_env.split(','):
            ext = ext.strip().lower()
            if ext:
                # Ensure extensions start with dot for consistency
                if not ext.startswith('.'):
                    ext = f'.{ext}'
                extensions.add(ext)
        
        logger.info(f"Loaded allowed extensions: {extensions}")
        return extensions
    
    def _load_extension_priority(self) -> Dict[str, int]:
        """Load extension priority ranking from environment configuration"""
        # Default priority: newer formats first, then older ones
        default_priority = '3mf,form,idea,stl,obj'
        priority_env = os.environ.get('FILE_EXTENSION_PRIORITY', default_priority)
        
        priority_dict = {}
        for idx, ext in enumerate(priority_env.split(',')):
            ext = ext.strip().lower()
            if ext:
                # Ensure extensions start with dot for consistency
                if not ext.startswith('.'):
                    ext = f'.{ext}'
                priority_dict[ext] = idx
        
        logger.info(f"Loaded extension priority: {priority_dict}")
        return priority_dict
    
    def _load_max_file_size(self) -> int:
        """Load maximum file size from environment configuration"""
        # Default: 50MB
        default_size = 50 * 1024 * 1024
        size_env = os.environ.get('MAX_FILE_SIZE_MB', '50')
        
        try:
            max_size_mb = int(size_env)
            max_size_bytes = max_size_mb * 1024 * 1024
            logger.info(f"Loaded max file size: {max_size_mb}MB ({max_size_bytes} bytes)")
            return max_size_bytes
        except (ValueError, TypeError):
            logger.warning(f"Invalid MAX_FILE_SIZE_MB value: {size_env}, using default: 50MB")
            return default_size
    
    def _load_min_file_size(self) -> int:
        """Load minimum file size from environment configuration"""
        # Default: 1KB to prevent empty files
        default_size = 1024
        size_env = os.environ.get('MIN_FILE_SIZE_KB', '1')
        
        try:
            min_size_kb = int(size_env)
            min_size_bytes = min_size_kb * 1024
            logger.info(f"Loaded min file size: {min_size_kb}KB ({min_size_bytes} bytes)")
            return min_size_bytes
        except (ValueError, TypeError):
            logger.warning(f"Invalid MIN_FILE_SIZE_KB value: {size_env}, using default: 1KB")
            return default_size
    
    def _load_storage_paths(self) -> Dict[str, str]:
        """Load storage path configuration from environment"""
        storage_root = os.environ.get('STORAGE_PATH', 'storage')
        
        paths = {
            'root': storage_root,
            'uploaded': os.path.join(storage_root, 'Uploaded'),
            'pending': os.path.join(storage_root, 'Pending'),
            'ready_to_print': os.path.join(storage_root, 'ReadyToPrint'),
            'printing': os.path.join(storage_root, 'Printing'),
            'completed': os.path.join(storage_root, 'Completed'),
            'rejected': os.path.join(storage_root, 'Rejected'),
            'archived': os.path.join(storage_root, 'Archived')
        }
        
        logger.info(f"Loaded storage paths: {paths}")
        return paths
    
    def _load_status_to_dir_mapping(self) -> Dict[str, str]:
        """Load centralized status to directory mapping"""
        # Standard status to directory mapping for the application
        # This centralizes the scattered STATUS_TO_DIR mappings
        return {
            'UPLOADED': 'Uploaded',
            'PENDING': 'Pending', 
            'READYTOPRINT': 'ReadyToPrint',
            'PRINTING': 'Printing',
            'COMPLETED': 'Completed',
            'PAIDPICKEDUP': 'PaidPickedUp',
            'REJECTED': 'Rejected',
            'ARCHIVED': 'Archived',
        }
    
    @property
    def allowed_extensions(self) -> Set[str]:
        """Get the set of allowed file extensions"""
        return self._allowed_extensions.copy()
    
    @property
    def extension_priority(self) -> Dict[str, int]:
        """Get the extension priority mapping"""
        return self._extension_priority.copy()
    
    @property
    def max_file_size(self) -> int:
        """Get the maximum allowed file size in bytes"""
        return self._max_file_size
    
    @property
    def max_file_size_mb(self) -> int:
        """Get the maximum allowed file size in MB"""
        return self._max_file_size // (1024 * 1024)
    
    @property
    def min_file_size(self) -> int:
        """Get the minimum allowed file size in bytes"""
        return self._min_file_size
    
    @property
    def min_file_size_kb(self) -> int:
        """Get the minimum allowed file size in KB"""
        return self._min_file_size // 1024
    
    @property
    def storage_paths(self) -> Dict[str, str]:
        """Get the storage path configuration"""
        return self._storage_paths.copy()
    
    def get_storage_path(self, status: str) -> str:
        """Get storage path for a specific job status"""
        # Map common status variations to storage path keys
        status_mapping = {
            'uploaded': 'uploaded',
            'pending': 'pending',
            'readytoprint': 'ready_to_print',
            'ready_to_print': 'ready_to_print',
            'ready to print': 'ready_to_print',
            'printing': 'printing',
            'completed': 'completed',
            'rejected': 'rejected',
            'archived': 'archived'
        }
        
        status_key = status.lower().strip()
        mapped_key = status_mapping.get(status_key, status_key)
        return self._storage_paths.get(mapped_key, self._storage_paths['root'])
    
    def is_allowed_extension(self, filename: str) -> bool:
        """Check if a filename has an allowed extension"""
        if not filename or '.' not in filename:
            return False
        
        extension = f".{filename.rsplit('.', 1)[1].lower()}"
        return extension in self._allowed_extensions
    
    def get_extension_priority(self, filename: str) -> int:
        """Get priority rank for a file extension (lower is better)"""
        if not filename or '.' not in filename:
            return len(self._extension_priority) + 1
        
        extension = f".{filename.rsplit('.', 1)[1].lower()}"
        return self._extension_priority.get(extension, len(self._extension_priority) + 1)
    
    def validate_file_size(self, file_size: int) -> bool:
        """Check if a file size is within allowed limits"""
        return self._min_file_size <= file_size <= self._max_file_size
    
    def get_file_size_validation_error(self, file_size: int) -> Optional[str]:
        """Get specific error message for file size validation failures"""
        if file_size < self._min_file_size:
            return f"File too small (minimum {self.min_file_size_kb}KB)"
        elif file_size > self._max_file_size:
            return f"File too large (maximum {self.max_file_size_mb}MB)"
        return None
    
    def validate_file_header(self, file_content: bytes, filename: str) -> Tuple[bool, Optional[str]]:
        """Validate file header to detect file type spoofing"""
        if not file_content:
            return False, "File is empty"
        
        if len(file_content) < 16:  # Minimum size for header validation
            return False, "File too small for header validation"
        
        extension = self._get_file_extension(filename)
        if not extension:
            return False, "No file extension found"
        
        # Validate header based on file extension
        if extension == '.stl':
            return self._validate_stl_header(file_content)
        elif extension == '.obj':
            return self._validate_obj_header(file_content)
        elif extension == '.3mf':
            return self._validate_3mf_header(file_content)
        elif extension in ['.form', '.idea']:
            return self._validate_zip_based_header(file_content)
        else:
            # For unknown extensions, just check basic file structure
            return self._validate_generic_header(file_content)
    
    def _get_file_extension(self, filename: str) -> Optional[str]:
        """Extract file extension from filename"""
        if not filename or '.' not in filename:
            return None
        return f".{filename.rsplit('.', 1)[1].lower()}"
    
    def _validate_stl_header(self, content: bytes) -> Tuple[bool, Optional[str]]:
        """Validate STL file header (binary or ASCII format)"""
        # Check for ASCII STL (starts with "solid")
        if content.startswith(b'solid'):
            # Verify it contains STL keywords
            content_str = content[:1024].decode('utf-8', errors='ignore').lower()
            if 'facet' in content_str and 'normal' in content_str:
                return True, None
        
        # Check for binary STL (80-byte header + 4-byte triangle count)
        if len(content) >= 84:
            try:
                # Skip 80-byte header, read triangle count
                triangle_count = struct.unpack('<I', content[80:84])[0]
                # Basic sanity check: triangle count should be reasonable
                if 0 <= triangle_count <= 1000000:  # Max 1M triangles
                    return True, None
            except struct.error:
                pass
        
        return False, "Invalid STL file format"
    
    def _validate_obj_header(self, content: bytes) -> Tuple[bool, Optional[str]]:
        """Validate OBJ file header"""
        # OBJ files are text-based, check for common keywords
        content_str = content[:1024].decode('utf-8', errors='ignore').lower()
        
        # Check for OBJ keywords
        obj_keywords = ['v ', 'vt ', 'vn ', 'f ', 'g ', 'o ']
        found_keywords = [kw for kw in obj_keywords if kw in content_str]
        
        if found_keywords:
            return True, None
        
        return False, "Invalid OBJ file format"
    
    def _validate_3mf_header(self, content: bytes) -> Tuple[bool, Optional[str]]:
        """Validate 3MF file header (ZIP-based format)"""
        # 3MF files are ZIP archives with specific structure
        if content.startswith(b'PK\x03\x04'):  # ZIP file signature
            # Check for 3MF-specific files in ZIP
            content_str = content[:2048].decode('utf-8', errors='ignore').lower()
            if '3dmodel.model' in content_str or '[content_types].xml' in content_str:
                return True, None
        
        return False, "Invalid 3MF file format"
    
    def _validate_zip_based_header(self, content: bytes) -> Tuple[bool, Optional[str]]:
        """Validate ZIP-based file headers (Form, Idea)"""
        # Form and Idea files are typically ZIP-based
        if content.startswith(b'PK\x03\x04'):  # ZIP file signature
            return True, None
        
        return False, "Invalid ZIP-based file format"
    
    def _validate_generic_header(self, content: bytes) -> Tuple[bool, Optional[str]]:
        """Validate generic file header for unknown extensions"""
        # Basic validation: file should not be empty and should have some structure
        if len(content) < 10:
            return False, "File too small"
        
        # Check for common binary file signatures that might be dangerous
        dangerous_signatures = [
            b'MZ',  # Windows executable
            b'\x7fELF',  # Linux executable
            b'\xfe\xed\xfa',  # Mach-O executable
        ]
        
        for sig in dangerous_signatures:
            if content.startswith(sig):
                return False, "File appears to be an executable"
        
        return True, None
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal attacks"""
        if not filename:
            return "unnamed_file"
        
        # Remove path separators and dangerous characters
        dangerous_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        sanitized = filename
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '_')
        
        # Remove leading/trailing dots and spaces
        sanitized = sanitized.strip('. ')
        
        # Ensure filename is not empty after sanitization
        if not sanitized:
            return "unnamed_file"
        
        return sanitized
    
    def validate_filename_security(self, filename: str) -> Tuple[bool, Optional[str]]:
        """Validate filename for security issues"""
        if not filename:
            return False, "No filename provided"
        
        # Check for path traversal attempts
        if '..' in filename or filename.startswith('/') or filename.startswith('\\'):
            return False, "Path traversal attempt detected"
        
        # Check for dangerous characters
        dangerous_chars = ['*', '?', '"', '<', '>', '|', ':', '\x00']
        for char in dangerous_chars:
            if char in filename:
                return False, f"Dangerous character '{char}' in filename"
        
        # Check for reserved names (Windows)
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
                         'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
                         'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
        
        name_without_ext = filename.rsplit('.', 1)[0].upper()
        if name_without_ext in reserved_names:
            return False, f"Reserved filename '{name_without_ext}' not allowed"
        
        return True, None
    
    def get_allowed_extensions_list(self) -> list:
        """Get allowed extensions as a list (for backward compatibility)"""
        return list(self._allowed_extensions)
    
    def get_allowed_extensions_set(self) -> set:
        """Get allowed extensions as a set (for backward compatibility)"""
        return self._allowed_extensions.copy()
    
    def reload_configuration(self):
        """Reload configuration from environment variables"""
        logger.info("Reloading file configuration from environment")
        self._allowed_extensions = self._load_allowed_extensions()
        self._extension_priority = self._load_extension_priority()
        self._max_file_size = self._load_max_file_size()
        self._min_file_size = self._load_min_file_size()
        self._storage_paths = self._load_storage_paths()
        self._status_to_dir = self._load_status_to_dir_mapping()

    # ========================================================================
    # CENTRALIZED PATH MANAGEMENT METHODS
    # ========================================================================

    @property
    def status_to_dir_mapping(self) -> Dict[str, str]:
        """Get the centralized status to directory mapping"""
        return self._status_to_dir.copy()

    def get_storage_root(self) -> Path:
        """Get the storage root directory path"""
        return Path(self._storage_paths['root'])

    def get_status_directory(self, status: str) -> Path:
        """Get the directory path for a specific job status"""
        status_upper = status.upper().strip()
        dir_name = self._status_to_dir.get(status_upper, 'Uploaded')
        return self.get_storage_root() / dir_name

    def get_job_file_path(self, filename: str, status: str = 'UPLOADED') -> Path:
        """Get the complete file path for a job file"""
        status_dir = self.get_status_directory(status)
        sanitized_filename = self.sanitize_filename(filename)
        return status_dir / sanitized_filename

    def get_job_metadata_path(self, filename: str, status: str = 'UPLOADED') -> Path:
        """Get the complete metadata path for a job file"""
        status_dir = self.get_status_directory(status)
        
        # Generate metadata filename from job filename
        if '.' in filename:
            base_name = filename.rsplit('.', 1)[0]
        else:
            base_name = filename
        
        sanitized_base = self.sanitize_filename(base_name)
        metadata_filename = f"{sanitized_base}_metadata.json"
        return status_dir / metadata_filename

    def get_unique_file_path(self, filename: str, status: str = 'UPLOADED') -> Tuple[Path, str]:
        """Get a unique file path by appending counter if file exists"""
        base_path = self.get_job_file_path(filename, status)
        
        # If file doesn't exist, return original path
        if not base_path.exists():
            return base_path, filename
            
        # Extract base name and extension
        if '.' in filename:
            base_name, extension = filename.rsplit('.', 1)
        else:
            base_name = filename
            extension = ''
            
        # Find unique filename with counter
        counter = 1
        while True:
            if extension:
                candidate_filename = f"{base_name}_{counter}.{extension}"
            else:
                candidate_filename = f"{base_name}_{counter}"
                
            candidate_path = self.get_job_file_path(candidate_filename, status)
            if not candidate_path.exists():
                return candidate_path, candidate_filename
            counter += 1
            
            # Safety check to prevent infinite loop
            if counter > 9999:
                raise RuntimeError("Cannot generate unique filename after 9999 attempts")

    def construct_standardized_filename(self, student_name: str, method: str, color: str, job_id: str, extension: str) -> str:
        """Construct a standardized filename following the application pattern"""
        # Normalize components (similar to submit.py logic)
        normalized_student = self._normalize_name_component(student_name or 'Student')
        normalized_method = self._normalize_simple_label(method or 'Method')
        normalized_color = self._normalize_simple_label(color or 'Color')
        
        # Ensure extension has dot prefix
        if not extension.startswith('.'):
            extension = f'.{extension}'
        
        return f"{normalized_student}_{normalized_method}_{normalized_color}_{job_id}{extension}"

    def _normalize_name_component(self, name: str) -> str:
        """Normalize a name component (from submit.py logic)"""
        if not name or not name.strip():
            return 'Student'
        parts = name.strip().replace('-', ' ').split()
        joined = ''.join(w.capitalize() for w in parts)
        return ''.join(ch for ch in joined if ch.isalnum()) or 'Student'

    def _normalize_simple_label(self, label: str) -> str:
        """Normalize a simple label component (from submit.py logic)"""
        if not label or not label.strip():
            return 'Value'
        parts = label.strip().replace('-', ' ').split()  
        labeled = ''.join(w.capitalize() for w in parts)
        return ''.join(ch for ch in labeled if ch.isalnum()) or 'Value'

    def validate_path_security(self, file_path: Union[str, Path]) -> Tuple[bool, Optional[str]]:
        """Validate that a file path is within the storage boundaries"""
        try:
            path_obj = Path(file_path).resolve()
            storage_root = self.get_storage_root().resolve()
            
            # Check if path is within storage root
            if not str(path_obj).startswith(str(storage_root)):
                return False, f"Path '{file_path}' is outside storage boundaries"
            
            # Check if path exists and is a file
            if path_obj.exists() and path_obj.is_dir():
                return False, f"Path '{file_path}' is a directory, not a file"
            
            return True, None
            
        except Exception as e:
            return False, f"Invalid path: {e}"

    def ensure_status_directory_exists(self, status: str) -> bool:
        """Ensure the status directory exists, creating if necessary"""
        try:
            status_dir = self.get_status_directory(status)
            status_dir.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Failed to create status directory for '{status}': {e}")
            return False

    def get_relative_path_from_storage_root(self, file_path: Union[str, Path]) -> Optional[str]:
        """Get relative path from storage root for a given file path"""
        try:
            path_obj = Path(file_path).resolve()
            storage_root = self.get_storage_root().resolve()
            
            if str(path_obj).startswith(str(storage_root)):
                return str(path_obj.relative_to(storage_root))
            return None
        except Exception:
            return None

    def infer_status_from_path(self, file_path: Union[str, Path]) -> Optional[str]:
        """Infer job status from file path location"""
        try:
            path_obj = Path(file_path)
            dir_name = path_obj.parent.name
            
            # Look up status by directory name
            for status, directory in self._status_to_dir.items():
                if directory == dir_name:
                    return status
            return None
        except Exception:
            return None

    def list_all_status_directories(self) -> Dict[str, Path]:
        """Get all status directories and their paths"""
        result = {}
        for status, dir_name in self._status_to_dir.items():
            result[status] = self.get_storage_root() / dir_name
        return result

    def get_storage_usage_info(self) -> Dict[str, Any]:
        """Get storage usage information for all status directories"""
        usage_info = {
            'storage_root': str(self.get_storage_root()),
            'directories': {},
            'total_files': 0,
            'total_size_bytes': 0
        }
        
        for status, dir_path in self.list_all_status_directories().items():
            dir_info = {
                'path': str(dir_path),
                'exists': dir_path.exists(),
                'file_count': 0,
                'size_bytes': 0
            }
            
            if dir_path.exists():
                try:
                    for file_path in dir_path.iterdir():
                        if file_path.is_file():
                            dir_info['file_count'] += 1
                            dir_info['size_bytes'] += file_path.stat().st_size
                except Exception as e:
                    logger.warning(f"Error scanning directory {dir_path}: {e}")
            
            usage_info['directories'][status] = dir_info
            usage_info['total_files'] += dir_info['file_count']
            usage_info['total_size_bytes'] += dir_info['size_bytes']
        
        return usage_info


# Global instance for easy access
_file_config_service = None


def get_file_configuration_service() -> FileConfigurationService:
    """Get the global file configuration service instance"""
    global _file_config_service
    if _file_config_service is None:
        _file_config_service = FileConfigurationService()
    return _file_config_service
