'use client'
import React from 'react'

interface CardProps {
  title: string
  icon?: string
  children?: React.ReactNode
  href?: string
}

export const Card: React.FC<CardProps> = ({ title, icon, children, href }) => {
  const CardContent = (
    <div className="nx-border nx-border-gray-200 dark:nx-border-gray-800 nx-rounded-lg nx-p-4 hover:nx-shadow-md nx-transition-shadow nx-h-full">
      {icon && (
        <div className="nx-text-2xl nx-mb-2">
          {icon}
        </div>
      )}
      <h3 className="nx-font-semibold nx-mb-2 nx-text-gray-900 dark:nx-text-gray-100">
        {title}
      </h3>
      {children && (
        <div className="nx-text-sm nx-text-gray-600 dark:nx-text-gray-400">
          {children}
        </div>
      )}
    </div>
  )

  if (href) {
    return (
      <a href={href} className="nx-no-underline hover:nx-no-underline">
        {CardContent}
      </a>
    )
  }

  return CardContent
}
