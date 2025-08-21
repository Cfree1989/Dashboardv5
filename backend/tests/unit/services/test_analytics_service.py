import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
from app.services.analytics_service import AnalyticsService
from app.services.interfaces.analytics_service_interface import DateRange, AnalyticsFilters
from app.models.job import Job
from app.models.event import Event
from app.models.payment import Payment


class TestAnalyticsService:
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
    
    def test_get_overview_metrics_cache_miss(self):
        """Test overview metrics calculates data when cache miss"""
        self.mock_cache.get.return_value = None
        
        with patch('app.services.analytics_service.Job') as mock_job:
            # Mock job query results
            mock_job.query.filter.return_value.with_entities.return_value.group_by.return_value.all.return_value = [
                ('PENDING', 5), ('COMPLETED', 3)
            ]
            mock_job.query.filter.return_value.count.return_value = 8
            
            with patch('app.services.analytics_service.Event') as mock_event:
                # Mock event queries for turnaround and rejections
                mock_event.query.filter.return_value.all.return_value = []
                
                # Mock the helper methods to avoid SQLAlchemy query issues
                with patch.object(self.analytics_service, '_calculate_avg_turnaround', return_value=2.5):
                    with patch.object(self.analytics_service, '_count_recent_rejections', return_value=1):
                        result = self.analytics_service.get_overview_metrics(self.date_range, self.filters)
                        
                        assert 'by_status' in result
                        assert 'in_queue' in result
                        assert 'total_submissions' in result
                        assert 'date_range' in result
                        self.mock_cache.set.assert_called_once()
    
    def test_get_trend_data_cache_hit(self):
        """Test trend data returns cached data when available"""
        cached_data = {'submissions': [], 'approvals': []}
        self.mock_cache.get.return_value = cached_data
        
        result = self.analytics_service.get_trend_data(self.date_range, self.filters)
        
        assert result == cached_data
        self.mock_cache.get.assert_called_once()
    
    def test_get_trend_data_cache_miss(self):
        """Test trend data calculates data when cache miss"""
        self.mock_cache.get.return_value = None
        
        with patch('app.services.analytics_service.Event') as mock_event:
            # Mock event queries
            mock_event.query.filter.return_value.all.return_value = []
            
            # Mock the helper methods to avoid SQLAlchemy query issues
            with patch.object(self.analytics_service, '_calculate_avg_turnaround', return_value=2.5):
                result = self.analytics_service.get_trend_data(self.date_range, self.filters)
                
                assert 'submissions' in result
                assert 'approvals' in result
                assert 'date_range' in result
                self.mock_cache.set.assert_called_once()
    
    def test_get_resource_metrics_cache_hit(self):
        """Test resource metrics returns cached data when available"""
        cached_data = {'printing_throughput': 10, 'printer_utilization': {}}
        self.mock_cache.get.return_value = cached_data
        
        result = self.analytics_service.get_resource_metrics(self.date_range, self.filters)
        
        assert result == cached_data
        self.mock_cache.get.assert_called_once()
    
    def test_get_resource_metrics_cache_miss(self):
        """Test resource metrics calculates data when cache miss"""
        self.mock_cache.get.return_value = None
        
        with patch('app.services.analytics_service.Job') as mock_job:
            # Mock job query results
            mock_job.query.filter.return_value.all.return_value = []
            
            with patch('app.services.analytics_service.Event') as mock_event:
                mock_event.query.filter.return_value.first.return_value = None
                
                result = self.analytics_service.get_resource_metrics(self.date_range, self.filters)
                
                assert 'printing_throughput' in result
                assert 'printer_utilization' in result
                assert 'material_consumption_g' in result
                assert 'queue_age_buckets' in result
                self.mock_cache.set.assert_called_once()
    
    def test_get_financial_summary_cache_hit(self):
        """Test financial summary returns cached data when available"""
        cached_data = {'total_revenue_cents': 5000, 'payment_count': 10}
        self.mock_cache.get.return_value = cached_data
        
        result = self.analytics_service.get_financial_summary(self.date_range, self.filters)
        
        assert result == cached_data
        self.mock_cache.get.assert_called_once()
    
    def test_get_financial_summary_cache_miss(self):
        """Test financial summary calculates data when cache miss"""
        self.mock_cache.get.return_value = None
        
        with patch('app.services.analytics_service.Payment') as mock_payment:
            # Mock payment query results
            mock_payment.query.filter.return_value.all.return_value = []
            
            with patch('app.services.analytics_service.Job') as mock_job:
                mock_job.query.filter.return_value.all.return_value = []
                
                result = self.analytics_service.get_financial_summary(self.date_range, self.filters)
                
                assert 'revenue_over_time' in result
                assert 'total_revenue_cents' in result
                assert 'payment_count' in result
                assert 'date_range' in result
                self.mock_cache.set.assert_called_once()
    
    def test_calculate_avg_turnaround_with_data(self):
        """Test average turnaround calculation with valid data"""
        # Mock completed events
        mock_completed_event = Mock()
        mock_completed_event.job_id = 'job1'
        mock_completed_event.timestamp = datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc)
        
        # Mock created events
        mock_created_event = Mock()
        mock_created_event.job_id = 'job1'
        mock_created_event.timestamp = datetime(2024, 1, 15, 10, 0, tzinfo=timezone.utc)
        
        with patch('app.services.analytics_service.Event') as mock_event:
            mock_event.query.filter.return_value.all.side_effect = [
                [mock_completed_event],  # Completed events
                [mock_created_event]     # Created events
            ]
            
            result = self.analytics_service._calculate_avg_turnaround(self.date_range, self.filters)
            
            assert result == 2.0  # 2 hours difference
    
    def test_calculate_avg_turnaround_no_data(self):
        """Test average turnaround calculation with no data"""
        with patch('app.services.analytics_service.Event') as mock_event:
            mock_event.query.filter.return_value.all.return_value = []
            
            result = self.analytics_service._calculate_avg_turnaround(self.date_range, self.filters)
            
            assert result is None
    
    def test_count_recent_rejections_with_filters(self):
        """Test rejection counting with filters applied"""
        mock_rejection_event = Mock()
        mock_rejection_event.job_id = 'job1'
        
        mock_job = Mock()
        mock_job.printer = 'Prusa MK4S'
        mock_job.discipline = 'Computer Science'
        
        with patch('app.services.analytics_service.Event') as mock_event:
            mock_event.query.filter.return_value.all.return_value = [mock_rejection_event]
            
            with patch('app.services.analytics_service.Job') as mock_job_model:
                mock_job_model.query.get.return_value = mock_job
                
                result = self.analytics_service._count_recent_rejections(self.date_range, self.filters)
                
                assert result == 1
    
    def test_count_recent_rejections_filtered_out(self):
        """Test rejection counting filters out non-matching jobs"""
        mock_rejection_event = Mock()
        mock_rejection_event.job_id = 'job1'
        
        mock_job = Mock()
        mock_job.printer = 'Different Printer'  # Doesn't match filter
        mock_job.discipline = 'Computer Science'
        
        with patch('app.services.analytics_service.Event') as mock_event:
            mock_event.query.filter.return_value.all.return_value = [mock_rejection_event]
            
            with patch('app.services.analytics_service.Job') as mock_job_model:
                mock_job_model.query.get.return_value = mock_job
                
                result = self.analytics_service._count_recent_rejections(self.date_range, self.filters)
                
                assert result == 0
    
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
    
    def test_calculate_revenue_metrics(self):
        """Test revenue metrics calculation"""
        mock_payment = Mock()
        mock_payment.paid_ts = datetime(2024, 1, 15, 12, 0, tzinfo=timezone.utc)
        mock_payment.price_cents = 500
        mock_payment.paid_by_staff = 'Staff Member'
        
        mock_job = Mock()
        mock_job.printer = 'Prusa MK4S'
        mock_job.discipline = 'Computer Science'
        
        with patch('app.services.analytics_service.Payment') as mock_payment_model:
            mock_payment_model.query.filter.return_value.all.return_value = [mock_payment]
            
            with patch('app.services.analytics_service.Job') as mock_job_model:
                mock_job_model.query.get.return_value = mock_job
                
                result = self.analytics_service._calculate_revenue_metrics(self.date_range, self.filters)
                
                assert result['total_revenue_cents'] == 500
                assert result['payment_count'] == 1
                assert result['avg_ticket_usd'] == 5.0
                assert result['staff_payments']['Staff Member'] == 1
    
    def test_cache_key_generation(self):
        """Test cache key generation includes all relevant parameters"""
        self.mock_cache.get.return_value = None
        
        with patch('app.services.analytics_service.Job') as mock_job:
            mock_job.query.filter.return_value.with_entities.return_value.group_by.return_value.all.return_value = []
            mock_job.query.filter.return_value.count.return_value = 0
            
            with patch('app.services.analytics_service.Event') as mock_event:
                mock_event.query.filter.return_value.all.return_value = []
                
                self.analytics_service.get_overview_metrics(self.date_range, self.filters)
                
                # Verify cache key includes all parameters
                cache_call = self.mock_cache.get.call_args[0][0]
                assert cache_call[0] == 'overview'
                assert '2024-01-01' in str(cache_call[1])  # start date
                assert '2024-01-31' in str(cache_call[2])  # end date
                assert cache_call[3] == 'Prusa MK4S'       # printer filter
                assert cache_call[4] == 'Computer Science' # discipline filter
    
    def test_filters_applied_correctly(self):
        """Test that filters are applied correctly to queries"""
        self.mock_cache.get.return_value = None
        
        with patch('app.services.analytics_service.Job') as mock_job:
            mock_job.query.filter.return_value.with_entities.return_value.group_by.return_value.all.return_value = []
            mock_job.query.filter.return_value.count.return_value = 0
            
            with patch('app.services.analytics_service.Event') as mock_event:
                mock_event.query.filter.return_value.all.return_value = []
                
                self.analytics_service.get_overview_metrics(self.date_range, self.filters)
                
                # Verify filter calls were made
                mock_job.query.filter.assert_called()
                # Should have been called for both printer and discipline filters
                assert mock_job.query.filter.call_count >= 2
    
    def test_date_range_handling(self):
        """Test that date range is properly handled in queries"""
        self.mock_cache.get.return_value = None
        
        with patch('app.services.analytics_service.Job') as mock_job:
            mock_job.query.filter.return_value.with_entities.return_value.group_by.return_value.all.return_value = []
            mock_job.query.filter.return_value.count.return_value = 0
            
            with patch('app.services.analytics_service.Event') as mock_event:
                mock_event.query.filter.return_value.all.return_value = []
                
                self.analytics_service.get_overview_metrics(self.date_range, self.filters)
                
                # Verify date range is included in cache key
                cache_call = self.mock_cache.get.call_args[0][0]
                assert '2024-01-01' in str(cache_call[1])
                assert '2024-01-31' in str(cache_call[2])
