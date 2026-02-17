# PRD: Custom MDX Documentation Solution

**Date:** 2026-02-17
**Status:** Implemented
**Spec Reference:** General MVP requirement for usability
**Implementation Date:** 2026-02-17

## Overview

Replace Mintlify with a custom, self-hosted MDX-based documentation site. Mintlify requires payment for continued hosting, and building our own solution gives us full control, zero hosting costs (using Vercel/Netlify free tier), and eliminates vendor lock-in.

## Context

### Current State
- **31 MDX files** in `/docs` directory with comprehensive documentation:
  - Getting Started (introduction, quickstart, authentication)
  - API Reference (health, chat-completions, admin, customer, audit-logs, analytics)
  - Guides (PII redaction, compliance, rate-limiting, streaming)
  - Deployment (architecture, production, local-development)
  - Resources (troubleshooting, FAQ, changelog)
- **Mintlify configuration** in `mint.json` with navigation structure, branding, colors
- **Well-structured content** following consistent patterns with code examples
- **Dependency**: Hosted on Mintlify's platform (requires payment)

### Gap Being Addressed
- Mintlify wants payment to continue hosting
- Vendor lock-in prevents full customization
- Limited control over performance and features
- Unnecessary cost for what is essentially static site hosting

This PRD addresses the need for a self-hosted, cost-free documentation solution while preserving all existing content.

## Requirements

### 1. Documentation Framework Selection
Choose a modern, MDX-compatible static site generator:
- **1.1** Must support MDX (existing content format)
- **1.2** Must support navigation structure similar to mint.json
- **1.3** Must be fast and SEO-friendly
- **1.4** Must have good documentation and community support
- **1.5** Recommended options:
  - **Next.js + Nextra** - Built for docs, excellent MDX support, similar to Mintlify
  - **Docusaurus** - Meta's doc platform, mature and feature-rich
  - **Astro + Starlight** - Modern, fast, great DX

### 2. Preserve Existing Content
All 31 MDX files must work with minimal changes:
- **2.1** Maintain existing frontmatter (title, description)
- **2.2** Support existing MDX components (CardGroup, Card, CodeGroup, ResponseExample, etc.)
- **2.3** Preserve code syntax highlighting (bash, python, json, etc.)
- **2.4** Keep all code examples and formatting
- **2.5** Maintain internal links between docs

### 3. Navigation Structure
Replicate the mint.json navigation in the new framework:
- **3.1** Navigation groups: Getting Started, API Reference, Guides, Deployment, Resources
- **3.2** Nested navigation for API sections (Admin, Customer, Audit Logs, Analytics)
- **3.3** Sidebar with collapsible sections
- **3.4** Active page highlighting
- **3.5** Search functionality (full-text search across all docs)

### 4. Branding and Styling
Match current design with customization:
- **4.1** Use existing color scheme (primary: #3b82f6, light: #60a5fa, dark: #2563eb)
- **4.2** Support logo/favicon (placeholder SVGs exist in `/docs/logo/`)
- **4.3** Dark mode support (toggle between light/dark themes)
- **4.4** Responsive design (mobile, tablet, desktop)
- **4.5** Professional typography (similar to Mintlify's aesthetic)

### 5. Component Library
Create custom MDX components to match Mintlify syntax:
- **5.1** `<CardGroup>` and `<Card>` - Feature cards with icons
- **5.2** `<CodeGroup>` - Tabbed code examples (curl, Python, etc.)
- **5.3** `<ResponseExample>` - API response examples
- **5.4** Callout components (Note, Warning, Tip, Info boxes)
- **5.5** Mermaid diagram support (for architecture diagrams)

### 6. Deployment and Hosting
Deploy to Vercel with custom domain configuration:
- **6.1** Deploy to Vercel free tier
- **6.2** Automatic deployments from GitHub main branch
- **6.3** Configure custom domain: `aptly.nsquaredlabs.com`
- **6.4** Docs accessible at: `https://aptly.nsquaredlabs.com/docs`
- **6.5** Root redirect: `https://aptly.nsquaredlabs.com` → `https://aptly.nsquaredlabs.com/docs`
- **6.6** HTTPS enabled by default
- **6.7** Fast global CDN distribution
- **6.8** Build time <2 minutes for CI/CD

**Note**: This will be the first content on the main Aptly website. The docs site serves as both the website and documentation until other pages are added.

### 7. Developer Experience
Make docs easy to maintain:
- **7.1** Local development server with hot reload
- **7.2** TypeScript for type safety in components
- **7.3** ESLint and Prettier for code quality
- **7.4** Clear README for contributing to docs
- **7.5** Simple commands: `npm run dev`, `npm run build`, `npm run deploy`

## Technical Approach

### Recommended Stack: Next.js + Nextra

**Why Nextra:**
- Built specifically for documentation sites
- Excellent MDX support out of the box
- Similar to Mintlify (easiest migration path)
- Great performance (static generation)
- Strong community and maintained by Vercel

### Project Structure
```
aptly/
├── docs/                           # NEW: Next.js docs app
│   ├── pages/                      # MDX files (migrated from current /docs)
│   │   ├── _app.tsx               # App wrapper
│   │   ├── index.mdx              # Home (introduction)
│   │   ├── quickstart.mdx
│   │   ├── authentication.mdx
│   │   ├── api/
│   │   │   ├── health.mdx
│   │   │   ├── chat-completions.mdx
│   │   │   ├── admin/
│   │   │   ├── customer/
│   │   │   ├── audit-logs/
│   │   │   └── analytics/
│   │   ├── guides/
│   │   ├── deployment/
│   │   ├── troubleshooting.mdx
│   │   ├── faq.mdx
│   │   └── changelog.mdx
│   ├── components/                # Custom MDX components
│   │   ├── Card.tsx
│   │   ├── CardGroup.tsx
│   │   ├── CodeGroup.tsx
│   │   ├── ResponseExample.tsx
│   │   └── Callout.tsx
│   ├── theme.config.tsx           # Nextra theme config
│   ├── public/                    # Static assets
│   │   ├── logo/
│   │   └── favicon.svg
│   ├── styles/
│   │   └── globals.css
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.js
│   └── README.md
├── src/                           # Existing API code (unchanged)
├── tests/                         # Existing tests (unchanged)
└── README.md                      # Project README (unchanged)
```

### Next.js Configuration (next.config.js)
```js
const withNextra = require('nextra')({
  theme: 'nextra-theme-docs',
  themeConfig: './theme.config.tsx',
})

module.exports = withNextra({
  basePath: '/docs',
  assetPrefix: '/docs',
  images: {
    unoptimized: true, // For static export if needed
  },
  // Redirect root to /docs
  async redirects() {
    return [
      {
        source: '/',
        destination: '/docs',
        basePath: false,
        permanent: false,
      },
    ]
  },
})
```

### Nextra Configuration (theme.config.tsx)
```tsx
import { DocsThemeConfig } from 'nextra-theme-docs'

const config: DocsThemeConfig = {
  logo: <span>Aptly</span>,
  project: {
    link: 'https://github.com/your-org/aptly',
  },
  docsRepositoryBase: 'https://github.com/your-org/aptly/tree/main/docs',
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
}

export default config
```

### Vercel Configuration (vercel.json)
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs",
  "regions": ["iad1"],
  "redirects": [
    {
      "source": "/",
      "destination": "/docs"
    }
  ]
}
```

**DNS Configuration:**
- Point `aptly.nsquaredlabs.com` A record to Vercel's IP or CNAME to Vercel
- Docs will be accessible at `https://aptly.nsquaredlabs.com/docs`
- Root `https://aptly.nsquaredlabs.com` redirects to `/docs`

### Custom Component Examples

**CardGroup.tsx:**
```tsx
import React from 'react'

export const CardGroup = ({
  children,
  cols = 2
}: {
  children: React.ReactNode
  cols?: number
}) => {
  return (
    <div className={`grid gap-4 grid-cols-1 md:grid-cols-${cols} my-6`}>
      {children}
    </div>
  )
}
```

**Card.tsx:**
```tsx
import React from 'react'

export const Card = ({
  title,
  icon,
  children
}: {
  title: string
  icon?: string
  children?: React.ReactNode
}) => {
  return (
    <div className="border rounded-lg p-4 hover:shadow-md transition">
      {icon && <span className="text-2xl mb-2 block">{icon}</span>}
      <h3 className="font-semibold mb-2">{title}</h3>
      {children && <p className="text-sm text-gray-600 dark:text-gray-400">{children}</p>}
    </div>
  )
}
```

**CodeGroup.tsx:**
```tsx
'use client'
import React, { useState } from 'react'

export const CodeGroup = ({ children }: { children: React.ReactNode }) => {
  const [activeTab, setActiveTab] = useState(0)
  const codeBlocks = React.Children.toArray(children)

  return (
    <div className="code-group my-4">
      <div className="flex border-b">
        {codeBlocks.map((child: any, idx) => (
          <button
            key={idx}
            onClick={() => setActiveTab(idx)}
            className={`px-4 py-2 ${activeTab === idx ? 'border-b-2 border-blue-500' : ''}`}
          >
            {child.props.className?.split('-')[0] || `Tab ${idx + 1}`}
          </button>
        ))}
      </div>
      <div className="code-content">
        {codeBlocks[activeTab]}
      </div>
    </div>
  )
}
```

### Migration Script
Create a script to automate migration:
```bash
#!/bin/bash
# migrate-docs.sh

# 1. Create new docs directory structure
mkdir -p docs/{pages,components,public,styles}

# 2. Copy MDX files from old /docs to /docs/pages
# (Manual review required to ensure frontmatter compatibility)

# 3. Copy logo and favicon
cp -r docs-old/logo docs-old/favicon.svg docs/public/

# 4. Generate _meta.json files for Nextra navigation
# (Based on mint.json structure)

echo "Migration complete! Review files and test locally."
```

### Navigation Mapping (mint.json → Nextra)
Nextra uses `_meta.json` files for navigation:

```json
// pages/_meta.json
{
  "index": "Introduction",
  "quickstart": "Quickstart",
  "authentication": "Authentication",
  "api": "API Reference",
  "guides": "Guides",
  "deployment": "Deployment",
  "troubleshooting": "Troubleshooting",
  "faq": "FAQ",
  "changelog": "Changelog"
}

// pages/api/_meta.json
{
  "health": "Health Check",
  "chat-completions": "Chat Completions",
  "admin": "Admin",
  "customer": "Your Account",
  "audit-logs": "Audit Logs",
  "analytics": "Analytics"
}
```

## Files to Create/Modify

### New Files
- `docs/package.json` - Dependencies (Next.js, Nextra, React, etc.)
- `docs/theme.config.tsx` - Nextra theme configuration
- `docs/next.config.js` - Next.js config with Nextra plugin and basePath
- `docs/tsconfig.json` - TypeScript configuration
- `docs/components/*.tsx` - Custom MDX components (Card, CodeGroup, etc.)
- `docs/pages/_app.tsx` - App wrapper
- `docs/pages/_meta.json` - Navigation structure (per directory)
- `docs/styles/globals.css` - Custom styles
- `docs/README.md` - Documentation setup guide
- `docs/.gitignore` - Ignore node_modules, .next, etc.
- `docs/vercel.json` - Vercel deployment config with custom domain

### Modified Files
- All 31 MDX files in `/docs` → Move to `docs/pages/` with minimal changes
- Update component syntax if needed (most should work as-is)
- Update internal links to use Nextra conventions
- Update API base URLs in examples and references:
  - API endpoints: `https://aptly-api.nsquaredlabs.com`
  - Documentation: `https://aptly.nsquaredlabs.com/docs`
  - Website: `https://aptly.nsquaredlabs.com`

### Files to Archive
- `docs/mint.json` - Archive for reference (no longer needed)
- Mintlify-specific configurations

## Dependencies

```json
{
  "name": "aptly-docs",
  "version": "1.0.0",
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "^14.0.0",
    "nextra": "^2.13.0",
    "nextra-theme-docs": "^2.13.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/react": "^18.2.0",
    "typescript": "^5.0.0",
    "eslint": "^8.0.0",
    "eslint-config-next": "^14.0.0"
  }
}
```

## Testing Strategy

### Documentation Quality Checks
- **Local Preview**: Run `npm run dev` and manually verify all pages
- **Link Validation**: Check all internal links work correctly
- **Component Testing**: Verify Card, CodeGroup, ResponseExample render correctly
- **Code Examples**: Ensure syntax highlighting works for bash, python, json
- **Dark Mode**: Test light/dark theme switching
- **Mobile Responsive**: Test on mobile, tablet, desktop viewports
- **Search**: Verify search functionality works across all docs

### Build and Deploy Testing
- **Build Success**: `npm run build` completes without errors
- **Production Build**: Test production build locally with `npm run start`
- **Vercel Deploy**: Test deployment to Vercel preview environment
- **Performance**: Check Lighthouse scores (should be >90 for all metrics)
- **SEO**: Verify meta tags, sitemap generation

### Verification Checklist
- [ ] All 31 MDX files render correctly
- [ ] Navigation matches original mint.json structure
- [ ] Custom components (Card, CodeGroup) work as expected
- [ ] Code syntax highlighting works for all languages
- [ ] Search finds relevant docs
- [ ] Dark mode toggle works
- [ ] Mobile layout is responsive
- [ ] Deployed to Vercel/Netlify successfully
- [ ] Custom domain configured (if applicable)
- [ ] Build time <2 minutes

## Migration Steps

### Phase 1: Setup (Day 1)
1. Create `docs/` directory for Next.js app
2. Install dependencies (Next.js, Nextra, React)
3. Configure Nextra theme with branding
4. Create basic project structure

### Phase 2: Component Development (Day 1-2)
1. Build Card and CardGroup components
2. Build CodeGroup component with tabs
3. Build ResponseExample component
4. Build Callout components (Note, Warning, Tip)
5. Test components in isolation

### Phase 3: Content Migration (Day 2-3)
1. Copy MDX files to `pages/` directory
2. Create `_meta.json` files for navigation
3. Update component syntax if needed
4. **Update all API base URLs** in MDX files:
   - Find/replace `https://api.aptly.dev` → `https://aptly-api.nsquaredlabs.com`
   - Find/replace `http://localhost:8000` → `https://aptly-api.nsquaredlabs.com` (in production examples)
   - Keep localhost examples for local development sections
5. Verify all code examples render correctly
6. Test internal links

### Phase 4: Testing and Polish (Day 3)
1. Run local preview and fix issues
2. Test dark mode and responsive design
3. Verify search functionality
4. Check build performance
5. Run Lighthouse audit

### Phase 5: Deployment (Day 3-4)
1. Set up Vercel project linked to GitHub repo
2. Configure automatic deployments from main branch
3. Test preview deployment with basePath: '/docs'
4. Configure custom domain: `aptly.nsquaredlabs.com`
5. Set up DNS A/CNAME records pointing to Vercel
6. Verify redirect: `https://aptly.nsquaredlabs.com` → `https://aptly.nsquaredlabs.com/docs`
7. Deploy to production
8. Update README and CLAUDE.md with live docs URL
9. Test all links and API references point to `https://aptly-api.nsquaredlabs.com`

## Out of Scope

- **Video tutorials** - Text documentation only
- **Interactive API playground** - Not needed for MVP
- **Multi-language support** - English only
- **Versioned docs** - Single version for now
- **Analytics tracking** - Can add later if needed
- **Comments or feedback system** - Not needed initially
- **PDF export** - Not required for web docs

## Success Criteria

- [ ] All 31 existing MDX files work in new system
- [ ] Navigation structure matches Mintlify exactly
- [ ] Custom components render identically to Mintlify
- [ ] Dark mode works correctly
- [ ] Search finds relevant documentation
- [ ] Deployed to Vercel free tier
- [ ] Build time <2 minutes
- [ ] Lighthouse score >90 for performance, accessibility, SEO
- [ ] Custom domain configured: `https://aptly.nsquaredlabs.com`
- [ ] Docs accessible at: `https://aptly.nsquaredlabs.com/docs`
- [ ] Root redirect works: `https://aptly.nsquaredlabs.com` → `https://aptly.nsquaredlabs.com/docs`
- [ ] Zero ongoing costs (free tier hosting)
- [ ] Local development works: `npm run dev`
- [ ] API references point to correct base URL: `https://aptly-api.nsquaredlabs.com`

## Cost Comparison

### Current (Mintlify)
- **Hosting**: $120-300/year (or whatever they're charging)
- **Vendor lock-in**: Yes
- **Customization**: Limited

### Proposed (Next.js + Nextra + Vercel)
- **Hosting**: $0/year (Vercel free tier)
- **Vendor lock-in**: No (can deploy anywhere)
- **Customization**: Full control
- **Build time**: <2 minutes
- **Performance**: Likely faster (static generation)

## Notes

### Why Nextra over Docusaurus
- **Similarity to Mintlify**: Nextra is very similar to Mintlify, easier migration
- **Modern stack**: React 18, Next.js 14, latest features
- **Performance**: Excellent static generation and performance
- **Vercel integration**: Seamless deployment to Vercel
- **MDX support**: First-class MDX support out of the box

### Alternative: Astro + Starlight
If Nextra doesn't work out:
- **Astro Starlight**: Another excellent docs framework
- **Faster builds**: Astro is generally faster than Next.js
- **Less JavaScript**: Ships less JS to the browser
- **Similar features**: Navigation, search, dark mode, MDX support

### Rollback Plan
If migration fails:
- Keep existing Mintlify setup temporarily
- Pay for another month while fixing issues
- All content is already in MDX, so no lock-in
- Can try alternative framework (Docusaurus, Starlight)
