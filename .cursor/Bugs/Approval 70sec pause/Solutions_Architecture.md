# Solutions Architecture: Eliminating Stale Reads and Ensuring Immediate UI Consistency

## Context and Problem
- Incident: Post-approval, the UPLOADED list and counts stayed stale for 45–90s, despite immediate DB commit.
- Evidence: `Root_Cause_Analysis.md` and `Sequence_Diagram.md` confirm SQLAlchemy Session identity-map staleness across Gunicorn workers and client-side cache compounding.

## Objectives
- Ensure read-after-write consistency for dashboard lists and counts.
- Preserve performance and keep compatibility with existing Flask/SQLAlchemy stack.
- Avoid introducing heavy caching layers; keep infra simple.

## Target-State Architecture
- Backend (Flask + SQLAlchemy): Session-per-request hygiene; optional guarded invalidation toggle for real-time reads.
- Frontend (Next.js): Centralized post-mutation refetch that bypasses client cache to guarantee freshness.
- Runtime: Gunicorn workers unchanged; Nginx remains non-caching for API.

## Design Principles
- Favor session hygiene over global invalidation knobs.
- Isolate real-time read paths to be defensively fresh.
- Keep idempotent post-mutation refresh on the client.

## Key Changes
- Backend:
  - Session teardown hook ensures session-per-request hygiene:
    - `@app.teardown_request` → `db.session.remove()`
  - Add correlation-id `[RAW-TRACE]` logs across write→list→counts.
  - Guarded freshness toggle: `FRESH_READ_DEFENSIVE=1` enables `db.session.expire_all()` in `JobQueryService` (default OFF).
- Frontend:
  - Centralized `mutateThenRefetch` in `unified-api-client.ts` to refetch counts/list with `ttl: 0` and `cache: 'no-store'`.
  - Optimistic removal: immediately remove mutated job from current tab while fresh fetch runs.
  - Unified approach—no `_ts` query param needed when `ttl: 0` is honored.
- Infrastructure:
  - No Nginx cache; keep `proxy_buffering off` for `/api`.
  - Keep Gunicorn workers (4) as-is.

## Data Flow (Aligned with Sequence Diagram)
- Approval (GW2) commits → immediate list/count fetch (GW1) → fresh session + optional defensive expire → DB returns fresh rows → UI updated.
- Post-mutation UI uses `mutateThenRefetch` to avoid cache reuse; `ttl: 0` and `no-store` ensure freshness.
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
