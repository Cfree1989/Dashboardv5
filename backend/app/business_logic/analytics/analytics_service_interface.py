from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional

class DateRange:
    def __init__(self, start: datetime, end: datetime):
        self.start = start
        self.end = end

class AnalyticsFilters:
    def __init__(self, printer: Optional[str] = None, discipline: Optional[str] = None):
        self.printer = printer
        self.discipline = discipline

class IAnalyticsService(ABC):
    @abstractmethod
    def get_overview_metrics(self, date_range: DateRange, filters: AnalyticsFilters) -> Dict[str, Any]:
        """Get overview metrics for dashboard"""
        pass
    
    @abstractmethod
    def get_trend_data(self, date_range: DateRange, filters: AnalyticsFilters) -> Dict[str, Any]:
        """Get trend data over time"""
        pass
    
    @abstractmethod
    def get_resource_metrics(self, date_range: DateRange, filters: AnalyticsFilters) -> Dict[str, Any]:
        """Get resource utilization metrics"""
        pass
    
    @abstractmethod
    def get_financial_summary(self, date_range: DateRange, filters: AnalyticsFilters) -> Dict[str, Any]:
        """Get financial analysis data"""
        pass
