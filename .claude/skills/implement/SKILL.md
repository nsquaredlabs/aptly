---
name: implement
description: Structured workflow for implementing features - reads PRD, implements requirements, writes work summary
---

# Implement Feature Skill

This skill implements features from an existing PRD, tracking progress and writing a work summary when complete.

## Usage

```
/implement <prd-path-or-feature-name>
```

Examples:
- `/implement project-docs/prds/2026-01-26-streaming-support.md`
- `/implement streaming-support` (finds matching PRD by slug)

## Prerequisites

A PRD must exist before using this skill. Use `/plan-next` to create one if needed.

## Workflow

### Phase 1: Load PRD

1. Find the PRD file:
   - If a full path is provided, read that file
   - If a feature name/slug is provided, search `project-docs/prds/` for a matching file
   - If no PRD is found, inform the user to run `/plan-next` first

2. Parse the PRD and extract:
   - Requirements (numbered list)
   - Files to modify/create
   - Testing strategy
   - Success criteria

3. Present a summary to the user and confirm before proceeding

### Phase 2: Implement

1. Use the TaskCreate tool to create tasks from the PRD requirements
2. Implement each requirement one at a time, marking tasks as completed
3. Follow existing code patterns in the codebase
4. **Write tests for ALL new functionality** - this is mandatory, not optional
5. Run tests frequently during implementation and fix any failures

### Phase 3: Verify Test Coverage

**This phase is mandatory before writing the work summary.**

1. Run the full test suite with coverage:
   ```bash
   pytest tests/ -v --cov=src --cov-report=term-missing
   ```

2. Verify coverage remains **above 80%** overall
   - If coverage dropped below 80%, add more tests before proceeding
   - Focus tests on the new code paths added by this feature

3. Ensure all tests pass (0 failures)

4. Document the coverage in the work summary

### Phase 4: Write Work Summary

1. After implementation AND test verification is complete, create a summary at `project-docs/work-summaries/YYYY-MM-DD-<feature-slug>.md`
2. The summary should include:
   - **Feature**: Name of the feature implemented
   - **PRD Reference**: Link to the PRD file
   - **Changes Made**: Table of files created/modified with descriptions
   - **Tests Added**: List of test files and what they cover
   - **Test Results**: Number of tests passed and coverage percentage
   - **How to Test**: Manual verification steps
   - **Notes**: Implementation decisions, deviations from PRD, or follow-up items

## Work Summary Template

```markdown
# Work Summary: <Feature Name>

**Date:** YYYY-MM-DD
**PRD:** [Link to PRD](../prds/YYYY-MM-DD-feature-slug.md)

## Changes Made

| File | Change Type | Description |
|------|-------------|-------------|
| `path/to/file.py` | Modified | <what changed> |
| `path/to/new.py` | Created | <purpose> |

## Tests Added

| Test File | Tests | Description |
|-----------|-------|-------------|
| `tests/test_feature.py` | N tests | <what it tests> |

## Test Results

```
X passed in Y.YYs
Coverage: ZZ%
```

## How to Test

1. <Step to verify the feature works>
2. <Another verification step>

## Notes

- <Important implementation decisions>
- <Any deviations from the PRD>
- <Follow-up items if any>
```

## Important

- Always get user confirmation after loading the PRD before starting implementation
- Use TaskCreate/TaskUpdate to track progress through requirements
- Run tests frequently during implementation
- **Tests are mandatory**: Every new feature must have corresponding tests
- **Coverage gate**: Do not complete implementation if coverage drops below 80%
- If requirements need to change, update the PRD file
- The work summary should be accurate - only document what was actually done
- Mark the PRD status as "Implemented" when complete
