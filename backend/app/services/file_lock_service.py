# Import alias for backward compatibility
# Tests expect this module to exist
from .infrastructure.file_lock_service import FileLockService

__all__ = ['FileLockService']
