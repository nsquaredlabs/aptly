'use client'

import { Fragment, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'

interface PiiEntity {
  type: string
  replacement: string
  confidence: number
}

interface Log {
  id: string
  provider: string
  model: string
  pii_detected: PiiEntity[]
  response_pii_detected: PiiEntity[] | null
  tokens_input: number | null
  tokens_output: number | null
  latency_ms: number | null
  cost_usd: number | null
  compliance_framework: string | null
  user_id: string | null
  request_data: { messages?: Array<{ role: string; content: string }> } | null
  response_data: { content?: string } | null
  created_at: string
}

interface Props {
  logs: Log[]
  total: number
  page: number
  pageSize: number
  startDate: string
  endDate: string
}

function PiiChips({ entities, label }: { entities: PiiEntity[]; label: string }) {
  if (!entities.length) return null
  return (
    <div>
      <p className="text-xs text-gray-500 mb-2">{label}</p>
      <div className="flex flex-wrap gap-2">
        {entities.map((e, i) => (
          <span key={i} className="inline-flex items-center gap-1.5 text-xs bg-amber-900/30 text-amber-300 border border-amber-700/40 px-2 py-1 rounded">
            <span>{String(e.type ?? '').replace(/_/g, ' ')}</span>
            <span className="text-amber-600">→ {e.replacement}</span>
            {e.confidence != null && (
              <span className="text-amber-500/70">{Math.round(e.confidence * 100)}%</span>
            )}
          </span>
        ))}
      </div>
    </div>
  )
}

function MessageBlock({ messages }: { messages: Array<{ role: string; content: string }> }) {
  return (
    <div className="space-y-2">
      {messages.map((m, i) => (
        <div key={i}>
          <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">{m.role}</span>
          <p className="text-xs text-gray-300 mt-0.5 leading-relaxed whitespace-pre-wrap break-words">
            {typeof m.content === 'string' ? m.content : JSON.stringify(m.content)}
          </p>
        </div>
      ))}
    </div>
  )
}

export default function LogsClient({ logs, total, page, pageSize, startDate, endDate }: Props) {
  const router = useRouter()
  const pathname = usePathname()
  const [start, setStart] = useState(startDate)
  const [end, setEnd] = useState(endDate)
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const totalPages = Math.ceil(total / pageSize)

  function navigate(p: number) {
    const params = new URLSearchParams()
    if (start) params.set('start', start)
    if (end) params.set('end', end)
    params.set('page', String(p))
    router.push(`${pathname}?${params}`)
  }

  return (
    <>
      {/* Filters */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-4 mb-6 flex items-end gap-4">
        <div>
          <label className="block text-xs text-gray-500 mb-1">From</label>
          <input
            type="date"
            value={start}
            onChange={(e) => setStart(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">To</label>
          <input
            type="date"
            value={end}
            onChange={(e) => setEnd(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <button
          onClick={() => navigate(1)}
          className="bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg px-4 py-2 transition-colors"
        >
          Filter
        </button>
        {(start || end) && (
          <button
            onClick={() => { setStart(''); setEnd(''); router.push(pathname) }}
            className="text-gray-400 hover:text-gray-200 text-sm"
          >
            Clear
          </button>
        )}
        <span className="ml-auto text-gray-500 text-sm">{total.toLocaleString()} total</span>
      </div>

      {/* Table */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden mb-4">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-800">
              <th className="text-left px-5 py-3 text-xs text-gray-500 font-medium">Timestamp</th>
              <th className="text-left px-5 py-3 text-xs text-gray-500 font-medium">Model</th>
              <th className="text-left px-5 py-3 text-xs text-gray-500 font-medium">PII</th>
              <th className="text-left px-5 py-3 text-xs text-gray-500 font-medium">Tokens</th>
              <th className="text-left px-5 py-3 text-xs text-gray-500 font-medium">Cost</th>
              <th className="text-left px-5 py-3 text-xs text-gray-500 font-medium">Latency</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {logs.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-5 py-10 text-center text-gray-500 text-sm">
                  No logs found
                </td>
              </tr>
            ) : (
              logs.map((log) => {
                const inputPii = Array.isArray(log.pii_detected) ? log.pii_detected : []
                const responsePii = Array.isArray(log.response_pii_detected) ? log.response_pii_detected : []
                const totalPii = inputPii.length + responsePii.length
                const messages = log.request_data?.messages ?? []
                const responseText = log.response_data?.content ?? null

                return (
                  <Fragment key={log.id}>
                    <tr
                      onClick={() => setExpandedId(expandedId === log.id ? null : log.id)}
                      className="hover:bg-gray-800/50 cursor-pointer transition-colors"
                    >
                      <td className="px-5 py-3 text-sm text-gray-400 whitespace-nowrap">
                        {new Date(log.created_at).toLocaleString()}
                      </td>
                      <td className="px-5 py-3">
                        <span className="text-sm font-mono text-gray-300">{log.model}</span>
                        <span className="ml-2 text-xs text-gray-600">{log.provider}</span>
                      </td>
                      <td className="px-5 py-3">
                        {totalPii > 0 ? (
                          <span className="text-xs text-amber-400 bg-amber-400/10 px-2 py-0.5 rounded">
                            {totalPii} detected
                          </span>
                        ) : (
                          <span className="text-xs text-gray-600">—</span>
                        )}
                      </td>
                      <td className="px-5 py-3 text-sm text-gray-400">
                        {log.tokens_input != null ? (
                          <span>
                            <span className="text-gray-300">{(log.tokens_input + (log.tokens_output ?? 0)).toLocaleString()}</span>
                            <span className="text-gray-600 text-xs ml-1">({log.tokens_input}↑ {log.tokens_output ?? 0}↓)</span>
                          </span>
                        ) : '—'}
                      </td>
                      <td className="px-5 py-3 text-sm text-gray-400">
                        {log.cost_usd != null ? `$${log.cost_usd.toFixed(4)}` : '—'}
                      </td>
                      <td className="px-5 py-3 text-sm text-gray-400">
                        {log.latency_ms != null ? `${log.latency_ms}ms` : '—'}
                      </td>
                    </tr>

                    {expandedId === log.id && (
                      <tr className="bg-gray-800/20">
                        <td colSpan={6} className="px-5 py-5">
                          <div className="space-y-5">

                            {/* Metadata row */}
                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                              {log.user_id && (
                                <div>
                                  <p className="text-xs text-gray-500 mb-0.5">User</p>
                                  <p className="text-xs text-gray-300 font-mono truncate">{log.user_id}</p>
                                </div>
                              )}
                              {log.compliance_framework && (
                                <div>
                                  <p className="text-xs text-gray-500 mb-0.5">Framework</p>
                                  <span className="text-xs text-blue-400 bg-blue-400/10 px-1.5 py-0.5 rounded">
                                    {log.compliance_framework}
                                  </span>
                                </div>
                              )}
                              <div>
                                <p className="text-xs text-gray-500 mb-0.5">Tokens in / out</p>
                                <p className="text-xs text-gray-300">{log.tokens_input ?? '—'} / {log.tokens_output ?? '—'}</p>
                              </div>
                              {log.cost_usd != null && (
                                <div>
                                  <p className="text-xs text-gray-500 mb-0.5">Cost</p>
                                  <p className="text-xs text-gray-300">${log.cost_usd.toFixed(6)}</p>
                                </div>
                              )}
                            </div>

                            {/* PII */}
                            {(inputPii.length > 0 || responsePii.length > 0) && (
                              <div className="space-y-3">
                                <PiiChips entities={inputPii} label="PII in request" />
                                <PiiChips entities={responsePii} label="PII in response" />
                              </div>
                            )}

                            {/* Prompt / response */}
                            {messages.length > 0 && (
                              <div>
                                <p className="text-xs text-gray-500 mb-2">Redacted prompt</p>
                                <div className="bg-gray-900 border border-gray-800 rounded-lg px-4 py-3">
                                  <MessageBlock messages={messages} />
                                </div>
                              </div>
                            )}

                            {responseText && (
                              <div>
                                <p className="text-xs text-gray-500 mb-2">Response</p>
                                <div className="bg-gray-900 border border-gray-800 rounded-lg px-4 py-3">
                                  <p className="text-xs text-gray-300 leading-relaxed whitespace-pre-wrap break-words">{responseText}</p>
                                </div>
                              </div>
                            )}

                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                )
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <button
            onClick={() => navigate(page - 1)}
            disabled={page <= 1}
            className="text-sm text-gray-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed"
          >
            ← Previous
          </button>
          <span className="text-sm text-gray-500">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => navigate(page + 1)}
            disabled={page >= totalPages}
            className="text-sm text-gray-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed"
          >
            Next →
          </button>
        </div>
      )}
    </>
  )
}
