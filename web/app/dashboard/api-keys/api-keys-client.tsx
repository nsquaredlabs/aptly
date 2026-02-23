'use client'

import { useState } from 'react'
import { createKey, revokeKey } from './actions'

interface APIKey {
  id: string
  key_prefix: string
  name: string | null
  is_revoked: boolean
  created_at: string
  last_used_at: string | null
}

export default function APIKeysClient({ initialKeys }: { initialKeys: APIKey[] }) {
  const [keys, setKeys] = useState<APIKey[]>(initialKeys)
  const [showCreate, setShowCreate] = useState(false)
  const [newKeyName, setNewKeyName] = useState('')
  const [createdKey, setCreatedKey] = useState<string | null>(null)
  const [creating, setCreating] = useState(false)
  const [revoking, setRevoking] = useState<string | null>(null)
  const [confirmRevoke, setConfirmRevoke] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [error, setError] = useState('')

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    setCreating(true)
    setError('')
    try {
      const { key, id } = await createKey(newKeyName || 'Default')
      setCreatedKey(key)
      setKeys((prev) => [
        {
          id,
          key_prefix: key.slice(0, 12) + '...',
          name: newKeyName || 'Default',
          is_revoked: false,
          created_at: new Date().toISOString(),
          last_used_at: null,
        },
        ...prev,
      ])
      setNewKeyName('')
      setShowCreate(false)
    } catch {
      setError('Failed to create key')
    } finally {
      setCreating(false)
    }
  }

  async function handleRevoke(keyId: string) {
    setRevoking(keyId)
    try {
      await revokeKey(keyId)
      setKeys((prev) => prev.map((k) => k.id === keyId ? { ...k, is_revoked: true } : k))
    } catch {
      setError('Failed to revoke key')
    } finally {
      setRevoking(null)
      setConfirmRevoke(null)
    }
  }

  function copyKey() {
    if (!createdKey) return
    navigator.clipboard.writeText(createdKey)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const activeKeys = keys.filter((k) => !k.is_revoked)
  const revokedKeys = keys.filter((k) => k.is_revoked)

  return (
    <>
      {/* New key revealed */}
      {createdKey && (
        <div className="mb-6 bg-gray-900 border border-gray-700 rounded-xl p-5">
          <div className="flex items-start justify-between mb-3">
            <div>
              <p className="text-white font-medium">API key created</p>
              <p className="text-gray-400 text-sm mt-0.5">
                Copy this key now — it will not be shown again.
              </p>
            </div>
            <button onClick={() => setCreatedKey(null)} className="text-gray-500 hover:text-gray-300 text-xl leading-none">×</button>
          </div>
          <div className="flex items-center gap-3 bg-gray-800 rounded-lg px-4 py-3">
            <span className="text-gray-200 text-sm font-mono flex-1 break-all">{createdKey}</span>
            <button
              onClick={copyKey}
              className="shrink-0 text-sm font-medium text-blue-400 hover:text-blue-300 transition-colors"
            >
              {copied ? '✓ Copied' : 'Copy'}
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="mb-4 bg-red-900/30 border border-red-700 text-red-300 rounded-lg px-4 py-3 text-sm">
          {error}
        </div>
      )}

      {/* Create key */}
      <div className="mb-6">
        {showCreate ? (
          <form onSubmit={handleCreate} className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h3 className="text-white font-medium mb-4">New API key</h3>
            <div className="flex gap-3">
              <input
                type="text"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                placeholder="Key name (e.g. Production)"
                className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-3.5 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              />
              <button
                type="submit"
                disabled={creating}
                className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm font-medium rounded-lg px-4 py-2.5 transition-colors"
              >
                {creating ? 'Creating…' : 'Create'}
              </button>
              <button
                type="button"
                onClick={() => setShowCreate(false)}
                className="text-gray-400 hover:text-gray-200 text-sm px-3"
              >
                Cancel
              </button>
            </div>
          </form>
        ) : (
          <button
            onClick={() => setShowCreate(true)}
            className="bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium rounded-lg px-4 py-2.5 transition-colors"
          >
            + Create API key
          </button>
        )}
      </div>

      {/* Active keys */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden mb-6">
        <div className="px-5 py-4 border-b border-gray-800">
          <h2 className="text-white font-medium">Active keys ({activeKeys.length})</h2>
        </div>
        {activeKeys.length === 0 ? (
          <div className="px-5 py-8 text-center text-gray-500 text-sm">
            No active API keys. Create one to start using Aptly.
          </div>
        ) : (
          <div className="divide-y divide-gray-800">
            {activeKeys.map((key) => (
              <div key={key.id} className="px-5 py-4 flex items-center gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-gray-300 text-sm font-mono">{key.key_prefix}</span>
                    {key.name && (
                      <span className="text-gray-500 text-sm">· {key.name}</span>
                    )}
                  </div>
                  <div className="text-xs text-gray-600 mt-0.5">
                    Created {new Date(key.created_at).toLocaleDateString()}
                    {key.last_used_at && ` · Last used ${new Date(key.last_used_at).toLocaleDateString()}`}
                  </div>
                </div>
                {confirmRevoke === key.id ? (
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-400">Revoke this key?</span>
                    <button
                      onClick={() => handleRevoke(key.id)}
                      disabled={revoking === key.id}
                      className="text-xs text-red-400 hover:text-red-300"
                    >
                      {revoking === key.id ? 'Revoking…' : 'Yes, revoke'}
                    </button>
                    <button
                      onClick={() => setConfirmRevoke(null)}
                      className="text-xs text-gray-500 hover:text-gray-300"
                    >
                      Cancel
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => setConfirmRevoke(key.id)}
                    className="text-xs text-gray-500 hover:text-red-400 transition-colors"
                  >
                    Revoke
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Revoked keys */}
      {revokedKeys.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-800">
            <h2 className="text-gray-500 font-medium text-sm">Revoked keys ({revokedKeys.length})</h2>
          </div>
          <div className="divide-y divide-gray-800">
            {revokedKeys.map((key) => (
              <div key={key.id} className="px-5 py-4 flex items-center gap-4 opacity-50">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500 text-sm font-mono line-through">{key.key_prefix}</span>
                    {key.name && <span className="text-gray-600 text-sm">· {key.name}</span>}
                  </div>
                  <div className="text-xs text-gray-600 mt-0.5">
                    Revoked
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  )
}
