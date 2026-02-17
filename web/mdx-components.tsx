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

const mdxComponents = {
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

export function useMDXComponents(components: any) {
  return { ...mdxComponents, ...components }
}

export default mdxComponents
