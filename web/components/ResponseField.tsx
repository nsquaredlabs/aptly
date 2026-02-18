'use client'
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
    <div className="my-2 pl-4 border-l-2 border-green-500">
      <div className="flex items-center gap-2 mb-1">
        <code className="text-sm font-mono font-semibold text-green-700 dark:text-green-400">
          {name}
        </code>
        {type && (
          <span className="text-xs text-gray-500 dark:text-gray-400 font-mono">
            {type}
          </span>
        )}
        {required && (
          <span className="text-xs text-red-600 dark:text-red-400 font-semibold uppercase">
            required
          </span>
        )}
      </div>
      {children && (
        <div className="text-sm text-gray-700 dark:text-gray-300">
          {children}
        </div>
      )}
    </div>
  )
}
