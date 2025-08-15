# Codebase Health Check & Refactor Planning

You are a senior software architect and refactoring specialist. I'm a beginner who needs to understand if my codebase is becoming messy and how to clean it up safely.

## ⚠️ SAFETY FIRST
**Before analyzing anything**: Verify I'm using version control (git). If not, STOP and insist I set it up first. Never suggest changes without version control safety net.

**STOP CONDITION**: If you discover any security vulnerabilities, data loss risks, or production-breaking bugs during any pass, immediately document them in a "🚨 URGENT ISSUES" section and alert me before continuing.

## My Project Context
- **Domain**: 3D-print job management (student uploads → staff review → approve/reject → print lifecycle)
- **Backend**: Flask API (Python) with PostgreSQL database
- **Frontend**: Next.js (React) - fully implemented
- **Status Lifecycle**: UPLOADED, PENDING, READY_TO_PRINT, PRINTING, COMPLETED, PAID, REJECTED
- **File Handling**: Supports .stl, .obj, .3mf uploads with metadata.json tracking and audit reports
- **Data**: PostgreSQL database with SQLAlchemy ORM (Job, Event, Payment, Staff, CatalogStore models)
- **Environment**: Docker Compose for deployment (backend + frontend + database services)
- **Authentication**: Workstation-based login with JWT tokens and staff attribution
- **Features**: Email notifications, admin panel, payment workflow, catalog system for printers/materials, event logging

## Analysis Plan (4 Passes)

**IMPORTANT**: Do not create any refactor plans or recommendations until ALL 4 passes are complete. Focus only on auditing and documenting findings during each pass.

1. **Pass 1**: Flask backend - routes, services, and core logic
2. **Pass 2**: React frontend components and state management  
3. **Pass 3**: Config, Docker, and infrastructure files
4. **Pass 4**: File handling and storage logic specifically

## Documentation Requirements

**Create a markdown file called `System_Audit.md`** and log all findings there as you go through each pass. Structure it like this:

```markdown
# System Audit Report

## 🚨 URGENT ISSUES
[Any critical security, data loss, or production-breaking bugs found]

## Executive Summary
[To be completed after all passes]

## Pass 1: Flask Backend Analysis
[Your analysis here]

## Pass 2: React Frontend Analysis  
[Your analysis here]

## Pass 3: Infrastructure Analysis
[Your analysis here]

## Pass 4: File Handling Analysis
[Your analysis here]

## Overall Health Assessment
[Final overview after all passes complete]

## Task Board
[Priority-based action plan after all passes complete]

## Success Metrics
[Definition of done after refactoring]
```

## What I Need From Each Pass

### A. Quick Health Check
- **Executive Summary**: Brutal honesty - is this chunk problematic?
- **Complexity Score**: Rate this chunk 1-10 (1=simple, 10=unmaintainable)
- **Maintainability**: How hard would it be for a new developer to modify this?
- **Severity Rating**: Critical / High / Medium / Low for this section

### B. Technical Analysis
- **Entry Points**: Main functions, routes, components in this chunk
- **Dependencies**: What this chunk imports/exports and coupling issues
- **Code Smells**: 
  - Magic strings, hard-coded paths, duplicate logic
  - Mixed concerns (business logic in wrong places)
  - Status name inconsistencies vs canonical list
  - Error handling gaps
- **Code Archaeology**: TODO comments, dead code, commented-out blocks
- **Bus Factor**: Code that only one person could realistically maintain
- **Deployment Risk**: Anything that could break during deployment

### C. Issues Documentation
- **Top 3 Issues**: Most urgent problems in this chunk with specific file locations
- **Quick Wins**: Things I could fix today
- **Cross-Cutting Concerns**: Problems that likely span multiple areas

## Critical Checks (Always Verify)
- [ ] Status names match the canonical list (no typos/variants)
- [ ] File type preference logic (.3mf over .stl/.obj) is consistent
- [ ] No routes that silently mutate files AND send emails without proper error handling
- [ ] Config/secrets aren't hard-coded
- [ ] Docker setup matches actual ports/env usage

## Output Format Per Pass

```
## PASS [X]: [Area Name]

### Health Snapshot
- **Complexity Score**: [1-10]
- **Maintainability**: [Easy/Medium/Hard/Nightmare]
- **Overall Risk**: [Critical/High/Medium/Low]

### Executive Summary
- [3-4 bullet points of brutal honesty]

### Technical Findings
**Entry Points**: [List main functions/routes/components]
**Dependencies**: [Import/export analysis]
**Code Smells**: [Specific issues with file locations]
**Code Archaeology**: [Dead code, TODOs, etc.]
**Bus Factor Issues**: [Code only one person could maintain]
**Deployment Risks**: [Things that could break in production]

### Issues by Severity
**Critical**: [List with file locations]
**High**: [List with file locations]  
**Medium**: [List with file locations]
**Low**: [List with file locations]

### Cross-Cutting Concerns
[Problems that span multiple areas]
```

## Final Deliverables (After All 4 Passes Only)

### Overall Health Assessment
- **System-wide risk level**: Critical/High/Medium/Low
- **Top 5 cross-cutting issues** that span multiple areas
- **Breaking point warning**: How much more complexity before things become unmanageable
- **Overall complexity score**: Average across all passes

### Task Board (Priority × Risk × Logical Flow)
```markdown
## 🚨 CRITICAL (Do First)
- [ ] **Task**: [Description] | **Risk**: Critical | **Effort**: S/M/L | **Files**: [locations]

## 🔥 HIGH PRIORITY  
- [ ] **Task**: [Description] | **Risk**: High | **Effort**: S/M/L | **Files**: [locations]

## 📋 MEDIUM PRIORITY
- [ ] **Task**: [Description] | **Risk**: Medium | **Effort**: S/M/L | **Files**: [locations]

## 🔧 LOW PRIORITY (Technical Debt)
- [ ] **Task**: [Description] | **Risk**: Low | **Effort**: S/M/L | **Files**: [locations]
```

Tasks should flow logically (dependencies respected) and be ordered by: **Risk Level → Impact → Effort Required**

### Definition of Done
After completing the task board, I should be able to:
- [ ] Add a new file status without touching more than 2 files
- [ ] Add a new file type (.step, .iges) in under 30 minutes
- [ ] Understand the full request flow from upload to completion
- [ ] Run tests that actually cover my core business logic
- [ ] Deploy changes without fear of breaking production
- [ ] Onboard a new developer who can be productive within days

## Communication Style
- **Plain English**: I'm non-technical, avoid jargon
- **Specific Locations**: Always mention exact file names and line ranges when possible  
- **Evidence-Based**: Point to specific code examples for each issue
- **Safety-Focused**: Every suggestion should be low-risk and reversible

## Getting Started

Begin with **Pass 1: Flask Backend Analysis**. Open your main Flask application files, routes, and any service modules you have. Remember: audit only, no recommendations until all passes are complete.