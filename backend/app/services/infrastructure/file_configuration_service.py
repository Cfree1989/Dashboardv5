"""
File Configuration Service

Centralized configuration service for file handling operations.
Consolidates file type definitions, size limits, and validation rules
from across the application to provide a single source of truth.
"""

import os
from typing import Set, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class FileConfigurationService:
    """Centralized service for file handling configuration"""
    
    def __init__(self):
        self._allowed_extensions = self._load_allowed_extensions()
        self._extension_priority = self._load_extension_priority()
        self._max_file_size = self._load_max_file_size()
        self._storage_paths = self._load_storage_paths()
    
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
        return file_size <= self._max_file_size
    
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
        self._storage_paths = self._load_storage_paths()


# Global instance for easy access
_file_config_service = None


def get_file_configuration_service() -> FileConfigurationService:
    """Get the global file configuration service instance"""
    global _file_config_service
    if _file_config_service is None:
        _file_config_service = FileConfigurationService()
    return _file_config_service
