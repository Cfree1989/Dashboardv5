# 3D Print Management System - Build Plan

## Background and Motivation

Building a complete 3D Print Management System for academic/makerspace environments.

### Current Protocol Handler Issue Analysis

The protocol handler system for opening 3D model files directly from the dashboard is experiencing cross-browser compatibility and registration issues:

**Implemented Components:**
- ✅ SlicerOpener.exe with robust path validation, multi-slicer support, GUI feedback, and logging
- ✅ Frontend multi-strategy protocol invocation (anchor + window.open + iframe fallback)
- ✅ Backend event logging endpoint `/log-file-open`
- ✅ Configuration system with security validation and drive mapping support

**Current Issues:**
1. **500 Error on Logging**: The `/log-file-open` endpoint is returning 500 errors, blocking audit trail creation
2. **Protocol Mismatch**: Frontend uses `print3d://` but register.bat only registers `3dprint://`
3. **Cross-Tab Inconsistency**: Protocol invocation works in "Uploaded" tab but fails in other status tabs
4. **Browser/Extension Interference**: Some browsers or extensions (like Yoroi) may intercept custom protocols

**Working Elements:**
- SlicerOpener.exe correctly processes URLs when the browser actually invokes the protocol
- Path validation and slicer detection work reliably 
- GUI feedback and logging systems function as designed
- Copy-to-clipboard fallback provides reliable file access

**Root Cause Hypothesis:**
The issue appears to be at the browser-to-OS handoff layer rather than the protocol handler itself. The frontend generates correct URLs, but browser behavior varies between tabs due to SPA routing context, user gesture capture, or security policy differences.

**Immediate Investigation Steps (for Executor):**
1. **Debug 500 Error**: Check browser DevTools Network tab for `/log-file-open` response body to identify specific backend error
2. **Protocol Registration Gap**: Verify which protocol scheme is actually registered by checking Windows registry entries
3. **Path Format Differences**: Use "Copy File Path" on failing tabs vs working tabs to compare absolute/relative path formats
4. **Browser Clean Test**: Test in Incognito/Private mode with extensions disabled to eliminate interference
5. **Manual Protocol Test**: Test `print3d://open/?path=C:\\Dashboardv5\\storage\\ReadyToPrint\\...` directly in address bar

**Quick Wins to Implement First:**
1. **Add Debug Anchor**: Place real `<a href="print3d://...">Open (Debug)</a>` link next to existing button on failing tabs
2. **SPA Router Bypass**: Modify click handler to use `e.preventDefault()` + `window.location.assign()` instead of programmatic elements  
3. **Enhanced Launch Sequence**: Replace parallel strategy with sequential (anchor → setTimeout → window.open) approach
4. **Browser Extension Detection**: Add `window.chrome?.runtime` logging to identify extension interference

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
- Current Phase: Phase 5 — UI Workflows
- Next Milestone: Phase 5.4 — Notes Editing + "Open File" Button
- Overall Progress: ~65%

### Active Workstreams (Open)

1) **Protocol Handler Cross-Tab Debugging (PRIORITY)** — Fix inconsistent "Open File" behavior
- [ ] 2.1 Fix `/log-file-open` 500 error (backend debugging)
- [ ] 2.2 Register print3d:// protocol (update register.bat)
- [ ] 2.3 Cross-tab protocol invocation improvements (browser compatibility)
- [ ] 3.1 Add "Open (Debug)" link option (debugging tool)
- [ ] 3.2 Frontend protocol invocation logging (diagnostics)
- Target: Reliable protocol launching from all job status tabs with complete audit trail

2) File Tracking & Metadata
- [x] Metadata durability: keep DB `job.file_path` and `metadata.json.authoritative_filename` in sync across transitions; add tests
- [x] Audit report endpoint: flags missing authoritative file, duplicate/stale siblings, directory/status mismatches
- [x] Admin UI: Audit report view + safe actions (delete orphan, delete stale, mark reviewed) with events
- [x] FS tests: transition path updates on disk + `metadata.json` sync using temp storage

3) Incident — Missing Jobs After Reboot (triage + prevention)
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
- [x] Frontend: Payment modal integration on `COMPLETED` cards
  - [x] Tests: update `frontend/src/components/dashboard/modals/payment-modal.test.tsx` (validation + submit + failure alert)
  - [x] Tests: extend `frontend/src/components/dashboard/job-list.test.tsx` (button visible, submit → API call, list removal + counts refresh, error keeps modal open)
  - [x] UI: “Mark Paid/Picked Up” button wired in `job-card.tsx` → opens `PaymentModal`
  - [x] Hook `payment-modal.tsx` submit → `POST /api/v1/jobs/:id/payment`
  - [x] Success: close modal, remove from list, trigger counts refresh
  - [x] Error handling: inline alert in modal; retain context for retry
  - [x] A11y: labels and disabled states ensured
- Acceptance: End-to-end payment recorded; job moves to Paid & Picked Up; events/audit present; tests pass

4) Notes Editing & Open File Button (New Active)
- Notes Editing — Append-style with inline attribution
  - Goal: When a staff member adds a note, automatically prefix it with their name (e.g., "Conrad Freeman - Model needs to be split"). Preserve history by appending to the existing `job.notes` text with newline separation.
  - Backend
    - [x] New endpoint: `POST /api/v1/jobs/<id>/notes` with `{ text: string, staff_name }`
      - Appends a single line to `job.notes` as: `<staff_name> - <text>` with a timestamp kept only in the `NoteAdded` event (avoid duplicating in text)
      - Enforce per-entry limit (e.g., 1000 chars) and total notes length limit (e.g., 5000 chars)
      - Validate active staff; on success, return updated job object
      - Log `NoteAdded` event with `{ text_len, staff_name }`
    - [ ] Keep existing `PATCH /jobs/<id>/notes` for full-replace (legacy); new UI will use POST append only
    - [x] Tests: success append, per-entry len guard, total len guard, event content, inactive staff
  - Frontend
    - [x] Replace inline full-editor with an "Add note" composer (single-line or textarea) + staff attribution dropdown
    - [x] On submit: POST `/api/v1/jobs/<id>/notes`; on success, prepend/append rendered note line without a page reload
    - [x] Render existing notes as a list split by newlines; newest first
    - [x] A11y: labels, aria-live for status, keyboard submit, disabled while sending
    - [x] Error states: inline banner with retry; character counter (per-entry)
    - [x] Visible "Has notes" indicator on `JobCard` without expanding
      - UI: Show FileText icon with tooltip "Has notes" whenever `job.notes` is non-empty; on md+ also show small label "Has notes"; icon-only on small screens
      - Placement: Under the printer line within the card details; high-contrast color; aria-label for screen readers
      - Live update: After adding a note, indicator appears immediately without refresh
      - Enhancement: Indicator is clickable for quick edit (expands and focuses composer); icon/label sizing aligned with card metadata
  - Acceptance: Adding a note results in an appended line prefixed with the staff name; history preserved; event logged; tests pass (API + UI).
- "Open File" Button (Protocol handler deferred; provide graceful fallback)
  - [x] Backend: `POST /api/v1/jobs/<id>/log-file-open` (no staff attribution)
  - [x] Frontend: Add "Open File" to job cards for all statuses
    - [x] Modal (no staff field): primary open via `3dprint://open?path=<urlencoded job.file_path>`
    - [x] Secondary: "Copy File Path" action (clipboard) + inline feedback
    - [x] On confirm: POST log event, then proceed
  - [x] Fallback: Helper text if protocol not installed
  - [x] Toasts: Success toasts wired for copy path, approval, rejection, status changes (Printing/Complete/Paid&Picked Up have explicit messages), review/unreview, and payment
    - [x] A11y: focus management, keyboard activation; pauses auto-refresh while open
  - Acceptance: Clicking "Open File" logs the event and either opens via protocol (if installed) or allows copying path. Automated UI tests added and passing.
  - [x] Polish: Replace blocking `alert()` with a non-blocking toast for "Copy File Path" success
    - Plan A (simplest): Local inline toast inside the Open File modal
      - Show a small success pill (e.g., "Copied to clipboard") in the bottom-right of the modal
      - Auto-hide after 2 seconds; does not block interaction
      - No global provider, minimal code change, easy to test
    - Plan B (nice to have, later): Lightweight global toast provider shared across app
      - Add `ToastProvider` to `app/layout.tsx` and `useToast()` hook
      - Reuse for future success/error messages
    - Tests: Simulate click → assert success pill appears then disappears (use fake timers)
    - Acceptance: Copy action shows non-blocking confirmation with no browser alert dialogs

4) Protocol Handler Cross-Tab Debugging & Fixes
- [x] Build SlicerOpener with logging; integrate open/save awareness events; Approve modal already has rescan UX
    - [x] Step 1 — Repo scaffold and installer (Complete)
      - [x] Add `SlicerOpener/SlicerOpener.py` with: config-driven paths+slicer mapping, robust path validation, GUI success/error, rotating file logging, multi-slicer chooser
      - [x] Add `SlicerOpener/config.example.ini`
      - [x] Add `SlicerOpener/register.bat` (admin) to write Windows registry keys for `3dprint://`
      - [x] Add `SlicerOpener/README.md` with build (PyInstaller) and workstation setup instructions
      - Success criteria: Files exist; code builds with PyInstaller; README covers install and troubleshooting
    - [ ] Step 2 — Critical Bug Fixes (Executor Priority)
      - [ ] 2.1 Fix `/log-file-open` 500 error
        - Issue: Backend endpoint may have token/DB issue causing 500 responses
        - Root cause: Check Event model fields, DB connection, authentication middleware
        - Test: Send manual POST to endpoint with valid token and verify response
        - Success: Endpoint returns 200 with event logged correctly
      - [ ] 2.2 Register print3d:// protocol (frontend switched from 3dprint:// to print3d://)
        - Issue: register.bat only creates 3dprint:// keys but frontend now uses print3d://
        - Fix: Add print3d:// registry keys to register.bat or create separate print3d-register.bat
        - Test: Manual protocol link test in address bar: print3d://open/?path=C:\\path\\to\\file.stl
        - Success: Protocol handler launches and processes print3d:// URLs
      - [ ] 2.3 Cross-tab protocol invocation improvements
        - Issue: Protocol works in "Uploaded" tab but fails in other tabs ("Pending", "ReadyToPrint", etc.)
        - Investigation needed: 
          * Test in clean browser profile/incognito with extensions disabled
          * Compare file paths returned by "Copy File Path" across different tabs
          * Check if SPA routing or page-specific JavaScript is interfering
        - Fix approaches:
          * Add real anchor element rendering option as debug tool
          * Implement tab-specific launch strategy detection
          * Add client-side protocol invocation logging for debugging
        - **Technical Strategy**: Since the issue appears browser-specific rather than handler-specific, focus on frontend robustness:
          * **SPA Router Bypass**: Use `e.preventDefault()` + `e.stopPropagation()` + `window.location.assign()` to prevent Next.js interception
          * **Sequential Launch Strategy**: Replace parallel approach with timed sequence (anchor click → setTimeout → window.open fallback)
          * **User Gesture Preservation**: Ensure clean event propagation and attach only to real button clicks
          * **Protocol Detection**: Implement iframe-based protocol support testing with timeout fallback
          * **Enhanced Logging**: Add browser/extension detection and timing diagnostics
        - Success: Protocol launches consistently from all job status tabs
    - [ ] Step 3 — Enhanced Debugging Tools (Executor)
      - [ ] 3.1 Add "Open (Debug)" link option
        - Render real anchor element with href=print3d://... for comparison testing
        - **Implementation**: `<a href="print3d://..." style="margin-left: 10px">Open (Debug)</a>` alongside existing button
        - Toggle-able via admin setting or always-present during development
        - Success: Debug anchor bypasses SPA interference and provides reference behavior
      - [ ] 3.2 Frontend protocol invocation logging
        - Log attempted href, browser errors, and success/failure states
        - Display invocation attempt details in browser console for troubleshooting
        - Success: Clear visibility into what happens during protocol launch attempts
      - [ ] 3.3 Path validation debugging
        - Show exact file_path value and URI construction in UI
        - Validate absolute vs relative path handling across job statuses
        - Success: Clear indication of path format differences that may affect browser behavior
    - [ ] Step 4 — Build + smoke-test on Windows (Executor)
      - [ ] Build one-file exe via PyInstaller; verify GUI dialogs, selection UI, and logging
      - [ ] Manual test from dashboard: click Open File → opens slicer (fallback works if protocol not installed)
      - [ ] Test both 3dprint:// and print3d:// protocol schemes
      - Success criteria: Slicer launches with sample files; logs contain validation entries; both protocols work
    - [ ] Step 5 — Packaging (Planner/Executor)
      - [ ] Provide signed zip with `SlicerOpener.exe`, `config.ini` template, and updated `register.bat`
      - [ ] Include registration for both protocol schemes
      - [ ] Optional: add `.reg` alternative; icon polish
      - Success criteria: Single zip usable by staff; minimal steps
    - [ ] Step 6 — Backend/Frontend touchups (Planner/Executor)
      - [ ] Confirm event type name alignment (`FileOpenedInSlicer`) and error-toasts consistency
      - [ ] Short in-app setup guide link for staff (admin-only)
      - [ ] Remove debug tools once protocol launches consistently
      - Success criteria: Clear UX; consistent events; clean production code

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

### Project Status Board — Active Items
- [x] Phase 4.3 — Payment & Pickup (Frontend Integration)
  - [x] Tests first: `payment-modal.test.tsx`, `job-list.test.tsx`
  - [x] Wire “Record Payment” button in `job-card.tsx` for `COMPLETED`
  - [x] Submit flow to `/api/v1/jobs/:id/payment` with attribution
  - [x] Success: close modal, remove card, refresh counts/last-updated
  - [x] Errors: show helpful inline alerts
  - [x] A11y + loading/disabled states
- [x] Phase 5.4 — Notes Editing
  - [x] Backend: `POST /api/v1/jobs/<id>/notes` append-only; log `NoteAdded`; per-entry + total limits; tests
  - [x] Frontend: Replace full-editor with "Add note" composer; render list with name prefix; a11y
  - [x] Frontend: Visible "Has notes" indicator on job cards (icon/label, tooltip, aria-label, auto-updates)
  - [x] Tests: API (append validations) and UI (add note flow, errors, indicator presence/absence and live update)
- [x] Add "Open File" Button (protocol handler later)
  - [x] Frontend modal (no staff attribution); primary open via protocol; fallback copy path; POST `/log-file-open`
  - [x] Tests: UI behavior + event POST

- [x] UI Polish: Prevent action buttons from overlapping/stacking poorly on job cards
  - Change: In `frontend/src/components/dashboard/job-card.tsx`, updated the action bar to `flex-wrap` with `gap-2` and `ml-auto`, replacing `space-x-2`. Added `whitespace-nowrap` per button and hid long labels on small screens (`hidden sm:inline`).
  - Success criteria: Buttons wrap to a new line within the card without overlapping neighboring cards; layout remains right-aligned; small screens show icon-only labels.

- [x] Archival retention adjustment
  - [x] Docs: Update archival retention from 90 to 45 days in `/.cursor/masterplan.md`
    - [x] Section 3.4.2 — Archived: parenthetical example now 45 days
    - [x] Section 5.7 — Data Retention: Retention Period and Archival Process now 45 days
    - [x] API Spec — `POST /admin/archive`: default `retention_days` now 45
  - Impact: Documentation and implementation aligned; tests updated and passing

- [x] Align implementation defaults with 45-day policy
  - [x] Backend: Ensure `/api/v1/admin/archive` default `retention_days` is 45 when omitted
  - [x] Admin UI: Default value in Data Management forms set to 45
  - [x] Tests: Add/adjust tests to verify defaulting behavior and display values
  - Success: API returns expected behavior with omitted param; UI shows 45 by default; tests pass

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
 - [x] Admin System Health UI: Wired to `GET /api/v1/admin/audit/report`, orphan cleanup, stale file deletion, and "mark reviewed" actions

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
  - [x] Admin UI (report view + safe actions)
  - Acceptance: Audit flags inconsistencies; safe actions available; events logged (Met)
- 4.3 Payment & Pickup
  - Backend
    - [x] `POST /api/v1/jobs/:id/payment` with `{ grams, txn_no, picked_up_by, staff_name }`; validate status `COMPLETED`
    - [x] Persist `Payment` record; transition to `PAIDPICKEDUP`; log attributed events; unit tests
  - Frontend
    - [x] Payment modal on `COMPLETED` cards; inputs + validation; success removes job and refreshes counts; error states; a11y
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

### Immediate Priority (Executor Tasks)
1) **Protocol Handler Debug & Fix** — Critical for staff workflow efficiency
   - Fix `/log-file-open` 500 error (likely authentication or database issue)
   - Update register.bat to include print3d:// protocol registration
   - Add debugging tools to identify browser-specific protocol invocation issues
   - Test cross-tab consistency and implement workarounds for SPA interference
   - Target: Reliable "Open File" functionality from all dashboard tabs

### Medium Priority (Post-Protocol Fix)
2) **Missing Jobs Incident Resolution** — System stability
   - Verify database connection and prevent SQLite fallback
   - Add backend diagnostics and runbook documentation
3) **Admin Overrides Implementation** — Complete existing scaffolded UI
   - Wire backend endpoints with proper guardrails and audit trails
4) **E2E Testing & Deployment Documentation** — Production readiness
   - Write comprehensive end-to-end tests for full workflow
   - Document production deployment procedures

### Future Priority
5) **Analytics Dashboard** — Operational insights after core stability achieved


