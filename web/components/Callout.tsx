'use client'
import React from 'react'

interface CalloutProps {
  type?: 'info' | 'warning' | 'error' | 'success' | 'note'
  children: React.ReactNode
  emoji?: string
}

export const Callout: React.FC<CalloutProps> = ({ type = 'info', children, emoji }) => {
  const styles = {
    info: {
      bg: 'bg-blue-50 dark:bg-blue-900/20',
      border: 'border-blue-200 dark:border-blue-800',
      text: 'text-blue-900 dark:text-blue-200',
      emoji: emoji || 'ℹ️',
    },
    warning: {
      bg: 'bg-yellow-50 dark:bg-yellow-900/20',
      border: 'border-yellow-200 dark:border-yellow-800',
      text: 'text-yellow-900 dark:text-yellow-200',
      emoji: emoji || '⚠️',
    },
    error: {
      bg: 'bg-red-50 dark:bg-red-900/20',
      border: 'border-red-200 dark:border-red-800',
      text: 'text-red-900 dark:text-red-200',
      emoji: emoji || '❌',
    },
    success: {
      bg: 'bg-green-50 dark:bg-green-900/20',
      border: 'border-green-200 dark:border-green-800',
      text: 'text-green-900 dark:text-green-200',
      emoji: emoji || '✅',
    },
    note: {
      bg: 'bg-gray-50 dark:bg-gray-900/20',
      border: 'border-gray-200 dark:border-gray-800',
      text: 'text-gray-900 dark:text-gray-200',
      emoji: emoji || '📝',
    },
  }

  const style = styles[type]

  return (
    <div
      className={`
        my-6 rounded-lg border p-4
        ${style.bg} ${style.border} ${style.text}
      `}
    >
      <div className="flex gap-3">
        <div className="text-xl leading-6">
          {style.emoji}
        </div>
        <div className="flex-1 text-sm">
          {children}
        </div>
      </div>
    </div>
  )
}

// Convenience exports for common callout types
export const Note: React.FC<Omit<CalloutProps, 'type'>> = (props) => (
  <Callout type="note" {...props} />
)

export const Warning: React.FC<Omit<CalloutProps, 'type'>> = (props) => (
  <Callout type="warning" {...props} />
)

export const Info: React.FC<Omit<CalloutProps, 'type'>> = (props) => (
  <Callout type="info" {...props} />
)

export const Error: React.FC<Omit<CalloutProps, 'type'>> = (props) => (
  <Callout type="error" {...props} />
)

export const Success: React.FC<Omit<CalloutProps, 'type'>> = (props) => (
  <Callout type="success" {...props} />
)
