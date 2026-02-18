import Link from 'next/link'

export default function DocsLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-white dark:bg-black">
      {/* Header */}
      <header className="border-b border-gray-200 dark:border-gray-800">
        <nav className="container mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <span className="text-blue-600 dark:text-blue-400 text-xl">$</span>
            <span className="text-xl font-mono font-bold text-gray-900 dark:text-white">aptly</span>
          </Link>
          <div className="flex gap-6 font-mono text-sm">
            <Link
              href="/docs"
              className="text-gray-600 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 transition-colors"
            >
              ./docs
            </Link>
            <Link
              href="/api-reference"
              className="text-gray-600 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 transition-colors"
            >
              ./api
            </Link>
          </div>
        </nav>
      </header>

      {/* Sidebar + Content */}
      <div className="container mx-auto px-6 py-8">
        <div className="flex gap-12">
          {/* Sidebar */}
          <aside className="w-48 flex-shrink-0">
            <nav className="sticky top-8 space-y-1 font-mono text-sm">
              <Link
                href="/docs"
                className="block px-3 py-2 text-gray-600 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 hover:bg-gray-50 dark:hover:bg-gray-950 transition-colors"
              >
                Introduction
              </Link>
              <Link
                href="/docs/quickstart"
                className="block px-3 py-2 text-gray-600 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 hover:bg-gray-50 dark:hover:bg-gray-950 transition-colors"
              >
                Quickstart
              </Link>
              <Link
                href="/docs/concepts"
                className="block px-3 py-2 text-gray-600 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 hover:bg-gray-50 dark:hover:bg-gray-950 transition-colors"
              >
                Key Concepts
              </Link>
              <Link
                href="/docs/guides"
                className="block px-3 py-2 text-gray-600 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 hover:bg-gray-50 dark:hover:bg-gray-950 transition-colors"
              >
                Common Patterns
              </Link>
              <Link
                href="/docs/faq"
                className="block px-3 py-2 text-gray-600 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 hover:bg-gray-50 dark:hover:bg-gray-950 transition-colors"
              >
                FAQ
              </Link>
              <div className="border-t border-gray-200 dark:border-gray-800 my-4" />
              <Link
                href="/api-reference"
                className="block px-3 py-2 text-blue-600 dark:text-blue-400 hover:bg-gray-50 dark:hover:bg-gray-950 transition-colors"
              >
                API Reference →
              </Link>
            </nav>
          </aside>

          {/* Content */}
          <main className="flex-1 max-w-3xl">
            {children}
          </main>
        </div>
      </div>
    </div>
  )
}
