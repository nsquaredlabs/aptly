'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'

export function AnimatedCodeDemo() {
  const [phase, setPhase] = useState<'idle' | 'deleting' | 'typing' | 'complete'>('idle')
  const [displayedText, setDisplayedText] = useState('client = OpenAI(\n  api_key="sk_your_openai_key"\n)')
  const [showCursor, setShowCursor] = useState(false)
  const [pauseTyping, setPauseTyping] = useState(false)

  const originalLines = 'client = OpenAI(\n  api_key="sk_your_openai_key"\n)'
  const newLines = `client = OpenAI(
  base_url="https://api-aptly.nsquaredlabs.com/v1",
  api_key="apt_live_your_key_here"
)

response = client.chat.completions.create(
  model="gpt-4",
  messages=[{"role": "user", "content": "My email is john@example.com"}],
  extra_body={"api_keys": {"openai": "sk_your_openai_key"}}
)`

  useEffect(() => {
    let timeout: NodeJS.Timeout

    if (phase === 'idle') {
      timeout = setTimeout(() => {
        setShowCursor(true)
        setPhase('deleting')
      }, 2500)
    } else if (phase === 'deleting') {
      if (displayedText.length > 0) {
        timeout = setTimeout(() => {
          setDisplayedText(displayedText.slice(0, -1))
        }, 20)
      } else {
        setPhase('typing')
      }
    } else if (phase === 'typing') {
      if (pauseTyping) {
        timeout = setTimeout(() => {
          setPauseTyping(false)
        }, 200)
      } else {
        if (displayedText.length < newLines.length) {
          const nextChar = newLines[displayedText.length]

          // Check if we just completed a word (space, quote, comma, etc.)
          const shouldPause = nextChar === ' ' || nextChar === '"' || nextChar === ',' || nextChar === '/'

          timeout = setTimeout(() => {
            setDisplayedText(newLines.slice(0, displayedText.length + 1))
            if (shouldPause) {
              setPauseTyping(true)
            }
          }, 60)
        } else {
          setPhase('complete')
        }
      }
    } else if (phase === 'complete') {
      timeout = setTimeout(() => {
        setShowCursor(false)
      }, 500)
      timeout = setTimeout(() => {
        setDisplayedText(originalLines)
        setPhase('idle')
      }, 4000)
    }

    return () => clearTimeout(timeout)
  }, [phase, displayedText, pauseTyping])

  const codeLines = [
    'from openai import OpenAI',
    '',
  ]

  const benefits = [
    '✓ PII automatically redacted before sending to OpenAI',
    '✓ Complete audit trail logged',
    '✓ Your OpenAI key stays secure (passed per-request)',
  ]

  const lines = displayedText.split('\n')

  return (
    <div className="border border-gray-300 dark:border-gray-800">
      {/* Terminal header */}
      <div className="bg-gray-100 dark:bg-gray-900 px-4 py-2 border-b border-gray-300 dark:border-gray-800 font-mono text-xs text-gray-600 dark:text-gray-400">
        <span className="text-blue-600 dark:text-blue-400">~/aptly</span> $ python example.py
      </div>

      {/* Code */}
      <div className="bg-white dark:bg-black p-6 overflow-x-auto min-h-[400px]">
        <pre className="font-mono text-sm text-gray-900 dark:text-gray-100">
          {/* Static top lines */}
          {codeLines.map((line, i) => (
            <div key={i}>{line}</div>
          ))}

          {/* Animated typing/deleting with inline cursor */}
          {lines.map((line, i) => (
            <div key={i}>
              {line}
              {/* Show cursor at the end of the last line */}
              {showCursor && i === lines.length - 1 && (
                <motion.span
                  animate={{ opacity: [1, 0] }}
                  transition={{ duration: 0.8, repeat: Infinity, repeatType: 'reverse' }}
                  className="inline-block w-2 h-4 bg-blue-600 dark:bg-blue-400 align-middle"
                />
              )}
            </div>
          ))}

          {/* Benefits (show when complete) */}
          {phase === 'complete' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5 }}
              className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-800"
            >
              {benefits.map((benefit, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.15 }}
                  className="text-gray-500 dark:text-gray-500"
                >
                  # {benefit}
                </motion.div>
              ))}
            </motion.div>
          )}
        </pre>
      </div>
    </div>
  )
}
