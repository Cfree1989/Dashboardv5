# Interfaces module for backward compatibility
from ...business_logic.analytics.analytics_service_interface import (
    DateRange,
    AnalyticsFilters,
    IAnalyticsService,
)

__all__ = [
    "DateRange",
    "AnalyticsFilters",
    "IAnalyticsService",
]
