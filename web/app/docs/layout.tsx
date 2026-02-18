import { Footer, Layout, Navbar } from 'nextra-theme-docs'
import { Banner, Head } from 'nextra/components'
import { getPageMap } from 'nextra/page-map'

export default async function DocsLayout({ children }: { children: React.ReactNode }) {
  const pageMap = await getPageMap()

  return (
    <Layout
      pageMap={pageMap}
      banner={<Banner dismissible={false}>Aptly API Documentation</Banner>}
      navbar={<Navbar logo={<span style={{ fontWeight: 700, fontSize: '1.25rem' }}>Aptly</span>} />}
      footer={<Footer>© 2026 NSquared Labs</Footer>}
    >
      <Head />
      {children}
    </Layout>
  )
}
