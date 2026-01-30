# PRD: Streaming Response Tests

**Date:** 2026-01-26
**Status:** Implemented
**Spec Reference:** Section "Streaming Support" and "Testing Requirements" of SPEC.md

## Overview

Add comprehensive test coverage for the streaming chat completion handler (`_handle_streaming_completion` in `src/main.py`, lines 707-809). This is a critical feature per the spec ("Streaming MUST be implemented from the start") but currently has no test coverage.

## Context

### Current State
- Streaming endpoint exists and is functional (`POST /v1/chat/completions` with `stream: true`)
- Non-streaming chat completions have full test coverage
- The `_handle_streaming_completion` function (lines 707-809) is completely untested
- Overall coverage is 80%, but `src/main.py` is at 84% due to untested streaming paths

### Gap Being Addressed
The streaming response handler includes:
1. SSE event formatting and yielding
2. Async iteration over LLM stream chunks
3. Audit log creation at stream completion
4. Error handling during streaming
5. Final chunk with `aptly` metadata

None of these paths are tested, creating risk for a feature the spec designates as mandatory.

## Requirements

### Mock Infrastructure
1. Create a mock async generator that simulates LiteLLM streaming responses
2. Mock should support configurable chunks (content, finish_reason, is_final)
3. Mock should support error injection for testing error paths

### Happy Path Tests
4. `test_chat_completion_streaming_basic` - Verify streaming returns SSE format with correct headers
5. `test_chat_completion_streaming_chunks` - Verify chunks are yielded with correct structure
6. `test_chat_completion_streaming_final_chunk` - Verify final chunk contains `aptly` metadata
7. `test_chat_completion_streaming_audit_log` - Verify audit log is created after stream completes

### PII Redaction in Streaming
8. `test_chat_completion_streaming_pii_redacted` - Verify PII is redacted before streaming to LLM
9. `test_chat_completion_streaming_pii_in_metadata` - Verify `pii_detected` flag in final chunk

### Error Handling Tests
10. `test_chat_completion_streaming_provider_error` - Verify error SSE event on LLM failure
11. `test_chat_completion_streaming_rate_limited` - Verify 429 before streaming starts (rate limit checked before stream)

### Edge Cases
12. `test_chat_completion_streaming_empty_response` - Handle LLM returning no content
13. `test_chat_completion_streaming_done_event` - Verify `[DONE]` SSE event at end

## Technical Approach

### Streaming Mock Pattern
```python
async def mock_streaming_response(chunks: list[dict]):
    """Create a mock async generator for LiteLLM streaming."""
    for chunk in chunks:
        yield MockStreamChunk(**chunk)

@pytest.fixture
def mock_llm_stream(mocker):
    """Fixture that patches call_llm to return a streaming mock."""
    async def _create_stream(chunks):
        mocker.patch(
            "src.main.call_llm",
            return_value=mock_streaming_response(chunks)
        )
    return _create_stream
```

### SSE Response Testing
Use `httpx` with `stream=True` to consume SSE responses:
```python
async with client.stream("POST", "/v1/chat/completions", json=payload) as response:
    async for line in response.aiter_lines():
        if line.startswith("data: "):
            # Parse and validate SSE event
```

### Audit Log Verification
After streaming completes, query the mocked Supabase to verify audit log was created with:
- Correct `customer_id`
- `response_data.content` containing accumulated stream content
- `pii_detected` array matching input detections

## Files to Modify/Create

- `tests/test_chat_completions.py` - Add streaming test cases
- `tests/conftest.py` - Add streaming mock fixtures (if needed)

## Database Changes

None - tests use mocked Supabase.

## Testing Strategy

### Test Structure
All new tests go in `tests/test_chat_completions.py` to keep streaming tests alongside non-streaming tests.

### Critical Test Cases (Must Pass)
- `test_chat_completion_streaming_basic` - SSE format correct
- `test_chat_completion_streaming_audit_log` - Audit log created
- `test_chat_completion_streaming_pii_redacted` - PII never sent to LLM
- `test_chat_completion_streaming_provider_error` - Errors handled gracefully

### Coverage Target
- `src/main.py` coverage: 84% → 95%+
- Lines 707-809 fully covered

## Dependencies

- Existing test infrastructure (fakeredis, mocked Supabase)
- `httpx` async streaming support (already in requirements)

## Out of Scope

- Integration tests with real LLM providers
- Performance/load testing of streaming
- WebSocket alternative to SSE
- Client-side streaming consumption examples

## Success Criteria

- [ ] All 10+ new streaming tests pass
- [ ] `src/main.py` coverage reaches 95%+
- [ ] Lines 707-809 in `_handle_streaming_completion` are covered
- [ ] Streaming error paths are tested
- [ ] `pytest tests/test_chat_completions.py -v` shows all streaming tests green
