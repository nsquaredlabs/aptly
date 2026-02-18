import './global.css'
import type { ReactNode } from 'react'

export const metadata = {
  title: 'Aptly - Compliance-as-a-Service for LLMs',
  description: 'API middleware with automatic PII redaction and audit logging for AI applications',
}

export default function RootLayout({
  children,
}: {
  children: ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
      </head>
      <body>{children}</body>
    </html>
  )
}
