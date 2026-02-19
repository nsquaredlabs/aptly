# Project Analysis: Framework-Specific Entity Detection

**Analysis Date:** 2026-02-18
**Spec Version:** 3.0.0
**Focus Area:** compliance_frameworks field implementation

---

## Sources Analyzed

| Source | Files | Last Updated |
|--------|-------|--------------|
| Work Summaries | 7 files | 2026-02-17 |
| PRDs | 8 files | 2026-02-17 |
| SPEC.md | 1 file | 2026-01-24 |
| Source Code | 13 files in src/ | Current |
| Tests | 10 files in tests/ | Current |

---

## Current Implementation Status

### Completed Features (from Work Summaries)

- ✅ **MVP Middleware API** (2026-01-26)
  - Admin authentication with APTLY_ADMIN_SECRET
  - Customer API key authentication
  - Chat completions endpoint (OpenAI-compatible)
  - PII redaction (Microsoft Presidio)
  - Immutable audit logs
  - Rate limiting (Redis)

- ✅ **Streaming Response Tests** (2026-01-26)
  - SSE streaming for chat completions
  - Test coverage for streaming

- ✅ **Test Infrastructure Setup** (2026-01-26)
  - pytest + fixtures
  - Mocked Supabase client
  - 88% test coverage

- ✅ **Production Deployment** (2026-01-27)
  - Deployed to Railway
  - Domain: api-aptly.nsquaredlabs.com
  - Health checks passing

- ✅ **Response PII Detection** (2026-01-27)
  - PII detection in LLM responses
  - Logged in audit trail

- ✅ **Customer Analytics API** (2026-02-04)
  - 5 analytics endpoints
  - Usage, models, users, PII stats, CSV export

- ✅ **Custom Documentation** (2026-02-17)
  - Next.js + Nextra documentation site
  - OpenAPI spec with Scalar
  - Animated code demo

### Partial / Not Fully Implemented

- ⚠️ **Compliance Frameworks** - Field exists but has NO functional effect
  - Database field: `customers.compliance_frameworks TEXT[]`
  - API support: Can set/update via admin and customer endpoints
  - Audit logging: Framework name logged in `audit_logs.compliance_framework`
  - **Missing**: Framework-specific entity detection
  - **Missing**: HIPAA, FinTech, GDPR, SOC2-specific recognizers

---

## Gap Analysis: Compliance Frameworks

### Current Behavior

The `compliance_frameworks` field is **metadata only**:

1. **Stored** in `customers` table
2. **Retrieved** during authentication
3. **Logged** in audit logs
4. **Displayed** in API responses
5. **NOT USED** to modify PII detection behavior

All customers detect the same 13 entity types regardless of their declared compliance frameworks:
- PERSON, EMAIL_ADDRESS, PHONE_NUMBER, US_SSN, CREDIT_CARD
- IBAN_CODE, MEDICAL_LICENSE, US_PASSPORT, LOCATION
- DATE_TIME, IP_ADDRESS, URL, NRP

### What's Missing

#### 1. Framework-Specific Entity Sets

**HIPAA (Healthcare):**
- Missing: Medical Record Numbers (MRN)
- Missing: Health Plan Beneficiary Numbers
- Missing: Device Identifiers/Serial Numbers
- Missing: Vehicle License Plates
- Have: US_SSN, MEDICAL_LICENSE, PERSON, PHONE_NUMBER, LOCATION, DATE_TIME ✓

**FinTech/PCI-DSS:**
- Missing: CVV/CVC codes
- Missing: Routing numbers
- Missing: Generic account numbers
- Have: CREDIT_CARD, IBAN_CODE, US_BANK_NUMBER ✓

**GDPR (EU):**
- Missing: EU National IDs (Spain, Italy, France, Germany, etc.)
- Missing: VAT numbers
- Missing: Non-US passport numbers
- Have: EMAIL_ADDRESS, PHONE_NUMBER, IP_ADDRESS, LOCATION ✓

**SOC 2 (Security):**
- Missing: API keys (AWS, GCP, GitHub, etc.)
- Missing: JWT tokens
- Missing: Private keys
- Have: Good audit logging infrastructure ✓

#### 2. Framework-to-Entity Mapping

No logic exists to load different recognizers based on `compliance_frameworks` value.

#### 3. Custom Recognizers

While Microsoft Presidio supports 50+ built-in recognizers and custom recognizer creation, Aptly only uses 13 entities from the default set.

---

## Technical Context

### Presidio Capabilities

Microsoft Presidio supports:
- **18 built-in entities** currently available (we use 13)
- **50+ regional recognizers** (Spain, Italy, Poland, India, etc.)
- **Custom recognizer API** for pattern-based and ML-based entity detection
- **Framework-specific entity sets** (documented in presidio-research repo)

### Available Presidio Entities Not Currently Used

```python
# Additional entities available in Presidio:
"US_DRIVER_LICENSE"    # HIPAA
"US_ITIN"              # FinTech
"UK_NHS"               # HIPAA (UK)
"US_BANK_NUMBER"       # FinTech
"CRYPTO"               # FinTech (cryptocurrency wallets)
"MAC_ADDRESS"          # SOC2
# + 40+ regional entities (Spain, Italy, etc.)
```

---

## Recommended Next Steps

### Option 1: Framework-Specific Entity Detection (Recommended)

**Why:** Delivers on the compliance_frameworks promise. Customers selecting "HIPAA" should get HIPAA-relevant PII detection.

**Effort:** Medium (2-3 days)

**What it enables:**
- HIPAA customers detect MRN, health plan numbers, device IDs
- FinTech customers detect CVV, routing numbers, account numbers
- GDPR customers detect EU national IDs, VAT numbers
- SOC2 customers detect API keys, credentials
- Generic mode keeps current 13-entity baseline

**Implementation approach:**
1. Define framework-specific entity sets
2. Add custom recognizers for missing entities (MRN, CVV, etc.)
3. Modify `PIIRedactor` to accept entity list parameter
4. Update chat completion flow to select entities based on customer's frameworks
5. Add tests for framework-specific detection

**Files to modify:**
- `src/compliance/pii_redactor.py` - Add framework entity mappings
- `src/compliance/custom_recognizers.py` - New file for custom patterns
- `src/main.py` - Pass framework to redactor initialization
- `tests/test_pii_detection.py` - Add framework-specific tests

**Database changes:** None (uses existing `compliance_frameworks` field)

**Success criteria:**
- Customer with `frameworks: ["hipaa"]` detects MRN and health plan numbers
- Customer with `frameworks: ["fintech"]` detects CVV and routing numbers
- Customer with `frameworks: ["hipaa", "gdpr"]` detects union of both sets
- Customer with `frameworks: []` uses baseline 13 entities
- All framework-specific tests pass

---

### Option 2: Analytics Enhancement

**Why:** Customers need insights into their LLM usage.

**Effort:** Small (1 day) - already have analytics endpoints

**What it enables:**
- Cost tracking per user/model
- PII detection trends
- Usage forecasting

**Status:** Already implemented in 2026-02-04. Could add:
- Cost alerts
- Anomaly detection
- Custom date ranges

---

### Option 3: Multi-Provider Key Management

**Why:** Simplify customer experience when using multiple LLM providers.

**Effort:** Medium (2 days)

**What it enables:**
- Store encrypted provider keys (OpenAI, Anthropic, etc.)
- Customers don't pass `api_keys` in each request
- Key rotation without code changes

**Trade-offs:**
- Increases security responsibility (we store keys)
- Contradicts current "customer-provided keys" design
- Would require encryption infrastructure

---

## Priority Ranking

### 1. Framework-Specific Entity Detection (High Priority)

**Score: 9/10**
- **User Value:** High - delivers on existing feature promise
- **Dependencies:** None - uses existing infrastructure
- **Strategic Fit:** Core compliance offering
- **Technical Debt:** Fixes incomplete implementation
- **User Feedback:** Implicit - field exists but doesn't work

### 2. Enhanced Analytics (Medium Priority)

**Score: 5/10**
- **User Value:** Medium - nice to have
- **Dependencies:** None
- **Strategic Fit:** Good for enterprise customers
- **Technical Debt:** None - clean addition

### 3. Multi-Provider Key Management (Low Priority)

**Score: 3/10**
- **User Value:** Medium
- **Dependencies:** Requires encryption infrastructure
- **Strategic Fit:** Contradicts current design philosophy
- **Technical Debt:** Would increase security surface area

---

## Recommendation

**Proceed with Option 1: Framework-Specific Entity Detection**

This feature:
1. Makes the existing `compliance_frameworks` field functional
2. Differentiates Aptly from generic PII redaction tools
3. Delivers real value to HIPAA, FinTech, GDPR, and SOC2 customers
4. Requires no database changes (uses existing schema)
5. Builds on proven Presidio capabilities

The implementation is straightforward:
- Define entity sets for each framework
- Add 10-15 custom recognizers for missing patterns
- Wire framework selection into existing redaction flow
- Add comprehensive test coverage

---

## Next Action

Write PRD for Framework-Specific Entity Detection feature, including:
- Framework-to-entity mappings
- Custom recognizer patterns
- Implementation approach
- Test cases
- Success criteria
