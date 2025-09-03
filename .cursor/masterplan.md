# 3D Print System Project Plan (Beginner-Friendly Flask API + Next.js Edition)

## 1. Project Overview
This project is a fully functional Flask-based 3D print job management system, specifically designed for beginners. The system is tailored for an academic/makerspace setting with up to three staff members operating concurrently on separate computers. It uses a **workstation-based login system with per-action staff attribution** and is designed with safeguards to prevent data conflicts and race conditions inherent in a multi-user environment. The system handles the complete workflow from student submission to completion, with comprehensive file tracking, staff approval, and the ability to open the exact uploaded files directly in local applications.

> **Key Design Principle**: This project prioritizes **beginner-friendly implementation** with clear, step-by-step guidance and minimal complexity. Built from a basic working foundation with iterative feature additions, the system maintains simplicity while delivering comprehensive functionality.

> **Note:** The system is designed for a multi-user environment and is deployed using Docker. The core services (API, database, background workers) run as containers on a single host machine. Staff can access the system from up to three lab computers via a web browser. All computers must have access to the same shared network storage for file management, and the `SlicerOpener` protocol handler must be installed locally on each.

The project has replaced potentially ad-hoc or manual 3D print request systems with a **centralized, API-driven, and workflow-oriented platform.** It uses a **Flask API-only backend** with a **Next.js frontend**, following a clear separation of concerns where the backend handles all business logic and the frontend consumes REST APIs. It delivers clarity, efficiency, accurate file tracking, and a **strong, non-fragile foundation**, addressing the complexities of file changes introduced by slicer software and ensuring resilience.

### 1.1.1 Academic Context & University Integration
The system is specifically designed for university academic environments with the following characteristics:

**Academic Discipline Support**: The system supports 7 primary academic disciplines as evidenced in the frontend submission form (`frontend/src/components/submission/submission-form.tsx`):
- Art
- Architecture  
- Landscape Architecture
- Interior Design
- Engineering
- Hobby/Personal
- Other

**Course Integration**: Students must provide class numbers (e.g., "ARCH 4000") or "N/A" for non-course projects, enabling academic tracking and reporting.

**University Payment System**: The system integrates with university Tiger-Cash payment system as evidenced in the Payment model (`backend/app/models/payment.py`):
- `txn_no` field stores Tiger-Cash transaction numbers
- Weight-based pricing: $0.10/gram for filament, $0.20/gram for resin
- $3.00 minimum charge enforced across all jobs
- Manual transaction recording with staff attribution

**Educational Workflow**: The system includes comprehensive educational content and warnings:
- Mandatory liability disclaimer referencing "Additive Manufacturing Moodle page"
- Detailed printer dimension guidance for student education
- Material-specific descriptions and cost information
- File format and scaling requirements clearly communicated

### 1.1.2 System Boundaries & Integration Points
**External Dependencies**:
- **Email System**: Office 365 SMTP integration for automated notifications
- **File Storage**: Network-mounted shared storage accessible by all workstations
- **Slicer Software**: Local installation of PrusaSlicer, PreForm, or other slicer applications
- **University Network**: Integration with campus network infrastructure and security policies

**Internal Boundaries**:
- **No External APIs**: System operates independently without third-party service dependencies
- **Self-Contained**: All business logic, file management, and user interface contained within the system
- **Protocol Handler**: Custom `3dprint://` protocol for direct file opening (implemented in `SlicerOpener/SlicerOpener.py`)

**Data Isolation**:
- **Student Data**: Minimal PII collection (name, email, discipline, class number)
- **Staff Attribution**: Full audit trail with workstation and staff member tracking
- **File Security**: Comprehensive validation and path traversal prevention

### 1.1.3 Operational Constraints & Assumptions
**Physical Infrastructure**:
- **Network Storage**: All computers must mount shared storage at identical paths
- **Workstation Limits**: Maximum of 2 concurrent staff workstations supported
- **Printer Integration**: Manual printer operation with system tracking only
- **Protocol Handler**: Must be installed locally on each staff computer

**User Behavior Assumptions**:
- **Staff Training**: Staff members understand basic 3D printing concepts and slicer software
- **Student Education**: Students have access to educational materials (Moodle page referenced)
- **File Management**: Staff will use slicer software to create/modify files in designated directories
- **Payment Processing**: Manual Tiger-Cash transactions with staff recording

**Technical Constraints**:
- **File Size Limits**: 50MB maximum file upload size
- **Rate Limiting**: 3 submissions per IP per hour, 10 login attempts per IP per hour
- **Session Duration**: Workstation sessions configured for full workday duration
- **Concurrency**: Job locking system prevents simultaneous edits by multiple staff

### 1.2.1 Evidence Audit Trail
**Academic Context Evidence**:
- **Discipline Options**: Verified 7 disciplines in `frontend/src/components/submission/submission-form.tsx`
- **Course Integration**: Confirmed class_number field in Job model (`backend/app/models/job.py`)
- **Payment System**: Validated Tiger-Cash integration in Payment model (`backend/app/models/payment.py`)
- **Educational Content**: Confirmed liability disclaimer and printer guidance in submission form

**System Boundaries Evidence**:
- **Protocol Handler**: Verified implementation in `SlicerOpener/SlicerOpener.py`
- **File Security**: Confirmed validation in `backend/app/services/infrastructure/atomic_file_service.py`
- **Rate Limiting**: Verified in `backend/app/routes/auth.py` and `backend/app/routes/submit.py`
- **Concurrency Control**: Confirmed job locking fields in Job model

**Operational Constraints Evidence**:
- **File Size Limits**: Verified 50MB limit in submission validation
- **Session Management**: Confirmed workstation authentication in auth routes
- **Payment Processing**: Validated weight-based pricing in payment service
- **Network Storage**: Confirmed path consistency requirements in deployment docs

## 1.2 User Roles & Personas
The system serves two primary user roles:
●	**Students**: Users submitting 3D models for printing. They use a simple interface for uploading files, providing details, and tracking job progress through email notifications.
●	**Staff/Admins**: Users managing the print queue, printers, and the system itself. They use comprehensive tools for reviewing submissions, taking notes about jobs, approving/rejecting jobs, managing files, operating slicer software, tracking job status, and overseeing system health.

## 2. Core Features & Requirements

### 2.1 Core Features (Beginner-Friendly Implementation)

**Essential System Features**:
1.  **Student submission process**: Provides comprehensive 3D model file upload (.stl, .obj, .3mf) with metadata collection (name, email, print_method, color, discipline, course_number) via a **Next.js form** with full client-side and server-side validation.
2.  **Staff approval workflow**: Delivers complete job review, file slicing, and approve/reject capabilities via a **Next.js dashboard** with mandatory staff attribution for all actions.
3.  **Dynamic catalog management**: **NEWLY IMPLEMENTED** - Complete admin dashboard for managing printers, materials, and colors with immediate reflection in student submission forms. Eliminates hardcoded values and enables easy addition of new equipment and materials.
4.  **File lifecycle management**: Manages original files through status-based directory structure with `metadata.json` for resilience and atomic file operations.
5.  **Job status tracking**: Complete progression through UPLOADED → PENDING → READYTOPRINT → PRINTING → COMPLETED → PAIDPICKEDUP → ARCHIVED, and REJECTED → ARCHIVED workflows.
6.  **Workstation Authentication & Action Attribution**: Operational 3-workstation shared password system with mandatory per-action user attribution providing both ease of use and full accountability.
7.  **Email notifications**: **Asynchronously** delivers automated updates to students for approvals, rejections, and completions via RQ background tasks with HTML templates.
8.  **Direct file opening**: Functional `print3d://` protocol handler opens files in local slicer software with comprehensive security validation.
9.  **Payment & pickup workflow**: Complete weight-based payment calculation with manual Tiger-Cash transaction recording and pickup confirmation functionality.
10. **Financial reporting**: Operational CSV export system with revenue and transaction data for administrative oversight.
11. **Analytics dashboard**: Live operational insights, resource utilization metrics, and financial performance tracking with comprehensive endpoints.

**Advanced Operational Features**:
12. **Enhanced operational dashboard**: Live auto-updating **Next.js interface** with comprehensive staff alerting:
    *   **Auto-updating data**: Dashboard refreshes automatically every 45 seconds without manual intervention using optimized API polling
    *   **Background audio notifications**: A lightweight background sound plays automatically when new jobs are submitted; no on-page toggle. Future configuration will be exposed in the admin settings.
    *   **Visual alert indicators**: Persistent "NEW" badges with pulsing animations for unreviewed jobs until staff acknowledgment
    *   **Job age tracking**: Human-readable time elapsed display ("2d 4h ago") with color-coded prioritization (green < 24h, yellow < 48h, orange < 72h, red > 72h)
    *   **Staff acknowledgment system**: "Mark as Reviewed" functionality to clear visual alerts
    *   **Debug panel**: Development interface showing current state and system health
    *   **Last updated indicator**: Timestamp showing when dashboard data was last refreshed
13. **Multi-computer support**: System operates on up to three staff computers simultaneously, all using shared storage and database.
14. **Event Logging**: **Immutable event log** system tracking all changes with complete audit trail tied to **attributed staff members**.
15. **Thumbnails**: **Asynchronously** generates previews from uploaded files via RQ background tasks. Graceful fallback for generation failures with placeholder display.
16. **Comprehensive File Validation**: Multi-layer file validation including header validation, security checks, size limits, and path traversal prevention.
17. **Atomic File Operations**: Resilient file operations with staging areas, rollback capabilities, and transaction safety.
18. **System Health Monitoring**: Real-time system health monitoring with CPU, memory, disk, and network metrics.
19. **Error Boundaries & Recovery**: Frontend error boundaries with fallback UI and automatic retry mechanisms.

### 2.2 Technical Requirements (Beginner-Focused)

#### 2.2.1 Backend (Flask API-Only)
-   **Framework**: Flask (Python) with **API-only endpoints** - no HTML templates or server-side rendering
-   **Database**: PostgreSQL via SQLAlchemy ORM with Flask-Migrate for schema management
-   **Task Queue**: RQ for background jobs (emails, thumbnail generation, monitoring tasks, and a recurring job to check for expired confirmation tokens)
-   **Email**: Flask-Mail with Office 365 SMTP integration
-   **File Validation**: Comprehensive multi-layer validation including:
    - File header validation for STL, OBJ, 3MF, and ZIP-based formats
    - Security validation with path traversal prevention and dangerous character detection
    - File size validation with configurable minimum (1KB) and maximum (50MB) limits
    - Filename sanitization and reserved name detection
-   **Sibling File Detection**: A configurable list of slicer file extensions (e.g.,`.3mf`, `.form`, `.idea`) is used to automatically detect when a staff member has saved a new authoritative file
-   **Atomic File Operations**: Resilient file operations with staging areas, rollback capabilities, and transaction safety
-   **File Storage**: Network-mounted folders with standardized structure:
    ```
    storage/
    ├─ Uploaded/         # New submissions
    ├─ Pending/          # Awaiting staff review
    ├─ ReadyToPrint/     # Approved, ready for printing
    ├─ Printing/         # Currently being printed
    ├─ Completed/        # Finished prints
    ├─ PaidPickedUp/      # Final state
    └─ Archived/         # Archived jobs
    ```

#### 2.2.2 Frontend (Next.js App Router)
-   **Framework**: Next.js 14+ with App Router and TypeScript
-   **Styling**: Tailwind CSS with custom themes and animations
-   **UI Components**: shadcn/ui component library (Radix UI primitives)
-   **Frontend Architecture**:
    -   **Next.js App Router**: Modern file-based routing with server and client components
    -   **TypeScript**: Full type safety throughout the application
    -   **Tailwind CSS**: Utility-first styling with custom animations and themes
    -   **shadcn/ui**: Complete UI component library based on Radix UI primitives
    -   **Zustand State Management**: Global state management with focused stores eliminating prop drilling and centralizing shared state
        - **AuthStore**: Global authentication state and session management
        - **DashboardStore**: Dashboard state (search, refresh, job operations) with real-time updates
        - **ModalStore**: Centralized modal management with type safety and queue control
        - **JobOperationsStore**: Job-related operations, loading states, and optimistic updates
    -   **Sound System**: Background-only audio using the Browser Audio API; plays on new job submissions without UI toggles. Admin configuration is available.
    -   **Optimized API Layer**: Intelligent caching, request deduplication, and adaptive polling for performance
    -   **Error Boundaries**: Component-level error isolation with fallback UI and retry mechanisms
-   **Advanced Dashboard Features**:
    -   **Real-time Updates**: Auto-refresh every 45 seconds with visual and audio notifications using optimized API polling
    -   **Sound Notifications**: Background sound plays on new job uploads (no user-facing toggle); future admin page will control enable/disable and volume.
    -   **Visual Alert System**: "NEW" badges and pulsing animations for unreviewed jobs
    -   **Job Age Tracking**: Color-coded time elapsed display with human-readable formatting
    -   **Interactive Modals with User Attribution**: All state-changing modals (approve, reject, etc.) require the user to select their name from a dropdown before proceeding, ensuring every action is logged with the correct user.
    -   **Notes System**: Inline editing with auto-save and keyboard shortcuts
    -   **Debug Panel**: Development troubleshooting with state visibility
    -   **Job Locking**: Prevents concurrent edits with visual feedback and conflict resolution
-   **Routing Structure**:
    ```
    app/
    ├─ dashboard/page.tsx     # Staff operational dashboard
    ├─ analytics/page.tsx     # Analytics and insights dashboard
    ├─ submit/page.tsx        # Student submission form
    ├─ login/page.tsx         # Workstation login page
    └─ confirm/[token]/page.tsx # Student confirmation
    ```

#### 2.2.3 Authentication (Workstation Login & Action Attribution)
To ensure both ease of use in a chaotic lab environment and full accountability, the system uses a hybrid authentication model. This model replaces traditional individual user sessions.

- **Workstation Login**: Each physical computer terminal in the lab is treated as a "Workstation" and is assigned its own shared, long-lived password. Staff log in to the workstation once at the beginning of the day. The session is configured to last the entire workday.
- **Persistent Workstation Display**: The UI always prominently displays the name of the logged-in workstation (e.g., "Workstation: Front Desk").
- **Mandatory Action Attribution**: For any state-changing operation (e.g., approving a job, marking it complete, adding a note), the UI modal for that action contains a **mandatory dropdown menu** labeled "Performing Action As:". The staff member must select their own name from the list before they can proceed. This is implemented across all modals: approval, rejection, status changes, notes editing, and payment processing.
- **Accountability**: This ensures that while the workstation's session is shared, every critical action is explicitly attributed to a specific staff member in the event logs. The `Event` model stores both the `workstation_id` and the `triggered_by` (the staff member's name).
- **Staff List Management**: The staff list is stored centrally in the database and exposed through a `/api/v1/staff` endpoint. All workstations fetch this list dynamically at login (and refresh it periodically). Administrators manage the list via a lightweight "Staff Management" section in the dashboard (add / remove / deactivate), ensuring immediate consistency across every terminal.
- **Staff Status Tracking**: Staff can be marked as active/inactive, with inactive staff not appearing in attribution dropdowns but preserving historical attribution in event logs.

#### 2.2.4 Key Constraints & Principles
- **No Individual User Logins**: Staff do not have their own passwords for the system. Authentication is handled at the workstation level.
- **Beginner-Friendly**: Clear explanations and step-by-step setup
- **API-First Design**: Frontend consumes RESTful Flask API endpoints
- **CORS Configuration**: Enabled for Next.js development server integration

-   **API Communication**:
    -   Cross-Origin Resource Sharing (CORS) is enabled on the Flask API to allow requests from the Next.js frontend.
    -   The API is stateless and RESTful.
    -   Native **fetch API** for HTTP requests with error handling and retry logic.
-   **Task Queue**: RQ for **asynchronous processing** (emails, thumbnails, monitoring, file operations).
-   **API Security & Rate Limiting**:
    -   **Flask-Limiter** integration for abuse protection:
        -   `/api/v1/submit`: 5 submissions per IP per hour
        -   `/api/v1/auth/login`: 10 attempts per IP per hour (brute-force protection)
        -   Return `429 Too Many Requests` for exceeded limits
    -   **File Upload Limits**: 50MB max file size, 1KB minimum file size, monitor total storage usage
-   **File handling**: Shared network storage (mounted at OS level) with standardized naming, status-based directory structure, and embedded `metadata.json`.
-   **Direct file opening**: Custom protocol handler to open local files in slicer software.
-   **Email**: Flask-Mail with Office 365 SMTP integration.
-   **Database**: **PostgreSQL** with Flask-Migrate for schema management.
-   **Time Display**: All timestamps from the API are in **UTC**. The Next.js frontend is responsible for converting and displaying them in the user's local timezone using `date-fns` library.
-   **Pricing Model**: Weight-only pricing ($0.10/gram filament, $0.20/gram resin) with $3.00 minimum charge.
-   **Time Input**: Hour-based time inputs with conservative rounding (always round UP to nearest 0.5 hours).
-   **Critical Dependencies**:
    -   **Backend**: `Flask`, `Flask-SQLAlchemy`, `Flask-Migrate`, `Flask-CORS`, `Flask-Limiter`, `psycopg2-binary`, `python-dotenv`, `PyJWT`, `rq`, `openpyxl`, `pandas`, `itsdangerous` (for secure tokens).
    -   **Frontend**: `next`, `react`, `react-dom`, `typescript`, `tailwindcss`, `@radix-ui/*`, `lucide-react`, `date-fns`, `class-variance-authority`, `clsx`, `tailwind-merge`, `recharts`, `zustand` (for global state management).

#### 2.2.5 Implemented Advanced Features
**System Monitoring & Health**:
- **Comprehensive Monitoring Service**: Real-time system health monitoring with CPU, memory, disk, and network metrics
- **Performance Monitoring**: Request timing, error rates, and slow endpoint detection with automatic alerts
- **Structured Logging**: JSON-structured logging for production with automatic log rotation
- **Health Check Endpoints**: Granular health checks for database, Redis, storage, and system resources
- **Cross-platform Monitoring Scripts**: Linux/Mac and Windows monitoring scripts for production deployment

**API Optimization & Caching**:
- **Intelligent Caching**: Request deduplication, adaptive TTL, and performance statistics tracking
- **Optimized API Patterns**: Adaptive polling, request batching, and activity-based optimization
- **Error Handling**: Standardized error response formats across all API endpoints
- **Performance Analytics**: Request timing, cache hit rates, and performance metrics

**File Validation & Security**:
- **Comprehensive File Validation**: File header validation for STL, OBJ, 3MF, and ZIP-based formats
- **Security Validation**: Path traversal prevention, dangerous character detection, and filename sanitization
- **File Size Validation**: Configurable minimum (1KB) and maximum (50MB) file size limits with clear error messages
- **Atomic File Operations**: Resilient file operations with staging areas and rollback capabilities
- **Duplicate Detection**: File content hashing prevents duplicate active submissions

**Error Boundaries & Stability**:
- **Frontend Error Boundaries**: Reusable error boundary components with fallback UI and retry mechanisms
- **Centralized Error Reporting**: Structured error reporting with backend integration and analytics
- **Graceful Degradation**: Component-level error isolation preventing full page crashes
- **Error Recovery**: Automatic retry mechanisms and user-friendly error messages

**Job Management & Concurrency**:
- **Job Locking System**: Prevents multiple staff members from editing the same job simultaneously
- **Lock Management**: Automatic lock acquisition on modal open, extension via heartbeat, release on close
- **Conflict Resolution**: Clear UI feedback when jobs are locked by other users
- **Admin Override**: Administrators can force-unlock stuck locks with audit logging

### 2.3 Beginner-Friendly Architecture Principles
This project will adhere to simplicity and clarity while building a robust foundation:

#### 2.3.1 Core Architectural Decisions
1.  **Authentication**: **Workstation-level shared passwords** combined with **mandatory per-action staff attribution** to ensure both ease of use and accountability. No individual user accounts or complex session management.
2.  **API Design**: **Flask API-only backend** with clear RESTful endpoints, no HTML templates or server-side rendering.
3.  **Frontend Separation**: **Next.js frontend** consumes API endpoints, complete separation of concerns.
4.  **Models**: Essential `Job` model, plus an **`Event` model** for comprehensive logging and audit trails.
5.  **File Management**: Straightforward folder structure, accessible via shared network, with `metadata.json` alongside files for resilience.

#### 2.3.2 Implementation Strategy
1.  **Incremental Development**: Start with minimal viable product (MVP), then build upon the foundation with additional features.
2.  **Routes**: API-only routes organized with **Flask Blueprints**, all actions triggering **event logs**.
3.  **Error Handling**: Comprehensive error handling with clear user feedback and logging.
4.  **Testing Strategy**: Focus on API endpoints, business logic, file handling, and workflow events.
5.  **Documentation**: Step-by-step guides for setup, deployment, and maintenance.

#### 2.3.3 Technology Stack Simplification
1.  **Docker-Based Environment**: The entire application stack is defined in a `docker-compose.yml` file, ensuring a consistent, reproducible environment for both development and production. This simplifies setup and eliminates cross-platform compatibility issues.
2.  **Simplified Authentication**: A custom-built workstation login system replaces the need for complex third-party identity providers.
3.  **No Microservices**: Single Flask application with clear module organization.
4.  **Progressive Enhancement**: Build solid foundation first, then add features like custom protocol handlers.
5.  **Progressive Enhancement**: Build solid foundation, then add advanced dashboard features.

### 2.4 User Experience Requirements

#### 2.4.1 Essential UX Features
**Student Submission Experience**:
-   **Dynamic Form Behavior**: Color selection must be disabled until print method is selected, with contextual help text
-   **Progressive Disclosure**: Print method descriptions should be clearly visible to guide material choice
-   **Input Validation**: Real-time client-side validation with visual feedback to prevent submission errors
-   **Educational Content**: Comprehensive introduction text with liability disclaimers and scaling guidance
-   **File Validation**: Immediate feedback on file selection with size and type checking (50MB max, .stl/.obj/.3mf only)
-   **Accessibility**: Visual error states with red borders, clear error messages, and error scrolling for form submission
-   **Duplicate Prevention**: System detects and prevents duplicate active submissions with clear error messaging

**Basic Staff Dashboard Experience**:
-   **Clean Interface**: Simple, professional dashboard showing job cards with essential information
-   **Basic Actions**: Approve/reject modals with form validation, cost calculation, and mandatory staff attribution
-   **Job Management**: Status updates with clear visual feedback and job locking for concurrency control
-   **Workstation Authentication**: Seamless login experience for each computer terminal
-   **Staff Attribution**: All state-changing actions require staff member selection from dropdown

#### 2.4.2 Advanced UX Features
**Enhanced Operational Dashboard UX**:
    *   **Real-time Updates**: Dashboard data refreshes automatically every 45 seconds without user intervention using optimized API polling
    *   **Audio Feedback**: A background sound plays when new jobs are uploaded (no on-page toggle). Future admin settings will allow configuring this behavior.
    *   **Visual Alert System**: Unreviewed jobs display prominent "NEW" badges with pulsing highlight borders until acknowledged
    *   **Temporal Awareness**: Job age display with human-readable format ("2d 4h ago") and color-coded prioritization
    *   **Staff Acknowledgment**: Clear "Mark as Reviewed" functionality to manage alert states
    *   **Last Updated Indicator**: Timestamp showing when dashboard data was last refreshed
    *   **Job Locking**: Visual feedback when jobs are locked by other users with conflict resolution
    *   **Error Recovery**: Automatic retry mechanisms and graceful degradation for failed operations

#### 2.4.3 Universal Design Standards
**Mobile and Accessibility Considerations**: 
- Ensure the submission form and dashboard are fully functional and readable on mobile devices.
- Test UI components with screen readers for basic WCAG 2.1 compliance.
- Ensure keyboard-only navigation works for all modals and interactive elements.

**Professional UI Design Standards**:
- All UI components must follow modern web design best practices
- Use consistent spacing system (multiples of 4px or 8px)
- Implement proper visual hierarchy with appropriate typography scales
- Support system font preferences and user accessibility settings
- Maintain minimum touch target size (44px minimum)
- Use professional color palette with sufficient contrast ratios
- Follow responsive design principles for all screen sizes

#### 2.4.4 Admin Dashboard UX
- **Placement**: Dedicated `/admin` page with tabbed navigation between administrative functions.
- **Access**: Requires valid workstation JWT. Admin actions display explicit confirmation dialogs and show attribution (`staff_name`, `workstation_id`).
- **Core Sections**:
  - **Settings**: Background sound configuration (enable/disable, volume); environment banner; basic system info. No per-user toggles.
  - **Staff Management**: List, add, deactivate/reactivate staff; reflects instantly in attribution dropdowns. Maps to `/staff` endpoints.
  - **Catalog Management**: **NEWLY IMPLEMENTED** - User-friendly interface for managing printers, materials, and colors with immediate submission form updates:
    * **Printer Management**: Add new printers with ID, display name, supported methods (Filament/Resin), and active/inactive status
    * **Material Management**: Add materials with method assignment, cost per gram configuration, and color collection management
    * **Color Management**: Per-material color management with add/remove capabilities and real-time preview
    * **Dynamic Integration**: Changes instantly reflect in student submission form dropdowns
    * **Professional Interface**: Tabbed layout (Printers | Materials & Colors) with table views and intuitive form controls
    * **Version Tracking**: All catalog changes increment version number with staff attribution
    * **API Integration**: Maps to `/catalog` endpoints with PUT operations for updates
  - **Admin Overrides**: Force unlock, force confirm, change status, mark failed; guarded by confirmations and reason fields. Maps to `/jobs/<id>/admin/*` endpoints.
  - **Data Management**: Archival and pruning controls with retention days and preview counts. Maps to `/admin/archive` and `/admin/prune`.
  - **System Health & Integrity**: Start audit, view last report, delete orphaned files. Maps to `/admin/audit/*`.
  - **Email Tools**: Resend emails with visible cooldowns and rate-limit feedback. Maps to `/jobs/<id>/admin/resend-email`.
- **UI States**: Loading spinners for long actions, empty-state messages, error banners with retry, success toasts.
- **Auditability**: All actions log `Event` entries and show last action metadata inline (who/when).

#### 2.4.5 Analytics Dashboard UX
- **Route**: `/analytics` (App Router page).
- **Data Sources**: `/analytics/overview`, `/analytics/trends`, `/analytics/resources`, `/stats`, `/stats/detailed`.
- **Overview Cards**: Total submissions, in-queue by status, average turnaround, storage usage vs. limit, recent rejections.
- **Trend Charts**: Submissions and approvals over time; printing throughput; average lead time; filters for period (7/30/90 days) and discipline/printer.
- **Resource Metrics**: Printer utilization (stacked bars by day), material consumption (filament/resin grams), queue age distribution.
- **Financial Summary**: Revenue totals by period, average ticket size, payment counts; link to export flow.
- **Filters & Controls**: Days/printer/discipline selectors; server-side filtering mapped to query params.
- **States**: Loading skeletons, empty-data placeholders, error with retry; last-refreshed timestamp.


#### 2.4.6 Job Cards & Notes System
**Job Card Interface**:
- **Card Layout**: Grid-based layout with responsive design (1-3 columns based on screen size)
- **Essential Information Display**: Student name, display name, submission time, email, printer, color, and discipline
- **Status Indicators**: Visual status badges and color-coded age indicators
- **Expandable Details**: Collapsible sections for additional job information and notes
- **Action Buttons**: Context-sensitive action buttons (approve, reject, status changes, delete) with confirmation dialogs
- **Lock Status**: Visual indication when jobs are locked by other users with conflict resolution
- **File Operations**: "Open File" button with protocol handler integration and file path copying

**Notes System Features**:
- **Inline Editing**: Click-to-edit interface for adding and modifying job notes
- **Staff Attribution**: Mandatory staff member selection for all note operations
- **Character Limits**: 1000 characters per note entry, 5000 characters total notes limit
- **Append-Only Model**: New notes are appended to existing notes with timestamp preservation
- **Visual Feedback**: Real-time character count, save status indicators, and error messages
- **Keyboard Navigation**: Full keyboard accessibility with Enter/Space activation
- **Auto-Focus**: Automatic focus on textarea when entering edit mode
- **Validation**: Client-side validation for empty notes and character limits
- **Error Handling**: Clear error messages for validation failures and network errors

**Notes Workflow**:
1. **Adding Notes**: Click "Add note" or existing notes to enter edit mode
2. **Staff Selection**: Mandatory dropdown selection of staff member name
3. **Note Entry**: Type note in textarea with real-time character count
4. **Validation**: System validates note length and staff selection
5. **Saving**: Explicit save button with loading state and success feedback
6. **Display**: Notes displayed as bulleted list with newest notes first

**Evidence Sources**:
- **Job Card Implementation**: `frontend/src/components/dashboard/job-card.tsx`
- **Notes API**: `backend/app/routes/jobs_staff.py` (PATCH `/notes` endpoint)
- **Notes Validation**: 1000 character per entry limit, 5000 character total limit
- **Staff Attribution**: Mandatory staff_name field in all note operations

#### 2.4.7 Search, Sorting & Global Controls
**Search Functionality**:
- **Real-time Search**: Debounced search input with 400ms delay for performance
- **Search Scope**: Searches student name and email addresses (case-insensitive)
- **Search Match Counts**: Shows count of matching jobs per status tab
- **Search Persistence**: Search terms persist across status tab changes
- **API Integration**: Server-side search filtering via `/api/v1/jobs?search=term`
- **Search Counts API**: `/api/v1/jobs/counts?search=term` for match counts by status

**Sorting System**:
- **Default Sorting**: Jobs sorted by creation date (newest first) by default
- **Sortable Fields**: Creation date, student name, printer, and other job attributes
- **Sort Direction**: Toggle between ascending and descending order
- **Client-side Sorting**: Sorting performed in frontend for responsive UI
- **Stable Sorting**: Multiple tie-breakers ensure consistent sort order
- **Sort State Management**: Sort preferences maintained in component state

**Global Expand/Collapse Controls**:
- **Global Toggle Button**: "Expand All" / "Collapse All" button in job list header
- **Signal-based System**: Uses incrementing signal counters to trigger global actions
- **Individual Card Response**: Each job card responds to expand/collapse signals
- **Visual Feedback**: Button text and icon change based on current state
- **State Tracking**: Tracks expand vs collapse signal counts to determine button state
- **Smooth Animations**: CSS transitions for expand/collapse animations

**Filtering System**:
- **Status Filtering**: Filter by job status (UPLOADED, PENDING, etc.)
- **Printer Filtering**: Filter by specific printer type
- **Discipline Filtering**: Filter by academic discipline
- **Combined Filters**: Multiple filters can be applied simultaneously
- **URL Integration**: Filter state reflected in URL parameters
- **Filter Persistence**: Filters maintained across page refreshes

**Performance Optimizations**:
- **Debounced Search**: 400ms delay prevents excessive API calls
- **Memoized Sorting**: Sorted job list cached to prevent unnecessary re-computation
- **Optimized API**: Request deduplication and caching via optimized API layer
- **Lazy Loading**: Job cards load progressively as needed
- **Error Boundaries**: Component-level error isolation for stability

**Evidence Sources**:
- **Search Implementation**: `frontend/src/app/dashboard/page.tsx` (debounced search, match counts)
- **Sorting Logic**: `frontend/src/components/dashboard/job-list.tsx` (memoized sorting, stable sort)
- **Global Controls**: `frontend/src/components/dashboard/job-list.tsx` (expand/collapse signals)
- **API Integration**: `backend/app/services/infrastructure/job_query_service.py` (search filtering)
- **Filter Management**: `frontend/src/types/index.ts` (JobListFilters interface)

#### 2.4.8 Required Submission Form Introduction Text

A mandatory warning and liability disclaimer must be displayed at the top of the student submission form. The full, unaltered text for this warning is specified in the "Student Submission UI/UX" description under **Section 3.4.2**.

## 3. System Architecture & Implementation Structure

### 3.1 Project Structure

The project follows a clear separation between backend and frontend, designed for beginner-friendly development and deployment:

```
DASHBOARDV5/
├── frontend/                # Next.js Application
│   ├── src/
│   │   ├── app/             # App Router pages
│   │   │   ├── dashboard/
│   │   │   │   └── page.tsx     # Staff dashboard
│   │   │   ├── submit/
│   │   │   │   ├── page.tsx     # Student submission form
│   │   │   │   └── success/
│   │   │   │       └── page.tsx # Submission success
│   │   │   ├── login/
│   │   │   │   └── page.tsx     # Workstation login page
│   │   │   ├── confirm/
│   │   │   │   └── [token]/
│   │   │   │       └── page.tsx # Student email confirmation
│   │   │   ├── admin/           # Admin dashboard pages
│   │   │   ├── analytics/       # Analytics dashboard pages
│   │   │   ├── staff-analytics/ # Staff analytics pages
│   │   │   ├── globals.css      # Global styles
│   │   │   ├── layout.tsx       # Root layout
│   │   │   ├── error.tsx        # Error boundary
│   │   │   ├── not-found.tsx    # 404 page
│   │   │   └── page.tsx         # Home page (redirect to dashboard)
│   │   ├── components/          # UI Components
│   │   │   ├── dashboard/       # Dashboard-specific components
│   │   │   │   ├── job-card.tsx              # Main job card component (refactored)
│   │   │   │   ├── job-card-header.tsx       # Job info display & review states
│   │   │   │   ├── job-card-notes.tsx        # Notes editing & management
│   │   │   │   ├── job-card-actions.tsx      # Action buttons & status changes
│   │   │   │   ├── job-card-details.tsx      # Expandable job details
│   │   │   │   ├── job-card-original-backup.tsx # Archived original (1,028 lines)
│   │   │   │   ├── index.ts                  # Clean component exports
│   │   │   │   ├── job-list.tsx
│   │   │   │   ├── status-tabs.tsx
│   │   │   │   ├── diag-panel.tsx
│   │   │   │   ├── last-updated.tsx
│   │   │   │   └── modals/
│   │   │   │       ├── approval-modal.tsx
│   │   │   │       ├── rejection-modal.tsx
│   │   │   │       ├── payment-modal.tsx
│   │   │   │       ├── review-modal.tsx
│   │   │   │       ├── status-change-modal.tsx
│   │   │   │       └── confirm-dialog.tsx
│   │   │   ├── analytics/       # Analytics dashboard components
│   │   │   ├── admin/           # Admin dashboard components
│   │   │   │   ├── admin-settings.tsx
│   │   │   │   ├── staff-panel.tsx
│   │   │   │   ├── catalog-management.tsx  # Dynamic catalog editor
│   │   │   │   ├── admin-overrides.tsx
│   │   │   │   ├── data-management.tsx
│   │   │   │   ├── system-health.tsx
│   │   │   │   ├── email-tools.tsx
│   │   │   │   └── monitoring-dashboard.tsx
│   │   │   ├── staff-analytics/ # Staff analytics components
│   │   │   ├── student-analytics/ # Student analytics components
│   │   │   ├── submission/      # Form components
│   │   │   ├── layout/          # Layout components
│   │   │   ├── error-boundary.tsx # Error boundary component
│   │   │   ├── LoginCard.tsx    # Login component
│   │   │   └── ui/              # shadcn/ui components
│   │   │       ├── button.tsx
│   │   │       ├── card.tsx
│   │   │       ├── input.tsx
│   │   │       ├── select.tsx
│   │   │       └── ... (other UI components)
│   │   ├── lib/                 # Utility functions
│   │   │   ├── api.ts           # API client functions
│   │   │   └── utils.ts         # General utilities
│   │   ├── store/               # Zustand state management
│   │   │   ├── index.ts         # Store exports and utilities
│   │   │   ├── utils.ts         # Store utilities and patterns
│   │   │   ├── types/           # Store type definitions
│   │   │   │   └── index.ts     # Store interfaces and types
│   │   │   └── slices/          # Individual store implementations
│   │   │       ├── auth-store.ts         # Authentication store
│   │   │       ├── dashboard-store.ts    # Dashboard state store
│   │   │       ├── modal-store.ts        # Modal management store
│   │   │       └── job-operations-store.ts # Job operations store
│   │   └── types/               # TypeScript types
│   │       └── index.ts         # Type definitions
│   ├── .env.local               # Frontend environment variables
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── jest.config.js
│   ├── jest.setup.ts
│   ├── Dockerfile               # Development Dockerfile
│   └── Dockerfile.prod          # Production Dockerfile
│
├── backend/                 # Flask API Application
│   ├── app/
│   │   ├── __init__.py      # App factory
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── job.py       # Job model with locking
│   │   │   ├── event.py     # Event log model
│   │   │   ├── payment.py   # Payment model
│   │   │   ├── staff.py     # Staff model
│   │   │   └── catalog.py   # Catalog configuration storage
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py      # Authentication endpoints (workstation validation)
│   │   │   ├── jobs.py      # Job management endpoints
│   │   │   ├── jobs_staff.py # Staff job operations
│   │   │   ├── submit.py    # Student submission endpoints
│   │   │   ├── payment.py   # Payment processing endpoints
│   │   │   ├── analytics.py # Analytics and reporting endpoints
│   │   │   ├── staff.py     # Staff management endpoints
│   │   │   ├── admin.py     # Admin operations endpoints
│   │   │   ├── health.py    # Health check endpoints
│   │   │   ├── catalog.py   # Catalog management endpoints
│   │   │   ├── diag.py      # Diagnostic endpoints
│   │   │   ├── export.py    # Data export endpoints
│   │   │   └── monitoring.py # System monitoring endpoints
│   │   ├── business_logic/  # Decomposed business logic services
│   │   │   ├── __init__.py
│   │   │   ├── job_lifecycle/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── job_approval_service.py
│   │   │   │   ├── job_status_service.py
│   │   │   │   └── job_transition_service.py
│   │   │   ├── admin_operations/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── job_admin_service.py
│   │   │   │   └── job_notes_service.py
│   │   │   ├── shared_services/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── job_locking_service.py
│   │   │   │   ├── job_event_service.py
│   │   │   │   ├── db_transaction_service.py
│   │   │   │   ├── response_service.py
│   │   │   │   ├── validation_service.py
│   │   │   │   ├── auth_service.py
│   │   │   │   ├── event_service.py
│   │   │   │   ├── error_handling_service.py
│   │   │   │   ├── email_service.py
│   │   │   │   ├── token_service.py
│   │   │   │   └── catalog_service.py
│   │   │   └── analytics/
│   │   │       ├── __init__.py
│   │   │       ├── analytics_service.py
│   │   │       └── caching_service.py
│   │   ├── services/        # Infrastructure and orchestration
│   │   │   ├── __init__.py
│   │   │   ├── orchestration/
│   │   │   │   ├── __init__.py
│   │   │   │   └── job_orchestration_service.py  # Unified service interface
│   │   │   ├── infrastructure/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── file_configuration_service.py
│   │   │   │   ├── file_discovery_service.py
│   │   │   │   ├── atomic_file_service.py
│   │   │   │   ├── file_lock_service.py
│   │   │   │   ├── job_query_service.py
│   │   │   │   ├── payment_service.py
│   │   │   │   ├── payment_service_interface.py
│   │   │   │   └── file_service.py
│   │   │   ├── interfaces/
│   │   │   │   ├── __init__.py
│   │   │   │   └── analytics_service_interface.py
│   │   │   └── monitoring_service.py
│   │   ├── schemas/         # API schemas
│   │   │   ├── __init__.py
│   │   │   └── catalog.py   # Catalog validation schemas
│   │   ├── utils/           # Utilities
│   │   │   ├── __init__.py
│   │   │   ├── decorators.py # Auth decorators
│   │   │   ├── file_utils.py # File operation utilities
│   │   │   └── date_utils.py # Date handling utilities
│   │   ├── templates/       # Email templates
│   │   └── seed.py          # Database seeding
│   ├── migrations/          # Database migrations
│   ├── tests/               # Test suite
│   ├── scripts/             # Utility scripts
│   ├── docs/                # Documentation
│   ├── logs/                # Application logs
│   ├── instance/            # Instance-specific files
│   ├── .env                 # Backend environment variables
│   ├── requirements.txt     # Python dependencies
│   ├── run.py               # Development server
│   ├── Dockerfile           # Development Dockerfile
│   └── Dockerfile.prod      # Production Dockerfile
│
├── storage/                 # File storage (network-mounted)
│   ├── Uploaded/
│   ├── Pending/
│   ├── ReadyToPrint/
│   ├── Printing/
│   ├── Completed/
│   ├── PaidPickedUp/
│   ├── Rejected/
│   └── Archived/
│
├── SlicerOpener/            # Protocol handler
│   ├── SlicerOpener.py      # Python script
│   ├── SlicerOpener.exe     # Compiled executable (PyInstaller)
│   ├── config.ini           # Configuration file
│   ├── config.example.ini   # Example configuration
│   ├── register.bat         # Windows registry setup
│   ├── SlicerOpener.spec    # PyInstaller spec file
│   ├── sliceropener.log     # Application logs
│   ├── README.md            # Documentation
│   ├── build/               # Build artifacts
│   ├── dist/                # Distribution files
│   └── releases/            # Release packages
│
├── scripts/                 # Utility scripts
├── tests/                   # Integration tests
├── logs/                    # System logs
├── docker-compose.dev.yml   # Development environment
├── docker-compose.prod.yml  # Production environment
├── .dockerignore            # Specifies files to ignore in Docker builds
├── pytest.ini              # Test configuration
└── .gitignore              # Git ignore rules
```

### 3.1.1 Current Service Architecture
The system operates with a fully decomposed, orchestrated architecture that replaced the original monolithic services:

**Orchestration Layer**:
- **JobOrchestrationService**: Operational unified interface for all job lifecycle operations
- **Service Composition**: Actively coordinates between specialized business logic services
- **API Compatibility**: Maintains complete compatibility with existing route interfaces

**Business Logic Services** (Operational decomposed architecture):
- **JobApprovalService**: Operational job approval, rejection, and review workflows
- **JobStatusService**: Active status transitions (printing, complete, pickup, etc.)
- **JobTransitionService**: Operational status change validation and orchestration
- **JobAdminService**: Live admin operations (force unlock, status changes, etc.)
- **JobNotesService**: Operational job notes and comments management
- **JobLockingService**: Active job locking for concurrency control
- **JobEventService**: Live event logging and audit trails

**Infrastructure Services**:
- **FileConfigurationService**: File validation, security, and configuration management (`backend/app/services/infrastructure/file_configuration_service.py`)
- **FileDiscoveryService**: Discovers and validates candidate files for approval (`backend/app/services/infrastructure/file_discovery_service.py`)
- **AtomicFileService**: Ensures atomic file operations with rollback capabilities (`backend/app/services/infrastructure/atomic_file_service.py`)
- **FileLockService**: Manages file-level locking for concurrent access (`backend/app/services/infrastructure/file_lock_service.py`)
- **JobQueryService**: Handles job querying and filtering operations (`backend/app/services/infrastructure/job_query_service.py`)
- **PaymentService**: Manages payment processing and calculations (`backend/app/services/infrastructure/payment_service.py`)
- **MonitoringService**: Comprehensive system monitoring and health checks (`backend/app/services/monitoring_service.py`)

**Shared Services** (in both business_logic and services):
- **DbTransactionService**: Manages database transactions and consistency (`backend/app/business_logic/shared_services/db_transaction_service.py`)
- **ValidationService**: Centralized input validation and error handling (`backend/app/business_logic/shared_services/validation_service.py`)
- **ResponseService**: Standardized API response formatting (`backend/app/business_logic/shared_services/response_service.py`)
- **ErrorHandlingService**: Comprehensive error handling and recovery (`backend/app/business_logic/shared_services/error_handling_service.py`)
- **EventService**: Event logging and management (`backend/app/business_logic/shared_services/event_service.py`)
- **TokenService**: Token generation and validation (`backend/app/business_logic/shared_services/token_service.py`)
- **CatalogService**: Data catalog and reference management (`backend/app/business_logic/shared_services/catalog_service.py`)
- **CachingService**: Request caching and optimization (`backend/app/business_logic/analytics/caching_service.py`)
- **AnalyticsService**: Analytics and reporting functionality (`backend/app/business_logic/analytics/analytics_service.py`)

**Service Architecture Status**:
- **Complete Service Decomposition**: Successfully operates with 8 focused business logic services replacing the original 1,166-line monolithic service
- **API Compatibility**: Maintains 100% compatibility with existing route interfaces
- **Import Hierarchy**: Clean dependency management prevents circular imports
- **Service Composition**: Orchestration layer coordinates between specialized business logic services
- **Production Ready**: Full transition completed with backward-compatible import aliases

### 3.2 Database Schema & Models

The system uses PostgreSQL with SQLAlchemy ORM for robust data management and comprehensive audit trails.

#### 3.2.1 Core Models

**Staff Model** - Represents staff members for attribution and tracking:
```python
class Staff(db.Model):
    name = db.Column(db.String(100), primary_key=True)
    is_active = db.Column(db.Boolean, default=True)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    deactivated_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships - optional, for query optimization
    actions = db.relationship('Event', backref='attributed_staff', lazy=True, 
                             primaryjoin="Staff.name == foreign(Event.triggered_by)")
```

**Job Model** - Central entity representing each 3D print request:
```python
class Job(db.Model):
   id = db.Column(db.String, primary_key=True, default=lambda: uuid.uuid4().hex)
   short_id = db.Column(db.String(12), unique=True, index=True, nullable=True)
   student_name = db.Column(db.String(100), nullable=False)
   student_email = db.Column(db.String(100), nullable=False)
   discipline = db.Column(db.String(50), nullable=False)
   class_number = db.Column(db.String(50), nullable=False)
   
   # File Management
   original_filename = db.Column(db.String(256), nullable=False)
   display_name = db.Column(db.String(256), nullable=False)
   file_path = db.Column(db.String(512), nullable=False)
   metadata_path = db.Column(db.String(512), nullable=False)
   file_hash = db.Column(db.String(64), nullable=True)
   
   # Job Configuration
   status = db.Column(db.String(50), default='UPLOADED')
   printer = db.Column(db.String(64), nullable=False)
   color = db.Column(db.String(32), nullable=False)
   material = db.Column(db.String(32), nullable=False)
   weight_g = db.Column(db.Float, nullable=True)
   time_hours = db.Column(db.Float, nullable=True)
   cost_usd = db.Column(db.Numeric(6, 2), nullable=True)
   
   # Student Confirmation
   acknowledged_minimum_charge = db.Column(db.Boolean, default=False)
   student_confirmed = db.Column(db.Boolean, default=False)
   student_confirmed_at = db.Column(db.DateTime, nullable=True)
   confirm_token = db.Column(db.String(128), nullable=True, unique=True)
   confirm_token_expires = db.Column(db.DateTime, nullable=True)
   is_confirmation_expired = db.Column(db.Boolean, default=False)
   confirmation_last_sent_at = db.Column(db.DateTime, nullable=True)
   
   # Staff Management
   reject_reasons = db.Column(db.JSON, nullable=True)
   staff_viewed_at = db.Column(db.DateTime, nullable=True)    # For visual alerts
   last_updated_by = db.Column(db.String(100), nullable=True) # Staff member name from attribution dropdown
   notes = db.Column(db.Text, nullable=True)                  # Staff notes

   # Locking fields
   locked_by = db.Column(db.String(100), nullable=True)
   locked_until = db.Column(db.DateTime, nullable=True)
   
   # Timestamps
   created_at = db.Column(db.DateTime, default=datetime.utcnow)
   updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
   
   # Relationships
   payment = db.relationship('Payment', backref='job', uselist=False, cascade='all, delete-orphan')
```

**Status Name Standardization**

To maintain consistency across the codebase, job statuses follow these naming conventions:

1. **Internal Identifiers (API, Code, Database):** UPPERCASE
   - Example: `UPLOADED`, `PENDING`, `READYTOPRINT`, `PRINTING`, `COMPLETED`, `PAIDPICKEDUP`, `REJECTED`, `ARCHIVED`
   - Used in: API endpoints, TypeScript types, database values, conditional logic

2. **Directory Names:** PascalCase
   - Example: `Uploaded/`, `Pending/`, `ReadyToPrint/`, `Printing/`, `Completed/`, `PaidPickedUp/`, `Archived/`
   - Used in: File system organization

3. **User Interface:** Title Case with spaces
   - Example: "Uploaded", "Pending", "Ready to Print", "Printing", "Completed", "Paid & Picked Up", "Rejected"
   - Used in: Dashboard displays, modals, status indicators

This clear distinction helps maintain consistency while optimizing for each context.

**Event Model** - Immutable audit trail for all system actions:
```python
class Event(db.Model):
   id = db.Column(db.Integer, primary_key=True)
   job_id = db.Column(db.String, nullable=True)  # Removed foreign key constraint for system events
   timestamp = db.Column(db.DateTime, default=datetime.utcnow)
   event_type = db.Column(db.String(50), nullable=False)
   details = db.Column(db.JSON, nullable=True)
   triggered_by = db.Column(db.String(100), nullable=False)
   workstation_id = db.Column(db.String(100), nullable=False)
   
   def to_dict(self):
       return {
           'id': self.id,
           'job_id': self.job_id,
           'timestamp': self.timestamp.isoformat(),
           'event_type': self.event_type,
           'details': self.details,
           'triggered_by': self.triggered_by,
           'workstation_id': self.workstation_id
       }
```

**Payment Model** - Financial transaction tracking for completed jobs:
```python
class Payment(db.Model):
    job_id = db.Column(db.String, db.ForeignKey('job.id'), primary_key=True)
    grams = db.Column(db.Float, nullable=False)           # Actual weight from scale
    price_cents = db.Column(db.Integer, nullable=False)   # Final calculated price in cents
    txn_no = db.Column(db.String(50), nullable=False)     # Tiger-Cash transaction number
    picked_up_by = db.Column(db.String(100), nullable=False)  # Person who collected
    paid_ts = db.Column(db.DateTime, default=datetime.utcnow)
    paid_by_staff = db.Column(db.String(100), nullable=False) # Staff member who processed
```

**Staff Model** - Represents staff members for attribution and tracking:
```python
class Staff(db.Model):
    name = db.Column(db.String(100), primary_key=True)
    is_active = db.Column(db.Boolean, default=True)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    deactivated_at = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'name': self.name,
            'is_active': self.is_active,
            'added_at': self.added_at.isoformat() if self.added_at else None,
            'deactivated_at': self.deactivated_at.isoformat() if self.deactivated_at else None
        }
```

**CatalogStore Model** - Stores system configuration catalog as versioned JSON:
```python
class CatalogStore(db.Model):
    id = db.Column(db.String(50), primary_key=True)  # Always 'active' for current catalog
    version = db.Column(db.Integer, nullable=False, default=1)
    data = db.Column(db.JSON, nullable=False)
    updated_by = db.Column(db.String(100), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now())
    
    def to_dict(self):
        return {
            'version': self.version,
            'data': self.data,
            'updated_by': self.updated_by,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
```

#### 3.2.2 Key Design Decisions

**Authentication Integration**: The `last_updated_by` and `triggered_by` fields store the staff member's name selected from the attribution dropdown, enabling full accountability for every action. The `workstation_id` provides additional context for where the action originated.

**File Resilience**: Both `file_path` and `metadata_path` ensure data integrity even if database and file system become disconnected.

**Flexible Status System**: String-based status allows for easy expansion of workflow states without schema changes.

**Audit Trail**: Every action creates an immutable Event record with full context for debugging and accountability.

**Data Class Architecture**: Comprehensive data classes for type-safe service communication:
- **JobApprovalData**: Staff name, weight, time, authoritative filename, printer override
- **JobRejectionData**: Staff name, reasons list, custom reason
- **JobReviewData**: Staff name, reviewed boolean
- **JobStatusTransitionData**: Staff name, workstation ID, additional data
- **JobAdminStatusChangeData**: Staff name, new status, reason
- **JobDeleteData**: Staff name, reason
- **JobResendEmailData**: Staff name, email type
- **JobForceUnlockData**: Staff name, reason
- **JobNoteData**: Staff name, note content
- **JobUpdateNotesData**: Staff name, notes text
- **JobLockData**: Staff name, lock duration

### 3.3 Authentication Architecture

The system's authentication is designed for a high-turnover, shared-terminal environment, prioritizing operational simplicity while maintaining strict per-action accountability. It uses two distinct models for staff and students.

#### 3.3.1 Staff Authentication: Workstation & Attribution Model
- **Workstation Login**: Each physical computer is considered a "Workstation" and is assigned a unique password. This password is used to initiate a long-lived session (e.g., 12 hours) for that specific computer. Staff do not have individual passwords.
- **Session Management**: A simple, long-lived JWT is issued to the browser upon successful workstation login. This token contains the `workstation_id` (e.g., "Front-Desk-Computer").
- **Per-Action Attribution**: For every state-changing action (approve, reject, etc.), the UI modal **requires** the acting user to select their name from a dropdown list of active staff members.
- **API Requirement**: The API endpoints for these actions require a `staff_name` field in the request body. The backend validates that the name is on the official staff list.

#### 3.3.1.1 Staff Turnover Management
To effectively manage staff turnover while maintaining system integrity, the following process is implemented:

**Staff Onboarding Process:**
1. **Staff List Management**: The system includes an admin-accessible UI in the dashboard for managing the staff list, which is stored in the database.
2. **Adding New Staff**: An administrator adds new staff members through this interface, providing their name as it should appear in attribution dropdowns.
3. **Training Documentation**: New staff are provided with documentation on the attribution model and how to select their name for actions.
4. **No Individual Login Required**: Since authentication is workstation-based, new staff only need to be added to the staff list without creating credentials.
5. **First Action Guidance**: The UI highlights newly added staff names in the dropdown for a configurable period (e.g., 7 days) to help staff identify their name.

**Staff Offboarding Process:**
1. **Deactivation vs. Deletion**: When staff leave, administrators mark them as "inactive" rather than deleting them completely, preserving historical attribution.
2. **Audit Trail Preservation**: Past actions attributed to departed staff remain unchanged in the event log for accountability and historical reference.
3. **Dropdown Visibility**: Inactive staff names no longer appear in attribution dropdowns for new actions.
4. **Visual Indication**: In historical event logs, names of inactive staff are visually distinguished (e.g., greyed out or with an "(inactive)" label).
5. **Reporting Access**: Reports can still filter by all staff names, including inactive ones, for complete historical accountability.

**Implementation Status:**
- The `Staff` model includes an `is_active` boolean field, defaulting to `true`.
- The staff management UI includes "Add Staff," "Deactivate Staff," and "Reactivate Staff" capabilities.
- Only active staff are included in attribution dropdowns in the frontend.
- API endpoints for staff list retrieval include an optional `include_inactive` parameter.

#### 3.3.2 Student Authentication: Email-Based Confirmation
Students do not have accounts or passwords. Instead, their approval for a print job is handled via a secure, one-time-use email link.

**Confirmation Flow**:
- **Secure Tokens**: When a job is approved by staff, the backend generates a unique, cryptographically-signed token using a library like `itsdangerous`.
- **Token-Based URL**: This token is embedded into a URL that points to the frontend's confirmation page (e.g., `/confirm/<token>`).
- **Time-Limited Expiration**: The token is set to expire after a configured period (e.g., 72 hours) to ensure decisions are made in a timely manner. The system includes workflows for students to request a new link if theirs expires.
- **Stateless**: This process is entirely stateless. The system validates the token without requiring any kind of persistent session or cookie on the student's side.

#### 3.3.3 Security & Accountability
- **Comprehensive Audit Trail**: Every staff action is logged with:
    - `triggered_by`: The name of the staff member who performed the action.
    - `workstation_id`: The computer from which the action was performed.
- **File Operations**: All file movements and modifications are fully attributed.
- **Admin Actions**: Override and manual actions are fully attributed.
- **Security Benefits**: While using shared workstation passwords, this model prevents anonymous actions, which is the primary security and management risk. When a staff member leaves, they are simply removed from the active staff list in the configuration, preventing them from being selected in the attribution dropdown.

---
**Authentication**

*Note: Authentication is handled by a simple, custom-built workstation login system.*

*   `POST /auth/login`
    *   **Description**: Authenticates a workstation.
    *   **Body**: `{ "workstation_id": "front-desk", "password": "shared-password" }`
    *   **Success (200)**: `{ "token": "workstation-jwt" }`
    *   **Error (401)**: `{ "message": "Invalid workstation ID or password" }`

*   **JWT Validation Middleware**: All protected endpoints validate the workstation JWT in the `Authorization: Bearer <token>` header. The middleware makes the `workstation_id` available to the request context.

### 3.4 Route Handler Architecture

The system uses a comprehensive route handler architecture that integrates with the orchestrated service layer:

**Route Handler Organization**:
- **jobs.py**: Main job management endpoints using JobOrchestrationService
- **jobs_staff.py**: Staff-specific job operations with validation
- **admin.py**: Administrative operations and system management
- **auth.py**: Workstation authentication with environment-based configuration
- **submit.py**: Student submission endpoints with comprehensive validation
- **payment.py**: Payment processing and financial operations
- **analytics.py**: Analytics and reporting endpoints
- **staff.py**: Staff management operations
- **health.py**: System health monitoring endpoints
- **catalog.py**: Catalog management and configuration endpoints
- **diag.py**: Diagnostic and troubleshooting endpoints
- **export.py**: Data export and reporting endpoints
- **monitoring.py**: System monitoring and metrics endpoints

**Route Handler Integration Pattern**:
- **Service Composition**: Routes use JobOrchestrationService for unified interface
- **Validation Layer**: ValidationService provides consistent input validation
- **Response Standardization**: ResponseService ensures consistent API responses
- **Error Handling**: Centralized error handling with proper HTTP status codes
- **Rate Limiting**: Flask-Limiter integration for abuse protection
- **Authentication**: JWT middleware for workstation authentication

**Testing Architecture**:
- **Unit Tests**: Comprehensive test suite for business logic services (`backend/tests/unit/`)
- **Integration Tests**: End-to-end workflow testing (`backend/tests/tests/integration/`)
- **Test Coverage**: Service-level testing with mock dependencies
- **Test Patterns**: Simple tests for business logic, integration tests for workflows
- **Mock Framework**: Jest and React Testing Library for frontend components

### 3.5 Job Lifecycle & Workflow Management

The system manages 3D print jobs through a comprehensive, event-driven workflow that ensures accountability, file integrity, and clear communication with students.


#### 3.4.1 Core Workflow Principles

**File Resilience Strategy**: 
- **metadata.json** files accompany every job file, containing essential job details for data resilience
- **Original File Preservation**: Student uploads are preserved throughout the entire lifecycle for historical reference and re-slicing needs
- **Authoritative File Tracking**: System tracks both original uploads and staff-modified files (e.g., sliced versions)

**Standardized File Naming**: `FirstAndLastName_PrintMethod_Color_SimpleJobID.original_extension`

**Event-Driven Architecture**: Every action generates immutable event logs with staff member attribution for complete audit trails.

#### 3.4.2 Workflow Status Progression

> **Note on Status Naming:** Throughout this document and codebase, job status identifiers are standardized in UPPERCASE format (e.g., `UPLOADED`, `PENDING`, `READYTOPRINT`) for all internal references, API endpoints, and database values. Directory names use PascalCase (e.g., `Uploaded/`), and user-facing displays use Title Case with spaces (e.g., "Ready to Print").

**1. UPLOADED Status**
* **Trigger:** Student completes submission through Next.js form, backend processes `POST /api/submit`
* **File Operations:**
  * File validation (type, size, format) with comprehensive error handling
  * Standardized rename: `JaneDoe_Filament_Blue_123.stl`
  * Storage location: `storage/Uploaded/`
  * **metadata.json** creation with complete job context
  * Database updates: `file_path`, `original_filename`, `display_name`, `metadata_path`
  * Thumbnail generation (asynchronous, failure-tolerant)
* **System Actions:** 
  * File validation includes comprehensive security checks and header validation
  * Duplicate submission detection prevents identical active jobs
  * Job locking system prevents concurrent edits
  * Event logging captures all actions with staff attribution

**Student Submission UI/UX (Corresponds to 'Uploaded' Status)**
    **Page Flow**:
        `React Route (/submit)` → `Upload Form Page` → `API POST to /api/submit` → `File Validation & Job Creation` → `React Route (/submit/success?job=<id>)` OR `Upload Form Page with Errors`
 **Upload Form (`/submit`)**:
  **Form Introduction**: Comprehensive warning text at the top of the form stating:
    "Before submitting your model for 3D printing, please ensure you have thoroughly reviewed our Additive Manufacturing Moodle page, read all the guides, and checked the checklist. If necessary, revisit and fix your model before submission. Your model must be scaled and simplified appropriately, often requiring a second version specifically optimized for 3D printing. We will not print models that are broken, messy, or too large. Your model must follow the rules and constraints of the machine. We will not fix or scale your model as we do not know your specific needs or project requirements. We print exactly what you send us; if the scale is wrong or you are unsatisfied with the product, it is your responsibility. We will gladly print another model for you at an additional cost. We are only responsible for print failures due to issues under our control."
  **Fields**:
    * Student Name (text input, required, 2-100 characters)
    * Student Email (email input, required, validated format, max 100 characters)
    * Discipline (dropdown options, required): Art, Architecture, Landscape Architecture, Interior Design, Engineering, Hobby/Personal, Other
    * Class Number (text input, required, format example: "ARCH 4000 or N/A", max 50 characters, allows "N/A")
    * Print Method (dynamic dropdown, populated from catalog, required) with contextual descriptions:
      - Methods populated dynamically from catalog configuration (typically: "Filament", "Resin")
      - Resin: Description: Super high resolution and detail. Slow. Best For: Small items. Cost: More expensive.
      - Filament: Description: Good resolution, suitable for simpler models. Fast. Best For: Medium items. Cost: Least expensive.
    * Color Preference (dynamic dropdown, disabled until Print Method selected, required):
      - **Dynamic Population**: Colors loaded from catalog based on selected print method
      - **Real-Time Updates**: Form automatically reflects new colors added via admin dashboard
      - **Method Filtering**: Only shows colors available for the selected print method's materials
      - **Example Colors**: Filament typically includes True Red, Blue, Black, White, etc.; Resin typically includes Black, White, Gray, Clear
    * Printer Dimensions (informational section only, no user input): **CRITICAL EDUCATIONAL SECTION** - Displays complete scaling guidance to force students to measure and consider sizing. Shows text: "Will your model fit on our printers? Please check the dimensions (W x D x H): Filament - Prusa MK4S: 9.84" × 8.3" × 8.6" (250 × 210 × 220 mm), Prusa XL: 14.17" × 14.17" × 14.17" (360 × 360 × 360 mm), Raise3D Pro 2 Plus: 12" × 12" × 23.8" (305 × 305 × 605 mm). Resin - Formlabs Form 3: 5.7 × 5.7 × 7.3 inches (145 x 145 x 175 mm). Ensure your model's dimensions are within the specified limits for the printer you plan to use. If your model is too large, consider scaling it down or splitting it into parts. For more guidance, refer to the design guides on our Moodle page or ask for assistance in person. If exporting as .STL or .OBJ you MUST scale it down in millimeters BEFORE exporting. If you do not the scale will not work correctly."
    * Printer Selection (dynamic dropdown, populated from catalog, required): Students select which printer they think their model fits on after reviewing the dimensions above:
      - **Dynamic Population**: Students select from active printers supporting their chosen print method
      - **Real-Time Updates**: Form automatically reflects new printers added via admin dashboard  
      - **Method Filtering**: Only displays printers that support the selected print method
      - **Educational Purpose**: Forces students to actively choose based on dimensional constraints shown above
      - **Current Printers**: Typically includes Prusa MK4S, Prusa XL, Raise3D Pro 2 Plus (Filament), Formlabs Form 3 (Resin)
    * Minimum Charge Consent (Yes/No dropdown, required): "I understand there is a minimum $3.00 charge for all print jobs, and that the final cost may be higher based on material and time." Students must select "Yes" or "No"
    * File Upload (input type `file`, required, .stl/.obj/.3mf only, 50MB max size)
    * Submit Button
  **Client-Side Validation**:
    - Real-time file validation (type and size checking on selection)
    - Email format validation on blur
    - Color dropdown state management (disabled until method selected)
    - Visual error feedback with red borders and error messages
    - Form submission validation for all field types
    - Error scrolling to first error on submission attempt
    - Submit button loading state during submission
  * Server-Side Validation: All client-side checks re-validated by the Flask API.
- Success Page (/submit/success?job=<id>):
  * Displays a success message within the React application.
  * Shows the Job ID for reference.
  * Provides clear "next steps" messaging (e.g., "Your submission is now with staff for review. You will receive an email if it's rejected or approved, asking for your final confirmation before printing.").

**2. PENDING Status (Awaiting Student Confirmation)**
* **Trigger:** Staff member approves a job through the dashboard, triggering a `POST /api/jobs/<id>/approve` request.
* **Explicit Authoritative File Selection**: To eliminate ambiguity, the system requires staff to explicitly designate the correct file during the approval process. The workflow is as follows:
  1.  When a staff member initiates an approval, the frontend requests a list of potential authoritative files from the backend.
  2.  The backend scans the job's directory (e.g., `storage/Uploaded/`) for the original file and any other valid model files (e.g., `.stl`, `.obj`, `.3mf`, `.form`).
  3.  This list is presented to the staff member within the approval modal, allowing them to explicitly select the file that should be used for printing. The UI will recommend the most recently modified slicer file as a default.
  4.  The approval request sent to the backend includes the filename of the selected authoritative file.
* **File Operations:**
  * The explicitly chosen authoritative file and its `metadata.json` are moved from `storage/Uploaded/` → `storage/Pending/`. If the chosen file was not the original, the original student upload is also moved to `storage/Pending/` for archival purposes but is no longer considered the authoritative version.
  * The database is updated with the new `file_path`, `display_name`, and `metadata_path`.
* **System Actions:**
  * Staff member attribution for the approval action is logged.
  * Print parameters (weight, time, cost) submitted by the staff are validated.
  * A secure confirmation token is generated for the student.
  * An approval email, containing the job details and confirmation link, is queued for sending.

**Staff Approval UI/UX (Corresponds to 'Pending' Status)**
- **Interactive Approval Modal**: The modal will feature:
  - **Authoritative File Selection**: A list of radio buttons showing all valid model files found in the job's directory. The most recently modified non-original file will be pre-selected as a suggestion. The staff member **must** confirm or change this selection.
  - **Required Input Fields**: Standard inputs for weight (grams) and print time (hours).
  - **Calculated Cost**: A read-only field displaying the calculated cost based on the inputs.
  - **Action Buttons**: "Cancel" and "Approve" buttons. The "Approve" button is disabled until a file is selected and all required fields are filled.

#### 3. Rejected
* **Trigger:** Staff reviews an "Uploaded" job and clicks "Reject". The frontend sends a `POST` request to `/api/jobs/<id>/reject`.
* **File Operations:** The job's files remain in their current location (e.g., `storage/Uploaded/`). The job's status is updated to `REJECTED`, and it will be moved to `storage/Archived/` later by the standard data retention and archival process (see Section 5.7). The original uploaded file is preserved.
* **Key Actions:** Staff selects reasons in the React UI, backend logs event. Asynchronous task (SendRejectionEmail) triggered.
* **Email Notification:** Rejection email sent via task queue including reasons.

**Staff Rejection UI/UX (Corresponds to 'Rejected' Status)**
- Rejection Confirmation Modal: Title, message, checkbox group for common reasons, textarea for custom reason, cancel/reject buttons.

#### 4. ReadyToPrint
* **Trigger:** Student clicks the confirmation link. The link opens the React frontend, which sends a `POST` request to `/api/confirm/<token>`.
* **File Operations:** The authoritative file and metadata.json are moved from storage/Pending/ to storage/ReadyToPrint/. job.file_path is updated.
* **Key Actions:** Backend validates token, logs event. job.student_confirmed set to True.
* **Email Notification:** None.

#### 5. Printing
* **Trigger:** Staff clicks "Mark Printing" in the React UI. The frontend sends a `POST` request to `/api/jobs/<id>/mark-printing`.
* **File Operations:** The authoritative file and metadata.json are moved from storage/ReadyToPrint/ to storage/Printing/. job.file_path is updated.
* **Key Actions:** Staff starts print, API logs event.
* **Email Notification:** None.

#### 6. Completed
* **Trigger:** Staff clicks "Mark Complete" in the React UI. The frontend sends a `POST` request to `/api/jobs/<id>/mark-complete`.
* **File Operations:** The authoritative file and metadata.json are moved from storage/Printing/ to storage/Completed/. job.file_path is updated.
* **Key Actions:** Staff removes print, API logs event. Asynchronous task (SendCompletionEmail) triggered.
* **Email Notification:** Completion email sent via task queue.

#### 7. PaidPickedUp
* **Trigger:** Staff clicks "Mark Picked Up" in the React UI. The frontend sends a `POST` request to `/api/jobs/<id>/mark-picked-up`.
* **File Operations:** The authoritative file and metadata.json are moved from storage/Completed/ to storage/PaidPickedUp/. job.file_path is updated.
* **Key Actions:** Student collects print, API logs event.
* **Email Notification:** None.

#### 8. Archived
* **Trigger:** An administrator triggers the archival process via the dashboard, sending a `POST` request to `/api/v1/admin/archive`. The API will process all jobs in `PaidPickedUp` or `Rejected` status that are older than the configured retention period (e.g., 45 days).
* **File Operations:** The authoritative file and `metadata.json` for each eligible job are moved from their current location (e.g., `storage/PaidPickedUp/`) to `storage/Archived/`. The job's `file_path` is updated accordingly.
* **Key Actions:** The job status is changed to `ARCHIVED`. An `Event` is logged for each job that is archived, attributed to the admin who triggered the action.
* **UI/UX**: The admin dashboard will feature a data management section where an admin can review jobs eligible for archival and trigger the process with a confirmation dialog.

**General Staff Dashboard and Job Interaction UI/UX**
- Main Dashboard Layout (/dashboard): Header, status tabs, job list
- Job Row Details: Thumbnail, student name/email, display name, submission date/time, printer/color/material, cost, action buttons, event log viewer
- Job Detail View/Modal: All job metadata, editable fields, calculated cost, full event history, staff notes (editable notes section for staff/internal use), admin override controls
- **Direct Deletion**: A 'Delete' button will be available on job cards/modals for jobs in `UPLOADED` or `PENDING` status. This action is protected by a confirmation dialog to prevent accidental deletion.
- **Time-Limited Revert Actions**: For recent status changes (e.g., `Mark Complete`), a "Revert" button will be conditionally displayed for a short period, allowing staff to quickly correct errors without needing an admin.
- **Search and Filtering**: Dashboard supports search by student name, email, class number, and filtering by printer, discipline, submission date
- **Admin Override Capabilities**: Staff can manually override broken workflows:
  - Manually confirm jobs (bypass student confirmation)
  - Resend approval/confirmation emails with new tokens
  - Arbitrarily change job status for debugging purposes
  - Handle Print Failures: Mark a job in the `PRINTING` state as failed, log the reason, and return it to the `READYTOPRINT` queue without requiring student re-approval.
  - All override actions logged in Event table with `triggered_by = 'admin'`

**Administrative Controls & Manual Overrides UI/UX**
- Status override controls, file management controls, email control during overrides, other admin actions
- **System Health Panel**: A dedicated section in the dashboard for system auditing. It will allow an admin to:
  - Trigger a new file system integrity scan.
  - View the report from the last scan, listing orphaned files and broken database links.
  - Take explicit action on reported items, such as deleting selected orphaned files.
- Notes Management: Staff can add/edit notes for any job. All changes are saved and visible to staff only.
- **Emergency Override Modal**: allows status changes with reason logging
- **Print Failure Modal**: When marking a print as failed, a modal will appear requiring staff to log a reason for the failure before confirming the action to move the job back to the `READYTOPRINT` queue.
- **Resend Email Controls**: Generate new confirmation tokens when original links expire

**Fallback/Manual Processes for Pending Status:**
- If a student doesn't confirm within the token expiry period (e.g., 72 hours), the job is visually flagged on the staff dashboard (e.g., with a yellow warning icon) so staff can take proactive measures.
- Staff can manually resend a confirmation email (generating a new token), which is a rate-limited action.
- Staff can manually mark a job as confirmed if email confirmation fails (e.g., student confirms verbally). This action is logged.
- Students have a self-service option on the "expired link" page to request a new, rate-limited confirmation email.

**Expired Token and Resend Workflow (Student-Facing)**
- **Expired Link Handling**: When a student clicks an invalid or expired confirmation link, they are directed to a user-friendly frontend page (`/confirm/expired?job_id=...`).
- **Clear Messaging**: This page will clearly state that the link has expired and explain the next steps.
- **Self-Service Resend**: The page will feature a "Resend Confirmation Email" button. Clicking this triggers a new, public, but rate-limited API endpoint to send a fresh email with a new token.
- **Throttling**: To prevent abuse, this self-service resend option is limited (e.g., once per hour per job). The UI should reflect this, disabling the button and showing a countdown if a recent request has been made.

**UI/UX Implementation Notes:**
- All status changes must provide immediate visual feedback
- Use professional loading indicators for async operations
- Implement smooth transitions between states
- Provide clear error states with recovery options
- Use consistent iconography across all status indicators
- Follow modern web animation guidelines

#### 3.4.3 Implemented Workflow Enhancements
**Concurrency Control**:
- **Job Locking System**: Prevents multiple staff members from editing the same job simultaneously
- **Lock Management**: Automatic lock acquisition on modal open, extension via heartbeat, release on close
- **Conflict Resolution**: Clear UI feedback when jobs are locked by other users
- **Admin Override**: Administrators can force-unlock stuck locks with audit logging

**File Security & Validation**:
- **Comprehensive File Validation**: File header validation for STL, OBJ, 3MF, and ZIP-based formats
- **Security Validation**: Path traversal prevention, dangerous character detection, filename sanitization
- **Duplicate Detection**: File content hashing prevents duplicate active submissions
- **Atomic File Operations**: Resilient file operations with staging areas and rollback capabilities

**Error Handling & Recovery**:
- **Standardized Error Responses**: Consistent error format across all API endpoints
- **Frontend Error Boundaries**: Component-level error isolation preventing full page crashes
- **Graceful Degradation**: Fallback UI and retry mechanisms for failed operations
- **Error Reporting**: Centralized error reporting with backend integration and analytics

**Performance Optimization**:
- **Intelligent Caching**: Request deduplication, adaptive TTL, and performance statistics
- **Optimized API Patterns**: Adaptive polling, request batching, and activity-based optimization
- **Background Processing**: Asynchronous task processing for emails, monitoring, and file operations
- **Real-time Updates**: Auto-refreshing dashboard with visual and audio notifications

## 4. Technical Deep Dive: Direct File Access

> **Note:** All actions listed below automatically trigger an entry in the `Event` log as described in Section 3.2 and 3.4.

### 4.1 Deployment Topology: Central Backend, Multiple Clients

To ensure system stability and simplify management, the system is designed with a centralized backend architecture.

1.  **Backend Host (One Computer):**
    *   A single, designated staff PC or server acts as the **backend host**. This machine is responsible for running the entire Docker Compose stack, which includes:
        *   The Flask API (port 5000)
        *   The PostgreSQL Database
        *   The Redis message broker and RQ worker
    *   This centralized approach prevents database locking issues, simplifies backups, and ensures a single source of truth for all data and operations.

2.  **Client Workstations (Up to Three Computers):**
    *   Up to three additional lab computers can act as **client workstations**.
    *   These machines **do not run any server code**. Staff simply access the Next.js dashboard by navigating to the backend host's network IP address in a web browser (e.g., `http://192.168.1.100:3000`).
    *   The only software required on client workstations is the `SlicerOpener` protocol handler, which enables them to open files directly from the browser.

3.  **Shared Network Storage:**
    *   A core requirement is a shared network storage location (e.g., a network drive or NAS).
    *   **All computers** (the backend host and all client workstations) must mount this shared storage at the **exact same path** (e.g., `Z:\storage\` on Windows or `/mnt/3dprint_files` on Linux).
    *   Path consistency is critical for the `SlicerOpener` protocol handler and the Flask API to correctly locate and manage job files.

4.  **Database Strategy (PostgreSQL):**
    *   The PostgreSQL database runs in a Docker container on the backend host.
    *   This provides superior concurrency, data integrity, and scalability compared to file-based databases like SQLite, which is essential for a multi-user environment with background tasks.

**Implementation Status**: The deployment configuration is fully implemented:
- **Development Environment**: `docker-compose.dev.yml` (225 lines) with hot reloading and development features
- **Production Environment**: `docker-compose.prod.yml` (213 lines) with optimized builds and security hardening
- **Resource Limits**: Backend limited to 1GB RAM, 1 CPU; Frontend limited to 512MB RAM, 0.5 CPU
- **Health Checks**: Automated health monitoring for both backend and frontend services
- **Security**: No-new-privileges security option enabled for all containers
- **Logging**: JSON-formatted logs with rotation (10MB max, 3 files)
- **Networking**: Dedicated bridge network for service communication
- **Volume Mounts**: Source code mounted for development, storage directory shared across containers

**Environment Variable Configuration**:
- **Database**: `DATABASE_URL` (required, prevents SQLite fallback in production)
- **Authentication**: `SECRET_KEY`, JWT cookie settings, workstation passwords
- **Email**: Office 365 SMTP configuration (`MAIL_SERVER`, `MAIL_USERNAME`, etc.)
- **File Handling**: `STORAGE_PATH`, `ALLOWED_FILE_EXTENSIONS`, `MAX_FILE_SIZE_MB`
- **Redis**: `REDIS_URL`, `REDIS_PASSWORD` for background task processing
- **Frontend**: `NEXT_PUBLIC_API_URL`, `FRONTEND_PUBLIC_URL` for API communication
- **System**: `FLASK_ENV`, `APP_VERSION`, `ENVIRONMENT_BANNER` for operational settings

### 4.2 Custom Protocol Handler
- A custom `print3d://` protocol is registered on all staff computers.
- Example URL: print3d://open?path=Z:\storage\Uploaded\JaneDoe_Filament_Blue_123.stl

### 4.3 File Opening Solution
1.  **Custom Protocol Registration (Windows Example)**:
    ```
    Windows Registry:
    HKEY_CLASSES_ROOT\print3d\shell\open\command
    (Default) = "C:\Path\To\SlicerOpener.exe" "%1"
    ```
    Automated setup provided via `register.bat` file for staff machines.
    
2.  **Helper Application (`SlicerOpener.py`)**:
    *   Fully operational Python script (compiled to `.exe` using PyInstaller) serving as the protocol handler.
    *   **External Configuration**: The application loads settings from `config.ini` located in the same directory. The configuration defines:
        -   The authoritative storage base path (`AUTHORITATIVE_STORAGE_BASE_PATH`).
        -   Recognized slicer applications with name, executable path, and supported file extensions.
        -   Local log file path for audit trails.
    *   **GUI Feedback**: The application uses `tkinter.messagebox` for all user-facing feedback:
        -   Clear error dialogs for failures (invalid URL, security validation failed, file not found, no compatible slicer).
        -   Success dialog confirming which file was opened in which slicer.
    *   **Security Validation**: Performs robust security validation ensuring requested paths are descendants of `AUTHORITATIVE_STORAGE_BASE_PATH` preventing directory traversal attacks.
    *   **Slicer Dispatch Logic**: Parses file extensions and matches with configured compatible slicers:
        -   Single compatible slicer: Opens file directly
        -   Multiple compatible slicers: Displays GUI selection dialog
        -   No compatible slicers: Shows GUI error dialog
    *   **Comprehensive Logging**: All actions, configuration loads, validation results, and errors logged to `sliceropener.log` for auditing.

**Implementation Status**: The SlicerOpener protocol handler is fully implemented and deployed:
- **Source Code**: `SlicerOpener/SlicerOpener.py` (210 lines)
- **Compiled Executable**: `SlicerOpener/SlicerOpener.exe` (11MB, PyInstaller build)
- **Configuration**: `SlicerOpener/config.ini` and `SlicerOpener/config.example.ini`
- **Registry Setup**: `SlicerOpener/register.bat` for Windows protocol registration
- **Build System**: `SlicerOpener/SlicerOpener.spec` for PyInstaller configuration
- **Documentation**: `SlicerOpener/README.md` with setup and usage instructions
- **Logging**: `SlicerOpener/sliceropener.log` for operational debugging
- **Distribution**: `SlicerOpener/releases/` contains packaged releases
    ```python
    # SlicerOpener.py (Conceptual, with slicer selection)
    import sys, subprocess, os, configparser
    from urllib.parse import urlparse, parse_qs
    import tkinter
    from tkinter import messagebox

    def load_config(config_path='config.ini'):
        parser = configparser.ConfigParser()
        if not parser.read(config_path):
            raise FileNotFoundError(f"Configuration file not found at {config_path}")
        
        config = {
            'storage_base_path': parser.get('main', 'AUTHORITATIVE_STORAGE_BASE_PATH'),
            'slicers': []
        }
        for section in parser.sections():
            if section.startswith('slicer_'):
                config['slicers'].append({
                    'name': parser.get(section, 'name'),
                    'path': parser.get(section, 'path'),
                    'extensions': [ext.strip() for ext in parser.get(section, 'extensions').split(',')]
                })
        return config

    def get_compatible_slicer(file_path, slicers):
        file_ext = os.path.splitext(file_path)[1].lower()
        for slicer in slicers:
            if file_ext in slicer['extensions']:
                return slicer
        return None

    def show_error_popup(title, message):
        tkinter.Tk().withdraw() # Hide the main tkinter window
        messagebox.showerror(title, message)

    def show_success_popup(title, message):
        tkinter.Tk().withdraw() # Hide the main tkinter window
        messagebox.showinfo(title, message)
    
    def ask_slicer_choice(slicer_options):
        # This function must create a GUI dialog to ask the user to pick from a list of slicer names.
        # It should return the chosen slicer's dictionary object or None if cancelled.
        # (Conceptual implementation using tkinter would go here)
        pass

    # --- Main conceptual execution logic ---
    # 1. Load configuration from 'config.ini'.
    # 2. Parse the input URI and validate the file path for security.
    # 3. Find all compatible slicers from the configuration based on the file extension.
    # 4. Check the number of compatible slicers found:
    #    - If zero: Call show_error_popup("No Slicer Found", "No compatible slicer is configured for this file type.")
    #    - If one: Launch that slicer directly with the file path. Call show_success_popup(...).
    #    - If more than one: Call ask_slicer_choice(list_of_slicers).
    #      - If a choice is made, launch the chosen slicer. Call show_success_popup(...).
    #      - If the user cancels, do nothing.
    # 5. Handle all potential errors (file not found, slicer exe not found, etc.) with show_error_popup().
    ```

3.  **Web Dashboard Integration**:
    *   The "Open File" button in job cards generates `print3d://` links dynamically using `job.file_path`.
    *   Dashboard provides Windows path conversion for proper protocol handler integration.
    *   Fallback path copying available if protocol handler fails.

### 4.4 SlicerOpener Protocol Handler: Operational Implementation
- **Purpose**: Enables staff to open 3D print job files directly from the web dashboard in their local slicer software with a single click.
- **Current Protocol**: Uses `print3d://` scheme exclusively for clean operation.
- **Security Implementation**:
  - Validates files are within `AUTHORITATIVE_STORAGE_BASE_PATH` from `config.ini`
  - Resolves all paths to absolute form with descendant validation
  - Blocks path traversal attempts (..\, ../) and symbolic link exploits
  - Logs all security validation failures with clear GUI error dialogs
- **Operational Slicer Detection**:
  - Verifies requested file exists before launch attempts
  - Loads compatible slicers from `config.ini` based on file extensions
  - Single compatible slicer: Launches automatically
  - Multiple compatible slicers: Presents GUI selection dialog
  - No compatible slicers: Displays clear error dialog with configuration guidance
- **Audit Trail & Logging**:
  - Comprehensive logging to rotating log file (`sliceropener.log`)
  - Log entries include timestamp, URL, resolved path, validation results, and actions
  - Complete audit trail for security violations, file errors, and slicer launches
- **GUI Error Handling**:
  - Uses `tkinter` for all user-facing dialogs ensuring clear feedback
  - Professional success/error dialogs for all conditions
- **Dashboard Integration**:
  - Job cards generate `print3d://open?path=<urlencoded_path>` links
  - "Open File" button available for appropriate job statuses
  - Windows path conversion handles proper file system integration
  - Fallback path copying when protocol handler unavailable
- **Deployment & Registration**:
  - Automated Windows registry setup via `register.bat`
  - Complete installation package with executable and configuration templates
  - Per-workstation configuration with shared storage path consistency

## 5. Operational Considerations

### 5.1 System Components & Architecture

**Backend Components (Operational):**
- **Flask API Application**: Operational RESTful API with Blueprint organization, PostgreSQL database integration, and comprehensive job/event models
- **Workstation Authentication**: Live JWT-based authentication for workstations with per-action staff attribution
- **File Management Services**: Operational file handling, cost calculation algorithms, and resilient `metadata.json` generation
- **Asynchronous Task Processing**: Active RQ integration for email delivery and thumbnail generation
- **Custom Protocol Handler**: Deployed `SlicerOpener.py` application with security validation and slicer integration
- **Comprehensive Monitoring**: Live system monitoring with CPU, memory, disk, and network metrics collection
- **Health Check Systems**: Operational health endpoints for database, Redis, storage, and system resources

**Frontend Components (Live Production):**
- **Next.js Application**: Deployed App Router architecture with TypeScript, Tailwind CSS, and comprehensive shadcn/ui component library
- **Authentication Flow**: Operational login form for workstations, JWT storage in browser, and API request inclusion
- **Dashboard Interface**: Live real-time updating dashboard with background sound notifications, visual alerts, job age tracking, and advanced filtering
- **Interactive Workflows**: Operational approval/rejection modals, inline notes editing, and comprehensive form validation
- **Student Submission Interface**: Live dynamic form with catalog integration, contextual validation, progressive disclosure, and educational content
- **Admin Dashboard**: Operational dedicated admin interface with catalog management, staff management, system overrides, and monitoring
- **Analytics Dashboard**: Live comprehensive analytics and reporting interface with multiple visualization types
- **Error Boundaries**: Operational component-level error isolation with fallback UI and retry mechanisms

**Implementation Status**: The complete system is fully operational with comprehensive architecture:
- **App Router Pages**: All pages operational - Dashboard, submit, login, confirm, admin, analytics, staff-analytics
- **Dashboard Components**: All components live - Job cards, job lists, status tabs, modals, diagnostic panel
- **Modal System**: All modals operational - Approval, rejection, payment, review, status change, and confirmation dialogs
- **Error Handling**: Complete error boundaries, fallback UI, and retry mechanisms operational
- **Testing**: Comprehensive test suite with Jest and React Testing Library
- **Build System**: Both development and production Dockerfiles operational with optimized builds
- **Configuration**: All configuration files operational - Tailwind CSS, TypeScript, Jest, and Next.js

**Integration Components (Active Systems):**
- **API Communication Layer**: Operational frontend-backend integration with comprehensive error handling and retry logic
- **File Protocol System**: Active `print3d://` protocol with security validation and cross-application file opening
- **Email Notification System**: Operational automated email workflows with template management and delivery tracking
- **Audit & Logging System**: Live comprehensive event logging with individual user attribution and compliance-ready audit trails


### 5.2 Security Architecture & Considerations

#### 5.2.1 Authentication Security (Workstation & Attribution Model)
- **Shared Workstation Credentials**: Each physical computer terminal operates with its own shared password, providing streamlined access in a busy lab environment while avoiding individual password management.
- **Mandatory Staff Attribution**: Operational primary security control with mandatory, per-action attribution. Every state-changing operation requires staff member selection from a dropdown, ensuring all actions are logged and traceable to specific individuals.
- **Traceability**: Active combination of `workstation_id` and attributed `staff_name` provides complete audit trail for every critical action, effectively mitigating shared credential risks.
- **Session Management**: Operational secure JWTs for workstation sessions, with secure cookie handling and proper lifecycle management via middleware.
- **Staff List Management**: Live staff list management with immediate revocation - removing staff from the centralized list instantly prevents attribution to new actions, effectively blocking system access.

#### 5.2.2 Application Security (Operational)
- **Secure File Upload Handling**: Live comprehensive validation including file type verification, size limits, and content scanning
- **Student Confirmation Security**: Operational time-limited, cryptographically signed tokens using itsdangerous library with proper expiration handling
- **Path Traversal Prevention**: Active strict validation of all file paths with absolute path resolution and base directory containment checks
- **API Endpoint Protection**: All state-changing requests protected by operational workstation JWT authentication
- **Content Security Policy**: Implemented CSP headers to prevent XSS and other injection attacks

#### 5.2.3 System-Level Security (Active)
- **Network Share Permissions**: Configured read/write access for application server with restricted general user access
- **Protocol Handler Security**: `SlicerOpener.py` operates with robust security validation, logging, and safe file path handling
- **Database Security**: PostgreSQL running with connection encryption, user permissions, and security configurations
- **Dependency Management**: Active dependency monitoring with security update procedures
- **Environment Variable Protection**: All sensitive configuration secured in environment variables, never in code

#### Logging and Retention (Implemented):
- All application logs, including protocol handler access logs and error logs, stored with rotation enabled using JSON-formatted logging.
- Logs retained with automatic rotation (10MB max, 3 files) according to operational policies.

### 5.3 Deployment Considerations
The entire application stack is operationally deployed using Docker and Docker Compose, providing simplified setup and consistent development/production environments.

1.  **Dockerized Services**: The `docker-compose.dev.yml` and `docker-compose.prod.yml` files define operational services:
    *   `backend`: Operational Flask API application, served by Gunicorn in production.
    *   `frontend`: Live Next.js application running in production mode with optimized builds.
    *   `db`: PostgreSQL database service operational with persistent Docker volumes.
    *   `worker`: Active RQ background worker handling asynchronous tasks.
    *   `redis`: Operational Redis message broker for background worker queue with password authentication.

2.  **Deployment Process (Operational)**:
    *   **Host Machine Setup**: Designated lab computer or server actively hosting Docker containers with full Docker and Docker Compose installation.
    *   **Configuration & Secrets Management**:
        - **Current Method**: Environment-specific variables (database passwords, secret keys, API URLs) managed in `.env` files read by Docker Compose.
        - **Security Implementation**: Environment variables secured for production deployment while maintaining beginner-friendly setup.
    *   **Database Migrations**: Database schema managed by `Flask-Migrate` with proven manual deployment process:
        1.  Code updates deployed with `docker-compose build` for new images.
        2.  Database service started: `docker-compose up -d db`.
        3.  Migrations applied: `docker-compose run --rm backend flask db upgrade`.
        4.  Full application launch: `docker-compose up -d`.
        - **Operational Rationale**: Manual process proven reliable for beginner-level workflow, preventing race conditions and startup failures.
    *   **Launch Commands**: Complete operational deployment via single commands: `docker-compose -f docker-compose.dev.yml up -d` for development or `docker-compose -f docker-compose.prod.yml up -d` for production.

3.  **System Access (Live)**:
    *   Staff access Next.js frontend by navigating to backend host IP address in web browsers (e.g., `http://192.168.1.50:3000`).
    *   Next.js application operational with pre-configured Docker internal networking to backend service.

4.  **External Components (Deployed)**:
    *   **Network Storage**: Shared `storage/` directory mounted on Docker host machine with volume mounts allowing Flask API file operations.
    *   **SlicerOpener Protocol Handler**: `SlicerOpener.exe` and `config.ini` installed on all staff computers with shared network storage path configuration.

5. **CORS Configuration**: Production Flask API CORS settings operational with restricted domain access configured via environment variables.

### 5.3.1 Implemented Deployment Features
**Development/Production Separation**:
- **Separate Compose Files**: `docker-compose.dev.yml` and `docker-compose.prod.yml` with environment-specific configurations
- **Production Optimization**: Frontend runs in production mode, optimized builds, and security hardening
- **Development Features**: Volume mounts, hot reloading, and debugging capabilities
- **Environment Variables**: Separate `.env` files for development and production configurations

**Enhanced Health Monitoring**:
- **Health Check Endpoints**: Granular health checks for database, Redis, storage, and system resources
- **Monitoring Scripts**: Cross-platform monitoring scripts for Linux/Mac and Windows
- **Performance Monitoring**: Request timing, error rates, and slow endpoint detection
- **Structured Logging**: JSON-structured logging for production with automatic log rotation

**Security Hardening**:
- **Network Isolation**: Dedicated Docker networks for service communication
- **Redis Authentication**: Password-protected Redis with secure configuration
- **Resource Limits**: Memory and CPU limits for all containers
- **Security Options**: No-new-privileges and read-only mounts where appropriate

### 5.4 University Network Considerations
- Firewalls: May block custom protocols or outgoing connections for the helper app. Liaise with IT.
- Server Restrictions: University IT may have policies against running persistent servers or specific ports.
- Admin Rights: Registering protocol handlers or installing software might require admin rights. The helper app can be deployed to user-space if packaged correctly.
- Storage Quotas: Be mindful of file sizes and implement cleanup if quotas are restrictive.
- Alternative File Access: If custom protocol is unfeasible, a fallback could be instructing staff to copy a displayed network path, or a less ideal "download and open".
- **Email Deliverability**: To minimize the risk of emails being marked as spam, the outgoing mail server must be correctly configured with SPF and DKIM records. This should be coordinated with university IT.

### 5.5 Cost Matrix & Calculation (Operational)
- Filament Print Cost: $0.10 per gram (enforced in catalog configuration).
- Resin Print Cost: $0.20 per gram (enforced in catalog configuration).
- $3.00 minimum charge for all print jobs (system-enforced).
- Operational cost calculation based on dynamic catalog material pricing and job weight.

### 5.6 Metrics & Reporting (Live Implementation)
- **Usage Statistics**: Complete submission counts, trends, and printer utilization tracking via analytics dashboard.
- **Reporting Interface**: Operational CSV export system, comprehensive analytics views, and interactive charts.
- **Financial Reporting**: Live payment export functionality with date range filtering and staff attribution.
- **Real-Time Analytics**: Operational dashboard with overview metrics, trend analysis, and resource utilization charts.

### 5.7 Data Retention and Archival Policy
The system implements a two-stage process for data lifecycle management to ensure both data availability for a reasonable period and eventual cleanup.

- **Stage 1: Archival (Operational Semi-Automated)**
  - **Retention Period**: Job data and associated files for jobs in final states (`PaidPickedUp` or `Rejected`) are retained in active state for 45 days.
  - **Archival Process**: Jobs become eligible for archival after 45 days. Admin-triggered process (`POST /api/v1/admin/archive`) moves job status to `ARCHIVED` and relocates files to `storage/Archived/` directory. Database records preserved for historical purposes while cleaning active file storage. All actions logged in `Event` table.

- **Stage 2: Permanent Deletion (Operational Manual Trigger)**
  - **Deletion Policy**: Jobs in `ARCHIVED` state are retained for 1 year before becoming eligible for permanent deletion.
  - **Deletion Process**: Operational admin-triggered process (`POST /api/v1/admin/prune`) permanently deletes job database records and archived files. This destructive action requires explicit confirmation and is fully logged.

- **Active Jobs**: Jobs in `Uploaded`, `Pending`, `ReadyToPrint`, `Printing`, or `Completed` statuses are considered active and are not subject to this policy until they reach a final state.

### 5.8 Backup and Disaster Recovery
A comprehensive, automated backup strategy is critical for business continuity. This strategy covers both the PostgreSQL database and the shared file storage, with a clear recovery plan to minimize downtime and ensure data integrity.

**1. Automated Backup Strategy**
- **Automation & Synchronization**: A single, automated backup script will run daily during off-peak hours (e.g., 3:00 AM). The script will first execute the database dump and, immediately upon its completion, begin the file system backup. This sequential process minimizes the time window between the two snapshots, ensuring they are closely synchronized.
- **Database Backup**: The script will use `pg_dump` to create a complete SQL dump of the PostgreSQL database.
- **File Storage Backup**: The script will use a versioning backup tool like `rsync` to create an incremental backup of the entire `storage/` directory.
- **Secure Off-Site Storage**: Backups **must** be pushed to a secure, remote location that is physically separate from the application host (e.g., a university-provided secure network drive or a designated cloud storage bucket). This protects against data loss from local hardware failure or disaster.
- **Retention Policy**:
    - Daily backups are retained for 14 days.
    - A weekly backup (e.g., from Sunday) is retained for 2 months.
    - A monthly backup is retained for 1 year.
- **Monitoring & Alerts**: The backup script will log its execution and send an email alert to a designated admin address upon success or failure.

**2. Recovery Plan & Procedure**
This plan outlines the steps to restore the system to a functional state from a chosen backup set (a matching pair of database and file system backups).
- **Responsibility**: Lab staff are responsible for initiating and overseeing the recovery process.
- **Step-by-Step Restore Procedure**:
    1.  **Halt the System**: Stop all running application services using the `docker-compose down` command.
    2.  **Prepare for Restore**: Clear the current (corrupted or empty) Docker volumes for the database and the contents of the `storage/` directory on the host machine.
    3.  **Restore File System**: Copy the contents of the chosen file storage backup into the host's `storage/` directory.
    4.  **Restore Database**: Restore the database from the corresponding `pg_dump` backup file. This involves starting the `db` service, copying the SQL dump file into the container, and using the `psql` utility to load the data.
    5.  **Restart System**: Start all application services with `docker-compose up -d`.
    6.  **Verify Integrity**: Once the system is running, an administrator **must** immediately trigger a **System Health and Integrity Audit** (as defined in Section 5.9). This crucial final step identifies and allows for the correction of any minor inconsistencies between the restored database and file system that may have occurred if a job was being processed during the backup window.

**3. Backup Validation**
- To ensure backups are viable, lab staff are responsible for performing a test restore to a non-production environment on a quarterly basis. This validates both the integrity of the backups and the accuracy of the recovery plan.

### 5.9 System Health and Integrity Auditing (Operational)
The system includes a fully operational admin-triggered integrity audit system to identify and resolve discrepancies between database and file storage. This system actively prevents orphaned files and broken database links, serving as the recovery mechanism for incomplete file transactions.

- **Three-Way Integrity Scan (Live Implementation)**: The operational audit tool performs comprehensive scans:
    1.  **Filesystem to Database (Orphaned Files)**: Scans all `storage/` directories and verifies each job file has corresponding database entry. Files without database entries are flagged as "Orphaned."
    2.  **Database to Filesystem (Broken Links)**: Iterates through job records confirming `file_path` and `metadata_path` point to existing files. Missing files flagged as "Broken Links."
    3.  **Database to Filesystem (Stale Files)**: Identifies files sharing job IDs but located in directories mismatched with database status. Flags remnants of incomplete operations as "Stale" and safe for deletion.

- **Admin-Driven Resolution (Operational Dashboard)**: The audit system operates with safe, manual resolution:
    -   Generates detailed reports listing orphaned files, broken links, and stale files via `/api/v1/admin/audit/report`.
    -   Presents reports in operational "System Health" section of admin dashboard.
    -   Provides admin tools for safe issue resolution including orphaned file deletion and metadata repair via dedicated endpoints.
    -   All resolution actions logged in `Event` table with full staff attribution.

### 5.10 Professional UI Design Patterns (Operational Standards)
- **Card-style Dashboard Interface**: Operational card-based job display with responsive grid layout
- **Anti-redundancy Principles**: Implemented consistent information display without duplication
- **Time Display Management**: Live human-readable time formatting with color-coded age indicators
- **Display Name System**: Operational standardized job naming and file display conventions
- **Template Management**: Live email template system with HTML/text dual formatting

### 5.11 Development Implementation Lessons (Applied Knowledge)
- **Platform Compatibility**: PowerShell compatibility resolved for cross-platform development
- **Path Handling**: Operational robust file path management with Windows/Linux compatibility
- **Framework Integration**: Proven Flask-SQLAlchemy-Migrate integration patterns
- **Template Management**: Live email template system with fallback mechanisms
- **JavaScript Implementation**: Operational TypeScript patterns with React component architecture

**UI/UX Lessons (Applied Standards):**
- **Form Validation**: Operational real-time feedback with visual error states and scrolling
- **Error Guidance**: Implemented proper error scrolling to first invalid field
- **Loading States**: All async operations include comprehensive loading indicators
- **Accessibility**: Modern accessibility guidelines implemented throughout interface
- **Responsive Testing**: All UI components tested and operational across screen sizes
- **Keyboard Navigation**: Complete keyboard accessibility for all interactive elements

**Technical Lessons (Production Practices):**
- **File Operations**: Operational explicit success verification for all file system operations
- **System Logging**: Comprehensive file system operation logging implemented
- **Network Resilience**: Graceful network share disconnection handling operational
- **Email Operations**: Robust error handling implemented for all email workflows
- **Atomic Operations**: Atomic file operations implemented system-wide
- **Path Validation**: Comprehensive file path validation operational before all operations

**Process Lessons (Operational Procedures):**
- **Configuration Management**: All configuration changes documented in version control
- **Environment Separation**: Separate development and production environments operational
- **Email Testing**: Email template compatibility verified across multiple clients
- **Protocol Handler Maintenance**: Protocol handler registration verification procedures established
- **Change Logging**: Comprehensive system change logging implemented
- **Component Documentation**: All custom UI components documented with usage guidelines

### 5.12 Critical Success Factors (Achieved)
1. **File System Integrity (Operational):**
   - Live validation of file locations via health monitoring
   - Operational automated metadata.json consistency checks
   - Comprehensive error handling for all file operations
   - Implemented backup verification procedures

2. **User Experience (Delivered):**
   - Operational adherence to modern UI/UX design principles
   - Consistent feedback implemented for all operations
   - Clear error messages and recovery paths operational
   - Complete form validation and user guidance systems

3. **System Reliability (Active):**
   - Operational health checks for all system components
   - Comprehensive logging implemented for all operations
   - Graceful network issue handling operational
   - Documented backup procedures in place

4. **Staff Efficiency (Operational):**
   - Streamlined workflow processes implemented
   - Clear status indicators operational throughout interface
   - Direct file access operational via protocol handler
   - Complete error recovery procedures implemented

### 5.13 Known Issues and Workarounds (Resolved/Operational)
1. **Network Share Access (Handled):**
   - Operational retry logic implemented for file operations
   - File metadata caching operational where appropriate
   - Clear error messages operational for access issues
   - Complete recovery procedures documented and tested

2. **Protocol Handler (Managed):**
   - Regular verification procedures established for registry entries
   - Operational fallback procedures for failed operations
   - Complete documentation available for reinstallation
   - Comprehensive logging operational for all handler operations

3. **Email Delivery (Robust):**
   - Operational retry logic implemented for failed sends
   - Message queuing operational via RQ background tasks
   - Delivery success monitoring operational
   - SPF/DKIM requirements documented for university IT coordination

4. **UI Components (Production-Ready):**
   - Cross-browser testing completed and operational
   - Mobile responsiveness verified and implemented
   - Accessibility features documented and operational
   - Consistent styling maintained throughout application

### 5.14 Event Log Management and Data Retention

**Event Log Rotation Policy (Operational):**
- The `Event` table includes operational cleanup to prevent unlimited growth
- Events older than 180 days are archived or deleted based on operational policies
- Critical events (job creation, status changes, admin overrides) retain longer than routine events
- Database indexes operational on `job_id`, `timestamp`, and `event_type` for optimal query performance
- Regular cleanup procedures maintain database performance

**Event Storage Strategy (Active):**
- High-priority events: Retained for 1 year (job creation, approvals, rejections, completions)
- Medium-priority events: Retained for 180 days (status changes, email sends, file operations)
- Low-priority events: Retained for 90 days (dashboard views, search queries, routine operations)
- Archive format: JSON files organized by date for analysis

### 5.15 Student Resubmission Workflow (Operational)

**Rejected Job Resubmission (Active Process):**
- Students can submit new jobs after rejection - no automatic resubmission linking
- Original rejected jobs remain in system for staff reference and learning
- Staff notes from rejected jobs inform future submissions
- System supports independent submission tracking without cross-linking

**Handling Lab-Caused Print Failures (Operational):**
- Print failures due to lab issues handled via administrative action marking jobs as failed from `PRINTING` status.
- Action logs failure and reason, returns job to `READYTOPRINT` status for reprinting.
- No cost adjustment needed as original cost retained, no new student confirmation required.
- All actions fully logged for auditing with staff attribution.

**Resubmission Tracking (Future Enhancement):**
- Optional `parent_job_id` field to link resubmissions to original jobs
- Dashboard view to see submission history per student
- Analytics on common rejection reasons to improve student guidance

### 5.16 System Health and Service Monitoring (Operational)
The system includes operational health monitoring to ensure high availability and prevent silent failures of critical backend components. This is distinct from data integrity audit and focuses on live service status.

- **Health Check Endpoint**: Operational public, unauthenticated API endpoint (`GET /api/v1/health`) allows automated monitoring tools (UptimeRobot, university IT monitoring) to check system status without credentials.
- **Component Status Checks**: The health check verifies all critical infrastructure components:
    1.  **API Service**: Endpoint responding with `200 OK` confirms Flask API operational status.
    2.  **Database Connectivity**: Operational simple, non-locking queries (`SELECT 1`) confirm database reachability and responsiveness.
    3.  **Background Worker Connectivity**: Active connection checks to Redis message broker ensure background tasks can be queued and processed.
- **Alerting**: Operational monitoring with external service integration for automatic alert triggering (email, SMS) to system administrators when health checks fail, enabling rapid outage response.

### 5.17 Concurrency Control and Data Integrity (Operational Safeguards)
The system implements operational safeguards ensuring data consistency and preventing race conditions in the multi-user, multi-computer environment:

- **API-Level Job Locking (Operational)**: The system operates with robust, stateful, API-level locking preventing simultaneous conflicting actions on jobs.
    - **Lock Acquisition**: Before critical actions (approval modals), frontend requests backend locks. API sets `locked_by_user` field and `locked_until` timestamp (5 minutes future) on jobs.
    - **Lock Heartbeat**: During extended UI interactions, frontend automatically sends periodic heartbeat requests extending lock duration, preventing expiration during legitimate use.
    - **Lock Release**: Upon action completion/cancellation, frontend explicitly releases locks. All state-changing API endpoints guarantee lock release regardless of success/failure, preventing permanent job locks.
    - **Pre-Action Verification**: Frontend re-fetches latest job state (including lock/review status) before displaying state-changing UI. Changed data (other user reviewed/locked job) triggers user notification and action prevention.
    - **Conflict Handling**: Already-locked job attempts return `409 Conflict` errors including lock holder identity. UI gracefully handles with notifications ("This job is being edited by Jane Doe") and disables editing controls.
    - **Lock Status Display**: `GET /jobs` and `GET /jobs/<job_id>` endpoints include current lock status allowing UI to proactively display job lock states.
    - **Admin Override**: Automatic expiration serves as abandoned session fallback. Administrators operate dedicated API endpoints to forcibly release stuck locks with full audit trails.

- **Transactional File Operations (Operational)**: All workflows involving database updates and file system modifications operate with resilience against unexpected failures. Database remains the operational "source of truth" with inconsistency detection and correction capabilities.
    - **Resilient Workflow ("Copy, Update, then Delete") - Active**: Operational sequence replaces simple move operations:
        1.  **Copy**: Authoritative file copied to destination directory (e.g., from `/Uploaded` to `/Pending`).
        2.  **Update Database**: Database transaction updates job status and file path reflecting new location.
        3.  **Commit**: Database transaction committed. System "source of truth" correctly points to new file.
        4.  **Delete Original**: Original file deleted from source directory.
    - **Recovery Path (Operational)**: Crash occurring between steps 3-4 leaves system in database-consistent state with stale duplicate file in old directory. System Health and Integrity Audit operational to detect and resolve this scenario by identifying mismatched files.

### 5.18 Staff-Level Error Correction (Operational)
The system provides operational error correction capabilities handling common human errors gracefully without requiring administrator intervention. Staff can correct their own mistakes quickly and cleanly.

- **Contextual Revert Actions (Live)**: After staff members change job status, contextual "Revert" buttons appear in the UI.
- **Supported Reversions (Operational)**: Functionality available for specific, non-destructive transitions:
    - Reverting jobs from `COMPLETED` back to `PRINTING`.
    - Reverting jobs from `PAIDPICKEDUP` back to `COMPLETED`.
- **Operational Workflow**:
    - Revert actions use dedicated API endpoints (`POST /jobs/<job_id>/revert-completion`).
    - Backend validates revert action validity for job's current state.
    - Actions are transactional, ensuring both database status and file location are correctly rolled back.
    - `StatusReverted` events logged in job audit trails, including triggering staff member.
- **Operational Scope**: This is not a general "undo" feature. Does not apply to destructive actions or actions triggering external communications (student approval emails). Complex corrections require Admin Override workflow.

### 5.19 Duplicate Submission Handling (Operational)
The system implements operational content-based deduplication at API level preventing accidental or redundant job submissions.

- **File Content Hashing (Active)**: Upon every file upload via `POST /api/submit` endpoint, backend calculates SHA-256 hash of file contents.
- **Deduplication Logic (Operational)**: Before creating new jobs, API queries database for existing "active" jobs with same file hash and student email address.
    - "Active" jobs defined as any status before printing begins (`UPLOADED`, `PENDING`, `READYTOPRINT`).
- **Collision Handling (Live)**:
    - Identical active job found: submission rejected with `409 Conflict` error informing user of duplicate job existence.
    - No identical active job found: new job created with calculated `file_hash` stored in database.
- **Reprint Allowance (Operational)**: Logic allows students to submit same file again if previous job is `PRINTING`, `COMPLETED`, or other post-active state, supporting legitimate reprint requests.

### 5.20 Direct Job Deletion (Operational)
The system provides operational direct, permanent deletion capability for staff to efficiently remove erroneous, unwanted, or duplicate submissions.

- **Purpose (Active)**: Workflow operational for immediate active queue cleanup, distinct from standard job lifecycle archival.
- **Operational Scope**: Deletion is destructive action permitted only for jobs in `UPLOADED` or `PENDING` statuses. Cannot be performed on student-confirmed jobs or production queue entries.
- **Confirmation Protection (Implemented)**: Irreversible action protected by confirmation modal in frontend clearly stating permanent deletion of job and associated files.
- **Operational Workflow**:
    1.  Staff member clicks "Delete" button on eligible job, acquiring lock on job.
    2.  Confirmation modal appears. Upon confirmation, frontend sends `DELETE /api/v1/jobs/<job_id>` request.
    3.  Backend API validates job deletable status and requesting user lock ownership.
    4.  API executes deletion as transaction: permanently deletes job files from network storage, then deletes job record and associated event logs from database.
- **Auditing (Active)**: All delete actions logged to secure, system-level audit log recording job ID, student details, and performing staff member.

## 6. API Specification 

All endpoints will be prefixed with `/api/v1`. All responses will be in JSON format. Timestamps are in UTC ISO 8601 format.

---
**Authentication**

*Note: Authentication is handled by a simple, custom-built workstation login system.*

*   `POST /auth/login`
    *   **Description**: Authenticates a workstation.
    *   **Body**: `{ "workstation_id": "front-desk", "password": "shared-password" }`
    *   **Success (200)**: `{ "token": "workstation-jwt" }`
    *   **Error (401)**: `{ "message": "Invalid workstation ID or password" }`

*   **JWT Validation Middleware**: All protected endpoints validate the workstation JWT in the `Authorization: Bearer <token>` header. The middleware makes the `workstation_id` available to the request context.

**Authentication Headers for Protected Endpoints:**
*   `Authorization: Bearer <workstation_jwt>`
*   **Success**: Request proceeds with workstation context available
*   **Error (401)**: `{ "message": "Invalid or expired token" }`
*   **Error (403)**: `{ "message": "Insufficient permissions" }`

---
**Public System Health**

*   `GET /health`
    *   **Description**: Provides a simple health check of the backend services. Does not require authentication. Intended for use by automated monitoring tools.
    *   **Success (200)**: Returns the operational status of key components. Example: `{ "status": "ok", "timestamp": "...", "components": { "database": "ok", "workers": "ok" } }`
    *   **Error (503 Service Unavailable)**: Returns if a critical component is down. Example: `{ "status": "error", "timestamp": "...", "components": { "database": "ok", "workers": "error", "details": "Could not connect to message broker." } }`

---
**Student Submission**

*   `POST /submit`
    *   **Body**: `multipart/form-data` with fields for `student_name`, `student_email`, `file`, etc.
    *   **Success (201)**: Returns the newly created job object.
    *   **Error (400)**: Returns validation errors.
    *   **Error (409)**: `{ "message": "An identical active job has already been submitted.", "existing_job_id": "..." }`
    *   **Error (429)**: `{ "message": "Submission limit exceeded. Please try again later." }`

*   `POST /confirm/<token>`
    *   **Body**: (Empty)
    *   **Success (200)**: Returns the updated job object.
    *   **Error (404/400)**: If token is invalid or expired.
    *   **Error (410)**: `{ "message": "Confirmation link expired", "reason": "expired", "job_id": "abc123" }`

*   `GET /confirm/expired`
    *   **Query Params**: `?job_id=abc123`
    *   **Success (200)**: Returns job details and instructions for expired confirmation

*   `POST /submit/resend-confirmation`
    *   **Description**: Allows a student to request a new confirmation email for an unconfirmed job. This is a public but rate-limited endpoint.
    *   **Body**: `{ "job_id": "..." }`
    *   **Success (200)**: `{ "message": "A new confirmation email has been sent." }`
    *   **Error (404)**: If job ID is not found or job is already confirmed/rejected.
    *   **Error (429)**: `{ "message": "You can request a new email in X minutes." }`

---
**Staff Management**

*   `GET /staff`
    *   **Auth**: Required (Workstation JWT)
    *   **Query Params**: `?include_inactive=true` (optional, defaults to false)
    *   **Success (200)**: `{ "staff": [{"name": "Jane Doe", "is_active": true, "added_at": "timestamp"}, ...] }`

*   `POST /staff`
    *   **Auth**: Required (Workstation JWT)
    *   **Body**: `{ "name": "New Staff Name", "staff_name": "Admin User" }`
    *   **Success (201)**: `{ "name": "New Staff Name", "is_active": true, "added_at": "timestamp" }`
    *   **Error (409)**: `{ "message": "Staff member with this name already exists" }`

*   `PATCH /staff/:name`
    *   **Auth**: Required (Workstation JWT)
    *   **Body**: `{ "is_active": false, "staff_name": "Admin User" }`
    *   **Success (200)**: `{ "name": "Staff Name", "is_active": false, "added_at": "timestamp", "deactivated_at": "timestamp" }`
    *   **Error (404)**: `{ "message": "Staff member not found" }`

---
**Catalog Management**

*   `GET /catalog`
    *   **Description**: Gets the current catalog configuration with printers, materials, and colors
    *   **Rate Limit**: 60 per minute
    *   **Success (200)**: `{ "version": 5, "data": { "methods": ["Filament", "Resin"], "printers": [...], "materials": [...] }, "updated_by": "Admin", "updated_at": "timestamp" }`
    *   **Headers**: Cache-Control and ETag for client-side caching

*   `PUT /catalog`
    *   **Description**: Updates the catalog configuration (admin only)
    *   **Auth**: Required (Workstation JWT)
    *   **Rate Limit**: 10 per minute
    *   **Body**: `{ "data": { "methods": [...], "printers": [...], "materials": [...] } }`
    *   **Success (200)**: `{ "message": "Catalog updated successfully", "version": 6, "updated_by": "Admin", "updated_at": "timestamp" }`
    *   **Error (400)**: Validation errors for invalid catalog structure
    *   **Validation**: Full schema validation ensures proper printer/material/color relationships

*   `GET /catalog/version`
    *   **Description**: Gets just the catalog version for lightweight polling
    *   **Rate Limit**: 60 per minute  
    *   **Success (200)**: `{ "version": 5 }`
    *   **Headers**: Cache-Control and ETag for efficient polling

---
**Staff Dashboard**

*   `GET /jobs`
    *   **Query Params**: `?status=UPLOADED&search=student_name&printer=prusa_mk4s&discipline=Engineering&confirmation_expired=true` (all optional)
    *   **Auth**: Required (Workstation JWT)
    *   **Success (200)**: `{ "jobs": [job_object_1, job_object_2, ...], "total": 25, "filtered": 10 }`

*   `GET /jobs/<job_id>`
    *   **Auth**: Required (Workstation JWT)
    *   **Success (200)**: Returns the full `job_object`, including its event history.

*   `DELETE /jobs/<job_id>`
    *   **Auth**: Required (Workstation JWT)
    *   **Description**: Permanently deletes a job and its associated files. This action is irreversible and only permitted for jobs in 'UPLOADED' or 'PENDING' status. The requesting user must hold the lock. The lock is automatically released upon completion of the request, whether it succeeds or fails.
    *   **Success (204 No Content)**: The job was successfully deleted.
    *   **Error (403 Forbidden)**: If the user tries to delete a job that is not in a deletable status, or if the user does not hold the lock.
    *   **Error (404 Not Found)**: If the job doesn't exist.

*   `GET /jobs/<job_id>/candidate-files`
    *   **Auth**: Required (Workstation JWT)
    *   **Description**: Scans the job's current directory and returns a list of potential authoritative files for the approval modal.
    *   **Success (200)**: `{ "files": ["original_file.stl", "sliced_version.3mf", "another_save.3mf"] }`

*   `POST /jobs/<job_id>/lock`
    *   **Auth**: Required (Workstation JWT)
    *   **Description**: Acquires an exclusive lock on a job to prevent concurrent edits.
    *   **Success (200)**: `{ "message": "Job locked successfully", "locked_until": "timestamp" }`
    *   **Error (409 Conflict)**: `{ "message": "Job is currently locked by another user.", "locked_by": "Jane Doe", "locked_until": "timestamp" }`

*   `POST /jobs/<job_id>/unlock`
    *   **Auth**: Required (Workstation JWT)
    *   **Description**: Releases an exclusive lock on a job.
    *   **Success (200)**: `{ "message": "Job unlocked successfully." }`

*   `POST /jobs/<job_id>/extend`
    *   **Auth**: Required (Workstation JWT)
    *   **Description**: Extends the duration of an existing lock (heartbeat).
    *   **Success (200)**: `{ "message": "Lock extended successfully", "locked_until": "timestamp" }`
    *   **Error (403 Forbidden)**: If the user does not hold the lock.

*   `POST /jobs/<job_id>/approve`
    *   **Auth**: Required (Workstation JWT)
    *   **Description**: Approves a job. The lock is automatically released upon completion.
    *   **Body**: `{ "weight_g": 25.5, "time_hours": 3.5, ..., "staff_name": "Jane Doe" }`
    *   **Success (200)**: Returns updated job. Logs approval with `staff_name` and `workstation_id`.

*   `POST /jobs/<job_id>/reject`
    *   **Auth**: Required (Workstation JWT)
    *   **Description**: Rejects a job. The lock is automatically released upon completion.
    *   **Body**: `{ "reasons": [...], "custom_reason": "...", "staff_name": "Jane Doe" }`
    *   **Success (200)**: Returns updated job. Logs rejection with `staff_name` and `workstation_id`.

*   `POST /jobs/<job_id>/mark-printing`
    *   **Auth**: Required (Workstation JWT)
    *   **Description**: Marks a job as printing. The lock is automatically released upon completion.
    *   **Body**: `{ "staff_name": "Jane Doe" }`
    *   **Success (200)**: Returns updated job. Logs status change with `staff_name` and `workstation_id`.

*   `POST /jobs/<job_id>/mark-complete`
    *   **Auth**: Required (Workstation JWT)
    *   **Description**: Marks a job as complete. The lock is automatically released upon completion.
    *   **Body**: `{ "staff_name": "Jane Doe" }`
    *   **Success (200)**: Returns updated job. Logs completion with `staff_name` and `workstation_id`.

*   `POST /jobs/<job_id>/mark-picked-up`
    *   **Auth**: Required (Workstation JWT)
    *   **Description**: Marks a job as picked up. The lock is automatically released upon completion.
    *   **Body**: `{ "staff_name": "Jane Doe" }`
    *   **Success (200)**: Returns updated job. Logs pickup with `staff_name` and `workstation_id`.

*   `POST /jobs/<job_id>/review`
    *   **Auth**: Required (Workstation JWT)
    *   **Description**: Marks a job as reviewed (or un-reviewed). The lock is automatically released upon completion.
    *   **Body**: `{ "reviewed": true }` (or `false` to mark as unreviewed)
    *   **Success (200)**: Returns updated job. Updates `staff_viewed_at` with `staff_name` and `workstation_id`.

*   `PATCH /jobs/<job_id>/notes`
    *   **Auth**: Required (Workstation JWT)
    *   **Description**: Updates the notes for a job. The lock is automatically released upon completion.
    *   **Body**: `{ "notes": "Staff notes go here." }`
    *   **Success (200)**: Returns updated job. Logs notes update with `staff_name` and `workstation_id`.

*   `POST /jobs/<job_id>/revert-completion`
    *   **Auth**: Required (Workstation JWT)
    *   **Description**: Reverts a job from `COMPLETED` back to `PRINTING`.
    *   **Success (200)**: Returns updated job. Logs `StatusReverted` event.

*   `POST /jobs/<job_id>/revert-pickup`
    *   **Auth**: Required (Workstation JWT)
    *   **Description**: Reverts a job from `PAIDPICKEDUP` back to `COMPLETED`.
    *   **Success (200)**: Returns updated job. Logs `StatusReverted` event.

---
**Payment & Pickup**

*   `POST /jobs/<job_id>/payment`
    *   **Auth**: Required (Workstation JWT)
    *   **Description**: Records payment and transitions job to PAIDPICKEDUP. The lock is automatically released upon completion.
    *   **Body**: `{ "grams": 25.5, "txn_no": "TC123456", "picked_up_by": "Jane Doe", "staff_name": "Staff Member" }`
    *   **Success (200)**: Returns updated job object with payment details
    *   **Error (400)**: Validation errors for missing/invalid data
    *   **Error (403)**: If job is not in COMPLETED status or user doesn't hold lock

---
**Admin Override Endpoints**

*   `POST /jobs/<job_id>/admin/force-unlock`
    *   **Auth**: Required (Workstation JWT)
    *   **Description**: Forcibly releases a lock on a job.
    *   **Body**: `{ "reason": "User browser crashed, releasing stuck lock.", "staff_name": "Admin User" }`
    *   **Success (200)**: `{ "message": "Lock has been forcibly released." }`. Logs an `AdminAction` event.

*   `POST /jobs/<job_id>/admin/force-confirm`
    *   **Auth**: Required (Workstation JWT)
    *   **Body**: `{ "reason": "Student confirmed verbally", "bypass_email": true, "staff_name": "Admin User" }`
    *   **Success (200)**: Returns the updated job object. Logs admin override event with staff attribution.

*   `POST /jobs/<job_id>/admin/change-status`
    *   **Auth**: Required (Workstation JWT)
    *   **Body**: `{ "new_status": "READYTOPRINT", "reason": "Debugging workflow issue", "staff_name": "Admin User" }`
    *   **Success (200)**: Returns the updated job object. Logs admin override event with staff attribution.

*   `POST /jobs/<job_id>/admin/mark-failed`
    *   **Auth**: Required (Workstation JWT)
    *   **Description**: Marks a job in the `PRINTING` status as failed due to lab error and returns it to the `READYTOPRINT` queue.
    *   **Body**: `{ "reason": "Filament tangle detected on printer.", "staff_name": "Jane Doe" }`
    *   **Success (200)**: Returns the updated job object. Logs a `PrintFailed` event with the provided reason and an `AdminAction` event.

*   `POST /jobs/<job_id>/admin/resend-email`
    *   **Auth**: Required (Workstation JWT)
    *   **Description**: Allows staff to resend a notification email. This action is rate-limited.
    *   **Body**: `{ "email_type": "approval", "staff_name": "Jane Doe" }` (options: "approval", "rejection", "completion")
    *   **Success (200)**: `{ "message": "Email resent successfully", "new_token": "abc123" }`. Logs email resend with staff attribution.
    *   **Error (429)**: `{ "message": "An email was sent recently. Please wait before resending." }`
    *   **Error (409)**: `{ "message": "Job is currently locked by another user." }`

---
**Admin System Health**

*   `POST /admin/audit/start`
    *   **Description**: Triggers a new system health and integrity scan. This will be an asynchronous task.
    *   **Auth**: Required (Workstation JWT)
    *   **Success (202)**: `{ "message": "System audit started successfully.", "task_id": "some-async-task-id" }`. Logs the `AdminAction` event.

*   `GET /admin/audit/report`
    *   **Description**: Retrieves the report from the last completed system health scan.
    *   **Auth**: Required (Workstation JWT)
    *   **Success (200)**: `{ "report_generated_at": "timestamp", "orphaned_files": ["path/to/orphan1.stl"], "broken_links": [{"job_id": "abc", "missing_path": "path/to/missing.stl"}] }`.

*   `DELETE /admin/audit/orphaned-file`
    *   **Description**: Deletes a specific orphaned file from the storage. This action is logged.
    *   **Auth**: Required (Workstation JWT)
    *   **Body**: `{ "file_path": "path/to/orphan1.stl", "staff_name": "Admin User" }`
    *   **Success (200)**: `{ "message": "Orphaned file deleted successfully." }`. Logs the `FileDeleted` event with admin attribution.

---
**Admin Data Management**

*   `POST /admin/archive`
    *   **Description**: Triggers the archival of all jobs in a final state (`PaidPickedUp`, `Rejected`) that are older than the specified retention period.
    *   **Auth**: Required (Workstation JWT)
    *   **Body**: `{ "retention_days": 45, "staff_name": "Admin User" }` (Optional, defaults to 45)
    *   **Success (200)**: `{ "message": "Archival process completed", "jobs_archived": 12 }`. Logs a single `AdminAction` event for the batch operation, and individual `JobArchived` events for each job.

*   `POST /admin/prune`
    *   **Description**: Permanently deletes all jobs in the `ARCHIVED` state that are older than the specified retention period. This is a destructive action.
    *   **Auth**: Required (Workstation JWT)
    *   **Body**: `{ "retention_days": 365, "staff_name": "Admin User" }` (Optional, defaults to 365)
    *   **Success (200)**: `{ "message": "Pruning process completed", "jobs_deleted": 5 }`. Logs an `AdminAction` event and individual `JobDeleted` events for each job that is pruned.

---
**Financial Reporting**

*   `POST /export/payments`
    *   **Auth**: Required (Workstation JWT)
    *   **Description**: Generates CSV export of payment data for specified period - returns file directly
    *   **Body**: `{ "start_date": "2024-01-01", "end_date": "2024-01-31", "staff_name": "Admin User" }`
    *   **Success (200)**: Returns CSV file with `Content-Disposition: attachment` header
    *   **Content Type**: `text/csv` with filename based on date range

---
**Analytics & Insights**

*   `GET /analytics/overview`
    *   **Auth**: Required (Workstation JWT)
    *   **Query Params**: `?days=30&printer=all&discipline=all` (optional)
    *   **Success (200)**: Operational metrics, resource utilization, and financial performance data

*   `GET /analytics/trends`
    *   **Auth**: Required (Workstation JWT)
    *   **Query Params**: `?period=monthly&metric=submissions&start_date=2024-01-01` (optional)
    *   **Success (200)**: Time-series data for trend visualizations

*   `GET /analytics/resources`
    *   **Auth**: Required (Workstation JWT)
    *   **Success (200)**: Printer utilization, material consumption, and capacity planning metrics

---
**Dashboard Stats & Analytics**

*   `GET /stats`
    *   **Auth**: Required (Workstation JWT)
    *   **Success (200)**: `{ "uploaded": 10, "pending": 5, "readyToPrint": 3, "storage_usage_mb": 1024, "storage_limit_mb": 10240 }`

*   `GET /stats/detailed`
    *   **Auth**: Required (Workstation JWT) 
    *   **Query Params**: `?days=30&printer=all&discipline=all` (optional)
    *   **Success (200)**: Detailed analytics including submission trends, printer utilization, common rejection reasons, and staff activity metrics

---
**System Monitoring & Diagnostics**

*   `GET /monitoring/health`
    *   **Description**: Comprehensive system health status with component-level details
    *   **Success (200)**: `{ "status": "healthy", "timestamp": "...", "components": { "system": {...}, "database": {...}, "storage": {...}, "redis": {...} } }`
    *   **Error (503)**: If system is degraded or unhealthy

*   `GET /monitoring/metrics/system`
    *   **Description**: System-level metrics (CPU, memory, disk, network)
    *   **Success (200)**: Detailed system resource metrics with usage percentages and raw values

*   `GET /monitoring/metrics/application` 
    *   **Description**: Application-specific metrics (requests, errors, performance)
    *   **Success (200)**: Request timing, error rates, and performance statistics

*   `GET /monitoring/metrics/all`
    *   **Description**: All metrics in single response for dashboard consumption
    *   **Success (200)**: Combined system, application, database, storage, and Redis metrics

*   `GET /monitoring/history`
    *   **Query Params**: `?hours=24` (optional, defaults to 24)
    *   **Description**: Historical metrics for trend analysis
    *   **Success (200)**: Time-series metrics data

*   `GET /monitoring/alerts`
    *   **Description**: Current performance alerts and warnings
    *   **Success (200)**: `{ "alerts": [{"type": "high_cpu", "severity": "warning", "message": "...", "timestamp": "..."}] }`

*   `GET /_diag`
    *   **Auth**: Required (Workstation JWT)
    *   **Description**: System diagnostic information including database engine, job counts, email configuration status
    *   **Success (200)**: Diagnostic data for troubleshooting and system verification

*   `POST /_diag/test-email`
    *   **Auth**: Required (Workstation JWT)  
    *   **Description**: Test email functionality by sending a test message
    *   **Body**: `{ "staff_name": "Admin User" }`
    *   **Success (200)**: `{ "message": "Test email sent successfully" }`

---
**Additional Admin Operations**

*   `DELETE /admin/audit/stale-file`
    *   **Auth**: Required (Workstation JWT)
    *   **Description**: Deletes stale files identified during integrity audits
    *   **Body**: `{ "file_path": "path/to/stale.stl", "staff_name": "Admin User" }`
    *   **Success (200)**: `{ "message": "Stale file deleted successfully." }`

*   `POST /admin/audit/repair-metadata`
    *   **Auth**: Required (Workstation JWT)  
    *   **Description**: Repairs or recreates metadata.json files for jobs with metadata issues
    *   **Body**: `{ "job_id": "abc123", "staff_name": "Admin User" }`
    *   **Success (200)**: `{ "message": "Metadata repaired successfully." }`

*   `POST /admin/audit/repair-location`
    *   **Auth**: Required (Workstation JWT)
    *   **Description**: Moves job files to correct directory based on database status
    *   **Body**: `{ "job_id": "abc123", "staff_name": "Admin User" }`  
    *   **Success (200)**: `{ "message": "File location repaired successfully." }`

*   `GET /admin/settings`
    *   **Auth**: Required (Workstation JWT)
    *   **Description**: Gets current admin configuration settings
    *   **Success (200)**: Current system settings and configuration

*   `POST /admin/settings`
    *   **Auth**: Required (Workstation JWT)
    *   **Description**: Updates admin system settings  
    *   **Body**: `{ "staff_name": "Admin User", "sound": {"enabled": true, "volume": 50}, "environment_banner": "DEVELOPMENT" }`
    *   **Success (200)**: `{ "message": "Settings updated successfully" }`

**API Implementation Status:**
- **Complete Endpoint Coverage**: All documented endpoints are fully implemented and operational
- **Comprehensive Route Architecture**: 96+ endpoints across 13 route modules providing complete system functionality
- **Production Ready**: All endpoints include proper error handling, validation, and response formatting
- **Service Integration**: Routes use orchestration layer and business logic services for clean separation of concerns
- **Rate Limiting**: Appropriate rate limiting implemented on submission, authentication, and admin endpoints
- **Dual Route Support**: Some core job operations available through both `/jobs` and `/jobs_staff` blueprints for organizational flexibility

**API Response Standards:**
- All timestamps in UTC ISO 8601 format
- All file sizes in bytes unless otherwise specified
- All monetary amounts in USD cents (e.g., 300 = $3.00)
- Consistent error response format: `{ "error": "error_code", "message": "Human readable message", "details": {...} }`
- All list endpoints support pagination via `?page=1&limit=50` parameters
- All protected endpoints log access attempts for security auditing

## 7. Status Mapping Table

### Internal Status ↔ Directory ↔ UI Label Mapping

| Internal Status | Directory Name | UI Label | Description |
|----------------|----------------|----------|-------------|
| `UPLOADED` | `Uploaded/` | "Uploaded" | Student submission received |
| `PENDING` | `Pending/` | "Pending" | Awaiting student confirmation |
| `READYTOPRINT` | `ReadyToPrint/` | "Ready to Print" | Approved and confirmed |
| `PRINTING` | `Printing/` | "Printing" | Currently being printed |
| `COMPLETED` | `Completed/` | "Completed" | Print finished |
| `PAIDPICKEDUP` | `PaidPickedUp/` | "Paid & Picked Up" | Final state |
| `REJECTED` | `Rejected/` | "Rejected" | Job rejected by staff |
| `ARCHIVED` | `Archived/` | "Archived" | Archived for retention |

### Status Progression Rules
- **Normal Flow**: UPLOADED → PENDING → READYTOPRINT → PRINTING → COMPLETED → PAIDPICKEDUP → ARCHIVED
- **Rejection Flow**: UPLOADED → REJECTED → ARCHIVED
- **Revert Actions**: COMPLETED → PRINTING, PAIDPICKEDUP → COMPLETED
- **Admin Override**: Any status can be changed via admin endpoints
