# Integration & Deployment Plan

## Overview
Deploy session hygiene and defensive freshness without schema changes; low-risk rollout.

## Environments
- Dev → Staging → Production

## Pre-Checks
- Ensure CI passes unit/integration tests.
- Verify no pending migrations.

## Implementation Steps
1) Backend
- Add teardown handler in `backend/app/__init__.py`:
  - `@app.teardown_request` → `db.session.remove()`
- Confirm `JobQueryService` retains `db.session.expire_all()` in list/counts.

2) Frontend
- Ensure post-mutation paths call `fetchJobs(true)`.

3) Infrastructure
- No changes to Nginx or Gunicorn required.

## Deployment Steps
- Dev
  - Build backend and frontend images; run docker-compose.dev.
  - Manual test: approve → list/ counts; confirm immediate update.
- Staging
  - Build with Dockerfile.prod; deploy via docker-compose.prod.
  - Validate `/api/v1/jobs` and `/api/v1/jobs/counts` timing and freshness.
- Production
  - Rolling deploy backend, then frontend.
  - Monitor logs for `[JOB-QUERY-TIMING]` and errors.

## Validation Checklist
- Approve job → UPLOADED list and counts reflect immediately.
- No increase in request latency >10% on list/counts.
- No session leak warnings.

## Rollback Strategy
- Revert the teardown addition in `__init__.py`.
- Frontend can retain bypass; harmless.
- Redeploy previous images.

## Risk Matrix
- Low: Backend teardown handler — mitigated with tests.
- Low: Frontend bypass — local to mutation flows.

## Monitoring & Alerting
- Add log sampling for teardown exceptions (dev only).
- Track average query time for lists/counts.

## Ownership
- Backend: API team
- Frontend: Dashboard team
- DevOps: Deploy/monitor

## References
- Root_Cause_Analysis.md, Sequence_Diagram.md
- Context7: SQLAlchemy Session identity map and expiration (/sqlalchemy/sqlalchemy)
