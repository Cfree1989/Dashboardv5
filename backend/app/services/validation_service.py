# Import alias for backward compatibility
# Tests expect this module to exist
from ..business_logic.shared_services.validation_service import ValidationService, ValidationResult

__all__ = ['ValidationService', 'ValidationResult']
