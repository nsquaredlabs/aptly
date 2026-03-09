"""Tests for the chat completions endpoint - THE MAIN FEATURE."""

import json
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone
from decimal import Decimal

from tests.conftest import TEST_API_SECRET
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
            data = line[6:]
            if data != "[DONE]":
                events.append(json.loads(data))
            else:
                events.append({"done": True})
    return events


@pytest.mark.asyncio
async def test_chat_completion_basic(client):
    """Basic chat completion works."""
    with patch("src.main.audit_logger") as mock_audit:
        mock_audit.log = AsyncMock(return_value="log_test123")

        with patch("src.main.call_llm") as mock_call_llm:
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
                headers={"Authorization": f"Bearer {TEST_API_SECRET}"},
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
async def test_chat_completion_pii_redaction(client):
    """PII is detected and redacted before sending to LLM."""
    with patch("src.main.audit_logger") as mock_audit:
        mock_audit.log = AsyncMock(return_value="log_test123")

        with patch("src.main.PIIRedactor") as mock_redactor_class:
            mock_redactor = MagicMock()
            mock_redactor_class.return_value = mock_redactor

            mock_redactor.redact_messages.return_value = (
                [{"role": "user", "content": "Patient PERSON_A has diabetes."}],
                [
                    PIIDetection(
                        type="PERSON",
                        replacement="PERSON_A",
                        confidence=0.95,
                        start=8,
                        end=18,
                        original_value="John Smith",
                    )
                ],
            )

            # Mock unredact to return content as-is (no placeholders in LLM response)
            mock_redactor.unredact.side_effect = lambda text, _: text

            # Mock redact for response PII scan
            mock_redactor.redact.return_value = RedactionResult(
                redacted_text="I understand.",
                detections=[],
                pii_detected=False,
            )

            with patch("src.main.call_llm") as mock_call_llm:
                mock_call_llm.return_value = LLMResponse(
                    id="chatcmpl-test123",
                    model="gpt-4",
                    content="I understand.",
                    finish_reason="stop",
                    tokens_input=10,
                    tokens_output=5,
                    cost_usd=Decimal("0.0005"),
                )

                response = await client.post(
                    "/v1/chat/completions",
                    headers={"Authorization": f"Bearer {TEST_API_SECRET}"},
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
    assert data["aptly"]["pii_detected"] is True
    assert "PERSON" in data["aptly"]["pii_entities"]
    mock_redactor.redact_messages.assert_called_once()


@pytest.mark.asyncio
async def test_chat_completion_audit_log_created(client):
    """Every request creates an audit log entry."""
    with patch("src.main.audit_logger") as mock_audit:
        mock_audit.log = AsyncMock(return_value="log_test123")

        with patch("src.main.call_llm") as mock_call_llm:
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
                headers={"Authorization": f"Bearer {TEST_API_SECRET}"},
                json={
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": "Hi"}],
                    "api_keys": {"openai": "sk-test123"},
                },
            )

    assert response.status_code == 200
    mock_audit.log.assert_called_once()
    data = response.json()
    assert data["aptly"]["audit_log_id"] == "log_test123"


@pytest.mark.asyncio
async def test_chat_completion_missing_api_keys(client):
    """Returns 422 when api_keys not provided."""
    response = await client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {TEST_API_SECRET}"},
        json={
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_completion_missing_provider_key(client):
    """Returns 400 when API key for required provider is missing."""
    response = await client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {TEST_API_SECRET}"},
        json={
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}],
            "api_keys": {"anthropic": "sk-ant-test"},
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert data["detail"]["error"]["code"] == "INVALID_REQUEST"


@pytest.mark.asyncio
async def test_chat_completion_invalid_model(client):
    """Returns 400 for unknown model."""
    response = await client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {TEST_API_SECRET}"},
        json={
            "model": "unknown-model-xyz",
            "messages": [{"role": "user", "content": "Hello"}],
            "api_keys": {"openai": "sk-test123"},
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_chat_completion_rate_limited(client):
    """Returns 429 when rate limit exceeded."""
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
            headers={"Authorization": f"Bearer {TEST_API_SECRET}"},
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
async def test_chat_completion_unauthorized(client):
    """Returns 401 for missing API secret."""
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
async def test_chat_completion_streaming_basic(client):
    """Verify streaming returns SSE format with correct headers."""
    with patch("src.main.audit_logger") as mock_audit:
        mock_audit.log = AsyncMock(return_value="log_stream123")

        with patch("src.main.call_llm") as mock_call_llm:
            chunks = create_stream_chunks(["Hello", " world", "!"])
            mock_call_llm.return_value = mock_stream_generator(chunks)

            response = await client.post(
                "/v1/chat/completions",
                headers={"Authorization": f"Bearer {TEST_API_SECRET}"},
                json={
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": "Hi"}],
                    "api_keys": {"openai": "sk-test123"},
                    "stream": True,
                },
            )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_chat_completion_streaming_chunks(client):
    """Verify chunks are yielded with correct structure."""
    with patch("src.main.audit_logger") as mock_audit:
        mock_audit.log = AsyncMock(return_value="log_stream123")

        with patch("src.main.call_llm") as mock_call_llm:
            chunks = create_stream_chunks(["Hello", " there"])
            mock_call_llm.return_value = mock_stream_generator(chunks)

            response = await client.post(
                "/v1/chat/completions",
                headers={"Authorization": f"Bearer {TEST_API_SECRET}"},
                json={
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": "Hi"}],
                    "api_keys": {"openai": "sk-test123"},
                    "stream": True,
                },
            )

    assert response.status_code == 200
    events = parse_sse_events(response.text)
    data_events = [e for e in events if "done" not in e]
    assert len(data_events) >= 2
    first_chunk = data_events[0]
    assert first_chunk["object"] == "chat.completion.chunk"


@pytest.mark.asyncio
async def test_chat_completion_streaming_final_chunk(client):
    """Verify final chunk contains aptly metadata."""
    with patch("src.main.audit_logger") as mock_audit:
        mock_audit.log = AsyncMock(return_value="log_final123")

        with patch("src.main.call_llm") as mock_call_llm:
            chunks = create_stream_chunks(["Response", " complete"])
            mock_call_llm.return_value = mock_stream_generator(chunks)

            response = await client.post(
                "/v1/chat/completions",
                headers={"Authorization": f"Bearer {TEST_API_SECRET}"},
                json={
                    "model": "gpt-4",
                    "messages": [{"role": "user", "content": "Hi"}],
                    "api_keys": {"openai": "sk-test123"},
                    "stream": True,
                },
            )

    assert response.status_code == 200
    events = parse_sse_events(response.text)
    data_events = [e for e in events if "done" not in e]

    # Find the final chunk (with aptly metadata)
    final_chunks = [e for e in data_events if "aptly" in e]
    assert len(final_chunks) == 1
    assert final_chunks[0]["aptly"]["audit_log_id"] == "log_final123"


@pytest.mark.asyncio
async def test_chat_completion_response_pii_detection(client):
    """PII in LLM response is detected and reported."""
    with patch("src.main.audit_logger") as mock_audit:
        mock_audit.log = AsyncMock(return_value="log_resp_pii")

        with patch("src.main.PIIRedactor") as mock_redactor_class:
            mock_redactor = MagicMock()
            mock_redactor_class.return_value = mock_redactor

            # No PII in input
            mock_redactor.redact_messages.return_value = (
                [{"role": "user", "content": "Tell me about the patient."}],
                [],
            )

            # Mock unredact to return content as-is
            mock_redactor.unredact.side_effect = lambda text, _: text

            # PII in response
            mock_redactor.redact.return_value = RedactionResult(
                redacted_text="PERSON_A is doing well.",
                detections=[
                    PIIDetection(type="PERSON", replacement="PERSON_A", confidence=0.9, start=0, end=10, original_value="John Smith")
                ],
                pii_detected=True,
            )

            with patch("src.main.call_llm") as mock_call_llm:
                mock_call_llm.return_value = LLMResponse(
                    id="chatcmpl-resp-pii",
                    model="gpt-4",
                    content="John Smith is doing well.",
                    finish_reason="stop",
                    tokens_input=10,
                    tokens_output=10,
                    cost_usd=Decimal("0.001"),
                )

                response = await client.post(
                    "/v1/chat/completions",
                    headers={"Authorization": f"Bearer {TEST_API_SECRET}"},
                    json={
                        "model": "gpt-4",
                        "messages": [{"role": "user", "content": "Tell me about the patient."}],
                        "api_keys": {"openai": "sk-test123"},
                    },
                )

    assert response.status_code == 200
    data = response.json()
    assert data["aptly"]["response_pii_detected"] is True
    assert "PERSON" in data["aptly"]["response_pii_entities"]


@pytest.mark.asyncio
async def test_chat_completion_llm_error(client):
    """Returns 502 for LLM provider errors."""
    with patch("src.main.call_llm") as mock_call_llm:
        mock_call_llm.side_effect = Exception("Provider timeout")

        response = await client.post(
            "/v1/chat/completions",
            headers={"Authorization": f"Bearer {TEST_API_SECRET}"},
            json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": "Hello"}],
                "api_keys": {"openai": "sk-test123"},
            },
        )

    assert response.status_code == 502
    data = response.json()
    assert data["detail"]["error"]["code"] == "PROVIDER_ERROR"


@pytest.mark.asyncio
async def test_chat_completion_unredacts_response(client):
    """LLM response containing redaction placeholders is un-redacted for the user."""
    with patch("src.main.audit_logger") as mock_audit:
        mock_audit.log = AsyncMock(return_value="log_unredact")

        with patch("src.main.PIIRedactor") as mock_redactor_class:
            mock_redactor = MagicMock()
            mock_redactor_class.return_value = mock_redactor
            mock_redactor.mode = "mask"

            # Input PII redaction: "My name is John Smith" → "My name is PERSON_A"
            mock_redactor.redact_messages.return_value = (
                [{"role": "user", "content": "My name is PERSON_A"}],
                [
                    PIIDetection(
                        type="PERSON",
                        replacement="PERSON_A",
                        confidence=0.95,
                        start=11,
                        end=21,
                        original_value="John Smith",
                    )
                ],
            )

            # unredact replaces PERSON_A → John Smith in LLM response
            mock_redactor.unredact.return_value = "Hello John Smith"

            # Response PII scan on the unredacted content
            mock_redactor.redact.return_value = RedactionResult(
                redacted_text="Hello PERSON_A",
                detections=[
                    PIIDetection(
                        type="PERSON",
                        replacement="PERSON_A",
                        confidence=0.95,
                        start=6,
                        end=16,
                        original_value="John Smith",
                    )
                ],
                pii_detected=True,
            )

            with patch("src.main.call_llm") as mock_call_llm:
                mock_call_llm.return_value = LLMResponse(
                    id="chatcmpl-unredact",
                    model="gpt-4",
                    content="Hello PERSON_A",
                    finish_reason="stop",
                    tokens_input=10,
                    tokens_output=5,
                    cost_usd=Decimal("0.0005"),
                )

                response = await client.post(
                    "/v1/chat/completions",
                    headers={"Authorization": f"Bearer {TEST_API_SECRET}"},
                    json={
                        "model": "gpt-4",
                        "messages": [
                            {"role": "user", "content": "My name is John Smith"}
                        ],
                        "api_keys": {"openai": "sk-test123"},
                    },
                )

    assert response.status_code == 200
    data = response.json()
    # The user-facing response should contain the original PII (un-redacted)
    assert "John Smith" in data["choices"][0]["message"]["content"]
    assert "PERSON_A" not in data["choices"][0]["message"]["content"]
    mock_redactor.unredact.assert_called_once()


@pytest.mark.asyncio
async def test_chat_completion_audit_log_stays_redacted(client):
    """Audit log stores the raw LLM response (redacted), not the un-redacted version."""
    with patch("src.main.audit_logger") as mock_audit:
        mock_audit.log = AsyncMock(return_value="log_audit_redacted")

        with patch("src.main.PIIRedactor") as mock_redactor_class:
            mock_redactor = MagicMock()
            mock_redactor_class.return_value = mock_redactor
            mock_redactor.mode = "mask"

            mock_redactor.redact_messages.return_value = (
                [{"role": "user", "content": "My name is PERSON_A"}],
                [
                    PIIDetection(
                        type="PERSON",
                        replacement="PERSON_A",
                        confidence=0.95,
                        start=11,
                        end=21,
                        original_value="John Smith",
                    )
                ],
            )

            mock_redactor.unredact.return_value = "Hello John Smith"

            mock_redactor.redact.return_value = RedactionResult(
                redacted_text="Hello PERSON_A",
                detections=[
                    PIIDetection(
                        type="PERSON",
                        replacement="PERSON_A",
                        confidence=0.95,
                        start=6,
                        end=16,
                        original_value="John Smith",
                    )
                ],
                pii_detected=True,
            )

            with patch("src.main.call_llm") as mock_call_llm:
                mock_call_llm.return_value = LLMResponse(
                    id="chatcmpl-audit-redact",
                    model="gpt-4",
                    content="Hello PERSON_A",
                    finish_reason="stop",
                    tokens_input=10,
                    tokens_output=5,
                    cost_usd=Decimal("0.0005"),
                )

                response = await client.post(
                    "/v1/chat/completions",
                    headers={"Authorization": f"Bearer {TEST_API_SECRET}"},
                    json={
                        "model": "gpt-4",
                        "messages": [
                            {"role": "user", "content": "My name is John Smith"}
                        ],
                        "api_keys": {"openai": "sk-test123"},
                    },
                )

    assert response.status_code == 200
    # Verify audit log was called with the raw LLM response (still redacted)
    mock_audit.log.assert_called_once()
    audit_entry = mock_audit.log.call_args[0][0]
    assert audit_entry.response_data["content"] == "Hello PERSON_A"
    assert "John Smith" not in audit_entry.response_data["content"]
