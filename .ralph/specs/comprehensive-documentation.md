# PRD: Comprehensive Documentation with Mintlify

**Date:** 2026-01-30
**Status:** Draft
**Spec Reference:** General MVP requirement for usability

## Overview

Create comprehensive documentation for Aptly using Mintlify, including a README, quickstart guide, API reference, and architectural guides. This will enable self-service customer onboarding and reduce the barrier to adoption.

## Context

### Current State
- SPEC.md exists as internal product specification
- DEPLOYMENT.md exists for production setup
- CLAUDE.md exists for AI assistant guidance
- No README.md (critical for GitHub discoverability)
- No customer-facing documentation
- No API reference documentation
- No usage examples or tutorials

### Gap Being Addressed
Without user-facing documentation, potential customers cannot:
- Understand what Aptly does at a glance
- Learn how to integrate Aptly into their applications
- Reference API endpoints and parameters
- Troubleshoot common issues
- Understand PII redaction modes and compliance features

This PRD addresses the documentation gap to enable adoption.

## Requirements

### 1. GitHub README.md
Create a project README that serves as the landing page:
- **1.1** Clear one-line description and value proposition
- **1.2** Key features list (PII redaction, audit logging, multi-provider)
- **1.3** Quick installation/setup instructions
- **1.4** Simple usage example (creating customer + chat completion)
- **1.5** Link to full documentation (Mintlify site)
- **1.6** Badges for build status, coverage, license
- **1.7** Contributing guidelines and license information

### 2. Mintlify Configuration
Set up Mintlify documentation platform:
- **2.1** Create `/docs` directory for all documentation files
- **2.2** Create `mint.json` configuration file with navigation structure
- **2.3** Configure branding (name, colors, logo placeholder)
- **2.4** Set up navigation groups: Getting Started, API Reference, Guides, Deployment
- **2.5** Configure OpenAPI/API reference if applicable

### 3. Getting Started Documentation
Create introductory content in `/docs`:
- **3.1** **Introduction** (`/docs/introduction.mdx`) - What is Aptly, key benefits, use cases
- **3.2** **Quickstart** (`/docs/quickstart.mdx`) - 5-minute setup guide:
  - Prerequisites (Supabase, Redis)
  - Installation steps
  - Environment configuration
  - Creating first customer
  - Making first API request
- **3.3** **Authentication** (`/docs/authentication.mdx`) - Explain admin secret vs API keys, how to authenticate requests

### 4. API Reference Documentation
Document all 13 API endpoints in `/docs/api/`:
- **4.1** Health endpoint (`/docs/api/health.mdx`)
- **4.2** Admin endpoints (`/docs/api/admin/`):
  - Create customer
  - List customers
  - Get customer
  - Create API key for customer
- **4.3** Chat completions endpoint (`/docs/api/chat-completions.mdx`) - The main feature:
  - Request parameters (required and optional)
  - Streaming vs non-streaming
  - PII redaction behavior
  - Response format
  - Error codes
  - Example requests (OpenAI, Anthropic, etc.)
- **4.4** Customer endpoints (`/docs/api/customer/`):
  - List API keys
  - Create API key
  - Revoke API key
  - Get profile
  - Update settings
- **4.5** Audit logs endpoints (`/docs/api/audit-logs/`):
  - Query logs
  - Get log detail

### 5. Guides
Create practical guides in `/docs/guides/`:
- **5.1** **PII Redaction Guide** (`/docs/guides/pii-redaction.mdx`):
  - Supported entity types
  - Redaction modes (mask, hash, remove)
  - Examples for each mode
  - Response PII detection
  - When to use `redact_response: true`
- **5.2** **Compliance Guide** (`/docs/guides/compliance.mdx`):
  - HIPAA compliance features
  - Audit log immutability
  - Data retention
  - Supported compliance frameworks
- **5.3** **Rate Limiting** (`/docs/guides/rate-limiting.mdx`):
  - How rate limits work
  - Rate limit headers
  - Plan-based limits
  - Handling 429 responses
- **5.4** **Streaming Responses** (`/docs/guides/streaming.mdx`):
  - When to use streaming
  - SSE format
  - Client implementation examples
  - Error handling in streams

### 6. Architecture & Deployment
Document system design in `/docs/deployment/`:
- **6.1** **Architecture Overview** (`/docs/deployment/architecture.mdx`):
  - Request flow diagram (text-based or mermaid)
  - Component descriptions
  - Data flow
  - Security model
- **6.2** **Deployment Guide** (`/docs/deployment/production.mdx`) - Adapt existing DEPLOYMENT.md:
  - Supabase setup
  - Redis setup
  - Railway deployment
  - Environment variables reference
- **6.3** **Local Development** (`/docs/deployment/local-development.mdx`):
  - Setting up development environment
  - Running tests
  - Using docker-compose for Redis

### 7. Additional Resources
- **7.1** **Troubleshooting** (`/docs/troubleshooting.mdx`) - Common errors and solutions
- **7.2** **FAQ** (`/docs/faq.mdx`) - Frequently asked questions
- **7.3** **Changelog** (`/docs/changelog.mdx`) - Version history (link to git tags/releases)

## Technical Approach

### Mintlify Structure
```
/
├── README.md                          # GitHub landing page
├── docs/
│   ├── mint.json                      # Mintlify configuration
│   ├── introduction.mdx               # What is Aptly
│   ├── quickstart.mdx                 # 5-min getting started
│   ├── authentication.mdx             # Auth guide
│   ├── api/
│   │   ├── health.mdx
│   │   ├── chat-completions.mdx       # Main endpoint (detailed)
│   │   ├── admin/
│   │   │   ├── create-customer.mdx
│   │   │   ├── list-customers.mdx
│   │   │   ├── get-customer.mdx
│   │   │   └── create-api-key.mdx
│   │   ├── customer/
│   │   │   ├── list-keys.mdx
│   │   │   ├── create-key.mdx
│   │   │   ├── revoke-key.mdx
│   │   │   ├── get-profile.mdx
│   │   │   └── update-settings.mdx
│   │   └── audit-logs/
│   │       ├── query-logs.mdx
│   │       └── get-log.mdx
│   ├── guides/
│   │   ├── pii-redaction.mdx
│   │   ├── compliance.mdx
│   │   ├── rate-limiting.mdx
│   │   └── streaming.mdx
│   ├── deployment/
│   │   ├── architecture.mdx
│   │   ├── production.mdx
│   │   └── local-development.mdx
│   ├── troubleshooting.mdx
│   ├── faq.mdx
│   └── changelog.mdx
```

### mint.json Configuration
```json
{
  "name": "Aptly",
  "logo": {
    "dark": "/logo/dark.svg",
    "light": "/logo/light.svg"
  },
  "favicon": "/favicon.svg",
  "colors": {
    "primary": "#3b82f6",
    "light": "#60a5fa",
    "dark": "#2563eb"
  },
  "navigation": [
    {
      "group": "Getting Started",
      "pages": ["introduction", "quickstart", "authentication"]
    },
    {
      "group": "API Reference",
      "pages": [
        "api/health",
        "api/chat-completions",
        {
          "group": "Admin",
          "pages": ["api/admin/create-customer", "api/admin/list-customers", ...]
        },
        {
          "group": "Customer",
          "pages": ["api/customer/list-keys", "api/customer/create-key", ...]
        },
        {
          "group": "Audit Logs",
          "pages": ["api/audit-logs/query-logs", "api/audit-logs/get-log"]
        }
      ]
    },
    {
      "group": "Guides",
      "pages": ["guides/pii-redaction", "guides/compliance", ...]
    },
    {
      "group": "Deployment",
      "pages": ["deployment/architecture", "deployment/production", ...]
    },
    {
      "group": "Resources",
      "pages": ["troubleshooting", "faq", "changelog"]
    }
  ]
}
```

### Content Style Guide
- Use active voice and imperative mood ("Create a customer" not "A customer is created")
- Include code examples for every API endpoint
- Show both curl and Python requests library examples
- Include expected responses (success and error cases)
- Use callouts for important notes, warnings, and tips
- Keep explanations concise but complete
- Link related pages (e.g., chat completions → PII redaction guide)

### Code Examples Standard
Every API endpoint should have:
1. **curl example** - Universal, works everywhere
2. **Python example** - Primary language for customers
3. **Expected response** - JSON formatted
4. **Error response** - At least one common error case

Example format:
```mdx
## Create Customer

<CodeGroup>
```bash curl
curl -X POST https://api.aptly.dev/v1/admin/customers \
  -H "X-Admin-Secret: your-admin-secret" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@company.com",
    "company_name": "Company Inc",
    "plan": "pro"
  }'
```

```python Python
import requests

response = requests.post(
    "https://api.aptly.dev/v1/admin/customers",
    headers={
        "X-Admin-Secret": "your-admin-secret",
        "Content-Type": "application/json"
    },
    json={
        "email": "admin@company.com",
        "company_name": "Company Inc",
        "plan": "pro"
    }
)

customer = response.json()
print(f"API Key: {customer['api_key']['key']}")  # Save this!
```
</CodeGroup>

<ResponseExample>
```json 201 Created
{
  "customer": {
    "id": "cus_abc123",
    "email": "admin@company.com",
    ...
  },
  "api_key": {
    "key": "apt_live_xyz789...",
    ...
  }
}
```
</ResponseExample>
```

## Files to Create

### New Files
- `README.md` - GitHub landing page
- `docs/mint.json` - Mintlify configuration
- `docs/introduction.mdx` - Product introduction
- `docs/quickstart.mdx` - Getting started guide
- `docs/authentication.mdx` - Auth documentation
- `docs/api/*.mdx` - 13+ API endpoint docs
- `docs/guides/*.mdx` - 4 guide documents
- `docs/deployment/*.mdx` - 3 deployment docs
- `docs/troubleshooting.mdx` - Troubleshooting guide
- `docs/faq.mdx` - FAQ
- `docs/changelog.mdx` - Version history

### Files to Reference (Not Modify)
- `SPEC.md` - Source of truth for API behavior
- `DEPLOYMENT.md` - Source for production deployment docs
- `src/main.py` - Source for endpoint parameters and responses
- `tests/*.py` - Source for realistic examples

## Dependencies

- Mintlify CLI (for local preview): `npm install -g mintlify`
- No runtime dependencies (static documentation)
- Mintlify cloud hosting (free tier available)

## Testing Strategy

### Documentation Quality Checks
- **Manual Review**: Read through all docs for clarity and accuracy
- **Code Example Validation**: Test all curl/Python examples against local server
- **Link Validation**: Ensure all internal links work
- **Mintlify Preview**: Run `mintlify dev` to preview locally
- **Spell Check**: Use spell checker on all content
- **Technical Accuracy**: Cross-reference API docs with SPEC.md and actual implementation

### Verification Checklist
- [ ] README.md renders correctly on GitHub
- [ ] mint.json navigation structure works
- [ ] All API endpoints documented
- [ ] All code examples tested and working
- [ ] No broken internal links
- [ ] Mintlify preview builds without errors
- [ ] Deployment guide tested against Railway
- [ ] PII examples show correct redaction behavior

### No Automated Tests Required
Documentation is not code - focus on:
- Accuracy (matches actual API behavior)
- Completeness (covers all endpoints)
- Clarity (easy for developers to understand)
- Examples (working code samples)

## Out of Scope

- **Video tutorials** - Text documentation only for MVP
- **Interactive API playground** - Use curl examples instead
- **Auto-generated API docs from OpenAPI** - Manual documentation for better quality
- **Dashboard/UI documentation** - No dashboard exists (API-only product)
- **Client SDK documentation** - SDK doesn't exist yet (future PRD)
- **Translation to other languages** - English only for MVP
- **Versioned docs** - Single version for MVP (v3.0.0)

## Success Criteria

- [ ] README.md exists and clearly explains Aptly's value proposition
- [ ] Mintlify site builds and deploys successfully
- [ ] All 13 API endpoints have complete documentation with examples
- [ ] Quickstart guide allows a new user to make their first API call in <10 minutes
- [ ] PII redaction guide includes examples for all 3 modes (mask, hash, remove)
- [ ] Deployment guide successfully tested on clean Railway project
- [ ] Zero broken links in documentation
- [ ] Code examples tested and verified working

## Notes

### Mintlify Deployment Options
1. **Mintlify Cloud** (Recommended) - Free hosting, automatic builds from GitHub
2. **Self-hosted** - Export static site, host on Vercel/Netlify
3. **Local only** - Use `mintlify dev` for development

For MVP, use Mintlify Cloud for simplicity.

### Content Migration
- Adapt DEPLOYMENT.md → `/docs/deployment/production.mdx`
- Extract API examples from tests → API reference docs
- Use SPEC.md as reference but write for end-users, not internal team

### Maintainability
- Keep docs close to code (`/docs` in same repo)
- Update docs in same PR as code changes
- Link from README to Mintlify docs site
- Use Mintlify's GitHub integration for auto-deploys
