import { requireAuth } from '@/lib/auth'
import { createAdminClient } from '@/lib/supabase/admin'
import APIKeysClient from './api-keys-client'

export default async function APIKeysPage() {
  const { customerId } = await requireAuth()

  const admin = createAdminClient()
  const { data: keys } = await admin
    .from('api_keys')
    .select('id, key_prefix, name, is_revoked, created_at, last_used_at')
    .eq('customer_id', customerId)
    .order('created_at', { ascending: false })

  return (
    <div className="p-8">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white">API Keys</h1>
          <p className="text-gray-400 mt-1">
            Manage your API keys. Keys are used to authenticate requests to the Aptly API.
          </p>
        </div>
        <APIKeysClient initialKeys={keys ?? []} />
      </div>
    </div>
  )
}
