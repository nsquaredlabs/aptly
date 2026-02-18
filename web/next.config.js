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
  images: {
    unoptimized: true,
  },
  transpilePackages: ['nextra', 'nextra-theme-docs'],
  output: 'standalone',
})
