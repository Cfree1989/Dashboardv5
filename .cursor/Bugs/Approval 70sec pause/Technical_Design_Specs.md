# Technical Design Specifications: Read-After-Write Freshness

## Scope
Backend session hygiene and defensive invalidation; frontend post-mutation cache bypass; no schema changes.

## Components and Edits

### 1) Backend: Session Hygiene
- File: `backend/app/__init__.py`
- Add teardown handler after extensions init:
  - `@app.teardown_request` → `db.session.remove()`
- Rationale: Ensure session-per-request; clear identity map per request lifecycle.

### 2) Backend: Defensive Invalidation (already in place)
- File: `backend/app/services/infrastructure/job_query_service.py`
- Keep (no change):
  - `db.session.expire_all()` at start of `list_jobs()` and `get_job_counts()`.
- Rationale: Forces fresh rows for real-time lists and counts.

### 3) Frontend: Post-Mutation Fetch Bypass
- File(s): `frontend/src/components/dashboard/job-list.tsx`, and any mutation callers
- Ensure: All success paths after approve/reject/transition call `fetchJobs(true)`.
- Rationale: Avoid client cache for immediate UI consistency.

## Pseudocode Edits

### Add session teardown in app factory
```python
# backend/app/__init__.py
# ... after app, db.init_app(app), etc.
@app.teardown_request
def remove_session(exception=None):
    try:
        db.session.remove()
    except Exception:
        # swallow to avoid masking real response errors; logs already capture exceptions
        pass
```

### Ensure frontend bypass
```ts
// job-card.tsx or caller
await onApprove(job.id);
await fetchJobs(true); // bypass cache to ensure fresh rows
```

## Test Plan

### Unit/Integration (Backend)
- Test: Approve → immediate list
  - Arrange: Create job in UPLOADED
  - Act: POST /jobs/:id/approve; then GET /jobs?status=UPLOADED
  - Assert: Approved job not present
- Test: Counts update
  - After approval, GET /jobs/counts → UPLOADED decreases by 1
- Test: Teardown called
  - Simulate request; assert `db.session` not leaking objects across requests

### Frontend
- Test: Mutation triggers fresh fetch
  - Mock API: approve returns 200; subsequent list returns updated list when bypassCache=true
  - Assert: UI moves card within 2–3s

## Acceptance Criteria
- Read-after-write behavior consistent within < 2–3s across tabs and counts.
- No session leakage across requests; no DetachedInstance errors introduced.
- No Nginx/Gunicorn config changes required.

## Observability
- Keep `[JOB-QUERY-TIMING]` and `[APPROVAL-BACKEND-TIMING]` logs.
- Optional: Add debug log when teardown fires in development.

## Rollback
- Safe to revert teardown addition; maintain `expire_all()` defense as a fallback.

## References (Context7)
- SQLAlchemy Session identity map; `expire_all()` expires state; `expire_on_commit` controls post-commit behavior. (/sqlalchemy/sqlalchemy)
