# Agent Build & Run Instructions

## Project Type
Documentation project using Mintlify

## Prerequisites
- Mintlify CLI: `npm install -g mintlify`
- Python 3.11+ (for testing API examples)
- Access to src/ codebase for reference

## Preview Documentation Locally
```bash
cd docs
mintlify dev
```
This will start a local server at http://localhost:3000

## Validate Documentation
```bash
# Check for broken links (if tool available)
# Check that all code examples are valid syntax
# Verify mint.json is valid JSON
cat docs/mint.json | python -m json.tool > /dev/null
```

## Test API Examples
When creating code examples for API endpoints:

```bash
# 1. Start local Aptly server (if needed to test examples)
cd /Users/nishal/projects/aptly
uvicorn src.main:app --reload --port 8000

# 2. Test curl examples from documentation
# Copy/paste from docs and verify they work

# 3. Test Python examples
# Create temp script and run
```

## Build Commands
**Not applicable** - This is a documentation project. Mintlify builds happen in cloud or via `mintlify build`.

## Test Commands
**Not applicable** - Documentation quality is verified manually and through Mintlify preview.

## Deployment
Documentation will be deployed via:
- Mintlify Cloud (automatic from GitHub)
- Or self-hosted via `mintlify build` → static site export

## Current Status
Creating comprehensive documentation for Aptly API.
Progress tracked in .ralph/fix_plan.md

## Notes
- This project creates DOCUMENTATION, not code
- Reference existing code in src/ for accurate examples
- All new files go in /docs directory
- Follow Mintlify .mdx format
- Include curl + Python examples for every API endpoint
