'use client'
import React from 'react'

interface ParamFieldProps {
  header?: string
  path?: string
  body?: string
  type?: string
  required?: boolean
  children: React.ReactNode
}

export const ParamField: React.FC<ParamFieldProps> = ({
  header,
  path,
  body,
  type,
  required,
  children,
}) => {
  const paramName = header || path || body

  return (
    <div className="my-3 border-l-4 border-blue-500 bg-gray-50 dark:bg-gray-800/50 pl-4 py-3">
      <div className="flex items-center gap-2 mb-1">
        {paramName && (
          <code className="text-sm font-mono font-semibold text-gray-900 dark:text-gray-100">
            {paramName}
          </code>
        )}
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
      <div className="text-sm text-gray-700 dark:text-gray-300">
        {children}
      </div>
    </div>
  )
}
