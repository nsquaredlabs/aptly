'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'

const NAV = [
  { href: '/dashboard', label: 'Dashboard', icon: '▦' },
  { href: '/dashboard/api-keys', label: 'API Keys', icon: '⚷' },
  { href: '/dashboard/settings', label: 'Settings', icon: '⚙' },
  { href: '/dashboard/logs', label: 'Logs', icon: '≡' },
]

interface SidebarProps {
  companyName: string | null
}

export default function Sidebar({ companyName }: SidebarProps) {
  const pathname = usePathname()
  const router = useRouter()

  async function handleLogout() {
    const supabase = createClient()
    await supabase.auth.signOut()
    router.push('/login')
    router.refresh()
  }

  return (
    <aside className="w-56 bg-gray-900 border-r border-gray-800 flex flex-col h-full">
      <div className="px-5 py-5 border-b border-gray-800">
        <span className="text-white font-semibold text-lg">Aptly</span>
      </div>

      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {NAV.map(({ href, label, icon }) => {
          const active = pathname === href || (href !== '/dashboard' && pathname.startsWith(href))
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                active
                  ? 'bg-blue-600/20 text-blue-400'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
              }`}
            >
              <span className="text-base leading-none">{icon}</span>
              {label}
            </Link>
          )
        })}
      </nav>

      <div className="px-4 py-4 border-t border-gray-800 space-y-3">
        {companyName && (
          <p className="text-xs text-gray-500 truncate">{companyName}</p>
        )}
        <button
          onClick={handleLogout}
          className="w-full text-left text-sm text-gray-500 hover:text-gray-300 transition-colors"
        >
          Logout
        </button>
      </div>
    </aside>
  )
}
