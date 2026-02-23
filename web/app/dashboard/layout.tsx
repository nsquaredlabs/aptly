import { requireAuth } from '@/lib/auth'
import { createAdminClient } from '@/lib/supabase/admin'
import Sidebar from '@/components/dashboard/sidebar'

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { customerId } = await requireAuth()

  const admin = createAdminClient()
  const { data: customer } = await admin
    .from('customers')
    .select('company_name')
    .eq('id', customerId)
    .single()

  return (
    <div className="flex h-screen bg-gray-950 overflow-hidden">
      <Sidebar companyName={customer?.company_name ?? null} />
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  )
}
