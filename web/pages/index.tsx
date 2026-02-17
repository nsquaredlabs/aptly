import React from 'react'
import Link from 'next/link'

export default function Home() {
  return (
    <div className="min-h-screen bg-white dark:bg-black">
      {/* Header */}
      <header className="border-b border-gray-200 dark:border-gray-800">
        <nav className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-blue-600 dark:text-blue-400 text-xl">$</span>
            <span className="text-xl font-mono font-bold text-gray-900 dark:text-white">aptly</span>
          </div>
          <div className="flex gap-6 font-mono text-sm">
            <Link
              href="/docs"
              className="text-gray-600 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400 transition-colors"
            >
              ./docs
            </Link>
          </div>
        </nav>
      </header>

      <main>
        {/* 1. HERO */}
        <section className="container mx-auto px-6 py-20 md:py-32">
          <div className="max-w-4xl mx-auto">
            {/* Eyebrow */}
            <div className="font-mono text-sm text-blue-600 dark:text-blue-400 mb-6">
              <span className="text-gray-400"># </span>Compliance-as-a-Service
            </div>

            {/* Headline */}
            <h1 className="text-5xl md:text-7xl font-bold text-gray-900 dark:text-white mb-6 leading-tight">
              Use AI Without
              <br />
              Leaking PII
            </h1>

            {/* Subheadline */}
            <p className="text-xl md:text-2xl text-gray-600 dark:text-gray-400 mb-10 max-w-3xl leading-relaxed">
              Drop-in API that automatically redacts sensitive data and logs every request.
              <br className="hidden md:block" />
              Stay compliant while using any LLM.
            </p>

            {/* CTA */}
            <div className="flex flex-col sm:flex-row gap-4 mb-12">
              <Link
                href="/docs/quickstart"
                className="px-8 py-4 bg-blue-600 text-white font-mono font-semibold hover:bg-blue-700 transition-colors border-2 border-blue-600"
              >
                Get Started
              </Link>
              <Link
                href="/docs/api-reference"
                className="px-8 py-4 border-2 border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-300 font-mono font-semibold hover:border-blue-600 dark:hover:border-blue-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
              >
                API Reference
              </Link>
            </div>

            {/* Trust Signals */}
            <div className="flex flex-wrap gap-6 text-sm font-mono text-gray-500 dark:text-gray-500">
              <div className="flex items-center gap-2">
                <span className="text-blue-600 dark:text-blue-400">✓</span>
                <span>OpenAI Compatible</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-blue-600 dark:text-blue-400">✓</span>
                <span>GDPR & SOC 2 Ready</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-blue-600 dark:text-blue-400">✓</span>
                <span>5 Minute Setup</span>
              </div>
            </div>
          </div>
        </section>

        {/* Code Preview */}
        <section className="container mx-auto px-6 pb-20">
          <div className="max-w-4xl mx-auto">
            <div className="border border-gray-300 dark:border-gray-800">
              {/* Terminal header */}
              <div className="bg-gray-100 dark:bg-gray-900 px-4 py-2 border-b border-gray-300 dark:border-gray-800 font-mono text-xs text-gray-600 dark:text-gray-400">
                <span className="text-blue-600 dark:text-blue-400">~/aptly</span> $ python example.py
              </div>
              {/* Code */}
              <div className="bg-white dark:bg-black p-6 overflow-x-auto">
                <pre className="font-mono text-sm text-gray-900 dark:text-gray-100">
                  <code>{`from openai import OpenAI

client = OpenAI(
  base_url="https://aptly-api.nsquaredlabs.com/v1",
  api_key="apt_live_your_key_here"
)

response = client.chat.completions.create(
  model="gpt-4",
  messages=[{
    "role": "user",
    "content": "My email is john@example.com"
  }]
)

# ✓ PII automatically redacted before sending to OpenAI
# ✓ Complete audit trail logged
# ✓ Zero code changes required`}</code>
                </pre>
              </div>
            </div>
          </div>
        </section>

        {/* 3. PROBLEM-AGITATE */}
        <section className="bg-gray-50 dark:bg-gray-950 border-y border-gray-200 dark:border-gray-900 py-20">
          <div className="container mx-auto px-6">
            <div className="max-w-4xl mx-auto">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">
                The AI Compliance Problem
              </h2>
              <p className="text-xl text-gray-600 dark:text-gray-400 mb-16 font-mono text-sm">
                // Using AI in production means exposing your data to third-party APIs
              </p>

              <div className="space-y-1">
                {/* Problem 1 */}
                <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-6">
                  <div className="flex items-start gap-4">
                    <span className="font-mono text-sm text-gray-400 dark:text-gray-600 flex-shrink-0">01</span>
                    <div>
                      <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2 font-mono">
                        71% of organizations struggle with cross-border data compliance
                      </h3>
                      <p className="text-gray-600 dark:text-gray-400">
                        Every time you send a request to OpenAI, Anthropic, or any LLM provider, you're transferring data across borders.
                        One leaked SSN, credit card, or health record could trigger GDPR fines up to €20M or 4% of revenue.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Problem 2 */}
                <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-6">
                  <div className="flex items-start gap-4">
                    <span className="font-mono text-sm text-gray-400 dark:text-gray-600 flex-shrink-0">02</span>
                    <div>
                      <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2 font-mono">
                        PII sent to AI tools may be retained, logged, or reused for training
                      </h3>
                      <p className="text-gray-600 dark:text-gray-400">
                        Third-party AI APIs don't guarantee deletion. Your customer data could end up in training datasets,
                        server logs, or exposed through prompt injection attacks. Italy just fined OpenAI €15M for GDPR violations.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Problem 3 */}
                <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-6">
                  <div className="flex items-start gap-4">
                    <span className="font-mono text-sm text-gray-400 dark:text-gray-600 flex-shrink-0">03</span>
                    <div>
                      <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2 font-mono">
                        Only 1 in 3 organizations have AI governance frameworks
                      </h3>
                      <p className="text-gray-600 dark:text-gray-400">
                        Without audit trails, you can't prove compliance during regulatory audits.
                        No visibility into what PII was sent where means you're flying blind when the EU AI Act enforcement begins.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 4. VALUE STACK */}
        <section className="py-20">
          <div className="container mx-auto px-6">
            <div className="max-w-4xl mx-auto">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">
                Everything You Need for Compliant AI
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mb-16 font-mono text-sm">
                // Production-ready compliance in one API call
              </p>

              <div className="space-y-1">
                {/* Feature 1 */}
                <div className="border border-gray-200 dark:border-gray-800 p-6 bg-white dark:bg-black hover:border-blue-600 dark:hover:border-blue-400 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <span className="text-2xl">🔒</span>
                      <div>
                        <h3 className="text-lg font-bold text-gray-900 dark:text-white font-mono">Automatic PII Redaction</h3>
                        <p className="text-gray-600 dark:text-gray-400 text-sm">
                          Detects and masks SSNs, emails, credit cards, names before sending to LLMs
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Feature 2 */}
                <div className="border border-gray-200 dark:border-gray-800 p-6 bg-white dark:bg-black hover:border-blue-600 dark:hover:border-blue-400 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <span className="text-2xl">📝</span>
                      <div>
                        <h3 className="text-lg font-bold text-gray-900 dark:text-white font-mono">Immutable Audit Logs</h3>
                        <p className="text-gray-600 dark:text-gray-400 text-sm">
                          Database-enforced immutability for regulatory compliance and forensics
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Feature 3 */}
                <div className="border border-gray-200 dark:border-gray-800 p-6 bg-white dark:bg-black hover:border-blue-600 dark:hover:border-blue-400 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <span className="text-2xl">🔌</span>
                      <div>
                        <h3 className="text-lg font-bold text-gray-900 dark:text-white font-mono">Multi-Provider Support</h3>
                        <p className="text-gray-600 dark:text-gray-400 text-sm">
                          OpenAI, Anthropic, Google, Cohere - use any model with one integration
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Feature 4 */}
                <div className="border border-gray-200 dark:border-gray-800 p-6 bg-white dark:bg-black hover:border-blue-600 dark:hover:border-blue-400 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <span className="text-2xl">⚡</span>
                      <div>
                        <h3 className="text-lg font-bold text-gray-900 dark:text-white font-mono">Zero Code Changes</h3>
                        <p className="text-gray-600 dark:text-gray-400 text-sm">
                          Drop-in replacement for OpenAI SDK - change one line and you're protected
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Value Summary */}
              <div className="mt-8 p-8 border-2 border-blue-600 dark:border-blue-400 bg-white dark:bg-black">
                <div className="text-center">
                  <p className="font-mono text-sm text-gray-600 dark:text-gray-400 mb-2">TOTAL_VALUE =</p>
                  <p className="text-3xl font-bold text-gray-900 dark:text-white mb-4 font-mono">Complete Compliance Stack</p>
                  <Link
                    href="/docs/quickstart"
                    className="inline-block px-8 py-3 bg-blue-600 text-white font-mono font-semibold hover:bg-blue-700 transition-colors"
                  >
                    Start Building
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 5. SOCIAL PROOF */}
        <section className="bg-gray-50 dark:bg-gray-950 border-y border-gray-200 dark:border-gray-900 py-20">
          <div className="container mx-auto px-6">
            <div className="max-w-4xl mx-auto">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-16">
                The Industry Challenge
              </h2>

              <div className="grid md:grid-cols-3 gap-1">
                {/* Stat 1 */}
                <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-8">
                  <div className="font-mono text-5xl font-bold text-blue-600 dark:text-blue-400 mb-2">71%</div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    of organizations cite cross-border data compliance as their top AI challenge
                  </p>
                </div>

                {/* Stat 2 */}
                <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-8">
                  <div className="font-mono text-5xl font-bold text-blue-600 dark:text-blue-400 mb-2">€15M</div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Fine issued to OpenAI by Italy for GDPR violations in 2025
                  </p>
                </div>

                {/* Stat 3 */}
                <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-8">
                  <div className="font-mono text-5xl font-bold text-blue-600 dark:text-blue-400 mb-2">1/3</div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    organizations have established comprehensive AI governance frameworks
                  </p>
                </div>
              </div>

              {/* Quote */}
              <div className="mt-8 border-l-4 border-blue-600 dark:border-blue-400 bg-white dark:bg-black p-8">
                <blockquote className="text-lg text-gray-700 dark:text-gray-300 mb-4 font-mono">
                  "You can't govern what you can't see. Scalable AI governance begins with mapping your data landscape."
                </blockquote>
                <p className="text-sm text-gray-500 dark:text-gray-500 font-mono">
                  — Security Boulevard
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* 6. TRANSFORMATION */}
        <section className="py-20">
          <div className="container mx-auto px-6">
            <div className="max-w-4xl mx-auto">
              <h2 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">
                From Setup to Scale
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mb-16 font-mono text-sm">
                // See results immediately, compound value over time
              </p>

              <div className="space-y-1">
                {/* Stage 1 */}
                <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-6">
                  <div className="flex items-start gap-6">
                    <div className="flex-shrink-0 w-10 h-10 border-2 border-blue-600 dark:border-blue-400 flex items-center justify-center font-mono font-bold text-blue-600 dark:text-blue-400">
                      1
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2 font-mono">
                        Quick Win: 5 Minutes to Protection
                      </h3>
                      <p className="text-gray-600 dark:text-gray-400">
                        Change your base_url to Aptly's API endpoint. That's it. Your first request is now automatically scanning for and redacting PII.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Stage 2 */}
                <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-6">
                  <div className="flex items-start gap-6">
                    <div className="flex-shrink-0 w-10 h-10 border-2 border-blue-600 dark:border-blue-400 flex items-center justify-center font-mono font-bold text-blue-600 dark:text-blue-400">
                      2
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2 font-mono">
                        Compound: Every Request Builds Your Audit Trail
                      </h3>
                      <p className="text-gray-600 dark:text-gray-400">
                        Each API call creates an immutable log entry with timestamps, PII detections, and full request metadata.
                        Your compliance documentation writes itself.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Stage 3 */}
                <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-6">
                  <div className="flex items-start gap-6">
                    <div className="flex-shrink-0 w-10 h-10 border-2 border-blue-600 dark:border-blue-400 flex items-center justify-center font-mono font-bold text-blue-600 dark:text-blue-400">
                      3
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2 font-mono">
                        Advantage: Pass Audits Without Breaking a Sweat
                      </h3>
                      <p className="text-gray-600 dark:text-gray-400">
                        When regulators ask "how do you handle PII in AI systems?", you have a complete answer: automatic redaction,
                        immutable logs, and zero data retention by third parties.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Stage 4 */}
                <div className="border border-gray-200 dark:border-gray-800 bg-white dark:bg-black p-6">
                  <div className="flex items-start gap-6">
                    <div className="flex-shrink-0 w-10 h-10 border-2 border-blue-600 dark:border-blue-400 flex items-center justify-center font-mono font-bold text-blue-600 dark:text-blue-400">
                      4
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2 font-mono">
                        10x: Ship AI Features Without Legal Bottlenecks
                      </h3>
                      <p className="text-gray-600 dark:text-gray-400">
                        Your team moves faster because compliance is handled. No more "we can't use AI here because of PII concerns."
                        Every new LLM feature is automatically compliant from day one.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 7. SECONDARY CTA */}
        <section className="bg-blue-600 dark:bg-blue-600 py-20">
          <div className="container mx-auto px-6">
            <div className="max-w-3xl mx-auto text-center">
              <h2 className="text-3xl md:text-5xl font-bold text-white mb-6 font-mono">
                Ready to Use AI Safely?
              </h2>
              <p className="text-xl text-blue-100 mb-8">
                Get started in 5 minutes with our OpenAI-compatible API
              </p>
              <Link
                href="/docs/quickstart"
                className="inline-block px-10 py-4 bg-white text-blue-600 font-mono font-bold hover:bg-gray-100 transition-colors border-2 border-white"
              >
                Yes, Show Me How
              </Link>
            </div>
          </div>
        </section>
      </main>

      {/* 8. FOOTER */}
      <footer className="border-t border-gray-200 dark:border-gray-800">
        <div className="container mx-auto px-6 py-12">
          <div className="grid md:grid-cols-3 gap-8 mb-8">
            {/* Logo & Description */}
            <div className="md:col-span-2">
              <div className="flex items-center gap-2 mb-4">
                <span className="text-blue-600 dark:text-blue-400 text-xl">$</span>
                <span className="text-xl font-mono font-bold text-gray-900 dark:text-white">aptly</span>
              </div>
              <p className="text-gray-600 dark:text-gray-400 text-sm">
                Compliance-as-a-Service for AI applications.
                <br />
                Automatic PII redaction and audit logging for any LLM.
              </p>
            </div>

            {/* Product */}
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-4 font-mono text-sm">Product</h3>
              <ul className="space-y-2 text-sm">
                <li>
                  <Link href="/docs" className="text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400">
                    Documentation
                  </Link>
                </li>
                <li>
                  <Link href="/docs/api-reference" className="text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400">
                    API Reference
                  </Link>
                </li>
                <li>
                  <Link href="/docs/quickstart" className="text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400">
                    Quick Start
                  </Link>
                </li>
              </ul>
            </div>
          </div>

          {/* Bottom Bar */}
          <div className="border-t border-gray-200 dark:border-gray-800 pt-8">
            <p className="text-gray-600 dark:text-gray-400 text-sm font-mono">
              © 2026 NSquared Labs
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
