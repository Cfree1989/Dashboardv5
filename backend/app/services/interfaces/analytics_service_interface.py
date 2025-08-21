# Import alias for backward compatibility
# Tests expect this module to exist
from ...business_logic.analytics.analytics_service_interface import DateRange, AnalyticsFilters, IAnalyticsService

__all__ = ['DateRange', 'AnalyticsFilters', 'IAnalyticsService']
