import React from 'react'
import { DocsThemeConfig } from 'nextra-theme-docs'

const config: DocsThemeConfig = {
  logo: <span style={{ fontWeight: 700, fontSize: '1.25rem' }}>Aptly</span>,
  project: {
    link: 'https://github.com/nsquaredlabs/aptly',
  },
  docsRepositoryBase: 'https://github.com/nsquaredlabs/aptly/tree/main/docs',
  footer: {
    text: '© 2026 NSquared Labs',
  },
  primaryHue: 210, // Blue color scheme
  darkMode: true,
  nextThemes: {
    defaultTheme: 'system',
  },
  sidebar: {
    defaultMenuCollapseLevel: 1,
    toggleButton: true,
  },
  toc: {
    backToTop: true,
  },
  search: {
    placeholder: 'Search documentation...',
  },
  useNextSeoProps() {
    return {
      titleTemplate: '%s – Aptly',
      defaultTitle: 'Aptly - Compliance-as-a-Service for LLMs',
      description: 'API middleware with automatic PII redaction and audit logging for AI applications',
      openGraph: {
        url: 'https://aptly.nsquaredlabs.com/docs',
        siteName: 'Aptly',
      },
    }
  },
  head: (
    <>
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <meta property="og:title" content="Aptly Documentation" />
      <meta property="og:description" content="Compliance-as-a-Service for LLMs" />
      <link rel="icon" href="/docs/favicon.svg" type="image/svg+xml" />
    </>
  ),
}

export default config
