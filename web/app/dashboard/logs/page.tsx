import { requireAuth } from '@/lib/auth'
import { createAdminClient } from '@/lib/supabase/admin'
import LogsClient from './logs-client'

const PAGE_SIZE = 25

export default async function LogsPage({
  searchParams,
}: {
  searchParams: Promise<{ page?: string; start?: string; end?: string }>
}) {
  const { customerId } = await requireAuth()
  const params = await searchParams
  const page = parseInt(params.page ?? '1', 10)
  const offset = (page - 1) * PAGE_SIZE
  const start = params.start
  const end = params.end

  const admin = createAdminClient()

  let query = admin
    .from('audit_logs')
    .select(
      'id, provider, model, pii_detected, response_pii_detected, tokens_input, tokens_output, latency_ms, cost_usd, compliance_framework, user_id, request_data, response_data, created_at',
      { count: 'exact' }
    )
    .eq('customer_id', customerId)
    .order('created_at', { ascending: false })
    .range(offset, offset + PAGE_SIZE - 1)

  if (start) query = query.gte('created_at', new Date(start).toISOString())
  if (end) {
    const endDate = new Date(end)
    endDate.setHours(23, 59, 59, 999)
    query = query.lte('created_at', endDate.toISOString())
  }

  const { data: logs, count } = await query

  return (
    <div className="p-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">Audit Logs</h1>
            <p className="text-gray-400 mt-1">Immutable record of all LLM requests through Aptly</p>
          </div>
          <a
            href={`/api/logs/export?customer_id=${customerId}`}
            className="text-sm text-blue-400 hover:text-blue-300 border border-blue-400/30 px-4 py-2 rounded-lg hover:border-blue-400 transition-colors"
          >
            Export CSV
          </a>
        </div>
        <LogsClient
          logs={logs ?? []}
          total={count ?? 0}
          page={page}
          pageSize={PAGE_SIZE}
          startDate={start ?? ''}
          endDate={end ?? ''}
        />
      </div>
    </div>
  )
}
