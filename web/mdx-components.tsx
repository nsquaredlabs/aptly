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
import { CodeBlock } from './components/CodeBlock'

export function useMDXComponents(components: Record<string, React.ComponentType<any>>) {
  return {
    ...components,
    pre: (props: any) => <CodeBlock {...props} />,
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
