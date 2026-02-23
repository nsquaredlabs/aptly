'use client'

import { useState } from 'react'
import { updateSettings } from './actions'

const FRAMEWORKS = [
  {
    id: 'HIPAA',
    label: 'HIPAA',
    description: 'Healthcare — detects MRNs, health plan numbers, device serials',
    extraEntities: 3,
  },
  {
    id: 'FinTech',
    label: 'FinTech / PCI-DSS',
    description: 'Financial — detects CVV, routing numbers, account numbers',
    extraEntities: 3,
  },
  {
    id: 'GDPR',
    label: 'GDPR',
    description: 'EU compliance — detects EU VAT numbers, national IDs, EU passports',
    extraEntities: 3,
  },
  {
    id: 'SOC2',
    label: 'SOC2',
    description: 'Security — detects API keys, AWS keys, GitHub tokens, JWTs',
    extraEntities: 6,
  },
]

interface Customer {
  company_name: string | null
  plan: string
  pii_redaction_mode: string
  compliance_frameworks: string[]
}

interface Props {
  customer: Customer | null
  email: string
  customerId: string
  requestsThisMonth: number
  planLimits: { requests_per_month: number | null; rate_per_hour: number }
}

export default function SettingsClient({ customer, email, customerId, requestsThisMonth, planLimits }: Props) {
  const [companyName, setCompanyName] = useState(customer?.company_name ?? '')
  const [redactionMode, setRedactionMode] = useState(customer?.pii_redaction_mode ?? 'mask')
  const [frameworks, setFrameworks] = useState<string[]>(customer?.compliance_frameworks ?? [])
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')

  function toggleFramework(id: string) {
    setFrameworks((prev) =>
      prev.includes(id) ? prev.filter((f) => f !== id) : [...prev, id]
    )
  }

  const totalExtraEntities = FRAMEWORKS
    .filter((f) => frameworks.includes(f.id))
    .reduce((sum, f) => sum + f.extraEntities, 0)

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    setError('')
    setSaved(false)
    try {
      await updateSettings({
        company_name: companyName,
        pii_redaction_mode: redactionMode as 'mask' | 'hash' | 'remove',
        compliance_frameworks: frameworks,
      })
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch {
      setError('Failed to save settings')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSave} className="space-y-6">
      {error && (
        <div className="bg-red-900/30 border border-red-700 text-red-300 rounded-lg px-4 py-3 text-sm">
          {error}
        </div>
      )}

      {/* Profile */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-5">
        <h2 className="text-white font-medium">Profile</h2>

        <div>
          <label className="block text-sm text-gray-400 mb-1.5">Company name</label>
          <input
            type="text"
            value={companyName}
            onChange={(e) => setCompanyName(e.target.value)}
            className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3.5 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
          />
        </div>

        <div>
          <label className="block text-sm text-gray-400 mb-1.5">Email</label>
          <input
            type="email"
            value={email}
            disabled
            className="w-full bg-gray-800/50 border border-gray-700 rounded-lg px-3.5 py-2.5 text-gray-500 text-sm cursor-not-allowed"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">Customer ID</label>
            <p className="text-gray-500 text-xs font-mono bg-gray-800 rounded px-3 py-2">{customerId}</p>
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">Plan</label>
            <p className="text-gray-300 text-sm bg-gray-800 rounded px-3 py-2 capitalize">{customer?.plan ?? 'free'}</p>
          </div>
        </div>
      </div>

      {/* PII Redaction Mode */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
        <div>
          <h2 className="text-white font-medium">PII Redaction Mode</h2>
          <p className="text-gray-500 text-sm mt-1">How detected PII is handled before being sent to the LLM.</p>
        </div>
        <div className="space-y-2">
          {[
            { value: 'mask', label: 'Mask', example: '"John Smith" → "PERSON_A"' },
            { value: 'hash', label: 'Hash', example: '"John Smith" → "HASH_a3f2c1b9"' },
            { value: 'remove', label: 'Remove', example: '"John Smith" → "[REDACTED]"' },
          ].map(({ value, label, example }) => (
            <label key={value} className="flex items-center gap-3 cursor-pointer group">
              <input
                type="radio"
                name="redaction_mode"
                value={value}
                checked={redactionMode === value}
                onChange={() => setRedactionMode(value)}
                className="accent-blue-500"
              />
              <div>
                <span className="text-gray-200 text-sm">{label}</span>
                <span className="text-gray-500 text-xs ml-2">{example}</span>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Compliance Frameworks */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
        <div>
          <h2 className="text-white font-medium">Compliance Frameworks</h2>
          <p className="text-gray-500 text-sm mt-1">
            All customers detect 12 baseline PII entities. Enable frameworks to detect additional industry-specific entities.
          </p>
        </div>

        <div className="space-y-3">
          {FRAMEWORKS.map((f) => (
            <label key={f.id} className="flex items-start gap-3 cursor-pointer group">
              <input
                type="checkbox"
                checked={frameworks.includes(f.id)}
                onChange={() => toggleFramework(f.id)}
                className="mt-0.5 accent-blue-500"
              />
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-gray-200 text-sm font-medium">{f.label}</span>
                  <span className="text-xs text-blue-400 bg-blue-400/10 px-1.5 py-0.5 rounded">
                    +{f.extraEntities} entities
                  </span>
                </div>
                <p className="text-gray-500 text-xs mt-0.5">{f.description}</p>
              </div>
            </label>
          ))}
        </div>

        {frameworks.length > 0 && (
          <p className="text-sm text-gray-400 pt-2 border-t border-gray-800">
            Total entities detected: <span className="text-white font-medium">{12 + totalExtraEntities}</span>
            <span className="text-gray-600"> (12 baseline + {totalExtraEntities} framework-specific)</span>
          </p>
        )}
      </div>

      {/* Plan Information */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
        <h2 className="text-white font-medium">Plan &amp; Usage</h2>
        <div className="space-y-3">
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span className="text-gray-400">Requests this month</span>
              <span className="text-gray-300">
                {requestsThisMonth.toLocaleString()}
                {planLimits.requests_per_month
                  ? ` / ${planLimits.requests_per_month.toLocaleString()}`
                  : ' / unlimited'}
              </span>
            </div>
            {planLimits.requests_per_month && (
              <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 rounded-full"
                  style={{
                    width: `${Math.min(100, (requestsThisMonth / planLimits.requests_per_month) * 100)}%`,
                  }}
                />
              </div>
            )}
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Rate limit</span>
            <span className="text-gray-300">{planLimits.rate_per_hour.toLocaleString()} req/hour</span>
          </div>
        </div>
        <a
          href="mailto:hello@nsquaredlabs.com?subject=Upgrade Aptly Plan"
          className="inline-block text-sm text-blue-400 hover:text-blue-300"
        >
          Contact us to upgrade →
        </a>
      </div>

      {/* Save */}
      <div className="flex items-center gap-4">
        <button
          type="submit"
          disabled={saving}
          className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm font-medium rounded-lg px-5 py-2.5 transition-colors"
        >
          {saving ? 'Saving…' : 'Save settings'}
        </button>
        {saved && <span className="text-green-400 text-sm">✓ Saved</span>}
      </div>
    </form>
  )
}
