import { NextRequest, NextResponse } from 'next/server'
import { createAdminClient } from '@/lib/supabase/admin'
import { createClient } from '@/lib/supabase/server'
import { adminCreateCustomer } from '@/lib/aptly-api'

export async function POST(request: NextRequest) {
  const { supabaseUserId, email, company_name } = await request.json()

  if (!supabaseUserId || !email || !company_name) {
    return NextResponse.json({ error: 'Missing required fields' }, { status: 400 })
  }

  // Verify the caller owns the Supabase Auth user they claim
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user || user.id !== supabaseUserId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const admin = createAdminClient()

  try {
    // Create the Aptly customer
    const customer = await adminCreateCustomer({ email, company_name })

    // Create the users row linking auth user to customer (owner role)
    const { error: userError } = await admin.from('users').insert({
      supabase_auth_id: supabaseUserId,
      customer_id: customer.id,
      email,
      role: 'owner',
    })

    if (userError) {
      throw new Error(`Failed to create user record: ${userError.message}`)
    }

    return NextResponse.json({ customer_id: customer.id })
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Signup failed'
    return NextResponse.json({ error: message }, { status: 500 })
  }
}
