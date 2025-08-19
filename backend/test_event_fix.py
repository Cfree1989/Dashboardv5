#!/usr/bin/env python3
"""
Test script for Event Logging System Fix (D2-S2)
Tests the updated Event model and log_event function with system-level events.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import pytest
pytest.skip("Skipping manual event logging script in pytest", allow_module_level=True)

from app import create_app
from app.services.event_service import log_event, JOB_SPECIFIC_EVENTS, SYSTEM_EVENTS

def test_event_logging():
    """Test the updated event logging functionality."""
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing Event Logging System Fix (D2-S2)")
        print("=" * 50)
        
        # Test 1: System event with job_id=None (should work)
        print("✅ Test 1: System event with job_id=None")
        try:
            log_event('CatalogUpdated', {'test': True}, triggered_by='test_user', job_id=None)
            print("   ✅ System event logged successfully")
        except Exception as e:
            print(f"   ❌ System event failed: {e}")
            return False
        
        # Test 2: Job-specific event with job_id (should work)
        print("✅ Test 2: Job-specific event with job_id")
        try:
            log_event('JobCreated', {'test': True}, triggered_by='test_user', job_id='test_job_123')
            print("   ✅ Job-specific event logged successfully")
        except Exception as e:
            print(f"   ❌ Job-specific event failed: {e}")
            return False
        
        # Test 3: Job-specific event without job_id (should fail)
        print("✅ Test 3: Job-specific event without job_id (should fail)")
        try:
            log_event('JobCreated', {'test': True}, triggered_by='test_user', job_id=None)
            print("   ❌ Job-specific event should have failed but didn't")
            return False
        except ValueError as e:
            print(f"   ✅ Job-specific event correctly rejected: {e}")
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            return False
        
        # Test 4: System event with job_id (should fail)
        print("✅ Test 4: System event with job_id (should fail)")
        try:
            log_event('CatalogUpdated', {'test': True}, triggered_by='test_user', job_id='test_job_123')
            print("   ❌ System event should have failed but didn't")
            return False
        except ValueError as e:
            print(f"   ✅ System event correctly rejected: {e}")
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            return False
        
        # Test 5: Invalid event type (should fail)
        print("✅ Test 5: Invalid event type (should fail)")
        try:
            log_event('InvalidEvent', {'test': True}, triggered_by='test_user', job_id=None)
            print("   ❌ Invalid event should have failed but didn't")
            return False
        except ValueError as e:
            print(f"   ✅ Invalid event correctly rejected: {e}")
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            return False
        
        print("=" * 50)
        print("🎉 All tests passed! Event logging fix is working correctly.")
        return True

if __name__ == '__main__':
    success = test_event_logging()
    sys.exit(0 if success else 1)
