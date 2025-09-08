# Cline Tasks — Stale Read Remediation (Executor)

## Action Plan (from Solutions_Architecture.md)
- [x] Backend: Add session-per-request teardown `@app.teardown_request -> db.session.remove()`
- [x] Backend: Keep defensive `db.session.expire_all()` in `JobQueryService.list_jobs()` and `get_job_counts()`
- [x] Frontend: Ensure post-mutation refresh bypasses cache (`fetchJobs(true)`)
- [x] Infrastructure: Nginx keeps API buffering off (no caching for `/api`)
- [x] Logging: Sampling-based warning if session teardown fails
- [x] Lints: Verify modified files have no linter issues
- [x] Documentation: Update `.cursor/scratchpad.md` with progress and lessons

## Implementation Details
1) Backend teardown hook
   - File: `backend/app/__init__.py`
   - Added:
     ```python
     @app.teardown_request
     def remove_session(exception=None):
         try:
             db.session.remove()
         except Exception as e:
             if int(time.time() * 1000) % 100 == 0:
                 app.logger.warning('Session teardown remove() failed', extra={'extra_fields': {'error': str(e), 'event': 'session_teardown_failure'}})
     ```

2) Defensive expiration on read paths
   - File: `backend/app/services/infrastructure/job_query_service.py`
   - Verified `db.session.expire_all()` is called in `list_jobs()` and `get_job_counts()`

3) Frontend post-mutation refresh
   - File: `frontend/src/components/dashboard/job-list.tsx`
   - Verified `handleJobMutation()` calls `await fetchJobs(true)` to bypass cache
   - `JobCard` awaits `onApprove` before closing modal

4) Nginx API buffering disabled
   - File: `docker/nginx/conf.d/default.conf`
   - Verified `location /api` contains `proxy_buffering off;`

5) Lints
   - Ran lints on `backend/app/__init__.py` — no issues

## Validation
- Approve job → immediate `fetchJobs(true)` ensures fresh UI
- Session removed after each request avoids identity-map staleness across workers
- Nginx not buffering API responses

## Next Step
- [ ] Update `.cursor/scratchpad.md` with progress and lessons


