import pytest
from datetime import datetime, timedelta, timezone
from app.utils.date_utils import DateUtils
from unittest.mock import patch
from flask import Flask

class TestDateUtils:
    
    def test_parse_date_range_with_explicit_dates(self):
        """Test parse_date_range with explicit start and end dates"""
        app = Flask(__name__)
        with app.test_request_context('/?start_date=2024-01-01T00:00:00&end_date=2024-01-07T23:59:59'):
            start, end = DateUtils.parse_date_range()
            
            assert start == datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
            assert end == datetime(2024, 1, 7, 23, 59, 59, tzinfo=timezone.utc)
    
    def test_parse_date_range_with_days_parameter(self):
        """Test parse_date_range with days parameter"""
        app = Flask(__name__)
        with app.test_request_context('/?days=14'):
            with patch('app.utils.date_utils.datetime') as mock_datetime:
                mock_now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
                mock_datetime.now.return_value = mock_now
                
                start, end = DateUtils.parse_date_range()
                
                expected_start = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
                assert start == expected_start
                assert end == mock_now
    
    def test_parse_date_range_default_days(self):
        """Test parse_date_range with default 7 days"""
        app = Flask(__name__)
        with app.test_request_context('/'):
            with patch('app.utils.date_utils.datetime') as mock_datetime:
                mock_now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
                mock_datetime.now.return_value = mock_now
                
                start, end = DateUtils.parse_date_range()
                
                expected_start = datetime(2024, 1, 8, 12, 0, 0, tzinfo=timezone.utc)
                assert start == expected_start
                assert end == mock_now
    
    def test_parse_date_range_invalid_dates(self):
        """Test parse_date_range with invalid date format falls back to days"""
        app = Flask(__name__)
        with app.test_request_context('/?start_date=invalid-date&end_date=also-invalid'):
            with patch('app.utils.date_utils.datetime') as mock_datetime:
                # Mock only the now() method, not the entire datetime module
                mock_now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
                mock_datetime.now.return_value = mock_now
                # Allow fromisoformat to work normally for the ValueError
                mock_datetime.fromisoformat.side_effect = ValueError("Invalid date format")
                
                start, end = DateUtils.parse_date_range()
                
                expected_start = datetime(2024, 1, 8, 12, 0, 0, tzinfo=timezone.utc)
                assert start == expected_start
                assert end == mock_now
    
    def test_calculate_retention_cutoff(self):
        """Test calculate_retention_cutoff"""
        with patch('app.utils.date_utils.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
            mock_datetime.utcnow.return_value = mock_now
            
            cutoff = DateUtils.calculate_retention_cutoff(30)
            
            expected_cutoff = datetime(2023, 12, 16, 12, 0, 0, tzinfo=timezone.utc)
            assert cutoff == expected_cutoff
    
    def test_format_date_for_display(self):
        """Test format_date_for_display"""
        test_date = datetime(2024, 1, 15, 12, 30, 45, tzinfo=timezone.utc)
        
        formatted = DateUtils.format_date_for_display(test_date)
        
        assert formatted == "2024-01-15 12:30:45 UTC"
    
    def test_get_current_utc(self):
        """Test get_current_utc"""
        with patch('app.utils.date_utils.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
            mock_datetime.now.return_value = mock_now
            
            current = DateUtils.get_current_utc()
            
            assert current == mock_now
    
    def test_is_within_range(self):
        """Test is_within_range"""
        start = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, 23, 59, 59, tzinfo=timezone.utc)
        
        # Test date within range
        within_date = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        assert DateUtils.is_within_range(within_date, start, end) is True
        
        # Test date at start boundary
        assert DateUtils.is_within_range(start, start, end) is True
        
        # Test date at end boundary
        assert DateUtils.is_within_range(end, start, end) is True
        
        # Test date before range
        before_date = datetime(2023, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        assert DateUtils.is_within_range(before_date, start, end) is False
        
        # Test date after range
        after_date = datetime(2024, 2, 1, 0, 0, 0, tzinfo=timezone.utc)
        assert DateUtils.is_within_range(after_date, start, end) is False
