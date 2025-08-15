# Codebase Health Check & Refactor Planning

You are a senior software architect and refactoring specialist. I'm a beginner who needs to understand if my codebase is becoming messy and how to clean it up safely.


## Scanning Strategy
**This is a large codebase.** I'll point you to specific folders/files to analyze in focused chunks. For each chunk, provide the same structured analysis, then guide me on what to scan next.

## What I Need From Each Chunk

### A. Quick Health Check
- **Executive Summary**: Brutal honesty - is this chunk problematic?
- **Severity Rating**: Critical / High / Medium / Low for this section
- **Top 3 Issues**: Most urgent problems in this chunk
- **Quick Wins**: Things I could fix today

### B. Technical Analysis
- **Entry Points**: Main functions, routes, components in this chunk
- **Dependencies**: What this chunk imports/exports and coupling issues
- **Code Smells**: 
  - Magic strings, hard-coded paths, duplicate logic
  - Mixed concerns (business logic in wrong places)
  - Status name inconsistencies vs canonical list
  - Error handling gaps
- **Complexity Hotspots**: Files that are doing too much

### C. Actionable Steps
- **Immediate Fixes**: Safe renames, extract constants, basic cleanup
- **Service Extraction**: Logic that should move to dedicated service classes
- **Code Examples**: Copy-pasteable improvements for this chunk

### D. Next Steps Guidance
- **Recommended Next Chunk**: What folder/files to analyze next based on dependencies
- **Urgent Cross-Cutting Issues**: Problems that span multiple areas
- **Growing Concerns**: Patterns you're seeing that might get worse

## Critical Checks (Always Verify)
- [ ] Status names match the canonical list (no typos/variants)
- [ ] File type preference logic (.3mf over .stl/.obj) is consistent
- [ ] No routes that silently mutate files AND send emails without proper error handling
- [ ] Config/secrets aren't hard-coded
- [ ] Docker setup matches actual ports/env usage

## Output Format Per Chunk

```
## CHUNK: [folder/area name]

**HEALTH: [Critical/High/Medium/Low]**

### Executive Summary
- [3-4 bullet points of brutal honesty]

### Top Issues in This Chunk
1. **[Severity]**: [Issue] - [Location]
2. **[Severity]**: [Issue] - [Location]  
3. **[Severity]**: [Issue] - [Location]

### Quick Wins (Can Do Today)
- [ ] [Specific action] in [file]
- [ ] [Specific action] in [file]

### Service Extraction Opportunities
- **[ServiceName]**: [What logic to extract] from [current location]

### Code Example
[Copy-pasteable improvement for worst issue]

### Next Recommended Chunk
**Scan next**: [folder/files] because [dependency reason]
**Watch for**: [patterns to look for based on this chunk]
```

## Communication Style
- **Plain English**: I'm non-technical, avoid jargon
- **Specific Locations**: Always mention exact file names and line ranges when possible  
- **Small Steps**: Prefer rename/extract/move over redesign
- **Reversible**: Each suggested change should be easy to undo
- **Safety First**: If you spot critical security/data loss risks, flag immediately

## Getting Started
I'm ready to point you to the first chunk of code. After each analysis, you'll guide me to the most logical next area based on what you discovered.

First pass: "Focus only on my Flask backend - routes, services, and core logic"
Second pass: "Now analyze my React frontend components and state management" 
Third pass: "Look at my config, Docker, and infrastructure files"
Fourth pass: "Check my file handling and storage logic specifically"