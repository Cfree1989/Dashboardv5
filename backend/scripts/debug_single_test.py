#!/usr/bin/env python3
"""
Single test debugging script for isolating test failures.

Usage:
    python scripts/debug_single_test.py tests/test_file.py::TestClass::test_method
"""

import subprocess
import sys
import os

def run_single_test(test_path):
    """Run a single test in isolation with detailed output"""
    cmd = ["pytest", test_path, "-v", "-s", "--tb=long"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result

def analyze_test_result(result, test_path):
    """Analyze test result and provide debugging guidance"""
    print(f"=== Test Analysis for {test_path} ===")
    print(f"Exit code: {result.returncode}")
    
    if result.returncode == 0:
        print("✅ Test PASSED")
        return
    
    print("❌ Test FAILED")
    print("\n=== STDOUT ===")
    print(result.stdout)
    print("\n=== STDERR ===")
    print(result.stderr)
    
    # Analyze common failure patterns
    stderr_lower = result.stderr.lower()
    stdout_lower = result.stdout.lower()
    
    print("\n=== Failure Pattern Analysis ===")
    
    if "attributeerror" in stderr_lower:
        print("🔍 PATTERN: AttributeError - Object missing expected attribute")
        print("   Likely causes:")
        print("   - Service API evolved but tests not updated")
        print("   - Mock object not set up correctly")
        print("   - Missing import or module")
        print("   Next steps: Check API compatibility or mock setup")
    
    elif "typeerror" in stderr_lower:
        print("🔍 PATTERN: TypeError - Wrong number of arguments or type mismatch")
        print("   Likely causes:")
        print("   - Method signature changed")
        print("   - Wrong argument types passed")
        print("   - Mock return value has wrong type")
        print("   Next steps: Check method signatures and mock return values")
    
    elif "importerror" in stderr_lower or "modulenotfounderror" in stderr_lower:
        print("🔍 PATTERN: ImportError - Module cannot be imported")
        print("   Likely causes:")
        print("   - Module doesn't exist")
        print("   - Import path changed")
        print("   - Circular import")
        print("   - Missing dependency")
        print("   Next steps: Check import paths and dependencies")
    
    elif "working outside of application context" in stderr_lower:
        print("🔍 PATTERN: Flask Context Error - Accessing Flask context outside app")
        print("   Likely causes:")
        print("   - Service accessing Flask.g in test isolation")
        print("   - Missing app.app_context() wrapper")
        print("   - Service not designed for test isolation")
        print("   Next steps: Add context safety or use app.app_context()")
    
    elif "assertionerror" in stderr_lower:
        print("🔍 PATTERN: AssertionError - Test assertion failed")
        print("   Likely causes:")
        print("   - Logic error in test or code")
        print("   - Mock not behaving as expected")
        print("   - Test data mismatch")
        print("   Next steps: Check test logic and mock behavior")
    
    else:
        print("🔍 PATTERN: Unknown error type")
        print("   Next steps: Analyze error message manually")
    
    print("\n=== Recommended Next Steps ===")
    print("1. Check if this is a fundamental error (ImportError, AttributeError)")
    print("2. If fundamental, fix this error before debugging other tests")
    print("3. If not fundamental, check if this test depends on a broken service")
    print("4. Use git checkout to rollback if debugging takes >30 minutes")

def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/debug_single_test.py <test_path>")
        print("Example: python scripts/debug_single_test.py tests/test_atomic_file_service.py::TestAtomicFileOperation::test_initialization")
        sys.exit(1)
    
    test_path = sys.argv[1]
    
    # Validate test path format
    if "::" not in test_path:
        print("❌ Error: Test path must include class and method (e.g., file.py::Class::method)")
        sys.exit(1)
    
    print(f"🔍 Running single test: {test_path}")
    print("=" * 60)
    
    result = run_single_test(test_path)
    analyze_test_result(result, test_path)
    
    if result.returncode != 0:
        sys.exit(result.returncode)

if __name__ == "__main__":
    main()
