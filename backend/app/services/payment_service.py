# Import alias for backward compatibility
# Tests expect this module to exist
from .infrastructure.payment_service import PaymentService

__all__ = ['PaymentService']
