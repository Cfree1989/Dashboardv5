#!/usr/bin/env python3
"""
Comprehensive Import Testing Script
Task 2.3: Test All Import Paths

This script tests all import scenarios to ensure no import warnings or errors.
"""

import sys
import warnings
from pathlib import Path
import importlib
import traceback

def test_import_scenario(module_name: str, description: str) -> tuple[bool, str]:
    """Test a specific import scenario"""
    try:
        # Capture warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # Attempt import
            module = importlib.import_module(module_name)
            
            # Check for warnings
            if w:
                warning_messages = [str(warning.message) for warning in w]
                return False, f"Import succeeded but generated warnings: {warning_messages}"
            
            return True, "Import successful"
            
    except Exception as e:
        return False, f"Import failed: {str(e)}"

def test_import_combinations() -> list[tuple[bool, str]]:
    """Test various import combinations"""
    results = []
    
    # Add current directory to Python path
    current_dir = Path.cwd()
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    # Test scenarios
    test_scenarios = [
        # Basic package imports
        ("app.services", "Services package import"),
        ("app.business_logic", "Business logic package import"),
        
        # Individual service imports
        ("app.services.infrastructure.atomic_file_service", "AtomicFileService import"),
        ("app.services.infrastructure.file_lock_service", "FileLockService import"),
        ("app.services.infrastructure.payment_service", "PaymentService import"),
        
        # Foundation services
        ("app.business_logic.shared_services.validation_service", "ValidationService import"),
        ("app.business_logic.shared_services.response_service", "ResponseService import"),
        ("app.business_logic.shared_services.auth_service", "AuthService import"),
        ("app.business_logic.shared_services.catalog_service", "CatalogService import"),
        ("app.business_logic.shared_services.token_service", "TokenService import"),
        ("app.business_logic.shared_services.error_handling_service", "ErrorHandlingService import"),
        ("app.business_logic.shared_services.event_service", "EventService import"),
        ("app.business_logic.shared_services.db_transaction_service", "DatabaseTransactionService import"),
        
        # Job lifecycle services
        ("app.business_logic.job_lifecycle.job_approval_service", "JobApprovalService import"),
        ("app.business_logic.job_lifecycle.job_status_service", "JobStatusService import"),
        ("app.business_logic.job_lifecycle.job_transition_service", "JobTransitionService import"),
        
        # Admin operations services
        ("app.business_logic.admin_operations.job_admin_service", "JobAdminService import"),
        ("app.business_logic.admin_operations.job_notes_service", "JobNotesService import"),
        
        # Shared services
        ("app.business_logic.shared_services.job_locking_service", "JobLockingService import"),
        ("app.business_logic.shared_services.job_event_service", "JobEventService import"),
        
        # Analytics services
        ("app.business_logic.analytics.analytics_service", "AnalyticsService import"),
        ("app.business_logic.analytics.caching_service", "CachingService import"),
        ("app.business_logic.analytics.analytics_service_interface", "AnalyticsServiceInterface import"),
        
        # Orchestration services
        ("app.services.orchestration.job_orchestration_service", "JobOrchestrationService import"),
        
        # Package-level imports
        ("app.business_logic.job_lifecycle", "Job lifecycle package import"),
        ("app.business_logic.admin_operations", "Admin operations package import"),
        ("app.business_logic.shared_services", "Shared services package import"),
        ("app.business_logic.analytics", "Analytics package import"),
        ("app.services.orchestration", "Orchestration package import"),
        ("app.services.infrastructure", "Infrastructure package import"),
    ]
    
    print("🧪 Testing import scenarios...")
    for module_name, description in test_scenarios:
        success, message = test_import_scenario(module_name, description)
        results.append((success, f"{description}: {message}"))
        
        if success:
            print(f"✅ {description}")
        else:
            print(f"❌ {description}: {message}")
    
    return results

def test_import_patterns() -> list[tuple[bool, str]]:
    """Test specific import patterns to ensure they work correctly"""
    results = []
    
    # Add current directory to Python path
    current_dir = Path.cwd()
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    print("\n🔍 Testing import patterns...")
    
    # Test pattern 1: Services package import
    try:
        from app.services import AtomicFileService, ValidationService, AnalyticsService
        results.append((True, "Services package: All services import successfully"))
        print("✅ Services package: All services import successfully")
    except Exception as e:
        results.append((False, f"Services package: Import failed - {e}"))
        print(f"❌ Services package: Import failed - {e}")
    
    # Test pattern 2: Business logic package import
    try:
        from app.business_logic import JobApprovalService, JobStatusService, JobTransitionService
        results.append((True, "Business logic package: All services import successfully"))
        print("✅ Business logic package: All services import successfully")
    except Exception as e:
        results.append((False, f"Business logic package: Import failed - {e}"))
        print(f"❌ Business logic package: Import failed - {e}")
    
    # Test pattern 3: Orchestration service import
    try:
        from app.services.orchestration.job_orchestration_service import JobOrchestrationService
        results.append((True, "Orchestration service: Import successful"))
        print("✅ Orchestration service: Import successful")
    except Exception as e:
        results.append((False, f"Orchestration service: Import failed - {e}"))
        print(f"❌ Orchestration service: Import failed - {e}")
    
    # Test pattern 4: Foundation services import
    try:
        from app.business_logic.shared_services.validation_service import ValidationService
        from app.business_logic.shared_services.response_service import ResponseService
        results.append((True, "Foundation services: Import successful"))
        print("✅ Foundation services: Import successful")
    except Exception as e:
        results.append((False, f"Foundation services: Import failed - {e}"))
        print(f"❌ Foundation services: Import failed - {e}")
    
    # Test pattern 5: Analytics services import
    try:
        from app.business_logic.analytics.analytics_service import AnalyticsService
        from app.business_logic.analytics.caching_service import CachingService
        results.append((True, "Analytics services: Import successful"))
        print("✅ Analytics services: Import successful")
    except Exception as e:
        results.append((False, f"Analytics services: Import failed - {e}"))
        print(f"❌ Analytics services: Import failed - {e}")
    
    return results

def test_warnings_as_errors() -> list[tuple[bool, str]]:
    """Test imports with warnings treated as errors"""
    results = []
    
    # Add current directory to Python path
    current_dir = Path.cwd()
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    print("\n⚠️  Testing with warnings as errors...")
    
    # Configure warnings to be treated as errors
    warnings.filterwarnings('error')
    
    test_modules = [
        'app.services',
        'app.business_logic',
        'app.services.orchestration.job_orchestration_service',
        'app.business_logic.job_lifecycle',
        'app.business_logic.shared_services',
        'app.business_logic.analytics'
    ]
    
    for module_name in test_modules:
        try:
            importlib.import_module(module_name)
            results.append((True, f"{module_name}: No warnings generated"))
            print(f"✅ {module_name}: No warnings generated")
        except Exception as e:
            results.append((False, f"{module_name}: Warning/Error - {e}"))
            print(f"❌ {module_name}: Warning/Error - {e}")
    
    return results

def main():
    """Main test function"""
    print("🧪 Comprehensive Import Testing")
    print("=" * 50)
    
    all_results = []
    
    # Test import scenarios
    scenario_results = test_import_combinations()
    all_results.extend(scenario_results)
    
    # Test import patterns
    pattern_results = test_import_patterns()
    all_results.extend(pattern_results)
    
    # Test warnings as errors
    warning_results = test_warnings_as_errors()
    all_results.extend(warning_results)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    
    successful_tests = sum(1 for success, _ in all_results if success)
    total_tests = len(all_results)
    failed_tests = total_tests - successful_tests
    
    print(f"   Total Tests: {total_tests}")
    print(f"   Successful: {successful_tests}")
    print(f"   Failed: {failed_tests}")
    print(f"   Success Rate: {(successful_tests/total_tests)*100:.1f}%")
    
    if failed_tests == 0:
        print("\n🎉 All import tests passed!")
        return 0
    else:
        print(f"\n⚠️  {failed_tests} tests failed:")
        for success, message in all_results:
            if not success:
                print(f"   - {message}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
