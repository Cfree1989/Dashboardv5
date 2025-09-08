# Root Cause Analysis: Stale UPLOADED list after approval

## Summary
- After approving a job from UPLOADED, the modal closes but the job remains visible in the UPLOADED tab and the tab count does not change immediately. The job disappears 45–90 seconds later and appears under PENDING.
- Database updates are immediate and correct; delay is in API responses returning stale data.

## Impact
- Staff see incorrect job status for up to ~90s
- Confusing UX (job appears to remain in UPLOADED)

## Timeline of Events
- Approval request returns 200 quickly; logs show commit completes in milliseconds
- Subsequent GET /api/v1/jobs?status=UPLOADED responds with stale list
- Counts and lists eventually update later without further action

## What we observed
- Frontend was calling fresh data endpoints as expected after approval
- Database reflected status=PENDING immediately (validated via external_db_check.py)
- No explicit caching layers in requirements or Nginx config

## Technical Findings
- Approval flow commits immediately in `backend/app/business_logic/job_lifecycle/job_approval_service.py`:
```44:176:backend/app/business_logic/job_lifecycle/job_approval_service.py
        db.session.add(job)
        db.session.commit()
        db.session.refresh(job)
        logger.info(f"[APPROVAL-BACKEND-TIMING] Job {job_id} status after commit: {job.status}")
```
- Listing uses `JobQueryService` which explicitly forces session to see latest committed data:
```36:62:backend/app/services/infrastructure/job_query_service.py
        # Force database session refresh to see latest committed changes
        db.session.expire_all()
        query = Job.query
        if filters.status:
            query = query.filter_by(status=filters.status)
        jobs = query.all()
```
- Routes construct a fresh `JobQueryService()` per request (no shared state), reducing risk of long-lived session reuse:
```56:71:backend/app/routes/jobs.py
@bp.route('', methods=['GET'])
@token_required
def list_jobs():
    job_query_service = JobQueryService()
    filters = JobFilters(
        status=request.args.get('status'),
        search=request.args.get('search'),
        printer=request.args.get('printer'),
        discipline=request.args.get('discipline')
    )
    jobs = job_query_service.list_jobs(filters)
    return ResponseService.success([job.to_dict() for job in jobs])
```
- SQLAlchemy is configured with `expire_on_commit=False` globally, but queries explicitly call `db.session.expire_all()` to avoid stale reads:
```178:223:backend/app/__init__.py
    db.init_app(app)
    db.session.expire_on_commit = False
```
- Gunicorn is used only in production; dev runs a single-process Flask server. In production, 4 workers are configured:
```33:35:backend/Dockerfile.prod
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "run:app"]
```
- Nginx config does not enable proxy cache for dynamic API; `/api` location has `proxy_buffering off;`.

## Root Cause
Two interacting contributors created stale reads immediately after approval:
- A. Multiple Gunicorn workers can serve requests concurrently. If a long-lived session on Worker A had not expired, it could return stale entities when queried immediately after Worker B commits. SQLAlchemy defaults combined with connection pooling can delay visibility if the session identity map isn’t invalidated.
- B. Frontend request-level caching previously returned warm responses for up to ~60s; when present, the UI showed stale lists until cache TTL elapsed. This compounded the perception of backend delay.

The decisive fix in code is the forced invalidation before list/count queries: `db.session.expire_all()` in `JobQueryService`. On the frontend, bypassing cache on post-mutation fetches guarantees freshness.

## Why the database change was immediate
- Verified independently using `external_db_check.py`, which connects directly via psycopg2 and observed the UPLOADED count drop as soon as approval completed.

## Contributing Factors
- `expire_on_commit=False` avoids attribute expiration, improving perf but increasing risk of stale identity-map data across requests if sessions aren’t reset per request.
- Missing explicit teardown of sessions at request end (no `db.session.remove()` hook observed), relying on Flask-SQLAlchemy’s default context scoping; long-lived sessions in workers can retain identity maps.
- Frontend caching layer returned previously fetched results unless bypassed.

## Corrective Actions (Implemented)
- Backend: Add `db.session.expire_all()` in `JobQueryService.list_jobs()` and `get_job_counts()` to force fresh reads after writes.
- Frontend: Ensure post-approval refresh uses `fetchJobs(true)` to bypass client cache and immediately fetch fresh data.

## Preventative Measures
- Add `@app.teardown_appcontext` or `@app.teardown_request` handler to call `db.session.remove()` ensuring sessions are cleared at end of each request to prevent stale identity maps.
- Keep `db.session.expire_all()` in read paths that feed real-time UI components (lists/counts) to be defensive.
- Consider enabling `expire_on_commit=True` if safe for the app, or move to session-per-request patterns explicitly.
- Add regression tests: approve job → immediately list UPLOADED → must not include approved job; verify counts route too.
- Monitor logs for query timing and include a correlation id across write→read sequences during approval flows.

## Verification Steps
1. Approve a job in UPLOADED.
2. Immediately GET `/api/v1/jobs?status=UPLOADED` and `/api/v1/jobs/counts`.
3. Confirm the approved job is not listed and counts reflect the change.
4. Validate external_db_check.py shows UPLOADED count drop concurrently.

## References
- Approval write path and commit: `backend/app/business_logic/job_lifecycle/job_approval_service.py`
- Read paths: `backend/app/services/infrastructure/job_query_service.py`
- Routes using fresh service instances: `backend/app/routes/jobs.py`
- Gunicorn worker config (prod only): `backend/Dockerfile.prod`
- Nginx proxy settings (no API caching): `docker/nginx/conf.d/default.conf`
