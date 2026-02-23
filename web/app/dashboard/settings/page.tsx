import { requireAuth } from '@/lib/auth'
import { createAdminClient } from '@/lib/supabase/admin'
import SettingsClient from './settings-client'

const PLAN_LIMITS = {
  free: { requests_per_month: 1000, rate_per_hour: 100 },
  pro: { requests_per_month: 50000, rate_per_hour: 1000 },
  enterprise: { requests_per_month: null, rate_per_hour: 10000 },
}

export default async function SettingsPage() {
  const { customerId, email } = await requireAuth()

  const admin = createAdminClient()
  const { data: customer } = await admin
    .from('customers')
    .select('*')
    .eq('id', customerId)
    .single()

  // Get this month's usage
  const monthStart = new Date()
  monthStart.setDate(1)
  monthStart.setHours(0, 0, 0, 0)

  const { count: requestsThisMonth } = await admin
    .from('audit_logs')
    .select('id', { count: 'exact', head: true })
    .eq('customer_id', customerId)
    .gte('created_at', monthStart.toISOString())

  const plan = (customer?.plan ?? 'free') as keyof typeof PLAN_LIMITS
  const limits = PLAN_LIMITS[plan]

  return (
    <div className="p-8">
      <div className="max-w-2xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white">Settings</h1>
        </div>
        <SettingsClient
          customer={customer}
          email={email}
          customerId={customerId}
          requestsThisMonth={requestsThisMonth ?? 0}
          planLimits={limits}
        />
      </div>
    </div>
  )
}
