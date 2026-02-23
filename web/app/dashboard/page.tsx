import { requireAuth } from '@/lib/auth'
import { createAdminClient } from '@/lib/supabase/admin'

interface PiiRow {
  pii_detected: unknown[]
}

interface AuditLog {
  id: string
  model: string
  provider: string
  pii_detected: unknown[]
  created_at: string
  compliance_framework: string | null
}

function countPiiEntities(rows: PiiRow[]): number {
  return rows.reduce(
    (sum, row) => sum + (Array.isArray(row.pii_detected) ? row.pii_detected.length : 0),
    0
  )
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
      <p className="text-gray-500 text-sm">{label}</p>
      <p className="text-2xl font-bold text-white mt-1">{value.toLocaleString()}</p>
    </div>
  )
}

export default async function DashboardPage() {
  const { customerId } = await requireAuth()
  const admin = createAdminClient()

  // This month stats
  const monthStart = new Date()
  monthStart.setDate(1)
  monthStart.setHours(0, 0, 0, 0)

  // Today stats
  const todayStart = new Date()
  todayStart.setHours(0, 0, 0, 0)

  const [
    { count: totalRequests },
    { count: requestsToday },
    { data: recentLogs },
    { count: activeKeyCount },
    { data: piiLogs },
    { data: piiToday },
  ] = await Promise.all([
    admin.from('audit_logs').select('id', { count: 'exact', head: true })
      .eq('customer_id', customerId)
      .gte('created_at', monthStart.toISOString()),
    admin.from('audit_logs').select('id', { count: 'exact', head: true })
      .eq('customer_id', customerId)
      .gte('created_at', todayStart.toISOString()),
    admin.from('audit_logs').select('id, model, provider, pii_detected, created_at, compliance_framework')
      .eq('customer_id', customerId)
      .order('created_at', { ascending: false })
      .limit(5),
    admin.from('api_keys').select('id', { count: 'exact', head: true })
      .eq('customer_id', customerId)
      .eq('is_revoked', false),
    admin.from('audit_logs').select('pii_detected')
      .eq('customer_id', customerId)
      .gte('created_at', monthStart.toISOString()),
    admin.from('audit_logs').select('pii_detected')
      .eq('customer_id', customerId)
      .gte('created_at', todayStart.toISOString()),
  ])

  const piiDetectionsMonth = countPiiEntities(piiLogs ?? [])
  const piiDetectionsToday = countPiiEntities(piiToday ?? [])

  return (
    <div className="p-8">
      <div className="max-w-5xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-gray-400 mt-1">This month&apos;s activity</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard label="Requests this month" value={totalRequests ?? 0} />
          <StatCard label="PII detections this month" value={piiDetectionsMonth} />
          <StatCard label="Requests today" value={requestsToday ?? 0} />
          <StatCard label="Active API keys" value={activeKeyCount ?? 0} />
        </div>

        {/* Recent activity */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-800 flex items-center justify-between">
            <h2 className="text-white font-medium">Recent activity</h2>
            <a href="/dashboard/logs" className="text-blue-400 text-sm hover:text-blue-300">
              View all →
            </a>
          </div>
          {!recentLogs || recentLogs.length === 0 ? (
            <div className="px-5 py-10 text-center text-gray-500 text-sm">
              No requests yet. Make your first API call to see activity here.
            </div>
          ) : (
            <div className="divide-y divide-gray-800">
              {recentLogs.map((log: AuditLog) => (
                <div key={log.id} className="px-5 py-4 flex items-center gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-gray-300 text-sm font-mono">{log.model}</span>
                      {log.compliance_framework && (
                        <span className="text-xs text-blue-400 bg-blue-400/10 px-1.5 py-0.5 rounded">
                          {log.compliance_framework}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-600 mt-0.5">
                      {new Date(log.created_at).toLocaleString()}
                    </p>
                  </div>
                  {Array.isArray(log.pii_detected) && log.pii_detected.length > 0 ? (
                    <span className="text-xs text-amber-400 bg-amber-400/10 px-2 py-1 rounded">
                      {log.pii_detected.length} PII detected
                    </span>
                  ) : (
                    <span className="text-xs text-gray-600 bg-gray-800 px-2 py-1 rounded">
                      No PII
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* PII today callout */}
        {piiDetectionsToday > 0 && (
          <div className="mt-4 bg-amber-900/20 border border-amber-700/50 rounded-xl px-5 py-4">
            <p className="text-amber-300 text-sm">
              <span className="font-medium">{piiDetectionsToday} PII entities</span> detected and redacted today.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
