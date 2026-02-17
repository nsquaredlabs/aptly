'use client'
import React, { useState, ReactElement } from 'react'

interface CodeGroupProps {
  children: React.ReactNode
}

export const CodeGroup: React.FC<CodeGroupProps> = ({ children }) => {
  const [activeTab, setActiveTab] = useState(0)
  const codeBlocks = React.Children.toArray(children) as ReactElement[]

  // Extract language from code block metadata
  const getTabLabel = (child: ReactElement, index: number): string => {
    if (child.props && child.props.className) {
      const match = child.props.className.match(/language-(\w+)/)
      if (match) {
        const lang = match[1]
        // Capitalize common languages nicely
        const labelMap: Record<string, string> = {
          bash: 'cURL',
          curl: 'cURL',
          python: 'Python',
          javascript: 'JavaScript',
          typescript: 'TypeScript',
          json: 'JSON',
          go: 'Go',
          java: 'Java',
          ruby: 'Ruby',
          php: 'PHP',
        }
        return labelMap[lang.toLowerCase()] || lang.toUpperCase()
      }
    }
    // Check for data-language attribute
    if (child.props && child.props['data-language']) {
      return child.props['data-language']
    }
    return `Tab ${index + 1}`
  }

  return (
    <div className="nx-mt-6 nx-mb-6">
      <div className="nx-flex nx-border-b nx-border-gray-200 dark:nx-border-gray-800">
        {codeBlocks.map((child, idx) => (
          <button
            key={idx}
            onClick={() => setActiveTab(idx)}
            className={`
              nx-px-4 nx-py-2 nx-text-sm nx-font-medium nx-transition-colors
              ${
                activeTab === idx
                  ? 'nx-text-blue-600 dark:nx-text-blue-400 nx-border-b-2 nx-border-blue-600 dark:nx-border-blue-400'
                  : 'nx-text-gray-600 dark:nx-text-gray-400 hover:nx-text-gray-900 dark:hover:nx-text-gray-200'
              }
            `}
          >
            {getTabLabel(child, idx)}
          </button>
        ))}
      </div>
      <div className="code-group-content">
        {codeBlocks[activeTab]}
      </div>
    </div>
  )
}
