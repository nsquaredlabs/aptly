'use client'
import React from 'react'

interface CheckProps {
  children: React.ReactNode
}

export const Check: React.FC<CheckProps> = ({ children }) => {
  return (
    <div className="nx-flex nx-items-start nx-gap-2 nx-my-2">
      <span className="nx-text-green-600 dark:nx-text-green-400 nx-text-xl nx-mt-0.5">✓</span>
      <div className="nx-flex-1 nx-text-sm">{children}</div>
    </div>
  )
}
