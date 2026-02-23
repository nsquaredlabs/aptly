import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@/lib/supabase/server'
import { createAdminClient } from '@/lib/supabase/admin'

interface AuditLogRow {
  id: string
  created_at: string
  provider: string
  model: string
  pii_detected: unknown[]
  tokens_input: number | null
  tokens_output: number | null
  latency_ms: number | null
  compliance_framework: string | null
}

const CSV_HEADER = ['id', 'created_at', 'provider', 'model', 'pii_detected_count', 'tokens_input', 'tokens_output', 'latency_ms', 'compliance_framework']

export async function GET(_request: NextRequest) {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const admin = createAdminClient()
  const { data: userRow } = await admin
    .from('users')
    .select('customer_id')
    .eq('supabase_auth_id', user.id)
    .single()

  if (!userRow) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const { data: logs } = await admin
    .from('audit_logs')
    .select('id, provider, model, pii_detected, tokens_input, tokens_output, latency_ms, compliance_framework, created_at')
    .eq('customer_id', userRow.customer_id)
    .order('created_at', { ascending: false })
    .limit(10000)

  const rows = [
    CSV_HEADER,
    ...(logs ?? []).map((l: AuditLogRow) => [
      l.id,
      l.created_at,
      l.provider,
      l.model,
      Array.isArray(l.pii_detected) ? l.pii_detected.length : 0,
      l.tokens_input ?? '',
      l.tokens_output ?? '',
      l.latency_ms ?? '',
      l.compliance_framework ?? '',
    ]),
  ]

  const csv = rows.map((r) => r.join(',')).join('\n')

  return new NextResponse(csv, {
    headers: {
      'Content-Type': 'text/csv',
      'Content-Disposition': `attachment; filename="aptly-logs-${new Date().toISOString().slice(0, 10)}.csv"`,
    },
  })
}
