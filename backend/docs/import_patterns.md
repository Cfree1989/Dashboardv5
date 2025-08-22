# Import Patterns and Best Practices

## Overview

This document outlines the import patterns and best practices used in the 3D Print Management System to prevent circular dependencies and maintain clean architecture.

## Import Architecture

### Directory Structure

```
app/
├── services/                   # Infrastructure and orchestration services
│   ├── __init__.py             # Main services package (imports foundation services)
│   ├── infrastructure/         # Low-level technical services
│   └── orchestration/          # Service coordination layer
├── business_logic/             # Business logic services
│   ├── __init__.py             # Business logic package
│   ├── job_lifecycle/          # Job lifecycle operations
│   ├── admin_operations/       # Admin operations
│   ├── shared_services/        # Foundation services
│   └── analytics/              # Analytics services
└── routes/                     # Route handlers (import services as needed)
```

### Import Hierarchy

1. **Infrastructure Services** (Lowest level)
   - AtomicFileService, FileLockService, PaymentService
   - No dependencies on business logic

2. **Foundation Services** (Shared business logic)
   - ValidationService, ResponseService, AuthService, etc.
   - Can depend on infrastructure services
   - Used by all business logic services

3. **Business Logic Services** (Domain-specific)
   - JobApprovalService, JobStatusService, etc.
   - Depend on foundation services
   - No dependencies on orchestration services

4. **Orchestration Services** (Coordination layer)
   - JobOrchestrationService
   - Composes business logic services
   - Provides unified interface for routes

5. **Route Handlers** (Highest level)
   - Import orchestration services or business logic services directly
   - No circular dependencies back to services package

## Import Rules

### ✅ Allowed Patterns

1. **Foundation Services → Infrastructure Services**
   ```python
   from app.services.infrastructure import AtomicFileService
   ```

2. **Business Logic Services → Foundation Services**
   ```python
   from app.business_logic.shared_services.validation_service import ValidationService
   ```

3. **Orchestration Services → Business Logic Services**
   ```python
   from app.business_logic.job_lifecycle import JobApprovalService
   ```

4. **Route Handlers → Any Services**
   ```python
   from app.services.orchestration.job_orchestration_service import JobOrchestrationService
   from app.business_logic.job_lifecycle import JobApprovalService
   ```

5. **Services Package → Foundation Services (for backward compatibility)**
   ```python
   from ..business_logic.shared_services.validation_service import ValidationService
   ```

### ❌ Forbidden Patterns

1. **Services Package → Orchestration Services**
   ```python
   # DON'T: This creates circular dependencies
   from .orchestration.job_orchestration_service import JobOrchestrationService
   ```

2. **Business Logic Services → Orchestration Services**
   ```python
   # DON'T: This creates circular dependencies
   from app.services.orchestration import JobOrchestrationService
   ```

3. **Foundation Services → Business Logic Services**
   ```python
   # DON'T: This creates circular dependencies
   from app.business_logic.job_lifecycle import JobApprovalService
   ```

4. **Wildcard Imports in Production Code**
   ```python
   # DON'T: Use specific imports instead
   from app.services import *
   ```

## Best Practices

### 1. Use Specific Imports

```python
# ✅ Good: Specific imports
from app.business_logic.job_lifecycle.job_approval_service import JobApprovalService

# ❌ Bad: Wildcard imports
from app.business_logic.job_lifecycle import *
```

### 2. Use Relative Imports Within Packages

```python
# ✅ Good: Relative imports within same package
from .job_approval_service import JobApprovalService
from ..shared_services.validation_service import ValidationService

# ❌ Bad: Absolute imports within same package
from app.business_logic.job_lifecycle.job_approval_service import JobApprovalService
```

### 3. Use Absolute Imports for Cross-Package Dependencies

```python
# ✅ Good: Absolute imports for cross-package dependencies
from app.business_logic.shared_services.validation_service import ValidationService

# ❌ Bad: Relative imports for cross-package dependencies
from ...business_logic.shared_services.validation_service import ValidationService
```

### 4. Import at Module Level

```python
# ✅ Good: Import at module level
from app.business_logic.job_lifecycle.job_approval_service import JobApprovalService

class MyService:
    def __init__(self):
        self.approval_service = JobApprovalService()

# ❌ Bad: Import inside functions
class MyService:
    def some_method(self):
        from app.business_logic.job_lifecycle.job_approval_service import JobApprovalService
        service = JobApprovalService()
```

### 5. Use Dependency Injection

```python
# ✅ Good: Dependency injection for testability
class JobService:
    def __init__(self, validation_service=None):
        self.validation = validation_service or ValidationService

# ❌ Bad: Hard-coded dependencies
class JobService:
    def __init__(self):
        self.validation = ValidationService()
```

## Validation

### Automated Validation

Use the import validation script to detect issues:

```bash
python scripts/validate_imports.py
```

The script checks for:
- Circular dependencies
- Import pattern violations
- Runtime import failures

### Manual Validation

1. **Check Import Graph**: Ensure no cycles exist
2. **Test Imports**: Verify all imports work at runtime
3. **Review Patterns**: Follow established import patterns

## Common Issues and Solutions

### Issue: Circular Import Error

**Symptoms**: `ImportError: cannot import name 'X' from partially initialized module 'Y'`

**Solution**: 
1. Identify the circular dependency
2. Move shared code to a common module
3. Use dependency injection
4. Restructure the import hierarchy

### Issue: Import Not Found

**Symptoms**: `ModuleNotFoundError: No module named 'X'`

**Solution**:
1. Check the module path is correct
2. Ensure the module exists
3. Verify Python path includes the project root
4. Check for typos in import statements

### Issue: Import Performance

**Symptoms**: Slow application startup

**Solution**:
1. Use lazy imports for heavy modules
2. Import only what you need
3. Avoid importing unused modules
4. Use conditional imports where appropriate

## Migration Guidelines

### When Adding New Services

1. **Determine the service type** (infrastructure, foundation, business logic, orchestration)
2. **Choose the appropriate directory** based on the service type
3. **Follow the import hierarchy** for dependencies
4. **Update the services package** if needed for backward compatibility
5. **Run validation** to ensure no circular dependencies

### When Refactoring Services

1. **Analyze current dependencies** using the validation script
2. **Plan the refactoring** to maintain the import hierarchy
3. **Update imports** in all affected files
4. **Test thoroughly** to ensure no regressions
5. **Run validation** to confirm no new circular dependencies

## Tools and Scripts

### Import Validation Script

Location: `backend/scripts/validate_imports.py`

Usage:
```bash
cd backend
python scripts/validate_imports.py
```

Features:
- Detects circular dependencies
- Validates import patterns
- Tests runtime imports
- Provides detailed reporting

### Manual Testing

Test imports manually:
```python
# Test services package
from app.services import *

# Test business logic package
from app.business_logic import *

# Test orchestration services
from app.services.orchestration.job_orchestration_service import JobOrchestrationService
```

## Conclusion

Following these import patterns and best practices ensures:
- No circular dependencies
- Clean, maintainable code
- Proper separation of concerns
- Easy testing and debugging
- Scalable architecture

Always run the validation script after making changes to imports to catch issues early.
