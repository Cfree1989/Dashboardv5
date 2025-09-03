# Task 6: Service Pattern Consistency Analysis

## Current State Summary

### Routes Using JobOrchestrationService (CONSISTENT ✅):
- `jobs.py` - Fully consistent, uses JobOrchestrationService + ResponseService

### Routes with Direct Model Access (INCONSISTENT ❌):

#### High Priority - Admin Routes (admin.py):
- **Direct operations**: `Job.query.all()`, `db.session.query()`, `db.session.commit()`
- **Missing orchestration methods needed**:
  - `get_all_jobs()` - Replace Job.query.all()
  - `archive_jobs_by_criteria()` - Replace bulk archival logic  
  - `prune_archived_jobs()` - Replace bulk deletion logic
  - `repair_job_metadata()` - Replace direct db updates
  - `repair_job_location()` - Replace direct db updates
  - `relink_job_file()` - Replace direct db updates

#### High Priority - Submit Routes (submit.py):
- **Response pattern**: Uses `jsonify()` only, needs ResponseService
- **Missing orchestration methods needed**:
  - `create_job_with_upload()` - Replace direct Job creation + db operations
  - `confirm_job_submission()` - Replace direct job confirmation logic
  - `resend_confirmation_email()` - Replace direct email resend logic

#### Medium Priority - Staff Routes (staff.py):  
- **Missing orchestration methods needed**:
  - `get_all_staff()` / `get_active_staff()` - Replace Staff.query operations
  - `create_staff()` - Replace direct Staff creation
  - `update_staff_status()` - Replace direct Staff updates

#### Medium Priority - Jobs Staff Routes (jobs_staff.py):
- **Claims to use orchestration but doesn't** - Heavy direct model access
- **Needs refactoring to use existing orchestration methods**

#### Lower Priority - Export Routes (export.py):
- **Missing orchestration methods needed**:
  - `get_payments_for_export()` - Replace complex payment queries
  - `log_export_event()` - Replace direct Event creation

#### Lower Priority - Analytics Routes (analytics_old.py):
- **Heavy direct model access** - extensive query operations
- **Recommend**: Create dedicated AnalyticsService instead of orchestration methods

### Response Pattern Inconsistencies:

#### Routes Using jsonify() Only (NEEDS STANDARDIZATION ❌):
- `submit.py` - 15+ jsonify calls, no ResponseService
- `health.py` - 5+ jsonify calls, no ResponseService  

#### Routes with Mixed Patterns (NEEDS CLEANUP):
- `monitoring.py` - Mixed ResponseService/jsonify usage
- `admin.py` - 1 jsonify call among many ResponseService calls

## Implementation Priority

### Phase 1: High Impact Routes
1. **admin.py** - Create missing orchestration methods for admin operations
2. **submit.py** - Migrate to ResponseService + create orchestration methods  
3. **jobs_staff.py** - Remove direct model access, use existing orchestration

### Phase 2: Medium Impact Routes
4. **staff.py** - Create staff orchestration methods
5. **export.py** - Create export orchestration methods
6. **health.py** - Migrate to ResponseService (simple change)

### Phase 3: Specialized Services  
7. **analytics_old.py** - Create dedicated AnalyticsService (separate from orchestration)
8. **monitoring.py** - Clean up mixed response patterns

## Service Methods to Create

### JobOrchestrationService Extensions:
```python
# Admin operations
def get_all_jobs(self) -> List[Job]
def archive_jobs_by_criteria(self, criteria_data: JobArchivalData) -> int
def prune_archived_jobs(self) -> int  
def repair_job_metadata(self, job_id: str, repair_data: JobRepairData) -> Job
def repair_job_location(self, job_id: str, repair_data: JobRepairData) -> Job
def relink_job_file(self, job_id: str, relink_data: JobRelinkData) -> Job

# Submit operations  
def create_job_with_upload(self, submission_data: JobSubmissionData) -> Job
def confirm_job_submission(self, job_id: str, confirmation_data: JobConfirmationData) -> Job
def resend_confirmation_email(self, job_id: str) -> bool

# Query operations
def get_job_by_id(self, job_id: str) -> Optional[Job]
def get_job_events(self, job_id: str) -> List[Event]
```

### New StaffOrchestrationService:
```python
def get_all_staff(self, active_only: bool = False) -> List[Staff]
def create_staff(self, staff_data: StaffCreationData) -> Staff  
def update_staff_status(self, staff_name: str, update_data: StaffUpdateData) -> Staff
```

### New AnalyticsService:
```python  
def get_printing_analytics(self, filters: AnalyticsFilters) -> Dict
def get_completion_analytics(self, filters: AnalyticsFilters) -> Dict
def get_payment_analytics(self, filters: AnalyticsFilters) -> Dict
def get_staff_analytics(self, filters: AnalyticsFilters) -> Dict
def get_student_analytics(self, filters: AnalyticsFilters) -> Dict
```
