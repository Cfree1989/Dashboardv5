# Cascade Failure Debugging Protocol

## Overview

This protocol provides a systematic approach to debugging test failures during service extraction and refactoring. It is designed to prevent hours of debugging by following a structured methodology.

## Core Principles

### 1. Start with the Simplest Error
**NEVER debug the most complex error first**
- Find the most fundamental error (TypeError, AttributeError, ImportError)
- Fix the root cause before addressing symptoms
- Use single-test isolation to reduce noise

### 2. Single-Test Isolation
**NEVER debug with full test suite output**
```bash
# WRONG: Overwhelming noise
pytest tests/ -v

# RIGHT: Isolate the simplest error
pytest tests/test_atomic_file_service.py::TestAtomicFileOperation::test_initialization -v -s
```

### 3. Layer-by-Layer Verification
**Debug in dependency order**:
1. Import errors (can't even load the module)
2. Attribute errors (module loads but API mismatch)
3. Logic errors (API works but behavior wrong)
4. Integration errors (multiple components)

## Debugging Protocol

### STEP 1: Identify the Simplest Error
```bash
# Run full suite to see all errors
pytest --tb=short -v

# Look for the most fundamental error type:
# - ImportError: Module can't be imported
# - AttributeError: Object missing expected attribute
# - TypeError: Wrong number of arguments
# - SyntaxError: Code won't parse
```

### STEP 2: Isolate the Error
```bash
# Run single test in isolation
pytest path/to/test_file.py::TestClass::test_method -v -s

# Expected output: Clear error message without noise
# If still noisy, run with --tb=long for full traceback
```

### STEP 3: Analyze the Root Cause
**For ImportError**:
- Check if module exists
- Check import paths
- Check for circular imports
- Check for missing dependencies

**For AttributeError**:
- Compare expected vs actual API
- Check if service API evolved
- Look for missing attributes
- Check mock setup

**For TypeError**:
- Compare method signatures
- Check argument counts
- Look for API changes
- Check mock return values

### STEP 4: Fix the Fundamental Issue
**DO NOT fix symptoms first**
- Fix the API mismatch before fixing tests
- Fix the import error before fixing logic
- Fix the attribute error before fixing behavior

### STEP 5: Verify the Fix
```bash
# Test the fix in isolation
pytest path/to/test_file.py::TestClass::test_method -v

# If it passes, expand scope gradually
pytest path/to/test_file.py -v
pytest path/to/test_file.py path/to/related_test.py -v
```

## Common Failure Patterns

### Pattern 1: API Evolution
**Symptoms**: AttributeError for missing attributes
**Example**: `'AtomicFileMoveOperation' object has no attribute 'operation_type'`
**Root Cause**: Service API changed but tests not updated
**Solution**: Update tests to match current API or add compatibility layer

### Pattern 2: Mock Path Changes
**Symptoms**: ImportError in mocked modules
**Example**: `ModuleNotFoundError: No module named 'app.services.new_service'`
**Root Cause**: Service extraction changed import paths
**Solution**: Update @patch decorators to use new import paths

### Pattern 3: Mock State Pollution
**Symptoms**: Inconsistent test results, call count mismatches
**Example**: `assert 1 == 2` where 1 is mock call count
**Root Cause**: Mock objects not reset between tests
**Solution**: Add mock reset in setUp/tearDown or use fresh mocks

### Pattern 4: Flask Context Issues
**Symptoms**: "Working outside of application context"
**Example**: RuntimeError when accessing Flask.g in tests
**Root Cause**: Services accessing Flask context in test isolation
**Solution**: Add context safety or use app.app_context() in tests

### Pattern 5: Test Data Brittleness
**Symptoms**: 400 errors in tests that should pass
**Example**: Catalog validation rejecting test data
**Root Cause**: Application data changed but test data not updated
**Solution**: Update test data to match current application state

## Debugging Tools

### 1. Single Test Runner
```bash
# scripts/debug_single_test.py
#!/usr/bin/env python3
import subprocess
import sys

def run_single_test(test_path):
    """Run a single test in isolation with detailed output"""
    cmd = ["pytest", test_path, "-v", "-s", "--tb=long"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result

if __name__ == "__main__":
    test_path = sys.argv[1]
    result = run_single_test(test_path)
    print(f"Exit code: {result.returncode}")
    print(f"STDOUT:\n{result.stdout}")
    print(f"STDERR:\n{result.stderr}")
```

### 2. Mock Analysis Tool
```bash
# scripts/analyze_mocks.py
#!/usr/bin/env python3
import re
import sys
from pathlib import Path

def find_mock_usage(test_dir):
    """Find all mock usage in test files"""
    mock_patterns = [
        r'@patch\(',
        r'MagicMock\(',
        r'mock\.',
    ]
    
    for test_file in Path(test_dir).rglob('test_*.py'):
        content = test_file.read_text()
        for pattern in mock_patterns:
            if re.search(pattern, content):
                print(f"Mock usage in {test_file}")
                break

if __name__ == "__main__":
    find_mock_usage(sys.argv[1] if len(sys.argv) > 1 else "tests/")
```

### 3. API Comparison Tool
```bash
# scripts/compare_api.py
#!/usr/bin/env python3
import inspect
import importlib

def compare_api(module_path, class_name):
    """Compare expected vs actual API for a class"""
    try:
        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)
        
        print(f"API for {class_name}:")
        for name, obj in inspect.getmembers(cls):
            if not name.startswith('_'):
                print(f"  {name}: {type(obj).__name__}")
    except Exception as e:
        print(f"Error analyzing {module_path}.{class_name}: {e}")

if __name__ == "__main__":
    compare_api(sys.argv[1], sys.argv[2])
```

## Emergency Procedures

### When Tests Start Failing After Changes

#### STEP 1: DO NOT debug the modified route file first
- The error is likely in a dependency, not your changes
- Look for the simplest, most fundamental error

#### STEP 2: Find the simplest error
```bash
# Run critical tests first
pytest tests/test_atomic_file_service.py::TestAtomicFileOperation::test_initialization -v -s
pytest tests/test_jobs.py::test_approve_job -v -s
pytest tests/test_submit.py -v -s
```

#### STEP 3: If AttributeError, debug mock initialization
- Check if mocks are set up correctly
- Verify mock return values
- Check for mock state pollution

#### STEP 4: Check for import-time side effects
```python
# Test import side effects
python -c "import sys; initial=set(sys.modules.keys()); from app.services.target_service import TargetService; new=set(sys.modules.keys())-initial; print(f'New modules: {new}')"
```

#### STEP 5: Rollback if necessary
```bash
# If debugging takes >30 minutes, rollback and try different approach
git checkout -- path/to/modified/file.py
```

## Success Metrics

### Debugging Efficiency
- **Time to root cause**: <30 minutes
- **Single-test isolation**: Always used
- **Layer-by-layer approach**: Always followed
- **Rollback frequency**: <10% of changes

### Test Health Maintenance
- **Test pass rate**: Never drop below 85%
- **Mock brittleness**: Reduced by 50%
- **API compatibility**: 100% maintained
- **Debugging time**: <2 hours per issue

## Conclusion

This protocol ensures systematic debugging that prevents cascade failures and reduces debugging time from hours to minutes. The key is to always start with the simplest error and work through issues in dependency order.

**Remember**: The goal is not to fix every test immediately, but to understand the root cause and fix it systematically.
