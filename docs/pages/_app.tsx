import type { AppProps } from 'next/app'
import { MDXProvider } from '@mdx-js/react'
import {
  Card,
  CardGroup,
  CodeGroup,
  ResponseExample,
  Callout,
  Note,
  Warning,
  Info,
  Error,
  Success,
  ParamField,
  Accordion,
  AccordionGroup,
  Check,
  Tip,
  ResponseField,
  Expandable,
} from '../components'
import '../styles/globals.css'

const components = {
  Card,
  CardGroup,
  CodeGroup,
  ResponseExample,
  Callout,
  Note,
  Warning,
  Info,
  Error,
  Success,
  ParamField,
  Accordion,
  AccordionGroup,
  Check,
  Tip,
  ResponseField,
  Expandable,
}

export default function App({ Component, pageProps }: AppProps) {
  return (
    <MDXProvider components={components}>
      <Component {...pageProps} />
    </MDXProvider>
  )
}
