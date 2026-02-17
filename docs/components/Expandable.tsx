'use client'
import React, { useState } from 'react'

interface ExpandableProps {
  title: string
  children: React.ReactNode
  defaultOpen?: boolean
}

export const Expandable: React.FC<ExpandableProps> = ({
  title,
  children,
  defaultOpen = false,
}) => {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  return (
    <div className="nx-my-3 nx-border nx-border-gray-200 dark:nx-border-gray-800 nx-rounded">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="nx-w-full nx-flex nx-items-center nx-justify-between nx-p-3 nx-text-left hover:nx-bg-gray-50 dark:hover:nx-bg-gray-900 nx-transition-colors"
      >
        <span className="nx-text-sm nx-font-medium">{title}</span>
        <svg
          className={`nx-w-4 nx-h-4 nx-transition-transform ${
            isOpen ? 'nx-rotate-180' : ''
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>
      {isOpen && (
        <div className="nx-px-3 nx-pb-3 nx-border-t nx-border-gray-200 dark:nx-border-gray-800">
          {children}
        </div>
      )}
    </div>
  )
}
