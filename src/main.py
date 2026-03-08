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
from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db import get_db


# Initialize Sentry if DSN is configured
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        release=f"aptly@{settings.api_version}",
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            StarletteIntegration(transaction_style="endpoint"),
        ],
        send_default_pii=False,
    )
from src.auth import ApiAuth
from src.rate_limiter import rate_limiter, get_rate_limit_headers
from src.compliance.pii_redactor import PIIRedactor
from src.compliance.audit_logger import audit_logger, AuditLogEntry
from src.compliance.framework_entities import get_entities_for_frameworks
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
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    redact_response: bool = False


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
async def health_check(session: AsyncSession = Depends(get_db)):
    """Health check endpoint - no authentication required."""
    checks = {"database": "ok", "redis": "ok"}

    # Check database
    try:
        from sqlalchemy import text
        await session.execute(text("SELECT 1"))
    except Exception:
        checks["database"] = "error"

    # Check Redis
    if settings.redis_url:
        try:
            r = redis.from_url(settings.redis_url)
            await r.ping()
            await r.close()
        except Exception:
            checks["redis"] = "error"
    else:
        checks["redis"] = "disabled"

    all_ok = all(v in ("ok", "disabled") for v in checks.values())
    status_value = "healthy" if all_ok else "degraded"

    return {
        "status": status_value,
        "version": settings.api_version,
        "checks": checks,
    }


# ============================================================================
# Chat Completions
# ============================================================================


@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    _auth: ApiAuth,
    response: Response,
    session: AsyncSession = Depends(get_db),
):
    """
    OpenAI-compatible chat completion endpoint with PII redaction.

    Requires API secret authentication.
    """
    start_time = time.time()

    # Check rate limit (global)
    rate_result = await rate_limiter.check_rate_limit(
        "global",
        settings.rate_limit_per_hour,
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

    # Get framework-specific entities to detect
    entities = get_entities_for_frameworks(settings.compliance_frameworks)

    logger.info(
        "pii_redaction_starting",
        frameworks=settings.compliance_frameworks,
        entity_count=len(entities),
    )

    # Initialize PII redactor with configured mode and framework-specific entities
    redactor = PIIRedactor(
        mode=settings.pii_redaction_mode,
        entities=entities,
    )

    # Redact PII from messages
    messages_dict = [m.model_dump() for m in request.messages]
    redacted_messages, pii_detections = redactor.redact_messages(messages_dict)

    # Get compliance framework (use first one if multiple)
    compliance_framework = (
        settings.compliance_frameworks[0] if settings.compliance_frameworks else None
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
            redacted_messages=redacted_messages,
            pii_detections=pii_detections,
            provider=provider,
            compliance_framework=compliance_framework,
            start_time=start_time,
            llm_kwargs=llm_kwargs,
            redactor=redactor,
            session=session,
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
        ),
        session=session,
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
    redacted_messages: list[dict],
    pii_detections: list,
    provider: str,
    compliance_framework: str | None,
    start_time: float,
    llm_kwargs: dict,
    redactor: PIIRedactor,
    session: AsyncSession,
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
                            provider=provider,
                            model=request.model,
                            request_data={"messages": redacted_messages},
                            response_data={"content": full_content},
                            user_id=request.user,
                            pii_detected=pii_log_data,
                            response_pii_detected=response_pii_log_data,
                            tokens_input=0,
                            tokens_output=0,
                            latency_ms=latency_ms,
                            compliance_framework=compliance_framework,
                        ),
                        session=session,
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
# Audit Logs
# ============================================================================


@app.get("/v1/logs", response_model=AuditLogsResponse)
async def query_logs(
    _auth: ApiAuth,
    session: AsyncSession = Depends(get_db),
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
        session=session,
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
    _auth: ApiAuth,
    session: AsyncSession = Depends(get_db),
):
    """Get detailed audit log entry."""
    log = await audit_logger.get_log(log_id, session)

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
    _auth: ApiAuth,
    session: AsyncSession = Depends(get_db),
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
        start_date=_parse_date(start_date, now - timedelta(days=30)),
        end_date=_parse_date(end_date, now),
        session=session,
        granularity=granularity,
    )


@app.get("/v1/analytics/models", response_model=ModelBreakdownResponse)
async def analytics_models(
    _auth: ApiAuth,
    session: AsyncSession = Depends(get_db),
    start_date: str | None = None,
    end_date: str | None = None,
):
    """Breakdown of usage by model."""
    now = datetime.now(timezone.utc)
    return await analytics_service.get_model_breakdown(
        start_date=_parse_date(start_date, now - timedelta(days=30)),
        end_date=_parse_date(end_date, now),
        session=session,
    )


@app.get("/v1/analytics/users", response_model=UserBreakdownResponse)
async def analytics_users(
    _auth: ApiAuth,
    session: AsyncSession = Depends(get_db),
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 50,
):
    """Breakdown of usage by end-user."""
    now = datetime.now(timezone.utc)
    return await analytics_service.get_user_breakdown(
        start_date=_parse_date(start_date, now - timedelta(days=30)),
        end_date=_parse_date(end_date, now),
        session=session,
        limit=min(max(1, limit), 100),
    )


@app.get("/v1/analytics/pii", response_model=PIIStatsResponse)
async def analytics_pii(
    _auth: ApiAuth,
    session: AsyncSession = Depends(get_db),
    start_date: str | None = None,
    end_date: str | None = None,
):
    """PII detection statistics."""
    now = datetime.now(timezone.utc)
    return await analytics_service.get_pii_stats(
        start_date=_parse_date(start_date, now - timedelta(days=30)),
        end_date=_parse_date(end_date, now),
        session=session,
    )


@app.get("/v1/analytics/export")
async def analytics_export(
    _auth: ApiAuth,
    start_date: str,
    end_date: str,
    session: AsyncSession = Depends(get_db),
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
        start_date=start_dt,
        end_date=end_dt,
        session=session,
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
