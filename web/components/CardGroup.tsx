'use client'
import React from 'react'

interface CardGroupProps {
  children: React.ReactNode
  cols?: number
}

export const CardGroup: React.FC<CardGroupProps> = ({ children, cols = 2 }) => {
  return (
    <div
      className="nx-grid nx-gap-4 nx-my-6"
      style={{
        gridTemplateColumns: `repeat(1, minmax(0, 1fr))`,
      }}
      // Use media queries for responsive columns
      data-cols={cols}
    >
      <style jsx>{`
        @media (min-width: 768px) {
          div[data-cols="2"] {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }
          div[data-cols="3"] {
            grid-template-columns: repeat(3, minmax(0, 1fr));
          }
          div[data-cols="4"] {
            grid-template-columns: repeat(4, minmax(0, 1fr));
          }
        }
      `}</style>
      {children}
    </div>
  )
}
