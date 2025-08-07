# 3D Print Management System - Comprehensive Build Plan

## Background and Motivation

Based on the analysis of `masterplan.md`, `Rebuild.md`, `project-info.md`, and the system architecture diagrams, we are building a complete 3D Print Management System from absolute scratch. This system is designed for academic/makerspace environments with the following key requirements:

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
- **Beginner-friendly implementation** with clear, step-by-step guidance
- **API-first design** with clear separation of concerns
- **Multi-user environment** supporting up to 2 staff workstations
- **File resilience** through standardized naming and metadata tracking
- **Professional UI/UX** following modern design patterns
- **Comprehensive error handling** and recovery mechanisms

## Key Challenges and Analysis

### Technical Challenges:
1. **File System Integrity**: Ensuring atomic file operations and recovery from partial failures
2. **Multi-User Concurrency**: Preventing race conditions between staff workstations
3. **Protocol Handler Security**: Validating file paths and preventing directory traversal attacks
4. **Email Delivery Reliability**: Handling SMTP failures and token expiration
5. **Database Consistency**: Maintaining referential integrity across complex workflows

### Operational Challenges:
1. **Staff Training**: Ensuring proper use of attribution system and workflow procedures
2. **Network Storage**: Coordinating shared storage access across multiple machines
3. **Backup and Recovery**: Implementing comprehensive data protection strategies
4. **System Monitoring**: Detecting and responding to operational issues
5. **Data Retention**: Managing archival and cleanup processes

### User Experience Challenges:
1. **Form Validation**: Real-time client-side validation with clear error feedback
2. **Real-time Updates**: Auto-refreshing dashboard with sound notifications
3. **Mobile Responsiveness**: Ensuring functionality across all device types
4. **Accessibility**: WCAG 2.1 compliance for inclusive design
5. **Error Recovery**: Clear messaging and recovery paths for all failure scenarios

## High-level Task Breakdown

### Phase 1: Environment Setup & Foundation (Week 1)
**Success Criteria**: Complete development environment with Docker containers running

1. **Project Structure Creation**
   - Create directory structure following masterplan specifications
   - Initialize Git repository with proper .gitignore
   - Set up Docker Compose configuration
   - Create initial documentation structure

2. **Backend Foundation Setup**
   - Install Python dependencies (Flask, SQLAlchemy, etc.)
   - Create Flask application factory
   - Set up database models (Job, Event, Staff, Payment)
   - Configure database migrations with Flask-Migrate
   - Implement basic authentication system

3. **Frontend Foundation Setup**
   - Initialize Next.js project with TypeScript
   - Install UI dependencies (Tailwind CSS, shadcn/ui)
   - Create authentication context and API client
   - Set up basic routing structure
   - Configure development environment

4. **Database Initialization**
   - Create PostgreSQL container
   - Run initial migrations
   - Seed database with test data
   - Verify database connectivity

### Phase 2: Core API Development (Week 2)
**Success Criteria**: All essential API endpoints functional with proper error handling

1. **Authentication & Authorization**
   - Implement workstation login system
   - Create JWT token management
   - Add staff management endpoints
   - Implement rate limiting and security measures

2. **Job Management API**
   - Create job CRUD operations
   - Implement status transition logic
   - Add file upload and validation
   - Create job search and filtering

3. **Student Submission API**
   - Implement file upload with validation
   - Add duplicate detection logic
   - Create email confirmation system
   - Handle form validation and error responses

4. **Event Logging System**
   - Implement comprehensive event logging
   - Add staff attribution tracking
   - Create audit trail queries
   - Add event export functionality

### Phase 3: Frontend Core Features (Week 3)
**Success Criteria**: Complete student submission form and basic staff dashboard

1. **Student Submission Interface**
   - [x] Create `SubmissionForm` component in `frontend/src/components/submission/submission-form.tsx` with required fields:
       * Student Name (text), Email (email), Discipline (dropdown), Class Number (text), Print Method (dropdown), Color Preference (conditional dropdown), Printer Selection (dropdown), Minimum Charge Consent (boolean), File Upload (file input with progress).
       * Success Criteria: All inputs render correctly with proper labels.
       * Test: Unit tests verify presence and initial state of each input.
   - [x] Implement real-time client-side validation:
       * Disable Color dropdown until Print Method selected.
       * Validate email format on blur; file type/size on selection.
       * Show error messages and block submission when invalid.
       * Success Criteria: Invalid fields display errors immediately.
       * Test: Unit tests for validation rules; manual tests with invalid inputs.
   - [x] Integrate API call to `POST /api/v1/submit`:
       * Display loading indicator during submission.
       * On 201: capture job ID and trigger redirect to `/submit/success?job=<id>`.
       * On 400/409/429: display inline error messages.
       * Success Criteria: Form submits and handles responses correctly.
       * Test: Manual form submission scenarios (valid + error flows).
   - [x] Create success and error pages:
       * Success Page (`/submit/success?job=<id>`) shows confirmation and instructions.
       * Error states remain on form with error banners.
       * Success Criteria: Redirect and error flows function as intended.
       * Test: Manual verification of redirection and error display.
   - [x] Add email confirmation handling:
       * Create student confirmation page (`frontend/src/app/confirm/[token]/page.tsx`).
       * Parses `token` from route param and POSTs to `/api/v1/confirm/<token>`.
       * Shows success, expired, or error states appropriately.
       * Success Criteria: student confirmation flow works end-to-end.
       * Test: manual link-click verification at `/confirm/<token>`.

### Phase 3.1: UI/UX Refinement (Submission Form)

**Goal**: Update the submission form to match the design mockup and masterplan specifications exactly.

1. **Update Submission Form Layout and Styling** 
   - **Action**: Complete visual redesign of `frontend/src/components/submission/submission-form.tsx` to match the provided image mockup
   - **Visual Updates Needed**:
     * Add comprehensive form introduction/warning text at top as specified in masterplan lines 532-533
     * Update form styling to match mockup (single column layout, proper spacing)
     * Change page title to "3D Print Submission" 
     * Add subtitle text "Submit your 3D model for printing. Please ensure you've reviewed our guidelines before proceeding."
     * Style the important warning section with yellow background and warning icon
   - **Success Criteria**: Form visually matches the provided mockup image
   - **Test**: Manual visual comparison with mockup image

2. **Restructure Student Name Field**
   - **Action**: Change from separate first/last name inputs to single "Full Name" field as per masterplan line 535
   - **Implementation**: Replace firstName/lastName states with single studentName state
   - **Success Criteria**: Single name field present and functional
   - **Test**: Form submission includes full name as student_name in API call

3. **Add Print Method Descriptions**
   - **Action**: Update Print Method dropdown to include contextual descriptions as specified in masterplan lines 539-541
   - **Implementation**: 
     * Add descriptions for Filament: "Good resolution, suitable for simpler models. Fast. Best For: Medium items. Cost: Least expensive."
     * Add descriptions for Resin: "Super high resolution and detail. Slow. Best For: Small items. Cost: More expensive."
   - **Success Criteria**: Descriptions visible in dropdown options or as help text
   - **Test**: Visual verification that descriptions are displayed appropriately

4. **Add Printer Dimensions Information Section**
   - **Action**: Implement informational printer dimensions section as specified in masterplan lines 545-546
   - **Implementation**: 
     * Add read-only informational section with complete scaling guidance text
     * Include all printer specifications: Filament printers (Prusa MK4S, Prusa XL, Raise3D Pro 2 Plus) and Resin printer (Formlabs Form 3)
     * Add dimension details: "Will your model fit on our printers? Please check the dimensions (W x D x H):"
     * Include scaling warnings about STL/OBJ export requirements
   - **Success Criteria**: Information section displays all printer specifications clearly
   - **Test**: Visual verification that all printer dimensions and guidance text are present

5. **Update Form Validation and Error Handling**
   - **Action**: Ensure all validation matches masterplan requirements
   - **Implementation**:
     * Validate full name (2-100 characters)
     * Validate email format (max 100 characters)
     * Validate class number format (max 50 characters, allows "N/A")
     * Ensure all required fields are validated
     * Add proper error scrolling and visual feedback
   - **Success Criteria**: All validation rules work as specified in masterplan
   - **Test**: Manual testing of all validation scenarios

6. **Polish Visual Design and Responsiveness** 
   - **Action**: Final polish to ensure form matches mockup exactly
   - **Implementation**:
     * Adjust spacing, typography, colors to match mockup
     * Ensure mobile responsiveness
     * Add proper focus states and accessibility features
     * Verify submit button styling and loading states
     * Refine minimum charge consent checkbox styling to match mockup
   - **Success Criteria**: Form is visually polished and matches mockup on all screen sizes
   - **Test**: Cross-browser and device testing

2. **Staff Dashboard Foundation**
   - [x] Build `DashboardLayout` in `frontend/src/app/dashboard/layout.tsx`:
       * Header with logo and workstation display.
       * Status tabs (UPLOADED, PENDING, etc.) for navigation.
       * Success Criteria: Layout renders and wraps page content.
       * Test: Unit tests for layout; manual inspection in browser.
   - [x] Implement `JobList` component and data fetching:
       * Use `api.getJobs({status,search,filters})` to fetch jobs.
       * Render `JobCard` components (`components/dashboard/job-card.tsx`).
       * Success Criteria: Job cards display correct data.
       * Test: Mock API in unit tests; manual verify job list.
   - [x] Add filter controls:
       * Inputs: search bar, dropdowns for printer/discipline, status tabs.
       * Update query params and refetch list on change.
       * Success Criteria: Filters dynamically update list.
       * Test: Integration tests; manual filter usage. ✅ PASS - Manual verification shows search, printer, discipline, and status filters all update URL and re-fetch job list as expected.

3. **Job Management Modals**
   - [ ] Approval Modal (`ApprovalModal` in `components/dashboard/modals/approval-modal.tsx`):
       * Fetch candidate files via `GET /jobs/<id>/candidate-files`.
       * Radio list for file selection; inputs for weight and time.
       * Display calculated cost; staff attribution dropdown.
       * Success Criteria: Modal opens, inputs validate, submit calls `/jobs/:id/approve`.
       * Test: Unit tests for modal state; manual approval flow.
   - [ ] Rejection Modal (`RejectionModal` in `components/dashboard/modals/rejection-modal.tsx`):
       * Checkbox list of rejection reasons; custom reason textarea.
       * Staff attribution dropdown.
       * Success Criteria: Modal validation and submit to `/jobs/:id/reject`.
       * Test: Unit tests for validation; manual rejection flow.
   - [ ] Status Change Modals (Printing, Complete, Pickup):
       * Confirmation dialogs with staff attribution dropdown.
       * Submit to respective endpoints (`/mark-printing`, `/mark-complete`, `/mark-picked-up`).
       * Success Criteria: Status updates and UI refresh.
       * Test: Unit tests; manual status change flows.
   - [ ] Create notes editing interface:
       * Inline `notes` textarea in job detail modal.
       * PATCH `/api/v1/jobs/:id/notes` on save.
       * Success Criteria: notes persist and display after reload.
       * Test: unit tests & manual notes edit flow.

4. **Real-time Updates**
   - [ ] Create `useAutoRefresh` hook (`frontend/src/lib/hooks/useAutoRefresh.ts`):
       * Accepts callback and interval (default 45s).
       * Success Criteria: Callback invoked at each interval.
       * Test: Unit test for timing; manual observation.
   - [ ] Audio Notification System:
       * Integrate `Audio` API to play sound when a new job arrives.
       * Provide toggle control in UI; persist setting.
       * Success Criteria: Sound plays on new job; toggle persists across sessions.
       * Test: Unit test mock Audio; manual audio verification.
   - [ ] Visual Alert Indicators and Job Age Tracking:
       * "NEW" pulsing badge for unreviewed jobs in `JobCard`.
       * Age label color-coded: green <24h, yellow <48h, etc.
       * Success Criteria: Badges and colors display correctly and update over time.
       * Test: Storybook snapshots; manual visual test.
   - [ ] Staff Acknowledgment Action:
       * Add "Mark as Reviewed" button to `JobCard`.
       * On click, POST to `/jobs/:id/review` with `reviewed: true`.
       * Success Criteria: Badge removed and job marked reviewed.
       * Test: Unit test; manual acknowledgment flow.

### Phase 4: Advanced Features (Week 4)
**Success Criteria**: Complete workflow with email notifications and file management

1. **Email Service Integration**
   - Implement Flask-Mail configuration
   - Create email templates
   - Add background task processing
   - Handle email delivery failures
   - Add email resend functionality

2. **File Management System**
   - Implement file upload processing
   - Create metadata.json generation
   - Add file movement between directories
   - Implement thumbnail generation
   - Add file integrity validation

3. **Payment & Pickup Workflow**
   - Create payment recording interface
   - Implement cost calculation logic
   - Add pickup confirmation system
   - Create financial reporting
   - Add payment history tracking

4. **Protocol Handler Development**
   - Create SlicerOpener.py application
   - Implement security validation
   - Add slicer detection and selection
   - Create Windows registry setup
   - Add error handling and logging

### Phase 5: Advanced Dashboard Features (Week 5)
**Success Criteria**: Complete operational dashboard with analytics and admin features

1. **Enhanced Dashboard Features**
   - Add real-time statistics
   - Implement advanced filtering
   - Create job search functionality
   - Add bulk operations
   - Implement keyboard shortcuts

2. **Analytics & Reporting**
   - Create analytics dashboard
   - Implement trend visualization
   - Add resource utilization metrics
   - Create financial reporting
   - Add export functionality

3. **Admin Override System**
   - Create admin action modals
   - Implement status override functionality
   - Add manual confirmation options
   - Create system health monitoring
   - Add data integrity auditing

4. **System Health & Monitoring**
   - Implement health check endpoints
   - Add system status monitoring
   - Create backup verification
   - Add error tracking and alerting
   - Implement performance monitoring

### Phase 6: Testing & Quality Assurance (Week 6)
**Success Criteria**: Comprehensive testing with all features validated

1. **API Testing**
   - Create unit tests for all endpoints
   - Implement integration tests
   - Add error scenario testing
   - Test authentication and authorization
   - Validate file operations

2. **Frontend Testing**
   - Test form validation and submission
   - Validate real-time updates
   - Test modal interactions
   - Verify responsive design
   - Test accessibility features

3. **End-to-End Testing**
   - Test complete job workflows
   - Validate email delivery
   - Test file protocol handler
   - Verify multi-user scenarios
   - Test error recovery paths

4. **Performance Testing**
   - Test concurrent user access
   - Validate file upload performance
   - Test database query optimization
   - Verify memory usage
   - Test network resilience

### Phase 7: Deployment & Documentation (Week 7)
**Success Criteria**: Production-ready system with comprehensive documentation

1. **Production Deployment**
   - Create production Docker configuration
   - Set up environment variables
   - Configure SSL certificates
   - Set up monitoring and logging
   - Create backup procedures

2. **Documentation**
   - Create user manuals
   - Write technical documentation
   - Add API documentation
   - Create deployment guides
   - Write troubleshooting guides

3. **Training Materials**
   - Create staff training videos
   - Write operational procedures
   - Add troubleshooting guides
   - Create FAQ documentation
   - Write maintenance procedures

4. **Final Testing & Validation**
   - Conduct user acceptance testing
   - Validate all workflows
   - Test backup and recovery
   - Verify security measures
   - Test disaster recovery procedures

## Project Status Board

### Phase 1: Environment Setup & Foundation
- [x] Project structure creation
- [x] Backend foundation setup
- [x] Frontend foundation setup
- [x] Database initialization
  - [x] Configure Flask-Migrate
  - [x] Generate initial migration
  - [x] Apply migration
  - [x] Create seeding script
  - [x] Seed database

### Phase 2: Core API Development
- [x] Authentication & authorization
  - [x] Implement workstation login endpoint
  - [x] Test login endpoint functionality
  - [x] Implement JWT generation and validation
  - [x] Create token-required decorator
  - [x] Implement staff management endpoints (CRUD)
  - [x] Add rate limiting to auth endpoints
- [x] Job management API
- [x] Student submission API
- [x] Event logging system

### Phase 3: Frontend Core Features
- [x] Student submission interface
- [x] **UI/UX Refinement (Submission Form) - COMPLETE**
  - [x] Update submission form layout and styling to match mockup
  - [ ] Restructure student name field (single full name) — cancelled (retaining separate fields)
  - [x] Add print method descriptions
  - [x] Add printer dimensions information section (moved above printer selection)
  - [x] Added scaling confirmation checkbox for STL/OBJ files
  - [x] Update form validation and error handling
  - [x] Polish visual design and responsiveness
- [x] Staff dashboard foundation (layout, page stub, and JobList created)
- [ ] Job management modals
- [ ] Real-time updates

### Phase 4: Advanced Features
- [ ] Email service integration
- [ ] File management system
- [ ] Payment & pickup workflow
- [ ] Protocol handler development

### Phase 5: Advanced Dashboard Features
- [ ] Enhanced dashboard features
- [ ] Analytics & reporting
- [ ] Admin override system
- [ ] System health & monitoring

### Phase 6: Testing & Quality Assurance
- [ ] API testing
- [ ] Frontend testing
- [ ] End-to-End testing
- [ ] Performance testing

### Phase 7: Deployment & Documentation
- [ ] Production deployment
- [ ] Documentation
- [ ] Training materials
- [ ] Final testing & validation

## Current Status / Progress Tracking

**Current Phase**: Phase 3.1 - UI/UX Refinement (Submission Form)
**Next Milestone**: Complete submission form redesign to match mockup
**Estimated Completion**: 6 weeks from start date

### Completed Tasks:
- [x] Comprehensive analysis of masterplan.md
- [x] Review of Rebuild.md implementation guide
- [x] Analysis of project-info.md requirements
- [x] Examination of system architecture diagrams
- [x] Creation of exhaustive build plan
- [x] Project structure creation
- [x] Backend foundation setup (Flask app factory, models, requirements)
- [x] Frontend foundation setup (Next.js, Tailwind CSS, basic structure)
- [x] Git repository initialization
- [x] Docker Compose configuration
- [x] Docker container builds successful
- [x] **Phase 1: Environment Setup & Foundation COMPLETE**
- [x] Fixed 404 error preventing web access to the frontend application.
- [x] Provided pgAdmin connection instructions and removed default server registration

### In Progress:
- [ ] Phase 3.1: UI/UX Refinement (Submission Form) - Design update to match mockup

### Blockers:
- None currently identified

### Phase 1 Success Metrics Achieved:
- [x] All Docker containers running successfully
- [x] Frontend application loading (Next.js dev server)
- [x] Backend application loading (Flask debug server)
- [x] Database container running (PostgreSQL)
- [x] Redis container running (for background tasks)
- [x] Basic project structure established
- [x] Git repository initialized with proper .gitignore
- [x] Database initialized and seeded

### Execution Log: Database Connectivity Fix
- Provided user instructions to configure pgAdmin server connection:
  * In pgAdmin, right-click on "Servers" and select "Create" > "Server..."
  * Under the "General" tab, set:
    - Name: 3D Print System DB
  * Under the "Connection" tab, set:
    - Host: localhost
    - Port: 5432
    - Maintenance database: 3d_print_system
    - Username: fablab_user
    - Password: fablab
  * Click "Save" to establish the connection and verify that you can see the database objects.

## Executor's Feedback or Assistance Requests

### Critical Issue Analysis: Network Connectivity Problems

**Context**: User reports "Network error, please try again" on form submission and "Failed to load jobs" in dashboard.

**Root Cause Analysis**:
1. **Backend API is running** - Container up on port 5000
2. **Frontend is running** - Next.js server accessible on port 3000  
3. **Authentication required** - Backend `/api/v1/jobs` endpoint requires JWT token (returns "Token is missing")
4. **API routing issue** - Frontend making calls to `/api/v1/*` but no Next.js API route handler exists

**Critical Problem Identified**: 
- Frontend components are calling `/api/v1/submit` and `/api/v1/jobs` directly
- These calls go to Next.js (port 3000) instead of Flask backend (port 5000)
- Next.js has no API routes configured, causing network errors
- Need API proxy configuration or base URL setup to route calls to Flask backend

**Impact**: 
- **BLOCKING** - Core functionality completely broken
- Student submissions fail entirely
- Staff dashboard cannot load any data
- System is non-functional for primary use cases

**Recommendation**: **STOP current work and fix immediately**. This is a fundamental architecture issue that blocks all API-dependent functionality. Cannot proceed with job management modals when basic API communication is broken.

**Next Action Required**: Configure API routing between Next.js frontend and Flask backend.

### Critical Issue Analysis: Database Connectivity Problems - RESOLVED ✅
**Context**: User updated pgAdmin and PostgreSQL; unable to connect to the database using the default `postgres` user; when Docker is running, authentication fails; when Docker is off, connection times out.
**Root Cause Analysis**:
1. The default `postgres` superuser has no password configured in the Docker container; the project uses a custom user `fablab_user` with password `fablab`.
2. When Docker is running, the Postgres container exposes port 5432 but only recognizes `fablab_user`, not `postgres`.
3. When Docker is not running, no Postgres server is listening on port 5432, causing connection timeouts.
**Resolution Applied**:
- ✅ User successfully configured pgAdmin with correct credentials (`fablab_user`/`fablab`)
- ✅ Removed conflicting PostgreSQL 17 server registration from pgAdmin
- ✅ Verified database schema is properly set up with all required tables (alembic_version, event, job, payment, staff)
- ✅ Confirmed Docker containers are running and database is active
**Status**: RESOLVED - Database connectivity fully functional

## Lessons

- Include info useful for debugging in the program output.
- Read the file before you try to edit it.
- If there are vulnerabilities that appear in the terminal, run npm audit before proceeding
- Always ask before using the -force git command