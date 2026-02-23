'use server'

import { requireAuth } from '@/lib/auth'
import { createAdminClient } from '@/lib/supabase/admin'
import { adminCreateAPIKey } from '@/lib/aptly-api'
import { revalidatePath } from 'next/cache'

export async function createKey(name: string): Promise<{ key: string; id: string }> {
  const { customerId } = await requireAuth()
  const created = await adminCreateAPIKey(customerId, name)
  revalidatePath('/dashboard/api-keys')
  return { key: created.key, id: created.id }
}

export async function revokeKey(keyId: string): Promise<void> {
  const { customerId } = await requireAuth()
  const admin = createAdminClient()

  // Verify key belongs to this customer before revoking
  const { data: key } = await admin
    .from('api_keys')
    .select('id, customer_id')
    .eq('id', keyId)
    .eq('customer_id', customerId)
    .single()

  if (!key) throw new Error('Key not found')

  await admin
    .from('api_keys')
    .update({ is_revoked: true, revoked_at: new Date().toISOString() })
    .eq('id', keyId)

  revalidatePath('/dashboard/api-keys')
}
