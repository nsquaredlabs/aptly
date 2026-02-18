const withNextra = require('nextra')({
  theme: 'nextra-theme-docs',
  themeConfig: './theme.config.tsx',
  defaultShowCopyCode: true,
})

module.exports = withNextra({
  images: {
    unoptimized: true,
  },
  transpilePackages: ['nextra', 'nextra-theme-docs'],
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  // Continue even if pages fail to export
  experimental: {
    fallbackNodePolyfills: false,
  },
})
