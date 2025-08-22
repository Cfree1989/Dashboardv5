# Services Package
# Emergency Service Decomposition - Clean Architecture
# 
# Import Structure:
# 1. Infrastructure Services (Low-level technical services)
# 2. Foundation Services (Shared business logic services)
# 3. Analytics Services (Business intelligence services)
# 4. Backward Compatibility (Import aliases and interfaces)
#
# Note: Job lifecycle and orchestration services are intentionally excluded
# to prevent circular import issues. These should be imported directly
# where needed rather than through this package.

# =============================================================================
# 1. INFRASTRUCTURE SERVICES (Low-level technical services)
# =============================================================================
from .infrastructure import AtomicFileService, FileLockService, PaymentService

# =============================================================================
# 2. FOUNDATION SERVICES (Shared business logic services)
# =============================================================================
# Import aliases for services that moved to business_logic structure
# This provides backward compatibility for existing imports
from ..business_logic.shared_services.validation_service import ValidationService, ValidationResult
from ..business_logic.shared_services.response_service import ResponseService
from ..business_logic.shared_services.auth_service import *
from ..business_logic.shared_services.catalog_service import CatalogService
from ..business_logic.shared_services.token_service import *
from ..business_logic.shared_services.error_handling_service import *
from ..business_logic.shared_services.event_service import *
from ..business_logic.shared_services.db_transaction_service import *

# =============================================================================
# 3. ANALYTICS SERVICES (Business intelligence services)
# =============================================================================
from ..business_logic.analytics.analytics_service import AnalyticsService
from ..business_logic.analytics.caching_service import CachingService

# =============================================================================
# 4. BACKWARD COMPATIBILITY (Import aliases and interfaces)
# =============================================================================
# Create interfaces alias for backward compatibility
class interfaces:
    from ..business_logic.analytics.analytics_service_interface import DateRange, AnalyticsFilters

# =============================================================================
# EXPORT LIST (Public API)
# =============================================================================
__all__ = [
    # Infrastructure Services
    'AtomicFileService', 
    'FileLockService',
    'PaymentService',
    
    # Foundation Services
    'ValidationService',
    'ValidationResult', 
    'ResponseService',
    'CatalogService',
    
    # Analytics Services
    'AnalyticsService',
    'CachingService',
    
    # Backward Compatibility
    'interfaces',
]
