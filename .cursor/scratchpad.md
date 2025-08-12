# 3D Print Management System - Build Plan

## Project Status

**Current Phase**: Pre-E2E Implementation  
**Overall Progress**: ~85% (core functionality complete, protocol handler resolved)  
**Next Priority**: Pre-E2E gap items → E2E testing → Production deployment

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

### Protocol Handler Resolution
**Issue**: Cross-tab protocol invocation failures  
**Root Cause**: User gesture preservation - modal JavaScript buttons broke browser gesture chain  
**Solution**: Replaced modal buttons with real anchor elements (`<a href="print3d://...">`)  
**Result**: Reliable file opening from all dashboard tabs with complete audit trail

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
- [ ] P5. Payments export — backend + tests
- [x] P6. Background audio trigger — frontend + tests ✅ **COMPLETED**
- [x] P7. Health alias — backend ✅ **COMPLETED**

## Background and Motivation — P4: Soft-Delete + Confirmation
Deleting jobs immediately is risky. Soft-delete preserves recoverability and audit trail while avoiding accidental data loss. A minimal confirmation (typing `short_id`) reduces mistakes without adding complexity.

## Key Challenges and Analysis — P4
- Preserve file/data integrity: move to `Archived/` rather than remove
- Keep API simple: reuse existing move helpers, event logging
- Provide an emergency hard-delete for true removal (admin-only)

## High-level Task Breakdown — P4
1) Backend: Update `DELETE /api/v1/jobs/<id>` to set `status='ARCHIVED'`, move files via `move_authoritative(job, 'ARCHIVED')`, log `JobArchived`, return 200 with job JSON
2) Backend: Add `POST /api/v1/jobs/<id>/hard-delete` (requires `staff_name` + elevated role flag later; for now, standard token) to permanently delete row and files; log `JobHardDeleted`
3) Frontend: On delete, show confirm dialog requiring `short_id` entry; call soft-delete; show toast
4) Tests: soft-delete transitions, metadata sync, events; hard-delete removes row/files; guards (only early statuses for soft-delete or allow all? default to early)

### Success Criteria
- Soft-delete replaces hard-delete: status becomes `ARCHIVED`, files moved, event logged
- Hard-delete endpoint exists and removes row/files
- Frontend requires `short_id` entry to confirm delete

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
1. P5. Payments export — backend + tests
2. E2E happy path
3. Deployment docs

## 📚 Lessons Learned

- **Protocol Handler**: User gesture preservation is critical for custom protocols
- **File Paths**: Normalize to Windows format (`C:\Dashboardv5\storage\`) for SlicerOpener
- **Rate Limiting**: Flask-Limiter already configured, just need endpoint decorators
- **Testing**: Use temp storage fixtures, mock filesystem operations
- **Development**: Prefer `pytest -q` on Windows PowerShell (avoid `&&`)
- **Flask-Limiter**: Returns HTML error pages by default, use `response.get_json()` with None check

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

## Executor's Feedback or Assistance Requests
- All Pre-E2E gap items completed except P5 (Payments export)
- Ready to proceed with P5 implementation or move to E2E testing

---

**Last Updated**: Current session  
**Next Review**: After Pre-E2E completion


