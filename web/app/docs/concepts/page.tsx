export default function Concepts() {
  return (
    <article className="prose-custom">
      <div className="font-mono text-sm text-blue-600 dark:text-blue-400 mb-6">
        <span className="text-gray-400"># </span>Key Concepts
      </div>

      <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-6 leading-tight">
        Understanding Aptly
      </h1>

      <p className="text-xl text-gray-600 dark:text-gray-400 mb-12 leading-relaxed">
        Core concepts for PII redaction, compliance frameworks, and audit logging.
      </p>

      {/* PII Redaction Modes */}
      <section className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4 font-mono border-b border-gray-200 dark:border-gray-800 pb-2">
          PII Redaction Modes
        </h2>

        <p className="text-gray-600 dark:text-gray-400 mb-6">
          Aptly supports three redaction modes. Configure your account's default mode via the <code className="bg-gray-100 dark:bg-gray-900 px-2 py-0.5 rounded font-mono text-sm">PATCH /v1/me</code> endpoint.
        </p>

        <div className="space-y-1">
          <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-6">
            <div className="flex items-start gap-4">
              <span className="font-mono text-sm text-gray-400 dark:text-gray-600 flex-shrink-0">01</span>
              <div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2 font-mono">
                  mask (Default)
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-3">
                  Replaces PII with labeled placeholders. Best for maintaining context while protecting data.
                </p>
                <div className="border border-gray-300 dark:border-gray-800">
                  <div className="bg-gray-100 dark:bg-gray-900 px-4 py-2 border-b border-gray-300 dark:border-gray-800 font-mono text-xs text-gray-600 dark:text-gray-400">
                    Example
                  </div>
                  <div className="bg-white dark:bg-black p-4">
                    <div className="font-mono text-sm space-y-2">
                      <div>
                        <span className="text-gray-500">Input:</span> <span className="text-gray-900 dark:text-gray-100">"Contact John Smith at john@acme.com"</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Output:</span> <span className="text-gray-900 dark:text-gray-100">"Contact PERSON_A at EMAIL_ADDRESS_A"</span>
                      </div>
                    </div>
                  </div>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-3">
                  ✓ Preserves sentence structure<br />
                  ✓ LLM can still understand relationships<br />
                  ✓ Best for most use cases
                </p>
              </div>
            </div>
          </div>

          <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-6">
            <div className="flex items-start gap-4">
              <span className="font-mono text-sm text-gray-400 dark:text-gray-600 flex-shrink-0">02</span>
              <div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2 font-mono">
                  hash
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-3">
                  Replaces PII with deterministic hashes. Same value always gets the same hash.
                </p>
                <div className="border border-gray-300 dark:border-gray-800">
                  <div className="bg-gray-100 dark:bg-gray-900 px-4 py-2 border-b border-gray-300 dark:border-gray-800 font-mono text-xs text-gray-600 dark:text-gray-400">
                    Example
                  </div>
                  <div className="bg-white dark:bg-black p-4">
                    <div className="font-mono text-sm space-y-2">
                      <div>
                        <span className="text-gray-500">Input:</span> <span className="text-gray-900 dark:text-gray-100">"John Smith called, John Smith left a message"</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Output:</span> <span className="text-gray-900 dark:text-gray-100">"HASH_a3f2c1b9 called, HASH_a3f2c1b9 left a message"</span>
                      </div>
                    </div>
                  </div>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-3">
                  ✓ Maintains consistency across requests<br />
                  ✓ Can track entities without revealing identity<br />
                  ✓ Good for analytics use cases
                </p>
              </div>
            </div>
          </div>

          <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-6">
            <div className="flex items-start gap-4">
              <span className="font-mono text-sm text-gray-400 dark:text-gray-600 flex-shrink-0">03</span>
              <div>
                <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2 font-mono">
                  remove
                </h3>
                <p className="text-gray-600 dark:text-gray-400 mb-3">
                  Completely removes PII from the text. Most secure but may lose context.
                </p>
                <div className="border border-gray-300 dark:border-gray-800">
                  <div className="bg-gray-100 dark:bg-gray-900 px-4 py-2 border-b border-gray-300 dark:border-gray-800 font-mono text-xs text-gray-600 dark:text-gray-400">
                    Example
                  </div>
                  <div className="bg-white dark:bg-black p-4">
                    <div className="font-mono text-sm space-y-2">
                      <div>
                        <span className="text-gray-500">Input:</span> <span className="text-gray-900 dark:text-gray-100">"Contact John Smith at john@acme.com"</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Output:</span> <span className="text-gray-900 dark:text-gray-100">"Contact [REDACTED] at [REDACTED]"</span>
                      </div>
                    </div>
                  </div>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-3">
                  ✓ Maximum data protection<br />
                  ✓ Best for highly sensitive data<br />
                  ⚠ May reduce LLM usefulness
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Detected PII Types */}
      <section className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4 font-mono border-b border-gray-200 dark:border-gray-800 pb-2">
          Detected PII Types
        </h2>

        <p className="text-gray-600 dark:text-gray-400 mb-6">
          Aptly uses Microsoft Presidio to detect these PII entity types:
        </p>

        <div className="grid md:grid-cols-2 gap-1">
          <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-4">
            <ul className="space-y-2 text-sm font-mono">
              <li className="text-gray-900 dark:text-gray-100">• PERSON (Names)</li>
              <li className="text-gray-900 dark:text-gray-100">• EMAIL_ADDRESS</li>
              <li className="text-gray-900 dark:text-gray-100">• PHONE_NUMBER</li>
              <li className="text-gray-900 dark:text-gray-100">• US_SSN</li>
              <li className="text-gray-900 dark:text-gray-100">• CREDIT_CARD</li>
            </ul>
          </div>
          <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-4">
            <ul className="space-y-2 text-sm font-mono">
              <li className="text-gray-900 dark:text-gray-100">• US_DRIVER_LICENSE</li>
              <li className="text-gray-900 dark:text-gray-100">• US_PASSPORT</li>
              <li className="text-gray-900 dark:text-gray-100">• IP_ADDRESS</li>
              <li className="text-gray-900 dark:text-gray-100">• LOCATION</li>
              <li className="text-gray-900 dark:text-gray-100">• DATE_TIME</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Compliance Frameworks */}
      <section className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4 font-mono border-b border-gray-200 dark:border-gray-800 pb-2">
          Compliance Frameworks
        </h2>

        <p className="text-gray-600 dark:text-gray-400 mb-6">
          Tag your account with compliance frameworks to organize audit logs and demonstrate regulatory compliance.
        </p>

        <div className="space-y-1">
          <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-xl">🇪🇺</span>
                <div>
                  <div className="font-bold text-gray-900 dark:text-white font-mono">GDPR</div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">General Data Protection Regulation (EU)</p>
                </div>
              </div>
            </div>
          </div>

          <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-xl">🏥</span>
                <div>
                  <div className="font-bold text-gray-900 dark:text-white font-mono">HIPAA</div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Health Insurance Portability and Accountability Act (US)</p>
                </div>
              </div>
            </div>
          </div>

          <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-xl">🔒</span>
                <div>
                  <div className="font-bold text-gray-900 dark:text-white font-mono">SOC 2</div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">System and Organization Controls Type 2</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Audit Logs */}
      <section className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4 font-mono border-b border-gray-200 dark:border-gray-800 pb-2">
          Audit Logs
        </h2>

        <p className="text-gray-600 dark:text-gray-400 mb-6">
          Every API request creates an immutable audit log entry with:
        </p>

        <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-6">
          <ul className="space-y-3 text-gray-600 dark:text-gray-400">
            <li className="flex items-start gap-3">
              <span className="text-blue-600 dark:text-blue-400">✓</span>
              <div>
                <strong className="text-gray-900 dark:text-white">Timestamp:</strong> Exact date/time of request
              </div>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-blue-600 dark:text-blue-400">✓</span>
              <div>
                <strong className="text-gray-900 dark:text-white">PII Detections:</strong> Which PII types were found and how they were redacted
              </div>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-blue-600 dark:text-blue-400">✓</span>
              <div>
                <strong className="text-gray-900 dark:text-white">Provider & Model:</strong> Which LLM was called (e.g., "openai/gpt-4")
              </div>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-blue-600 dark:text-blue-400">✓</span>
              <div>
                <strong className="text-gray-900 dark:text-white">Token Usage:</strong> Input/output tokens and cost
              </div>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-blue-600 dark:text-blue-400">✓</span>
              <div>
                <strong className="text-gray-900 dark:text-white">User ID:</strong> Optional end-user identifier for tracking
              </div>
            </li>
            <li className="flex items-start gap-3">
              <span className="text-blue-600 dark:text-blue-400">✓</span>
              <div>
                <strong className="text-gray-900 dark:text-white">Request/Response Data:</strong> Full messages (with PII already redacted)
              </div>
            </li>
          </ul>
        </div>

        <div className="bg-blue-50 dark:bg-blue-950 border-l-4 border-blue-600 dark:border-blue-400 p-4 mt-6">
          <p className="text-sm text-blue-900 dark:text-blue-100">
            <strong className="font-mono">Database Trigger:</strong> Audit logs are enforced immutable at the database level.
            Even with service role access, modification and deletion are prevented via PostgreSQL triggers.
          </p>
        </div>
      </section>

      {/* Data Retention */}
      <section className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4 font-mono border-b border-gray-200 dark:border-gray-800 pb-2">
          Data Retention
        </h2>

        <p className="text-gray-600 dark:text-gray-400 mb-4">
          Audit logs are retained based on your plan:
        </p>

        <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
              <tr>
                <th className="px-4 py-3 text-left font-mono text-sm text-gray-900 dark:text-white">Plan</th>
                <th className="px-4 py-3 text-left font-mono text-sm text-gray-900 dark:text-white">Retention</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
              <tr>
                <td className="px-4 py-3 font-mono text-sm text-gray-900 dark:text-gray-100">Free</td>
                <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">30 days</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-sm text-gray-900 dark:text-gray-100">Pro</td>
                <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">1 year</td>
              </tr>
              <tr>
                <td className="px-4 py-3 font-mono text-sm text-gray-900 dark:text-gray-100">Enterprise</td>
                <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">7 years (configurable)</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </article>
  )
}
