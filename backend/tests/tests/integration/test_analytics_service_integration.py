import pytest
from datetime import datetime, timezone, timedelta
from app.services.analytics_service import AnalyticsService
from app.services.interfaces.analytics_service_interface import DateRange, AnalyticsFilters
from app.models.job import Job
from app.models.event import Event
from app.models.payment import Payment
from app.models.staff import Staff
from app import db


class TestAnalyticsServiceIntegration:
    """Integration tests for AnalyticsService following roadmap guidance"""
    
    def test_analytics_service_direct_usage(self, app):
        """Test AnalyticsService with real database - no complex mocking"""
        with app.app_context():
            # Create a staff member
            staff = Staff(name='Test Staff')
            db.session.add(staff)
            
            # Create test jobs with required fields
            job1 = Job(
                id='analytics_test_1',
                student_name='Test Student 1',
                student_email='test1@example.com',
                discipline='Computer Science',
                class_number='CS101',
                original_filename='test1.stl',
                display_name='Test Job 1',
                file_path='/tmp/test1.stl',
                metadata_path='/tmp/test1_metadata.json',
                status='PENDING',
                printer='Prusa MK4S',
                color='True Black',
                material='filament',
                weight_g=25.0,
                cost_usd=3.50
            )
            
            job2 = Job(
                id='analytics_test_2',
                student_name='Test Student 2',
                student_email='test2@example.com',
                discipline='Computer Science',
                class_number='CS102',
                original_filename='test2.stl',
                display_name='Test Job 2',
                file_path='/tmp/test2.stl',
                metadata_path='/tmp/test2_metadata.json',
                status='COMPLETED',
                printer='Prusa MK4S',
                color='True Black',
                material='filament',
                weight_g=30.0,
                cost_usd=4.00
            )
            
            db.session.add(job1)
            db.session.add(job2)
            
            # Create test events
            event1 = Event(
                job_id='analytics_test_1',
                event_type='JobCreated',
                timestamp=datetime.now(timezone.utc),
                triggered_by='Test Staff',
                workstation_id='WS001'
            )
            
            event2 = Event(
                job_id='analytics_test_2',
                event_type='JobMarkedComplete',
                timestamp=datetime.now(timezone.utc),
                triggered_by='Test Staff',
                workstation_id='WS001'
            )
            
            db.session.add(event1)
            db.session.add(event2)
            db.session.commit()
            
            # Test AnalyticsService with real data
            service = AnalyticsService()
            
            # Define date range and filters
            start_date = datetime.now(timezone.utc) - timedelta(days=1)
            end_date = datetime.now(timezone.utc) + timedelta(days=1)
            date_range = DateRange(start_date, end_date)
            filters = AnalyticsFilters(printer='Prusa MK4S', discipline='Computer Science')
            
            # Test overview metrics
            overview = service.get_overview_metrics(date_range, filters)
            
            assert 'by_status' in overview
            assert 'total_submissions' in overview
            assert 'date_range' in overview
            assert overview['by_status']['PENDING'] >= 1
            assert overview['by_status']['COMPLETED'] >= 1
            assert overview['total_submissions'] >= 2
            
            # Test trend data
            trends = service.get_trend_data(date_range, filters)
            
            assert 'submissions' in trends
            assert 'approvals' in trends
            assert 'date_range' in trends
            assert isinstance(trends['submissions'], list)
            assert isinstance(trends['approvals'], list)
            
            # Test resource metrics
            resources = service.get_resource_metrics(date_range, filters)
            
            assert 'printing_throughput' in resources
            assert 'printer_utilization' in resources
            assert 'material_consumption_g' in resources
            assert 'queue_age_buckets' in resources
            
            # Test financial summary
            financial = service.get_financial_summary(date_range, filters)
            
            assert 'revenue_over_time' in financial
            assert 'total_revenue_cents' in financial
            assert 'payment_count' in financial
            
            # Cleanup
            db.session.delete(event1)
            db.session.delete(event2)
            db.session.delete(job1)
            db.session.delete(job2)
            db.session.delete(staff)
            db.session.commit()
    
    def test_analytics_service_with_payment_workflow(self, app):
        """Test AnalyticsService with complete payment workflow"""
        with app.app_context():
            # Create staff and completed job
            staff = Staff(name='Payment Staff')
            db.session.add(staff)
            
            job = Job(
                id='payment_analytics_test',
                student_name='Payment Student',
                student_email='payment@example.com',
                discipline='Engineering',
                class_number='ENG201',
                original_filename='payment_test.stl',
                display_name='Payment Test Job',
                file_path='/tmp/payment_test.stl',
                metadata_path='/tmp/payment_test_metadata.json',
                status='COMPLETED',
                printer='Prusa MK4S',
                color='True Black',
                material='filament',
                weight_g=35.0,
                cost_usd=5.00
            )
            db.session.add(job)
            
            # Create payment
            payment = Payment(
                job_id='payment_analytics_test',
                grams=35.0,
                price_cents=500,  # $5.00
                txn_no='TXN123',
                picked_up_by='Test Student',
                paid_by_staff='Payment Staff',
                paid_ts=datetime.now(timezone.utc)
            )
            db.session.add(payment)
            db.session.commit()
            
            # Test analytics with payment data
            service = AnalyticsService()
            
            start_date = datetime.now(timezone.utc) - timedelta(days=1)
            end_date = datetime.now(timezone.utc) + timedelta(days=1)
            date_range = DateRange(start_date, end_date)
            filters = AnalyticsFilters(printer='Prusa MK4S', discipline='Engineering')
            
            # Test financial metrics with real payment data
            financial = service.get_financial_summary(date_range, filters)
            
            assert financial['total_revenue_cents'] >= 500
            assert financial['payment_count'] >= 1
            
            # Test resource metrics with payment job
            resources = service.get_resource_metrics(date_range, filters)
            
            assert resources['material_consumption_g']['filament'] >= 35.0
            
            # Cleanup
            db.session.delete(payment)
            db.session.delete(job)
            db.session.delete(staff)
            db.session.commit()
    
    def test_analytics_service_caching_behavior(self, app):
        """Test that caching works correctly in real environment"""
        with app.app_context():
            service = AnalyticsService()
            
            start_date = datetime.now(timezone.utc) - timedelta(days=1)
            end_date = datetime.now(timezone.utc) + timedelta(days=1)
            date_range = DateRange(start_date, end_date)
            filters = AnalyticsFilters()
            
            # First call should compute and cache
            result1 = service.get_overview_metrics(date_range, filters)
            
            # Second call should return cached result
            result2 = service.get_overview_metrics(date_range, filters)
            
            # Results should be identical (cached)
            assert result1 == result2
            assert 'date_range' in result1
            assert 'by_status' in result1
