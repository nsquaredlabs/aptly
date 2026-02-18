'use client'
import React from 'react'

interface ResponseExampleProps {
  children: React.ReactNode
}

export const ResponseExample: React.FC<ResponseExampleProps> = ({ children }) => {
  return (
    <div className="nx-mt-6 nx-mb-6">
      <div className="nx-bg-gray-50 dark:nx-bg-gray-900 nx-border nx-border-gray-200 dark:nx-border-gray-800 nx-rounded-lg">
        <div className="nx-px-4 nx-py-2 nx-border-b nx-border-gray-200 dark:nx-border-gray-800 nx-bg-gray-100 dark:nx-bg-gray-800/50">
          <span className="nx-text-sm nx-font-medium nx-text-gray-700 dark:nx-text-gray-300">
            Response
          </span>
        </div>
        <div className="nx-p-0">
          {children}
        </div>
      </div>
    </div>
  )
}
