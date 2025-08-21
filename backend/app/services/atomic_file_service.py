# Import alias for backward compatibility
# Tests expect this module to exist
from .infrastructure.atomic_file_service import AtomicFileService, AtomicFileOperation, get_atomic_file_service

__all__ = ['AtomicFileService', 'AtomicFileOperation', 'get_atomic_file_service']
