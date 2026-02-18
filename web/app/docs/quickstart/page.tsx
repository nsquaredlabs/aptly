import Link from 'next/link'

export default function Quickstart() {
  return (
    <article className="prose-custom">
      <div className="font-mono text-sm text-blue-600 dark:text-blue-400 mb-6">
        <span className="text-gray-400"># </span>Quickstart
      </div>

      <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-6 leading-tight">
        Get Started in 5 Minutes
      </h1>

      <p className="text-xl text-gray-600 dark:text-gray-400 mb-12 leading-relaxed">
        This guide walks you through creating an account, making your first API call,
        and verifying that PII is being redacted.
      </p>

      {/* Step 1 */}
      <section className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4 font-mono border-b border-gray-200 dark:border-gray-800 pb-2">
          Step 1: Get Your API Key
        </h2>

        <p className="text-gray-600 dark:text-gray-400 mb-4">
          Contact us to create your account and receive your Aptly API key:
        </p>

        <div className="border border-gray-300 dark:border-gray-800">
          <div className="bg-gray-100 dark:bg-gray-900 px-4 py-2 border-b border-gray-300 dark:border-gray-800 font-mono text-xs text-gray-600 dark:text-gray-400">
            Expected Response
          </div>
          <div className="bg-white dark:bg-black p-6">
            <pre className="font-mono text-sm text-gray-900 dark:text-gray-100 overflow-x-auto">
{`{
  "customer": {
    "id": "cus_abc123",
    "email": "you@company.com",
    "plan": "pro"
  },
  "api_key": {
    "key": "apt_live_xyz789...",
    "rate_limit_per_hour": 10000
  }
}`}
            </pre>
          </div>
        </div>

        <div className="bg-blue-50 dark:bg-blue-950 border-l-4 border-blue-600 dark:border-blue-400 p-4 mt-4">
          <p className="text-sm text-blue-900 dark:text-blue-100">
            <strong className="font-mono">Note:</strong> Save your API key securely. It won't be shown again.
          </p>
        </div>
      </section>

      {/* Step 2 */}
      <section className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4 font-mono border-b border-gray-200 dark:border-gray-800 pb-2">
          Step 2: Make Your First Request
        </h2>

        <p className="text-gray-600 dark:text-gray-400 mb-4">
          If you're already using the OpenAI SDK, the change is trivial—just update the <code className="bg-gray-100 dark:bg-gray-900 px-2 py-0.5 rounded font-mono text-sm">base_url</code>:
        </p>

        <div className="border border-gray-300 dark:border-gray-800 mb-6">
          <div className="bg-gray-100 dark:bg-gray-900 px-4 py-2 border-b border-gray-300 dark:border-gray-800 font-mono text-xs text-gray-600 dark:text-gray-400">
            Python
          </div>
          <div className="bg-white dark:bg-black p-6">
            <pre className="font-mono text-sm text-gray-900 dark:text-gray-100 overflow-x-auto">
{`from openai import OpenAI

client = OpenAI(
    base_url="https://aptly-api.nsquaredlabs.com/v1",
    api_key="apt_live_your_key_here"
)

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{
        "role": "user",
        "content": "My email is john.doe@example.com and my SSN is 123-45-6789"
    }],
    # Pass your OpenAI key in the request
    extra_body={
        "api_keys": {
            "openai": "sk-your-openai-key"
        }
    }
)

print(response.choices[0].message.content)
print(response.aptly.pii_detected)  # True
print(response.aptly.pii_entities)  # ['EMAIL_ADDRESS', 'US_SSN']`}
            </pre>
          </div>
        </div>

        <div className="border border-gray-300 dark:border-gray-800">
          <div className="bg-gray-100 dark:bg-gray-900 px-4 py-2 border-b border-gray-300 dark:border-gray-800 font-mono text-xs text-gray-600 dark:text-gray-400">
            JavaScript/TypeScript
          </div>
          <div className="bg-white dark:bg-black p-6">
            <pre className="font-mono text-sm text-gray-900 dark:text-gray-100 overflow-x-auto">
{`import OpenAI from 'openai';

const client = new OpenAI({
  baseURL: 'https://aptly-api.nsquaredlabs.com/v1',
  apiKey: 'apt_live_your_key_here',
});

const response = await client.chat.completions.create({
  model: 'gpt-4',
  messages: [{
    role: 'user',
    content: 'My email is john.doe@example.com and my SSN is 123-45-6789'
  }],
  // Pass your OpenAI key in the request
  api_keys: {
    openai: 'sk-your-openai-key'
  }
});

console.log(response.choices[0].message.content);
console.log(response.aptly.pii_detected);  // true
console.log(response.aptly.pii_entities);  // ['EMAIL_ADDRESS', 'US_SSN']`}
            </pre>
          </div>
        </div>
      </section>

      {/* Step 3 */}
      <section className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4 font-mono border-b border-gray-200 dark:border-gray-800 pb-2">
          Step 3: Verify PII Redaction
        </h2>

        <p className="text-gray-600 dark:text-gray-400 mb-4">
          The response includes metadata about what PII was detected and redacted:
        </p>

        <div className="border border-gray-300 dark:border-gray-800">
          <div className="bg-gray-100 dark:bg-gray-900 px-4 py-2 border-b border-gray-300 dark:border-gray-800 font-mono text-xs text-gray-600 dark:text-gray-400">
            Response Metadata
          </div>
          <div className="bg-white dark:bg-black p-6">
            <pre className="font-mono text-sm text-gray-900 dark:text-gray-100 overflow-x-auto">
{`{
  "aptly": {
    "audit_log_id": "log_abc123",
    "pii_detected": true,
    "pii_entities": ["EMAIL_ADDRESS", "US_SSN"],
    "response_pii_detected": false,
    "response_pii_entities": [],
    "compliance_framework": "gdpr",
    "latency_ms": 245
  }
}`}
            </pre>
          </div>
        </div>

        <p className="text-gray-600 dark:text-gray-400 mt-4">
          What actually got sent to OpenAI (with default <code className="bg-gray-100 dark:bg-gray-900 px-2 py-0.5 rounded font-mono text-sm">mask</code> mode):
        </p>

        <div className="border border-gray-300 dark:border-gray-800 mt-4">
          <div className="bg-white dark:bg-black p-6">
            <pre className="font-mono text-sm text-gray-900 dark:text-gray-100 overflow-x-auto">
{`"My email is EMAIL_ADDRESS_A and my SSN is US_SSN_A"`}
            </pre>
          </div>
        </div>
      </section>

      {/* Step 4 */}
      <section className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4 font-mono border-b border-gray-200 dark:border-gray-800 pb-2">
          Step 4: Check Your Audit Logs
        </h2>

        <p className="text-gray-600 dark:text-gray-400 mb-4">
          Every request creates an immutable audit log entry. Query your logs via the API:
        </p>

        <div className="border border-gray-300 dark:border-gray-800">
          <div className="bg-gray-100 dark:bg-gray-900 px-4 py-2 border-b border-gray-300 dark:border-gray-800 font-mono text-xs text-gray-600 dark:text-gray-400">
            curl
          </div>
          <div className="bg-white dark:bg-black p-6">
            <pre className="font-mono text-sm text-gray-900 dark:text-gray-100 overflow-x-auto">
{`curl https://aptly-api.nsquaredlabs.com/v1/logs \\
  -H "Authorization: Bearer apt_live_your_key_here"`}
            </pre>
          </div>
        </div>

        <p className="text-gray-600 dark:text-gray-400 mt-4">
          The response includes all your logged requests with PII detection details, timestamps, and costs.
        </p>
      </section>

      {/* What's Next */}
      <section className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4 font-mono border-b border-gray-200 dark:border-gray-800 pb-2">
          What's Next
        </h2>

        <div className="space-y-4">
          <Link
            href="/docs/concepts"
            className="border border-gray-200 dark:border-gray-800 hover:border-blue-600 dark:hover:border-blue-400 p-4 transition-colors block"
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="font-bold text-gray-900 dark:text-white font-mono">Configure PII Redaction Modes</div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Learn about mask, hash, and remove modes
                </p>
              </div>
              <span className="text-blue-600 dark:text-blue-400">→</span>
            </div>
          </Link>

          <Link
            href="/docs/guides"
            className="border border-gray-200 dark:border-gray-800 hover:border-blue-600 dark:hover:border-blue-400 p-4 transition-colors block"
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="font-bold text-gray-900 dark:text-white font-mono">See Common Patterns</div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Real-world examples and use cases
                </p>
              </div>
              <span className="text-blue-600 dark:text-blue-400">→</span>
            </div>
          </Link>

          <Link
            href="/api-reference"
            className="border-2 border-blue-600 dark:border-blue-400 bg-blue-50 dark:bg-blue-950 p-4 transition-colors block"
          >
            <div className="flex items-center justify-between">
              <div>
                <div className="font-bold text-blue-600 dark:text-blue-400 font-mono">Explore the Full API</div>
                <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                  Complete API reference with all endpoints
                </p>
              </div>
              <span className="text-blue-600 dark:text-blue-400">→</span>
            </div>
          </Link>
        </div>
      </section>
    </article>
  )
}
