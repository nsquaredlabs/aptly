import React from 'react'

interface ResponseFieldProps {
  name: string
  type?: string
  required?: boolean
  children?: React.ReactNode
}

export const ResponseField: React.FC<ResponseFieldProps> = ({
  name,
  type,
  required,
  children,
}) => {
  return (
    <div className="nx-my-3 nx-pl-4 nx-border-l-2 nx-border-gray-200 dark:nx-border-gray-800">
      <div className="nx-flex nx-items-center nx-gap-2 nx-mb-1">
        <code className="nx-text-sm nx-font-mono nx-text-purple-600 dark:nx-text-purple-400">
          {name}
        </code>
        {type && (
          <span className="nx-text-xs nx-text-gray-500 dark:nx-text-gray-400 nx-font-mono">
            {type}
          </span>
        )}
        {required && (
          <span className="nx-text-xs nx-text-red-600 dark:nx-text-red-400 nx-font-semibold">
            required
          </span>
        )}
      </div>
      {children && (
        <div className="nx-text-sm nx-text-gray-700 dark:nx-text-gray-300">
          {children}
        </div>
      )}
    </div>
  )
}
