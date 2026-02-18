export default function FAQ() {
  return (
    <article className="prose-custom">
      <div className="font-mono text-sm text-blue-600 dark:text-blue-400 mb-6">
        <span className="text-gray-400"># </span>FAQ
      </div>

      <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-6 leading-tight">
        Frequently Asked Questions
      </h1>

      <p className="text-xl text-gray-600 dark:text-gray-400 mb-12 leading-relaxed">
        Common questions about Aptly's functionality, security, and compliance.
      </p>

      {/* General */}
      <section className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6 font-mono border-b border-gray-200 dark:border-gray-800 pb-2">
          General
        </h2>

        <div className="space-y-6">
          <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-6">
            <h3 className="font-bold text-gray-900 dark:text-white mb-3 font-mono">
              Does Aptly slow down my API requests?
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Minimal overhead (~50-100ms for PII scanning). The bulk of latency comes from the LLM provider itself.
              We use Microsoft Presidio for fast, local PII detection—no additional API calls required.
            </p>
          </div>

          <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-6">
            <h3 className="font-bold text-gray-900 dark:text-white mb-3 font-mono">
              Can I use Aptly with my existing OpenAI/Anthropic code?
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Yes! Just change the <code className="bg-gray-100 dark:bg-gray-900 px-2 py-0.5 rounded font-mono text-sm">base_url</code> to Aptly's endpoint.
              Everything else stays the same.
            </p>
          </div>

          <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-6">
            <h3 className="font-bold text-gray-900 dark:text-white mb-3 font-mono">
              Which LLM providers does Aptly support?
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-2">
              Aptly uses LiteLLM under the hood, so it supports 100+ providers including:
            </p>
            <ul className="list-disc list-inside text-gray-600 dark:text-gray-400 space-y-1 ml-4">
              <li>OpenAI (GPT-4, GPT-3.5)</li>
              <li>Anthropic (Claude 3.5 Sonnet, Opus, Haiku)</li>
              <li>Google (Gemini 1.5 Pro, Flash)</li>
              <li>Cohere (Command R+)</li>
              <li>Together AI (Llama 3.1, Mixtral)</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Security & Privacy */}
      <section className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6 font-mono border-b border-gray-200 dark:border-gray-800 pb-2">
          Security & Privacy
        </h2>

        <div className="space-y-6">
          <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-6">
            <h3 className="font-bold text-gray-900 dark:text-white mb-3 font-mono">
              Does Aptly store my LLM provider API keys?
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              No. You pass your provider keys per-request in the <code className="bg-gray-100 dark:bg-gray-900 px-2 py-0.5 rounded font-mono text-sm">api_keys</code> field.
              Aptly never persists them. This "customer-provided keys" model ensures you maintain full control.
            </p>
          </div>

          <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-6">
            <h3 className="font-bold text-gray-900 dark:text-white mb-3 font-mono">
              Are audit logs truly immutable?
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Yes. We use PostgreSQL database triggers to prevent modification or deletion of audit log entries,
              even with service role access. This satisfies regulatory requirements for immutable audit trails.
            </p>
          </div>

          <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-6">
            <h3 className="font-bold text-gray-900 dark:text-white mb-3 font-mono">
              What happens to the original (unredacted) data?
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              The original request is never stored. Audit logs only contain the <em>redacted</em> version that was sent to the LLM.
              Original PII never leaves your request and is never persisted by Aptly.
            </p>
          </div>

          <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-6">
            <h3 className="font-bold text-gray-900 dark:text-white mb-3 font-mono">
              Can Aptly guarantee the LLM provider won't see PII?
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Aptly redacts detected PII before forwarding to the LLM. However, PII detection is probabilistic—no system is 100% accurate.
              We use Microsoft Presidio (industry standard) and achieve high accuracy, but you should still review your compliance requirements.
            </p>
          </div>
        </div>
      </section>

      {/* Compliance */}
      <section className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6 font-mono border-b border-gray-200 dark:border-gray-800 pb-2">
          Compliance
        </h2>

        <div className="space-y-6">
          <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-6">
            <h3 className="font-bold text-gray-900 dark:text-white mb-3 font-mono">
              Does Aptly make me GDPR compliant?
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Aptly provides two foundational controls—automatic PII redaction and immutable audit logs—but GDPR compliance
              requires more than technology. You still need data processing agreements, privacy policies, user consent mechanisms, etc.
              Aptly significantly reduces risk but doesn't replace a full compliance program.
            </p>
          </div>

          <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-6">
            <h3 className="font-bold text-gray-900 dark:text-white mb-3 font-mono">
              Can I use Aptly for HIPAA-covered data?
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Aptly can be part of a HIPAA compliance strategy (we detect health-related PII), but you'll need a Business Associate Agreement (BAA)
              with both Aptly and your LLM provider. Contact us to discuss HIPAA requirements.
            </p>
          </div>

          <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-6">
            <h3 className="font-bold text-gray-900 dark:text-white mb-3 font-mono">
              How long are audit logs retained?
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Retention periods vary by plan: 30 days (Free), 1 year (Pro), 7 years (Enterprise, configurable).
              After the retention period, logs are automatically purged.
            </p>
          </div>
        </div>
      </section>

      {/* Billing & Limits */}
      <section className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6 font-mono border-b border-gray-200 dark:border-gray-800 pb-2">
          Billing & Limits
        </h2>

        <div className="space-y-6">
          <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-6">
            <h3 className="font-bold text-gray-900 dark:text-white mb-3 font-mono">
              Does Aptly charge for LLM usage?
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              No. You pay your LLM provider directly (via your own API keys). Aptly charges only for the compliance middleware service.
            </p>
          </div>

          <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-6">
            <h3 className="font-bold text-gray-900 dark:text-white mb-3 font-mono">
              What are the rate limits?
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Free tier: 100 requests/hour. Pro tier: 10,000 requests/hour. Enterprise: Custom limits.
              Rate limits are enforced per customer, not per API key.
            </p>
          </div>

          <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-6">
            <h3 className="font-bold text-gray-900 dark:text-white mb-3 font-mono">
              What happens if I exceed my rate limit?
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              You'll receive a <code className="bg-gray-100 dark:bg-gray-900 px-2 py-0.5 rounded font-mono text-sm">429 Too Many Requests</code> response
              with a <code className="bg-gray-100 dark:bg-gray-900 px-2 py-0.5 rounded font-mono text-sm">Retry-After</code> header indicating when you can try again.
            </p>
          </div>
        </div>
      </section>

      {/* Technical */}
      <section className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6 font-mono border-b border-gray-200 dark:border-gray-800 pb-2">
          Technical
        </h2>

        <div className="space-y-6">
          <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-6">
            <h3 className="font-bold text-gray-900 dark:text-white mb-3 font-mono">
              Does Aptly support streaming responses?
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Yes. Set <code className="bg-gray-100 dark:bg-gray-900 px-2 py-0.5 rounded font-mono text-sm">stream=True</code> and you'll receive
              server-sent events just like with OpenAI. The audit log is created when the stream completes.
            </p>
          </div>

          <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-6">
            <h3 className="font-bold text-gray-900 dark:text-white mb-3 font-mono">
              Can I customize which PII types to detect?
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Not currently. Aptly detects all standard PII types (SSN, email, phone, credit card, etc.) by default.
              Custom entity detection is on the roadmap for Enterprise plans.
            </p>
          </div>

          <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-6">
            <h3 className="font-bold text-gray-900 dark:text-white mb-3 font-mono">
              Can I self-host Aptly?
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Yes, for Enterprise customers. Contact us to discuss on-premise deployment options.
            </p>
          </div>

          <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-6">
            <h3 className="font-bold text-gray-900 dark:text-white mb-3 font-mono">
              What's the difference between masking and hashing?
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              <strong>Masking</strong> (<code className="bg-gray-100 dark:bg-gray-900 px-2 py-0.5 rounded font-mono text-sm">PERSON_A</code>) preserves
              entity type and makes text readable. <strong>Hashing</strong> (<code className="bg-gray-100 dark:bg-gray-900 px-2 py-0.5 rounded font-mono text-sm">HASH_a3f2c1b9</code>) is
              deterministic—the same value always gets the same hash, useful for tracking entities across requests without revealing identity.
            </p>
          </div>
        </div>
      </section>

      {/* Still have questions? */}
      <section className="mb-12">
        <div className="border-2 border-blue-600 dark:border-blue-400 bg-blue-50 dark:bg-blue-950 p-8 text-center">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-3 font-mono">
            Still have questions?
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Check out the full API reference or contact us directly.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="/api-reference"
              className="px-6 py-3 bg-blue-600 text-white font-mono font-semibold hover:bg-blue-700 transition-colors inline-block"
            >
              API Reference
            </a>
            <a
              href="mailto:support@nsquaredlabs.com"
              className="px-6 py-3 border-2 border-blue-600 dark:border-blue-400 text-blue-600 dark:text-blue-400 font-mono font-semibold hover:bg-blue-600 hover:text-white transition-colors inline-block"
            >
              Contact Support
            </a>
          </div>
        </div>
      </section>
    </article>
  )
}
