import Link from 'next/link'

export default function DocsIntroduction() {
  return (
    <article className="prose-custom">
      <div className="font-mono text-sm text-blue-600 dark:text-blue-400 mb-6">
        <span className="text-gray-400"># </span>Documentation
      </div>

      <h1 className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-6 leading-tight">
        Compliance-as-a-Service for AI Applications
      </h1>

      <p className="text-xl text-gray-600 dark:text-gray-400 mb-12 leading-relaxed">
        Aptly is a drop-in API that sits between your application and any LLM provider,
        automatically redacting PII and creating immutable audit logs for every request.
      </p>

      {/* What It Does */}
      <section className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4 font-mono border-b border-gray-200 dark:border-gray-800 pb-2">
          What It Does
        </h2>
        <div className="space-y-1">
          <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-4">
            <div className="flex items-start gap-3">
              <span className="text-blue-600 dark:text-blue-400">✓</span>
              <div>
                <strong className="text-gray-900 dark:text-white">Automatic PII Detection</strong>
                <p className="text-gray-600 dark:text-gray-400 text-sm mt-1">
                  Scans every request for sensitive data (SSNs, emails, credit cards, names, etc.) before sending to LLMs
                </p>
              </div>
            </div>
          </div>
          <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-4">
            <div className="flex items-start gap-3">
              <span className="text-blue-600 dark:text-blue-400">✓</span>
              <div>
                <strong className="text-gray-900 dark:text-white">Configurable Redaction</strong>
                <p className="text-gray-600 dark:text-gray-400 text-sm mt-1">
                  Choose how to handle PII: mask it (PERSON_A), hash it, or remove it entirely
                </p>
              </div>
            </div>
          </div>
          <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-4">
            <div className="flex items-start gap-3">
              <span className="text-blue-600 dark:text-blue-400">✓</span>
              <div>
                <strong className="text-gray-900 dark:text-white">Immutable Audit Trail</strong>
                <p className="text-gray-600 dark:text-gray-400 text-sm mt-1">
                  Every request is logged with timestamps, PII detections, and full metadata (database-enforced immutability)
                </p>
              </div>
            </div>
          </div>
          <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-4">
            <div className="flex items-start gap-3">
              <span className="text-blue-600 dark:text-blue-400">✓</span>
              <div>
                <strong className="text-gray-900 dark:text-white">Multi-Provider Support</strong>
                <p className="text-gray-600 dark:text-gray-400 text-sm mt-1">
                  Works with OpenAI, Anthropic, Google, Cohere, Together AI, and more via LiteLLM
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4 font-mono border-b border-gray-200 dark:border-gray-800 pb-2">
          How It Works
        </h2>

        <div className="border border-gray-300 dark:border-gray-800 mb-6">
          <div className="bg-gray-100 dark:bg-gray-900 px-4 py-2 border-b border-gray-300 dark:border-gray-800 font-mono text-xs text-gray-600 dark:text-gray-400">
            Request Flow
          </div>
          <div className="bg-white dark:bg-black p-6">
            <pre className="font-mono text-xs text-gray-900 dark:text-gray-100 overflow-x-auto">
{`┌─────────────┐
│ Your App    │
└──────┬──────┘
       │
       │ 1. API Request
       │
┌──────▼──────────────────────────────────────────┐
│ Aptly Middleware                                │
│                                                  │
│ ┌────────────────┐      ┌──────────────────┐   │
│ │ PII Detection  │─────▶│ Redaction        │   │
│ └────────────────┘      └──────────────────┘   │
│                                                  │
└──────┬───────────────────────────────────┬──────┘
       │                                   │
       │ 2. Redacted Request              │ 3. Audit Log
       │                                   │
┌──────▼──────┐                    ┌──────▼──────┐
│ LLM Provider│                    │ Database    │
│ (OpenAI)    │                    │ (Immutable) │
└─────────────┘                    └─────────────┘`}
            </pre>
          </div>
        </div>

        <p className="text-gray-600 dark:text-gray-400 mb-4">
          Your application sends requests to Aptly instead of directly to OpenAI/Anthropic/etc.
          Aptly scans for PII, redacts it based on your settings, forwards the clean request to your chosen LLM,
          and logs everything before returning the response.
        </p>
      </section>

      {/* Why Use Aptly */}
      <section className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4 font-mono border-b border-gray-200 dark:border-gray-800 pb-2">
          Why Use Aptly
        </h2>

        <div className="space-y-6 text-gray-600 dark:text-gray-400">
          <div>
            <h3 className="font-bold text-gray-900 dark:text-white mb-2 font-mono">Zero Code Changes</h3>
            <p>
              If you're already using the OpenAI SDK, you only need to change the <code className="bg-gray-100 dark:bg-gray-900 px-2 py-0.5 rounded font-mono text-sm">base_url</code> parameter.
              That's it. No refactoring, no new libraries to learn.
            </p>
          </div>

          <div>
            <h3 className="font-bold text-gray-900 dark:text-white mb-2 font-mono">Compliance Out of the Box</h3>
            <p>
              GDPR requires you to demonstrate "appropriate technical and organizational measures" for data protection.
              Aptly gives you automatic PII redaction and immutable audit logs—the two foundational requirements.
            </p>
          </div>

          <div>
            <h3 className="font-bold text-gray-900 dark:text-white mb-2 font-mono">You Own Your Keys</h3>
            <p>
              Aptly never stores your LLM provider API keys. You pass them per-request, maintaining full control
              and ensuring Aptly can never make unauthorized calls on your behalf.
            </p>
          </div>

          <div>
            <h3 className="font-bold text-gray-900 dark:text-white mb-2 font-mono">Provider Agnostic</h3>
            <p>
              Switch between OpenAI, Anthropic, Google, or Cohere without changing your integration.
              Aptly normalizes the interface so your code stays the same.
            </p>
          </div>
        </div>
      </section>

      {/* Next Steps */}
      <section className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4 font-mono border-b border-gray-200 dark:border-gray-800 pb-2">
          Next Steps
        </h2>

        <div className="grid md:grid-cols-2 gap-4">
          <Link
            href="/docs/quickstart"
            className="border-2 border-gray-200 dark:border-gray-800 hover:border-blue-600 dark:hover:border-blue-400 p-6 transition-colors block"
          >
            <div className="font-bold text-gray-900 dark:text-white mb-2 font-mono">Quickstart →</div>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Get up and running in 5 minutes
            </p>
          </Link>

          <Link
            href="/docs/concepts"
            className="border-2 border-gray-200 dark:border-gray-800 hover:border-blue-600 dark:hover:border-blue-400 p-6 transition-colors block"
          >
            <div className="font-bold text-gray-900 dark:text-white mb-2 font-mono">Key Concepts →</div>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Understand PII modes and compliance
            </p>
          </Link>

          <Link
            href="/docs/guides"
            className="border-2 border-gray-200 dark:border-gray-800 hover:border-blue-600 dark:hover:border-blue-400 p-6 transition-colors block"
          >
            <div className="font-bold text-gray-900 dark:text-white mb-2 font-mono">Common Patterns →</div>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Real-world use cases and examples
            </p>
          </Link>

          <Link
            href="/api-reference"
            className="border-2 border-blue-600 dark:border-blue-400 bg-blue-50 dark:bg-blue-950 p-6 transition-colors block"
          >
            <div className="font-bold text-blue-600 dark:text-blue-400 mb-2 font-mono">API Reference →</div>
            <p className="text-sm text-blue-700 dark:text-blue-300">
              Complete API documentation
            </p>
          </Link>
        </div>
      </section>
    </article>
  )
}
