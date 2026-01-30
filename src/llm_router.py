import json
import structlog
from typing import AsyncIterator, Any
from dataclasses import dataclass
from decimal import Decimal

from litellm import acompletion
from litellm.exceptions import (
    AuthenticationError,
    RateLimitError,
    ServiceUnavailableError,
)

logger = structlog.get_logger()

# Provider to API key mapping
PROVIDER_KEY_MAPPING = {
    "openai": "openai",
    "anthropic": "anthropic",
    "google": "google",
    "cohere": "cohere",
    "together": "together",
    "together_ai": "together",
}

# Approximate costs per 1K tokens (simplified pricing)
MODEL_COSTS = {
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "claude-3-opus": {"input": 0.015, "output": 0.075},
    "claude-3-sonnet": {"input": 0.003, "output": 0.015},
    "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
    "claude-3-5-sonnet": {"input": 0.003, "output": 0.015},
    "gemini-pro": {"input": 0.00025, "output": 0.0005},
    "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
}


@dataclass
class LLMResponse:
    """Response from LLM provider."""

    id: str
    model: str
    content: str
    finish_reason: str | None
    tokens_input: int
    tokens_output: int
    cost_usd: Decimal


@dataclass
class StreamChunk:
    """A single chunk from a streaming response."""

    id: str
    content: str | None
    finish_reason: str | None
    is_final: bool


def detect_provider(model: str) -> str:
    """
    Detect LLM provider from model name.

    Args:
        model: The model name (e.g., "gpt-4", "claude-3-opus")

    Returns:
        Provider name (openai, anthropic, google, cohere, together)

    Raises:
        ValueError: If provider cannot be detected
    """
    model_lower = model.lower()

    if model_lower.startswith(("gpt", "o1", "o3")):
        return "openai"
    elif model_lower.startswith("claude"):
        return "anthropic"
    elif model_lower.startswith("gemini"):
        return "google"
    elif model_lower.startswith("command"):
        return "cohere"
    elif "llama" in model_lower or "mixtral" in model_lower:
        return "together"
    else:
        raise ValueError(f"Unknown model: {model}")


def get_api_key_for_provider(provider: str, api_keys: dict[str, str]) -> str:
    """
    Get the API key for a provider from the api_keys dict.

    Args:
        provider: The provider name
        api_keys: Dict of provider -> api_key

    Returns:
        The API key

    Raises:
        ValueError: If no API key found for provider
    """
    # Check direct match
    if provider in api_keys:
        return api_keys[provider]

    # Check aliases
    key_name = PROVIDER_KEY_MAPPING.get(provider, provider)
    if key_name in api_keys:
        return api_keys[key_name]

    raise ValueError(f"No API key provided for provider: {provider}")


def calculate_cost(model: str, tokens_input: int, tokens_output: int) -> Decimal:
    """Calculate estimated cost based on token usage."""
    # Find matching cost config
    model_lower = model.lower()
    costs = None

    for model_prefix, model_costs in MODEL_COSTS.items():
        if model_lower.startswith(model_prefix.lower()):
            costs = model_costs
            break

    if not costs:
        return Decimal("0")

    input_cost = Decimal(str(costs["input"])) * tokens_input / 1000
    output_cost = Decimal(str(costs["output"])) * tokens_output / 1000

    return input_cost + output_cost


async def call_llm(
    model: str,
    messages: list[dict],
    api_keys: dict[str, str],
    stream: bool = False,
    **kwargs: Any,
) -> LLMResponse | AsyncIterator[StreamChunk]:
    """
    Call LLM provider via LiteLLM.

    Args:
        model: The model to use
        messages: Chat messages
        api_keys: Provider API keys
        stream: Enable streaming
        **kwargs: Additional parameters (temperature, max_tokens, etc.)

    Returns:
        LLMResponse for non-streaming, AsyncIterator[StreamChunk] for streaming

    Raises:
        ValueError: Invalid model or missing API key
        AuthenticationError: Invalid provider API key
        RateLimitError: Provider rate limit exceeded
        ServiceUnavailableError: Provider unavailable
    """
    provider = detect_provider(model)
    api_key = get_api_key_for_provider(provider, api_keys)

    logger.info(
        "llm_request",
        model=model,
        provider=provider,
        stream=stream,
        message_count=len(messages),
    )

    if stream:
        return _stream_completion(model, messages, api_key, **kwargs)
    else:
        return await _call_completion(model, messages, api_key, **kwargs)


async def _call_completion(
    model: str,
    messages: list[dict],
    api_key: str,
    **kwargs: Any,
) -> LLMResponse:
    """Make a non-streaming completion call."""
    try:
        response = await acompletion(
            model=model,
            messages=messages,
            api_key=api_key,
            **kwargs,
        )

        # Extract response data
        choice = response.choices[0]
        usage = response.usage

        tokens_input = usage.prompt_tokens if usage else 0
        tokens_output = usage.completion_tokens if usage else 0

        return LLMResponse(
            id=response.id,
            model=response.model,
            content=choice.message.content or "",
            finish_reason=choice.finish_reason,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            cost_usd=calculate_cost(model, tokens_input, tokens_output),
        )

    except AuthenticationError as e:
        logger.warning("llm_auth_error", model=model, error=str(e))
        raise
    except RateLimitError as e:
        logger.warning("llm_rate_limit", model=model, error=str(e))
        raise
    except ServiceUnavailableError as e:
        logger.error("llm_unavailable", model=model, error=str(e))
        raise


async def _stream_completion(
    model: str,
    messages: list[dict],
    api_key: str,
    **kwargs: Any,
) -> AsyncIterator[StreamChunk]:
    """Make a streaming completion call."""
    try:
        response = await acompletion(
            model=model,
            messages=messages,
            api_key=api_key,
            stream=True,
            **kwargs,
        )

        response_id = None
        async for chunk in response:
            if not response_id and hasattr(chunk, "id"):
                response_id = chunk.id

            choice = chunk.choices[0] if chunk.choices else None
            if not choice:
                continue

            delta = choice.delta
            content = delta.content if delta else None
            finish_reason = choice.finish_reason

            yield StreamChunk(
                id=response_id or "unknown",
                content=content,
                finish_reason=finish_reason,
                is_final=finish_reason is not None,
            )

    except AuthenticationError as e:
        logger.warning("llm_auth_error_stream", model=model, error=str(e))
        raise
    except RateLimitError as e:
        logger.warning("llm_rate_limit_stream", model=model, error=str(e))
        raise
    except ServiceUnavailableError as e:
        logger.error("llm_unavailable_stream", model=model, error=str(e))
        raise


def format_sse_event(data: dict) -> str:
    """Format a dict as a Server-Sent Event."""
    return f"data: {json.dumps(data)}\n\n"


def format_sse_done() -> str:
    """Format the done event for SSE."""
    return "data: [DONE]\n\n"
