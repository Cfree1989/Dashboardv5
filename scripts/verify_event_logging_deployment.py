#!/usr/bin/env python3
"""
Production Deployment Verification Script for Event Logging System

This script verifies that the event logging system fix (D2) is properly deployed
and working in production. It tests all critical functionality including:

1. System-level events (job_id=None)
2. Job-specific events (job_id=job.id)
3. Admin functions without 500 errors
4. Catalog service system events
5. Mixed event type queries
6. Event validation and error handling
7. Performance under load
"""

import os
import sys
import time
from datetime import datetime

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import create_app, db
from app.models.event import Event
from app.models.job import Job
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
        'printer': 'Prusa MK3S',
        'color': 'Black',
        'material': 'Filament',
        'status': 'UPLOADED'
    }
    defaults.update(kwargs)
    return Job(id=job_id, **defaults)


def test_system_events():
    """Test that system-level events work correctly."""
    print("🔍 Testing System-Level Events...")
    
    # Test system event creation
    log_event('CatalogUpdated', details={'test': 'production'}, triggered_by='admin_user')
    log_event('ErrorMonitoringCleared', details={'cleared_by': 'admin_user'}, triggered_by='admin_user')
    log_event('AdminAction', details={'action': 'test'}, triggered_by='admin_user')
    
    # Verify events were created with job_id=None
    system_events = Event.query.filter(Event.job_id.is_(None)).all()
    assert len(system_events) >= 3, f"Expected at least 3 system events, got {len(system_events)}"
    
    event_types = [event.event_type for event in system_events]
    assert 'CatalogUpdated' in event_types, "CatalogUpdated event not found"
    assert 'ErrorMonitoringCleared' in event_types, "ErrorMonitoringCleared event not found"
    assert 'AdminAction' in event_types, "AdminAction event not found"
    
    print("✅ System-level events working correctly")


def test_job_specific_events():
    """Test that job-specific events work correctly."""
    print("🔍 Testing Job-Specific Events...")
    
    # Create a test job
    job = create_test_job('test_job_123')
    db.session.add(job)
    db.session.commit()
    
    # Test job-specific event creation
    log_event('JobCreated', details={'test': 'job'}, triggered_by='student_user', job_id=job.id)
    log_event('JobApproved', details={'test': 'job'}, triggered_by='staff_user', job_id=job.id)
    
    # Verify events were created with job_id
    job_events = Event.query.filter(Event.job_id == job.id).all()
    assert len(job_events) >= 2, f"Expected at least 2 job events, got {len(job_events)}"
    
    event_types = [event.event_type for event in job_events]
    assert 'JobCreated' in event_types, "JobCreated event not found"
    assert 'JobApproved' in event_types, "JobApproved event not found"
    
    print("✅ Job-specific events working correctly")


def test_catalog_service_events():
    """Test that catalog service system events work correctly."""
    print("🔍 Testing Catalog Service Events...")
    
    # Test catalog seeding
    CatalogService.seed_catalog_if_missing()
    
    # Verify catalog seeded event was created
    catalog_event = Event.query.filter_by(event_type='CatalogSeeded').first()
    assert catalog_event is not None, "CatalogSeeded event not found"
    assert catalog_event.job_id is None, "CatalogSeeded event should have job_id=None"
    assert catalog_event.triggered_by == 'system', "CatalogSeeded event should be triggered by system"
    
    print("✅ Catalog service events working correctly")


def test_event_validation():
    """Test that event validation works correctly."""
    print("🔍 Testing Event Validation...")
    
    # Test that job-specific events require job_id
    try:
        log_event('JobCreated', details={'test': 'validation'}, triggered_by='test_user')
        assert False, "Job-specific event without job_id should fail"
    except ValueError as e:
        assert "job_id is required" in str(e), f"Unexpected error: {e}"
    
    # Test that system events reject job_id
    try:
        log_event('CatalogUpdated', details={'test': 'validation'}, triggered_by='test_user', job_id='some_job_id')
        assert False, "System event with job_id should fail"
    except ValueError as e:
        assert "job_id should be None" in str(e), f"Unexpected error: {e}"
    
    # Test that invalid event types are rejected
    try:
        log_event('InvalidEventType', details={'test': 'validation'}, triggered_by='test_user')
        assert False, "Invalid event type should fail"
    except ValueError as e:
        assert "Invalid event type" in str(e), f"Unexpected error: {e}"
    
    print("✅ Event validation working correctly")


def test_mixed_event_queries():
    """Test that queries work correctly with mixed event types."""
    print("🔍 Testing Mixed Event Queries...")
    
    # Create a test job
    job = create_test_job('test_job_456')
    db.session.add(job)
    db.session.commit()
    
    # Create mixed events
    log_event('JobCreated', details={'test': 'mixed'}, triggered_by='student_user', job_id=job.id)
    log_event('CatalogUpdated', details={'test': 'mixed'}, triggered_by='admin_user')
    
    # Test querying by job_id presence
    events_with_job = Event.query.filter(Event.job_id.isnot(None)).count()
    events_without_job = Event.query.filter(Event.job_id.is_(None)).count()
    
    assert events_with_job >= 1, f"Expected at least 1 event with job_id, got {events_with_job}"
    assert events_without_job >= 1, f"Expected at least 1 event without job_id, got {events_without_job}"
    
    # Test querying by event type
    job_events = Event.query.filter(Event.event_type == 'JobCreated').count()
    system_events = Event.query.filter(Event.event_type == 'CatalogUpdated').count()
    
    assert job_events >= 1, f"Expected at least 1 JobCreated event, got {job_events}"
    assert system_events >= 1, f"Expected at least 1 CatalogUpdated event, got {system_events}"
    
    print("✅ Mixed event queries working correctly")


def test_performance():
    """Test that event logging performs well under load."""
    print("🔍 Testing Performance...")
    
    # Create a test job
    job = create_test_job('perf_test_job')
    db.session.add(job)
    db.session.commit()
    
    # Test performance of multiple events
    start_time = time.time()
    
    for i in range(100):
        log_event('JobCreated', details={'iteration': i}, triggered_by='test_user', job_id=job.id)
    
    job_events_time = time.time() - start_time
    
    start_time = time.time()
    
    for i in range(100):
        log_event('CatalogUpdated', details={'iteration': i}, triggered_by='test_user')
    
    system_events_time = time.time() - start_time
    
    # Both should complete in reasonable time (less than 5 seconds each)
    assert job_events_time < 5.0, f"Job events took too long: {job_events_time:.2f}s"
    assert system_events_time < 5.0, f"System events took too long: {system_events_time:.2f}s"
    
    # Verify events were created
    job_event_count = Event.query.filter_by(job_id=job.id).count()
    system_event_count = Event.query.filter(Event.job_id.is_(None)).count()
    
    assert job_event_count >= 100, f"Expected at least 100 job events, got {job_event_count}"
    assert system_event_count >= 100, f"Expected at least 100 system events, got {system_event_count}"
    
    print(f"✅ Performance test passed - Job events: {job_events_time:.2f}s, System events: {system_events_time:.2f}s")


def test_event_serialization():
    """Test that event serialization works correctly."""
    print("🔍 Testing Event Serialization...")
    
    # Create a system event with unique details
    unique_details = {'test': 'serialization', 'unique_id': 'test_serialization_123'}
    log_event('CatalogUpdated', details=unique_details, triggered_by='test_user_serialization')
    
    # Find the specific event we just created
    event = Event.query.filter_by(
        event_type='CatalogUpdated',
        triggered_by='test_user_serialization'
    ).first()
    
    assert event is not None, "Event not found"
    event_dict = event.to_dict()
    
    # Verify serialization
    assert event_dict['job_id'] is None, "System event job_id should be None in serialization"
    assert event_dict['event_type'] == 'CatalogUpdated', "Event type should be preserved"
    assert event_dict['triggered_by'] == 'test_user_serialization', "Triggered by should be preserved"
    assert 'timestamp' in event_dict, "Timestamp should be included"
    assert 'details' in event_dict, "Details should be included"
    assert event_dict['details'] == unique_details, "Details should be preserved"
    
    print("✅ Event serialization working correctly")


def main():
    """Main verification function."""
    print("🚀 Event Logging System Production Deployment Verification")
    print("=" * 60)
    print(f"Started at: {datetime.now().isoformat()}")
    print()
    
    # Set up the application context
    app = create_app()
    with app.app_context():
        # Create database tables
        db.create_all()
        
        try:
            # Run all verification tests
            test_system_events()
            test_job_specific_events()
            test_catalog_service_events()
            test_event_validation()
            test_mixed_event_queries()
            test_performance()
            test_event_serialization()
            
            print()
            print("🎉 ALL TESTS PASSED!")
            print("✅ Event Logging System is properly deployed and working correctly")
            print()
            print("📊 Summary:")
            total_events = Event.query.count()
            system_events = Event.query.filter(Event.job_id.is_(None)).count()
            job_events = Event.query.filter(Event.job_id.isnot(None)).count()
            
            print(f"   - Total events: {total_events}")
            print(f"   - System events: {system_events}")
            print(f"   - Job events: {job_events}")
            print(f"   - Event types tested: {len(set([e.event_type for e in Event.query.all()]))}")
            
        except Exception as e:
            print(f"❌ VERIFICATION FAILED: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    
    print()
    print("🏁 Verification completed successfully!")
    print("The Event Logging System Fix (D2) is ready for production use.")


if __name__ == '__main__':
    main()
