import React from 'react'

export default {
  logo: <span style={{ fontWeight: 700, fontSize: '1.25rem' }}>Aptly</span>,
  footer: {
    content: <span>© 2026 NSquared Labs</span>,
  },
  primaryHue: 210,
  sidebar: {
    defaultMenuCollapseLevel: 1,
  },
  toc: {
    backToTop: true,
  },
  search: {
    placeholder: 'Search documentation...',
  },
  head: (
    <>
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <meta property="og:title" content="Aptly Documentation" />
      <meta property="og:description" content="Compliance-as-a-Service for LLMs" />
    </>
  ),
}
