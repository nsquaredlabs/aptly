# PRD: Framework-Specific Entity Detection

**Date:** 2026-02-18
**Status:** Implemented
**Spec Reference:** Section on PII Detection & Redaction (SPEC.md lines 643-728)

---

## Overview

Make the `compliance_frameworks` field functional by loading framework-specific PII entity recognizers. Currently, the field is metadata-only—all customers detect the same 13 entity types regardless of their declared compliance needs. This PRD implements HIPAA, FinTech (PCI-DSS), GDPR, and SOC2-specific entity detection.

---

## Context

### Current State

The system currently supports:
- Database field: `customers.compliance_frameworks TEXT[]`
- API support: Field can be set/updated via admin and customer endpoints
- Audit logging: First framework logged in `audit_logs.compliance_framework`
- Fixed entity detection: All customers use the same 13 Presidio entities

**Problem:** A customer setting `compliance_frameworks: ["HIPAA"]` gets the exact same PII detection as one with `["FinTech"]` or no frameworks at all. The field has no functional effect.

### Gap Being Addressed

1. **HIPAA customers** need Medical Record Numbers, Health Plan IDs, Device Serial Numbers
2. **FinTech customers** need CVV codes, Routing Numbers, Account Numbers
3. **GDPR customers** need EU National IDs, VAT Numbers, Passport Numbers
4. **SOC2 customers** need API Keys, Cloud Credentials, JWT Tokens
5. **Generic customers** should continue using the baseline 13 entities

---

## Requirements

### 1. Framework Entity Mappings

Define entity sets for each framework:

**Baseline (all customers):**
```python
BASELINE_ENTITIES = [
    "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER",
    "LOCATION", "DATE_TIME", "IP_ADDRESS", "URL"
]
```

**HIPAA (Healthcare):**
```python
HIPAA_ENTITIES = BASELINE_ENTITIES + [
    "US_SSN", "US_PASSPORT", "US_DRIVER_LICENSE",
    "MEDICAL_LICENSE", "UK_NHS",
    "MEDICAL_RECORD_NUMBER",      # Custom recognizer
    "HEALTH_PLAN_NUMBER",          # Custom recognizer
    "DEVICE_SERIAL_NUMBER",        # Custom recognizer
]
```

**FinTech (PCI-DSS):**
```python
FINTECH_ENTITIES = BASELINE_ENTITIES + [
    "CREDIT_CARD", "IBAN_CODE", "US_BANK_NUMBER",
    "CRYPTO", "US_ITIN",
    "CVV",                         # Custom recognizer
    "ROUTING_NUMBER",              # Custom recognizer
    "ACCOUNT_NUMBER",              # Custom recognizer
]
```

**GDPR (EU Compliance):**
```python
GDPR_ENTITIES = BASELINE_ENTITIES + [
    "IBAN_CODE", "IP_ADDRESS",
    "EU_NATIONAL_ID",              # Enable Presidio regional recognizers
    "EU_VAT_NUMBER",               # Custom recognizer
    "EU_PASSPORT",                 # Enable Presidio regional recognizers
]
```

**SOC2 (Security):**
```python
SOC2_ENTITIES = BASELINE_ENTITIES + [
    "API_KEY",                     # Custom recognizer
    "AWS_KEY",                     # Custom recognizer
    "GCP_KEY",                     # Custom recognizer
    "GITHUB_TOKEN",                # Custom recognizer
    "JWT_TOKEN",                   # Custom recognizer
    "PRIVATE_KEY",                 # Custom recognizer
]
```

### 2. Custom Recognizers

Create pattern-based recognizers for entities not in Presidio's default set:

**2.1 Medical Record Number (MRN)**
- Pattern: 6-10 alphanumeric characters, often prefixed with "MRN", "MR#", "Medical Record"
- Examples: "MRN123456", "MR#A12345678", "Medical Record: 9876543"
- Confidence: 0.85 (medium-high)

**2.2 Health Plan Number**
- Pattern: 9-12 digits, often prefixed with "Plan ID", "Health Plan", "Member ID"
- Examples: "Plan ID: 123456789", "Member ID 987654321"
- Confidence: 0.80 (medium)

**2.3 Device Serial Number**
- Pattern: Alphanumeric, 8-20 characters, often prefixed with "S/N", "Serial", "Device ID"
- Examples: "S/N: ABC123DEF456", "Device ID XYZ789"
- Confidence: 0.75 (medium, lower due to generic pattern)

**2.4 CVV/CVC Code**
- Pattern: 3-4 digits, often near "CVV", "CVC", "Security Code"
- Examples: "CVV: 123", "CVC 4567"
- Confidence: 0.90 (high when context present)
- **Caution:** Requires context to avoid false positives on random 3-digit numbers

**2.5 Routing Number**
- Pattern: 9 digits, ABA routing number format with checksum validation
- Examples: "021000021", "Routing: 111000025"
- Confidence: 0.95 (very high with checksum)

**2.6 Account Number**
- Pattern: 8-17 digits, often prefixed with "Account", "Acct", "A/C"
- Examples: "Account: 12345678901", "Acct# 9876543210"
- Confidence: 0.80 (medium, generic pattern)

**2.7 EU VAT Number**
- Pattern: Country code (2 letters) + 8-12 digits
- Examples: "DE123456789", "FR12345678901", "VAT: GB123456789"
- Confidence: 0.90 (high with country code)

**2.8 API Keys**
- Pattern: Long alphanumeric strings (32-128 chars), often with prefixes
- Examples: "sk-proj-...", "AKIA...", "ghp_...", "AIza..."
- Confidence: 0.95 (very high with known prefixes)
- Prefixes: `sk-` (OpenAI), `AKIA` (AWS), `ghp_` (GitHub), `AIza` (Google)

**2.9 AWS Keys**
- Pattern: `AKIA[A-Z0-9]{16}` for access keys
- Examples: "AKIAIOSFODNN7EXAMPLE"
- Confidence: 0.99 (extremely high, very specific pattern)

**2.10 JWT Tokens**
- Pattern: Three base64url-encoded parts separated by dots
- Examples: "eyJhbGci...[long string]"
- Confidence: 0.90 (high, distinctive structure)

### 3. Framework Selection Logic

**3.1 Multiple Frameworks**

When a customer has multiple frameworks, use the **union** of all entity sets:

```python
frameworks = customer.compliance_frameworks  # ["HIPAA", "GDPR"]
entities = BASELINE_ENTITIES.copy()

for framework in frameworks:
    entities.extend(FRAMEWORK_ENTITIES.get(framework.lower(), []))

entities = list(set(entities))  # Deduplicate
```

**3.2 No Frameworks**

If `compliance_frameworks` is empty or null, use `BASELINE_ENTITIES`.

**3.3 Unknown Frameworks**

Log a warning and skip unknown framework names (e.g., customer enters "ISO27001"):
```python
logger.warning("unknown_framework", framework=framework, customer_id=customer.id)
```

### 4. PIIRedactor Changes

Modify `PIIRedactor` class to accept entity list:

```python
class PIIRedactor:
    def __init__(
        self,
        mode: RedactionMode = "mask",
        entities: list[str] | None = None
    ):
        """
        Initialize PIIRedactor with optional entity list.

        Args:
            mode: Redaction mode (mask, hash, remove)
            entities: List of entity types to detect.
                     If None, uses BASELINE_ENTITIES.
        """
        self.mode = mode
        self.entities = entities or BASELINE_ENTITIES

        # Initialize Presidio with custom recognizers
        nlp_config = {...}
        nlp_engine = NlpEngineProvider(nlp_configuration=nlp_config).create_engine()

        self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine)

        # Add custom recognizers
        for recognizer in get_custom_recognizers():
            self.analyzer.registry.add_recognizer(recognizer)
```

### 5. Chat Completion Flow Update

In `src/main.py`, pass framework-derived entity list to redactor:

```python
# Get customer's frameworks
frameworks = customer.compliance_frameworks or []

# Build entity list
entities = get_entities_for_frameworks(frameworks)

# Initialize redactor with framework-specific entities
redactor = PIIRedactor(
    mode=customer.pii_redaction_mode,
    entities=entities
)

# Redact messages
redacted_messages, detections = redactor.redact_messages(request.messages)
```

### 6. Audit Log Enhancement

Add `entities_scanned` field to audit logs (optional, for debugging):

```python
{
    "compliance_framework": "HIPAA",
    "entities_scanned": ["PERSON", "EMAIL_ADDRESS", ..., "MEDICAL_RECORD_NUMBER"],
    "pii_detected": [...]
}
```

**Note:** This is stored as metadata in the existing `audit_logs.request_data` JSONB field—no schema migration needed.

---

## Technical Approach

### Implementation Steps

**Step 1: Define Entity Mappings** (`src/compliance/framework_entities.py`)

```python
# New file
BASELINE_ENTITIES = [...]
HIPAA_ENTITIES = [...]
FINTECH_ENTITIES = [...]
GDPR_ENTITIES = [...]
SOC2_ENTITIES = [...]

FRAMEWORK_ENTITIES = {
    "hipaa": HIPAA_ENTITIES,
    "fintech": FINTECH_ENTITIES,
    "pci-dss": FINTECH_ENTITIES,  # Alias
    "gdpr": GDPR_ENTITIES,
    "soc2": SOC2_ENTITIES,
}

def get_entities_for_frameworks(frameworks: list[str]) -> list[str]:
    """
    Get union of entities for given frameworks.

    Args:
        frameworks: List of framework names (case-insensitive)

    Returns:
        List of entity type names to detect
    """
    if not frameworks:
        return BASELINE_ENTITIES.copy()

    entities = set(BASELINE_ENTITIES)

    for framework in frameworks:
        framework_lower = framework.lower()
        if framework_lower in FRAMEWORK_ENTITIES:
            entities.update(FRAMEWORK_ENTITIES[framework_lower])
        else:
            logger.warning("unknown_framework", framework=framework)

    return sorted(list(entities))
```

**Step 2: Create Custom Recognizers** (`src/compliance/custom_recognizers.py`)

```python
from presidio_analyzer import PatternRecognizer

def get_custom_recognizers() -> list[PatternRecognizer]:
    """Return list of custom PII recognizers."""
    return [
        # Medical Record Number
        PatternRecognizer(
            supported_entity="MEDICAL_RECORD_NUMBER",
            patterns=[
                {
                    "name": "mrn_pattern",
                    "regex": r"\b(MRN|MR#|Medical Record)[:\s#]*([A-Z0-9]{6,10})\b",
                    "score": 0.85,
                }
            ],
            context=["patient", "medical", "health", "record"],
        ),

        # CVV Code
        PatternRecognizer(
            supported_entity="CVV",
            patterns=[
                {
                    "name": "cvv_pattern",
                    "regex": r"\b(CVV|CVC|Security Code)[:\s]*(\d{3,4})\b",
                    "score": 0.90,
                }
            ],
            context=["card", "credit", "payment"],
        ),

        # Routing Number (with checksum validation)
        PatternRecognizer(
            supported_entity="ROUTING_NUMBER",
            patterns=[
                {
                    "name": "routing_pattern",
                    "regex": r"\b(Routing|ABA)[:\s#]*(\d{9})\b",
                    "score": 0.95,
                }
            ],
            context=["bank", "account", "transfer"],
        ),

        # API Keys (OpenAI, AWS, GitHub, Google)
        PatternRecognizer(
            supported_entity="API_KEY",
            patterns=[
                {
                    "name": "openai_key",
                    "regex": r"\bsk-proj-[A-Za-z0-9_-]{48,}\b",
                    "score": 0.99,
                },
                {
                    "name": "aws_key",
                    "regex": r"\bAKIA[A-Z0-9]{16}\b",
                    "score": 0.99,
                },
                {
                    "name": "github_token",
                    "regex": r"\bghp_[A-Za-z0-9]{36,}\b",
                    "score": 0.99,
                },
                {
                    "name": "google_key",
                    "regex": r"\bAIza[A-Za-z0-9_-]{35,}\b",
                    "score": 0.99,
                },
            ],
        ),

        # ... (8 more recognizers)
    ]
```

**Step 3: Update PIIRedactor** (`src/compliance/pii_redactor.py`)

```python
from src.compliance.custom_recognizers import get_custom_recognizers
from src.compliance.framework_entities import BASELINE_ENTITIES

class PIIRedactor:
    def __init__(
        self,
        mode: RedactionMode = "mask",
        entities: list[str] | None = None
    ):
        nlp_config = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
        }
        nlp_engine = NlpEngineProvider(nlp_configuration=nlp_config).create_engine()

        self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine)

        # Add custom recognizers
        for recognizer in get_custom_recognizers():
            self.analyzer.registry.add_recognizer(recognizer)

        self.anonymizer = AnonymizerEngine()
        self.mode = mode
        self.entities = entities or BASELINE_ENTITIES

    def redact(self, text: str) -> RedactionResult:
        """Redact PII from text using framework-specific entities."""
        if not text or not text.strip():
            return RedactionResult(...)

        # Detect PII using self.entities
        results = self.analyzer.analyze(
            text=text,
            entities=self.entities,  # <-- Use framework-specific list
            language="en",
        )

        # ... rest of implementation unchanged
```

**Step 4: Update Chat Completion Handler** (`src/main.py`)

```python
from src.compliance.framework_entities import get_entities_for_frameworks

@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    customer: Customer = Depends(CustomerAuth()),
):
    # ... (existing code)

    # Get framework-specific entities
    entities = get_entities_for_frameworks(customer.compliance_frameworks)

    logger.info(
        "pii_redaction_starting",
        customer_id=customer.id,
        frameworks=customer.compliance_frameworks,
        entity_count=len(entities),
    )

    # Initialize redactor with framework entities
    redactor = PIIRedactor(
        mode=customer.pii_redaction_mode,
        entities=entities
    )

    # Redact messages
    redacted_messages, detections = redactor.redact_messages(request.messages)

    # ... (existing code continues)
```

---

## Files to Modify/Create

| File | Change Type | Description |
|------|-------------|-------------|
| `src/compliance/framework_entities.py` | **Create** | Entity mappings for HIPAA, FinTech, GDPR, SOC2 |
| `src/compliance/custom_recognizers.py` | **Create** | 10 custom Presidio recognizers |
| `src/compliance/pii_redactor.py` | **Modify** | Add `entities` parameter to `__init__`, pass to analyzer |
| `src/main.py` | **Modify** | Call `get_entities_for_frameworks()` before redaction |
| `tests/test_framework_entities.py` | **Create** | Unit tests for entity mapping logic |
| `tests/test_custom_recognizers.py` | **Create** | Tests for each custom recognizer pattern |
| `tests/test_chat_completions.py` | **Modify** | Add framework-specific detection tests |

---

## Database Changes

**None.** This feature uses the existing `compliance_frameworks` field.

Optional: Add `entities_scanned` to audit log metadata for debugging. This is stored in the existing `audit_logs.request_data` JSONB column—no migration needed.

---

## Testing Strategy

### Unit Tests

**`tests/test_framework_entities.py`** (10 tests)
- Test `get_entities_for_frameworks()` with each framework
- Test multiple frameworks (union behavior)
- Test empty/null frameworks (returns baseline)
- Test unknown framework (logs warning, ignores)
- Test case-insensitivity ("HIPAA" vs "hipaa")
- Test deduplication (baseline + framework overlap)

**`tests/test_custom_recognizers.py`** (25 tests)
- Test each custom recognizer with positive examples
- Test each recognizer with negative examples (should not match)
- Test context requirements (e.g., CVV near "card")
- Test confidence scores
- Test edge cases (short/long strings, special characters)

### Integration Tests

**`tests/test_chat_completions.py`** (new tests, ~8 tests)

```python
def test_chat_completion_hipaa_detects_mrn(client, mock_supabase):
    """HIPAA customer detects Medical Record Numbers."""
    # Mock customer with frameworks: ["HIPAA"]
    # Request with text: "Patient MRN: A1234567 has diabetes"
    # Assert: PII detected includes MEDICAL_RECORD_NUMBER
    # Assert: Redacted text contains "MEDICAL_RECORD_NUMBER_A"

def test_chat_completion_fintech_detects_cvv(client, mock_supabase):
    """FinTech customer detects CVV codes."""
    # Mock customer with frameworks: ["FinTech"]
    # Request with text: "My CVV is 123"
    # Assert: PII detected includes CVV
    # Assert: Redacted text contains "CVV_A"

def test_chat_completion_gdpr_detects_vat(client, mock_supabase):
    """GDPR customer detects EU VAT numbers."""
    # Mock customer with frameworks: ["GDPR"]
    # Request with text: "Company VAT: DE123456789"
    # Assert: PII detected includes EU_VAT_NUMBER

def test_chat_completion_soc2_detects_api_key(client, mock_supabase):
    """SOC2 customer detects API keys."""
    # Mock customer with frameworks: ["SOC2"]
    # Request with text: "My key is sk-proj-abc123..."
    # Assert: PII detected includes API_KEY

def test_chat_completion_multiple_frameworks(client, mock_supabase):
    """Customer with multiple frameworks detects union of entities."""
    # Mock customer with frameworks: ["HIPAA", "GDPR"]
    # Request with text containing MRN and VAT number
    # Assert: Both MEDICAL_RECORD_NUMBER and EU_VAT_NUMBER detected

def test_chat_completion_no_frameworks_baseline(client, mock_supabase):
    """Customer with no frameworks uses baseline entities."""
    # Mock customer with frameworks: []
    # Request with text containing PERSON, EMAIL (baseline)
    # Assert: Baseline entities detected
    # Assert: MRN, CVV not detected (not in baseline)

def test_chat_completion_unknown_framework_ignored(client, mock_supabase):
    """Unknown framework logged but doesn't break detection."""
    # Mock customer with frameworks: ["ISO27001", "HIPAA"]
    # Assert: Warning logged for "ISO27001"
    # Assert: HIPAA entities still detected

def test_chat_completion_audit_log_records_frameworks(client, mock_supabase):
    """Audit log includes compliance framework."""
    # Mock customer with frameworks: ["HIPAA"]
    # Send chat completion
    # Assert: Audit log compliance_framework == "HIPAA"
```

### Critical Test Cases That MUST Pass

1. **`test_hipaa_mrn_detection`** - HIPAA customer detects "MRN: 123456"
2. **`test_fintech_cvv_detection`** - FinTech customer detects "CVV: 123"
3. **`test_fintech_routing_detection`** - FinTech customer detects routing number
4. **`test_soc2_api_key_detection`** - SOC2 customer detects OpenAI/AWS keys
5. **`test_multiple_frameworks_union`** - Union of entities when multiple frameworks
6. **`test_no_frameworks_baseline_only`** - No frameworks = baseline entities only
7. **`test_unknown_framework_graceful`** - Unknown framework doesn't crash

---

## Dependencies

### Existing Infrastructure (No New Dependencies)

- Microsoft Presidio (already installed)
- Presidio PatternRecognizer API (built-in)
- Existing `compliance_frameworks` database field

### No External Dependencies

All custom recognizers use Presidio's built-in `PatternRecognizer` class. No new Python packages required.

---

## Out of Scope

### Deferred to Future PRDs

1. **ML-based recognizers** - Current implementation uses regex patterns only
2. **Custom entity training** - No customer-defined entity types (e.g., internal ID formats)
3. **Framework combinations** - No special logic for "HIPAA + FinTech" beyond union
4. **Regional Presidio recognizers** - Enable Spain, Italy, etc. recognizers (easy addition later)
5. **Entity-level confidence thresholds** - All entities use default confidence
6. **Redaction mode per entity** - All entities use customer's global redaction mode
7. **Framework validation** - No API enforcement of which frameworks customers can select

### Explicitly NOT Included

- Dashboard UI for selecting frameworks (API-only feature)
- Framework-specific audit report formats (all use same format)
- Compliance attestation/certification (Aptly doesn't certify HIPAA compliance)

---

## Success Criteria

### Feature Complete When:

- [x] Framework entity mappings defined for HIPAA, FinTech, GDPR, SOC2
- [x] 10 custom recognizers implemented and registered
- [x] `PIIRedactor` accepts entity list parameter
- [x] Chat completion handler selects entities based on customer frameworks
- [x] All 25+ new tests pass
- [x] No regressions in existing PII detection tests
- [x] Test coverage >85% for new files

### Verification Commands

```bash
# Run all tests
pytest tests/ -v --cov=src --cov-report=term-missing

# Run framework-specific tests only
pytest tests/test_framework_entities.py -v
pytest tests/test_custom_recognizers.py -v
pytest tests/test_chat_completions.py::test_chat_completion_hipaa_detects_mrn -v

# Test with real API (after deployment)
# 1. Create HIPAA customer
curl -X POST https://api-aptly.nsquaredlabs.com/v1/admin/customers \
  -H "X-Admin-Secret: $APTLY_ADMIN_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "hipaa-test@example.com",
    "company_name": "Test Healthcare",
    "compliance_frameworks": ["HIPAA"]
  }'

# 2. Send completion with MRN
curl -X POST https://api-aptly.nsquaredlabs.com/v1/chat/completions \
  -H "Authorization: Bearer apt_live_..." \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "Patient MRN: A1234567 has diabetes"}
    ],
    "api_keys": {"openai": "sk-..."}
  }'

# 3. Verify response shows redacted MRN
# Expected: "Patient MEDICAL_RECORD_NUMBER_A has MEDICAL_CONDITION_A"
```

---

## Implementation Notes

### Pattern Design Considerations

1. **Context Requirements**: Recognizers like CVV require context words ("card", "credit") to reduce false positives on random 3-digit numbers.

2. **Confidence Scores**: Higher confidence for specific patterns (AWS keys: 0.99) vs. generic patterns (account numbers: 0.80).

3. **Regex Safety**: All patterns avoid catastrophic backtracking (tested with long inputs).

4. **False Positives**: Some patterns (Device Serial Number, Account Number) are intentionally broad—better to over-detect than miss sensitive data.

### Performance Impact

- **Negligible**: Adding recognizers to Presidio analyzer has minimal performance cost (~5-10ms per request).
- **Entity count**: Analyzing 25 entities instead of 13 adds <5% latency.
- **No breaking changes**: Existing customers continue using baseline entities if frameworks not set.

### Migration Path

1. **Existing customers**: No change unless they update their `compliance_frameworks` field.
2. **New customers**: Can set frameworks on creation via admin endpoint.
3. **Gradual rollout**: Test with internal/beta customers before announcing feature.

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Custom recognizers have false positives | Medium | Low | Use context requirements, test with real data |
| Performance degradation | Low | Low | Benchmark with 25 entities vs. 13 (expect <10ms increase) |
| Breaking changes to existing customers | Low | High | Default to baseline entities if frameworks empty |
| Presidio version compatibility | Low | Medium | Pin presidio-analyzer version in requirements.txt |
| Complex framework combinations | Low | Low | Use simple union logic, document in API reference |

---

## Timeline Estimate

| Phase | Duration | Tasks |
|-------|----------|-------|
| Phase 1: Entity Mappings | 0.5 days | Define 5 framework entity sets, write unit tests |
| Phase 2: Custom Recognizers | 1 day | Implement 10 recognizers, write pattern tests |
| Phase 3: Integration | 0.5 days | Wire into PIIRedactor and chat completion flow |
| Phase 4: Testing | 1 day | Write 25+ tests, manual testing, fix edge cases |
| **Total** | **3 days** | Full feature implementation |

---

## Appendix: Entity Reference

### Baseline Entities (All Customers)

| Entity | Example | Presidio Support |
|--------|---------|-----------------|
| PERSON | "John Smith" | ✅ Built-in |
| EMAIL_ADDRESS | "john@example.com" | ✅ Built-in |
| PHONE_NUMBER | "(555) 123-4567" | ✅ Built-in |
| LOCATION | "123 Main St, New York" | ✅ Built-in |
| DATE_TIME | "January 1, 2026" | ✅ Built-in |
| IP_ADDRESS | "192.168.1.1" | ✅ Built-in |
| URL | "https://example.com" | ✅ Built-in |

### HIPAA-Specific Entities

| Entity | Example | Implementation |
|--------|---------|----------------|
| US_SSN | "123-45-6789" | ✅ Built-in |
| MEDICAL_LICENSE | "A12345" | ✅ Built-in |
| MEDICAL_RECORD_NUMBER | "MRN: A1234567" | 🆕 Custom |
| HEALTH_PLAN_NUMBER | "Plan ID: 123456789" | 🆕 Custom |
| DEVICE_SERIAL_NUMBER | "S/N: ABC123" | 🆕 Custom |

### FinTech-Specific Entities

| Entity | Example | Implementation |
|--------|---------|----------------|
| CREDIT_CARD | "4532-1234-5678-9010" | ✅ Built-in |
| US_BANK_NUMBER | "123456789012" | ✅ Built-in |
| IBAN_CODE | "DE89370400440532013000" | ✅ Built-in |
| CRYPTO | "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa" | ✅ Built-in |
| CVV | "CVV: 123" | 🆕 Custom |
| ROUTING_NUMBER | "021000021" | 🆕 Custom |
| ACCOUNT_NUMBER | "Acct: 12345678901" | 🆕 Custom |

### SOC2-Specific Entities

| Entity | Example | Implementation |
|--------|---------|----------------|
| API_KEY | "sk-proj-abc123..." | 🆕 Custom |
| AWS_KEY | "AKIAIOSFODNN7EXAMPLE" | 🆕 Custom |
| GITHUB_TOKEN | "ghp_abc123..." | 🆕 Custom |
| JWT_TOKEN | "eyJhbGci..." | 🆕 Custom |

---

## References

- [Microsoft Presidio Documentation](https://microsoft.github.io/presidio/)
- [Presidio Custom Recognizers](https://microsoft.github.io/presidio/analyzer/adding_recognizers/)
- [HIPAA PHI Requirements](https://github.com/microsoft/presidio-research/blob/master/docs/requirements/industry/hipaa/phi.md)
- Current implementation: `src/compliance/pii_redactor.py`
- SPEC.md Section: PII Detection & Redaction (lines 643-728)
