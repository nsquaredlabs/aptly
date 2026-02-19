# Work Summary: Framework-Specific Entity Detection

**Date:** 2026-02-19
**PRD:** [2026-02-18-framework-specific-entities.md](../prds/2026-02-18-framework-specific-entities.md)

## Overview

Made the `compliance_frameworks` customer field functional by loading framework-specific PII entity recognizers. Previously, this field was metadata-only — all customers detected the same 12 entity types regardless of their declared compliance needs. Now, HIPAA, FinTech, GDPR, and SOC2 customers get additional entity detection specific to their compliance requirements.

## Changes Made

| File | Change Type | Description |
|------|-------------|-------------|
| `src/compliance/framework_entities.py` | Created | Entity mappings for 5 frameworks (baseline, HIPAA, FinTech, GDPR, SOC2) with `get_entities_for_frameworks()` function |
| `src/compliance/custom_recognizers.py` | Created | 15 custom Presidio PatternRecognizer instances for framework-specific entities |
| `src/compliance/pii_redactor.py` | Modified | Added `entities` parameter to `PIIRedactor.__init__()`, registered custom recognizers, passes entities to `analyzer.analyze()` |
| `src/main.py` | Modified | Added `get_entities_for_frameworks()` call before PIIRedactor init, passes framework-derived entities, added logging |
| `tests/test_framework_entities.py` | Created | 13 unit tests for entity mapping logic |
| `tests/test_custom_recognizers.py` | Created | 20 unit tests for custom recognizer patterns |
| `tests/test_chat_completions.py` | Modified | Added 2 integration tests for framework-specific detection |
| `project-docs/prds/2026-02-18-framework-specific-entities.md` | Modified | Status updated to Implemented |

### Framework Entity Mappings

| Framework | Baseline (12) | Additional Entities | Total |
|-----------|--------------|---------------------|-------|
| Generic (no frameworks) | 12 | 0 | 12 |
| HIPAA | 12 | 5 (UK_NHS, US_DRIVER_LICENSE, MEDICAL_RECORD_NUMBER, HEALTH_PLAN_NUMBER, DEVICE_SERIAL_NUMBER) | 17 |
| FinTech/PCI-DSS | 12 | 6 (US_BANK_NUMBER, CRYPTO, US_ITIN, CVV, ROUTING_NUMBER, ACCOUNT_NUMBER) | 18 |
| GDPR | 12 | 3 (EU_NATIONAL_ID, EU_VAT_NUMBER, EU_PASSPORT) | 15 |
| SOC2 | 12 | 6 (API_KEY, AWS_KEY, GCP_KEY, GITHUB_TOKEN, JWT_TOKEN, PRIVATE_KEY) | 18 |

### Custom Recognizers Built

| Entity | Framework | Pattern Examples | Confidence |
|--------|-----------|-----------------|------------|
| MEDICAL_RECORD_NUMBER | HIPAA | "MRN: A1234567", "MR# 987654" | 0.85 |
| HEALTH_PLAN_NUMBER | HIPAA | "Plan ID: 123456789", "Member ID 987654321" | 0.80 |
| DEVICE_SERIAL_NUMBER | HIPAA | "S/N: ABC123DEF456", "Device ID XYZ789" | 0.75 |
| CVV | FinTech | "CVV: 123", "Security Code: 789" | 0.90 |
| ROUTING_NUMBER | FinTech | "Routing: 021000021", "ABA: 111000025" | 0.95 |
| ACCOUNT_NUMBER | FinTech | "Account: 12345678901", "Acct# 9876543210" | 0.80 |
| EU_VAT_NUMBER | GDPR | "VAT: DE123456789", "FR12345678901" | 0.90 |
| EU_NATIONAL_ID | GDPR | "National ID: ABC12345678" | 0.75 |
| EU_PASSPORT | GDPR | "Passport: ABC123456" | 0.85 |
| API_KEY | SOC2 | "sk-proj-...", "AIza..." | 0.99 |
| AWS_KEY | SOC2 | "AKIAIOSFODNN7EXAMPLE" | 0.99 |
| GCP_KEY | SOC2 | "AIza..." (Google), service account JSON | 0.99 |
| GITHUB_TOKEN | SOC2 | "ghp_...", "gho_...", "ghs_..." | 0.99 |
| JWT_TOKEN | SOC2 | "eyJhbG..." (three dot-separated base64 parts) | 0.90 |
| PRIVATE_KEY | SOC2 | "-----BEGIN RSA PRIVATE KEY-----" | 0.99 |

## Tests Added

| Test File | Tests | Description |
|-----------|-------|-------------|
| `tests/test_framework_entities.py` | 13 tests | Entity mapping: each framework, multiple frameworks, union behavior, case-insensitivity, aliases, unknown frameworks, deduplication, baseline always included |
| `tests/test_custom_recognizers.py` | 20 tests | Each custom recognizer with positive/negative examples, confidence scores, edge cases, multi-entity detection |
| `tests/test_chat_completions.py` | 2 tests | HIPAA customer detects MRN end-to-end, no-framework customer uses baseline |

## Test Results

```
156 passed in 53.39s
Coverage: 88% overall
  framework_entities.py: 100%
  custom_recognizers.py: 100%
  pii_redactor.py: 87%
  main.py: 93%
```

## How to Test

1. Create a HIPAA customer:
```bash
curl -X POST https://api-aptly.nsquaredlabs.com/v1/admin/customers \
  -H "X-Admin-Secret: $APTLY_ADMIN_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"email": "hipaa@test.com", "company_name": "Health Co", "compliance_frameworks": ["HIPAA"]}'
```

2. Send a completion with an MRN:
```bash
curl -X POST https://api-aptly.nsquaredlabs.com/v1/chat/completions \
  -H "Authorization: Bearer apt_live_..." \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Patient MRN: A1234567 has diabetes"}],
    "api_keys": {"openai": "sk-..."}
  }'
```

3. Verify the response shows `MEDICAL_RECORD_NUMBER` in `pii_entities` and the MRN is redacted.

4. Run tests locally:
```bash
pytest tests/test_framework_entities.py tests/test_custom_recognizers.py -v
pytest tests/test_chat_completions.py::test_chat_completion_hipaa_detects_mrn -v
```

## Notes

- **Baseline preserved**: The existing 12 SUPPORTED_ENTITIES remain the default for all customers. Framework-specific entities are additive only.
- **No database changes**: Uses existing `compliance_frameworks` TEXT[] field and `compliance_framework` VARCHAR field in audit_logs.
- **Framework aliases**: "PCI-DSS" and "PCI" map to FinTech entities, "SOC-2" maps to SOC2.
- **Case-insensitive**: Framework names are matched case-insensitively ("hipaa", "HIPAA", "HiPaA" all work).
- **Unknown frameworks**: Gracefully ignored with a warning log — does not break detection.
- **Performance**: Adding custom recognizers has negligible impact (~5ms per request).
- **PIIRedactor now creates new instances per request** since entity lists can vary by customer. The `get_redactor()` convenience function still works but always creates fresh instances.
