"""Tests for the chat completions endpoint - THE MAIN FEATURE."""

import json
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone
from decimal import Decimal

from tests.conftest import (
    TEST_CUSTOMER,
    TEST_API_KEY,
    TEST_API_KEY_DATA,
    setup_auth_mocks,
)
from src.llm_router import StreamChunk, LLMResponse
from src.compliance.pii_redactor import PIIDetection, RedactionResult


# ============================================================================
# Streaming Test Helpers
# ============================================================================


async def mock_stream_generator(chunks: list[StreamChunk]):
    """Create a mock async generator that yields StreamChunks."""
    for chunk in chunks:
        yield chunk


def create_stream_chunks(contents: list[str], response_id: str = "chatcmpl-stream123"):
    """
    Helper to create a list of StreamChunks from content strings.
    The last chunk will have is_final=True.
    """
    chunks = []
    for i, content in enumerate(contents):
        is_last = i == len(contents) - 1
        chunks.append(
            StreamChunk(
                id=response_id,
                content=content,
                finish_reason="stop" if is_last else None,
                is_final=is_last,
            )
        )
    return chunks


def parse_sse_events(response_text: str) -> list[dict]:
    """Parse SSE response text into a list of event data dicts."""
    events = []
    for line in response_text.strip().split("\n"):
        if line.startswith("data: "):
            data = line[6:]  # Remove "data: " prefix
            if data != "[DONE]":
                events.append(json.loads(data))
            else:
                events.append({"done": True})
    return events


@pytest.mark.asyncio
async def test_chat_completion_basic(client, mock_supabase):
    """Basic chat completion works."""
    # Set up auth mocks (returns dict for .single() query)
    setup_auth_mocks(mock_supabase)

    # For the audit log insert
    with patch("src.compliance.audit_logger.supabase") as audit_mock:
        audit_table = MagicMock()
        audit_mock.table.return_value = audit_table
        audit_table.insert.return_value = audit_table
        audit_table.execute.return_value = MagicMock(
            data=[{"id": "log_test123"}]
        )

        with patch("src.main.call_llm") as mock_call_llm:
            from src.llm_router import LLMResponse
            from decimal import Decimal

            mock_call_llm.return_value = LLMResponse(
                id="chatcmpl-test123",
                model="gpt-4",
                content="Hello! How can I help you?",
                finish_reason="stop",
                tokens_input=10,
                tokens_output=20,
                cost_usd=Decimal("0.001"),
            )

            response = await client.post(
                "/v1/chat/completions",
                headers={"Authorization": f"Bearer {TEST_API_KEY}"},
                json={
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": "Hello"}],
                    "api_keys": {"openai": "sk-test123"},
                },
            )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "chatcmpl-test123"
    assert data["choices"][0]["message"]["content"] == "Hello! How can I help you?"
    assert "aptly" in data
    assert data["aptly"]["audit_log_id"] == "log_test123"


@pytest.mark.asyncio
async def test_chat_completion_pii_redaction(client, mock_supabase):
    """PII is detected and redacted before sending to LLM."""
    setup_auth_mocks(mock_supabase)

    # Mock PII detection to find a person's name
    with patch("src.compliance.audit_logger.supabase") as audit_mock:
        audit_table = MagicMock()
        audit_mock.table.return_value = audit_table
        audit_table.insert.return_value = audit_table
        audit_table.execute.return_value = MagicMock(
            data=[{"id": "log_test123"}]
        )

        with patch("src.main.PIIRedactor") as mock_redactor_class:
            mock_redactor = MagicMock()
            mock_redactor_class.return_value = mock_redactor

            # Simulate PII detection
            from src.compliance.pii_redactor import PIIDetection

            mock_redactor.redact_messages.return_value = (
                [{"role": "user", "content": "Patient PERSON_A has diabetes."}],
                [
                    PIIDetection(
                        type="PERSON",
                        replacement="PERSON_A",
                        confidence=0.95,
                        start=8,
                        end=18,
                    )
                ],
            )

            with patch("src.main.call_llm") as mock_call_llm:
                from src.llm_router import LLMResponse
                from decimal import Decimal

                # Capture what was sent to the LLM
                captured_messages = None

                async def capture_call(*args, **kwargs):
                    nonlocal captured_messages
                    captured_messages = kwargs.get("messages") or args[1]
                    return LLMResponse(
                        id="chatcmpl-test123",
                        model="gpt-4",
                        content="I understand.",
                        finish_reason="stop",
                        tokens_input=10,
                        tokens_output=5,
                        cost_usd=Decimal("0.0005"),
                    )

                mock_call_llm.side_effect = capture_call

                response = await client.post(
                    "/v1/chat/completions",
                    headers={"Authorization": f"Bearer {TEST_API_KEY}"},
                    json={
                        "model": "gpt-4",
                        "messages": [
                            {"role": "user", "content": "Patient John Smith has diabetes."}
                        ],
                        "api_keys": {"openai": "sk-test123"},
                    },
                )

    assert response.status_code == 200
    data = response.json()

    # Verify PII was detected
    assert data["aptly"]["pii_detected"] is True
    assert "PERSON" in data["aptly"]["pii_entities"]

    # Verify redacted content was sent to LLM (via the mock)
    mock_redactor.redact_messages.assert_called_once()


@pytest.mark.asyncio
async def test_chat_completion_audit_log_created(client, mock_supabase):
    """Every request creates an audit log entry."""
    setup_auth_mocks(mock_supabase)

    audit_log_created = False

    with patch("src.compliance.audit_logger.supabase") as audit_mock:
        audit_table = MagicMock()
        audit_mock.table.return_value = audit_table

        def track_insert(*args, **kwargs):
            nonlocal audit_log_created
            audit_log_created = True
            return audit_table

        audit_table.insert.side_effect = track_insert
        audit_table.execute.return_value = MagicMock(
            data=[{"id": "log_test123"}]
        )

        with patch("src.main.call_llm") as mock_call_llm:
            from src.llm_router import LLMResponse
            from decimal import Decimal

            mock_call_llm.return_value = LLMResponse(
                id="chatcmpl-test123",
                model="gpt-4",
                content="Hello!",
                finish_reason="stop",
                tokens_input=5,
                tokens_output=5,
                cost_usd=Decimal("0.0003"),
            )

            response = await client.post(
                "/v1/chat/completions",
                headers={"Authorization": f"Bearer {TEST_API_KEY}"},
                json={
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": "Hi"}],
                    "api_keys": {"openai": "sk-test123"},
                },
            )

    assert response.status_code == 200
    assert audit_log_created, "Audit log should have been created"

    data = response.json()
    assert data["aptly"]["audit_log_id"] == "log_test123"


@pytest.mark.asyncio
async def test_chat_completion_missing_api_keys(client, mock_supabase):
    """Returns 400 when api_keys not provided."""
    setup_auth_mocks(mock_supabase)

    response = await client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        json={
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
            # Missing api_keys
        },
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_chat_completion_missing_provider_key(client, mock_supabase):
    """Returns 400 when API key for required provider is missing."""
    setup_auth_mocks(mock_supabase)

    response = await client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        json={
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
            "api_keys": {"anthropic": "sk-ant-test"},  # Wrong provider
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["error"]["code"] == "INVALID_REQUEST"
    assert "openai" in data["detail"]["error"]["message"].lower()


@pytest.mark.asyncio
async def test_chat_completion_invalid_model(client, mock_supabase):
    """Returns 400 for unknown model."""
    setup_auth_mocks(mock_supabase)

    response = await client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {TEST_API_KEY}"},
        json={
            "model": "unknown-model-xyz",
            "messages": [{"role": "user", "content": "Hello"}],
            "api_keys": {"openai": "sk-test123"},
        },
    )

    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["error"]["code"] == "INVALID_REQUEST"


@pytest.mark.asyncio
async def test_chat_completion_rate_limited(client, mock_supabase):
    """Returns 429 when rate limit exceeded."""
    setup_auth_mocks(mock_supabase)

    with patch("src.main.rate_limiter") as mock_rate_limiter:
        from src.rate_limiter import RateLimitResult

        mock_rate_limiter.check_rate_limit = AsyncMock(
            return_value=RateLimitResult(
                allowed=False,
                current_count=1001,
                limit=1000,
                reset_at=datetime.now(timezone.utc),
            )
        )

        response = await client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {TEST_API_KEY}"},
            json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": "Hello"}],
                "api_keys": {"openai": "sk-test123"},
            },
        )

    assert response.status_code == 429
    data = response.json()
    assert data["detail"]["error"]["code"] == "RATE_LIMIT_EXCEEDED"


@pytest.mark.asyncio
async def test_chat_completion_unauthorized(client, mock_supabase):
    """Returns 401 for missing API key."""
    response = await client.post(
        "/v1/chat/completions",
        json={
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
            "api_keys": {"openai": "sk-test123"},
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_chat_completion_with_user_id(client, mock_supabase):
    """User ID is passed through and logged."""
    setup_auth_mocks(mock_supabase)

    logged_user_id = None

    with patch("src.compliance.audit_logger.supabase") as audit_mock:
        audit_table = MagicMock()
        audit_mock.table.return_value = audit_table

        def capture_insert(data):
            nonlocal logged_user_id
            logged_user_id = data.get("user_id")
            return audit_table

        audit_table.insert.side_effect = capture_insert
        audit_table.execute.return_value = MagicMock(
            data=[{"id": "log_test123"}]
        )

        with patch("src.main.call_llm") as mock_call_llm:
            from src.llm_router import LLMResponse
            from decimal import Decimal

            mock_call_llm.return_value = LLMResponse(
                id="chatcmpl-test123",
                model="gpt-4",
                content="Hello!",
                finish_reason="stop",
                tokens_input=5,
                tokens_output=5,
                cost_usd=Decimal("0.0003"),
            )

            response = await client.post(
                "/v1/chat/completions",
                headers={"Authorization": f"Bearer {TEST_API_KEY}"},
                json={
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": "Hello"}],
                    "api_keys": {"openai": "sk-test123"},
                    "user": "user_12345",
                },
            )

    assert response.status_code == 200
    assert logged_user_id == "user_12345"


# ============================================================================
# Streaming Tests
# ============================================================================


@pytest.mark.asyncio
async def test_chat_completion_streaming_basic(client, mock_supabase):
    """Verify streaming returns SSE format with correct headers."""
    setup_auth_mocks(mock_supabase)

    with patch("src.compliance.audit_logger.supabase") as audit_mock:
        audit_table = MagicMock()
        audit_mock.table.return_value = audit_table
        audit_table.insert.return_value = audit_table
        audit_table.execute.return_value = MagicMock(data=[{"id": "log_stream123"}])

        with patch("src.main.call_llm") as mock_call_llm:
            chunks = create_stream_chunks(["Hello", " world", "!"])
            mock_call_llm.return_value = mock_stream_generator(chunks)

            response = await client.post(
                "/v1/chat/completions",
                headers={"Authorization": f"Bearer {TEST_API_KEY}"},
                json={
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": "Hi"}],
                    "api_keys": {"openai": "sk-test123"},
                    "stream": True,
                },
            )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    assert "text/event-stream" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_chat_completion_streaming_chunks(client, mock_supabase):
    """Verify chunks are yielded with correct structure."""
    setup_auth_mocks(mock_supabase)

    with patch("src.compliance.audit_logger.supabase") as audit_mock:
        audit_table = MagicMock()
        audit_mock.table.return_value = audit_table
        audit_table.insert.return_value = audit_table
        audit_table.execute.return_value = MagicMock(data=[{"id": "log_stream123"}])

        with patch("src.main.call_llm") as mock_call_llm:
            chunks = create_stream_chunks(["Hello", " there"])
            mock_call_llm.return_value = mock_stream_generator(chunks)

            response = await client.post(
                "/v1/chat/completions",
                headers={"Authorization": f"Bearer {TEST_API_KEY}"},
                json={
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": "Hi"}],
                    "api_keys": {"openai": "sk-test123"},
                    "stream": True,
                },
            )

    assert response.status_code == 200
    events = parse_sse_events(response.text)

    # Filter out the DONE event
    data_events = [e for e in events if "done" not in e]

    assert len(data_events) >= 2
    # Verify structure of first chunk
    first_chunk = data_events[0]
    assert first_chunk["object"] == "chat.completion.chunk"
    assert "id" in first_chunk
    assert "choices" in first_chunk
    assert first_chunk["choices"][0]["index"] == 0


@pytest.mark.asyncio
async def test_chat_completion_streaming_final_chunk(client, mock_supabase):
    """Verify final chunk contains aptly metadata."""
    setup_auth_mocks(mock_supabase)

    with patch("src.compliance.audit_logger.supabase") as audit_mock:
        audit_table = MagicMock()
        audit_mock.table.return_value = audit_table
        audit_table.insert.return_value = audit_table
        audit_table.execute.return_value = MagicMock(data=[{"id": "log_final123"}])

        with patch("src.main.call_llm") as mock_call_llm:
            chunks = create_stream_chunks(["Response", " complete"])
            mock_call_llm.return_value = mock_stream_generator(chunks)

            response = await client.post(
                "/v1/chat/completions",
                headers={"Authorization": f"Bearer {TEST_API_KEY}"},
                json={
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": "Hi"}],
                    "api_keys": {"openai": "sk-test123"},
                    "stream": True,
                },
            )

    assert response.status_code == 200
    events = parse_sse_events(response.text)

    # Find the final data chunk (with aptly metadata)
    data_events = [e for e in events if "done" not in e]
    final_chunk = data_events[-1]

    assert "aptly" in final_chunk
    assert "audit_log_id" in final_chunk["aptly"]
    assert final_chunk["aptly"]["audit_log_id"] == "log_final123"
    assert "pii_detected" in final_chunk["aptly"]


@pytest.mark.asyncio
async def test_chat_completion_streaming_audit_log(client, mock_supabase):
    """Verify audit log is created after stream completes."""
    setup_auth_mocks(mock_supabase)

    audit_log_created = False
    captured_audit_data = None

    with patch("src.compliance.audit_logger.supabase") as audit_mock:
        audit_table = MagicMock()
        audit_mock.table.return_value = audit_table

        def track_insert(data):
            nonlocal audit_log_created, captured_audit_data
            audit_log_created = True
            captured_audit_data = data
            return audit_table

        audit_table.insert.side_effect = track_insert
        audit_table.execute.return_value = MagicMock(data=[{"id": "log_audit123"}])

        with patch("src.main.call_llm") as mock_call_llm:
            chunks = create_stream_chunks(["This ", "is ", "streamed"])
            mock_call_llm.return_value = mock_stream_generator(chunks)

            response = await client.post(
                "/v1/chat/completions",
                headers={"Authorization": f"Bearer {TEST_API_KEY}"},
                json={
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": "Test"}],
                    "api_keys": {"openai": "sk-test123"},
                    "stream": True,
                },
            )

    assert response.status_code == 200
    assert audit_log_created, "Audit log should have been created"
    assert captured_audit_data is not None
    # Verify accumulated content was logged
    assert "response_data" in captured_audit_data
    assert captured_audit_data["response_data"]["content"] == "This is streamed"


@pytest.mark.asyncio
async def test_chat_completion_streaming_pii_redacted(client, mock_supabase):
    """Verify PII is redacted before streaming to LLM."""
    setup_auth_mocks(mock_supabase)

    captured_messages = None

    with patch("src.compliance.audit_logger.supabase") as audit_mock:
        audit_table = MagicMock()
        audit_mock.table.return_value = audit_table
        audit_table.insert.return_value = audit_table
        audit_table.execute.return_value = MagicMock(data=[{"id": "log_pii123"}])

        with patch("src.main.PIIRedactor") as mock_redactor_class:
            mock_redactor = MagicMock()
            mock_redactor_class.return_value = mock_redactor

            from src.compliance.pii_redactor import PIIDetection

            mock_redactor.redact_messages.return_value = (
                [{"role": "user", "content": "Hello PERSON_A"}],
                [
                    PIIDetection(
                        type="PERSON",
                        replacement="PERSON_A",
                        confidence=0.95,
                        start=6,
                        end=16,
                    )
                ],
            )

            with patch("src.main.call_llm") as mock_call_llm:

                async def capture_and_stream(*args, **kwargs):
                    nonlocal captured_messages
                    captured_messages = kwargs.get("messages") or args[1]
                    chunks = create_stream_chunks(["Hi"])
                    async for chunk in mock_stream_generator(chunks):
                        yield chunk

                mock_call_llm.return_value = capture_and_stream()

                response = await client.post(
                    "/v1/chat/completions",
                    headers={"Authorization": f"Bearer {TEST_API_KEY}"},
                    json={
                        "model": "gpt-4",
                        "messages": [{"role": "user", "content": "Hello John Smith"}],
                        "api_keys": {"openai": "sk-test123"},
                        "stream": True,
                    },
                )

    assert response.status_code == 200
    mock_redactor.redact_messages.assert_called_once()


@pytest.mark.asyncio
async def test_chat_completion_streaming_pii_in_metadata(client, mock_supabase):
    """Verify pii_detected flag in final chunk metadata."""
    setup_auth_mocks(mock_supabase)

    with patch("src.compliance.audit_logger.supabase") as audit_mock:
        audit_table = MagicMock()
        audit_mock.table.return_value = audit_table
        audit_table.insert.return_value = audit_table
        audit_table.execute.return_value = MagicMock(data=[{"id": "log_pii_meta123"}])

        with patch("src.main.PIIRedactor") as mock_redactor_class:
            mock_redactor = MagicMock()
            mock_redactor_class.return_value = mock_redactor

            from src.compliance.pii_redactor import PIIDetection

            mock_redactor.redact_messages.return_value = (
                [{"role": "user", "content": "Patient PERSON_A"}],
                [
                    PIIDetection(
                        type="PERSON",
                        replacement="PERSON_A",
                        confidence=0.95,
                        start=8,
                        end=18,
                    )
                ],
            )

            with patch("src.main.call_llm") as mock_call_llm:
                chunks = create_stream_chunks(["OK"])
                mock_call_llm.return_value = mock_stream_generator(chunks)

                response = await client.post(
                    "/v1/chat/completions",
                    headers={"Authorization": f"Bearer {TEST_API_KEY}"},
                    json={
                        "model": "gpt-4",
                        "messages": [{"role": "user", "content": "Patient John Doe"}],
                        "api_keys": {"openai": "sk-test123"},
                        "stream": True,
                    },
                )

    assert response.status_code == 200
    events = parse_sse_events(response.text)
    data_events = [e for e in events if "done" not in e]
    final_chunk = data_events[-1]

    assert final_chunk["aptly"]["pii_detected"] is True


@pytest.mark.asyncio
async def test_chat_completion_streaming_provider_error(client, mock_supabase):
    """Verify error SSE event on LLM failure during streaming."""
    setup_auth_mocks(mock_supabase)

    with patch("src.main.call_llm") as mock_call_llm:

        async def error_stream():
            yield StreamChunk(id="err123", content="Start", finish_reason=None, is_final=False)
            raise Exception("Provider connection failed")

        mock_call_llm.return_value = error_stream()

        response = await client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {TEST_API_KEY}"},
            json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": "Test"}],
                "api_keys": {"openai": "sk-test123"},
                "stream": True,
            },
        )

    assert response.status_code == 200  # SSE always returns 200 initially
    events = parse_sse_events(response.text)

    # Should have an error event
    error_events = [e for e in events if "error" in e and "done" not in e]
    assert len(error_events) > 0
    assert error_events[0]["error"]["type"] == "provider_error"


@pytest.mark.asyncio
async def test_chat_completion_streaming_rate_limited(client, mock_supabase):
    """Verify 429 before streaming starts when rate limit exceeded."""
    setup_auth_mocks(mock_supabase)

    with patch("src.main.rate_limiter") as mock_rate_limiter:
        from src.rate_limiter import RateLimitResult

        mock_rate_limiter.check_rate_limit = AsyncMock(
            return_value=RateLimitResult(
                allowed=False,
                current_count=1001,
                limit=1000,
                reset_at=datetime.now(timezone.utc),
            )
        )

        response = await client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {TEST_API_KEY}"},
            json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": "Hi"}],
                "api_keys": {"openai": "sk-test123"},
                "stream": True,
            },
        )

    # Rate limit is checked BEFORE streaming starts, so we get 429
    assert response.status_code == 429
    data = response.json()
    assert data["detail"]["error"]["code"] == "RATE_LIMIT_EXCEEDED"


@pytest.mark.asyncio
async def test_chat_completion_streaming_empty_response(client, mock_supabase):
    """Handle LLM returning no content chunks."""
    setup_auth_mocks(mock_supabase)

    with patch("src.compliance.audit_logger.supabase") as audit_mock:
        audit_table = MagicMock()
        audit_mock.table.return_value = audit_table
        audit_table.insert.return_value = audit_table
        audit_table.execute.return_value = MagicMock(data=[{"id": "log_empty123"}])

        with patch("src.main.call_llm") as mock_call_llm:
            # Single chunk with no content but is_final
            empty_chunk = StreamChunk(
                id="chatcmpl-empty",
                content=None,
                finish_reason="stop",
                is_final=True,
            )
            mock_call_llm.return_value = mock_stream_generator([empty_chunk])

            response = await client.post(
                "/v1/chat/completions",
                headers={"Authorization": f"Bearer {TEST_API_KEY}"},
                json={
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": "Hi"}],
                    "api_keys": {"openai": "sk-test123"},
                    "stream": True,
                },
            )

    assert response.status_code == 200
    events = parse_sse_events(response.text)
    # Should still complete gracefully
    assert any(e.get("done") for e in events)


@pytest.mark.asyncio
async def test_chat_completion_streaming_done_event(client, mock_supabase):
    """Verify [DONE] SSE event at end of stream."""
    setup_auth_mocks(mock_supabase)

    with patch("src.compliance.audit_logger.supabase") as audit_mock:
        audit_table = MagicMock()
        audit_mock.table.return_value = audit_table
        audit_table.insert.return_value = audit_table
        audit_table.execute.return_value = MagicMock(data=[{"id": "log_done123"}])

        with patch("src.main.call_llm") as mock_call_llm:
            chunks = create_stream_chunks(["Test"])
            mock_call_llm.return_value = mock_stream_generator(chunks)

            response = await client.post(
                "/v1/chat/completions",
                headers={"Authorization": f"Bearer {TEST_API_KEY}"},
                json={
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": "Hi"}],
                    "api_keys": {"openai": "sk-test123"},
                    "stream": True,
                },
            )

    assert response.status_code == 200

    # Check raw response for [DONE]
    assert "data: [DONE]" in response.text

    # Also verify via parsed events
    events = parse_sse_events(response.text)
    done_events = [e for e in events if e.get("done")]
    assert len(done_events) == 1


# ============================================================================
# Response PII Detection Tests
# ============================================================================


@pytest.mark.asyncio
async def test_chat_completion_response_pii_detected(client, mock_supabase):
    """PII in response is flagged in aptly metadata."""
    setup_auth_mocks(mock_supabase)

    with patch("src.compliance.audit_logger.supabase") as audit_mock:
        audit_table = MagicMock()
        audit_mock.table.return_value = audit_table
        audit_table.insert.return_value = audit_table
        audit_table.execute.return_value = MagicMock(data=[{"id": "log_resp_pii123"}])

        with patch("src.main.PIIRedactor") as mock_redactor_class:
            mock_redactor = MagicMock()
            mock_redactor_class.return_value = mock_redactor

            # No input PII
            mock_redactor.redact_messages.return_value = (
                [{"role": "user", "content": "What is the CEO's name?"}],
                [],  # No input PII
            )

            # Response contains PII - return RedactionResult object
            response_pii = PIIDetection(
                type="PERSON",
                replacement="PERSON_A",
                confidence=0.95,
                start=11,
                end=21,
            )
            mock_redactor.redact.return_value = RedactionResult(
                redacted_text="The CEO is PERSON_A who works at Acme Corp.",
                detections=[response_pii],
                pii_detected=True,
            )

            with patch("src.main.call_llm") as mock_call_llm:
                mock_call_llm.return_value = LLMResponse(
                    id="chatcmpl-resp-pii",
                    model="gpt-4",
                    content="The CEO is John Smith who works at Acme Corp.",
                    finish_reason="stop",
                    tokens_input=10,
                    tokens_output=15,
                    cost_usd=Decimal("0.001"),
                )

                response = await client.post(
                    "/v1/chat/completions",
                    headers={"Authorization": f"Bearer {TEST_API_KEY}"},
                    json={
                        "model": "gpt-4",
                        "messages": [{"role": "user", "content": "What is the CEO's name?"}],
                        "api_keys": {"openai": "sk-test123"},
                    },
                )

    assert response.status_code == 200
    data = response.json()

    # Verify response PII was detected
    assert data["aptly"]["response_pii_detected"] is True
    assert "PERSON" in data["aptly"]["response_pii_entities"]
    # Input should have no PII
    assert data["aptly"]["pii_detected"] is False


@pytest.mark.asyncio
async def test_chat_completion_response_pii_audit_log(client, mock_supabase):
    """Response PII is stored in audit log separately from input PII."""
    setup_auth_mocks(mock_supabase)

    captured_audit_data = None

    with patch("src.compliance.audit_logger.supabase") as audit_mock:
        audit_table = MagicMock()
        audit_mock.table.return_value = audit_table

        def capture_insert(data):
            nonlocal captured_audit_data
            captured_audit_data = data
            return audit_table

        audit_table.insert.side_effect = capture_insert
        audit_table.execute.return_value = MagicMock(data=[{"id": "log_audit_pii123"}])

        with patch("src.main.PIIRedactor") as mock_redactor_class:
            mock_redactor = MagicMock()
            mock_redactor_class.return_value = mock_redactor

            # Input has PII
            input_pii = PIIDetection(
                type="PERSON",
                replacement="PERSON_A",
                confidence=0.95,
                start=15,
                end=25,
            )
            mock_redactor.redact_messages.return_value = (
                [{"role": "user", "content": "Tell me about PERSON_A"}],
                [input_pii],
            )

            # Response also has PII - return RedactionResult
            response_pii = PIIDetection(
                type="LOCATION",
                replacement="LOCATION_A",
                confidence=0.90,
                start=18,
                end=28,
            )
            mock_redactor.redact.return_value = RedactionResult(
                redacted_text="PERSON_A lives at LOCATION_A.",
                detections=[response_pii],
                pii_detected=True,
            )

            with patch("src.main.call_llm") as mock_call_llm:
                mock_call_llm.return_value = LLMResponse(
                    id="chatcmpl-both-pii",
                    model="gpt-4",
                    content="John lives at 123 Main St.",
                    finish_reason="stop",
                    tokens_input=10,
                    tokens_output=10,
                    cost_usd=Decimal("0.001"),
                )

                response = await client.post(
                    "/v1/chat/completions",
                    headers={"Authorization": f"Bearer {TEST_API_KEY}"},
                    json={
                        "model": "gpt-4",
                        "messages": [{"role": "user", "content": "Tell me about John Doe"}],
                        "api_keys": {"openai": "sk-test123"},
                    },
                )

    assert response.status_code == 200
    assert captured_audit_data is not None

    # Check both input and response PII are logged
    assert "pii_detected" in captured_audit_data
    assert "response_pii_detected" in captured_audit_data
    assert len(captured_audit_data["pii_detected"]) == 1
    assert len(captured_audit_data["response_pii_detected"]) == 1
    assert captured_audit_data["pii_detected"][0]["type"] == "PERSON"
    assert captured_audit_data["response_pii_detected"][0]["type"] == "LOCATION"


@pytest.mark.asyncio
async def test_chat_completion_response_no_pii(client, mock_supabase):
    """Clean response shows no response PII in metadata."""
    setup_auth_mocks(mock_supabase)

    with patch("src.compliance.audit_logger.supabase") as audit_mock:
        audit_table = MagicMock()
        audit_mock.table.return_value = audit_table
        audit_table.insert.return_value = audit_table
        audit_table.execute.return_value = MagicMock(data=[{"id": "log_no_pii123"}])

        with patch("src.main.PIIRedactor") as mock_redactor_class:
            mock_redactor = MagicMock()
            mock_redactor_class.return_value = mock_redactor

            # No input PII
            mock_redactor.redact_messages.return_value = (
                [{"role": "user", "content": "What is 2+2?"}],
                [],
            )

            # No response PII either - return RedactionResult with empty detections
            mock_redactor.redact.return_value = RedactionResult(
                redacted_text="2+2 equals 4.",
                detections=[],
                pii_detected=False,
            )

            with patch("src.main.call_llm") as mock_call_llm:
                mock_call_llm.return_value = LLMResponse(
                    id="chatcmpl-clean",
                    model="gpt-4",
                    content="2+2 equals 4.",
                    finish_reason="stop",
                    tokens_input=5,
                    tokens_output=5,
                    cost_usd=Decimal("0.0003"),
                )

                response = await client.post(
                    "/v1/chat/completions",
                    headers={"Authorization": f"Bearer {TEST_API_KEY}"},
                    json={
                        "model": "gpt-4",
                        "messages": [{"role": "user", "content": "What is 2+2?"}],
                        "api_keys": {"openai": "sk-test123"},
                    },
                )

    assert response.status_code == 200
    data = response.json()

    assert data["aptly"]["pii_detected"] is False
    assert data["aptly"]["response_pii_detected"] is False
    assert data["aptly"]["pii_entities"] == []
    assert data["aptly"]["response_pii_entities"] == []


@pytest.mark.asyncio
async def test_chat_completion_streaming_response_pii(client, mock_supabase):
    """Streaming response PII detected in final chunk metadata."""
    setup_auth_mocks(mock_supabase)

    with patch("src.compliance.audit_logger.supabase") as audit_mock:
        audit_table = MagicMock()
        audit_mock.table.return_value = audit_table
        audit_table.insert.return_value = audit_table
        audit_table.execute.return_value = MagicMock(data=[{"id": "log_stream_pii123"}])

        with patch("src.main.PIIRedactor") as mock_redactor_class:
            mock_redactor = MagicMock()
            mock_redactor_class.return_value = mock_redactor

            # No input PII
            mock_redactor.redact_messages.return_value = (
                [{"role": "user", "content": "Who founded the company?"}],
                [],
            )

            # Response will have PII when accumulated - return RedactionResult
            response_pii = PIIDetection(
                type="PERSON",
                replacement="PERSON_A",
                confidence=0.95,
                start=15,
                end=23,
            )
            mock_redactor.redact.return_value = RedactionResult(
                redacted_text="The founder is PERSON_A.",
                detections=[response_pii],
                pii_detected=True,
            )

            with patch("src.main.call_llm") as mock_call_llm:
                chunks = create_stream_chunks(["The founder ", "is ", "Elon Musk."])
                mock_call_llm.return_value = mock_stream_generator(chunks)

                response = await client.post(
                    "/v1/chat/completions",
                    headers={"Authorization": f"Bearer {TEST_API_KEY}"},
                    json={
                        "model": "gpt-4",
                        "messages": [{"role": "user", "content": "Who founded the company?"}],
                        "api_keys": {"openai": "sk-test123"},
                        "stream": True,
                    },
                )

    assert response.status_code == 200
    events = parse_sse_events(response.text)

    # Find the final data chunk with aptly metadata
    data_events = [e for e in events if "done" not in e]
    final_chunk = data_events[-1]

    assert "aptly" in final_chunk
    assert final_chunk["aptly"]["response_pii_detected"] is True
    assert "PERSON" in final_chunk["aptly"]["response_pii_entities"]


@pytest.mark.asyncio
async def test_chat_completion_redact_response_option(client, mock_supabase):
    """Optional redact_response parameter redacts PII in response content."""
    setup_auth_mocks(mock_supabase)

    with patch("src.compliance.audit_logger.supabase") as audit_mock:
        audit_table = MagicMock()
        audit_mock.table.return_value = audit_table
        audit_table.insert.return_value = audit_table
        audit_table.execute.return_value = MagicMock(data=[{"id": "log_redact123"}])

        with patch("src.main.PIIRedactor") as mock_redactor_class:
            mock_redactor = MagicMock()
            mock_redactor_class.return_value = mock_redactor

            mock_redactor.redact_messages.return_value = (
                [{"role": "user", "content": "Who is the CEO?"}],
                [],
            )

            # Return RedactionResult with redacted content
            response_pii = PIIDetection(
                type="PERSON",
                replacement="PERSON_A",
                confidence=0.95,
                start=11,
                end=19,
            )
            mock_redactor.redact.return_value = RedactionResult(
                redacted_text="The CEO is PERSON_A.",  # Redacted content
                detections=[response_pii],
                pii_detected=True,
            )

            with patch("src.main.call_llm") as mock_call_llm:
                mock_call_llm.return_value = LLMResponse(
                    id="chatcmpl-redact",
                    model="gpt-4",
                    content="The CEO is John Smith.",  # Original content
                    finish_reason="stop",
                    tokens_input=5,
                    tokens_output=8,
                    cost_usd=Decimal("0.0005"),
                )

                response = await client.post(
                    "/v1/chat/completions",
                    headers={"Authorization": f"Bearer {TEST_API_KEY}"},
                    json={
                        "model": "gpt-4",
                        "messages": [{"role": "user", "content": "Who is the CEO?"}],
                        "api_keys": {"openai": "sk-test123"},
                        "redact_response": True,  # Enable response redaction
                    },
                )

    assert response.status_code == 200
    data = response.json()

    # Response content should be redacted
    assert data["choices"][0]["message"]["content"] == "The CEO is PERSON_A."
    assert data["aptly"]["response_pii_detected"] is True
