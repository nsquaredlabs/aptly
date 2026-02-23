# PRD: Customer Dashboard & Settings

**Date:** 2026-02-19
**Status:** Proposed
**Priority:** High
**Estimated Effort:** 3-4 days

## Overview

Build the customer-facing dashboard UI in the existing Next.js app (`web/`). This is the foundational UX that turns Aptly from an API-only tool into a self-service product. Customers need to sign up, log in, manage API keys, select compliance frameworks, and view their plan -- all without contacting an admin.

### Why Now

1. **All backend APIs exist.** Customer creation (`POST /v1/admin/customers`), API key CRUD (`/v1/api-keys`), profile read/update (`/v1/me`), and analytics (`/v1/analytics/*`) are all implemented and deployed.
2. **No self-service path exists.** Currently, creating a customer requires the admin secret. There is no login, no signup, no UI for key management.
3. **Prerequisite for growth.** Without a dashboard, every customer needs manual onboarding. The compliance policy engine (next PRD) also needs a UI for rule configuration.
4. **The Next.js app already exists** at `web/` with Tailwind CSS, deployed on Vercel. We just need to add authenticated pages.

## Requirements

### 1. Authentication: Signup & Login

#### Approach: Supabase Auth

Use Supabase Auth (already have a Supabase project) for email/password authentication. On signup, a Supabase Auth user is created, then a corresponding Aptly customer is created via a server-side call to the admin endpoint.

**Signup flow:**
1. User enters email, password, company name
2. Frontend calls Supabase Auth `signUp()`
3. A server-side API route (`/api/auth/signup`) calls `POST /v1/admin/customers` with the admin secret to create the Aptly customer
4. Server-side route creates a `users` row linking the Supabase Auth user to the customer (role: `owner`)
5. User is redirected to dashboard

**Login flow:**
1. User enters email, password
2. Frontend calls Supabase Auth `signInWithPassword()`
3. Dashboard loads, using the stored API key to call Aptly APIs

**Session management:**
- Supabase Auth handles JWT sessions (access + refresh tokens)
- No API key is created during signup — the user generates their first key manually from the API Keys page
- Dashboard API calls use the Supabase Auth session (JWT) directly, not Aptly API keys
- Aptly API keys are for external use (customer applications), not for dashboard auth

#### Pages

| Route | Description |
|-------|-------------|
| `/login` | Email/password login form |
| `/signup` | Email, password, company name signup form |
| `/logout` | Clear session, redirect to `/login` |

### 2. Dashboard Layout

A sidebar layout with navigation:

```
+------------------+----------------------------------------+
| Aptly            |                                        |
|                  |  [Page Content]                        |
| Dashboard        |                                        |
| API Keys         |                                        |
| Settings         |                                        |
| Logs             |                                        |
|                  |                                        |
| [Company Name]   |                                        |
| Logout           |                                        |
+------------------+----------------------------------------+
```

All dashboard routes are under `/dashboard/*` and require authentication (redirect to `/login` if no session).

### 3. Dashboard Home (`/dashboard`)

Overview page showing:

- **Usage summary** (from `GET /v1/analytics/usage`): total requests, PII detections, tokens used (current billing period)
- **Quick stats cards**: requests today, PII entities detected today, active API keys count
- **Recent activity**: last 5 audit log entries (from `GET /v1/logs?limit=5`)

### 4. API Keys Page (`/dashboard/api-keys`)

| Feature | API Endpoint | Details |
|---------|-------------|---------|
| List keys | `GET /v1/api-keys` | Show prefix, name, created date, last used, status |
| Create key | `POST /v1/api-keys` | Modal with name input. Show full key ONCE after creation with copy button |
| Revoke key | `DELETE /v1/api-keys/{id}` | Confirmation dialog. Cannot revoke the key currently in use for the session |
| Rotate key | Create new + revoke old | "Rotate" button creates a new key, shows it, then revokes the old one |

**Key display:** After creation, show the full key (`apt_live_...`) in a copy-able box with a warning: "This key will only be shown once. Copy it now." After dismissing, only the prefix is shown.

### 5. Settings Page (`/dashboard/settings`)

#### 5a. Profile Settings

| Field | Editable | API |
|-------|----------|-----|
| Company name | Yes | `PATCH /v1/me` |
| Email | Display only | From auth |
| Customer ID | Display only | From `/v1/me` |
| Plan | Display only | From `/v1/me` |
| PII redaction mode | Yes (dropdown: mask/hash/remove) | `PATCH /v1/me` |

#### 5b. Compliance Frameworks

- Show available frameworks: HIPAA, FinTech/PCI-DSS, GDPR, SOC2
- Toggle switches or checkboxes for each
- Show entity count per framework (e.g., "HIPAA: +5 entities detected")
- Save via `PATCH /v1/me` with `compliance_frameworks` field
- Show a summary of all active entities based on selected frameworks

#### 5c. Plan Information

- Display current plan name and limits
- Show usage vs. limits (requests/month, rate limit/hour)
- "Contact us to upgrade" link for now (no self-service billing in v1)

### 6. Audit Logs Page (`/dashboard/logs`)

| Feature | API | Details |
|---------|-----|---------|
| List logs | `GET /v1/logs` | Paginated table: timestamp, model, PII detected (yes/no), entity types, status |
| Filter by date | `GET /v1/logs?start_date=...&end_date=...` | Date range picker |
| Log detail | `GET /v1/logs/{id}` | Expand row or modal: full request/response metadata, PII entities with types and actions |
| Export | `GET /v1/analytics/export` | CSV download button |

## Technical Approach

### Stack

- **Framework:** Next.js App Router (already in `web/`)
- **Auth:** `@supabase/supabase-js` + `@supabase/ssr` for server-side auth
- **Styling:** Tailwind CSS (already configured)
- **UI components:** Build minimal components (no component library dependency). Cards, tables, modals, forms, sidebar.
- **API client:** Simple fetch wrapper that attaches the `Authorization: Bearer` header from the stored API key

### File Structure

```
web/
  app/
    (auth)/
      login/page.tsx
      signup/page.tsx
    (dashboard)/
      layout.tsx          # Sidebar + auth guard
      dashboard/page.tsx  # Overview
      api-keys/page.tsx
      settings/page.tsx
      logs/page.tsx
    api/
      auth/
        signup/route.ts   # Server-side customer creation
  components/
    dashboard/
      sidebar.tsx
      stat-card.tsx
      api-key-row.tsx
      log-table.tsx
      framework-selector.tsx
  lib/
    supabase/
      client.ts           # Browser Supabase client
      server.ts           # Server-side Supabase client
    aptly-api.ts          # Typed API client for Aptly endpoints
```

### Auth Guard

A middleware or layout-level check:

```typescript
// web/app/(dashboard)/layout.tsx
import { createServerClient } from '@/lib/supabase/server'
import { redirect } from 'next/navigation'

export default async function DashboardLayout({ children }) {
  const supabase = createServerClient()
  const { data: { session } } = await supabase.auth.getSession()

  if (!session) redirect('/login')

  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto p-8">{children}</main>
    </div>
  )
}
```

### Dashboard Auth vs API Keys

The dashboard authenticates via Supabase Auth sessions — NOT Aptly API keys. Dashboard API calls go through Next.js server-side routes that look up the customer by `supabase_auth_id` and use the admin secret internally. Aptly API keys (`apt_live_*`) are only for external use in customer applications.

### Environment Variables (web/)

```
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
APTLY_API_URL=https://aptly-api.nsquaredlabs.com
APTLY_ADMIN_SECRET=...  # Server-side only, for signup customer creation
```

## Backend Changes Required

### 1. Customer Lookup by Email

The signup flow needs to link a Supabase Auth user to an Aptly customer. Add a `supabase_auth_id` field to the customers table or look up by email.

**Migration:** Add a `users` table to support multiple users per customer.

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  supabase_auth_id UUID NOT NULL UNIQUE,
  customer_id UUID NOT NULL REFERENCES customers(id),
  email TEXT NOT NULL,
  role VARCHAR(50) NOT NULL DEFAULT 'member',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_supabase_auth_id ON users(supabase_auth_id);
CREATE INDEX idx_users_customer_id ON users(customer_id);
```

A customer can have multiple users. The first user to sign up creates the customer and is assigned `role = 'owner'`. Additional users can be invited later (out of scope for v1, but the data model supports it).

### 2. Signup API Enhancement

Modify `POST /v1/admin/customers` to accept an optional `supabase_auth_id` field and auto-create the first API key, returning it in the response.

Alternatively, keep the admin endpoint unchanged and have the signup API route:
1. Create customer via admin endpoint
2. Create API key via a direct Supabase insert (using the service role key, server-side only)

Recommend the second approach to avoid changing the admin API contract.

### 3. PATCH /v1/me Enhancement

Ensure `compliance_frameworks` is updatable via `PATCH /v1/me`. Check current implementation.

## Acceptance Criteria

- [ ] User can sign up with email, password, and company name
- [ ] User can log in and is redirected to dashboard
- [ ] Unauthenticated users are redirected to `/login`
- [ ] Dashboard shows usage summary and recent activity
- [ ] User can create a new API key and sees the full key once
- [ ] User can revoke an API key with confirmation
- [ ] User can rotate a key (create new + revoke old)
- [ ] User can update company name and PII redaction mode
- [ ] User can select/deselect compliance frameworks and see entity counts
- [ ] User can view paginated audit logs with date filtering
- [ ] User can export logs as CSV
- [ ] Plan information is displayed with usage vs. limits
- [ ] Session persists across page refreshes
- [ ] Logout clears session and redirects to login

## Out of Scope

- Self-service billing / plan upgrades (show "contact us" for now)
- OAuth / SSO login (email/password only for v1)
- Role-based permissions within teams (all users have equal access for v1)
- Policy engine UI (will be added after the policy engine backend ships)
- Real-time usage updates / WebSocket
- Email verification (can be added later via Supabase Auth config)

## Testing Strategy

### Manual Testing

- Full signup -> login -> dashboard -> create key -> revoke key -> update settings -> view logs flow
- Test auth redirect (visit `/dashboard` while logged out)
- Test key display (ensure full key only shown once)
- Test framework selection (verify entity count updates)

### Automated Tests

| Test | Description |
|------|-------------|
| `signup-flow.spec.ts` | E2E: signup creates user + customer, redirects to dashboard |
| `login-flow.spec.ts` | E2E: login with valid credentials shows dashboard |
| `auth-guard.spec.ts` | Unauthenticated access redirects to login |
| `api-keys.spec.ts` | Create, list, revoke keys via UI |
| `settings.spec.ts` | Update profile, select frameworks |

Use Playwright or Cypress for E2E tests. For unit tests, test the API client and auth helpers with Jest.

## Phased Implementation

Given the scope, recommend building in this order:

1. **Phase 1 (Day 1):** Auth setup (Supabase Auth integration, signup/login pages, auth guard, dashboard layout with sidebar)
2. **Phase 2 (Day 2):** API Keys page + Settings page (profile + frameworks)
3. **Phase 3 (Day 3):** Dashboard home (analytics integration) + Logs page
4. **Phase 4 (Day 4):** Polish, error handling, loading states, mobile responsiveness, E2E tests

## Success Metrics

- A new user can go from signup to first API call in under 2 minutes
- Zero admin intervention required for standard onboarding
- Dashboard loads in under 2 seconds
- All CRUD operations provide immediate visual feedback
