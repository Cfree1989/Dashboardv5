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

### Phase 5: Job Management Modals 📋 PENDING
- [ ] **Approval Modal** - File selection, weight/time inputs, cost calculation (next)
- [ ] **Rejection Modal** - Rejection reasons, custom messages
- [ ] **Status Change Modals** - Printing, Complete, Pickup confirmations  
- [ ] **Notes Editing** - Inline notes interface

### Phase 6: Real-time Updates 📋 PENDING
- [ ] **Auto-refresh hook** - Dashboard updates every 45s
- [ ] **Audio notifications** - Sound alerts for new jobs
- [ ] **Visual indicators** - "NEW" badges, job age tracking
- [ ] **Staff acknowledgment** - Mark as reviewed functionality

### Phase 7: Testing & Deployment 📋 PENDING
- [ ] Comprehensive testing (unit, integration, e2e)
- [ ] Production deployment configuration
- [ ] Documentation and training materials

## Current Status

**Current Phase**: Phase 4 - Advanced Features  
**Next Milestone**: Phase 5.1 - Approval Modal (UX + inputs)
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
- [ ] Executor: Phase 5.1.2 — Frontend: Build Approval Modal UI
  - Success criteria: Modal with inputs (weight_g, time_hours), live cost preview, required Staff Attribution dropdown (populated from `/api/v1/staff`), inline validation, accessible focus/ARIA; Storybook-like visual check not required
- [ ] Executor: Phase 5.1.3 — Wire JobCard "Approve" to Modal + API
  - Success criteria: Clicking Approve opens modal; on submit calls API with Authorization header; optimistic update removes job from `UPLOADED` list; error states render; toast on success
- [ ] Executor: Phase 5.1.4 — Tests
  - Success criteria: Backend tests for approve payload validation and event logging; Frontend tests for modal validation and API call; all CI tests pass
- [ ] Executor: Phase 5.1.5 — Candidate Files (stub)
  - Success criteria: Optional `GET /api/v1/jobs/:id/candidate-files` returns at least the uploaded file; frontend shows file selector (non-blocking); can be deferred to Phase 4.2 File Management

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
1. **Phase 4.1: Email Service Integration** ⚡ HIGH
2. **Phase 5.1: Approval Modal** 🔥 CRITICAL for staff workflow

### Short-term (Next Session):  
3. **Phase 5.2-5.4: Remaining Job Management Modals**
4. **Phase 4.2: File Management System**

### Medium-term:
5. **Phase 6: Real-time Updates**
6. **Phase 4.3: Payment & Pickup Workflow**

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