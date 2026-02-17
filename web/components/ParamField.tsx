import React from 'react'

interface ParamFieldProps {
  header?: string
  type?: string
  required?: boolean
  children: React.ReactNode
}

export const ParamField: React.FC<ParamFieldProps> = ({
  header,
  type,
  required,
  children,
}) => {
  return (
    <div className="nx-my-4 nx-border nx-border-gray-200 dark:nx-border-gray-800 nx-rounded-lg nx-p-4">
      <div className="nx-flex nx-items-center nx-gap-2 nx-mb-2">
        {header && (
          <code className="nx-text-sm nx-font-mono nx-bg-gray-100 dark:nx-bg-gray-900 nx-px-2 nx-py-1 nx-rounded">
            {header}
          </code>
        )}
        {type && (
          <span className="nx-text-xs nx-text-gray-500 dark:nx-text-gray-400">
            {type}
          </span>
        )}
        {required && (
          <span className="nx-text-xs nx-text-red-600 dark:nx-text-red-400 nx-font-semibold">
            required
          </span>
        )}
      </div>
      <div className="nx-text-sm nx-text-gray-700 dark:nx-text-gray-300">
        {children}
      </div>
    </div>
  )
}
