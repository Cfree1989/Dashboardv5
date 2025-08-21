# Services Package
# Emergency Service Decomposition - Clean Architecture

# Infrastructure Services (Low-level technical services)
from .infrastructure import file_service, AtomicFileService, FileLockService, PaymentService

# Import aliases for services that moved to business_logic structure
# This provides backward compatibility for existing imports

# Foundation services from business_logic.shared_services
from ..business_logic.shared_services.validation_service import ValidationService, ValidationResult
from ..business_logic.shared_services.response_service import ResponseService
from ..business_logic.shared_services.auth_service import *
from ..business_logic.shared_services.catalog_service import CatalogService
from ..business_logic.shared_services.token_service import *
from ..business_logic.shared_services.error_handling_service import *
from ..business_logic.shared_services.event_service import *
from ..business_logic.shared_services.db_transaction_service import *

# Analytics services from business_logic.analytics
from ..business_logic.analytics.analytics_service import AnalyticsService
from ..business_logic.analytics.caching_service import CachingService

# Job lifecycle services - import individually to avoid circular imports
# from ..business_logic.job_lifecycle.job_approval_service import *
# from ..business_logic.job_lifecycle.job_status_service import *
# from ..business_logic.job_lifecycle.job_transition_service import *

# Orchestration services - avoid importing here due to circular import
# from .orchestration.job_orchestration_service import JobOrchestrationService

# Create interfaces alias for backward compatibility
class interfaces:
    from ..business_logic.analytics.analytics_service_interface import DateRange, AnalyticsFilters

__all__ = [
    # Infrastructure
    'file_service',
    'AtomicFileService', 
    'FileLockService',
    'PaymentService',
    
    # Foundation Services
    'ValidationService',
    'ValidationResult', 
    'ResponseService',
    'CatalogService',
    
    # Analytics
    'AnalyticsService',
    'CachingService',
    
    # Interfaces
    'interfaces',
]
