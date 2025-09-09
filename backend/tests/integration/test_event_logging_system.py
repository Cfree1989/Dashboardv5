# type: ignore
import pytest
import json
from datetime import datetime, timezone
from app import db
from app.models.event import Event
from app.models.job import Job
from app.models.staff import Staff
from app.services.event_service import log_event, JOB_SPECIFIC_EVENTS, SYSTEM_EVENTS
from app.services.catalog_service import CatalogService


def create_test_job(job_id, **kwargs):
    """Helper function to create a test job with required fields."""
    defaults = {
        'student_name': 'Test Student',
        'student_email': 'test@example.com',
        'discipline': 'Engineering',
        'class_number': '101',
        'original_filename': 'test.stl',
        'display_name': 'Test Model',
        'file_path': '/test/path/test.stl',
        'metadata_path': '/test/path/test_metadata.json',
        'printer': 'Prusa MK4S',
        'color': 'True Black',
        'material': 'Filament',
        'status': 'UPLOADED'
    }
    defaults.update(kwargs)
    return Job(id=job_id, **defaults)


class TestEventLoggingSystem:
    """Comprehensive test suite for the event logging system fix."""

    def test_event_model_supports_nullable_job_id(self, app):
        with app.app_context():
            system_event = Event(
                job_id=None,
                event_type='CatalogUpdated',
                details={'test': 'data'},
                triggered_by='admin_user',
                workstation_id='workstation_1'
            )
            db.session.add(system_event)
            db.session.commit()
            assert system_event.id is not None
            assert system_event.job_id is None
            assert system_event.event_type == 'CatalogUpdated'

            job = create_test_job('test_job_123')
            db.session.add(job)
            db.session.commit()
            job_event = Event(
                job_id=job.id,
                event_type='JobCreated',
                details={'test': 'data'},
                triggered_by='student_user',
                workstation_id='workstation_2'
            )
            db.session.add(job_event)
            db.session.commit()
            assert job_event.id is not None
            assert job_event.job_id == job.id
            assert job_event.event_type == 'JobCreated'

    def test_event_service_validation_job_specific_events(self, app):
        with app.app_context():
            with pytest.raises(ValueError, match="job_id is required for job-specific event type"):
                log_event('JobCreated', details={'test': 'data'}, triggered_by='test_user')

            job = create_test_job('test_job_456')
            db.session.add(job)
            db.session.commit()
            log_event('JobCreated', details={'test': 'data'}, triggered_by='test_user', job_id=job.id)
            event = Event.query.filter_by(event_type='JobCreated', job_id=job.id).first()
            assert event is not None
            assert event.job_id == job.id
            assert event.triggered_by == 'test_user'

    def test_event_service_validation_system_events(self, app):
        with app.app_context():
            with pytest.raises(ValueError, match="job_id should be None for system event type"):
                log_event('CatalogUpdated', details={'test': 'data'}, triggered_by='test_user', job_id='some_job_id')
            log_event('CatalogUpdated', details={'test': 'data'}, triggered_by='test_user')
            event = Event.query.filter_by(event_type='CatalogUpdated').first()
            assert event is not None
            assert event.job_id is None
            assert event.triggered_by == 'test_user'

    def test_event_service_invalid_event_types(self, app):
        with app.app_context():
            with pytest.raises(ValueError, match="Invalid event type"):
                log_event('InvalidEventType', details={'test': 'data'}, triggered_by='test_user')

    def test_event_service_default_parameters(self, app):
        with app.app_context():
            from flask import g
            g.workstation_id = 'default_workstation'
            log_event('CatalogUpdated', details={'test': 'data'})
            event = Event.query.filter_by(event_type='CatalogUpdated').first()
            assert event is not None
            assert event.triggered_by == 'default_workstation'
            assert event.workstation_id == 'default_workstation'

    def test_admin_functions_with_system_events(self, client, token):
        response = client.post(
            '/api/v1/admin/error-monitoring/clear',
            json={'staff_name': 'admin_user'},
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200
        with client.application.app_context():
            event = Event.query.filter_by(event_type='ErrorMonitoringCleared').first()
            assert event is not None
            assert event.job_id is None
            assert event.triggered_by == 'admin_user'
            assert event.details['cleared_by'] == 'admin_user'

    def test_catalog_service_system_events(self, app):
        with app.app_context():
            CatalogService.seed_catalog_if_missing()
            event = Event.query.filter_by(event_type='CatalogSeeded').first()
            assert event is not None
            assert event.job_id is None
            assert event.triggered_by == 'system'
            catalog = CatalogService.get_catalog()
            assert catalog is not None

    def test_event_queries_with_mixed_event_types(self, app):
        with app.app_context():
            job = create_test_job('test_job_789')
            db.session.add(job)
            db.session.commit()
            log_event('JobCreated', details={'test': 'job_data'}, triggered_by='student_user', job_id=job.id)
            log_event('CatalogUpdated', details={'test': 'system_data'}, triggered_by='admin_user')
            all_events = Event.query.order_by(Event.timestamp.desc()).all()
            assert len(all_events) >= 2
            job_events = Event.query.filter(Event.job_id == job.id).all()
            assert len(job_events) == 1
            assert job_events[0].event_type == 'JobCreated'
            system_events = Event.query.filter(Event.job_id.is_(None)).all()
            assert len(system_events) >= 1
            assert any(event.event_type == 'CatalogUpdated' for event in system_events)

    def test_event_serialization_with_null_job_id(self, app):
        with app.app_context():
            log_event('CatalogUpdated', details={'test': 'data'}, triggered_by='test_user')
            event = Event.query.filter_by(event_type='CatalogUpdated').first()
            event_dict = event.to_dict()
            assert event_dict['job_id'] is None
            assert event_dict['event_type'] == 'CatalogUpdated'
            assert event_dict['triggered_by'] == 'test_user'
            assert 'timestamp' in event_dict
            assert 'details' in event_dict

    def test_event_type_classification_completeness(self, app):
        with app.app_context():
            for event_type in JOB_SPECIFIC_EVENTS:
                with pytest.raises(ValueError, match="job_id is required"):
                    log_event(event_type, details={'test': 'data'}, triggered_by='test_user')
            for event_type in SYSTEM_EVENTS:
                with pytest.raises(ValueError, match="job_id should be None"):
                    log_event(event_type, details={'test': 'data'}, triggered_by='test_user', job_id='some_job_id')

import pytest
import json
from datetime import datetime, timezone
from app import db
from app.models.event import Event
from app.models.job import Job
from app.models.staff import Staff
from app.services.event_service import log_event, JOB_SPECIFIC_EVENTS, SYSTEM_EVENTS
from app.services.catalog_service import CatalogService


def create_test_job(job_id, **kwargs):
    """Helper function to create a test job with required fields."""
    defaults = {
        'student_name': 'Test Student',
        'student_email': 'test@example.com',
        'discipline': 'Engineering',
        'class_number': '101',
        'original_filename': 'test.stl',
        'display_name': 'Test Model',
        'file_path': '/test/path/test.stl',
        'metadata_path': '/test/path/test_metadata.json',
        'printer': 'Prusa MK4S',
        'color': 'True Black',
        'material': 'Filament',
        'status': 'UPLOADED'
    }
    defaults.update(kwargs)
    return Job(id=job_id, **defaults)


class TestEventLoggingSystem:
    """Comprehensive test suite for the event logging system fix."""

    def test_event_model_supports_nullable_job_id(self, app):
        """Test that Event model properly supports nullable job_id."""
        with app.app_context():
            # Test system event with job_id=None
            system_event = Event(
                job_id=None,
                event_type='CatalogUpdated',
                details={'test': 'data'},
                triggered_by='admin_user',
                workstation_id='workstation_1'
            )
            db.session.add(system_event)
            db.session.commit()
            
            assert system_event.id is not None
            assert system_event.job_id is None
            assert system_event.event_type == 'CatalogUpdated'
            
            # Test job-specific event with job_id
            job = create_test_job('test_job_123')
            db.session.add(job)
            db.session.commit()
            
            job_event = Event(
                job_id=job.id,
                event_type='JobCreated',
                details={'test': 'data'},
                triggered_by='student_user',
                workstation_id='workstation_2'
            )
            db.session.add(job_event)
            db.session.commit()
            
            assert job_event.id is not None
            assert job_event.job_id == job.id
            assert job_event.event_type == 'JobCreated'

    def test_event_service_validation_job_specific_events(self, app):
        """Test validation for job-specific events."""
        with app.app_context():
            # Job-specific event without job_id should fail
            with pytest.raises(ValueError, match="job_id is required for job-specific event type"):
                log_event('JobCreated', details={'test': 'data'}, triggered_by='test_user')
            
            # Job-specific event with job_id should succeed
            job = create_test_job('test_job_456')
            db.session.add(job)
            db.session.commit()
            
            log_event('JobCreated', details={'test': 'data'}, triggered_by='test_user', job_id=job.id)
            
            # Verify event was created
            event = Event.query.filter_by(event_type='JobCreated', job_id=job.id).first()
            assert event is not None
            assert event.job_id == job.id
            assert event.triggered_by == 'test_user'

    def test_event_service_validation_system_events(self, app):
        """Test validation for system events."""
        with app.app_context():
            # System event with job_id should fail
            with pytest.raises(ValueError, match="job_id should be None for system event type"):
                log_event('CatalogUpdated', details={'test': 'data'}, triggered_by='test_user', job_id='some_job_id')
            
            # System event without job_id should succeed
            log_event('CatalogUpdated', details={'test': 'data'}, triggered_by='test_user')
            
            # Verify event was created
            event = Event.query.filter_by(event_type='CatalogUpdated').first()
            assert event is not None
            assert event.job_id is None
            assert event.triggered_by == 'test_user'

    def test_event_service_invalid_event_types(self, app):
        """Test validation for invalid event types."""
        with app.app_context():
            # Invalid event type should fail
            with pytest.raises(ValueError, match="Invalid event type"):
                log_event('InvalidEventType', details={'test': 'data'}, triggered_by='test_user')

    def test_event_service_default_parameters(self, app):
        """Test that event service uses default parameters correctly."""
        with app.app_context():
            # Test with minimal parameters (should use defaults from g)
            from flask import g
            g.workstation_id = 'default_workstation'
            
            log_event('CatalogUpdated', details={'test': 'data'})
            
            event = Event.query.filter_by(event_type='CatalogUpdated').first()
            assert event is not None
            assert event.triggered_by == 'default_workstation'
            assert event.workstation_id == 'default_workstation'

    def test_admin_functions_with_system_events(self, client, token):
        """Test that admin functions work correctly with system-level event logging."""
        # Test error monitoring clear endpoint
        response = client.post(
            '/api/v1/admin/error-monitoring/clear',
            json={'staff_name': 'admin_user'},
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200
        
        # Verify system event was logged
        with client.application.app_context():
            event = Event.query.filter_by(event_type='ErrorMonitoringCleared').first()
            assert event is not None
            assert event.job_id is None  # System event
            assert event.triggered_by == 'admin_user'
            assert event.details['cleared_by'] == 'admin_user'

    def test_catalog_service_system_events(self, app):
        """Test that catalog service properly logs system events."""
        with app.app_context():
            # Test catalog seeding event
            CatalogService.seed_catalog_if_missing()
            
            # Verify catalog seeded event was logged
            event = Event.query.filter_by(event_type='CatalogSeeded').first()
            assert event is not None
            assert event.job_id is None  # System event
            assert event.triggered_by == 'system'
            
            # Test catalog update event (this would require an update method, but we'll test the seeding)
            # The seeding should create a catalog and log the event
            catalog = CatalogService.get_catalog()
            assert catalog is not None

    def test_event_queries_with_mixed_event_types(self, app):
        """Test that event queries work correctly with both job-specific and system events."""
        with app.app_context():
            # Create a job
            job = create_test_job('test_job_789')
            db.session.add(job)
            db.session.commit()
            
            # Create job-specific event
            log_event('JobCreated', details={'test': 'job_data'}, triggered_by='student_user', job_id=job.id)
            
            # Create system event
            log_event('CatalogUpdated', details={'test': 'system_data'}, triggered_by='admin_user')
            
            # Test querying all events
            all_events = Event.query.order_by(Event.timestamp.desc()).all()
            assert len(all_events) >= 2
            
            # Test querying job-specific events
            job_events = Event.query.filter(Event.job_id == job.id).all()
            assert len(job_events) == 1
            assert job_events[0].event_type == 'JobCreated'
            
            # Test querying system events
            system_events = Event.query.filter(Event.job_id.is_(None)).all()
            assert len(system_events) >= 1
            assert any(event.event_type == 'CatalogUpdated' for event in system_events)

    def test_event_serialization_with_null_job_id(self, app):
        """Test that event serialization works correctly with null job_id."""
        with app.app_context():
            # Create system event
            log_event('CatalogUpdated', details={'test': 'data'}, triggered_by='test_user')
            
            event = Event.query.filter_by(event_type='CatalogUpdated').first()
            event_dict = event.to_dict()
            
            assert event_dict['job_id'] is None
            assert event_dict['event_type'] == 'CatalogUpdated'
            assert event_dict['triggered_by'] == 'test_user'
            assert 'timestamp' in event_dict
            assert 'details' in event_dict

    def test_event_type_classification_completeness(self, app):
        """Test that all event types are properly classified."""
        with app.app_context():
            # Test that all job-specific events require job_id
            for event_type in JOB_SPECIFIC_EVENTS:
                with pytest.raises(ValueError, match="job_id is required"):
                    log_event(event_type, details={'test': 'data'}, triggered_by='test_user')
            
            # Test that all system events reject job_id
            for event_type in SYSTEM_EVENTS:
                with pytest.raises(ValueError, match="job_id should be None"):
                    log_event(event_type, details={'test': 'data'}, triggered_by='test_user', job_id='some_job_id')

    def test_event_logging_integration_with_job_lifecycle(self, client, token):
        """Test event logging integration with complete job lifecycle."""
        # Submit a job
        import io
        data = {
            'student_name': 'Integration Test Student',
            'student_email': 'integration@example.com',
            'discipline': 'Engineering',
            'class_number': '101',
            'printer': 'Prusa MK4S',
            'color': 'True Black',
            'material': 'Filament',
            'file': (io.BytesIO(b'model data'), 'model.stl')
        }
        response = client.post('/api/v1/submit', data=data, content_type='multipart/form-data')
        assert response.status_code == 201
        job_data = response.get_json()
        job_id = job_data['id']
        
        # Approve the job
        response = client.post(
            f'/api/v1/jobs/{job_id}/approve',
            json={'staff_name': 'staff_user'},
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200
        
        # Complete the job
        response = client.post(
            f'/api/v1/jobs/{job_id}/complete',
            json={'staff_name': 'staff_user'},
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200
        
        # Verify events were logged correctly
        with client.application.app_context():
            events = Event.query.filter_by(job_id=job_id).order_by(Event.timestamp).all()
            event_types = [event.event_type for event in events]
            
            assert 'JobCreated' in event_types
            assert 'JobApproved' in event_types
            assert 'JobCompleted' in event_types
            
            # Verify all job events have job_id
            for event in events:
                assert event.job_id == job_id

    def test_admin_audit_events_with_job_id(self, client, token):
        """Test that admin audit events properly use job_id when applicable."""
        # First create a job
        import io
        data = {
            'student_name': 'Audit Test Student',
            'student_email': 'audit@example.com',
            'discipline': 'Engineering',
            'class_number': '101',
            'printer': 'Prusa MK4S',
            'color': 'True Black',
            'material': 'Filament',
            'file': (io.BytesIO(b'model data'), 'model.stl')
        }
        response = client.post('/api/v1/submit', data=data, content_type='multipart/form-data')
        assert response.status_code == 201
        job_data = response.get_json()
        job_id = job_data['id']
        
        # Test audit mark reviewed (should have job_id)
        response = client.post(
            '/api/v1/admin/audit/mark-reviewed',
            json={
                'job_id': job_id,
                'staff_name': 'admin_user',
                'issues': ['test_issue']
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200
        
        # Verify job-specific event was logged
        with client.application.app_context():
            event = Event.query.filter_by(event_type='AuditIssueReviewed', job_id=job_id).first()
            assert event is not None
            assert event.job_id == job_id
            assert event.triggered_by == 'admin_user'

    def test_event_logging_performance(self, app):
        """Test that event logging performs well with multiple events."""
        with app.app_context():
            import time
            
            # Create a job for testing
            job = create_test_job('perf_test_job', student_name='Performance Test', student_email='perf@example.com')
            db.session.add(job)
            db.session.commit()
            
            # Test performance of multiple job-specific events
            start_time = time.time()
            for i in range(100):
                log_event('JobCreated', details={'iteration': i}, triggered_by='test_user', job_id=job.id)
            
            job_events_time = time.time() - start_time
            
            # Test performance of multiple system events
            start_time = time.time()
            for i in range(100):
                log_event('CatalogUpdated', details={'iteration': i}, triggered_by='test_user')
            
            system_events_time = time.time() - start_time
            
            # Both should complete in reasonable time (less than 5 seconds each)
            assert job_events_time < 5.0
            assert system_events_time < 5.0
            
            # Verify events were created
            job_event_count = Event.query.filter_by(job_id=job.id).count()
            system_event_count = Event.query.filter(Event.job_id.is_(None)).count()
            
            assert job_event_count >= 100
            assert system_event_count >= 100

    def test_event_logging_error_handling(self, app):
        """Test that event logging handles errors gracefully."""
        with app.app_context():
            # Test with invalid event type
            with pytest.raises(ValueError):
                log_event('InvalidEventType', details={'test': 'data'}, triggered_by='test_user')
            
            # Test job-specific event without job_id
            with pytest.raises(ValueError):
                log_event('JobCreated', details={'test': 'data'}, triggered_by='test_user')
            
            # Test system event with job_id
            with pytest.raises(ValueError):
                log_event('CatalogUpdated', details={'test': 'data'}, triggered_by='test_user', job_id='some_job_id')
            
            # Verify no invalid events were created
            invalid_events = Event.query.filter_by(event_type='InvalidEventType').all()
            assert len(invalid_events) == 0

    def test_event_logging_data_integrity(self, app):
        """Test that event logging maintains data integrity."""
        with app.app_context():
            # Create a job
            job = create_test_job('integrity_test_job', student_name='Integrity Test', student_email='integrity@example.com')
            db.session.add(job)
            db.session.commit()
            
            # Log events with complex details
            complex_details = {
                'nested': {
                    'data': 'value',
                    'array': [1, 2, 3],
                    'boolean': True,
                    'null': None
                },
                'unicode': '测试数据',
                'special_chars': '!@#$%^&*()'
            }
            
            log_event('JobCreated', details=complex_details, triggered_by='test_user', job_id=job.id)
            
            # Verify event was stored correctly
            event = Event.query.filter_by(event_type='JobCreated', job_id=job.id).first()
            assert event is not None
            assert event.details == complex_details
            
            # Test serialization preserves data
            event_dict = event.to_dict()
            assert event_dict['details'] == complex_details

    def test_event_logging_timestamp_accuracy(self, app):
        """Test that event timestamps are accurate and consistent."""
        with app.app_context():
            import time
            
            # Log events with known timing
            start_time = datetime.utcnow()
            time.sleep(0.1)  # Small delay
            
            log_event('CatalogUpdated', details={'test': 'data'}, triggered_by='test_user')
            
            time.sleep(0.1)  # Small delay
            end_time = datetime.utcnow()
            
            # Verify event timestamp is within expected range
            event = Event.query.filter_by(event_type='CatalogUpdated').first()
            assert event is not None
            assert start_time <= event.timestamp <= end_time
            
            # Verify timestamp is timezone-aware (UTC)
            assert event.timestamp.tzinfo is None  # UTC time stored without timezone info

    def test_event_logging_workstation_id_handling(self, app):
        """Test that workstation_id is handled correctly."""
        with app.app_context():
            from flask import g
            
            # Test with explicit workstation_id
            log_event('CatalogUpdated', details={'test': 'data'}, triggered_by='test_user', workstation_id='explicit_workstation')
            
            event = Event.query.filter_by(event_type='CatalogUpdated').first()
            assert event.workstation_id == 'explicit_workstation'
            
            # Test with workstation_id from g
            g.workstation_id = 'g_workstation'
            log_event('CatalogUpdated', details={'test': 'data'}, triggered_by='test_user')
            
            event = Event.query.filter_by(event_type='CatalogUpdated').order_by(Event.timestamp.desc()).first()
            assert event.workstation_id == 'g_workstation'
            
            # Test with default fallback
            delattr(g, 'workstation_id')
            log_event('CatalogUpdated', details={'test': 'data'}, triggered_by='test_user')
            
            event = Event.query.filter_by(event_type='CatalogUpdated').order_by(Event.timestamp.desc()).first()
            assert event.workstation_id == 'system'  # Default fallback

    def test_event_logging_concurrent_access(self, app):
        """Test that event logging handles concurrent access correctly."""
        with app.app_context():
            import threading
            import time
            
            # Create a job for testing
            job = create_test_job('concurrent_test_job', student_name='Concurrent Test', student_email='concurrent@example.com')
            db.session.add(job)
            db.session.commit()
            
            events_created = []
            lock = threading.Lock()
            
            def create_events(thread_id):
                for i in range(10):
                    try:
                        log_event('JobCreated', details={'thread': thread_id, 'iteration': i}, 
                                triggered_by=f'user_{thread_id}', job_id=job.id)
                        with lock:
                            events_created.append(f'{thread_id}_{i}')
                    except Exception as e:
                        print(f"Thread {thread_id} error: {e}")
            
            # Create multiple threads
            threads = []
            for i in range(5):
                thread = threading.Thread(target=create_events, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Verify all events were created
            event_count = Event.query.filter_by(job_id=job.id).count()
            assert event_count == 50  # 5 threads * 10 events each
            
            # Verify no duplicate events
            event_ids = [event.id for event in Event.query.filter_by(job_id=job.id).all()]
            assert len(event_ids) == len(set(event_ids))  # No duplicates

    def test_event_logging_cleanup_and_maintenance(self, app):
        """Test that event logging system can be maintained and cleaned up."""
        with app.app_context():
            # Create some test events
            for i in range(10):
                log_event('CatalogUpdated', details={'test': i}, triggered_by='test_user')
            
            # Test event count
            total_events = Event.query.count()
            assert total_events >= 10
            
            # Test event cleanup (delete old events)
            old_event = Event.query.first()
            if old_event:
                db.session.delete(old_event)
                db.session.commit()
                
                # Verify event was deleted
                deleted_event = Event.query.get(old_event.id)
                assert deleted_event is None
            
            # Test event querying by date range
            recent_events = Event.query.filter(
                Event.timestamp >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            ).all()
            assert len(recent_events) >= 9  # Should have remaining events from today

    def test_event_logging_api_endpoints(self, client, token):
        """Test that API endpoints work correctly with the new event logging system."""
        # Test events endpoint with filtering
        response = client.get(
            '/api/v1/analytics/events?system_only=true',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200
        
        # Test events endpoint with job filtering
        response = client.get(
            '/api/v1/analytics/events?job_only=true',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200
        
        # Test job events endpoint
        # First create a job
        import io
        data = {
            'student_name': 'API Test Student',
            'student_email': 'api@example.com',
            'discipline': 'Engineering',
            'class_number': '101',
            'printer': 'Prusa MK4S',
            'color': 'True Black',
            'material': 'Filament',
            'file': (io.BytesIO(b'model data'), 'model.stl')
        }
        response = client.post('/api/v1/submit', data=data, content_type='multipart/form-data')
        assert response.status_code == 201
        job_data = response.get_json()
        job_id = job_data['id']
        
        # Test job events endpoint
        response = client.get(
            f'/api/v1/jobs/{job_id}/events',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200
        events = response.get_json()
        assert len(events) >= 1
        assert events[0]['job_id'] == job_id
        assert events[0]['event_type'] == 'JobCreated'


class TestEventLoggingMigration:
    """Test that the event logging system migration works correctly."""
    
    def test_database_schema_supports_nullable_job_id(self, app):
        """Test that the database schema properly supports nullable job_id."""
        with app.app_context():
            # Test that we can create events with null job_id
            system_event = Event(
                job_id=None,
                event_type='CatalogUpdated',
                details={'test': 'migration'},
                triggered_by='migration_test',
                workstation_id='migration_workstation'
            )
            db.session.add(system_event)
            db.session.commit()
            
            # Verify the event was stored correctly
            assert system_event.id is not None
            assert system_event.job_id is None
            
            # Test that we can query events with null job_id
            null_job_events = Event.query.filter(Event.job_id.is_(None)).all()
            assert len(null_job_events) >= 1
            assert any(event.id == system_event.id for event in null_job_events)
            
            # Test that we can query events with non-null job_id
            job = create_test_job('migration_test_job', student_name='Migration Test', student_email='migration@example.com')
            db.session.add(job)
            db.session.commit()
            
            job_event = Event(
                job_id=job.id,
                event_type='JobCreated',
                details={'test': 'migration'},
                triggered_by='migration_test',
                workstation_id='migration_workstation'
            )
            db.session.add(job_event)
            db.session.commit()
            
            non_null_job_events = Event.query.filter(Event.job_id.isnot(None)).all()
            assert len(non_null_job_events) >= 1
            assert any(event.id == job_event.id for event in non_null_job_events)

    def test_existing_events_remain_accessible(self, app):
        """Test that existing events remain accessible after migration."""
        with app.app_context():
            # Create events with job_id (simulating pre-migration state)
            job = create_test_job('existing_test_job', student_name='Existing Test', student_email='existing@example.com')
            db.session.add(job)
            db.session.commit()
            
            # Create events that would have existed before migration
            existing_event = Event(
                job_id=job.id,
                event_type='JobCreated',
                details={'test': 'existing'},
                triggered_by='existing_test',
                workstation_id='existing_workstation'
            )
            db.session.add(existing_event)
            db.session.commit()
            
            # Verify existing events are still accessible
            retrieved_event = Event.query.get(existing_event.id)
            assert retrieved_event is not None
            assert retrieved_event.job_id == job.id
            assert retrieved_event.event_type == 'JobCreated'
            
            # Verify event serialization works
            event_dict = retrieved_event.to_dict()
            assert event_dict['job_id'] == job.id
            assert event_dict['event_type'] == 'JobCreated'

    def test_mixed_event_types_in_queries(self, app):
        """Test that queries work correctly with mixed event types."""
        with app.app_context():
            # Create a job
            job = create_test_job('mixed_test_job', student_name='Mixed Test', student_email='mixed@example.com')
            db.session.add(job)
            db.session.commit()
            
            # Create mixed events
            log_event('JobCreated', details={'test': 'job'}, triggered_by='test_user', job_id=job.id)
            log_event('CatalogUpdated', details={'test': 'system'}, triggered_by='test_user')
            log_event('JobApproved', details={'test': 'job'}, triggered_by='test_user', job_id=job.id)
            log_event('ErrorMonitoringCleared', details={'test': 'system'}, triggered_by='test_user')
            
            # Test querying all events
            all_events = Event.query.order_by(Event.timestamp.desc()).all()
            assert len(all_events) >= 4
            
            # Test querying by event type
            job_events = Event.query.filter(Event.event_type.in_(['JobCreated', 'JobApproved'])).all()
            assert len(job_events) >= 2
            
            system_events = Event.query.filter(Event.event_type.in_(['CatalogUpdated', 'ErrorMonitoringCleared'])).all()
            assert len(system_events) >= 2
            
            # Test querying by job_id presence
            events_with_job = Event.query.filter(Event.job_id.isnot(None)).all()
            events_without_job = Event.query.filter(Event.job_id.is_(None)).all()
            
            assert len(events_with_job) >= 2
            assert len(events_without_job) >= 2
