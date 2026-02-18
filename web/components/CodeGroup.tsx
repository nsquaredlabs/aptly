'use client'
import React, { useState, ReactElement, useEffect } from 'react'

interface CodeGroupProps {
  children: React.ReactNode
}

export const CodeGroup: React.FC<CodeGroupProps> = ({ children }) => {
  const [activeTab, setActiveTab] = useState(0)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

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

  // For SSR, render first tab only
  if (!mounted) {
    return (
      <div className="my-6 rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700">
        <div className="flex bg-gray-100 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
          {codeBlocks.map((child, idx) => (
            <div
              key={idx}
              className={`
                px-4 py-2 text-sm font-medium
                ${
                  idx === 0
                    ? 'text-blue-600 dark:text-blue-400 bg-white dark:bg-gray-900 border-b-2 border-blue-600 dark:border-blue-400'
                    : 'text-gray-600 dark:text-gray-400'
                }
              `}
            >
              {getTabLabel(child, idx)}
            </div>
          ))}
        </div>
        <div className="code-group-content bg-gray-900">
          {codeBlocks[0]}
        </div>
      </div>
    )
  }

  return (
    <div className="my-6 rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700">
      <div className="flex bg-gray-100 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        {codeBlocks.map((child, idx) => (
          <button
            key={idx}
            onClick={() => setActiveTab(idx)}
            className={`
              px-4 py-2 text-sm font-medium transition-colors
              ${
                activeTab === idx
                  ? 'text-blue-600 dark:text-blue-400 bg-white dark:bg-gray-900 border-b-2 border-blue-600 dark:border-blue-400'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
              }
            `}
          >
            {getTabLabel(child, idx)}
          </button>
        ))}
      </div>
      <div className="code-group-content bg-gray-900">
        {codeBlocks[activeTab]}
      </div>
    </div>
  )
}
