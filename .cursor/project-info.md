# Project Information - 3D Print Management System

## Project Goals

Build a beginner-friendly Flask API + Next.js system for managing 3D print job workflows in academic/makerspace environments. Focus on simplicity, clear audit trails, and robust file management.

## Domain Glossary

### 3D Printing Terms
- **Filament**: Plastic material fed into FDM printers (PLA, TPU, PETG)
- **Resin**: Liquid photopolymer used in SLA printers
- **Slicer**: Software that converts 3D models into printer instructions (.gcode)
- **STL/OBJ/3MF**: Common 3D model file formats
- **Build Volume**: Maximum printable dimensions of a printer

### System Terms
- **Job**: A complete 3D print request from submission to pickup
- **Authoritative File**: The current "correct" file for a job (may be original or sliced version)
- **Workstation**: Physical computer terminal with shared login
- **Attribution**: Staff member selection required for all actions
- **Event Log**: Immutable audit trail of all system actions

### Job Status Flow
- **UPLOADED** → Student submitted, awaiting staff review
- **PENDING** → Approved by staff, awaiting student confirmation
- **READYTOPRINT** → Student confirmed, ready for printing
- **PRINTING** → Currently being printed
- **COMPLETED** → Print finished, awaiting pickup
- **PAIDPICKEDUP** → Student paid and collected print
- **REJECTED** → Staff rejected submission
- **ARCHIVED** → Final state for old jobs

## Coding Conventions

### Backend (Flask)
- Use Blueprint organization for routes
- All endpoints return JSON (no HTML templates)
- Every action creates Event log entry
- File operations use "copy-update-delete" pattern for resilience
- All timestamps in UTC, converted to local time in frontend

### Frontend (Next.js)
- Use App Router with TypeScript
- Components in `/components` organized by feature
- All API calls through centralized client in `/lib/api.ts`
- Forms use shadcn/ui components with validation
- Status changes require staff attribution dropdown

### Database
- PostgreSQL with SQLAlchemy ORM
- Use Flask-Migrate for schema changes
- Event table is append-only (no updates/deletes)
- All foreign keys use job.id as string (UUID)

### File Management
- Network storage mounted at same path on all machines
- Directory structure mirrors job status
- metadata.json accompanies every job file
- File paths stored as absolute paths in database

## Repository Etiquette

- Commit `.env.example` files, never actual `.env` files
- Docker Compose for consistent development environment
- Test API endpoints before committing
- Document any custom protocol handler changes
- Update this file when adding new domain concepts

## Critical Success Factors

1. **File Integrity**: Always validate file operations and log results
2. **Audit Trail**: Every action must be attributable to specific staff member
3. **Error Handling**: Provide clear error messages and recovery paths
4. **User Experience**: Follow modern UI/UX patterns consistently
5. **Security**: Validate all file paths, implement proper CORS, rate limiting