'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'

export function AnimatedCodeDemo() {
  const [phase, setPhase] = useState<'idle' | 'client-delete' | 'client-type' | 'extra-body' | 'complete'>('idle')
  const [clientText, setClientText] = useState('client = OpenAI(\n  api_key="sk_your_openai_key"\n)')
  const [extraBodyText, setExtraBodyText] = useState('')
  const [showCursor, setShowCursor] = useState(false)
  const [cursorAt, setCursorAt] = useState<'client' | 'extra'>('client')
  const [pauseTyping, setPauseTyping] = useState(false)

  const originalClient = 'client = OpenAI(\n  api_key="sk_your_openai_key"\n)'
  const newClient = `client = OpenAI(
  base_url="https://api-aptly.nsquaredlabs.com/v1",
  api_key="apt_live_your_key_here"
)`
  const newExtraBody = ',\n  extra_body={"api_keys": {"openai": "sk_your_openai_key"}}'

  useEffect(() => {
    let timeout: NodeJS.Timeout

    if (phase === 'idle') {
      timeout = setTimeout(() => {
        setShowCursor(true)
        setCursorAt('client')
        setPhase('client-delete')
      }, 2500)
    } else if (phase === 'client-delete') {
      if (clientText.length > 0) {
        timeout = setTimeout(() => {
          setClientText(clientText.slice(0, -1))
        }, 15)
      } else {
        setPhase('client-type')
      }
    } else if (phase === 'client-type') {
      if (pauseTyping) {
        timeout = setTimeout(() => {
          setPauseTyping(false)
        }, 200)
      } else {
        if (clientText.length < newClient.length) {
          const nextChar = newClient[clientText.length]
          const shouldPause = nextChar === ' ' || nextChar === '"' || nextChar === ',' || nextChar === '/'

          timeout = setTimeout(() => {
            setClientText(newClient.slice(0, clientText.length + 1))
            if (shouldPause) {
              setPauseTyping(true)
            }
          }, 60)
        } else {
          setCursorAt('extra')
          setPhase('extra-body')
        }
      }
    } else if (phase === 'extra-body') {
      if (pauseTyping) {
        timeout = setTimeout(() => {
          setPauseTyping(false)
        }, 200)
      } else {
        if (extraBodyText.length < newExtraBody.length) {
          const nextChar = newExtraBody[extraBodyText.length]
          const shouldPause = nextChar === ' ' || nextChar === '"' || nextChar === ',' || nextChar === ':'

          timeout = setTimeout(() => {
            setExtraBodyText(newExtraBody.slice(0, extraBodyText.length + 1))
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
        setClientText(originalClient)
        setExtraBodyText('')
        setPhase('idle')
      }, 4000)
    }

    return () => clearTimeout(timeout)
  }, [phase, clientText, extraBodyText, pauseTyping])

  const benefits = [
    '✓ PII automatically redacted before sending to OpenAI',
    '✓ Complete audit trail logged',
    '✓ Your OpenAI key stays secure (passed per-request)',
  ]

  const clientLines = clientText.split('\n')
  const extraLines = extraBodyText.split('\n')

  return (
    <div className="border border-gray-300 dark:border-gray-800">
      {/* Terminal header */}
      <div className="bg-gray-100 dark:bg-gray-900 px-4 py-2 border-b border-gray-300 dark:border-gray-800 font-mono text-xs text-gray-600 dark:text-gray-400">
        <span className="text-blue-600 dark:text-blue-400">~/aptly</span> $ python example.py
      </div>

      {/* Code */}
      <div className="bg-white dark:bg-black p-6 overflow-x-auto min-h-[400px]">
        <pre className="font-mono text-sm text-gray-900 dark:text-gray-100">
          <div>from openai import OpenAI</div>
          <div></div>

          {/* Client definition with cursor */}
          {clientLines.map((line, i) => (
            <div key={i}>
              {line}
              {showCursor && cursorAt === 'client' && i === clientLines.length - 1 && (
                <motion.span
                  animate={{ opacity: [1, 0] }}
                  transition={{ duration: 0.8, repeat: Infinity, repeatType: 'reverse' }}
                  className="inline-block w-2 h-4 bg-blue-600 dark:bg-blue-400 align-middle"
                />
              )}
            </div>
          ))}

          <div></div>
          <div>response = client.chat.completions.create(</div>
          <div>  model="gpt-4",</div>
          <div>  messages=[{'{"role": "user", "content": "My email is john@example.com"}'}]
            {/* Extra body with cursor */}
            {extraLines.map((line, i) => (
              <span key={i}>
                {line}
                {showCursor && cursorAt === 'extra' && i === extraLines.length - 1 && (
                  <motion.span
                    animate={{ opacity: [1, 0] }}
                    transition={{ duration: 0.8, repeat: Infinity, repeatType: 'reverse' }}
                    className="inline-block w-2 h-4 bg-blue-600 dark:bg-blue-400 align-middle"
                  />
                )}
              </span>
            ))}
          </div>
          <div>)</div>

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
