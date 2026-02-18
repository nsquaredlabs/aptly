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
              </div>
            </nav>
          </aside>

          {/* Main docs content */}
          <main className="flex-1 max-w-3xl">
            <article className="prose prose-gray max-w-none">
              {children}
            </article>
          </main>
        </div>
      </div>
    </div>
  )
}
