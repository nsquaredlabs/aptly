# Work Summary: Customer Dashboard & Settings

**Date:** 2026-02-19
**PRD:** [Customer Dashboard & Settings](../prds/2026-02-19-customer-dashboard.md)

## What Was Built

A full self-service customer dashboard in the existing Next.js app (`web/`), allowing customers to sign up, manage API keys, configure compliance settings, and view audit logs — without any admin intervention.

## Files Changed

| File | Change Type | Description |
|------|-------------|-------------|
| `supabase/migrations/20260219000000_add_users_table.sql` | Created | `users` table linking Supabase Auth users to Aptly customers (supports multiple users per customer) |
| `web/lib/supabase/client.ts` | Created | Browser-side Supabase client |
| `web/lib/supabase/server.ts` | Created | Server-side Supabase client with cookie handling |
| `web/lib/supabase/admin.ts` | Created | Service role client (bypasses RLS) for server-side dashboard operations |
| `web/lib/auth.ts` | Created | `requireAuth()` helper — validates session, returns user context, redirects to `/login` if unauthenticated |
| `web/lib/aptly-api.ts` | Created | Admin API client — `adminCreateCustomer()` and `adminCreateAPIKey()` (only operations needing raw key generation) |
| `web/proxy.ts` | Created | Session refresh proxy (Next.js 16 proxy convention) |
| `web/app/(auth)/login/page.tsx` | Created | Email/password login form |
| `web/app/(auth)/signup/page.tsx` | Created | Signup form: email, password, company name |
| `web/app/api/auth/signup/route.ts` | Created | Server route: creates Aptly customer + `users` row on signup |
| `web/app/api/logs/export/route.ts` | Created | CSV export of audit logs |
| `web/app/dashboard/layout.tsx` | Created | Auth guard + sidebar layout for all dashboard routes |
| `web/app/dashboard/page.tsx` | Created | Dashboard home: stat cards + recent activity |
| `web/app/dashboard/api-keys/page.tsx` | Created | API Keys server component |
| `web/app/dashboard/api-keys/api-keys-client.tsx` | Created | API Keys interactive UI (create/revoke with confirmations) |
| `web/app/dashboard/api-keys/actions.ts` | Created | Server actions: `createKey()`, `revokeKey()` |
| `web/app/dashboard/settings/page.tsx` | Created | Settings server component |
| `web/app/dashboard/settings/settings-client.tsx` | Created | Settings form: profile, PII mode, compliance frameworks, plan |
| `web/app/dashboard/settings/actions.ts` | Created | Server action: `updateSettings()` |
| `web/app/dashboard/logs/page.tsx` | Created | Logs server component with date filtering + pagination |
| `web/app/dashboard/logs/logs-client.tsx` | Created | Logs table with expandable rows and PII entity details |
| `web/components/dashboard/sidebar.tsx` | Created | Sidebar nav with active state + logout |
| `web/.env.local.example` | Created | Required environment variables |
| `web/package.json` | Modified | Added `@supabase/supabase-js`, `@supabase/ssr` |

## Key Decisions

1. **Dashboard uses Supabase directly, not Aptly API keys.** Since raw API keys can't be recovered from hashes, the dashboard reads data from Supabase via the service role client. Only API key *creation* goes through the Aptly admin endpoint (to generate `apt_live_*` keys).

2. **`users` table from day one.** Multiple users per customer supported at the data model level. Invite flows are out of scope for v1 but the schema is ready.

3. **No API key auto-created on signup.** Users generate their first key manually from the API Keys page (consistent with developer platform expectations).

4. **Server Actions for mutations.** Create/revoke keys and update settings use Next.js Server Actions, keeping API secrets server-side only.

5. **All dashboard auth via Supabase Auth sessions.** Aptly API keys (`apt_live_*`) are purely for external use in customer applications — never used by the dashboard itself.

## Testing

Build verified: `npm run build` passes with 0 type errors. Routes confirmed:

```
/login               — Auth: Login
/signup              — Auth: Signup
/dashboard           — Dashboard home (stats + recent activity)
/dashboard/api-keys  — API key management
/dashboard/settings  — Profile, PII mode, compliance frameworks, plan
/dashboard/logs      — Audit log viewer with date filter + CSV export
/api/auth/signup     — Server: create customer + users row
/api/logs/export     — Server: CSV download
```

Manual testing requires environment variables (`SUPABASE_*`, `APTLY_ADMIN_SECRET`) and the database migration to be applied.

## What's Next

- Apply the `users` migration to the Supabase project
- Set environment variables in Vercel for deployment
- Add the docs page about framework-specific entity detection (low priority)
- Compliance Policy Engine UI (next PRD)
