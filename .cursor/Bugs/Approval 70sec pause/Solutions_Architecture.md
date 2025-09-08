# Solutions Architecture: Eliminating Stale Reads and Ensuring Immediate UI Consistency

## Context and Problem
- Incident: Post-approval, the UPLOADED list and counts stayed stale for 45–90s, despite immediate DB commit.
- Evidence: `Root_Cause_Analysis.md` and `Sequence_Diagram.md` confirm SQLAlchemy Session identity-map staleness across Gunicorn workers and client-side cache compounding.

## Objectives
- Ensure read-after-write consistency for dashboard lists and counts.
- Preserve performance and keep compatibility with existing Flask/SQLAlchemy stack.
- Avoid introducing heavy caching layers; keep infra simple.

## Target-State Architecture
- Backend (Flask + SQLAlchemy): Session-per-request hygiene with defensive invalidation on read endpoints powering real-time UI.
- Frontend (Next.js): Post-mutation fetches bypass client cache to guarantee freshness.
- Runtime: Gunicorn workers unchanged; Nginx remains non-caching for API.

## Design Principles
- Favor session hygiene over global invalidation knobs.
- Isolate real-time read paths to be defensively fresh.
- Keep idempotent post-mutation refresh on the client.

## Key Changes
- Backend:
  - Keep defensive `db.session.expire_all()` in `JobQueryService.list_jobs()` and `get_job_counts()`.
  - Add session teardown hook to ensure session-per-request hygiene:
    - `@app.teardown_request` → `db.session.remove()`
  - Route-level approval now passes `g.workstation_id` explicitly and logs `[ROUTE-APPROVE]` entries.
- Frontend:
  - Ensure `fetchJobs(true)` is called after approval/reject/etc.
  - Bypass client caches by appending a `_ts` param on bypass and honoring `ttl: 0` correctly in the unified API client.
  - Set `Cache-Control: no-store, no-cache, must-revalidate` and `cache: 'no-store'` for direct requests.
  - Optimistic removal: immediately remove approved job from the UPLOADED list locally while the fresh fetch runs.
- Infrastructure:
  - No Nginx cache; keep `proxy_buffering off` for `/api`.
  - Keep Gunicorn workers (4) as-is.

## Data Flow (Aligned with Sequence Diagram)
- Approval (GW2) commits → immediate list/count fetch (GW1) → Session identity map is expired before query → DB returns fresh rows → UI updated.
- Post-mutation UI calls `fetchJobs(true)` to avoid client cache reuse; `_ts` enforces uniqueness.
- Optimistic removal ensures immediate visual consistency before network returns.

## Risks and Mitigations
- Risk: Added `expire_all()` on hot paths could increase query load.
  - Mitigation: Scope defensive expiration to lists/counts only; monitor query timings.
- Risk: Session removal on teardown must be correct in app factory.
  - Mitigation: Added teardown hook with sampled warning logs; validated in staging.

## Observability
- Keep timing logs `[JOB-QUERY-TIMING]`, `[JOB-COUNT-TIMING]`, and `[APPROVAL-BACKEND-TIMING]`.
- Sampling-based log for session teardown errors.
- Frontend console logs: `[FETCH-JOBS-TIMING]`, `[JOB-LIST-TIMING]`, `[JOB-CARD-TIMING]`, `[APPROVAL-TIMING]`.

## References (Context7)
- SQLAlchemy Session is an identity map; not a query cache; `expire_all()` and `refresh()` ensure freshness after commits. (Context7: /sqlalchemy/sqlalchemy – Session identity map, expire_all, expire_on_commit)

## Compatibility
- No schema changes. No API contract changes. Purely behavioral improvements.

## Success Criteria
- Approve job → immediate refresh shows job removed from UPLOADED and counts updated within < 2–3s.
- No regressions in other list endpoints.

## Out-of-Scope
- Introducing a second-level cache or sticky-session routing.
- Changing isolation levels.
