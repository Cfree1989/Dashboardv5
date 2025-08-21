# backend/app/utils/date_utils.py
from datetime import datetime, timedelta, timezone
from flask import request
from typing import Tuple

class DateUtils:
    @staticmethod
    def parse_date_range() -> Tuple[datetime, datetime]:
        """Parse date range from query parameters - extracted from analytics.py"""
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date and end_date:
            try:
                start = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
                end = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
                return start, end
            except ValueError:
                pass
        
        days = int(request.args.get('days', 7))
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days)
        return start, end
    
    @staticmethod
    def calculate_retention_cutoff(retention_days: int) -> datetime:
        """Calculate cutoff date for archival/pruning operations"""
        return datetime.utcnow() - timedelta(days=retention_days)
    
    @staticmethod
    def format_date_for_display(date: datetime) -> str:
        """Format date for display in analytics and reports"""
        return date.strftime('%Y-%m-%d %H:%M:%S UTC')
    
    @staticmethod
    def get_current_utc() -> datetime:
        """Get current UTC datetime"""
        return datetime.now(timezone.utc)
    
    @staticmethod
    def is_within_range(date: datetime, start: datetime, end: datetime) -> bool:
        """Check if date is within the specified range (inclusive)"""
        return start <= date <= end
