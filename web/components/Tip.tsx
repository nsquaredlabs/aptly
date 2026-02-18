'use client'
import React from 'react'

interface TipProps {
  children: React.ReactNode
}

export const Tip: React.FC<TipProps> = ({ children }) => {
  return (
    <div className="nx-my-6 nx-rounded-lg nx-border nx-border-blue-200 dark:nx-border-blue-800 nx-bg-blue-50 dark:nx-bg-blue-900/20 nx-p-4">
      <div className="nx-flex nx-gap-3">
        <div className="nx-text-xl nx-leading-6">💡</div>
        <div className="nx-flex-1 nx-text-sm nx-text-blue-900 dark:nx-text-blue-200">
          {children}
        </div>
      </div>
    </div>
  )
}
