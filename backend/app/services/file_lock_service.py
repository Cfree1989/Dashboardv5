# Import alias for backward compatibility
# Tests expect this module to exist
from .infrastructure.file_lock_service import FileLockService, get_file_lock_service

__all__ = ['FileLockService', 'get_file_lock_service']
