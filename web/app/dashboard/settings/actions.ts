'use server'

import { requireAuth } from '@/lib/auth'
import { createAdminClient } from '@/lib/supabase/admin'
import { revalidatePath } from 'next/cache'

export async function updateSettings(data: {
  company_name?: string
  pii_redaction_mode?: 'mask' | 'hash' | 'remove'
  compliance_frameworks?: string[]
}): Promise<void> {
  const { customerId } = await requireAuth()
  const admin = createAdminClient()

  const { error } = await admin
    .from('customers')
    .update({ ...data, updated_at: new Date().toISOString() })
    .eq('id', customerId)

  if (error) throw new Error(`Failed to update settings: ${error.message}`)

  revalidatePath('/dashboard/settings')
  revalidatePath('/dashboard')
}
