# 3D Print Management System - Build Plan

## Background and Motivation

Building a complete 3D Print Management System for academic/makerspace environments.

### Core System Requirements
1. Flask API-only backend (PostgreSQL)
2. Next.js frontend (TypeScript)
3. Workstation authentication + staff attribution
4. Full job lifecycle (submission → pickup)
5. File integrity via metadata.json
6. Event logging/audit trails
7. Email notifications and student confirmation
8. Custom protocol handler for slicer
9. Docker-based deployment

### Key Design Principles
- Professional V0 UI/UX
- API-first separation
- Multi-user (≤2 staff workstations)
- Robust error handling and recovery

## Working Roadmap (Condensed)

### Current Status
- Current Phase: Phase 4 — Advanced Features
- Next Milestone: Phase 4.2 — File Management: metadata authority durability
- Overall Progress: ~60%

### Active Workstreams (Open)

1) File Tracking & Metadata
- [x] Metadata durability: keep DB `job.file_path` and `metadata.json.authoritative_filename` in sync across transitions; add tests
- [x] Audit report endpoint: flags missing authoritative file, duplicate/stale siblings, directory/status mismatches
- [ ] Admin UI: Audit report view + safe actions (delete orphan, mark stale) with events
- [x] FS tests: transition path updates on disk + `metadata.json` sync using temp storage

2) Incident — Missing Jobs After Reboot (triage + prevention)
- [ ] Verify environment/DB in use
  - `docker compose ps`
  - `docker compose logs backend --no-log-prefix -n 100`
  - Health: `http://localhost:5000/health`
  - DB truth: `docker compose exec db psql -U fablab_user -d 3d_print_system -c "select status, count(*) from job group by status;"`
- [ ] Enforce Postgres usage and restore visibility
- [ ] Backend guardrails (no SQLite fallback) + test
- [ ] Backend diagnostics endpoint `_diag`
- [ ] Frontend diagnostics panel (admin-only)
- [ ] Runbook documentation

3) Payment & Pickup Workflow
- [x] Backend: `POST /api/v1/jobs/:id/payment` (grams, txn_no, picked_up_by) → transition to `PAIDPICKEDUP`; persists Payment; logs event; moves files; tests pass
- [ ] Frontend: Payment modal integration on `COMPLETED` cards; success removes job and refreshes counts

4) Protocol Handler (`3dprint://`)
- [ ] Build SlicerOpener with logging; integrate open/save awareness events; Approve modal already has rescan UX

5) Testing & Deployment
- [ ] Expand unit/integration/e2e coverage
- [ ] Production deployment configuration
- [ ] Documentation and training materials

6) Approve Endpoint — Manual Verification
- [ ] Phase 5.1.1 implemented and unit-tested; perform manual verification of `{ staff_name, weight_g, time_hours }`, cost calc (min $3), and event attribution

## Completed (Archive)

Preserved for history; reorganized for clarity (do not delete).

### Phase 1: Environment Setup & Foundation — COMPLETE
- [x] Project structure creation
- [x] Backend foundation (Flask app factory, models, requirements)
- [x] Frontend foundation (Next.js, Tailwind CSS)
- [x] Database initialization and seeding
- [x] Docker container configuration

### Phase 2: Core API Development — COMPLETE
- [x] Authentication & authorization (workstation login, JWT tokens)
- [x] Job management API (CRUD, status transitions, file upload)
- [x] Student submission API (validation, duplicate detection)
- [x] Event logging system (audit trails, staff attribution)

### Phase 3: Frontend Core Features — COMPLETE
- [x] Student submission interface (professional styling)
- [x] Staff dashboard with V0 design
  - [x] Header with last updated
  - [x] Status tabs with badges
  - [x] Job cards with icons, age coding, expandable details
  - [x] Responsive grid and loading states
  - [x] Error handling and accessibility
- [x] Design system rollout: login, submission, success/confirm, error pages

### Recently Completed Achievements
- ✅ V0 Design System Integration across pages
- ✅ Student-Staff access separation (dashboard restricted to staff)
- ✅ Responsive design and accessibility improvements
- ✅ Email Integration (Flask-Mail, templates, token service, approval+confirmation endpoints, frontend wiring)
- ✅ Tab Count Authentication Fix (counts include auth header)
- ✅ File Tracking: auto-select recommended file; “Detect newer saves” rescan; priority hierarchy

### Project Status Board — Completed Items (general)
- [x] Remove sound toggle and test button from dashboard UI
  - Success: Component deleted, imports removed, build passes
- [x] Implement backend approval + confirmation flow
  - Success: `POST /api/v1/jobs/:id/approve` → PENDING, email with token; confirmation sets READYTOPRINT; tests pass
- [x] Wire frontend Approve to backend endpoint
  - Success: Clicking Approve calls API; job removed from UPLOADED; frontend builds cleanly
- [x] Planner: Scope Phase 5.1 Approval Modal (UX + inputs)
  - Success: Documented plan with tasks, acceptance, and API contracts

### Phase 5.1 — Approval Modal Flow (Completed Parts)
- [x] 5.1.2 — Frontend: Approval Modal UI
- [x] 5.1.3 — Wire JobCard “Approve” to Modal + API
- [x] 5.1.4 — Tests (backend + frontend)
- [x] 5.1.5 — Candidate Files (stub)

### Phase 5.2 — Rejection Flow — COMPLETE
- [x] Backend: `POST /api/v1/jobs/:id/reject` with `{ staff_name, reasons[], custom_reason }`; validates status, sets `REJECTED`, logs event
- [x] Frontend: Rejection Modal UI (with confirmation); removes job on success
- [x] Tests: Frontend validation and API call

### Phase 5.3 — Status Change Modals — COMPLETE
- [x] Backend: `mark-printing`, `mark-complete`, `mark-picked-up` (guards + event logs)
- [x] Frontend: Reusable `StatusChangeModal`; contextual actions; success toast; counts refresh
- [x] Tests: Backend transitions validated; frontend modal tests

### Phase 6.2 — Visual Alerts & Reviewed Flow — COMPLETE
- [x] Backend: Persist `staff_viewed_at`; `POST /api/v1/jobs/<id>/review`; events `JobReviewed`/`JobReviewCleared`
- [x] Frontend: NEW badge rules; review/unreview modals; state persists across refresh
- [x] Tests: Backend + frontend

### Phase 4.2 — File Management (Completed Parts)
- [x] Backend: Candidate-files scan hardening (configurable extensions; priority > recency > name)
- [x] Frontend: Rescan in Approve modal; recommended preselected
- [x] Protocol touchpoint (logging only): `FileOpenedInSlicer`
- [x] Metadata durability + sync: confirmation and all transitions update `metadata.json` (`authoritative_filename`, `status`, `file_path`) and stay in parity with DB; covered by temp FS tests

### Authority Hardening — Completed Parts
- [x] Approve uses env-driven extensions and file existence checks
- [x] Approve event attribution uses `staff_name` + `workstation_id`
- [x] Deterministic candidate ranking; endpoint returns `recommended`
- [x] Resilient moves for transitions (copy → DB update → delete) with metadata sync

### Admin Page (MVP) — COMPLETE
- [x] Add `/admin` route with auth guard; header & layout
- [x] Move Diagnostics to Admin; remove from Dashboard
- [x] Implement Staff Management CRUD (list/add/toggle active)
- [x] Scaffold Overrides/Data Mgmt/Audit/Email tools (disabled)
- [x] Harden `_diag` (use `current_app` + ORM); optional alembic; nav link from dashboard
- [x] Tests for `_diag` (authorized/unauthorized)

## Incidents (Tracking)

### Missing Jobs After Reboot
- See Active Workstreams (item 2) for recovery and prevention steps.

## Lessons
- Include useful debug info in program output
- Read files before editing
- If vulnerabilities appear, run `npm audit` before proceeding
- Always ask before using the `-force` git command
- Remove unused imports/usages safely to avoid build breaks
 - On Windows PowerShell, prefer `pytest -q` (avoid piping to `cat`); `&&` is not a valid separator

## Future Tasks

### Phase 4 — Advanced Features (Remaining)
- 4.2 File Management: Metadata Durability
  - [x] Audit report endpoint (GET `/api/v1/admin/audit/report`) — identifies orphans, broken links (missing file/meta, dir/status mismatch, metadata mismatch), and stale duplicates
  - [ ] Admin UI (report view + safe actions)
  - Acceptance: Audit flags inconsistencies; safe actions available; events logged
- 4.3 Payment & Pickup
  - Backend
    - [x] `POST /api/v1/jobs/:id/payment` with `{ grams, txn_no, picked_up_by, staff_name }`; validate status `COMPLETED`
    - [x] Persist `Payment` record; transition to `PAIDPICKEDUP`; log attributed events; unit tests
  - Frontend
    - [ ] Payment modal on `COMPLETED` cards; inputs + validation; success removes job and refreshes counts; error states; a11y
  - Acceptance: End-to-end payment recorded; job moves to Paid & Picked Up; events/audit present; tests pass
- 4.4 Protocol Handler (Foundational)
  - [ ] Package `SlicerOpener` with `config.ini`, security validation, GUI feedback, logging, PyInstaller build, registry installer
  - [ ] API event logging for `FileOpenedInSlicer`; ensure dashboard links generate `3dprint://` URIs
  - Acceptance: Handler opens valid files via protocol; secure path validation; clear GUI errors; action logged

### Phase 5 — UI Workflows (Remaining)
- 5.4 Notes Editing
  - Backend: [ ] `PATCH /api/v1/jobs/<id>/notes` with attribution; events; tests
  - Frontend: [ ] Inline notes editor (auto-save, error states, a11y)
  - Acceptance: Notes persist and are audited; optimistic UI works; tests pass
- 5.5 Admin Overrides (Enable currently scaffolded UI)
  - Backend: [ ] Force unlock, force confirm, change status, mark failed endpoints with guardrails and events
  - Frontend: [ ] Wire actions with confirmations + reason capture
  - Acceptance: Admin-only actions work with full audit; error/edge cases covered
- 5.6 Direct Job Deletion (UPLOADED/PENDING)
  - Backend: [ ] `DELETE /api/v1/jobs/<id>` with locking precondition, irreversible delete of files + DB
  - Frontend: [ ] Confirmation modal; success removes job; tests
  - Acceptance: Eligible jobs delete safely; audited; tests pass
- 5.7 Revert Actions
  - Backend: [ ] `revert-completion`, `revert-pickup` endpoints; events
  - Frontend: [ ] Contextual “Revert” where applicable
  - Acceptance: Valid states revert cleanly; audited; tests pass

### Phase 6 — Real-time, Locks, Alerts (Remaining)
- 6.1 Auto-Refresh & Indicators
  - [ ] Job age color-coding; improved last-refreshed indicator
  - [ ] Background audio notification on new uploads (config in Admin later)
  - Acceptance: Visual/audio cues behave as specified; no console errors
- 6.2 Reviewed Flow — COMPLETE (for reference)
- 6.3 API-Level Locking
  - Backend: [ ] Lock/unlock/extend endpoints; lock fields on Job; server-side enforcement; tests
  - Frontend: [ ] Acquire on modal open; heartbeat; release on close; conflict UX
  - Acceptance: Concurrent edits prevented; clear conflict messaging; tests pass

### Phase 7 — Testing & Deployment
- [ ] E2E happy paths (submit → approve → confirm → print → complete → pay/pickup)
- [ ] CI pipeline (tests/lint/format on PRs)
- [ ] Production deploy config docs (env vars, secrets, volumes, reverse proxy, CORS)
- [ ] Public `GET /api/v1/health` with DB/worker checks
- Acceptance: Green CI; one-click deploy instructions verified

### Phase 8 — Analytics & Reporting
- Frontend `/analytics`
  - [ ] Overview cards (submissions, queue by status, turnaround, storage usage, rejections)
  - [ ] Trend charts (submissions/approvals over time, throughput, lead time)
  - [ ] Resource metrics (printer utilization, material consumption)
- Backend
  - [ ] `/analytics/overview`, `/analytics/trends`, `/analytics/resources`, `/stats`, `/stats/detailed`
  - Acceptance: Pages render with filters, loading/error/empty states; endpoints return expected shapes; tests pass

### Phase 9 — System Health & Integrity
- [ ] `_diag` already hardened; extend with worker status
- [ ] Audit endpoints: start audit, fetch report, delete orphaned file
- [ ] Admin UI: System Health with report and safe actions
- Acceptance: Audit identifies orphans/broken/stale; admin resolves safely; events logged

### Phase 10 — Data Retention & Archival
- [ ] `POST /api/v1/admin/archive` (retention days)
- [ ] `POST /api/v1/admin/prune` (retention days)
- [ ] Admin UI for preview counts and confirmations
- Acceptance: Policies enforced; actions audited; tests pass

### Phase 11 — Security & Rate Limiting
- [ ] Flask-Limiter: `/api/v1/submit` and `/api/v1/auth/login` throttling
- [ ] Tighten CORS/headers; basic CSP
- Acceptance: Limits enforced with proper 429s; CORS restricted in prod

### Phase 12 — Background Jobs & Email Queue
- [ ] Introduce Redis + RQ worker; queue emails (approval/rejection/completion) and exports
- [ ] Retry strategy and logging
- Acceptance: Async tasks reliable; app responsive; observability present

### Phase 13 — Financial Reporting
- [ ] `POST /api/v1/export/payments` to generate Excel; email link
- [ ] Admin UI trigger with filters and status
- Acceptance: Export generated and delivered; audited; rate limits where needed

### Phase 14 — Performance, Reliability, and Polish
- [ ] DB indexes (jobs by status/updated_at; events by job_id/timestamp)
- [ ] Event log rotation/retention policy
- [ ] Storage monitoring (usage vs limit)
- [ ] A11y sweep and visual polish
- Acceptance: Smoother UX and stable ops with documented SLOs

## Next Steps Priority Queue
1) Phase 4.2 — Audit admin UI + safe actions (delete orphan, mark stale) with events
2) Payment workflow — frontend integration (modal attach to COMPLETED cards + counts refresh)
3) Protocol handler (SlicerOpener) packaging and UX
4) Comprehensive testing + deployment docs
5) Analytics Dashboard (`/analytics`) after operations stabilize


