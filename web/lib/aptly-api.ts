/**
 * Aptly admin API client for server-side dashboard operations.
 *
 * The dashboard authenticates via Supabase Auth sessions. All data reads
 * go through the Supabase service role client (see lib/supabase/admin.ts).
 * Only API key creation needs to go through the Aptly admin API, because
 * the raw key is only returned at creation time.
 */

const APTLY_API_URL = process.env.APTLY_API_URL ?? 'https://aptly-api.nsquaredlabs.com'
const APTLY_ADMIN_SECRET = process.env.APTLY_ADMIN_SECRET!

// ---- Types ----------------------------------------------------------------

export interface Customer {
  id: string
  email: string
  company_name: string | null
  plan: 'free' | 'pro' | 'enterprise'
  compliance_frameworks: string[]
  pii_redaction_mode: 'mask' | 'hash' | 'remove'
  retention_days: number
  created_at: string
  updated_at: string
}

export interface APIKeyCreated {
  id: string
  key: string // raw key — only returned on creation
  key_prefix: string
  name: string | null
  rate_limit_per_hour: number
  created_at: string
}

// ---- Admin API calls (X-Admin-Secret auth) --------------------------------

export async function adminCreateCustomer(data: {
  email: string
  company_name: string
}): Promise<Customer> {
  const res = await fetch(`${APTLY_API_URL}/v1/admin/customers`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Admin-Secret': APTLY_ADMIN_SECRET,
    },
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const err = await res.text()
    throw new Error(`Failed to create customer: ${err}`)
  }
  return res.json()
}

export async function adminCreateAPIKey(
  customerId: string,
  name: string
): Promise<APIKeyCreated> {
  const res = await fetch(`${APTLY_API_URL}/v1/admin/customers/${customerId}/api-keys`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Admin-Secret': APTLY_ADMIN_SECRET,
    },
    body: JSON.stringify({ name }),
  })
  if (!res.ok) {
    const err = await res.text()
    throw new Error(`Failed to create API key: ${err}`)
  }
  return res.json()
}
