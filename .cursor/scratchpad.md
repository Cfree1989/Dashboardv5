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

#### P4. Delete Requires Lock (Optional)
- **Backend**: Add `locked_by`, `locked_until` to Job model
- **Endpoints**: Lock/unlock/extend; enforce on DELETE
- **Tests**: Lock acquisition, conflicts, delete without lock forbidden

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
- [ ] P2. Expired/resend confirmation — backend + frontend + tests  
- [ ] P3. Revert endpoints — backend + tests
- [ ] P4. Delete requires lock — minimal locking + tests
- [ ] P5. Payments export — backend + tests
- [ ] P6. Background audio trigger — frontend + tests
- [ ] P7. Health alias — backend

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

### Immediate (Pre-E2E)
1. **P1**: Submit rate limiting (must-do) ✅ **COMPLETED**
2. **P2-P7**: Optional Pre-E2E items
3. **E2E**: Happy path integration test
4. **Deployment**: Production docs

### Medium Priority
1. **SlicerOpener Packaging**: Signed zip distribution
2. **Analytics V0**: Component parity and animations
3. **Masterplan Gaps**: M1-M5 implementation

### Future
1. **Phase 6-14**: Advanced features and polish
2. **Production**: Monitoring, backup, performance optimization

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

---

**Last Updated**: Current session  
**Next Review**: After Pre-E2E completion


