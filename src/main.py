import time
import csv
import io
import json
import structlog
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Any

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from fastapi import FastAPI, HTTPException, Response, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, EmailStr
import redis.asyncio as redis

from src.config import settings


# Initialize Sentry if DSN is configured
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        release=f"aptly@{settings.api_version}",
        traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
        profiles_sample_rate=0.1,  # 10% of sampled transactions for profiling
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            StarletteIntegration(transaction_style="endpoint"),
        ],
        # Don't send PII to Sentry
        send_default_pii=False,
    )
from src.supabase_client import supabase
from src.auth import (
    AdminAuth,
    CustomerAuth,
    generate_api_key,
    hash_api_key,
)
from src.rate_limiter import rate_limiter, get_rate_limit_headers
from src.compliance.pii_redactor import PIIRedactor
from src.compliance.audit_logger import audit_logger, AuditLogEntry
from src.llm_router import (
    call_llm,
    detect_provider,
    format_sse_event,
    format_sse_done,
    LLMResponse,
)
from src.analytics import analytics_service

logger = structlog.get_logger()


# ============================================================================
# Lifespan
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("starting_aptly", environment=settings.environment)
    yield
    # Cleanup
    await rate_limiter.close()
    logger.info("stopping_aptly")


app = FastAPI(
    title="Aptly API",
    description="Compliance-as-a-service middleware for LLM requests",
    version=settings.api_version,
    lifespan=lifespan,
    servers=[
        {
            "url": "https://api-aptly.nsquaredlabs.com",
            "description": "Production server"
        }
    ],
)


# ============================================================================
# Request/Response Models
# ============================================================================


class ErrorDetail(BaseModel):
    type: str
    message: str
    code: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


# Admin Models
class CreateCustomerRequest(BaseModel):
    email: EmailStr
    company_name: str | None = None
    plan: str = "free"
    compliance_frameworks: list[str] = Field(default_factory=list)


class CustomerResponse(BaseModel):
    id: str
    email: str
    company_name: str | None
    plan: str
    compliance_frameworks: list[str]
    retention_days: int
    pii_redaction_mode: str
    created_at: datetime


class APIKeyResponse(BaseModel):
    id: str
    key: str | None = None  # Only returned on creation
    key_prefix: str
    name: str | None
    rate_limit_per_hour: int
    created_at: datetime


class CreateCustomerResponse(BaseModel):
    customer: CustomerResponse
    api_key: APIKeyResponse


class CreateAPIKeyRequest(BaseModel):
    name: str | None = None
    rate_limit_per_hour: int = 1000


# Chat Completion Models
class ChatMessage(BaseModel):
    role: str
    content: str | list[dict]


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    api_keys: dict[str, str]
    user: str | None = None
    stream: bool = False
    temperature: float | None = None
    max_tokens: int | None = None
    top_p: float | None = None
    frequency_penalty: float | None = None
    presence_penalty: float | None = None
    stop: str | list[str] | None = None
    redact_response: bool = False  # If True, redact PII in response content


class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str | None


class ChatCompletionUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class AptlyMetadata(BaseModel):
    audit_log_id: str
    pii_detected: bool
    pii_entities: list[str]
    response_pii_detected: bool
    response_pii_entities: list[str]
    compliance_framework: str | None
    latency_ms: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatCompletionChoice]
    usage: ChatCompletionUsage
    aptly: AptlyMetadata


# Audit Log Models
class AuditLogSummary(BaseModel):
    id: str
    user_id: str | None
    provider: str
    model: str
    tokens_input: int | None
    tokens_output: int | None
    latency_ms: int | None
    cost_usd: float | None
    pii_detected: list[dict]
    compliance_framework: str | None
    created_at: datetime


class AuditLogDetail(AuditLogSummary):
    request_data: dict
    response_data: dict | None


class PaginationInfo(BaseModel):
    total: int
    page: int
    per_page: int
    total_pages: int


class AuditLogsResponse(BaseModel):
    logs: list[AuditLogSummary]
    pagination: PaginationInfo


# Customer Profile Models
class UsageInfo(BaseModel):
    requests_this_month: int
    tokens_this_month: int
    rate_limit_per_hour: int
    requests_this_hour: int


class CustomerProfileResponse(BaseModel):
    id: str
    email: str
    company_name: str | None
    plan: str
    compliance_frameworks: list[str]
    retention_days: int
    pii_redaction_mode: str
    created_at: datetime
    usage: UsageInfo


class UpdateCustomerRequest(BaseModel):
    pii_redaction_mode: str | None = None
    compliance_frameworks: list[str] | None = None


# Analytics Models
class UsageDataPoint(BaseModel):
    date: str
    requests: int
    tokens_input: int
    tokens_output: int
    cost_usd: float
    avg_latency_ms: int


class UsageSummaryInfo(BaseModel):
    total_requests: int
    total_tokens: int
    total_cost_usd: float
    avg_latency_ms: int
    period_start: str
    period_end: str


class UsageSummaryResponse(BaseModel):
    summary: UsageSummaryInfo
    time_series: list[UsageDataPoint]


class ModelData(BaseModel):
    model: str
    provider: str
    requests: int
    tokens_input: int
    tokens_output: int
    cost_usd: float
    avg_latency_ms: int
    percentage_of_requests: float


class ModelBreakdownResponse(BaseModel):
    models: list[ModelData]
    period_start: str
    period_end: str


class UserData(BaseModel):
    user_id: str
    requests: int
    tokens_input: int
    tokens_output: int
    cost_usd: float
    last_active: str


class UsersWithNoId(BaseModel):
    requests: int
    tokens_input: int
    tokens_output: int
    cost_usd: float


class UserBreakdownResponse(BaseModel):
    users: list[UserData]
    users_with_no_id: UsersWithNoId
    total_unique_users: int
    period_start: str
    period_end: str


class PIISummaryInfo(BaseModel):
    requests_with_input_pii: int
    requests_with_response_pii: int
    total_requests: int
    input_pii_rate: float
    response_pii_rate: float


class PIIEntityType(BaseModel):
    type: str
    input_count: int
    response_count: int
    total_count: int


class PIIDataPoint(BaseModel):
    date: str
    requests_with_pii: int
    total_requests: int
    pii_rate: float


class PIIStatsResponse(BaseModel):
    summary: PIISummaryInfo
    entity_types: list[PIIEntityType]
    time_series: list[PIIDataPoint]
    period_start: str
    period_end: str


# ============================================================================
# Health Check
# ============================================================================


@app.get("/v1/health")
async def health_check():
    """Health check endpoint - no authentication required."""
    checks = {"database": "ok", "redis": "ok"}

    # Check database
    try:
        supabase.table("customers").select("id").limit(1).execute()
    except Exception:
        checks["database"] = "error"

    # Check Redis
    try:
        r = redis.from_url(settings.redis_url)
        await r.ping()
        await r.close()
    except Exception:
        checks["redis"] = "error"

    status_value = "healthy" if all(v == "ok" for v in checks.values()) else "degraded"

    return {
        "status": status_value,
        "version": settings.api_version,
        "checks": checks,
    }


# ============================================================================
# Admin Endpoints
# ============================================================================


@app.post(
    "/v1/admin/customers",
    response_model=CreateCustomerResponse,
    status_code=status.HTTP_201_CREATED,
)
async def admin_create_customer(
    request: CreateCustomerRequest,
    _: AdminAuth,
):
    """Create a new customer. Admin authentication required."""
    # Check if customer already exists
    existing = (
        supabase.table("customers")
        .select("id")
        .eq("email", request.email)
        .execute()
    )
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "type": "conflict",
                    "message": f"Customer with email {request.email} already exists",
                    "code": "CONFLICT",
                }
            },
        )

    # Create customer
    customer_data = {
        "email": request.email,
        "company_name": request.company_name,
        "plan": request.plan,
        "compliance_frameworks": request.compliance_frameworks,
    }

    try:
        customer_result = supabase.table("customers").insert(customer_data).execute()
        customer = customer_result.data[0]
    except Exception as e:
        logger.error("customer_creation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "type": "internal_error",
                    "message": "Failed to create customer",
                    "code": "INTERNAL_ERROR",
                }
            },
        )

    # Generate and store API key
    full_key, key_hash, key_prefix = generate_api_key("live")

    api_key_data = {
        "customer_id": customer["id"],
        "key_hash": key_hash,
        "key_prefix": key_prefix,
        "name": "Default API Key",
        "rate_limit_per_hour": settings.rate_limit_free
        if request.plan == "free"
        else settings.rate_limit_pro,
    }

    try:
        key_result = supabase.table("api_keys").insert(api_key_data).execute()
        api_key = key_result.data[0]
    except Exception as e:
        # Rollback customer creation
        supabase.table("customers").delete().eq("id", customer["id"]).execute()
        logger.error("api_key_creation_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "type": "internal_error",
                    "message": "Failed to create API key",
                    "code": "INTERNAL_ERROR",
                }
            },
        )

    logger.info(
        "customer_created",
        customer_id=customer["id"],
        email=request.email,
        plan=request.plan,
    )

    return CreateCustomerResponse(
        customer=CustomerResponse(
            id=customer["id"],
            email=customer["email"],
            company_name=customer.get("company_name"),
            plan=customer["plan"],
            compliance_frameworks=customer.get("compliance_frameworks", []),
            retention_days=customer.get("retention_days", 2555),
            pii_redaction_mode=customer.get("pii_redaction_mode", "mask"),
            created_at=customer["created_at"],
        ),
        api_key=APIKeyResponse(
            id=api_key["id"],
            key=full_key,  # Only returned on creation
            key_prefix=api_key["key_prefix"],
            name=api_key.get("name"),
            rate_limit_per_hour=api_key.get("rate_limit_per_hour", 1000),
            created_at=api_key["created_at"],
        ),
    )


@app.get("/v1/admin/customers")
async def admin_list_customers(
    _: AdminAuth,
    limit: int = 50,
    offset: int = 0,
):
    """List all customers. Admin authentication required."""
    result = (
        supabase.table("customers")
        .select("*", count="exact")
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )

    return {
        "customers": result.data,
        "total": result.count,
        "limit": limit,
        "offset": offset,
    }


@app.get("/v1/admin/customers/{customer_id}")
async def admin_get_customer(
    customer_id: str,
    _: AdminAuth,
):
    """Get customer details with API keys and usage. Admin authentication required."""
    # Get customer
    try:
        customer_result = (
            supabase.table("customers")
            .select("*")
            .eq("id", customer_id)
            .single()
            .execute()
        )
        customer = customer_result.data
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "type": "not_found",
                    "message": "Customer not found",
                    "code": "NOT_FOUND",
                }
            },
        )

    # Get API keys
    keys_result = (
        supabase.table("api_keys")
        .select("id, key_prefix, name, is_revoked, created_at, last_used_at, rate_limit_per_hour")
        .eq("customer_id", customer_id)
        .execute()
    )

    # Get usage stats
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    usage = await audit_logger.get_usage_stats(customer_id, month_start, now)

    return {
        "customer": customer,
        "api_keys": keys_result.data,
        "usage": {
            "requests_this_month": usage["requests"],
            "tokens_this_month": usage["tokens"],
        },
    }


@app.post(
    "/v1/admin/customers/{customer_id}/api-keys",
    response_model=APIKeyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def admin_create_api_key(
    customer_id: str,
    request: CreateAPIKeyRequest,
    _: AdminAuth,
):
    """Create an API key for a customer. Admin authentication required."""
    # Verify customer exists
    try:
        supabase.table("customers").select("id").eq("id", customer_id).single().execute()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "type": "not_found",
                    "message": "Customer not found",
                    "code": "NOT_FOUND",
                }
            },
        )

    # Generate and store API key
    full_key, key_hash, key_prefix = generate_api_key("live")

    api_key_data = {
        "customer_id": customer_id,
        "key_hash": key_hash,
        "key_prefix": key_prefix,
        "name": request.name,
        "rate_limit_per_hour": request.rate_limit_per_hour,
    }

    key_result = supabase.table("api_keys").insert(api_key_data).execute()
    api_key = key_result.data[0]

    return APIKeyResponse(
        id=api_key["id"],
        key=full_key,
        key_prefix=api_key["key_prefix"],
        name=api_key.get("name"),
        rate_limit_per_hour=api_key.get("rate_limit_per_hour", 1000),
        created_at=api_key["created_at"],
    )


# ============================================================================
# Chat Completions
# ============================================================================


@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    auth: CustomerAuth,
    response: Response,
):
    """
    OpenAI-compatible chat completion endpoint with PII redaction.

    Requires customer API key authentication.
    """
    start_time = time.time()
    customer = auth.customer
    api_key_info = auth.api_key

    # Check rate limit
    rate_result = await rate_limiter.check_rate_limit(
        customer.id,
        api_key_info.rate_limit_per_hour,
    )

    # Add rate limit headers
    for header, value in get_rate_limit_headers(rate_result).items():
        response.headers[header] = value

    if not rate_result.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": {
                    "type": "rate_limit_exceeded",
                    "message": f"Rate limit exceeded. Limit: {rate_result.limit} requests per hour.",
                    "code": "RATE_LIMIT_EXCEEDED",
                    "details": {
                        "limit": rate_result.limit,
                        "current": rate_result.current_count,
                        "reset_at": rate_result.reset_at.isoformat(),
                    },
                }
            },
        )

    # Validate model
    try:
        provider = detect_provider(request.model)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "type": "invalid_request",
                    "message": f"Unknown model: {request.model}",
                    "code": "INVALID_REQUEST",
                }
            },
        )

    # Check if API key is provided for the provider
    if provider not in request.api_keys and provider.replace("_", "") not in request.api_keys:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "type": "invalid_request",
                    "message": f"Missing API key for provider: {provider}",
                    "code": "INVALID_REQUEST",
                }
            },
        )

    # Initialize PII redactor with customer's mode
    redactor = PIIRedactor(mode=customer.pii_redaction_mode)

    # Redact PII from messages
    messages_dict = [m.model_dump() for m in request.messages]
    redacted_messages, pii_detections = redactor.redact_messages(messages_dict)

    # Get compliance framework (use first one if multiple)
    compliance_framework = (
        customer.compliance_frameworks[0] if customer.compliance_frameworks else None
    )

    # Build LLM kwargs
    llm_kwargs = {}
    if request.temperature is not None:
        llm_kwargs["temperature"] = request.temperature
    if request.max_tokens is not None:
        llm_kwargs["max_tokens"] = request.max_tokens
    if request.top_p is not None:
        llm_kwargs["top_p"] = request.top_p
    if request.frequency_penalty is not None:
        llm_kwargs["frequency_penalty"] = request.frequency_penalty
    if request.presence_penalty is not None:
        llm_kwargs["presence_penalty"] = request.presence_penalty
    if request.stop is not None:
        llm_kwargs["stop"] = request.stop

    # Handle streaming
    if request.stream:
        return await _handle_streaming_completion(
            request=request,
            customer=customer,
            redacted_messages=redacted_messages,
            pii_detections=pii_detections,
            provider=provider,
            compliance_framework=compliance_framework,
            start_time=start_time,
            llm_kwargs=llm_kwargs,
            redactor=redactor,
        )

    # Non-streaming completion
    try:
        llm_response: LLMResponse = await call_llm(
            model=request.model,
            messages=redacted_messages,
            api_keys=request.api_keys,
            stream=False,
            **llm_kwargs,
        )
    except Exception as e:
        error_type = type(e).__name__
        if "Authentication" in error_type:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "error": {
                        "type": "payment_required",
                        "message": "LLM provider rejected the API key",
                        "code": "PAYMENT_REQUIRED",
                    }
                },
            )
        elif "RateLimit" in error_type:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": {
                        "type": "provider_rate_limit",
                        "message": "LLM provider rate limit exceeded",
                        "code": "RATE_LIMIT_EXCEEDED",
                    }
                },
            )
        else:
            logger.error("llm_error", error=str(e), error_type=error_type)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail={
                    "error": {
                        "type": "provider_error",
                        "message": f"LLM provider error: {str(e)}",
                        "code": "PROVIDER_ERROR",
                    }
                },
            )

    latency_ms = int((time.time() - start_time) * 1000)

    # Scan response content for PII
    response_content = llm_response.content
    response_redaction_result = redactor.redact(response_content)
    response_pii_detections = response_redaction_result.detections

    # Optionally redact response content
    if request.redact_response and response_pii_detections:
        response_content = response_redaction_result.redacted_text

    # Create audit log
    pii_log_data = [
        {"type": d.type, "replacement": d.replacement, "confidence": d.confidence}
        for d in pii_detections
    ]
    response_pii_log_data = [
        {"type": d.type, "replacement": d.replacement, "confidence": d.confidence}
        for d in response_pii_detections
    ]

    audit_log_id = await audit_logger.log(
        AuditLogEntry(
            customer_id=customer.id,
            provider=provider,
            model=request.model,
            request_data={"messages": redacted_messages},
            response_data={"content": response_content},
            user_id=request.user,
            pii_detected=pii_log_data,
            response_pii_detected=response_pii_log_data,
            tokens_input=llm_response.tokens_input,
            tokens_output=llm_response.tokens_output,
            latency_ms=latency_ms,
            cost_usd=llm_response.cost_usd,
            compliance_framework=compliance_framework,
        )
    )

    # Build response
    return ChatCompletionResponse(
        id=llm_response.id,
        created=int(time.time()),
        model=llm_response.model,
        choices=[
            ChatCompletionChoice(
                index=0,
                message=ChatMessage(role="assistant", content=response_content),
                finish_reason=llm_response.finish_reason,
            )
        ],
        usage=ChatCompletionUsage(
            prompt_tokens=llm_response.tokens_input,
            completion_tokens=llm_response.tokens_output,
            total_tokens=llm_response.tokens_input + llm_response.tokens_output,
        ),
        aptly=AptlyMetadata(
            audit_log_id=audit_log_id,
            pii_detected=len(pii_detections) > 0,
            pii_entities=list(set(d.type for d in pii_detections)),
            response_pii_detected=len(response_pii_detections) > 0,
            response_pii_entities=list(set(d.type for d in response_pii_detections)),
            compliance_framework=compliance_framework,
            latency_ms=latency_ms,
        ),
    )


async def _handle_streaming_completion(
    request: ChatCompletionRequest,
    customer,
    redacted_messages: list[dict],
    pii_detections: list,
    provider: str,
    compliance_framework: str | None,
    start_time: float,
    llm_kwargs: dict,
    redactor: PIIRedactor,
):
    """Handle streaming chat completion."""

    async def generate():
        full_content = ""
        response_id = None
        finish_reason = None

        try:
            stream = await call_llm(
                model=request.model,
                messages=redacted_messages,
                api_keys=request.api_keys,
                stream=True,
                **llm_kwargs,
            )

            async for chunk in stream:
                response_id = chunk.id
                if chunk.content:
                    full_content += chunk.content

                if chunk.finish_reason:
                    finish_reason = chunk.finish_reason

                # Format as OpenAI-compatible SSE
                chunk_data = {
                    "id": chunk.id,
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": request.model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"content": chunk.content} if chunk.content else {},
                            "finish_reason": chunk.finish_reason,
                        }
                    ],
                }

                # Add aptly metadata on final chunk
                if chunk.is_final:
                    latency_ms = int((time.time() - start_time) * 1000)

                    # Scan accumulated response content for PII
                    response_redaction_result = redactor.redact(full_content)
                    response_pii_detections = response_redaction_result.detections
                    response_pii_log_data = [
                        {"type": d.type, "replacement": d.replacement, "confidence": d.confidence}
                        for d in response_pii_detections
                    ]

                    # Create audit log
                    pii_log_data = [
                        {"type": d.type, "replacement": d.replacement, "confidence": d.confidence}
                        for d in pii_detections
                    ]

                    audit_log_id = await audit_logger.log(
                        AuditLogEntry(
                            customer_id=customer.id,
                            provider=provider,
                            model=request.model,
                            request_data={"messages": redacted_messages},
                            response_data={"content": full_content},
                            user_id=request.user,
                            pii_detected=pii_log_data,
                            response_pii_detected=response_pii_log_data,
                            tokens_input=0,  # Not available in streaming
                            tokens_output=0,
                            latency_ms=latency_ms,
                            compliance_framework=compliance_framework,
                        )
                    )

                    chunk_data["aptly"] = {
                        "audit_log_id": audit_log_id,
                        "pii_detected": len(pii_detections) > 0,
                        "response_pii_detected": len(response_pii_detections) > 0,
                        "response_pii_entities": list(set(d.type for d in response_pii_detections)),
                    }

                yield format_sse_event(chunk_data)

            yield format_sse_done()

        except Exception as e:
            error_data = {
                "error": {
                    "type": "provider_error",
                    "message": str(e),
                    "code": "PROVIDER_ERROR",
                }
            }
            yield format_sse_event(error_data)
            yield format_sse_done()

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


# ============================================================================
# Customer API Key Management
# ============================================================================


@app.get("/v1/api-keys")
async def list_api_keys(auth: CustomerAuth):
    """List customer's API keys."""
    result = (
        supabase.table("api_keys")
        .select("id, key_prefix, name, rate_limit_per_hour, is_revoked, created_at, last_used_at")
        .eq("customer_id", auth.customer.id)
        .eq("is_revoked", False)
        .order("created_at", desc=True)
        .execute()
    )

    return {"api_keys": result.data}


@app.post("/v1/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    request: CreateAPIKeyRequest,
    auth: CustomerAuth,
):
    """Create a new API key for the authenticated customer."""
    full_key, key_hash, key_prefix = generate_api_key("live")

    api_key_data = {
        "customer_id": auth.customer.id,
        "key_hash": key_hash,
        "key_prefix": key_prefix,
        "name": request.name,
        "rate_limit_per_hour": auth.api_key.rate_limit_per_hour,  # Inherit from current key
    }

    result = supabase.table("api_keys").insert(api_key_data).execute()
    api_key = result.data[0]

    return APIKeyResponse(
        id=api_key["id"],
        key=full_key,
        key_prefix=api_key["key_prefix"],
        name=api_key.get("name"),
        rate_limit_per_hour=api_key.get("rate_limit_per_hour", 1000),
        created_at=api_key["created_at"],
    )


@app.delete("/v1/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: str,
    auth: CustomerAuth,
):
    """Revoke an API key."""
    # Check if key exists and belongs to customer
    try:
        key_result = (
            supabase.table("api_keys")
            .select("id, customer_id")
            .eq("id", key_id)
            .eq("customer_id", auth.customer.id)
            .single()
            .execute()
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "type": "not_found",
                    "message": "API key not found",
                    "code": "NOT_FOUND",
                }
            },
        )

    # Check if trying to revoke current key
    if key_id == auth.api_key.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": {
                    "type": "conflict",
                    "message": "Cannot revoke the API key you're currently using",
                    "code": "CONFLICT",
                }
            },
        )

    # Revoke the key
    supabase.table("api_keys").update(
        {"is_revoked": True, "revoked_at": datetime.now(timezone.utc).isoformat()}
    ).eq("id", key_id).execute()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ============================================================================
# Audit Logs
# ============================================================================


@app.get("/v1/logs", response_model=AuditLogsResponse)
async def query_logs(
    auth: CustomerAuth,
    start_date: str | None = None,
    end_date: str | None = None,
    user_id: str | None = None,
    model: str | None = None,
    limit: int = 50,
    page: int = 1,
):
    """Query audit logs with filtering and pagination."""
    # Parse dates
    start_dt = None
    end_dt = None

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        except ValueError:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        except ValueError:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59, tzinfo=timezone.utc
            )

    # Default to last 30 days
    if not start_dt:
        start_dt = datetime.now(timezone.utc) - timedelta(days=30)
    if not end_dt:
        end_dt = datetime.now(timezone.utc)

    logs, total = await audit_logger.query_logs(
        customer_id=auth.customer.id,
        start_date=start_dt,
        end_date=end_dt,
        user_id=user_id,
        model=model,
        limit=limit,
        page=page,
    )

    total_pages = (total + limit - 1) // limit if total > 0 else 1

    return AuditLogsResponse(
        logs=[AuditLogSummary(**log) for log in logs],
        pagination=PaginationInfo(
            total=total,
            page=page,
            per_page=limit,
            total_pages=total_pages,
        ),
    )


@app.get("/v1/logs/{log_id}", response_model=AuditLogDetail)
async def get_log_detail(
    log_id: str,
    auth: CustomerAuth,
):
    """Get detailed audit log entry."""
    log = await audit_logger.get_log(auth.customer.id, log_id)

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "type": "not_found",
                    "message": "Audit log not found",
                    "code": "NOT_FOUND",
                }
            },
        )

    return AuditLogDetail(**log)


# ============================================================================
# Customer Profile
# ============================================================================


@app.get("/v1/me", response_model=CustomerProfileResponse)
async def get_profile(auth: CustomerAuth):
    """Get current customer's profile and usage."""
    customer = auth.customer

    # Get usage stats
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    usage = await audit_logger.get_usage_stats(customer.id, month_start, now)

    # Get current hour usage
    current_hour_usage = await rate_limiter.get_current_usage(customer.id)

    return CustomerProfileResponse(
        id=customer.id,
        email=customer.email,
        company_name=customer.company_name,
        plan=customer.plan,
        compliance_frameworks=customer.compliance_frameworks,
        retention_days=customer.retention_days,
        pii_redaction_mode=customer.pii_redaction_mode,
        created_at=customer.created_at,
        usage=UsageInfo(
            requests_this_month=usage["requests"],
            tokens_this_month=usage["tokens"],
            rate_limit_per_hour=auth.api_key.rate_limit_per_hour,
            requests_this_hour=current_hour_usage,
        ),
    )


@app.patch("/v1/me", response_model=CustomerResponse)
async def update_profile(
    request: UpdateCustomerRequest,
    auth: CustomerAuth,
):
    """Update customer settings."""
    update_data = {}

    if request.pii_redaction_mode is not None:
        if request.pii_redaction_mode not in ("mask", "hash", "remove"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "type": "invalid_request",
                        "message": "pii_redaction_mode must be one of: mask, hash, remove",
                        "code": "INVALID_REQUEST",
                    }
                },
            )
        update_data["pii_redaction_mode"] = request.pii_redaction_mode

    if request.compliance_frameworks is not None:
        update_data["compliance_frameworks"] = request.compliance_frameworks

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "type": "invalid_request",
                    "message": "No valid fields to update",
                    "code": "INVALID_REQUEST",
                }
            },
        )

    result = (
        supabase.table("customers")
        .update(update_data)
        .eq("id", auth.customer.id)
        .execute()
    )

    updated = result.data[0]

    return CustomerResponse(
        id=updated["id"],
        email=updated["email"],
        company_name=updated.get("company_name"),
        plan=updated["plan"],
        compliance_frameworks=updated.get("compliance_frameworks", []),
        retention_days=updated.get("retention_days", 2555),
        pii_redaction_mode=updated.get("pii_redaction_mode", "mask"),
        created_at=updated["created_at"],
    )


# ============================================================================
# Analytics
# ============================================================================


def _parse_date(date_str: str | None, default: datetime) -> datetime:
    """Parse an ISO date string, falling back to default."""
    if not date_str:
        return default
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)


@app.get("/v1/analytics/usage", response_model=UsageSummaryResponse)
async def analytics_usage(
    auth: CustomerAuth,
    start_date: str | None = None,
    end_date: str | None = None,
    granularity: str = "day",
):
    """Usage summary with time series data."""
    if granularity not in ("day", "week", "month"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "type": "invalid_request",
                    "message": "granularity must be one of: day, week, month",
                    "code": "INVALID_REQUEST",
                }
            },
        )

    now = datetime.now(timezone.utc)
    return await analytics_service.get_usage_summary(
        customer_id=auth.customer.id,
        start_date=_parse_date(start_date, now - timedelta(days=30)),
        end_date=_parse_date(end_date, now),
        granularity=granularity,
    )


@app.get("/v1/analytics/models", response_model=ModelBreakdownResponse)
async def analytics_models(
    auth: CustomerAuth,
    start_date: str | None = None,
    end_date: str | None = None,
):
    """Breakdown of usage by model."""
    now = datetime.now(timezone.utc)
    return await analytics_service.get_model_breakdown(
        customer_id=auth.customer.id,
        start_date=_parse_date(start_date, now - timedelta(days=30)),
        end_date=_parse_date(end_date, now),
    )


@app.get("/v1/analytics/users", response_model=UserBreakdownResponse)
async def analytics_users(
    auth: CustomerAuth,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 50,
):
    """Breakdown of usage by end-user."""
    now = datetime.now(timezone.utc)
    return await analytics_service.get_user_breakdown(
        customer_id=auth.customer.id,
        start_date=_parse_date(start_date, now - timedelta(days=30)),
        end_date=_parse_date(end_date, now),
        limit=min(max(1, limit), 100),
    )


@app.get("/v1/analytics/pii", response_model=PIIStatsResponse)
async def analytics_pii(
    auth: CustomerAuth,
    start_date: str | None = None,
    end_date: str | None = None,
):
    """PII detection statistics."""
    now = datetime.now(timezone.utc)
    return await analytics_service.get_pii_stats(
        customer_id=auth.customer.id,
        start_date=_parse_date(start_date, now - timedelta(days=30)),
        end_date=_parse_date(end_date, now),
    )


@app.get("/v1/analytics/export")
async def analytics_export(
    auth: CustomerAuth,
    start_date: str,
    end_date: str,
    format: str = "csv",
    include: str | None = None,
):
    """Export analytics data as CSV or JSON."""
    if format not in ("csv", "json"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "type": "invalid_request",
                    "message": "format must be one of: csv, json",
                    "code": "INVALID_REQUEST",
                }
            },
        )

    start_dt = _parse_date(start_date, datetime.now(timezone.utc))
    end_dt = _parse_date(end_date, datetime.now(timezone.utc))
    include_list = [s.strip() for s in include.split(",")] if include else None

    rows = await analytics_service.get_export_data(
        customer_id=auth.customer.id,
        start_date=start_dt,
        end_date=end_dt,
        include=include_list,
    )

    filename = f"aptly-analytics-{start_dt.strftime('%Y-%m')}"

    if format == "json":
        return Response(
            content=json.dumps(rows),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename}.json"'},
        )

    # CSV
    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    else:
        writer = csv.writer(output)
        writer.writerow(["date", "requests", "tokens_input", "tokens_output", "cost_usd", "avg_latency_ms", "pii_detected_count", "top_model"])

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}.csv"'},
    )
