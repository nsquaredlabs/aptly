import { useMDXComponents as getThemeComponents } from 'nextra-theme-docs'
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

export function useMDXComponents(components) {
  return {
    ...getThemeComponents(),
    ...components,
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
}
