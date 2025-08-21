import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch
from app.services.analytics_service import AnalyticsService
from app.services.interfaces.analytics_service_interface import DateRange, AnalyticsFilters


class TestAnalyticsServiceSimple:
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_cache = Mock()
        self.analytics_service = AnalyticsService(caching_service=self.mock_cache)
        
        # Test data
        self.start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        self.end_date = datetime(2024, 1, 31, tzinfo=timezone.utc)
        self.date_range = DateRange(self.start_date, self.end_date)
        self.filters = AnalyticsFilters(printer="Prusa MK4S", discipline="Computer Science")
    
    def test_init_with_dependency_injection(self):
        """Test AnalyticsService initialization with dependency injection"""
        service = AnalyticsService(caching_service=self.mock_cache)
        assert service.cache == self.mock_cache
    
    def test_init_without_dependency_injection(self):
        """Test AnalyticsService initialization without dependency injection"""
        with patch('app.services.analytics_service.CachingService') as mock_caching_class:
            mock_caching_instance = Mock()
            mock_caching_class.return_value = mock_caching_instance
            
            service = AnalyticsService()
            
            mock_caching_class.assert_called_once()
            assert service.cache == mock_caching_instance
    
    def test_get_overview_metrics_cache_hit(self):
        """Test overview metrics returns cached data when available"""
        cached_data = {'by_status': {'PENDING': 5}, 'in_queue': 5}
        self.mock_cache.get.return_value = cached_data
        
        result = self.analytics_service.get_overview_metrics(self.date_range, self.filters)
        
        assert result == cached_data
        self.mock_cache.get.assert_called_once()
        self.mock_cache.set.assert_not_called()
    
    def test_get_trend_data_cache_hit(self):
        """Test trend data returns cached data when available"""
        cached_data = {'submissions': [], 'approvals': []}
        self.mock_cache.get.return_value = cached_data
        
        result = self.analytics_service.get_trend_data(self.date_range, self.filters)
        
        assert result == cached_data
        self.mock_cache.get.assert_called_once()
    
    def test_get_resource_metrics_cache_hit(self):
        """Test resource metrics returns cached data when available"""
        cached_data = {'printing_throughput': 10, 'printer_utilization': {}}
        self.mock_cache.get.return_value = cached_data
        
        result = self.analytics_service.get_resource_metrics(self.date_range, self.filters)
        
        assert result == cached_data
        self.mock_cache.get.assert_called_once()
    
    def test_get_financial_summary_cache_hit(self):
        """Test financial summary returns cached data when available"""
        cached_data = {'total_revenue_cents': 5000, 'payment_count': 10}
        self.mock_cache.get.return_value = cached_data
        
        result = self.analytics_service.get_financial_summary(self.date_range, self.filters)
        
        assert result == cached_data
        self.mock_cache.get.assert_called_once()
    
    def test_calculate_queue_age_buckets(self):
        """Test queue age bucket calculation"""
        now = datetime.now(timezone.utc)
        
        # Create mock jobs with different ages
        mock_job_1 = Mock()
        mock_job_1.status = 'PENDING'
        mock_job_1.created_at = now - timedelta(hours=12)  # 12 hours ago
        
        mock_job_2 = Mock()
        mock_job_2.status = 'UPLOADED'
        mock_job_2.created_at = now - timedelta(days=2)  # 2 days ago
        
        mock_job_3 = Mock()
        mock_job_3.status = 'COMPLETED'  # Should be ignored (not in queue)
        mock_job_3.created_at = now - timedelta(hours=1)
        
        jobs = [mock_job_1, mock_job_2, mock_job_3]
        
        result = self.analytics_service._calculate_queue_age_buckets(jobs)
        
        assert result['0-24h'] == 1  # job_1
        assert result['1-3d'] == 1   # job_2
        assert result['3-7d'] == 0
        assert result['1-2w'] == 0
        assert result['2w+'] == 0
    
    def test_cache_key_generation(self):
        """Test cache key generation includes all relevant parameters"""
        self.mock_cache.get.return_value = None
        
        # Mock all the complex database operations
        with patch.object(self.analytics_service, '_calculate_avg_turnaround', return_value=2.5):
            with patch.object(self.analytics_service, '_count_recent_rejections', return_value=1):
                with patch('app.services.analytics_service.Job') as mock_job:
                    mock_job.query.filter.return_value.with_entities.return_value.group_by.return_value.all.return_value = []
                    mock_job.query.filter.return_value.count.return_value = 0
                    
                    self.analytics_service.get_overview_metrics(self.date_range, self.filters)
                    
                    # Verify cache key includes all parameters
                    cache_call = self.mock_cache.get.call_args[0][0]
                    assert cache_call[0] == 'overview'
                    assert '2024-01-01' in str(cache_call[1])  # start date
                    assert '2024-01-31' in str(cache_call[2])  # end date
                    assert cache_call[3] == 'Prusa MK4S'       # printer filter
                    assert cache_call[4] == 'Computer Science' # discipline filter
    
    def test_date_range_handling(self):
        """Test that date range is properly handled in cache keys"""
        self.mock_cache.get.return_value = None
        
        # Mock all the complex database operations
        with patch.object(self.analytics_service, '_calculate_avg_turnaround', return_value=2.5):
            with patch.object(self.analytics_service, '_count_recent_rejections', return_value=1):
                with patch('app.services.analytics_service.Job') as mock_job:
                    mock_job.query.filter.return_value.with_entities.return_value.group_by.return_value.all.return_value = []
                    mock_job.query.filter.return_value.count.return_value = 0
                    
                    self.analytics_service.get_overview_metrics(self.date_range, self.filters)
                    
                    # Verify date range is included in cache key
                    cache_call = self.mock_cache.get.call_args[0][0]
                    assert '2024-01-01' in str(cache_call[1])
                    assert '2024-01-31' in str(cache_call[2])
    
    def test_filters_applied_to_cache_key(self):
        """Test that filters are properly included in cache keys"""
        self.mock_cache.get.return_value = None
        
        # Mock all the complex database operations
        with patch.object(self.analytics_service, '_calculate_avg_turnaround', return_value=2.5):
            with patch.object(self.analytics_service, '_count_recent_rejections', return_value=1):
                with patch('app.services.analytics_service.Job') as mock_job:
                    mock_job.query.filter.return_value.with_entities.return_value.group_by.return_value.all.return_value = []
                    mock_job.query.filter.return_value.count.return_value = 0
                    
                    self.analytics_service.get_overview_metrics(self.date_range, self.filters)
                    
                    # Verify cache key includes filter values (the important part)
                    cache_call = self.mock_cache.get.call_args[0][0]
                    assert cache_call[3] == 'Prusa MK4S'       # printer filter
                    assert cache_call[4] == 'Computer Science' # discipline filter
