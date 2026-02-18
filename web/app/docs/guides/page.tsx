export default function Guides() {
  return (
    <article className="prose-custom">
      <div className="font-mono text-sm text-blue-600 dark:text-blue-400 mb-6">
        <span className="text-gray-400"># </span>Common Patterns
      </div>

      <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-6 leading-tight">
        Real-World Use Cases
      </h1>

      <p className="text-xl text-gray-600 dark:text-gray-400 mb-12 leading-relaxed">
        Practical examples of how to use Aptly in production applications.
      </p>

      {/* Pattern 1: Customer Support Chatbot */}
      <section className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4 font-mono border-b border-gray-200 dark:border-gray-800 pb-2">
          Customer Support Chatbot
        </h2>

        <p className="text-gray-600 dark:text-gray-400 mb-4">
          A chatbot that handles customer inquiries may receive PII like names, emails, and phone numbers.
          Aptly ensures this data never reaches your LLM provider.
        </p>

        <div className="border border-gray-300 dark:border-gray-800 mb-4">
          <div className="bg-gray-100 dark:bg-gray-900 px-4 py-2 border-b border-gray-300 dark:border-gray-800 font-mono text-xs text-gray-600 dark:text-gray-400">
            Example
          </div>
          <div className="bg-white dark:bg-black p-6">
            <pre className="font-mono text-sm text-gray-900 dark:text-gray-100 overflow-x-auto">
{`response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful support agent."},
        {"role": "user", "content": user_message}
    ],
    user=user_id,  # Track which end-user made the request
    extra_body={
        "api_keys": {"openai": openai_key},
        "redact_response": True  # Also redact PII from LLM's response
    }
)

# Aptly automatically:
# - Redacts PII from user_message before sending to OpenAI
# - Logs the request with user_id for tracking
# - Optionally redacts PII from the response`}
            </pre>
          </div>
        </div>

        <div className="bg-blue-50 dark:bg-blue-950 border-l-4 border-blue-600 dark:border-blue-400 p-4">
          <p className="text-sm text-blue-900 dark:text-blue-100">
            <strong>Best Practice:</strong> Pass the <code className="bg-blue-100 dark:bg-blue-900 px-1.5 py-0.5 rounded font-mono">user</code> parameter
            to track which end-user made each request. This appears in audit logs and analytics.
          </p>
        </div>
      </section>

      {/* Pattern 2: Document Summarization */}
      <section className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4 font-mono border-b border-gray-200 dark:border-gray-800 pb-2">
          Document Summarization
        </h2>

        <p className="text-gray-600 dark:text-gray-400 mb-4">
          Summarizing legal documents, contracts, or medical records that contain names, addresses, and other PII.
        </p>

        <div className="border border-gray-300 dark:border-gray-800 mb-4">
          <div className="bg-gray-100 dark:bg-gray-900 px-4 py-2 border-b border-gray-300 dark:border-gray-800 font-mono text-xs text-gray-600 dark:text-gray-400">
            Example
          </div>
          <div className="bg-white dark:bg-black p-6">
            <pre className="font-mono text-sm text-gray-900 dark:text-gray-100 overflow-x-auto">
{`# Read a document containing PII
with open("contract.txt") as f:
    document = f.read()

response = client.chat.completions.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{
        "role": "user",
        "content": "Summarize this contract: " + document
    }],
    extra_body={
        "api_keys": {"anthropic": anthropic_key}
    }
)

summary = response.choices[0].message.content

# The summary will reference "PERSON_A" instead of actual names
# Original PII never left your infrastructure`}
            </pre>
          </div>
        </div>

        <p className="text-gray-600 dark:text-gray-400">
          Because Aptly uses <code className="bg-gray-100 dark:bg-gray-900 px-2 py-0.5 rounded font-mono text-sm">mask</code> mode by default,
          the LLM can still understand relationships while your compliance team knows no real names were sent.
        </p>
      </section>

      {/* Pattern 3: Streaming */}
      <section className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4 font-mono border-b border-gray-200 dark:border-gray-800 pb-2">
          Streaming Responses
        </h2>

        <p className="text-gray-600 dark:text-gray-400 mb-4">
          Stream LLM responses while still protecting PII. The audit log is created when the stream completes.
        </p>

        <div className="border border-gray-300 dark:border-gray-800 mb-4">
          <div className="bg-gray-100 dark:bg-gray-900 px-4 py-2 border-b border-gray-300 dark:border-gray-800 font-mono text-xs text-gray-600 dark:text-gray-400">
            Example
          </div>
          <div className="bg-white dark:bg-black p-6">
            <pre className="font-mono text-sm text-gray-900 dark:text-gray-100 overflow-x-auto">
{`stream = client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    stream=True,
    extra_body={"api_keys": {"openai": openai_key}}
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")

    # The final chunk includes Aptly metadata
    if hasattr(chunk, 'aptly'):
        print("PII detected:", chunk.aptly['pii_detected'])
        print("Audit log:", chunk.aptly['audit_log_id'])`}
            </pre>
          </div>
        </div>

        <p className="text-gray-600 dark:text-gray-400">
          PII is still redacted before streaming begins. The audit log is written when the stream completes.
        </p>
      </section>

      {/* Pattern 4: Analytics */}
      <section className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4 font-mono border-b border-gray-200 dark:border-gray-800 pb-2">
          Analytics & Cost Tracking
        </h2>

        <p className="text-gray-600 dark:text-gray-400 mb-4">
          Track LLM usage, costs, and PII detection rates across your application.
        </p>

        <div className="border border-gray-300 dark:border-gray-800 mb-4">
          <div className="bg-gray-100 dark:bg-gray-900 px-4 py-2 border-b border-gray-300 dark:border-gray-800 font-mono text-xs text-gray-600 dark:text-gray-400">
            Example
          </div>
          <div className="bg-white dark:bg-black p-6">
            <pre className="font-mono text-sm text-gray-900 dark:text-gray-100 overflow-x-auto">
{`# Get usage summary for the last 30 days
usage = requests.get(
    "https://api-aptly.nsquaredlabs.com/v1/analytics/usage",
    headers={"Authorization": "Bearer " + aptly_key},
    params={"granularity": "day"}
).json()

print("Total requests:", usage['summary']['total_requests'])
print("Total cost:", usage['summary']['total_cost_usd'])

# Get PII detection stats
pii_stats = requests.get(
    "https://api-aptly.nsquaredlabs.com/v1/analytics/pii",
    headers={"Authorization": "Bearer " + aptly_key}
).json()

print("Requests with PII:", pii_stats['summary']['requests_with_input_pii'])
print("PII detection rate:", pii_stats['summary']['input_pii_rate'])`}
            </pre>
          </div>
        </div>

        <p className="text-gray-600 dark:text-gray-400">
          Use the analytics endpoints to understand your LLM usage patterns and demonstrate compliance to auditors.
        </p>
      </section>
    </article>
  )
}
