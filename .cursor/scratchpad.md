# 3D Print Management System - Build Plan

## Background and Motivation

Building a complete 3D Print Management System for academic/makerspace environments with the following key requirements:

### Core System Requirements:
1. **Flask API-only backend** with PostgreSQL database
2. **Next.js frontend** with TypeScript and modern UI components  
3. **Workstation-based authentication** with mandatory staff attribution
4. **Complete job lifecycle management** from submission to pickup
5. **File integrity and resilience** with metadata.json tracking
6. **Comprehensive audit trails** with Event logging
7. **Email notifications** and student confirmation workflows
8. **Custom protocol handler** for direct file opening in slicer software
9. **Docker-based deployment** for consistency and simplicity

### Key Design Principles:
- **Professional UI/UX** following V0 design standards
- **API-first design** with clear separation of concerns
- **Multi-user environment** supporting up to 2 staff workstations
- **Comprehensive error handling** and recovery mechanisms

## Project Phases Overview
## Planner: Authoritative File Tracking Enhancement (Reduce Friction at Approve)

### Background and Motivation
- Current Approve flow requires staff to explicitly pick an authoritative file. This is safe but adds friction. We want the system to reliably track the authoritative file from submission through status transitions, while still allowing an override when needed.

### Key Challenges and Analysis
- Slicer saves can create multiple sibling files with various extensions; the newest is not always the right one.
- Watching the filesystem continuously from Docker/Windows is brittle; safer to scan at workflow checkpoints (Approve, status transitions) and to log explicit staff intent.
- We need a single source of truth: `job.file_path` in DB and mirrored in `metadata.json` for resilience.

### High-level Task Breakdown
1) Default Auto-Selection (Immediate UX)
   - Keep scanning candidates at Approve, but auto-select the recommended file (newest valid sibling). Hide the picker behind “Choose different file…”.
   - Success: Approve is one-click in most cases; staff can override when needed.

2) Source of Truth + History (DB + metadata.json)
   - Persist `authoritative_filename` and `authoritative_history` in `metadata.json`; keep DB `job.file_path` in sync.
   - On each transition, ensure files exist and paths are consistent; log event details.
   - Success: File choice is durable; recoverable after restarts.

3) Open/Save Awareness via Protocol Handler (Near-term)
   - When staff click “Open in Slicer” via `3dprint://`, log an `FileOpenedInSlicer` event.
   - Add a lightweight rescan button “Detect newer slicer saves” that re-ranks candidates and proposes update.
   - Success: Staff prompted when a newer sibling is detected; minimal manual effort.

4) Integrity Audit Hooks (Admin → System Health)
   - Extend audit to detect: missing authoritative file, duplicate/stale siblings, and directory/status mismatches.
   - Success: Admin report highlights inconsistencies with quick fixes.

### Acceptance Checklist
- Approve modal preselects a recommended file; picker is optional and collapsed by default.
- `job.file_path` and `metadata.json.authoritative_filename` always match after transitions.
- “Detect newer saves” action proposes the likely authoritative upgrade.
- System Health report flags missing/duplicate/stale authoritative files.

### Project Status Board — File Tracking
- [x] UX: Auto-select recommended file; collapse chooser behind “Choose different file…”
- [x] Metadata: write/read `authoritative_filename` + history in `metadata.json`; sync on transitions (write + history implemented; read not yet used client-side)
- [x] SlicerOpener: log `FileOpenedInSlicer`; add “Detect newer saves” rescan (logging stub in API; rescan added to Approve modal)
- [ ] Audit: extend report for authoritative file issues

### Phase 1: Environment Setup & Foundation ✅ COMPLETE
- [x] Project structure creation
- [x] Backend foundation setup (Flask app factory, models, requirements)
- [x] Frontend foundation setup (Next.js, Tailwind CSS, basic structure)
- [x] Database initialization and seeding
- [x] Docker container configuration

### Phase 2: Core API Development ✅ COMPLETE  
- [x] Authentication & authorization (workstation login, JWT tokens)
- [x] Job management API (CRUD, status transitions, file upload)
- [x] Student submission API (validation, duplicate detection)
- [x] Event logging system (audit trails, staff attribution)

### Phase 3: Frontend Core Features ✅ COMPLETE
- [x] Student submission interface with professional styling
- [x] Staff dashboard with V0 professional design system
  - [x] Professional header with last updated (sound toggle removed by design)
  - [x] Beautiful status tabs with hover effects and badges
  - [x] Job cards with icons, age coding, expandable details
  - [x] Responsive grid layout with loading states
  - [x] Professional error handling and accessibility
- [x] V0 Design System Rollout across all pages:
  - [x] Login page professional upgrade
  - [x] Submission form professional styling  
  - [x] Success and confirmation pages
  - [x] Error pages and edge cases

### Phase 4: Advanced Features 🔄 IN PROGRESS
- [x] **Email service integration** - Flask-Mail, templates, token-based confirmation, approval email
- [ ] **File management system** - Upload processing, metadata.json, file movement
- [ ] **Payment & pickup workflow** - Cost calculation, payment recording, pickup confirmation
- [ ] **Protocol handler development** - SlicerOpener.py for direct file opening

### Phase 5: Job Management Modals 📋 IN PROGRESS
- [ ] **Approval Modal** - File selection, weight/time inputs, cost calculation (next)
- [ ] **Rejection Modal** - Rejection reasons, custom messages
  - Note: Includes double-confirmation step to reduce errors
- [ ] **Status Change Modals** - Printing, Complete, Pickup confirmations  
- [ ] **Notes Editing** - Inline notes interface

### Phase 6: Real-time Updates 📋 PENDING
- [x] **Auto-refresh hook** - Dashboard updates every 45s
- [ ] **Audio notifications** - Sound alerts for new jobs
- [ ] **Visual indicators** - "NEW" badges, job age tracking
- [ ] **Staff acknowledgment** - Mark as reviewed functionality

### Phase 7: Testing & Deployment 📋 PENDING
- [ ] Comprehensive testing (unit, integration, e2e)
- [ ] Production deployment configuration
- [ ] Documentation and training materials

## Current Status

**Current Phase**: Phase 4 - Advanced Features  
**Next Milestone**: Phase 4.2 — File Management System (candidate-files + authoritative tracking)
**Overall Progress**: ~60% complete

### Recently Completed Achievements:
✅ **Complete V0 Design System Integration** - All pages now have professional, consistent styling  
✅ **Student-Staff Access Separation** - Dashboard access properly restricted to staff only  
✅ **Professional UI/UX** - Application looks and feels like a modern SaaS product  
✅ **Responsive Design** - Works perfectly on mobile, tablet, and desktop  
✅ **Enhanced Accessibility** - Proper focus states, ARIA labels, keyboard navigation  
✅ **Email Integration (Phase 4.1)** - Flask-Mail, templates, token service, approval+confirmation endpoints, and frontend Approve wiring

### Active Development:
✅ **Tab Count Authentication Fix** - Fixed dashboard tabs not showing job counts due to missing authentication headers  
✅ **Phase 4.1: Email Service Integration** - Implemented Flask-Mail, templates, confirmation token service, approval endpoint, and frontend approval wiring

✅ **Phase 4.2 (subset): File Tracking Auto-Select + Rescan + Priority**
- Backend `GET /api/v1/jobs/:id/candidate-files` hardened (allowed extensions via env, relevance tokens, sorted by recency, backward-compatible response shape)
- Added authoritative extension priority hierarchy: `.3mf, .form, .idea > .stl > .obj` (configurable via `AUTHORITATIVE_EXT_PRIORITY`); endpoint returns `recommended`
- Frontend Approval modal now preselects server-recommended file and hides chooser; added “Detect newer saves” button that rescans and re-ranks candidates

## Project Status Board

- [x] Remove sound toggle and test button from dashboard UI
  - Success criteria: Component deleted, imports removed, build passes with no lint errors
- [x] Executor: Implement backend approval + confirmation flow
  - Success criteria: `POST /api/v1/jobs/:id/approve` sets PENDING, sends email with token link; `POST /api/v1/submit/confirm/<token>` sets READYTOPRINT; tests pass
- [x] Executor: Wire frontend Approve to backend endpoint
  - Success criteria: Clicking Approve calls API, removes job from UPLOADED list on success; frontend builds cleanly
- [x] Planner: Scope Phase 5.1 Approval Modal (UX + inputs)
  - Success criteria: Documented plan with task breakdown, acceptance checklist, and clear API contracts added to this file
- [ ] Executor: Phase 5.1.1 — Backend: Extend Approve endpoint for attribution + cost
  - Success criteria: `POST /api/v1/jobs/:id/approve` accepts `{ staff_name, weight_g, time_hours }`, calculates `cost_usd` server-side (min $3.00; $0.10/gram filament, $0.20/gram resin), updates job fields, logs `StaffApproved` + `ApprovalEmailSent` with `triggered_by=staff_name` and `workstation_id`, returns updated job; unit tests green
  - Status: Implemented and unit-tested (19 tests passing) — awaiting manual verification before marking complete
- [x] Executor: Phase 5.1.2 — Frontend: Build Approval Modal UI
  - Success criteria: Modal with inputs (weight_g, time_hours), live cost preview, required Staff Attribution dropdown (populated from `/api/v1/staff`), inline validation, accessible focus/ARIA; Storybook-like visual check not required
- [x] Executor: Phase 5.1.3 — Wire JobCard "Approve" to Modal + API
  - Success criteria: Clicking Approve opens modal; on submit calls API with Authorization header; optimistic update removes job from `UPLOADED` list; error states render; toast on success
- [x] Executor: Phase 5.1.4 — Tests
  - Success criteria: Backend tests for approve payload validation and event logging; Frontend tests for modal validation and API call; all CI tests pass
- [x] Executor: Phase 5.1.5 — Candidate Files (stub)
  - Success criteria: Optional `GET /api/v1/jobs/:id/candidate-files` returns at least the uploaded file; frontend shows file selector (non-blocking); can be deferred to Phase 4.2 File Management

## Incident — Missing Jobs After Reboot (Planner)

### Background and Motivation
- After a morning reboot, jobs from yesterday no longer appear on the dashboard. This is an operational integrity issue blocking staff work.

### Key Challenges and Analysis
- Most likely root causes:
  - Backend connected to a different database than yesterday (SQLite fallback vs Postgres in Docker).
  - Postgres data volume reset or different Docker project/volume name in use.
  - Frontend pointing to a different backend instance/host after reboot.
- Code observations:
  - `GET /api/v1/jobs` applies only status/printer/discipline filters; no date-based filtering or auto-archival is implemented.
  - Frontend fetches counts and lists directly; no client-side date pruning.

### High-level Task Breakdown (Recovery + Prevention)
1) Verify active environment and database in-use (Today vs Yesterday)
   - Run environment checks:
     - `docker compose ps` and `docker compose logs backend --no-log-prefix -n 100`.
     - Backend health: open `http://localhost:5000/health`.
     - DB truth: `docker compose exec db psql -U fablab_user -d 3d_print_system -c "select status, count(*) from job group by status;"`.
   - Success criteria: We know exactly which DB is active and whether it contains yesterday's jobs.

2) If mismatch (SQLite vs Postgres) or empty DB, align services to Postgres and restore visibility
   - Ensure stack is started via Docker (`docker compose up -d`) so backend uses Postgres per `DATABASE_URL`.
   - If jobs exist in Postgres: confirm dashboard shows them across tabs.
   - Success criteria: Yesterday’s jobs visible again without code changes.

3) Add backend guardrails to prevent silent SQLite fallback
   - Fail fast when `DATABASE_URL` is missing in non-test mode; log active DB URI (sanitized) at startup.
   - Tests: add a unit/integration test asserting startup warning/fail in production mode without `DATABASE_URL`.
   - Success criteria: Local runs cannot silently create/use `app.db`.

4) Add a diagnostics endpoint for rapid triage (protected)
   - `GET /api/v1/_diag` (JWT required): returns `{ db_engine, db_url_sanitized, migration_head, job_counts_by_status, app_env }`.
   - Tests: endpoint returns expected fields with seeded data.
   - Success criteria: One-click visibility into environment and data health.

5) Frontend diagnostics panel (admin-only, lightweight)
   - Add a small panel/button in dashboard to fetch and display `_diag` information.
   - Success criteria: Staff can quickly confirm they are on the correct DB and see counts.

6) Documentation: Runbook for "Missing Jobs After Reboot"
   - Add a concise README section with the commands above, common causes, and fixes.
   - Success criteria: Clear steps for future incidents.

### Project Status Board (Incident Tasks)
- [ ] Task 1: Verify environment/DB
  - Success: Commands confirm services and DB contents; yesterday’s data location identified.
- [ ] Task 2: Enforce Postgres usage and regain visibility
  - Success: Dashboard shows yesterday’s jobs again.
- [ ] Task 3: Backend guardrails (no SQLite fallback)
  - Success: Startup fails/warns without `DATABASE_URL`; test added.
- [ ] Task 4: Backend diagnostics endpoint `_diag`
  - Success: Endpoint exists, protected, returns fields; tests pass.
- [ ] Task 5: Frontend diagnostics panel
  - Success: Admin-only UI shows `_diag` results.
- [ ] Task 6: Runbook doc
  - Success: README section added with step-by-step recovery.

### Executor's Feedback or Assistance Requests (Incident)
- Please confirm how the stack was started today vs yesterday (Docker vs local `flask run`/`python run.py`).
- Share outputs:
  - `docker compose ps`
  - `docker compose logs backend --no-log-prefix -n 100`
  - `docker compose exec db psql -U fablab_user -d 3d_print_system -c "select status, count(*) from job group by status;"`
- On the dashboard, do status badges show any non-zero counts?

## Planner: Admin Page & Diagnostics Placement

### Background and Motivation
- Diagnostics should not appear on the main dashboard. It belongs in an Admin/Settings area. The current diagnostics fetch returned HTTP 500 and must be stabilized.

### Key Challenges and Analysis
- Diagnostics endpoint may 500 due to environment accessors or raw SQL table naming.
- Admin page does not exist yet; we need a minimal protected page to host tools like diagnostics.

### High-level Task Breakdown
1) Remove Diagnostics panel from Dashboard
   - Edit `frontend/src/app/dashboard/page.tsx` to remove the diagnostics import and component.
   - Success: Dashboard has no diagnostics card; build passes.

2) Create Admin page and mount Diagnostics there
   - Add `frontend/src/app/admin/page.tsx` (protected by existing workstation JWT; redirect to `/login` if no token).
   - Render a simple "Admin / Settings" page that includes the Diagnostics panel component.
   - Success: Navigating to `/admin` shows diagnostics; other pages unaffected.

3) Fix `_diag` 500
   - Replace `db.get_app()` calls with `current_app` (available in request context).
   - Avoid raw SQL table names; compute job counts with ORM: `db.session.query(Job.status, db.func.count()).group_by(Job.status).all()`.
   - Keep alembic version read optional; no 500 if table missing.
   - Success: `_diag` returns 200 with fields even on empty DB; returns 401 on invalid/missing token.

4) Tests
   - Add a backend test for `_diag` happy path (with token) against in-memory SQLite.
   - Add a backend test for unauthorized access (401).
   - Success: Tests pass locally/CI.

5) (Optional) Route placement & permissions
   - Add an Admin nav link (visible only when token present) to `/admin` from dashboard header.
   - Success: Easy navigation to admin tools.

### Acceptance Checklist
- Dashboard no longer shows diagnostics.
- `/admin` exists and renders diagnostics with valid token; unauthorized users are redirected to login.
- `_diag` returns 200 with `{ db_engine, db_url_sanitized, migration_head|null, job_counts_by_status, app_env }` and never 500 in normal conditions.
- Tests added for `_diag`.

### Decision & Prioritization
- Proceed now with a minimal Admin page to host Diagnostics and remove the Diagnostics card from the main dashboard. Defer the full Analytics (`/analytics`) page until after current Phase 5 workflows are solid.
- Rationale: Diagnostics fix is directly related to stability and recent incident. Admin page is a small, contained addition. Analytics is larger and not blocking operations.

### Project Status Board (Admin/Diagnostics)
- [ ] Remove Diagnostics card from `dashboard/page.tsx`
  - Success: No diagnostics UI on dashboard; build passes
- [ ] Create `frontend/src/app/admin/page.tsx` and mount `DiagPanel`
  - Success: `/admin` shows diagnostics when logged in; redirects to `/login` otherwise
- [ ] Backend: Fix `_diag` 500 (use `current_app`, ORM counts, optional alembic)
  - Success: `_diag` stable 200; unauthorized 401
- [ ] Tests: `_diag` authorized/unauthorized
  - Success: Tests green

## Planner: Admin Page (MVP based on Images + Masterplan)

### Background and Motivation
- Create a dedicated Admin page (`/admin`) to house Diagnostics and administrative tools. Remove Diagnostics from the main dashboard. Follow the master plan’s Admin sections and match the provided screenshots for layout and tone.

### Key Challenges and Analysis
- Admin actions (overrides, archival, audit) are scoped in master plan but not fully implemented server-side yet. We’ll scaffold UI sections with clear disabled states and tooltips until endpoints exist.
- Ensure route protection via workstation JWT and consistent attribution patterns.

### High-level Task Breakdown (small, verifiable tasks)
1) Route & Access Control
   - Add `frontend/src/app/admin/page.tsx` as a protected page. If no token → redirect to `/login`.
   - Success: Visiting `/admin` while logged out redirects to login; with token, renders.

2) Page Layout & Header (match images & V0 styling)
   - Title "Admin / Settings", environment badge (Dev/Prod), subtitle text, last-updated timestamp.
   - Success: Visual header matches style from screenshots (spacing, typography).

3) Diagnostics Card (moved from Dashboard)
   - Use existing `DiagPanel` inside Admin page. Remove `DiagPanel` from `dashboard/page.tsx`.
   - Success: No diagnostics on dashboard; `/admin` shows diagnostics fetch and renders DB info and job counts.

4) Settings Card (MVP)
   - Fields (placeholders): Background sound enable/disable (disabled control for now), environment banner toggle (display only).
   - Success: Card renders; controls present but non-destructive; notes indicating "coming soon" where not wired.

5) Staff Management
   - List active staff (GET `/api/v1/staff`), with toggle to include inactive.
   - Actions: Add staff (POST `/api/v1/staff`), Deactivate/Reactivate (PATCH `/api/v1/staff/:name`).
   - Success: Can add, deactivate, reactivate; list updates; errors surfaced.

6) Admin Overrides (Scaffold Only)
   - Cards for Force Unlock, Force Confirm, Change Status, Mark Failed; disabled buttons with tooltip "Feature pending backend".
   - Success: UI communicates pending status; no actions performed.

7) Data Management (Archive/Prune) — Scaffold
   - Cards for Archive (POST `/api/v1/admin/archive`) and Prune (POST `/api/v1/admin/prune`); disabled until endpoints exist.
   - Success: UI present with descriptions; actions disabled.

8) System Health & Integrity (Audit) — Scaffold
   - Cards for Start Audit and View Report; disabled until endpoints exist.
   - Success: UI present with descriptions; actions disabled.

9) Email Tools — Scaffold
   - Card for Resend Email; disabled until endpoint exists.
   - Success: UI present with description; disabled.

10) Backend `_diag` Hardening (Fix 500)
   - Replace `db.get_app()` usage with `from flask import current_app`; use ORM for job counts: `db.session.query(Job.status, db.func.count()).group_by(Job.status)`.
   - Alembic version query optional; return `null` if not present; never 500.
   - Success: `_diag` 200 with stable schema; 401 when unauthorized.

11) Navigation
   - Add link to Admin from dashboard header (visible when token exists).
   - Success: Quick access to `/admin` from dashboard.

12) Tests (Backend)
   - `_diag` authorized returns expected fields; unauthorized returns 401 JSON.
   - Success: Tests pass.

13) QA & Accessibility
   - Responsive layout; keyboard navigation; aria labels on buttons/links; clear empty/error states.
   - Success: Basic a11y checks satisfied; no console errors.

### Acceptance Checklist (Admin MVP)
- `/admin` exists, protected by JWT; header matches style.
- Diagnostics works on `/admin` and is removed from `/dashboard`.
- Staff Management: list/add/deactivate/reactivate flows working.
- All other sections present as disabled scaffolds with clear descriptions.
- `_diag` stabilized (no 500), unauthorized returns 401.
- Navigation link to Admin available from dashboard.

### Project Status Board — Admin MVP
- [x] Add `/admin` route with auth guard
- [x] Build Admin header & layout per images (left menu, right content, top actions)
- [x] Move Diagnostics to Admin; remove from Dashboard
- [x] Implement Staff Management CRUD (list/add/toggle active)
- [x] Scaffold Overrides/Data Mgmt/Audit/Email tools (disabled pending backend)
- [x] Harden `_diag` (current_app + ORM)
- [x] Add Admin nav link from dashboard
- [x] Tests for `_diag` auth/no-auth

### Executor's Feedback or Assistance Requests (Admin)
- Confirm: From the screenshots, preferred section order and any specific labels/wording you want reproduced.
- Confirm: Are we okay to ship Staff Management as functional now, with other Admin sections disabled until backend endpoints are implemented?

## Phase 5.2 — Rejection Flow

- [x] Backend: `POST /api/v1/jobs/:id/reject` with `{ staff_name, reasons[], custom_reason }` — validates status `UPLOADED`, persists `reject_reasons`, sets status `REJECTED`, logs `StaffRejected`, returns updated job
- [x] Frontend: Rejection Modal UI and wiring
  - Success criteria: Modal with common reason checkboxes + custom message textarea, required Staff Attribution, submits to backend, removes job from `UPLOADED` on success, errors visible, accessible focus/ARIA
- Enhancement: Added second-step confirmation dialog ("Are you sure?") before submission
- [x] Tests: Frontend rejection modal validation and API call
  - Success criteria: Disabled submit until attribution/reason provided, correct payload shape, success path calls close/removal

## Phase 5.3 — Status Change Modals (Printing, Complete, Pickup)

- [x] Backend: Implement state transition endpoints
  - `POST /api/v1/jobs/:id/mark-printing` (from READYTOPRINT)
  - `POST /api/v1/jobs/:id/mark-complete` (from PRINTING)
  - `POST /api/v1/jobs/:id/mark-picked-up` (from COMPLETED)
  - Success criteria: Validate status preconditions; require `{ staff_name }`; log events; tests added
- [x] Frontend: Modals/UI + wiring
  - Success criteria: Each action opens a confirm modal with Staff Attribution; on success, move job to next tab and refresh counts; accessible and error states
  - Enhancement: Include second-step confirmation dialogs for each action
- [x] Tests: Backend status transition tests
  - Success criteria: Happy path transitions validated; guards enforced for wrong states

- #### High-level Task Breakdown (Frontend)
  1) Modal UI
     - Build/confirm a reusable `StatusChangeModal` in `frontend/src/components/dashboard/modals/status-change-modal.tsx` that accepts: `action` ("printing" | "complete" | "picked_up"), required Staff Attribution select (from `/api/v1/staff`), confirm/cancel buttons, loading/disabled states, and accessible labels.
  2) Wire Job Card Actions
     - In `frontend/src/components/dashboard/job-card.tsx`, surface context actions per status:
       - READYTOPRINT → “Mark Printing” → calls `POST /api/v1/jobs/:id/mark-printing`
       - PRINTING → “Mark Complete” → calls `POST /api/v1/jobs/:id/mark-complete`
       - COMPLETED → “Mark Picked Up” → calls `POST /api/v1/jobs/:id/mark-picked-up`
     - Require Staff Attribution via the modal before enabling confirm.
  3) API Integration
     - Ensure Authorization header is included; handle JSON errors; show success toast and inline error states.
  4) State Updates
     - On success, optimistically remove the job from the current list and trigger counts refresh in `dashboard/page.tsx` via the existing `onJobsMutated`/refresh hook.
  5) Tests
     - Add `status-change-modal.test.tsx` to validate: disabled confirm until staff selected, correct endpoint per action, success callback invoked, and error rendering.

- #### Acceptance Checklist (Frontend)
  - “Mark Printing/Complete/Picked Up” open a modal requiring Staff Attribution.
  - Confirm calls the correct endpoint and moves the job to the next tab; counts refresh immediately.
  - Buttons are disabled until valid; loading states and ARIA attributes are correct; errors displayed if API fails.
  - Tests pass locally/CI for modal validation and action wiring.

- ### Project Status Board — Phase 5.3 Frontend
  - [x] Modal component ready for three actions
    - Success: Reusable `StatusChangeModal` renders with attribution select and confirm disabled until valid
  - [x] Wire actions on `job-card.tsx`
    - Success: Contextual actions appear per status and open the modal
  - [x] Hook up API calls with auth + error handling
    - Success: Success toast + removal from current list; errors visible
  - [x] Counts refresh on mutation
    - Success: Tab badges update immediately after each transition
  - [x] Tests for modal + wiring
    - Success: New `status-change-modal.test.tsx` assertions pass

### Project Status Board — Phase 4.2 File Management
- [x] Backend: Candidate-files full scan hardening
  - Success: Configurable allowed extensions; only job-related siblings returned; sorted by recency; unit tests cover edge cases
- [x] Frontend: Rescan in Approve modal
  - Success: "Detect newer saves" action refreshes candidate list and re-ranks; recommended preselected; chooser collapsed by default
- [ ] Metadata: Authoritative tracking durability
  - Success: `authoritative_filename` + history reliably written in `metadata.json`; matches `job.file_path` across transitions; tests added
- [x] Protocol touchpoint (logging only)
  - Success: Clicking future "Open in Slicer" logs `FileOpenedInSlicer` (stub); no-op if handler not installed

- [x] Planner: Scope Phase 6.2 — Visual Alerts & Reviewed Flow
  - Success criteria: Document clear UX rules, backend persistence contract, frontend modal behavior, and tests; added tasks below
- [x] Executor: Phase 6.2.1 — Backend: Persist review state + expose in API (toggle)
  - Success criteria: Add `staff_viewed_at` to `Job.to_dict()`; implement `POST /api/v1/jobs/<id>/review` (auth required) with body `{ reviewed: boolean, staff_name: string }`.
    - If `reviewed === true`: validate status `UPLOADED`, set `staff_viewed_at=now`, log `JobReviewed` with `{ triggered_by, workstation_id }`.
    - If `reviewed === false`: validate status `UPLOADED`, set `staff_viewed_at=null`, log `JobReviewCleared` with attribution.
    - Return updated job; unit tests for both paths.
- [x] Executor: Phase 6.2.2 — Frontend: Review modal + visibility rules (with reapply)
  - Success criteria: Show NEW badge + glow only when `currentStatus==='UPLOADED' && !staff_viewed_at`.
    - Button “Mark as Reviewed” opens confirmation modal (text: “Have you reviewed this job?”) with required Staff Attribution select; on confirm, call backend with `{ reviewed: true }`, update job so indicator disappears and stays gone after refresh.
    - When `currentStatus==='UPLOADED' && staff_viewed_at` show a secondary action “Reapply NEW indicator” (or “Mark as Unreviewed”); opens modal with attribution; on confirm call backend with `{ reviewed: false }`, update job so indicator returns and persists across refresh.
    - Accessible focus/ARIA.
- [x] Executor: Phase 6.2.3 — Frontend/Backend Tests
  - Success criteria: Backend tests for review endpoint (status guard, event logging, auth; both reviewed/unreviewed). Frontend tests to ensure indicator visible only on Uploaded, modal required to clear/reapply, and persistence across refetch.

## Planner: Fixes from Feedback (Tabs count, Job ID length, Approved details)

### Key Challenges and Analysis
- **Tabs not counting jobs**: Backend `GET /api/v1/jobs` returns an array, but frontend expects `{ jobs: [...] }` when counting. This results in zero counts. Also, counts are fetched only on mount and not refreshed after approvals.
- **Long Job ID in UI**: UUID is shown in places; visually noisy. We should display a shortened form in UI while preserving the full value for actions.
- **Show cost/time after approval**: Backend now persists `weight_g`, `time_hours`, and `cost_usd`. The UI types and rendering need to surface these fields on cards.

### High-level Task Breakdown — Feedback Fixes
1) Tabs Count Fix
- Edit `frontend/src/app/dashboard/page.tsx` `fetchCounts()` to handle array response: `Array.isArray(data) ? data.length : (data.jobs || []).length`.
- Add a simple refresh hook so counts update after an approval: pass `onJobsMutated` callback from Dashboard to `JobList`; call `fetchCounts()` when invoked.
- Success: Tab badges reflect correct counts initially and update immediately after approving a job.

2) Shorten Job ID Display
- In `frontend/src/components/dashboard/job-card.tsx`, when rendering Job ID or fallback to ID in title, display a short form `id.slice(0, 8)` with an ellipsis or tooltip for full ID.
- Success: UI shows short IDs; actions continue to use full ID.

3) Show Approved Cost/Time on Cards
- Extend Job types in `job-card.tsx` and `job-list.tsx` to include `material`, `weight_g`, `time_hours`, `cost_usd`.
- Render a "Print Details" section (weight, time, cost) when these fields are present.
- Success: After approval, cards in `PENDING` (and beyond) show weight/time/cost.

### Acceptance Checklist (Feedback Fixes)
- Tab counts show correct numbers and update right after approving a job.
- Job IDs are shown in a shortened format in UI while keeping full functionality.
- Approved jobs display weight (g), time (hours), and cost (USD) on their cards.
- [ ] Planner: Scope Admin Page (settings and controls)
  - Success criteria: Define MVP features list (Staff Management, Admin Overrides, System Health/Audit, Archival controls, Background sound config), UI sections, and required API mappings; produce a short acceptance checklist
- [ ] Planner: Scope Analytics/Stats Page (`/analytics`)
  - Success criteria: Define overview cards and trend charts, map to `/analytics/overview`, `/analytics/trends`, `/analytics/resources`, and `/stats` endpoints; outline data shapes and loading states

## Planner: Visual Alerts & Reviewed Flow (Scope)

### Key Challenges and Analysis
- NEW indicator reappears on refresh because review state isn’t persisted: frontend only sets `staff_viewed_at` locally; backend doesn’t expose it in responses.
- Indicator should show only on `Uploaded` tab, but current UI shows whenever `!staff_viewed_at` regardless of tab.
- Clicking “Mark as Reviewed” should prompt a confirmation modal and require staff attribution; currently it’s a simple button with no persistence or attribution.

### High-level Task Breakdown — Phase 6.2 Visual Alerts
1) Backend: Review Persistence
- Add `staff_viewed_at` to `Job.to_dict()` so clients can render persisted review state.
- Implement `POST /api/v1/jobs/<job_id>/review`:
  - Auth required; body: `{ reviewed: boolean, staff_name: string }`.
  - Validate job exists and is in `UPLOADED` status; validate `staff_name` is active.
  - If `reviewed === true`: set `staff_viewed_at = now()`, `last_updated_by = staff_name`; log `JobReviewed`.
  - If `reviewed === false`: set `staff_viewed_at = null`, `last_updated_by = staff_name`; log `JobReviewCleared`.
  - Return updated job JSON.

2) Frontend: Modal + Visibility Rules
- Only render NEW badge + glow when `currentStatus === 'UPLOADED' && !job.staff_viewed_at`.
- Replace inline action with a modal: title “Mark as Reviewed”, body ask confirmation (“Have you reviewed this job?”) and include required Staff Attribution select (from `/api/v1/staff`).
- On confirm, call `POST /api/v1/jobs/:id/review` with Authorization and selected `staff_name` and the correct `reviewed` boolean; update local state with returned job; close modal.
- Ensure indicator never shows on non-Uploaded tabs.
 - Add a companion action in Uploaded when already reviewed: “Reapply NEW indicator”/“Mark as Unreviewed.”

3) Tests
- Backend: unit tests for review endpoint happy path, invalid status, invalid staff, event assertions.
- Frontend: component tests verifying visibility rule, modal validation (disabled confirm until staff selected), and that indicator remains cleared after a refetch.

### Acceptance Checklist (Phase 6.2)
- NEW indicator and glow appear only on `Uploaded` jobs that are unreviewed.
- “Mark as Reviewed” opens a confirmation modal with staff attribution; upon confirm, indicator disappears and stays gone across refreshes.
- Ability to reapply indicator on Uploaded jobs (“Mark as Unreviewed”) and it persists across refresh.
- Backend persists `staff_viewed_at` changes and logs `JobReviewed`/`JobReviewCleared` events with attribution.
- Tests added and passing.

## Executor's Feedback or Assistance Requests

- Phase 5.1.1 backend approve endpoint extended per plan; cost calculation and staff attribution added. Tests: green locally.
- Please verify manually if desired: approve call now requires JSON body `{ staff_name, weight_g, time_hours }` with valid Authorization header.
- If verification is OK, I will proceed to Phase 5.1.2 (Frontend Approval Modal UI).

## Lessons

- Read the file before editing to safely remove imports/usages without breaking the build.

## Phase 4.1: Email Service Integration (Current Focus)

**Goal**: Implement reliable email notifications for job confirmations and status updates  
**Estimated Time**: 60 minutes  
**Priority**: HIGH - Completed

### Detailed Sub-Tasks:

1. **Configure Flask-Mail Setup (done)**
   - Add Flask-Mail to requirements.txt
   - Configure SMTP settings in app configuration
   - Set up environment variables for email credentials
   - Initialize Mail instance in app factory

2. **Create Email Templates (done)**
   - Design `submission_confirmation.html` template
   - Design `status_update.html` template  
   - Include professional styling and branding
   - Add responsive email design

3. **Implement EmailService Class (done)**
   - Create `backend/app/services/email_service.py`
   - Methods: `send_confirmation_email()`, `send_status_update()`
   - Template rendering with job data
   - Error handling for SMTP failures

4. **Add Background Task Processing (deferred)**
   - Configure Celery with Redis broker
   - Create email task functions
   - Add retry logic for failed sends
   - Implement proper logging

**Success Criteria**: 
- Approval email sent with token link; student can confirm via `/confirm/[token]`
- Staff can trigger approval; events logged; tests green

## Key Challenges and Analysis — Phase 5.1 Approval Modal

- Backend `POST /api/v1/jobs/<id>/approve` is minimal: sets `PENDING`, sends email; lacks staff attribution, weight/time, and cost calculation; event creation partially inconsistent.
- No `candidate-files` endpoint exists; to keep scope tight, we will defer advanced file selection to Phase 4.2 and add a small stub as optional.
- Frontend has no modal; `JobList` currently posts directly to approve; we’ll replace with a modal workflow and validation.
- Cost rules: Filament $0.10/g, Resin $0.20/g, $3.00 minimum. Material source is job data; server must be source-of-truth for final cost.

## High-level Task Breakdown — Phase 5.1 Approval Modal

1) Backend: Extend Approve Endpoint (Phase 5.1.1)
- Inputs: `{ staff_name: string, weight_g: number > 0, time_hours: number > 0 }`
- Server: validate `staff_name` is active staff; compute `cost_usd` using job material; enforce $3 minimum; set `status='PENDING'`, update `weight_g`, `time_hours`, `cost_usd`; generate confirmation token; send email; log events with `triggered_by=staff_name` and `workstation_id`.
- Response: updated job JSON.
- Success: unit tests cover validation, cost calc, event logging, and email call path.

2) Frontend: Approval Modal UI (Phase 5.1.2)
- Fields: Staff Attribution (required select from `/api/v1/staff`), Weight (g), Time (hours, step 0.5), Read-only Cost preview.
- Validation: Required fields, positive numbers, disabled submit until valid; accessible labels and focus management.
- UX: Open from `Approve` button on `UPLOADED` cards; cancel closes without side effects.

3) Wiring Modal -> API (Phase 5.1.3)
- Flow: Open modal, submit posts to `/api/v1/jobs/:id/approve` with Authorization; on 200, remove job from current list and show toast; on error, show error message and keep modal open.

4) Tests (Phase 5.1.4)
- Backend: New tests for payload schema, staff validation, cost minimum, event fields (`triggered_by`, `workstation_id`).
- Frontend: Component test ensuring validation disables submit until valid, and submits expected payload.

5) Optional: Candidate Files (Phase 5.1.5)
- Minimal stub endpoint returning current uploaded filename to keep UI consistent; advanced file scanning deferred to Phase 4.2.

### Acceptance Checklist (Phase 5.1)
- Approve modal appears and validates inputs; staff list loads; cost preview correct for filament/resin with minimum enforced.
- Backend computes and persists `weight_g`, `time_hours`, `cost_usd`, sets `PENDING`, sends email, and logs events with staff attribution.
- After success, job disappears from `UPLOADED` list; no console errors; tests pass.

## Next Steps Priority Queue

### Immediate (This Session):
1. **Phase 5.3: Frontend Status Change Modals** 🔥 CRITICAL for staff workflow
2. **Phase 6: Auto-refresh + Last Updated** ⚡ HIGH

### Short-term (Next Session):  
3. **Phase 4.2: File Management System** (candidate-files full scan)
4. **Phase 4.3: Payment & Pickup modal** (grams/txn/picked_up_by)

### Medium-term:
5. **Analytics Dashboard** (`/analytics`) overview + trends
6. **Protocol Handler** (SlicerOpener) packaging

## Technical Architecture Status

**Backend (Flask)**: ✅ Fully operational
- Authentication system with JWT tokens
- Complete job lifecycle API
- Database models and migrations
- Event logging and audit trails

**Frontend (Next.js)**: ✅ Professional V0 design
- Student submission form with validation
- Staff dashboard with responsive grid layout
- Professional error handling and loading states
- Consistent design system across all pages

**Database (PostgreSQL)**: ✅ Configured and seeded
- Job, Staff, Event, Payment models
- Database migrations working
- Test data available

**Docker Environment**: ✅ Operational
- All containers running correctly
- Development environment stable
- Hot reloading working

## Lessons Learned

- **V0 Design Integration**: Applying professional design systems dramatically improves perceived quality
- **Student Access Control**: Never provide dashboard links to student-facing pages
- **API Proxy Configuration**: Next.js rewrites essential for frontend-backend communication  
- **Progressive Enhancement**: Build functional features first, then enhance with professional styling
- **Focus on Core Workflows**: Prioritize job submission → approval → completion flow above advanced features
- **Authentication Headers**: Always include Authorization headers in ALL API calls, including count fetches for tab badges

## Risk Assessment: LOW

**Why Low Risk**:
- Core functionality proven and working
- Professional UI complete and tested
- Clear separation between student and staff interfaces
- Well-defined API contracts
- Docker environment ensures consistency

**Current Blockers**: None identified

**Recommendation**: Proceed with Phase 4.1 (Email Service Integration) to complete the core user experience workflow.


The repo structure aligns well with the plan. A few planned pieces aren’t in the tree yet and should be added.
What matches the plan
Backend layout: backend/app/{models,routes,services,utils} with analytics.py, auth.py, jobs.py, payment.py, staff.py, submit.py; migrations present.
Frontend layout: frontend/src/app/{dashboard,submit,login,confirm} pages, shared components, types, and config files.
Storage: Status folders (Uploaded/, Pending/, ReadyToPrint/, Printing/, Completed/, PaidPickedUp/, Archived/) exist.
Docker: docker-compose.yml is present.
Tests: API tests exist under tests/.
Gaps vs the plan
Analytics UI: Planned /analytics page and analytics components aren’t in frontend/src/app/analytics yet.
Admin UI: No admin section/page yet (staff management, overrides, archival, health/audit, sound config).
Protocol handler: No SlicerOpener/ folder yet.
Background worker: Plan calls for RQ worker + Redis; ensure both are defined in docker-compose.yml and wired in the backend.
Email queueing: email_service.py exists (untracked), but full async flow and templates aren’t confirmed here.
Recommended next steps
Add frontend/src/app/analytics/page.tsx and frontend/src/components/analytics/*, wired to /analytics/* and /stats*.
Add an Admin section (initially under dashboard) with settings (background sound), staff management, overrides, archival, and system health (mapping to existing admin endpoints).
Add SlicerOpener/ with the handler and installer assets, per the plan.
Verify docker-compose.yml includes redis and worker services, and the backend enqueues tasks accordingly.
Everything is organized correctly overall; implement the missing Analytics and Admin pages, protocol handler, and worker/Redis to complete parity with the plan.