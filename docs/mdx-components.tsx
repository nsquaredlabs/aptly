import type { MDXComponents } from 'mdx/types'
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
} from './components'

export function useMDXComponents(components: MDXComponents): MDXComponents {
  return {
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
    ...components,
  }
}
