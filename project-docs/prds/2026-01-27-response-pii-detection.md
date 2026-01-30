# PRD: Response PII Detection

**Date:** 2026-01-27
**Status:** Implemented
**Spec Reference:** PII Detection & Redaction section of SPEC.md

## Overview

Add PII detection to LLM responses. Currently, Aptly only redacts PII from user inputs before sending to the LLM. However, LLM responses can also contain PII - hallucinated names, leaked training data, or information inferred from context. For true HIPAA/GDPR compliance, responses must also be scanned and flagged.

## Context

### Current State
- PII is detected and redacted from input messages before sending to LLM
- Audit logs store redacted request content
- Response content is stored in audit logs without PII scanning
- The `aptly` metadata in responses includes `pii_detected` and `pii_entities` but only reflects input PII

### Gap Being Addressed
- LLM responses may contain PII (names, emails, phone numbers, etc.)
- Customers expecting compliance guarantees need visibility into response PII
- No current mechanism to detect or flag PII in responses
- Audit logs should distinguish between input PII and output PII

## Requirements

1. Scan LLM response content for PII using the existing PIIRedactor
2. Add `response_pii_detected` and `response_pii_entities` to the `aptly` metadata in chat completion responses
3. Store response PII detections in audit logs separately from input PII
4. For streaming responses, scan the accumulated content at stream completion
5. Do NOT redact response content by default - only detect and flag (redaction would alter LLM output)
6. Add optional `redact_response` parameter to chat completion request to enable response redaction

## Technical Approach

### Non-Streaming Flow
```
LLM Response → PII Scan → Log (with response PII) → Return (with metadata)
```

### Streaming Flow
```
Stream chunks → Accumulate content → On completion: PII Scan → Log → Final chunk metadata
```

### Response Metadata Changes
```python
class AptlyMetadata(BaseModel):
    audit_log_id: str
    pii_detected: bool              # Input PII (existing)
    pii_entities: list[str]         # Input PII types (existing)
    response_pii_detected: bool     # NEW: Response PII
    response_pii_entities: list[str] # NEW: Response PII types
    compliance_framework: str | None
    latency_ms: int
```

### Audit Log Changes
```python
# In audit log entry
pii_detected: list[dict]           # Existing: input PII
response_pii_detected: list[dict]  # NEW: response PII
```

## Files to Modify/Create

- `src/main.py` - Add response PII scanning to chat completion handler
- `src/compliance/audit_logger.py` - Add `response_pii_detected` field to AuditLogEntry
- `supabase/migrations/002_response_pii.sql` - Add `response_pii_detected` column to audit_logs table
- `tests/test_chat_completions.py` - Add tests for response PII detection

## Database Changes

```sql
-- Add response_pii_detected column to audit_logs
ALTER TABLE audit_logs
ADD COLUMN response_pii_detected JSONB DEFAULT '[]';
```

## Testing Strategy

- Unit tests: PIIRedactor on response-like content
- Integration tests: Full chat completion with PII in mocked LLM response
- Streaming tests: Verify response PII detected after stream completion

### Critical Test Cases
- `test_chat_completion_response_pii_detected` - PII in response is flagged in metadata
- `test_chat_completion_response_pii_audit_log` - Response PII stored in audit log
- `test_chat_completion_response_no_pii` - Clean response shows no response PII
- `test_chat_completion_streaming_response_pii` - Streaming response PII in final chunk
- `test_chat_completion_redact_response_option` - Optional response redaction works

## Dependencies

- Existing PIIRedactor (no changes needed to the redactor itself)
- Existing audit logging infrastructure

## Out of Scope

- Real-time response blocking based on PII detection
- Custom PII entity types for responses
- Response PII webhooks (future feature)

## Success Criteria

- [ ] Response PII detected and included in `aptly` metadata
- [ ] Response PII stored separately in audit logs
- [ ] Streaming responses include response PII in final chunk
- [ ] Optional `redact_response` parameter works
- [ ] All tests pass with >80% coverage maintained
