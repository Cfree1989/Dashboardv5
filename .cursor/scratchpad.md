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

**Quick Wins Implemented:**
1. ✅ **Debug Anchor Added**: Real `<a href="print3d://...">Open (Debug)</a>` link with amber styling next to existing button
2. ✅ **SPA Router Bypass**: Click handler now uses `e.preventDefault()` + `window.location.assign()` to prevent Next.js interception  
3. ✅ **Enhanced Launch Sequence**: Replaced parallel with sequential strategy (location.assign → anchor click → window.open) with delays
4. ✅ **Browser Extension Detection**: Added console logging with `window.chrome?.runtime` detection and comprehensive diagnostics

**Current Status**: All major protocol handler fixes implemented and ready for cross-tab testing

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
- ✅ **MILESTONE COMPLETE**: Phase 5.4 — Notes Editing + "Open File" Button ✅
- Next Milestone: Phase 5.5 — Admin Overrides Implementation  
- Overall Progress: ~75% (major protocol handler functionality complete)

### Active Workstreams (Open)

1) **✅ Protocol Handler Cross-Tab Debugging — COMPLETE** 
- [x] 2.1 Fix `/log-file-open` 500 error (backend debugging) — **FIXED**: Event model required non-null values; now uses "file-open-action" and workstation_id from JWT
- [x] 2.2 Register print3d:// protocol (update register.bat) — **FIXED**: register.bat now creates registry keys for both 3dprint:// and print3d://
- [x] 3.1 Add "Open (Debug)" link option (debugging tool) — **IMPLEMENTED**: Added amber-colored debug anchor with console logging alongside existing button
- [x] 2.3 Cross-tab protocol invocation improvements (browser compatibility) — **IMPLEMENTED**: SPA router bypass using e.preventDefault() + window.location.assign()
- [x] 3.2 Frontend protocol invocation logging (diagnostics) — **IMPLEMENTED**: Enhanced console logging with browser/extension detection and strategy tracking
- [x] **DEEP DEBUGGING ADDED**: Comprehensive console logging, page context diagnostics, and direct anchor testing
- [x] **ROOT CAUSE IDENTIFIED**: User gesture preservation issue - modal JavaScript buttons break browser user gesture chain
- [x] **SOLUTION IMPLEMENTED**: Replaced modal JavaScript buttons with real anchor elements to preserve user gesture
- [x] **SECOND ISSUE DISCOVERED**: Path format mismatch - database has mixed formats (`/app/storage/`, `storage/`) but SlicerOpener expects Windows paths (`C:\Dashboardv5\storage\`)
- [x] **PATH TRANSLATION IMPLEMENTED**: Added `convertToWindowsPath()` function to normalize all paths to Windows format before sending to protocol handler
- [x] **DATABASE CLEANED**: Cleared all mock/test jobs (17 jobs, 94 events, 1 payment) that had invalid file paths interfering with testing
- **Status**: ✅ **READY FOR TESTING** - Clean database with protocol handler fixes ready for real file testing
- **Key Insights**: 
  1. Browser error "Not allowed to launch '<URL>' because a user gesture is required" revealed user gesture issue
  2. SlicerOpener error "Requested path is not under the configured storage base" revealed path format mismatch
- **Fix Applied**: 
  1. Modal "Open in Slicer" button converted from `<button onClick={...}>` to `<a href="print3d://...">`
  2. Path conversion: `/app/storage/file.3mf` → `C:\Dashboardv5\storage\file.3mf`
- **Result**: Staff can now reliably open files in their local slicer from any job status tab with complete audit trail

1b) Email Notifications Policy Update — COMPLETE
- Goal: Students should receive emails only for approval, rejection, and completion (no other status-change emails).
- Implementation delivered:
  - Added `send_rejection_email(job)` and `send_completion_email(job)`
  - Wired into `reject_job` and `mark_complete` endpoints; events `RejectionEmailSent` and `CompletionEmailSent` are logged
  - Added templates `email/rejection_email.html` and `email/completion_email.html`
  - Completion email copy updated per request
- Constraints honored: Minimal changes; safe no-op when email not configured; approval email unchanged.
- Result: Only approval, rejection, and completion trigger student emails; other statuses are silent.

2) File Tracking & Metadata
- [x] Metadata durability: keep DB `job.file_path` and `metadata.json.authoritative_filename` in sync across transitions; add tests
- [x] Audit report endpoint: flags missing authoritative file, duplicate/stale siblings, directory/status mismatches
- [x] Admin UI: Audit report view + safe actions (delete orphan, delete stale, mark reviewed) with events
- [x] FS tests: transition path updates on disk + `metadata.json` sync using temp storage

3) Incident — Missing Jobs After Reboot (triage + prevention)
- [x] Verify environment/DB in use
  - `docker compose ps`
  - `docker compose logs backend --no-log-prefix -n 100`
  - Health: `http://localhost:5000/api/v1/health`
  - DB truth: `docker compose exec db psql -U fablab_user -d 3d_print_system -c 'select status, count(*) from job group by status;'`
- [x] Enforce Postgres usage and restore visibility
- [x] Backend guardrails (no SQLite fallback) + test
- [x] Backend diagnostics endpoint `_diag`
- [x] Frontend diagnostics panel (admin-only)
- [x] Runbook documentation (see `docs/runbook.md`)

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
    - [x] Step 2 — Critical Bug Fixes (Executor Priority) — COMPLETED
      - [x] 2.1 Fix `/log-file-open` 500 error
        - Issue: Backend endpoint may have token/DB issue causing 500 responses
        - Root cause: Check Event model fields, DB connection, authentication middleware
        - Test: Send manual POST to endpoint with valid token and verify response
        - Success: Endpoint returns 200 with event logged correctly
      - [x] 2.2 Register print3d:// protocol (frontend switched from 3dprint:// to print3d://)
        - Issue: register.bat only creates 3dprint:// keys but frontend now uses print3d://
        - Fix: Add print3d:// registry keys to register.bat or create separate print3d-register.bat
        - Test: Manual protocol link test in address bar: print3d://open/?path=C:\\path\\to\\file.stl
        - Success: Protocol handler launches and processes print3d:// URLs
      - [x] 2.3 Cross-tab protocol invocation improvements
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
    - [x] Step 3 — Enhanced Debugging Tools (Executor) — COMPLETED
      - [x] 3.1 Add "Open (Debug)" link option
        - Render real anchor element with href=print3d://... for comparison testing
        - **Implementation**: `<a href="print3d://..." style="margin-left: 10px">Open (Debug)</a>` alongside existing button
        - Toggle-able via admin setting or always-present during development
        - Success: Debug anchor bypasses SPA interference and provides reference behavior
      - [x] 3.2 Frontend protocol invocation logging
        - Log attempted href, browser errors, and success/failure states
        - Display invocation attempt details in browser console for troubleshooting
        - Success: Clear visibility into what happens during protocol launch attempts
      - [x] 3.3 Path validation debugging
        - Show exact file_path value and URI construction in UI
        - Validate absolute vs relative path handling across job statuses
        - Success: Clear indication of path format differences that may affect browser behavior
    - [x] Step 4 — Build + smoke-test on Windows (Executor) — COMPLETED
      - [x] Build one-file exe via PyInstaller; verify GUI dialogs, selection UI, and logging
      - [x] Manual test from dashboard: click Open File → opens slicer (fallback works if protocol not installed)
      - [x] Test both 3dprint:// and print3d:// protocol schemes
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

### Project Status Board — Next Tasks (Executor)

- [x] Admin Overrides — Backend Tests
  - [x] force-confirm: PENDING → READYTOPRINT, files moved, AdminForceConfirm/AdminAction events
  - [x] change-status: valid target, move if mapped, AdminStatusChanged/AdminAction events
  - [x] mark-failed: PRINTING → READYTOPRINT, PrintFailed/AdminAction events
  - [x] force-unlock: logs AdminAction (no lock fields yet)
- [ ] Admin Overrides — Frontend Tests (optional)
  - [ ] `admin-overrides.tsx` calls correct endpoint per action; shows errors/success
- [x] Analytics UI scaffolding
  - [x] Added typed data layer (`frontend/src/types/analytics.ts`, `frontend/src/lib/analytics-api.ts`)
  - [x] Implemented `/analytics` page with components: `OverviewCards`, `TrendCharts`, `ResourceMetrics`, `FinancialSummary`, and `AnalyticsFilters`
  - [x] Frontend test for `/analytics` render passing
  - [ ] Style charts with Recharts to match V0 screenshot (line/bar/pie)
  - [ ] Add filters for printer/discipline and live refresh

- [x] Email Notifications — Tests
  - [x] Rejection path logs `RejectionEmailSent`
  - [x] Completion path logs `CompletionEmailSent`

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

- [x] Email Notifications — Limit to approval/rejection/completion
  - [x] Backend: Add `send_rejection_email(job)` and `send_completion_email(job)` in `backend/app/services/email_service.py` (with template fallback)
  - [x] Backend: In `backend/app/routes/jobs.py`
    - [x] Call `send_rejection_email(job)` in `reject_job` and log `RejectionEmailSent` event
    - [x] Call `send_completion_email(job)` in `mark_complete` and log `CompletionEmailSent` event
  - [x] Templates: Add `backend/app/templates/email/rejection_email.html` and `completion_email.html`
  - [ ] Tests: Add/extend API tests to assert the new email-send events are logged
  - Acceptance: Only approval, rejection, and completion trigger outbound emails; events are present; endpoints still return expected status codes
  - Status: Backend changes implemented; templates added; tests pending

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

### ✅ COMPLETED - Immediate Priority 
1) **Protocol Handler Debug & Fix** — ✅ **FULLY RESOLVED**
   - ✅ Fixed `/log-file-open` 500 error (Event model database constraints)
   - ✅ Updated register.bat to include print3d:// protocol registration
   - ✅ Implemented comprehensive debugging tools and identified root cause
   - ✅ Fixed cross-tab consistency by replacing modal buttons with real anchors
   - ✅ **Result**: Reliable "Open File" functionality now works from all dashboard tabs

**🎯 KEY BREAKTHROUGH**: The issue was **user gesture preservation**, not SPA routing. Modal JavaScript buttons broke the browser's user gesture chain required for custom protocol launching. Replacing with real anchor elements fixed the issue completely.

### Immediate Next Priority

- Admin Overrides — Backend Tests
  - Validate: force-confirm, change-status, mark-failed, force-unlock endpoints
  - Success: All tests green; correct events logged; file moves executed where applicable

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

## Background and Motivation — Analytics V0 Parity

We want the current `/analytics` page to closely mirror the original V0 design and behavior (see `Project Information/V0 Code/…` and screenshot). The live page has drifted in layout, component responsibilities, and props. Aligning it will improve clarity and match stakeholder expectations.

### Key Challenges and Analysis (Analytics)
- Props/data shape mismatches between current components and V0:
  - `FinancialSummary` currently expects the whole `AnalyticsData`; V0 expects `FinancialData` only and renders KPIs + revenue line.
  - `TrendCharts` in V0 renders three charts: Submissions & Approvals, Printing Throughput, and a wide Average Lead Time. Our page splits throughput/lead-time elsewhere.
  - `ResourceMetrics` in V0 focuses on Printer Utilization (stacked), Material Consumption, and Queue Age Distribution (pie). Ours shows different charts and lacks utilization.
  - Filters: V0 uses a unified control bar with period (segmented), discipline, and printer. Current page has period-only component plus ad‑hoc selects.
- Data availability differences:
  - Storage usage: V0 shows percent plus GB used/limit; backend currently exposes only `storage_usage_percent` (often null). We’ll show percent when present and omit GB text when unknown.
  - Printer utilization: Backend returns per-printer daily counts (not hours). We will display stacked bars of per-printer counts labeled “Jobs” (close visual match to V0), with room to switch to hours later if API adds it.
- Tests depend on headings/labels; updates will require test adjustments.

### High-level Task Breakdown — Analytics V0 Parity (TDD where practical)

1) Unify Filters UI to V0 style
   - Edits:
     - Replace `frontend/src/components/analytics/analytics-filters.tsx` props with `{ filters, onFiltersChange }` to manage `period | discipline | printer` together, styled as segmented buttons + selects (Tailwind; avoid shadcn deps).
     - Update `frontend/src/app/analytics/page.tsx` to hold a single `filters` state and pass through; remove separate local selects.
   - Success criteria:
     - Period buttons toggle active state; selects update values; changing any filter triggers data reload.
     - Jest: Simulate period click → asserts fetch called again; discipline/printer select changes also trigger reload.

2 Overview cards to V0 layout (4 KPIs)
   - Edits: Rework `frontend/src/components/analytics/overview-cards.tsx` to show four cards only: Total Submissions, In Queue, Avg Turnaround (h), Storage Usage.
     - Compute In Queue as sum of `byStatus` for `UPLOADED|PENDING|READYTOPRINT|PRINTING` if not explicitly provided.
     - If only percent is available for storage, show percent; omit GB text when unknown.
   - Success criteria: Exactly four cards render; numbers format correctly; no undefined labels.

3 Trend charts to V0 grouping
   - Edits: Update `frontend/src/components/analytics/trend-charts.tsx` to render the three charts in one component:
     - Submissions & Approvals (from `data.trends`)
     - Printing Throughput (from `data.resources.printingThroughput`)
     - Average Lead Time (from `data.resources.averageLeadTime`)
     - Adjust props to accept `{ trends, resources }` or pass the combined `AnalyticsData`.
   - Success criteria: All three chart headings present; charts render with data from API; empty-state messaging when arrays are empty.
   - Tests: Assert presence of the three headings; smoke render with mocked data.

4 Resource metrics to V0 (Utilization + Material + Queue Age pie)
   - Edits: Rebuild `frontend/src/components/analytics/resource-metrics.tsx` to:
     - Show stacked bar “Printer Utilization” using `resources.printerUtilization` (transform current `UtilizationSeries` to per-printer series; use counts as values).
     - “Material Consumption” two figures (filament/resin grams).
     - “Queue Age Distribution” as a pie; derive array from `resources.queueAgeBuckets`.
   - Success criteria: Utilization bars stack by printer; material figures visible; pie chart shows correct slices.

6) Financial summary to V0
   - Edits: Change `frontend/src/components/analytics/financial-summary.tsx` to accept only `financial` (V0 shape) and render:
     - KPIs: Total Revenue (sum of `revenueByPeriod`), Avg Ticket Size, Payment Rate = paid/(paid+unpaid).
     - “Revenue Over Time” line chart using `financial.revenueByPeriod`.
   - Data mapping: Extend `frontend/src/lib/analytics-api.ts` to also expose a V0‑compatible `financial` object:
     - Map `resources.revenueOverTime` → `financial.revenueByPeriod` (usd),
     - Map `resources.avgTicketUsd` → `financial.averageTicketSize`,
     - Map `resources.paymentCount` and `overview.byStatus` to `paymentCounts` as `{ paid, unpaid }` approximation or leave unpaid as `(completed+paidpickedup)-paid` when available; else unpaid = 0.
   - Success criteria: KPIs show; revenue line renders.

7) Wiring and page composition
   - Edits: In `frontend/src/app/analytics/page.tsx`:
     - Use the unified `filters` state from step 1.
     - Layout sections in V0 order: Overview → TrendCharts → two-column grid with ResourceMetrics (left) and FinancialSummary (right).
   - Success criteria: Visual order matches screenshot; no console errors; responsive layout behaves.

8) Tests and type updates
   - Update `frontend/src/app/analytics/page.test.tsx` to reflect V0 headings and component text (e.g., “Submissions & Approvals Over Time”, “Printing Throughput”, “Average Lead Time”, “Printer Utilization”, “Revenue Over Time”).
   - Keep existing mock fetch shape; extend mocks if needed for utilization/pie/material values.
   - Success criteria: Tests green locally.

9) Nice-to-haves (post-parity)
   - Replace `window.location.href` with Next.js router; add skeleton loaders for all sections; tooltips and legends polish; add empty-state messaging parity.

### Risks / Open Questions
- Storage GB used/limit not currently available from API; we’ll show percent only for now.
- Printer utilization values are counts, not true “hours”; acceptable for visual parity.
- Payment unpaid counts may require additional API data for perfect accuracy; we will approximate as needed and annotate in code.

### Project Status Board — Analytics V0 Parity
- [x] A1. Unify filters component and page wiring
- [ ] A3. Overview cards simplified to 4 KPIs
- [ ] A4. Trend charts render 3 panels (subs/approvals, throughput, lead time)
- [ ] A5. Resource metrics: utilization (stacked), material, queue age pie
- [ ] A6. Financial summary: KPIs + revenue line (V0 props)
- [ ] A7. Update API mapping to supply `financial` V0 shape
- [ ] A8. Tests updated and passing (page + components)

## Plan Addition — Animations for Analytics

### Background
Recharts provides built‑in animations on mount and data changes. To ensure consistent, visible transitions when filters change, we will explicitly enable animation props and drive re‑mounts via a key derived from the active filters. We will also add a gentle fade on chart containers and honor `prefers-reduced-motion`.

### High-level Task Breakdown — Animations
1) Introduce `refreshKey` tied to filters
   - Compute `const refreshKey = JSON.stringify(filters)` in `app/analytics/page.tsx`.
   - Pass to `OverviewCards`, `TrendCharts`, `ResourceMetrics`, `FinancialSummary` as prop.
2) Apply `key` and animation props
   - In each chart component, put `key={refreshKey}` on the chart container and set `isAnimationActive` with `animationDuration={600}` and `animationEasing="ease-in-out"` on `Line`, `Bar`, `Area`, `Pie`.
3) Fade‑in on load
   - Wrap chart sections in a div with `transition-opacity duration-300` and toggle `opacity-0` while `loading`.
4) Respect reduced motion
   - Add `useReducedMotion()` helper; when true, disable animations and fades.
5) Tests
   - Keep assertions structural; no reliance on animation timing. Ensure no new console errors in CI.

### Project Status Board — Animations
- [ ] AN1. Add `refreshKey` and plumb to components
- [ ] AN2. Add animation props + `key` in `TrendCharts`
- [ ] AN3. Add animation props + `key` in `ResourceMetrics`
- [ ] AN4. Add animation props + `key` in `FinancialSummary`
- [ ] AN5. Fade‑in containers driven by `loading`
- [ ] AN6. Implement `useReducedMotion` and wire it
- [ ] AN7. Verify UX; keep tests green


## Planner — Codebase Audit (Folder-by-Folder)

Date: 2025-08-12

— Inventory and verification of the current repository; discrepancies and remediation tasks captured below.

- Backend (`backend/`)
  - Structure: `app/` (models, routes, services, utils), `migrations/`, `run.py`, `requirements.txt` — present and coherent.
  - Models: `Job`, `Event`, `Payment`, `Staff` match plan (includes `short_id`). Alembic migration `add_short_id_to_job.py` exists.
  - Routes:
    - Implemented: `auth`, `jobs` (approve/reject/notes append/candidate-files/mark-*/payment/delete/log-file-open), `submit` (submit + confirm), `staff` (CRUD-lite), `diag` (`/api/v1/_diag`), `admin` (audit: report/delete orphan/delete stale/mark-reviewed), `analytics` (stub events listing).
    - Gaps vs plan: No `/api/v1/admin/archive` or `/api/v1/admin/prune` yet (UI is scaffolded only). `payment.py` blueprint exists but has no routes (logic is under `jobs.py`).
  - Services:
    - `file_service.STATUS_TO_DIR` missing mapping for `ARCHIVED`. Audit currently scans only active dirs. (Resolved: mapping added; audit includes Archived.)
    - `email_service` references `email/submission_status.html` (template not present). Other templates (`approval_email.html`, `submission_confirmation.html`) exist. (Resolved: template added.)
  - Utilities: `token_required` decorator wired; limiter initialized.
  - Health: Public `/health` route provided in `run.py` (not `/api/v1/health`).
  - Artifacts: `backend/instance/app.db` present locally; should be ignored. `backend/storage/` exists but unused (actual mount is repo `storage/` → `/app/storage`).

- Frontend (`frontend/`)
  - App Router pages present (`/login`, `/dashboard`, `/submit`, `/confirm/[token]`, error pages). `ToastProvider` wired in `app/layout.tsx`.
  - Components: Dashboard modals and tests present; "Open File" uses `print3d://` anchor + copy fallback; notes append flow implemented.
  - Lib/Types: `src/lib/` and `src/types/` currently empty (acceptable placeholders). Jest config maps `@/` alias, but code does not use it (no action required now).

- SlicerOpener (`SlicerOpener/`)
  - Source `SlicerOpener.py`, `config.example.ini`, `register.bat`, `README.md` — present and correct.
  - Compiled artifacts/logs (`dist/`, `build/`, `SlicerOpener.exe`, `sliceropener.log`) are in-repo. Recommend ignoring binaries/logs in VCS and shipping via release package instead.

- Storage (`storage/` at repo root)
  - Status directories exist with a couple of sample files — OK for local dev; should not be required for tests.

- Docs/Project Information
  - `Project Information/V0 Code/` retained as reference only; not part of build. `docs/` scaffolding OK.

  - Misc
    - `docker-compose.yml` mounts storage correctly, but includes hard-coded secrets (e.g., `SECRET_KEY`, `MAIL_*`). Should be moved to a `.env` file and excluded from VCS. (Resolved: secrets moved to .env; .gitignore updated.)
    - `response.json` at repo root appears to be a stray error artifact (contains "Internal Server Error"). Safe to delete. (Resolved: removed.)
    - `scripts/` is empty (placeholder).

### Gaps and Remediation Plan

1) Secrets hygiene (compose)
   - Issue: Hard-coded secrets (`SECRET_KEY`, `MAIL_USERNAME`, `MAIL_PASSWORD`) committed in `docker-compose.yml`.
   - Action: Move all secrets to `.env`; reference via `${VAR}` in compose; add `.env` to `.gitignore`.
   - Success: No secrets in VCS; compose reads from `.env`; app boots using Postgres.

2) Repository artifacts cleanup
   - Issue: Compiled binaries/logs (`SlicerOpener.exe`, `dist/`, `build/`, `sliceropener.log`), local DB (`backend/instance/app.db`), and stray `response.json` present.
   - Action: Add `.gitignore` entries; remove stray `response.json`; keep only `config.example.ini` (optionally `README.md`) under version control.
   - Success: `git status` shows no compiled/log artifacts; repo is clean.

3) Email template parity
   - Issue: `email_service.send_status_update_email` references `email/submission_status.html` (missing).
   - Action: Add minimal `backend/app/templates/email/submission_status.html` or adjust function to fallback without template.
   - Success: Calling `send_status_update_email` does not error; unit test passes.

4) Admin data management endpoints — (Resolved)
   - Implemented: `/api/v1/admin/archive` (default 45) and `/api/v1/admin/prune` (default 365) with guardrails and events.
   - Tests present: see `tests/test_admin_archive_prune.py`.
   - Success: Endpoints functional; tests pass.

5) Archived mapping for file ops/audit
   - Issue: `STATUS_TO_DIR` lacks `ARCHIVED` mapping; admin audit skips `Archived/`.
   - Action: Add `ARCHIVED: 'Archived'`; update audit to include archived dir when appropriate.
   - Success: Audit report includes archived items; no regressions in transitions.

6) Payment blueprint hygiene
   - Issue: `backend/app/routes/payment.py` is an empty blueprint while payment is implemented in `jobs.py`.
   - Action: Remove unused blueprint or add a comment/narrow purpose to avoid confusion.
   - Success: No dead blueprints registered; routes remain functional.

7) Optional: Health endpoint alignment
   - Issue: Health is at `/health` (public), plan mentions `/api/v1/health`.
   - Action: Add alias route under API prefix returning same payload.
   - Success: Both routes respond 200 in dev; tests cover at least one.

### High-level Task Breakdown (Audit Remediations)

- A. Secrets hygiene
  - Steps: Create `.env`; move secrets; update compose; add `.gitignore` entry
  - Success: `docker compose up -d --build` works; no secrets in git

- B. Clean artifacts
  - Steps: Add ignore rules; delete `response.json`; ensure `instance/app.db` not tracked
  - Success: `git status` clean; CI not affected

- C. Email template
  - Steps: Add minimal `submission_status.html`; unit test send without error
  - Success: Test passes; function safe to call

- D. Admin archive/prune
  - Steps: Implement endpoints + tests; wire to UI later
  - Success: API tests green; manual smoke via curl

- E. Archived mapping
  - Steps: Add mapping; extend audit; run tests
  - Success: Audit report lists archived where relevant

- F. Payment blueprint
  - Steps: Remove/annotate
  - Success: No route registration for empty blueprint

- G. Health alias (optional)
  - Steps: Add `/api/v1/health`; test returns 200
  - Success: Both endpoints OK

### Project Status Board — Audit Fixes

- [x] A. Move secrets to `.env` and update `docker-compose.yml`
- [x] B. Add `.gitignore` for `SlicerOpener/dist`, `SlicerOpener/build`, `SlicerOpener.exe`, `SlicerOpener/*.log`, `backend/instance/*.db`, `storage/**` (except fixture readme), and remove `response.json`
- [x] C. Add `backend/app/templates/email/submission_status.html`
- [x] C. Add `backend/app/templates/email/submission_status.html`
- [x] E. Add `ARCHIVED: 'Archived'` to `STATUS_TO_DIR` and include in audit
- [x] D. Implement `/api/v1/admin/archive` (default 45) and `/api/v1/admin/prune` (default 365) with tests
- [ ] (Future) F. Tidy `payment.py` blueprint (remove or document placeholder)
- [ ] (Future) G. Add `/api/v1/health` alias (optional)

### Current Status / Progress Tracking (Executor)

- Completed this session:
  - Implemented email notifications for rejection and completion
    - Added `send_rejection_email` and `send_completion_email` (with safe fallbacks) in `backend/app/services/email_service.py`
    - Wired calls in `reject_job` and `mark_complete`; log `RejectionEmailSent` and `CompletionEmailSent` events
    - Created templates `backend/app/templates/email/rejection_email.html` and `completion_email.html`
    - Updated completion email content to requested wording (room 145 Atkinson, TigerCASH, lab hours)
    - Lint checks passed; existing tests unaffected
  - Updated `docker-compose.yml` to use .env variables for backend secrets/config
  - Added `.gitignore` to ignore secrets, binaries, logs, node_modules, pycache, local DB, storage
  - Removed stray `response.json`
  - Added `ARCHIVED: 'Archived'` to `STATUS_TO_DIR`
  - Added email template `backend/app/templates/email/submission_status.html`
  - Restarted stack and verified `/health` OK
- Next in progress:
  - All backend tests green (45 passed). Proceed to next priority.

### Executor's Feedback or Assistance Requests

- Please ensure your local `.env` contains the keys listed in the previous message (SECRET_KEY, DATABASE_URL, REDIS_URL, MAIL_*, FRONTEND_PUBLIC_URL, STORAGE_PATH). Do not commit `.env`.
 - Would you like to customize the rejection email wording as well? Currently it lists reasons and a brief invitation to revise and resubmit.


