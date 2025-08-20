# Time-Travel Refactoring: Learning from Failed Attempts

You are a senior developer who has just completed a **failed** refactoring attempt on some Watch files. The changes didn't work and are about to be reverted. However, before the revert happens, you need to document everything you learned for your "past self" who will attempt this refactoring again.

## Your Mission
Update the existing `implementation_roadmap.md` document with your lessons learned. **Do not replace the roadmap** - instead, integrate your findings cohesively into the existing structure. Add new sections, update existing ones, and cross-reference with current roadmap items as needed.

Write your updates as if you're explaining to a version of yourself from 1 hour ago - someone who is about to start this exact same refactoring with fresh optimism but zero knowledge of what's about to go wrong.

## Integration Requirements

### How to Update the Roadmap
1. **Read the entire existing roadmap first** to understand the current structure and planned approach
2. **Identify where your lessons fit** - do they update existing tasks, add prerequisites, or reveal missing steps?
3. **Integrate organically** - your insights should enhance the roadmap, not break its flow
4. **Cross-reference** - link your lessons to specific roadmap items where relevant
5. **Update task priorities** - if you discovered that certain steps must happen first, reorder accordingly

### Integration Patterns

**For existing roadmap items** - Add comprehensive detail:
```markdown
## [Existing Task Title]
[Original task description]

### ⚠️ Lessons Learned: What Actually Happens Here
**Past You was planning**: [original approach from roadmap]
**Future You discovered**: [detailed explanation of what went wrong]
**Specific error patterns**: 
- Error message: `[exact error text]`
- When it occurs: [precise trigger conditions]
- Why it happens: [technical root cause]
- Files affected: [complete list with line numbers if relevant]

**Updated approach**: [revised strategy with step-by-step details]
**New prerequisites**: 
- [Prerequisite 1]: Why needed, how to implement, success criteria
- [Prerequisite 2]: Dependencies, implementation details, testing approach

**Detailed implementation steps**:
1. [Step 1]: [What to do], [How to verify it worked], [What can go wrong]
2. [Step 2]: [Detailed actions], [Expected outcomes], [Troubleshooting]
3. [Continue with specific steps...]

**Testing strategy**:
- Unit tests needed: [specific test cases]
- Integration tests: [scenarios to validate]  
- Manual verification: [exact steps to confirm success]

**Rollback plan**: [How to safely undo if this fails]

[Continue with original task details, updated as needed]
```

**For new critical sections** - Provide exhaustive detail:
```markdown
## 🚨 Critical Prerequisites (Added After Failed Attempt)
Based on failed refactor attempt on [date]:

### [New Required Step]
**Why this wasn't in original roadmap**: [detailed reasoning about what was missed]
**What happens if you skip this**: [specific failure modes and consequences]

**Detailed implementation**:
- **Files to modify**: [exact file paths and what changes in each]
- **Code patterns to look for**: [specific patterns that indicate this step is needed]
- **Dependencies**: [other systems/files this interacts with]
- **Configuration changes**: [environment variables, settings, etc.]

**Step-by-step process**:
1. **[Action]**: [Detailed instructions]
   - Command to run: `[exact command]`
   - Expected output: `[what you should see]`
   - If it fails: [troubleshooting steps]

2. **[Next Action]**: [More detailed instructions]
   - Files to check: [specific paths]
   - What to verify: [exact criteria]
   - Common issues: [problems and solutions]

**Success criteria**: 
- [Criterion 1]: [How to measure/verify]
- [Criterion 2]: [Specific indicators]
- [Criterion 3]: [Testing approach]

**Common gotchas**:
- [Issue 1]: [What looks right but isn't], [how to detect], [how to fix]
- [Issue 2]: [Subtle problem], [warning signs], [solution]

**Time estimate**: [Realistic time based on experience]
**Risk level**: [High/Medium/Low with justification]
```

**For roadmap reordering**:
```markdown
## Updated Task Priority Order
**Original order**: Task A → Task B → Task C
**Revised order**: Task B → New Task X → Task A → Task C
**Why the change**: [lessons learned that required reordering]
```

```markdown
## Hey Past Me, About That Watch File Refactor You're Planning...

### What You're About To Try (And Why It Won't Work)
**Past You is thinking**: "I'll just extract this watch logic into a service"
**Future You learned**: Don't. The watch callbacks have hidden dependencies on [specific issue]. Try [alternative approach] instead.

### The Trap You're About To Fall Into
**You're going to assume**: [incorrect assumption]  
**The reality is**: [what actually happens]  
**The clue you'll miss**: [specific warning sign]  
**What to look for instead**: [better indicator]

### That "Simple" Change That Breaks Everything  
**The innocent-looking line**: `[specific code]`
**Why it seems harmless**: [reasoning]
**What it actually destroys**: [cascade effect]
**The fix that actually works**: [solution]
```

## Key Areas to Document (Comprehensive Detail Required)

### 🚨 **Critical Gotchas** 
For each gotcha, provide:
- **Exact files and line numbers** where the issue manifests
- **Complete error messages** or unexpected behaviors
- **Step-by-step reproduction** of the problem
- **Root cause analysis** at the code level
- **Dependencies map** showing hidden connections
- **Timing diagrams** for race conditions
- **State mutation tracking** showing what changes when
- **Watch trigger cascades** with complete event chains

### 🔍 **Hidden Complexity Discovery**
Document with full detail:
- **File interconnection maps**: Which files import/depend on which, with dependency graphs
- **Business logic archaeology**: Where business rules are actually implemented vs where they appear to be
- **Event handling flow charts**: Complete event propagation paths with timing
- **Configuration dependency matrix**: All config that affects this functionality, including defaults and overrides
- **Runtime behavior documentation**: What actually happens vs what the code suggests should happen

### 🛠 **Prerequisite Analysis**  
Provide exhaustive documentation:
- **Complete dependency tree**: Everything that must exist before each step
- **Operation sequencing**: Exact order with explanations for why order matters
- **Infrastructure requirements**: All environment setup, packages, configurations needed
- **Test infrastructure needs**: What testing setup is required before starting
- **Data migration requirements**: Any data structure changes needed first

### 💡 **Alternative Architecture Analysis**
Full comparative analysis:
- **Current architecture flaws**: Detailed breakdown of what's wrong with current approach
- **Alternative 1**: [Name], pros/cons, implementation complexity, migration path
- **Alternative 2**: [Name], pros/cons, implementation complexity, migration path  
- **Incremental improvement path**: Step-by-step approach to improve current architecture
- **Tool recommendations**: Specific libraries/frameworks that solve these problems better
- **Simplification opportunities**: Places where complexity can be removed rather than refactored

### 📋 **Debugging Intelligence Database**
Create comprehensive debugging guide:
- **Error message translation**: What each cryptic error actually means in context
- **Console output patterns**: How to read the debugging output effectively
- **File watching behavior quirks**: Undocumented behaviors and workarounds
- **Browser dev tools cookbook**: Specific tools and techniques that revealed problems
- **Performance profiling insights**: What the profiler revealed about the real bottlenecks
- **Memory leak detection**: How to spot and debug memory issues in this context

## Required Format for Each Lesson (Maximum Detail)

```markdown
### [Descriptive Title of What Goes Wrong]

**What Past You will try**: 
[Specific action/approach with exact files and functions involved]

**Why it seems logical**:
[The detailed reasoning that makes this seem right, including any documentation or examples that support this approach]

**What actually happens**:
[Specific failure mode, complete error messages, unexpected behavior, performance issues]

**Technical deep dive**:
- **Root cause**: [Detailed explanation of why this fails at a technical level]
- **Call stack**: [If relevant, the sequence of function calls that leads to failure]
- **State changes**: [What state gets corrupted or modified unexpectedly]
- **Side effects**: [Unintended consequences in other parts of the system]

**Debugging process that revealed this**:
1. [Step 1]: [What you tried], [what it revealed], [tools used]
2. [Step 2]: [Investigation method], [findings], [dead ends]
3. [Step 3]: [Breakthrough moment], [key insight], [evidence]

**What Past You should do instead**:
[Concrete alternative approach with complete implementation details]
- **Files to modify**: [Exact paths and changes needed]
- **Code structure**: [Detailed architectural approach]
- **Dependencies**: [What needs to be in place first]
- **Testing approach**: [How to validate this works]

**Implementation template**:
```javascript
// Before (broken approach)
[exact code that fails]

// After (working approach)  
[exact code that succeeds]

// Key differences explained
[detailed explanation of why the change works]
```

**How to recognize this pattern in future**:
[Warning signs, code smells, error patterns that indicate this same issue]

**Related issues**:
- [Similar problems this approach might cause]
- [Other parts of codebase that might have the same issue]
- [Preventive measures for avoiding this pattern]

**Time lost on this issue**: [Hours spent debugging]
**Confidence level**: [How sure you are this solution works]
**Alternative approaches considered**: [Other solutions tried and why they didn't work]
```

## Investigation Approach (Forensic-Level Detail)

Before writing your roadmap updates, conduct thorough forensic analysis:

### 1. **Failure Path Reconstruction**
- **Timeline creation**: Exact sequence of events that led to problems, with timestamps
- **Decision tree analysis**: At each decision point, document why you chose that path and what the alternatives were
- **Code change tracking**: Every single file modification, why it was made, what it was supposed to accomplish
- **Testing at each step**: What tests passed/failed at each stage, what that revealed

### 2. **Assumption Archaeology** 
- **Original assumptions**: What you thought was true when you started
- **Evidence for assumptions**: What made these assumptions seem reasonable
- **Reality check**: Specific evidence that contradicted each assumption
- **Assumption source**: Where each false assumption came from (docs, code comments, team knowledge, etc.)

### 3. **Dependency Mapping (Complete)**
- **Static analysis**: All imports, requires, includes in affected files
- **Runtime dependencies**: What gets loaded/called at execution time
- **Configuration dependencies**: Environment variables, config files, build settings that affect behavior
- **Temporal dependencies**: What must happen before what, including async operations
- **Data dependencies**: What data structures must exist in what state

### 4. **Timing and Concurrency Analysis**
- **Race condition documentation**: Specific scenarios where timing matters
- **Async operation mapping**: All promises, callbacks, event handlers and their interactions
- **State synchronization issues**: When different parts of the system have inconsistent state
- **Event ordering problems**: When events fire in unexpected sequences

### 5. **Environmental Factor Analysis**
- **Development vs production differences**: What works in dev but fails elsewhere
- **Browser-specific behaviors**: Differences between Chrome/Firefox/Safari that matter
- **Operating system differences**: Mac vs Windows vs Linux issues
- **Hardware dependencies**: Memory, CPU, disk speed considerations
- **Network dependencies**: What requires network access and how failures are handled

## Tone and Style

- **Empathetic but direct**: You're helping your past self, not criticizing
- **Specific over generic**: Reference exact files, functions, and line numbers  
- **Actionable**: Every insight should lead to a concrete next action
- **Honest about complexity**: Don't sugarcoat how difficult this actually is

## Final Checklist

Before finishing your roadmap updates:
- [ ] Did you read and understand the existing roadmap structure?
- [ ] Are your additions clearly marked as "lessons learned" vs original content?
- [ ] Did you update task dependencies and priorities based on what you discovered?
- [ ] Would past you actually understand how the updated roadmap avoids the problems you hit?
- [ ] Did you explain WHY the roadmap needed updates, not just WHAT updates you made?
- [ ] Are there concrete code examples of what works vs what doesn't?
- [ ] Did you identify if any roadmap tasks can be simplified or eliminated?
- [ ] Would this updated roadmap save future attempts hours of frustration?
- [ ] Does the roadmap still flow logically after your updates?

## Getting Started

1. **First, thoroughly read the existing `implementation_roadmap.md`** to understand:
   - The current planned approach
   - Task order and dependencies  
   - Assumptions built into the roadmap

2. **Then analyze your failed refactor attempt**:
   - What changes were made
   - What errors occurred  
   - What behavior changed unexpectedly
   - What assumptions proved wrong
   - Which roadmap tasks were affected

3. **Finally, update the roadmap** by integrating your lessons learned in a way that enhances rather than disrupts the existing plan.