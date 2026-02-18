import Link from 'next/link'

export default function DocsLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="text-2xl font-bold text-gray-900">
              Aptly
            </Link>
            <nav className="flex gap-6">
              <Link href="/docs" className="text-gray-600 hover:text-gray-900">
                Documentation
              </Link>
              <a
                href="https://aptly-api.nsquaredlabs.com"
                className="text-gray-600 hover:text-gray-900"
                target="_blank"
                rel="noopener noreferrer"
              >
                API
              </a>
            </nav>
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-8">
          {/* Sidebar */}
          <aside className="w-64 flex-shrink-0">
            <nav className="space-y-1">
              <Link
                href="/docs"
                className="block px-3 py-2 text-sm font-medium text-gray-900 hover:bg-gray-100 rounded-md"
              >
                Introduction
              </Link>
              <Link
                href="/docs/quickstart"
                className="block px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-md"
              >
                Quickstart
              </Link>
              <Link
                href="/docs/authentication"
                className="block px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-md"
              >
                Authentication
              </Link>

              <div className="pt-4">
                <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  API Reference
                </div>
                <Link
                  href="/docs/api-reference/chat-completions"
                  className="block px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-md"
                >
                  Chat Completions
                </Link>
                <Link
                  href="/docs/api-reference/health"
                  className="block px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-md"
                >
                  Health Check
                </Link>

                <div className="pl-3 pt-2">
                  <div className="text-xs font-semibold text-gray-500 mb-1">Admin</div>
                  <Link href="/docs/api-reference/admin/create-customer" className="block px-3 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded-md">
                    Create Customer
                  </Link>
                  <Link href="/docs/api-reference/admin/list-customers" className="block px-3 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded-md">
                    List Customers
                  </Link>
                  <Link href="/docs/api-reference/admin/get-customer" className="block px-3 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded-md">
                    Get Customer
                  </Link>
                  <Link href="/docs/api-reference/admin/create-api-key" className="block px-3 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded-md">
                    Create API Key
                  </Link>
                </div>

                <div className="pl-3 pt-2">
                  <div className="text-xs font-semibold text-gray-500 mb-1">Customer</div>
                  <Link href="/docs/api-reference/customer/get-profile" className="block px-3 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded-md">
                    Get Profile
                  </Link>
                  <Link href="/docs/api-reference/customer/update-settings" className="block px-3 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded-md">
                    Update Settings
                  </Link>
                  <Link href="/docs/api-reference/customer/create-key" className="block px-3 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded-md">
                    Create Key
                  </Link>
                  <Link href="/docs/api-reference/customer/list-keys" className="block px-3 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded-md">
                    List Keys
                  </Link>
                  <Link href="/docs/api-reference/customer/revoke-key" className="block px-3 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded-md">
                    Revoke Key
                  </Link>
                </div>

                <div className="pl-3 pt-2">
                  <div className="text-xs font-semibold text-gray-500 mb-1">Audit Logs</div>
                  <Link href="/docs/api-reference/audit-logs/query-logs" className="block px-3 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded-md">
                    Query Logs
                  </Link>
                  <Link href="/docs/api-reference/audit-logs/get-log" className="block px-3 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded-md">
                    Get Log
                  </Link>
                </div>

                <div className="pl-3 pt-2">
                  <div className="text-xs font-semibold text-gray-500 mb-1">Analytics</div>
                  <Link href="/docs/api-reference/analytics/usage" className="block px-3 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded-md">
                    Usage
                  </Link>
                  <Link href="/docs/api-reference/analytics/models" className="block px-3 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded-md">
                    Models
                  </Link>
                  <Link href="/docs/api-reference/analytics/pii" className="block px-3 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded-md">
                    PII Detection
                  </Link>
                  <Link href="/docs/api-reference/analytics/users" className="block px-3 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded-md">
                    Users
                  </Link>
                  <Link href="/docs/api-reference/analytics/export" className="block px-3 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded-md">
                    Export
                  </Link>
                </div>
              </div>

              <div className="pt-4">
                <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Guides
                </div>
                <Link
                  href="/docs/guides/pii-redaction"
                  className="block px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-md"
                >
                  PII Redaction
                </Link>
                <Link
                  href="/docs/guides/streaming"
                  className="block px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-md"
                >
                  Streaming
                </Link>
                <Link
                  href="/docs/guides/rate-limiting"
                  className="block px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-md"
                >
                  Rate Limiting
                </Link>
                <Link
                  href="/docs/guides/compliance"
                  className="block px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-md"
                >
                  Compliance
                </Link>
              </div>

              <div className="pt-4">
                <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Deployment
                </div>
                <Link
                  href="/docs/deployment/architecture"
                  className="block px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-md"
                >
                  Architecture
                </Link>
                <Link
                  href="/docs/deployment/local-development"
                  className="block px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-md"
                >
                  Local Development
                </Link>
                <Link
                  href="/docs/deployment/production"
                  className="block px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-md"
                >
                  Production
                </Link>
              </div>

              <Link
                href="/docs/faq"
                className="block px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-md"
              >
                FAQ
              </Link>
              <Link
                href="/docs/changelog"
                className="block px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-md"
              >
                Changelog
              </Link>
            </nav>
          </aside>

          {/* Main docs content */}
          <main className="flex-1 max-w-4xl">
            <article className="prose max-w-none pb-16">
              {children}
            </article>
          </main>
        </div>
      </div>
    </div>
  )
}
