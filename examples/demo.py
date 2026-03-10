#!/usr/bin/env python3
"""
Demo script showing Aptly's PII redaction and un-redaction in action.

Prerequisites:
  - Aptly server running: aptly serve --reload
  - OpenAI API key set: export OPENAI_KEY=sk-...
  - pip install openai
"""

import os
import sys

from openai import OpenAI

APTLY_URL = os.getenv("APTLY_URL", "http://localhost:8000/v1")
APTLY_SECRET = os.getenv("APTLY_API_SECRET", "my-test-secret")
OPENAI_KEY = os.getenv("OPENAI_KEY")

if not OPENAI_KEY:
    print("Error: Set OPENAI_KEY environment variable first.")
    print("  export OPENAI_KEY=sk-...")
    sys.exit(1)

client = OpenAI(base_url=APTLY_URL, api_key=APTLY_SECRET)

print("=" * 60)
print("Aptly PII Redaction Demo")
print("=" * 60)

# --- Example 1: Basic PII redaction + un-redaction ---
print("\n--- Example 1: PII is redacted for the LLM, restored for you ---\n")

prompt = "My name is John Smith and my email is john@example.com. Please greet me by name."
print(f"You: {prompt}\n")

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}],
    extra_body={"api_keys": {"openai": OPENAI_KEY}},
)

print(f"LLM: {response.choices[0].message.content}")

# The aptly metadata is in the response
aptly = response.model_extra.get("aptly", {}) if hasattr(response, "model_extra") else {}
if aptly:
    print(f"\n  PII detected:    {aptly.get('pii_detected')}")
    print(f"  PII entities:    {aptly.get('pii_entities')}")
    print(f"  Audit log ID:    {aptly.get('audit_log_id')}")

# --- Example 2: Multiple PII types ---
print("\n--- Example 2: Multiple PII types ---\n")

prompt = "Patient Jane Doe (SSN: 123-45-6789, email: jane@hospital.org) needs a follow-up. Summarize."
print(f"You: {prompt}\n")

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}],
    extra_body={"api_keys": {"openai": OPENAI_KEY}},
)

print(f"LLM: {response.choices[0].message.content}")

aptly = response.model_extra.get("aptly", {}) if hasattr(response, "model_extra") else {}
if aptly:
    print(f"\n  PII entities:    {aptly.get('pii_entities')}")

# --- Example 3: Streaming ---
print("\n--- Example 3: Streaming with PII ---\n")

prompt = "Tell me a short joke about Alice Johnson who lives at alice.j@gmail.com."
print(f"You: {prompt}\n")
print("LLM: ", end="", flush=True)

stream = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": prompt}],
    extra_body={"api_keys": {"openai": OPENAI_KEY}},
    stream=True,
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)

print("\n")
print("=" * 60)
print("Done! Check your audit logs: curl http://localhost:8000/v1/logs -H 'Authorization: Bearer my-test-secret'")
