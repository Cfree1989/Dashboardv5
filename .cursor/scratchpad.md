# 3D Print Management System - Build Plan

## Project Status

**Current Phase**: Pre-E2E Implementation  
**Overall Progress**: ~90% (core functionality complete, Docker deployment working, UI improvements in progress)  
**Next Priority**: Complete UI enhancements → E2E testing → Production deployment

## System Overview

**Architecture**: Flask API (PostgreSQL) + Next.js frontend + Docker deployment  
**Key Features**: Workstation auth, full job lifecycle, file tracking, email notifications, protocol handler  
**Design**: API-first, multi-user (≤2 staff), robust error handling, audit trails

## ✅ Completed Features

### Core System
- ✅ Authentication (workstation login + JWT + staff attribution)
- ✅ Job lifecycle (submit → approve → confirm → print → complete → payment)
- ✅ File management (upload, tracking, metadata.json sync, audit reports)
- ✅ Email notifications (approval, rejection, completion)
- ✅ Admin system (staff management, data archival, system health)
- ✅ Payment & pickup workflow
- ✅ Notes editing (append-style with attribution)
- ✅ Protocol handler (3dprint:// and print3d://) - **RESOLVED**
- ✅ Docker Compose deployment - **WORKING**

### Protocol Handler Resolution
**Issue**: Cross-tab protocol invocation failures  
**Root Cause**: User gesture preservation - modal JavaScript buttons broke browser gesture chain  
**Solution**: Replaced modal buttons with real anchor elements (`<a href="print3d://...">`)  
**Result**: Reliable file opening from all dashboard tabs with complete audit trail

### Docker Deployment Resolution
**Issue**: Module resolution and architecture misalignment  
**Root Cause**: Running frontend standalone vs intended Docker Compose architecture  
**Solution**: Deploy using `docker-compose up -d` with proper container rebuild  
**Result**: All services running correctly, frontend connects to backend, site fully functional

## 🎯 Active Workstreams

### Pre-E2E Gap Items (Must Complete Before E2E)

#### P1. Submit Rate Limiting (Must-do)
- **Backend**: Add `@limiter.limit("3 per hour")` to `POST /api/v1/submit`
- **Tests**: `tests/test_submit_rate_limit.py` - 4 submissions → 3x 201, 1x 429
- **Success**: Fourth submission within hour returns 429

#### P2. Expired/Resend Confirmation (Optional)
- **Backend**: `POST /api/v1/submit/resend-confirmation` (rate-limited 1/hour)
- **Frontend**: `/confirm/expired` page with resend button
- **Tests**: Happy path, invalid job, rate limit, event logging

#### P3. Revert Endpoints (Optional)
- **Backend**: `POST /jobs/<id>/revert-completion` (COMPLETED → PRINTING)
- **Backend**: `POST /jobs/<id>/revert-pickup` (PAIDPICKEDUP → COMPLETED)
- **Tests**: Guards, file moves, metadata sync, events

#### P4. Soft-Delete + Confirmation (Optional)
- **Backend**: Change DELETE to soft-delete: set status `ARCHIVED`, move files to `Archived/`, log event; add `POST /api/v1/jobs/<id>/hard-delete` (admin-only) for permanent removal when needed
- **Frontend**: Delete action requires typing job `short_id` to confirm
- **Tests**: Delete moves files to Archived and sets status; hard-delete removes row and files; guards and events verified

#### P5. Payments Export (Optional)
- **Backend**: `POST /api/v1/export/payments` (CSV/XLSX summary)
- **Tests**: Date parsing, filtering, event logging

#### P6. Background Audio (Optional)
- **Frontend**: `sound-utils.ts` with `playNewUploadSound()`
- **Dashboard**: Detect UPLOADED count increase → play sound
- **Tests**: Mock function called on count increase

#### P7. Health Alias (Sanity)
- **Backend**: Confirm `/api/v1/health` alias exists alongside `/health`

### Project Status Board — Pre-E2E
- [x] P1. Submit rate limiting — backend + tests ✅ **COMPLETED**
- [x] P2. Expired/resend confirmation — backend + frontend + tests ✅ **COMPLETED**
- [x] P3. Revert endpoints — backend + tests ✅ **COMPLETED**
- [x] P4. Soft-delete + confirmation — backend + frontend + tests ✅ **COMPLETED**
- [x] P5. Payments export — backend + tests ✅ **COMPLETED**
- [x] P6. Background audio trigger — frontend + tests ✅ **COMPLETED**
- [x] P7. Health alias — backend ✅ **COMPLETED**

### UI2. Dashboard Sorting (Planner)

#### Background & Motivation
- Staff need consistent control over how jobs are ordered within each dashboard tab (status filter). The primary needs are sorting by submitted time, student name, and printer, with minimal risk of regressions and minimal code changes.

#### Key Challenges & Constraints
- Keep changes localized (do not refactor tabs or data fetching).
- Ensure stable, deterministic sort and predictable tie-breakers.
- Maintain accessibility and responsiveness of the existing layout.
- Avoid API changes; implement client-side sorting only.

#### Minimal-Touch Files (proposed)
- frontend/src/components/dashboard/job-list.tsx (add sort UI and logic)
- frontend/src/components/dashboard/job-list.test.tsx (tests)
- Optional: No change to `status-tabs.tsx`, `page.tsx`, or backend.

#### Success Criteria (Feature)
- A compact sort control appears above the list in every status tab.
- Options: Time (newest → oldest / oldest → newest), Name (A→Z / Z→A), Printer (A→Z / Z→A).
- Sorting works consistently, is stable, and does not disturb layout.
- Selection persists per user via localStorage and restores on reload.
- All unit tests pass; build succeeds with no linter errors.

#### High-level Task Breakdown (Granular)
1) S1 – Read-only scan (no code changes)
   - Locate render point in `job-list.tsx` for header controls.
   - Confirm data fields available: `created_at`, `student_name`, `printer`.
   - Define default: Time desc (newest first).
   - Success: Notes recorded in this scratchpad.

2) S2 – Introduce sort state and UI (dropdown + direction toggle)
   - Add internal state: `sortBy` ∈ {time, name, printer}, `sortDir` ∈ {asc, desc}.
   - Render compact control at top-right of `job-list` header.
   - Success: Control renders and updates state on interaction.

3) S3 – Implement stable client-side sort
   - Derive `sortedJobs` from props using `useMemo` and comparator per `sortBy`/`sortDir`.
   - Tie-breakers: `created_at` then `student_name` then `printer`.
   - Handle missing values safely.
   - Success: Visual order changes as expected.

3a) S3a – Motion-safe fade on sort (UX polish)
   - Wrap the list container with a 150–200ms opacity transition to soften reordering.
   - Use existing `frontend/src/lib/use-reduced-motion.ts` to respect reduced motion and disable animation when preferred.
   - No new dependencies; single-file change (`job-list.tsx`).
   - Success: Subtle fade during sort change; no layout shift or performance issues.

4) S4 – Persist selection
   - Write to localStorage on change; read on mount with sane fallback.
   - Key: `dashboard.sort.v1`.
   - Success: Selection restored after reload.

5) S5 – Tests
   - Update `job-list.test.tsx` with datasets to assert sorting by time/name/printer both directions.
   - Success: Tests pass locally.

6) S6 – Build & Lint
   - Run `npm run build` in frontend; ensure no type/lint errors.
   - Success: Green build.

7) S7 – Manual QA
   - Verify in each tab (UPLOADED, PENDING, READYTOPRINT, PRINTING, COMPLETED) that sorting UI appears and works without layout regressions.
   - Success: No visual overlap; keyboard accessible.

8) S8 – Documentation
   - Add short usage note to this scratchpad under Current Status.
   - Success: Checklist updated and marked complete.

#### Risks & Mitigations
- Risk: Large lists and sort perf — Mitigation: `useMemo` and simple comparators.
- Risk: Missing data cause crashes — Mitigation: Safe accessors and defaults.
- Risk: Layout shift — Mitigation: Compact UI aligned to existing header area.

#### Rollback Plan
- Feature is isolated to `job-list.tsx` and test; revert those files to prior revision if needed.

#### Estimated Effort
- 2–4 hours including tests and QA.

## 📋 Future Implementation (Post-E2E)

### Analytics V0 Parity
- **A1-A8**: Unify filters, overview cards, trend charts, resource metrics, financial summary
- **AN1-AN7**: Add animations with `refreshKey`, fade-in, reduced motion support

### Masterplan Coverage Gaps
- **M1**: Submission form disclaimer & UX parity with masterplan
- **M2**: Thumbnails (async previews with tolerant failure)
- **M3**: Admin Email Tools (resend emails, rate-limited)
- **M4**: Stats endpoints (`/api/v1/stats`, `/api/v1/stats/detailed`)
- **M5**: Backup & Disaster Recovery docs and scripts

### Phase 6-14 Features
- **Phase 6**: Real-time locks, alerts, auto-refresh
- **Phase 7**: E2E testing, CI pipeline, deployment docs
- **Phase 8**: Analytics & reporting (backend endpoints)
- **Phase 9**: System health & integrity (worker status)
- **Phase 10**: Data retention & archival (UI integration)
- **Phase 11**: Security & rate limiting (CORS, CSP)
- **Phase 12**: Background jobs & email queue (Redis + RQ)
- **Phase 13**: Financial reporting (Excel export, email)
- **Phase 14**: Performance, reliability, polish (DB indexes, monitoring)

## 🚀 Next Steps Priority
1. Complete UI enhancements (JobCard improvements)
2. E2E happy path testing
3. Deployment docs

## 📚 Lessons Learned

- **Protocol Handler**: User gesture preservation is critical for custom protocols
- **File Paths**: Normalize to Windows format (`C:\Dashboardv5\storage\`) for SlicerOpener
- **Rate Limiting**: Flask-Limiter already configured, just need endpoint decorators
- **Testing**: Use temp storage fixtures, mock filesystem operations
- **Development**: Prefer `pytest -q` on Windows PowerShell (avoid `&&`)
- **Flask-Limiter**: Returns HTML error pages by default, use `response.get_json()` with None check
- **Docker Deployment**: Always use `docker-compose up -d` for proper service networking
- **Module Resolution**: Rebuild containers after dependency changes with `docker-compose build frontend`

## 🔧 Technical Notes

- **Database**: PostgreSQL with SQLAlchemy, Alembic migrations
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, Recharts
- **Protocol**: 3dprint:// and print3d:// both registered
- **Email**: Flask-Mail with Office 365 SMTP (best-effort send)
- **Storage**: Shared network mount with status-based directories
- **Docker**: Multi-container with PostgreSQL, Redis, worker

## 📊 Current Status / Progress Tracking

### P1. Submit Rate Limiting ✅ COMPLETED
- **Backend**: Added `@limiter.limit("5 per hour")` decorator to `POST /api/v1/submit`
- **Tests**: Created comprehensive test suite `tests/test_submit_rate_limit.py`
- **Success Criteria**: ✅ 6th submission within hour returns 429 status code
- **Test Results**: All 3 tests passing (5 per hour limit, IP-based tracking, error message validation)
- **Implementation**: Flask-Limiter already configured, just needed endpoint decorator
- **Update**: Changed from 3 to 5 submissions per hour based on user request

### P2. Expired/Resend Confirmation ✅ COMPLETED
- **Backend**: Added `POST /api/v1/submit/resend-confirmation` with `@limiter.limit("1 per hour")`
  - Accepts JSON `{ job_id }` or `{ token }` (token parsed even if expired)
  - Generates fresh token and sends approval email with new confirmation URL
  - Logs `ResendConfirmationRequested` and `ApprovalEmailResent` events
- **Frontend**: New page `frontend/src/app/confirm/expired/page.tsx` with form to resend by Job ID or token
  - Added link from expired confirm flow to `/confirm/expired` (pending user UX review)
- **Tests**: `tests/test_submit_resend.py` covers happy path, invalid token, missing params, job not found, already confirmed, and rate limit — ✅ all passing
- **Success Criteria**: ✅ On expired link, user can request a new confirmation email; rate limit enforced (1/hour)

### P3. Revert Endpoints ✅ COMPLETED
- **Backend**: Added `POST /api/v1/jobs/<id>/revert-completion` (COMPLETED → PRINTING) and `POST /api/v1/jobs/<id>/revert-pickup` (PAIDPICKEDUP → COMPLETED)
- **Behavior**: Enforces status guards, moves files via `move_authoritative`, syncs metadata via `_sync_authoritative_metadata`, logs `JobRevertedToPrinting` / `JobRevertedToCompleted`
- **Tests**: `tests/test_revert_endpoints.py` covers happy paths and guards — ✅ passing
- **Impact**: Enables safe recovery from premature completion/pickup actions

### P4. Soft-Delete + Confirmation ✅ COMPLETED
- **Backend**: Modified `DELETE /api/v1/jobs/<id>` to perform soft-delete (status → `ARCHIVED`, files moved to `Archived/`, event logged); added `POST /api/v1/jobs/<id>/hard-delete` for permanent removal
- **Frontend**: Archive button with confirmation dialog requiring `short_id` entry; styled with faded orange theme
- **Tests**: Updated `tests/test_jobs.py` to verify soft-delete behavior and hard-delete functionality
- **Success Criteria**: ✅ Archive moves files to Archived directory and sets status; hard-delete removes row and files; frontend requires confirmation

### P6. Background Audio Trigger ✅ COMPLETED
- **Frontend**: Created `frontend/src/lib/sound-utils.ts` with Web Audio API implementation
  - `playNewUploadSound()`: Generates pleasant notification tone (800Hz → 1200Hz rise)
  - `playStatusChangeSound()`: Different tone for status changes (600Hz → 800Hz)
  - Fallback to HTML5 Audio with data URL beep if Web Audio API fails
  - Handles autoplay policies and suspended audio contexts
- **Dashboard Integration**: Updated `frontend/src/app/dashboard/page.tsx` to detect UPLOADED count increases
  - Uses localStorage to persist count across page refreshes for reliable detection
  - Compares against stored count to handle rapid refreshes and manual submissions
  - Only triggers sound when count increases (not on initial load or decrease)
  - Respects `canPlayAudio()` to check browser support and page visibility
- **Tests**: Created comprehensive test suite `frontend/src/lib/sound-utils.test.ts` covering audio support detection, sound generation, and error handling
- **Success Criteria**: ✅ Dashboard plays notification sound when new uploads are detected; works with auto-refresh, manual refresh, and rapid submissions; graceful fallback for unsupported browsers

### P7. Health Alias ✅ COMPLETED
- **Backend**: Confirmed `/api/v1/health` endpoint exists and is fully functional
  - Located in `backend/app/routes/health.py` with comprehensive health checks
  - Returns detailed status including database connectivity and component health
  - Proper HTTP status codes (200 for healthy, 503 for unhealthy)
  - Includes environment detection and component status reporting
- **Tests**: Verified with `tests/test_health.py` - endpoint returns 200 status with expected JSON structure
- **Bonus**: Root `/health` endpoint also exists in `backend/run.py` for simple health checks
- **Success Criteria**: ✅ `/api/v1/health` endpoint exists and returns proper health status with database connectivity check

### TT1. Tooltip System ✅ COMPLETED
- Implementation: `frontend/src/components/ui/tooltip.tsx` (Radix wrapper) with `TooltipProvider`, `Tooltip`, `TooltipTrigger`, `TooltipContent`; defaults: 200ms delay, top placement, motion-safe transitions
- Tests: `frontend/src/components/ui/tooltip.test.tsx` verifies focus open/blur close and Escape-to-close; tests pass
- Dependency: `@radix-ui/react-tooltip` added to `frontend/package.json`
- Ready for TT2 integration (icon-only buttons)

### UI1. JobCard Layout Improvements ✅ COMPLETED
- **Collapse Arrow**: Successfully moved to bottom center of card with proper styling and accessibility
- **Focus Ring**: Fixed clipping issue by adding `px-1` padding to textarea container (removed `overflow-visible` that was breaking grid layout)
- **Notes Section**: Positioned in expanded details area with proper structure and workflow
- **Additional Details**: Includes Discipline and Class fields as planned
- **Grid Layout**: Fixed 2-cards-per-row issue by removing `overflow-visible` from job card container
- **Status**: All layout improvements completed and working well, site fully functional

## Executor's Feedback or Assistance Requests

### Current Status
- All Pre-E2E gap items completed ✅
- Docker Compose deployment working correctly ✅
- Module resolution issues resolved ✅
- JobCard UI improvements completed ✅
- Site fully functional with all core features working

### Recent Accomplishments
- Successfully resolved `@radix-ui/react-tooltip` module resolution error
- Fixed Docker Compose architecture misalignment
- Moved collapse arrow to bottom center of job cards
- Fixed focus ring clipping issues
- Maintained proper card grid layout
- Resend modal now loads active staff names on open; added validation before sending
- Archive button now available on all job cards from `UPLOADED` through `COMPLETED`

### Next Steps
- All core UI improvements completed
- Ready for next phase: Analytics enhancements or deployment documentation
- Consider additional polish items as needed

---

**Last Updated**: Current session  
**Next Review**: After UI enhancements completion

## 📋 COMPREHENSIVE TASK CHECKLIST

### ✅ COMPLETED ITEMS
- [x] **Core System Features**
  - [x] Authentication (workstation login + JWT + staff attribution)
  - [x] Job lifecycle (submit → approve → confirm → print → complete → payment)
  - [x] File management (upload, tracking, metadata.json sync, audit reports)
  - [x] Email notifications (approval, rejection, completion)
  - [x] Admin system (staff management, data archival, system health)
  - [x] Payment & pickup workflow
  - [x] Notes editing (append-style with attribution)
  - [x] Protocol handler (3dprint:// and print3d://)
  - [x] Docker Compose deployment

- [x] **Pre-E2E Gap Items**
  - [x] P1. Submit rate limiting (5 per hour)
  - [x] P2. Expired/resend confirmation
  - [x] P3. Revert endpoints (completion → printing, pickup → completed)
  - [x] P4. Soft-delete + confirmation
  - [x] P5. Payments export (CSV)
  - [x] P6. Background audio trigger
  - [x] P7. Health alias

- [x] **UI Improvements**
  - [x] TT1. Tooltip system (Radix wrapper)
  - [x] UI1. JobCard layout improvements (collapse arrow, focus ring, notes section)

### 🔄 REMAINING TASKS

#### **Phase 1: Analytics Enhancements (High Priority)**
- [ ] **A1. Analytics Dashboard Parity**
  - [x] Unify filters across all analytics components
  - [x] Standardize overview cards design
  - [x] Implement consistent trend charts
  - [x] Add resource metrics visualization
  - [x] Create financial summary components
  - [x] Add animations with `refreshKey`
  - [x] Implement fade-in transitions
  - [x] Add reduced motion support

- [ ] **A2. Analytics Backend Endpoints**
  - [x] Create `/api/v1/analytics/overview` endpoint
  - [x] Create `/api/v1/analytics/trends` endpoint
  - [x] Create `/api/v1/analytics/resources` endpoint
  - [ ] Create `/api/v1/analytics/financial` endpoint
  - [ ] Add proper data aggregation and caching
  - [ ] Implement date range filtering
  - [ ] Add staff attribution to analytics

#### **Phase 2: Admin Features (Medium Priority)**
- [ ] **M1. Submission Form Improvements**
  - [ ] Improve UX parity with masterplan
  - [x] Add form validation enhancements
  - [x] Implement better error handling


- [ ] **M3. Admin Email Tools**
  - [x] Add resend email functionality (POST /api/v1/jobs/<id>/admin/resend-email)
  - [x] Implement rate-limited email resend (1/hour)
  - [x] Wire admin UI panel to endpoint
  - [x] Add resend modal with staff selection and confirmation
  - [ ] Add email template management

- [ ] **M4. Stats Endpoints**
  - [ ] Create `/api/v1/stats` endpoint
  - [ ] Create `/api/v1/stats/detailed` endpoint
  - [ ] Add comprehensive system statistics
  - [ ] Implement performance metrics

- [ ] **M5. Backup & Disaster Recovery**
  - [ ] Create backup scripts
  - [ ] Document disaster recovery procedures
  - [ ] Implement automated backup scheduling
  - [ ] Add backup verification tools

#### **Phase 3: Advanced Features (Lower Priority)**
- [ ] **Phase 6: Real-time Features**
  - [ ] Implement real-time locks
  - [ ] Add alert system
  - [ ] Enhance auto-refresh functionality
  - [ ] Add real-time notifications

- [ ] **Phase 8: Enhanced Analytics**
  - [ ] Add advanced reporting features
  - [ ] Implement custom date ranges
  - [ ] Add export functionality
  - [ ] Create dashboard customization

- [ ] **Phase 9: System Health**
  - [ ] Enhance worker status monitoring
  - [ ] Add system integrity checks
  - [ ] Implement health alerts
  - [ ] Create system diagnostics

- [ ] **Phase 10: Data Management**
  - [ ] Implement data retention policies
  - [ ] Add archival automation
  - [ ] Create data cleanup tools
  - [ ] Add data export features

- [ ] **Phase 11: Security Enhancements**
  - [ ] Implement CORS restrictions
  - [ ] Add Content Security Policy (CSP)
  - [ ] Enhance rate limiting
  - [ ] Add security monitoring

- [ ] **Phase 12: Background Processing**
  - [ ] Enhance Redis + RQ integration
  - [ ] Add email queue management
  - [ ] Implement background job monitoring
  - [ ] Add job retry mechanisms

- [ ] **Phase 13: Financial Reporting**
  - [ ] Implement Excel export functionality
  - [ ] Add automated email reports
  - [ ] Create financial dashboard
  - [ ] Add revenue tracking

- [ ] **Phase 14: Performance & Polish**
  - [ ] Add database indexes
  - [ ] Implement monitoring
  - [ ] Optimize performance
  - [ ] Add error tracking

#### **Phase 4: Documentation & Deployment**
- [ ] **Deployment Documentation**
  - [ ] Create comprehensive setup guide
  - [ ] Document Docker deployment process
  - [ ] Add troubleshooting guides
  - [ ] Create maintenance procedures

- [ ] **API Documentation**
  - [ ] Document all API endpoints
  - [ ] Create API usage examples
  - [ ] Add authentication documentation
  - [ ] Create integration guides

- [ ] **User Documentation**
  - [ ] Create user manuals
  - [ ] Add feature guides
  - [ ] Create video tutorials
  - [ ] Add FAQ section

#### **Phase 5: Testing & Quality Assurance**
- [ ] **E2E Testing (Post-Implementation)**
  - [ ] Set up E2E testing framework (Playwright/Cypress)
  - [ ] Create student submission workflow tests
  - [ ] Create staff approval workflow tests
  - [ ] Create file management workflow tests
  - [ ] Create payment workflow tests
  - [ ] Add cross-browser testing
  - [ ] Implement CI/CD pipeline

- [ ] **Quality Assurance**
  - [ ] Add comprehensive unit test coverage
  - [ ] Implement integration tests
  - [ ] Add performance testing
  - [ ] Create security testing
  - [ ] Add accessibility testing

#### **Phase 6: Production Readiness**
- [ ] **Production Deployment**
  - [ ] Set up production environment
  - [ ] Configure production database
  - [ ] Set up SSL certificates
  - [ ] Configure domain and DNS
  - [ ] Set up monitoring and logging
  - [ ] Create backup procedures
  - [ ] Implement disaster recovery

- [ ] **Performance Optimization**
  - [ ] Optimize database queries
  - [ ] Implement caching strategies
  - [ ] Add CDN for static assets
  - [ ] Optimize frontend bundle size
  - [ ] Add lazy loading
  - [ ] Implement service workers

### 🎯 IMMEDIATE NEXT STEPS (Choose One)


**Option B: Admin Features**
- Start with M1. Submission Form Improvements
- Focus on UX enhancements
- Estimated effort: 1-2 weeks

**Option C: Documentation**
- Start with deployment documentation
- Focus on setup and maintenance guides
- Estimated effort: 1 week

**Option D: Advanced Features**
- Start with Phase 6 real-time features
- Focus on enhancing user experience
- Estimated effort: 2-3 weeks

### 📊 PROGRESS SUMMARY
- **Core Features**: 100% Complete ✅
- **Pre-E2E Items**: 100% Complete ✅
- **UI Improvements**: 100% Complete ✅
- **Analytics**: 0% Complete ❌
- **Admin Features**: 0% Complete ❌
- **Documentation**: 0% Complete ❌
- **Testing**: 0% Complete ❌
- **Production**: 0% Complete ❌

**Overall Project Completion**: ~90% (Core functionality complete, ready for enhancements)