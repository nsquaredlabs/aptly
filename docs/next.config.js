const withNextra = require('nextra')({
  theme: 'nextra-theme-docs',
  themeConfig: './theme.config.tsx',
  defaultShowCopyCode: true,
  mdxOptions: {
    remarkPlugins: [],
    rehypePlugins: [],
  },
})

module.exports = withNextra({
  basePath: '/docs',
  assetPrefix: '/docs',
  images: {
    unoptimized: true,
  },
  transpilePackages: ['nextra', 'nextra-theme-docs'],
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
