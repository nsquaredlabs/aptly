'use client'
import React, { useState, ReactNode, useEffect } from 'react'

interface AccordionProps {
  title: string
  children: ReactNode
  defaultOpen?: boolean
}

export const Accordion: React.FC<AccordionProps> = ({ title, children, defaultOpen = false }) => {
  const [isOpen, setIsOpen] = useState(defaultOpen)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  // For SSR, render in default state
  if (!mounted) {
    return (
      <div className="nx-border nx-border-gray-200 dark:nx-border-gray-800 nx-rounded-lg nx-mb-2">
        <div className="nx-w-full nx-flex nx-items-center nx-justify-between nx-p-4 nx-text-left">
          <span className="nx-font-semibold">{title}</span>
          <svg
            className={`nx-w-5 nx-h-5 ${defaultOpen ? 'nx-rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
        {defaultOpen && (
          <div className="nx-px-4 nx-pb-4 nx-border-t nx-border-gray-200 dark:nx-border-gray-800">
            {children}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="nx-border nx-border-gray-200 dark:nx-border-gray-800 nx-rounded-lg nx-mb-2">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="nx-w-full nx-flex nx-items-center nx-justify-between nx-p-4 nx-text-left hover:nx-bg-gray-50 dark:hover:nx-bg-gray-900"
      >
        <span className="nx-font-semibold">{title}</span>
        <svg
          className={`nx-w-5 nx-h-5 nx-transition-transform ${isOpen ? 'nx-rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {isOpen && (
        <div className="nx-px-4 nx-pb-4 nx-border-t nx-border-gray-200 dark:nx-border-gray-800">
          {children}
        </div>
      )}
    </div>
  )
}

interface AccordionGroupProps {
  children: ReactNode
}

export const AccordionGroup: React.FC<AccordionGroupProps> = ({ children }) => {
  return <div className="nx-space-y-2 nx-my-6">{children}</div>
}
