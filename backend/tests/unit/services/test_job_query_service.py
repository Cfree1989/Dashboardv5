"""
Tests for JobQueryService

Tests the job querying and filtering logic extracted from list_jobs and get_job_counts endpoints.
"""

import pytest
from unittest.mock import Mock, patch

from app.services.infrastructure.job_query_service import JobQueryService, JobFilters


class TestJobFilters:
    def test_init_all_none(self):
        """Test JobFilters initialization with all None values"""
        filters = JobFilters()
        
        assert filters.status is None
        assert filters.search is None
        assert filters.printer is None
        assert filters.discipline is None

    def test_init_with_values(self):
        """Test JobFilters initialization with specific values"""
        filters = JobFilters(
            status='PENDING',
            search='john',
            printer='Prusa MK4S', 
            discipline='Engineering'
        )
        
        assert filters.status == 'PENDING'
        assert filters.search == 'john'
        assert filters.printer == 'Prusa MK4S'
        assert filters.discipline == 'Engineering'


class TestJobQueryService:
    def setup_method(self):
        self.service = JobQueryService()
    
    @patch('app.services.infrastructure.job_query_service.Job')
    def test_list_jobs_no_filters(self, mock_job_model):
        """Test listing jobs with no filters"""
        # Mock the query chain
        mock_query = Mock()
        mock_job_model.query = mock_query
        mock_query.all.return_value = ['job1', 'job2', 'job3']
        
        filters = JobFilters()
        result = self.service.list_jobs(filters)
        
        # Should call query.all() without any filtering
        mock_query.all.assert_called_once()
        assert result == ['job1', 'job2', 'job3']

    @patch('app.services.infrastructure.job_query_service.Job')
    def test_list_jobs_with_status_filter(self, mock_job_model):
        """Test listing jobs with status filter"""
        # Mock the query chain
        mock_query = Mock()
        mock_filtered_query = Mock()
        mock_job_model.query = mock_query
        mock_query.filter_by.return_value = mock_filtered_query
        mock_filtered_query.all.return_value = ['filtered_job']
        
        filters = JobFilters(status='PENDING')
        result = self.service.list_jobs(filters)
        
        # Should apply status filter
        mock_query.filter_by.assert_called_with(status='PENDING')
        mock_filtered_query.all.assert_called_once()
        assert result == ['filtered_job']

    @patch('app.services.infrastructure.job_query_service.Job')
    def test_list_jobs_with_multiple_filters(self, mock_job_model):
        """Test listing jobs with multiple database filters"""
        # Mock the query chain  
        mock_query = Mock()
        mock_status_query = Mock()
        mock_printer_query = Mock()
        mock_discipline_query = Mock()
        
        mock_job_model.query = mock_query
        mock_query.filter_by.return_value = mock_status_query
        mock_status_query.filter_by.return_value = mock_printer_query
        mock_printer_query.filter_by.return_value = mock_discipline_query
        mock_discipline_query.all.return_value = ['multi_filtered_job']
        
        filters = JobFilters(
            status='PENDING',
            printer='Prusa MK4S',
            discipline='Engineering'
        )
        result = self.service.list_jobs(filters)
        
        # Should apply all filters in sequence
        mock_query.filter_by.assert_called_with(status='PENDING')
        mock_status_query.filter_by.assert_called_with(printer='Prusa MK4S')
        mock_printer_query.filter_by.assert_called_with(discipline='Engineering')
        mock_discipline_query.all.assert_called_once()
        assert result == ['multi_filtered_job']

    @patch('app.services.infrastructure.job_query_service.Job')
    def test_list_jobs_with_search_filter(self, mock_job_model):
        """Test listing jobs with search filter"""
        # Create mock jobs
        job1 = Mock()
        job1.student_name = 'John Doe'
        job1.student_email = 'john@example.com'
        
        job2 = Mock()
        job2.student_name = 'Jane Smith'
        job2.student_email = 'jane@example.com'
        
        job3 = Mock()
        job3.student_name = 'Johnny Apple'
        job3.student_email = 'johnny@example.com'
        
        # Mock the query
        mock_query = Mock()
        mock_job_model.query = mock_query
        mock_query.all.return_value = [job1, job2, job3]
        
        filters = JobFilters(search='john')
        result = self.service.list_jobs(filters)
        
        # Should return jobs matching search term (case insensitive)
        assert job1 in result  # 'John' matches
        assert job2 not in result  # 'Jane' doesn't match
        assert job3 in result  # 'Johnny' matches
        assert len(result) == 2

    @patch('app.services.infrastructure.job_query_service.Job')
    def test_list_jobs_search_email(self, mock_job_model):
        """Test search filter matches email addresses"""
        # Create mock job
        job = Mock()
        job.student_name = 'Jane Smith'
        job.student_email = 'jane@university.edu'
        
        # Mock the query
        mock_query = Mock()
        mock_job_model.query = mock_query
        mock_query.all.return_value = [job]
        
        filters = JobFilters(search='university')
        result = self.service.list_jobs(filters)
        
        # Should match email domain
        assert job in result
        assert len(result) == 1

    @patch('app.services.infrastructure.job_query_service.Job')
    def test_get_job_counts_no_search(self, mock_job_model):
        """Test getting job counts without search filter"""
        # Mock the query chain
        mock_query = Mock()
        mock_entities_query = Mock()
        mock_grouped_query = Mock()
        
        mock_job_model.query = mock_query
        mock_query.with_entities.return_value = mock_entities_query
        mock_entities_query.group_by.return_value = mock_grouped_query
        mock_grouped_query.all.return_value = [
            ('PENDING', 5),
            ('PRINTING', 3), 
            ('COMPLETED', 10)
        ]
        
        result = self.service.get_job_counts()
        
        # Should return counts dictionary
        expected = {
            'PENDING': 5,
            'PRINTING': 3,
            'COMPLETED': 10
        }
        assert result == expected
        
        # Should not apply any search filter
        mock_query.filter.assert_not_called()

    @patch('app.services.infrastructure.job_query_service.Job')
    @patch('app.services.infrastructure.job_query_service.func')
    @patch('app.services.infrastructure.job_query_service.or_')
    def test_get_job_counts_with_search(self, mock_or, mock_func, mock_job_model):
        """Test getting job counts with search filter"""
        # Mock the query chain
        mock_query = Mock()
        mock_filtered_query = Mock()
        mock_entities_query = Mock()
        mock_grouped_query = Mock()
        
        mock_job_model.query = mock_query
        mock_query.filter.return_value = mock_filtered_query
        mock_filtered_query.with_entities.return_value = mock_entities_query
        mock_entities_query.group_by.return_value = mock_grouped_query
        mock_grouped_query.all.return_value = [('PENDING', 2)]
        
        # Mock the OR condition
        mock_or_condition = Mock()
        mock_or.return_value = mock_or_condition
        
        result = self.service.get_job_counts(search='john')
        
        # Should apply search filter
        mock_query.filter.assert_called_once_with(mock_or_condition)
        
        # Should build OR condition for name and email
        mock_or.assert_called_once()
        
        assert result == {'PENDING': 2}

    @patch('app.services.infrastructure.job_query_service.Job')
    def test_get_job_counts_converts_to_int(self, mock_job_model):
        """Test that job counts are converted to integers"""
        # Mock the query to return non-integer counts
        mock_query = Mock()
        mock_entities_query = Mock()
        mock_grouped_query = Mock()
        
        mock_job_model.query = mock_query
        mock_query.with_entities.return_value = mock_entities_query
        mock_entities_query.group_by.return_value = mock_grouped_query
        
        # SQLAlchemy might return other numeric types
        mock_grouped_query.all.return_value = [
            ('PENDING', 5.0),  # Float
            ('PRINTING', 3),   # Int
        ]
        
        result = self.service.get_job_counts()
        
        # Should convert all counts to int
        assert result == {'PENDING': 5, 'PRINTING': 3}
        assert isinstance(result['PENDING'], int)
        assert isinstance(result['PRINTING'], int)
