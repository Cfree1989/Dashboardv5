# Project Repository Documentation Structure

This document outlines the essential documentation structure for your Flask + Next.js 3D print management system, optimized for AI coding assistance while maintaining simplicity.

## 1. Repository Root Files (Essential)

| File | Purpose | Format |
|------|---------|--------|
| `README.md` | Quick-start guide with setup instructions and system overview | Markdown |
| `project-info.md` | **"Minimal brain"** – project goals, 3D printing glossary, coding conventions | Markdown |
| `CURSOR.md` | Cursor-specific tips, common commands, troubleshooting for this project | Markdown |
| `.editorconfig` | Enforce consistent formatting (Python/TypeScript) | INI |

## 2. `/docs` — Core Documentation

| Sub-folder | Key Files | Purpose for 3D Print System |
|------------|-----------|----------------------------|
| `requirements/` | `user-stories.md`, `workflow-states.md` | Clear specifications for student/staff workflows |
| `context/` | `glossary.md`, `style-guide.md` | 3D printing terminology, Flask/Next.js conventions |
| `examples/` | `sample-api-endpoint.py`, `sample-component.tsx` | Concrete code patterns to follow |
| `api/` | `endpoints.md` | Simple REST API documentation |

## 3. `/diagrams` — Simple Visual References

| Sub-folder | Files | Purpose |
|------------|-------|---------|
| `architecture/` | `system-overview.mmd` | Basic system architecture (Flask API + Next.js + PostgreSQL) |
| `workflows/` | `job-lifecycle.mmd` | Job status flow (UPLOADED → PENDING → etc.) |

## 4. `/tests` — Testing Structure

**Test Files:**
- `/tests/__init__.py`
- `/tests/test_api.py` 
- `/tests/test_workflows.py`

## 5. Essential Development Folders

Create these initially:

- `/scripts/` – Helper tools (SlicerOpener setup, database utilities)
- `/docker/` – Docker configuration files

## Priority Implementation Order

For maximum AI effectiveness, implement in this order:

1. **`project-info.md`** - Core project context and 3D printing glossary
2. **`docs/requirements/user-stories.md`** - Student and staff user stories  
3. **`docs/context/glossary.md`** - 3D printing terms, status definitions
4. **`docs/examples/`** - Sample Flask routes and React components
5. **`diagrams/workflows/job-lifecycle.mmd`** - Visual job flow diagram