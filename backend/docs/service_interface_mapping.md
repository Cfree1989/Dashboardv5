# Service Interface Mapping Document
## Emergency Service Decomposition - Architecture Transition Guide

**Date**: August 21, 2025  
**Purpose**: Document the mapping from old monolithic `JobLifecycleService` to new clean architecture services

---

## Overview

This document maps all interfaces from the old monolithic `JobLifecycleService` to the new clean architecture services, ensuring API compatibility during the transition.

## Service Class Mapping

| Old Service | New Service | Purpose |
|-------------|-------------|---------|
| `JobLifecycleService` (monolithic) | `JobOrchestrationService` (orchestration layer) | Main service interface for routes |

## Method Mapping

### Job Approval Operations
| Old Method | New Method | Delegates To |
|------------|------------|--------------|
| `approve_job()` | `orchestration_service.approve_job()` | `JobApprovalService` |
| `reject_job()` | `orchestration_service.reject_job()` | `JobApprovalService` |
| `review_job()` | `orchestration_service.review_job()` | `JobApprovalService` |

### Job Status Operations
| Old Method | New Method | Delegates To |
|------------|------------|--------------|
| `mark_printing()` | `orchestration_service.mark_printing()` | `JobStatusService` |
| `mark_complete()` | `orchestration_service.mark_complete()` | `JobStatusService` |
| `mark_picked_up()` | `orchestration_service.mark_picked_up()` | `JobStatusService` |
| `mark_failed()` | `orchestration_service.mark_failed()` | `JobStatusService` |
| `admin_force_confirm()` | `orchestration_service.admin_force_confirm()` | `JobStatusService` |
| `revert_to_printing()` | `orchestration_service.revert_to_printing()` | `JobStatusService` |
| `revert_to_completed()` | `orchestration_service.revert_to_completed()` | `JobStatusService` |

### Generic Status Transitions
| Old Method | New Method | Delegates To |
|------------|------------|--------------|
| `transition_status()` | `orchestration_service.transition_status()` | `JobTransitionService` |

### Admin Operations
| Old Method | New Method | Delegates To |
|------------|------------|--------------|
| `admin_change_status()` | `orchestration_service.admin_change_status()` | `JobAdminService` |
| `delete_job()` | `orchestration_service.delete_job()` | `JobAdminService` |
| `hard_delete_job()` | `orchestration_service.hard_delete_job()` | `JobAdminService` |
| `resend_approval_email()` | `orchestration_service.resend_approval_email()` | `JobAdminService` |
| `force_unlock_job()` | `orchestration_service.force_unlock_job()` | `JobAdminService` |

### Notes Operations
| Old Method | New Method | Delegates To |
|------------|------------|--------------|
| `append_note()` | `orchestration_service.append_note()` | `JobNotesService` |
| `update_notes()` | `orchestration_service.update_notes()` | `JobNotesService` |

### Locking Operations
| Old Method | New Method | Delegates To |
|------------|------------|--------------|
| `lock_job()` | `orchestration_service.lock_job()` | `JobLockingService` |
| `unlock_job()` | `orchestration_service.unlock_job()` | `JobLockingService` |
| `extend_job_lock()` | `orchestration_service.extend_job_lock()` | `JobLockingService` |

### Event Logging Operations
| Old Method | New Method | Delegates To |
|------------|------------|--------------|
| `log_event()` | `orchestration_service.log_event()` | `JobEventService` |
| `log_admin_action()` | `orchestration_service.log_admin_action()` | `JobEventService` |
| `sync_authoritative_metadata()` | `orchestration_service.sync_authoritative_metadata()` | `JobEventService` |

## Data Class Mapping

### Approval Data Classes
| Old Location | New Location |
|--------------|--------------|
| `JobApprovalData` | `app.business_logic.job_lifecycle.job_approval_service.JobApprovalData` |
| `JobRejectionData` | `app.business_logic.job_lifecycle.job_approval_service.JobRejectionData` |
| `JobReviewData` | `app.business_logic.job_lifecycle.job_approval_service.JobReviewData` |

### Status Data Classes
| Old Location | New Location |
|--------------|--------------|
| `JobStatusTransitionData` | `app.business_logic.job_lifecycle.job_status_service.JobStatusTransitionData` |

### Admin Data Classes
| Old Location | New Location |
|--------------|--------------|
| `JobAdminStatusChangeData` | `app.business_logic.admin_operations.job_admin_service.JobAdminStatusChangeData` |
| `JobDeleteData` | `app.business_logic.admin_operations.job_admin_service.JobDeleteData` |
| `JobResendEmailData` | `app.business_logic.admin_operations.job_admin_service.JobResendEmailData` |
| `JobForceUnlockData` | `app.business_logic.admin_operations.job_admin_service.JobForceUnlockData` |

### Notes Data Classes
| Old Location | New Location |
|--------------|--------------|
| `JobNoteData` | `app.business_logic.admin_operations.job_notes_service.JobNoteData` |
| `JobUpdateNotesData` | `app.business_logic.admin_operations.job_notes_service.JobUpdateNotesData` |

### Locking Data Classes
| Old Location | New Location |
|--------------|--------------|
| `JobLockData` | `app.business_logic.shared_services.job_locking_service.JobLockData` |

## Import Path Changes

### Old Import Pattern
```python
from app.services.job_lifecycle_service import JobLifecycleService, JobApprovalData
lifecycle_service = JobLifecycleService()
```

### New Import Pattern
```python
from app.services.orchestration.job_orchestration_service import JobOrchestrationService
from app.business_logic.job_lifecycle.job_approval_service import JobApprovalData
orchestration_service = JobOrchestrationService()
```

## Route Migration Examples

### Example 1: Job Approval Route
```python
# OLD
from app.services.job_lifecycle_service import JobLifecycleService, JobApprovalData
lifecycle_service = JobLifecycleService()
result = lifecycle_service.approve_job(job_id, approval_data)

# NEW
from app.services.orchestration.job_orchestration_service import JobOrchestrationService
from app.business_logic.job_lifecycle.job_approval_service import JobApprovalData
orchestration_service = JobOrchestrationService()
result = orchestration_service.approve_job(job_id, approval_data)
```

### Example 2: Job Status Route
```python
# OLD
from app.services.job_lifecycle_service import JobLifecycleService, JobStatusTransitionData
lifecycle_service = JobLifecycleService()
result = lifecycle_service.mark_printing(job_id, transition_data)

# NEW
from app.services.orchestration.job_orchestration_service import JobOrchestrationService
from app.business_logic.job_lifecycle.job_status_service import JobStatusTransitionData
orchestration_service = JobOrchestrationService()
result = orchestration_service.mark_printing(job_id, transition_data)
```

## Key Findings

✅ **API Compatibility**: All methods from the old service are preserved in the orchestration service  
✅ **Data Class Compatibility**: All data classes exist in the new architecture with same structure  
✅ **Method Signatures**: All method signatures are identical between old and new  
✅ **Return Types**: All return types are preserved  
✅ **Delegation Pattern**: Orchestration service delegates to appropriate business logic services  

## Migration Checklist

- [ ] Update route imports to use new service locations
- [ ] Replace `JobLifecycleService` instantiation with `JobOrchestrationService`
- [ ] Update data class imports to new locations
- [ ] Test each route individually before enabling in app
- [ ] Verify all method calls work with new service
- [ ] Test end-to-end functionality

## Notes

- All method signatures are identical - no parameter changes required
- All return types are preserved - no response handling changes required
- The orchestration service maintains full API compatibility
- Routes can be migrated one at a time without breaking existing functionality
