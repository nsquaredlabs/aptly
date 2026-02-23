import { createClient } from '@/lib/supabase/server'
import { createAdminClient } from '@/lib/supabase/admin'
import { redirect } from 'next/navigation'

export interface UserContext {
  supabaseUserId: string
  customerId: string
  email: string
  role: string
}

/**
 * Get the current user's context from the session.
 * Redirects to /login if not authenticated.
 * Call from Server Components and Route Handlers only.
 */
export async function requireAuth(): Promise<UserContext> {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()

  if (!user) redirect('/login')

  const admin = createAdminClient()

  const { data: userRow, error } = await admin
    .from('users')
    .select('customer_id, role')
    .eq('supabase_auth_id', user.id)
    .single()

  if (error || !userRow) redirect('/login')

  return {
    supabaseUserId: user.id,
    customerId: userRow.customer_id,
    email: user.email ?? '',
    role: userRow.role,
  }
}
