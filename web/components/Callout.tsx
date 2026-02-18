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
      bg: 'nx-bg-blue-50 dark:nx-bg-blue-900/20',
      border: 'nx-border-blue-200 dark:nx-border-blue-800',
      text: 'nx-text-blue-900 dark:nx-text-blue-200',
      emoji: emoji || 'ℹ️',
    },
    warning: {
      bg: 'nx-bg-yellow-50 dark:nx-bg-yellow-900/20',
      border: 'nx-border-yellow-200 dark:nx-border-yellow-800',
      text: 'nx-text-yellow-900 dark:nx-text-yellow-200',
      emoji: emoji || '⚠️',
    },
    error: {
      bg: 'nx-bg-red-50 dark:nx-bg-red-900/20',
      border: 'nx-border-red-200 dark:nx-border-red-800',
      text: 'nx-text-red-900 dark:nx-text-red-200',
      emoji: emoji || '❌',
    },
    success: {
      bg: 'nx-bg-green-50 dark:nx-bg-green-900/20',
      border: 'nx-border-green-200 dark:nx-border-green-800',
      text: 'nx-text-green-900 dark:nx-text-green-200',
      emoji: emoji || '✅',
    },
    note: {
      bg: 'nx-bg-gray-50 dark:nx-bg-gray-900/20',
      border: 'nx-border-gray-200 dark:nx-border-gray-800',
      text: 'nx-text-gray-900 dark:nx-text-gray-200',
      emoji: emoji || '📝',
    },
  }

  const style = styles[type]

  return (
    <div
      className={`
        nx-my-6 nx-rounded-lg nx-border nx-p-4
        ${style.bg} ${style.border} ${style.text}
      `}
    >
      <div className="nx-flex nx-gap-3">
        <div className="nx-text-xl nx-leading-6">
          {style.emoji}
        </div>
        <div className="nx-flex-1 nx-text-sm">
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
