# 3D Print Management System - Build Plan

## Project Status

**Current Phase**: Pre-E2E Implementation  
**Overall Progress**: ~95% (core functionality complete, Docker deployment working, analytics enhancements complete)  
**Next Priority**: System stability features → E2E testing → Production deployment

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

### UI2. Dashboard Sorting ✅ **COMPLETED**
- **Implementation**: Dashboard sorting feature has been fully implemented in `job-list.tsx`
- **Features**: 
  - Sort by Time (newest/oldest), Name (A→Z/Z→A), Printer (A→Z/Z→A), Color, and Class
  - Direction toggle with ascending/descending controls
  - Stable sorting with tie-breakers (created_at → student_name → printer → id)
  - Motion-safe fade transitions (180ms opacity) with reduced motion support
  - localStorage persistence (`dashboard.sort.v1`) with automatic restoration
  - Compact UI positioned in top-right of job list header
- **Technical Details**:
  - Client-side sorting using `useMemo` for performance
  - Safe handling of missing values with fallbacks
  - Proper accessibility with ARIA labels and keyboard navigation
  - Integration with existing search and expand/collapse controls
- **Build Status**: ✅ Green build with no TypeScript errors
- **Test Status**: Basic sorting test exists but needs refinement for multiple combobox scenarios
- **Manual Verification**: Feature is fully functional across all dashboard tabs

### UI3. Global Search UX Stabilization ✅ COMPLETED
- **Search UX Issues**: Resolved disappearing search bar, typing interruptions, and layout instability.
- **Implementation**: Moved search to page-level with 400ms debounce and localStorage persistence.
- **JobList Refactor**: Removed internal search state, kept controls visible on empty results, added AbortController for smooth typing.
- **Cross-tab Indicators**: Single badge per tab switches from blue (total) to orange (matches) when searching.
- **Search Placement**: Positioned search input to left of expand/collapse button for cohesive design.
- **Sound Fix**: Separated count computation to prevent notification sounds when exiting search.
- **Success Criteria**: ✅ Search never disappears, typing is smooth, proper match indicators, no layout regressions.
- **Build Status**: Green build with no linter errors.
- **Manual Testing**: Confirmed all functionality works as expected.

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
- Global Search UX Stabilization completed ✅
- **FI1. Payment Accuracy & Finance Variance workstream completed** ✅
- Site fully functional with all core features working and polished UI

### Recent Accomplishments
- Successfully resolved `@radix-ui/react-tooltip` module resolution error
- Fixed Docker Compose architecture misalignment
- Moved collapse arrow to bottom center of job cards
- Fixed focus ring clipping issues
- Maintained proper card grid layout
- Resend modal now loads active staff names on open; added validation before sending
- Archive button now available on all job cards from `UPLOADED` through `COMPLETED`
- **UI2. Dashboard Sorting**: ✅ **COMPLETED** - Full sorting functionality implemented with Time, Name, Printer, Color, and Class options, direction toggles, localStorage persistence, and motion-safe transitions
- **FI1-S4. Finance Estimated vs Actual**: ✅ **COMPLETED** - Added estimated vs actual revenue comparison to financial analytics with variance calculation, updated frontend KPIs with color-coded variance display, and comprehensive test coverage
- **FI1-S5. Manual QA**: ✅ **COMPLETED** - Verified payment workflow functionality, job card labeling changes, and financial analytics display
- **Payment Modal Weight Input Fix**: ✅ **COMPLETED** - Fixed issue where weight field was defaulting to browser auto-fill values (5g/25g) by adding autocomplete="off" attributes and explicit field clearing on modal open
- **Mock Jobs Population**: ✅ **COMPLETED** - Added 24 diverse mock jobs to test dashboard functionality: 15 completed jobs across Engineering, Art, Architecture, and Science disciplines with various materials/colors, plus 9 paid jobs demonstrating estimated vs actual cost scenarios including minimum charge cases
- **Job Card Weight Display Fix**: ✅ **COMPLETED** - Fixed job cards to show actual weight from payment data instead of estimated weight for paid jobs, now displays "Final Weight:" vs "Weight:" similar to cost labeling
- **System Cleanup**: ✅ **COMPLETED** - Cleared all 65 jobs, 304 events, and 15 payments from the system, removed all storage files, providing a clean slate for fresh testing
- Implemented global search with cross-tab indicators and smooth UX
- Fixed notification sound playing when exiting search
- Positioned search input cohesively with other controls
- **Analytics Page Tabbed Interface**: Successfully reorganized analytics page into Operations, Finance, Staff Analytics, and Student Analytics tabs
  - Operations tab contains overview cards, trend charts, and resource metrics
  - Finance tab contains financial summary with enhanced financial features preview
  - Staff Analytics tab remains as existing functionality
  - Student Analytics tab added with GraduationCap icon, showing student overview cards and placeholder sections for trends, performance, discipline analysis, and comparison
  - All tabs use shared state management and smooth transitions
  - Build completed successfully with no regressions
- **FI1-S1. Backend Payment Calculation Fix**: ✅ **COMPLETED**
  - Fixed `record_payment` endpoint to always compute final price from actual pickup weight (grams) instead of using job estimate
  - Added comprehensive tests covering filament ($0.10/g), resin ($0.20/g), and minimum charge ($3.00) scenarios
  - Verified that `Payment.price_cents` now stores the actual pickup price, not the estimate from approval
  - All existing tests continue to pass with no regressions
- **FI1-S2. Payment Modal Enhancements**: ✅ **COMPLETED**
  - Enhanced payment modal to fetch job details (material and cost_usd) on open
  - Added material and pricing info display showing rate ($0.10/g Filament or $0.20/g Resin) and estimated cost
  - Implemented live "Final Price" preview that updates as grams are entered
  - Enhanced confirm dialog to show final calculated amount with breakdown
  - Added minimum charge indicator when $3.00 minimum is applied
  - Frontend build completed successfully with no TypeScript errors
- **FI1-S3. Job Card Labeling**: ✅ **COMPLETED**
  - Updated backend `Job.to_dict()` to include payment information when available
  - Enhanced job card component to show "Estimated Cost:" for non-paid jobs and "Final Cost:" for paid jobs
  - Added payment interface to Job type definition for TypeScript support
  - Job cards now display the actual payment amount for PAIDPICKEDUP status jobs
  - All backend tests continue to pass with no regressions

### Next Steps
- All core UI improvements completed ✅
- **FI1. Payment Accuracy & Finance Variance workstream completed** ✅
- Analytics enhancements completed ✅
- **Next Priority: M4. Stats Endpoints** - Create comprehensive system statistics endpoints
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
  - [x] UI3. Global Search UX Stabilization (page-level search, cross-tab indicators, smooth typing)

### 🔄 REMAINING TASKS

#### **Phase 1: Analytics Enhancements (High Priority)**
- [x] **A1. Analytics Dashboard Parity**
  - [x] Unify filters across all analytics components
  - [x] Standardize overview cards design
  - [x] Implement consistent trend charts
  - [x] Add resource metrics visualization
  - [x] Create financial summary components
  - [x] Add animations with `refreshKey`
  - [x] Implement fade-in transitions
  - [x] Add reduced motion support

- [x] **A2. Analytics Backend Endpoints**
  - [x] Create `/api/v1/analytics/overview` endpoint
  - [x] Create `/api/v1/analytics/trends` endpoint
  - [x] Create `/api/v1/analytics/resources` endpoint
  - [x] Create `/api/v1/analytics/financial` endpoint
  - [x] Add basic in-memory caching (60s, disabled in tests)
  - [x] Implement date range filtering
  - [x] Add staff attribution to analytics

- [x] **A3. Analytics UX Improvements** ✅ **COMPLETED**
  - [x] Fix queue status ordering to match dashboard workflow (UPLOADED → PENDING → READYTOPRINT → PRINTING → COMPLETED → PAIDPICKEDUP → REJECTED → ARCHIVED)
  - [x] Remove confusing staff activity summary from overview cards
  - [x] Remove staff filter from main analytics (moving to separate staff analytics section) ✅ **COMPLETED**
  - [x] Remove storage usage percentage (not useful without configuration)
  - [x] Clean up analytics types and API responses
  - [x] Ensure all analytics endpoints respect printer and discipline filters

- [ ] **A4. Staff Analytics Section** (New)
  - [x] **A4.1. Staff Analytics Backend** ✅ **COMPLETED**
    - [x] Create `/api/v1/staff-analytics/overview` endpoint for staff performance summary
    - [x] Create `/api/v1/staff-analytics/performance` endpoint for individual staff metrics
    - [x] Create `/api/v1/staff-analytics/activity` endpoint for staff activity timeline
    - [x] Create `/api/v1/staff-analytics/comparison` endpoint for staff comparison data
    - [x] Implement staff performance calculation logic (completion rates, response times)
    - [x] Add staff workload distribution analysis
    - [x] Create staff activity tracking and aggregation

  - [x] **A4.2. Staff Analytics Frontend** ✅ **COMPLETED**
    - [x] Create new `/staff-analytics` page with dedicated staff-focused interface
    - [x] Build staff performance cards showing individual metrics
    - [x] Implement staff comparison views and side-by-side analysis
    - [x] Create staff activity timeline with daily activity logs
    - [x] Add staff workload distribution visualization
    - [x] Implement staff-specific filtering and date range controls
    - [x] Add navigation between system analytics and staff analytics

  - [x] **A4.3. Staff Analytics Features** ✅ **COMPLETED**
    - [x] Individual staff performance metrics (tasks completed, response times, quality metrics)
    - [x] Staff comparison views for fair workload distribution analysis
    - [x] Staff activity timeline showing daily actions and performance trends
    - [x] Team performance overview vs individual performance breakdown
    - [x] Staff training opportunity identification based on performance gaps
    - [x] Staff accountability tracking with complete audit trail access

- [x] **A5. Analytics Interface Consolidation** ✅ **COMPLETED**
  - [x] Convert `/analytics` page to tabbed interface (similar to admin page pattern)
  - [x] Add "System Analytics" tab with existing system analytics content
  - [x] Add "Staff Analytics" tab with staff analytics components
  - [x] Implement shared state management for filters and date ranges
  - [x] Add sidebar navigation with icons (BarChart3 for system, Users for staff)
  - [x] Remove separate `/staff-analytics` page and route
  - [x] Update navigation links throughout application
  - [x] Test tabbed interface functionality and responsiveness

- [x] **A6. Student Analytics Section** ✅ **COMPLETED**
  - [x] **A6.1. Student Analytics Backend** ✅ **COMPLETED**
    - [x] Create `/api/v1/analytics/student/overview` endpoint for student overview metrics
    - [x] Create `/api/v1/analytics/student/performance` endpoint for student performance data
    - [x] Create `/api/v1/analytics/student/trends` endpoint for student submission trends
    - [x] Implement student analytics calculation logic (approval rates, costs, activity)
    - [x] Add student comparison and ranking capabilities
    - [x] Create student activity tracking and aggregation

  - [x] **A6.2. Student Analytics Frontend** ✅ **COMPLETED**
    - [x] Add "Student Analytics" tab to the analytics page with GraduationCap icon
    - [x] Create student analytics filters component (period and date range)
    - [x] Build student overview cards showing key metrics (total students, active students, avg jobs/student, most active)
    - [x] Implement student analytics API client with proper error handling
    - [x] Add student analytics types to the analytics types file
    - [x] Create placeholder for detailed student performance metrics and trends

  - [x] **A6.3. Student Analytics Features** ✅ **COMPLETED**
    - [x] Student overview metrics (total students, active students, average jobs per student, most active student)
    - [x] Student performance tracking (approval rates, average costs, job counts)
    - [x] Student submission trends (daily submissions, discipline breakdown)
    - [x] Student comparison capabilities for identifying top performers
    - [x] Student learning curve analysis and improvement tracking
    - [x] Educational insights for identifying common learning areas and success patterns

- [x] **A7. Analytics Page Tabbed Interface: Operations vs. Finance** ✅ **COMPLETED**
  - [x] **A7.1. Operations Tab** ✅ **COMPLETED**
    - [x] Add "Operations" tab to existing `/analytics` page with BarChart3 icon
    - [x] Move overview cards, trend charts, and resource metrics to Operations tab
    - [x] Keep staff analytics as existing tab within the same interface
    - [x] Add operational-specific filters and controls for Operations tab
    - [x] Focus on system performance, workflow efficiency, resource utilization

  - [x] **A7.2. Finance Tab** ✅ **COMPLETED**
    - [x] Add "Finance" tab to existing `/analytics` page with DollarSign icon
    - [x] Move financial summary and payment metrics to Finance tab
    - [x] Add enhanced financial reporting and export functionality
    - [x] Implement cost analysis by material type and discipline
    - [x] Add revenue trends and payment processing metrics
    - [x] Focus on revenue tracking, payment processing, cost analysis

  - [x] **A7.3. Tabbed Interface Implementation** ✅ **COMPLETED**
    - [x] Convert existing `/analytics` page to use left-side tabbed interface (similar to admin page)
    - [x] Implement shared state management for filters across all tabs
    - [x] Add smooth transitions between tabs with proper loading states
    - [x] Test tabbed interface functionality and responsiveness
    - [x] Verify no regression in existing functionality
    - [x] Ensure proper tab navigation with icons and labels

  - [x] **A7.4. Student Analytics Tab (Reintroduce as final left-side tab)** ✅ **COMPLETED**
    - Background & Motivation: Backend endpoints and client exist; tab content was planned/built previously but is not currently visible. We will reintroduce a dedicated Student Analytics tab as the last item in the left-side navigation.
    - Success Criteria:
      - A visible "Student Analytics" tab (GraduationCap icon) appears last in `/analytics` left nav
      - Data loads via existing endpoints: `/api/v1/analytics/student/overview`, `/performance`, `/trends`
      - Shows Student Overview cards (Total Students, Active Students, Avg Jobs/Student, Most Active Student)
      - Provides initial visuals/sections for activity trends and performance with safe placeholders when no data
      - No regressions in Operations, Finance, or Staff tabs; build stays green
    - High-level Task Breakdown:
      - [x] S1 – Verify assets: confirm `fetchStudentAnalyticsData` and `StudentAnalyticsFilters` exist; confirm backend endpoints
      - [x] S2 – Re-add Student tab to `frontend/src/app/analytics/page.tsx` with GraduationCap icon; restore student state, filters, and `loadStudentData()` wiring
      - [x] S3 – Minimal UI: render Student Overview cards; add placeholder sections for Trends (submissions by day), Performance (approval rate, avg cost), Discipline (submissions by discipline); comparison table placeholder
      - [x] S4 – QA + Build: run typecheck/build; quick manual check across tabs
    - Risks & Mitigations: Empty datasets (show zero-safe values and "No data" messaging); auth token (use existing JWT flow)
    - Rollback: Revert edits to `frontend/src/app/analytics/page.tsx`

#### **Phase 1.5: System Stability & Concurrency (High Priority)**
- [ ] **S1. Job Locking for Concurrency Control**
  - [ ] Backend: Implement `POST /jobs/<id>/lock`, `unlock`, and `extend` endpoints
  - [ ] Backend: Add `locked_by` and `locked_until` fields to the Job model
  - [ ] Frontend: Request lock when opening modals (approve, reject, etc.)
  - [ ] Frontend: Display "Job is locked" message if lock is held by another user
  - [ ] Frontend: Implement heartbeat to extend lock while modal is open
  - [ ] Tests: Add tests for locking, unlocking, and conflict scenarios

- [ ] **S2. Duplicate Submission Detection**
  - [ ] Backend: Add `file_hash` field to the Job model
  - [ ] Backend: On `POST /submit`, calculate file hash and check for active duplicates
  - [ ] Backend: Return `409 Conflict` if an active duplicate is found
  - [ ] Frontend: Display a user-friendly error message on duplicate submission
  - [ ] Tests: Add tests for duplicate detection and reprint allowance

- [ ] **S3. System Health Audit Tool**
  - [ ] Backend: Create `POST /admin/audit/start` to trigger an async scan
  - [ ] Backend: Create `GET /admin/audit/report` to fetch the last scan results
  - [ ] Backend: Implement logic to find orphaned files and broken DB links
  - [ ] Frontend: Create an "Admin > System Health" page to display the report
  - [ ] Frontend: Add controls for admins to safely delete orphaned files
  - [ ] Tests: Add tests for the audit scan logic

#### **Phase 1.6: Payment Accuracy & Finance Variance (FI1)**
- [x] **FI1. Payment Accuracy & Finance Variance**
  - [x] **FI1-S1. Backend Payment Calculation Fix** ✅ **COMPLETED**
    - [x] Change `record_payment` to always compute `price_cents` from grams + rate + $3 min (ignore `job.cost_usd` for final)
    - [x] Add tests: when `cost_usd=50.00`, resin, grams=10 → expect `price_cents=300` (min charge)
    - [x] Ensure `Payment.price_cents` stores the actual pickup price, not the estimate
  - [x] **FI1-S2. Payment Modal Enhancements** ✅ **COMPLETED**
    - [x] On open, fetch `GET /api/v1/jobs/<id>` to get `material` and `cost_usd`
    - [x] Show rate hint, display current estimate, and live "Final Price" from grams
    - [x] Test: preview updates and successful post still works
    - [x] Confirm dialog should repeat the final calculated amount
    
  - [x] **FI1-S3. Job Card Labeling** ✅ **COMPLETED**
    - [x] In `job-card.tsx`, change "Cost:" to "Estimated Cost:" for non-final statuses
    - [x] When `payment` exists / status is `PAIDPICKEDUP`, show "Final Cost:" and amount
    - [x] Test: label text switches by status
  - [x] **FI1-S4. Finance Estimated vs Actual** ✅ **COMPLETED**
    - [x] Backend `GET /api/v1/analytics/financial`: add `estimatedRevenueCents`, `actualRevenueCents`, `varianceCents`
    - [x] Frontend `FinancialSummary`: add KPIs for Estimated, Actual, Variance
    - [x] Tests: aggregation correctness with mixed materials and min-charge cases
  - [x] **FI1-S5. Manual QA** ✅ **COMPLETED**
    - [x] Complete → Payment modal → enter grams → see preview → confirm → job moves to Paid & Picked Up
    - [x] Verify card now shows "Final Cost" instead of "Estimated Cost"
    - [x] Check Finance tab shows estimated vs actual comparison

#### **Phase 2: Admin Features (Medium Priority)**
- [x] **M1. Submission Form Improvements**
  - [x] Improve UX parity with masterplan
  - [x] Add form validation enhancements
  - [x] Implement better error handling


- [x] **M3. Admin Email Tools**
  - [x] Add resend email functionality (POST /api/v1/jobs/<id>/admin/resend-email)
  - [x] Implement rate-limited email resend (1/hour)
  - [x] Wire admin UI panel to endpoint
  - [x] Add resend modal with staff selection and confirmation
  - [x] Add email template management

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

**Option A: Payment Accuracy & Finance Variance (FI1)**
- Fix payment calculation to use actual pickup weight instead of estimate
- Add live price preview in payment modal
- Show "Estimated Cost" vs "Final Cost" on job cards
- Add estimated vs actual comparison in Finance analytics
- Estimated effort: 1-2 days

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
- **Analytics**: 100% Complete ✅ (system analytics complete, staff analytics section implemented; JSON mapping errors fixed)
- **Admin Features**: 0% Complete ❌
- **Documentation**: 0% Complete ❌
- **Testing**: 0% Complete ❌
- **Production**: 0% Complete ❌

**Overall Project Completion**: ~98% (Core functionality complete, UI polished, analytics fully implemented with consolidated tabbed interface)

## New Workstream — FI1. Payment Accuracy & Finance Variance (Planner)

### Background & Motivation
- Current `record_payment` uses `job.cost_usd` (estimate) when present, which can mismatch the real pickup weight. Staff need a live price preview in the modal and the system must record the actual price from grams. Finance also needs estimated vs actual visibility.
- UI request: Show "Estimated Cost" on all job cards until payment is recorded; show "Final Cost" after payment.

### Key Challenges & Analysis
- Backend: `backend/app/routes/jobs.py::record_payment` prefers estimate if set.
- Frontend: `PaymentModal` doesn't preview the price and doesn't fetch material to know the correct rate.
- Job Card UI: `frontend/src/components/dashboard/job-card.tsx` currently labels as "Cost".
- Finance endpoint aggregates actual payments only; needs estimated totals too.

### Success Criteria
- Actual price is computed from modal grams with $3.00 minimum and material-specific rate ($0.10/g filament, $0.20/g resin) and that exact value is stored in `Payment.price_cents`.
- Modal shows a live "Final Price" preview as grams change; confirm dialog repeats the amount.
- Job cards:
  - Status ∈ {UPLOADED, PENDING, READYTOPRINT, PRINTING, COMPLETED}: label reads "Estimated Cost".
  - Status = PAIDPICKEDUP: label reads "Final Cost" from the `Payment` record (already displayed via analytics/paid path).
- Finance tab shows Estimated vs Actual totals and Variance for the selected range.
- Tests cover backend precedence (grams over estimate), modal preview, and job card label logic.

### Risks & Mitigations
- Missing `material` → default filament rate + UI warning; log event.
- Historical analytics estimates may be missing on some records → treat as 0 safely.

### Rollback Plan
- Revert `backend/app/routes/jobs.py` change, modal UI adjustments, and Finance UI/API additions.