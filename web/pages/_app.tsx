import type { AppProps } from 'next/app'
import { MDXProvider } from '@mdx-js/react'
import '../styles/globals.css'
import * as customComponents from '../components'

const components = {
  ...customComponents,
}

export default function App({ Component, pageProps }: AppProps) {
  return (
    <MDXProvider components={components}>
      <Component {...pageProps} />
    </MDXProvider>
  )
}
