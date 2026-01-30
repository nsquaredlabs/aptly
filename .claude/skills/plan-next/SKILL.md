---
name: plan-next
description: Analyzes work summaries, PRDs, spec, and codebase to identify and write the next PRD for implementation
---

# Plan Next Feature Skill

This skill analyzes the current project state - completed work, existing PRDs, the spec, and the codebase - to identify and write the next logical PRD for implementation.

## Usage

```
/plan-next [optional focus area]
```

Examples:
- `/plan-next` - Analyze everything and suggest the next feature
- `/plan-next authentication` - Focus on authentication-related features
- `/plan-next from spec section 5` - Focus on a specific spec section

## Workflow

### Phase 1: Gather Context

Read and analyze the following sources in order:

1. **SPEC.md** - The source of truth for what the product should become
   - Identify all planned features and capabilities
   - Note the "What's NOT in MVP" section for Phase 2+ features
   - Extract the success criteria and verification commands

2. **Work Summaries** (`project-docs/work-summaries/`)
   - Read ALL work summary files chronologically
   - Build a list of what has been implemented
   - Note any follow-up items or known issues mentioned

3. **Existing PRDs** (`project-docs/prds/`)
   - Read ALL PRD files
   - Identify which PRDs have been implemented (cross-reference with work summaries)
   - Note any PRDs that are approved but not yet started

4. **Codebase Scan**
   - Check `src/` for implemented modules and their completeness
   - Check `tests/` for test coverage gaps
   - Look for TODO comments or incomplete implementations
   - Review any failing tests or known issues

### Phase 2: Gap Analysis

Create a structured analysis focused on **features and enhancements**, not test coverage:

```markdown
## Implementation Status

### Completed Features
- [x] Feature A (PRD: YYYY-MM-DD-feature-a.md, Summary: YYYY-MM-DD-feature-a.md)
- [x] Feature B (PRD: YYYY-MM-DD-feature-b.md, Summary: YYYY-MM-DD-feature-b.md)

### In Progress / Partial
- [ ] Feature C - 60% complete, missing X and Y

### Not Started (from Spec)
- [ ] Feature D - Section X of spec
- [ ] Feature E - Section Y of spec

### Phase 2+ Features (candidates for promotion)
- Feature X - would enable Y use case
- Feature Z - customer-requested
```

**Important:** Do NOT recommend test coverage improvements as next steps. Test coverage is handled by the `/implement` skill during feature development. Focus on:
- New user-facing features
- Enhancements to existing functionality
- API additions
- Performance improvements
- Integration capabilities

### Phase 3: Prioritize Next Feature

Consider these factors when choosing the next feature to implement:

1. **User Value** - Does it add functionality users will benefit from?
2. **Dependencies** - Can it be built with current infrastructure?
3. **Strategic Fit** - Does it move the product toward its vision?
4. **User Request** - Did the user specify a focus area?

**Do NOT recommend:**
- Test coverage improvements (handled during implementation)
- Code refactoring for its own sake
- Documentation-only tasks

Present a prioritized list to the user:

```markdown
## Recommended Next Steps

### Option 1: [Feature Name] (Recommended)
**Why:** [Brief justification focused on user/business value]
**Effort:** [Small/Medium/Large]
**Unlocks:** [What this enables for users]

### Option 2: [Feature Name]
**Why:** [Brief justification]
**Effort:** [Small/Medium/Large]

### Option 3: [Feature Name]
**Why:** [Brief justification]
```

### Phase 4: Write PRD

Once the user confirms which feature to pursue:

1. Create a new PRD file at `project-docs/prds/YYYY-MM-DD-<feature-slug>.md`
2. Follow the PRD template structure (see below)
3. Reference specific sections from SPEC.md where applicable
4. Ensure requirements are specific, testable, and numbered
5. Present the PRD to the user for review

## PRD Template

```markdown
# PRD: <Feature Name>

**Date:** YYYY-MM-DD
**Status:** Draft
**Spec Reference:** [Section X of SPEC.md if applicable]

## Overview

<Brief description of what this feature does and why it's the logical next step>

## Context

### Current State
<What exists today that this builds on>

### Gap Being Addressed
<What's missing that this PRD addresses>

## Requirements

1. <Specific, testable requirement>
2. <Specific, testable requirement>
3. ...

## Technical Approach

<High-level implementation strategy, referencing existing patterns in the codebase>

## Files to Modify/Create

- `path/to/existing.py` - <what changes>
- `path/to/new_file.py` - <new file purpose>

## Database Changes

<Any schema changes needed - reference existing migration patterns>

## Testing Strategy

- Unit tests for <component>
- Integration tests for <flow>
- Critical test cases that MUST pass:
  - `test_feature_basic` - <what it verifies>
  - `test_feature_edge_case` - <what it verifies>

## Dependencies

- <Any external dependencies or prerequisites>
- <Features that must exist first>

## Out of Scope

- <What this feature explicitly does NOT include>
- <Deferred to future PRDs>

## Success Criteria

- [ ] <Verification that feature works>
- [ ] <Test coverage requirement>
- [ ] <Integration requirement>
```

## Analysis Output Template

When presenting your analysis, use this format:

```markdown
# Project Analysis for Next PRD

**Analysis Date:** YYYY-MM-DD
**Spec Version:** X.Y.Z

## Sources Analyzed

| Source | Files | Last Updated |
|--------|-------|--------------|
| Work Summaries | N files | YYYY-MM-DD |
| PRDs | N files | YYYY-MM-DD |
| SPEC.md | 1 file | YYYY-MM-DD |
| Source Code | N files in src/ | - |
| Tests | N files in tests/ | - |

## Implementation Status

[Use the format from Phase 2]

## Recommended Next Steps

[Use the format from Phase 3]

---

**Ready to write PRD for:** [Feature Name]

Shall I proceed with writing the PRD?
```

## Important Notes

- Always read ALL relevant files before making recommendations
- Cross-reference work summaries with PRDs to verify completion status
- Check for discrepancies between spec, PRDs, and actual implementation
- **Focus on features and enhancements, NOT test coverage** - tests are created during implementation
- The user has final say on which feature to implement next
- Once PRD is written, the user can use `/implement` to execute it
