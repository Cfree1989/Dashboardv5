# Code Refactoring Analysis Prompt

You are a senior software engineer specializing in code refactoring and architectural improvement. Your task is to analyze the following large code files (1000+ lines each) and provide a comprehensive refactoring strategy to break them into smaller, more maintainable components:

## Target Files for Analysis
-All

## Required Output Files
You must create the following three essential report files with detailed analysis and recommendations:

- **`refactoring_executive_summary.md`** - Strategic overview, methodology selection, and high-level plan
- **`cross_file_dependencies_analysis.md`** - Analysis of dependencies between all four files and risk mitigation
- **`implementation_roadmap.md`** - Step-by-step implementation guide with proper sequencing and milestones

## Refactoring Methodologies & Approaches

### Core Methodologies to Consider
- **Fowler's Refactoring Catalog**: Apply systematic refactoring patterns (Extract Method, Extract Class, Move Method, etc.)
- **Strangler Fig Pattern**: Gradually replace sections while maintaining full functionality
- **Branch by Abstraction**: Create abstractions to enable safe parallel development
- **Mikado Method**: Map dependencies before refactoring to avoid breaking changes
- **Working Effectively with Legacy Code (Feathers)**: Add characterization tests before any structural changes
- **Domain-Driven Design (DDD)**: Organize code around business domains and bounded contexts
- **Clean Architecture**: Separate concerns into layers with clear dependency rules
- **SOLID Principles**: Apply Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion

### Safety-First Approaches
- **Test-First Refactoring**: Ensure comprehensive test coverage before making changes
- **Incremental Refactoring**: Make small, reversible changes with immediate verification
- **Parallel Run Strategy**: Run old and new implementations side-by-side for validation
- **Feature Toggles**: Use flags to switch between old and new implementations
- **Characterization Testing**: Capture existing behavior as tests before refactoring

## Analysis Framework

### 1. Initial Assessment
- **File Overview**: Summarize the primary purpose and responsibilities of the file
- **Size Metrics**: Report line count, function count, class count, and complexity indicators
- **Architecture Patterns**: Identify current architectural patterns or lack thereof
- **Dependencies**: Map external dependencies and internal coupling

### 2. Responsibility Analysis
- **Single Responsibility Violations**: Identify areas where the file handles multiple distinct concerns
- **Functional Groupings**: Categorize functions/methods by their primary responsibility
- **Data Flow Mapping**: Trace how data flows through different sections of the file
- **Business Logic Separation**: Distinguish between business logic, data access, presentation, and utility functions

### 3. Functionality Preservation Strategy
- **Behavior Documentation**: Catalog all current behaviors, including edge cases and error conditions
- **Regression Risk Assessment**: Identify high-risk areas where changes could break existing functionality
- **Test Gap Analysis**: Find untested behaviors that need characterization tests before refactoring
- **Side Effect Mapping**: Document all side effects, state changes, and external dependencies
- **Performance Baseline**: Establish current performance metrics to ensure no degradation
- **API Compatibility Matrix**: Map all public interfaces that must remain unchanged
- **Data Flow Integrity**: Ensure data transformations remain identical through refactoring
- **Class Extraction**: Identify groups of related functions that could form cohesive classes
- **Module Extraction**: Find standalone utilities or helpers that belong in separate modules
- **Service Layer Extraction**: Locate business logic that could be moved to dedicated service classes
- **Configuration Extraction**: Find hardcoded values or configuration that should be externalized
- **Constants and Enums**: Identify magic numbers and strings that should be extracted

### 4. Extraction Opportunities
- **Class Extraction**: Identify groups of related functions that could form cohesive classes
- **Module Extraction**: Find standalone utilities or helpers that belong in separate modules
- **Service Layer Extraction**: Locate business logic that could be moved to dedicated service classes
- **Configuration Extraction**: Find hardcoded values or configuration that should be externalized
- **Constants and Enums**: Identify magic numbers and strings that should be extracted

### 5. Dependency Issues
- **Circular Dependencies**: Identify potential circular dependency risks in proposed extractions
- **Coupling Analysis**: Assess tight coupling between different sections
- **Interface Opportunities**: Suggest where interfaces or abstract base classes could reduce coupling
- **Dependency Injection Points**: Recommend where DI could improve testability and flexibility

### 6. Refactoring Strategy Selection
- **Risk vs. Benefit Analysis**: Weigh refactoring benefits against implementation risks for each approach
- **Methodology Recommendation**: Choose the most appropriate refactoring methodology based on:
  - Current test coverage levels
  - Team experience and constraints
  - System criticality and uptime requirements
  - Available refactoring timeline
  - Dependencies and integration complexity
- **Phased Implementation Plan**: Design incremental steps that maintain functionality at each stage
- **Rollback Strategy**: Plan how to revert changes if issues arise
- **Validation Approach**: Define how to verify functionality is preserved after each phase
- **Phase-by-Phase Plan**: Provide a step-by-step refactoring approach with logical phases
- **Risk Assessment**: Identify high-risk refactoring areas that need extra testing
- **Testing Strategy**: Recommend testing approaches for each refactoring phase
- **Backward Compatibility**: Suggest strategies to maintain API compatibility during refactoring

### 6. Proposed File Structure
- **New File Organization**: Suggest specific new files/modules and their responsibilities
- **Naming Conventions**: Recommend clear, descriptive names for extracted components
- **Directory Structure**: Propose logical directory organization for the refactored code
- **Import Strategy**: Plan how modules will import and depend on each other

## Deliverables

### Required Report Files
Create each of the following three essential files with comprehensive analysis:

#### 1. `refactoring_executive_summary.md`
- **Executive Summary**: High-level overview of refactoring benefits and approach across all files
- **Current State Analysis**: Detailed breakdown of existing code structure and issues for each file
- **Methodology Selection**: Chosen refactoring approach with justification
- **Strategic Recommendations**: Key architectural decisions and component extractions
- **Functionality Preservation Plan**: Strategy for maintaining all existing behaviors
- **Timeline and Resource Estimates**: Overall project scope and effort required
- **Risk Assessment**: Major risks and mitigation strategies

#### 2. `cross_file_dependencies_analysis.md`
- **Dependency Mapping**: Visual representation of current inter-file dependencies
- **Circular Dependency Risks**: Potential issues from proposed extractions
- **Shared Component Opportunities**: Code that could be extracted into shared modules
- **Interface Design**: Proposed APIs between refactored components
- **Migration Strategy**: How to handle cross-file dependencies during refactoring
- **Breaking Change Analysis**: Impact assessment of proposed changes
- **Component Isolation Strategy**: Plan for decoupling tightly coupled code

#### 3. `implementation_roadmap.md`
- **Phase-by-Phase Plan**: Prioritized refactoring sequence across all files
- **Dependency-Aware Ordering**: Sequence that minimizes breaking changes
- **Milestone Definitions**: Clear checkpoints with deliverables and success criteria
- **Detailed Implementation Steps**: Specific actionable tasks for each phase
- **Testing Strategy**: Characterization tests, unit tests, and regression testing approach
- **Parallel Work Opportunities**: Tasks that can be done simultaneously
- **Integration Points**: When and how refactored components will be integrated
- **Rollback Procedures**: Clear steps for reverting changes if problems arise

### Code Examples
For each major extraction, provide:
- **Before/After Code Snippets**: Show current structure vs. proposed structure
- **Interface Definitions**: Suggest clear interfaces for extracted components
- **Usage Examples**: Demonstrate how refactored code would be used
- **Migration Guide**: Show how existing code would be updated to use new structure

## Analysis Guidelines

### Focus Areas
- **Functionality Preservation**: Ensure zero regression in existing behavior and performance
- **Maintainability**: Prioritize changes that make code easier to understand and modify
- **Testability**: Emphasize extractions that improve unit testing capabilities
- **Reusability**: Identify components that could be reused across the codebase
- **Performance**: Monitor and maintain current performance characteristics
- **Team Productivity**: Focus on changes that will improve developer experience
- **Risk Minimization**: Prioritize low-risk, high-impact refactoring opportunities first

### Constraints to Consider
- **Breaking Changes**: Minimize disruption to existing APIs and interfaces
- **Development Timeline**: Balance thoroughness with practical implementation timeframes
- **Team Familiarity**: Consider the team's experience with proposed patterns and architectures
- **System Integration**: Ensure refactored components integrate well with existing systems

### Quality Metrics
- **Cyclomatic Complexity**: Target reducing complexity in individual methods/functions
- **Code Duplication**: Identify and eliminate repeated code patterns
- **Method/Function Length**: Aim for functions under 20-30 lines where possible
- **Class Size**: Target classes with focused, single responsibilities

## Expected Outcome

The analysis should result in a clear, actionable plan that transforms a monolithic file into a well-organized, maintainable codebase with:
- Smaller, focused modules with single responsibilities
- Clear separation of concerns
- Improved testability and maintainability
- Reduced coupling and increased cohesion
- Better code organization and discoverability

Provide specific, practical recommendations that can be implemented incrementally without disrupting existing functionality.