import structlog
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from src.supabase_client import supabase

logger = structlog.get_logger()


@dataclass
class AuditLogEntry:
    """Data for creating an audit log entry."""

    customer_id: str
    provider: str
    model: str
    request_data: dict[str, Any]
    response_data: dict[str, Any] | None = None
    user_id: str | None = None
    pii_detected: list[dict] | None = None
    response_pii_detected: list[dict] | None = None  # PII detected in LLM response
    tokens_input: int | None = None
    tokens_output: int | None = None
    latency_ms: int | None = None
    cost_usd: Decimal | None = None
    compliance_framework: str | None = None


class AuditLogger:
    """
    Immutable audit log writer.

    All chat completion requests are logged with:
    - Redacted request/response content (never stores original PII)
    - Token usage and cost metrics
    - PII detection results
    - Compliance framework tracking
    """

    async def log(self, entry: AuditLogEntry) -> str:
        """
        Create an immutable audit log entry.

        Args:
            entry: The audit log data to record

        Returns:
            The ID of the created audit log

        Raises:
            Exception: If the log could not be created
        """
        log_data = {
            "customer_id": entry.customer_id,
            "provider": entry.provider,
            "model": entry.model,
            "request_data": entry.request_data,
            "user_id": entry.user_id,
            "pii_detected": entry.pii_detected or [],
            "response_pii_detected": entry.response_pii_detected or [],
        }

        # Add optional fields if present
        if entry.response_data is not None:
            log_data["response_data"] = entry.response_data
        if entry.tokens_input is not None:
            log_data["tokens_input"] = entry.tokens_input
        if entry.tokens_output is not None:
            log_data["tokens_output"] = entry.tokens_output
        if entry.latency_ms is not None:
            log_data["latency_ms"] = entry.latency_ms
        if entry.cost_usd is not None:
            log_data["cost_usd"] = float(entry.cost_usd)
        if entry.compliance_framework:
            log_data["compliance_framework"] = entry.compliance_framework

        try:
            result = supabase.table("audit_logs").insert(log_data).execute()

            if result.data:
                log_id = result.data[0]["id"]
                logger.info(
                    "audit_log_created",
                    log_id=log_id,
                    customer_id=entry.customer_id,
                    provider=entry.provider,
                    model=entry.model,
                )
                return log_id
            else:
                raise Exception("No data returned from insert")

        except Exception as e:
            logger.error(
                "audit_log_failed",
                customer_id=entry.customer_id,
                error=str(e),
            )
            raise

    async def get_log(self, customer_id: str, log_id: str) -> dict | None:
        """
        Retrieve a single audit log entry.

        Args:
            customer_id: The customer's ID (for access control)
            log_id: The audit log ID

        Returns:
            The audit log data or None if not found
        """
        try:
            result = (
                supabase.table("audit_logs")
                .select("*")
                .eq("id", log_id)
                .eq("customer_id", customer_id)
                .single()
                .execute()
            )
            return result.data
        except Exception:
            return None

    async def query_logs(
        self,
        customer_id: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        user_id: str | None = None,
        model: str | None = None,
        limit: int = 50,
        page: int = 1,
    ) -> tuple[list[dict], int]:
        """
        Query audit logs with filtering and pagination.

        Args:
            customer_id: The customer's ID
            start_date: Filter logs after this date
            end_date: Filter logs before this date
            user_id: Filter by end-user ID
            model: Filter by model name
            limit: Results per page (max 100)
            page: Page number (1-indexed)

        Returns:
            (logs, total_count)
        """
        # Clamp limit
        limit = min(max(1, limit), 100)
        offset = (page - 1) * limit

        # Build query
        query = (
            supabase.table("audit_logs")
            .select(
                "id, user_id, provider, model, tokens_input, tokens_output, "
                "latency_ms, cost_usd, pii_detected, compliance_framework, created_at",
                count="exact",
            )
            .eq("customer_id", customer_id)
            .order("created_at", desc=True)
        )

        # Apply filters
        if start_date:
            query = query.gte("created_at", start_date.isoformat())
        if end_date:
            query = query.lte("created_at", end_date.isoformat())
        if user_id:
            query = query.eq("user_id", user_id)
        if model:
            query = query.eq("model", model)

        # Apply pagination
        query = query.range(offset, offset + limit - 1)

        try:
            result = query.execute()
            logs = result.data or []
            total = result.count or 0
            return logs, total
        except Exception as e:
            logger.error("audit_log_query_failed", error=str(e))
            return [], 0

    async def get_usage_stats(
        self,
        customer_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        """
        Get usage statistics for a customer over a time period.

        Args:
            customer_id: The customer's ID
            start_date: Start of the period
            end_date: End of the period

        Returns:
            Dict with request_count and token_count
        """
        try:
            result = (
                supabase.table("audit_logs")
                .select("id, tokens_input, tokens_output", count="exact")
                .eq("customer_id", customer_id)
                .gte("created_at", start_date.isoformat())
                .lte("created_at", end_date.isoformat())
                .execute()
            )

            request_count = result.count or 0
            total_tokens = sum(
                (log.get("tokens_input") or 0) + (log.get("tokens_output") or 0)
                for log in (result.data or [])
            )

            return {
                "requests": request_count,
                "tokens": total_tokens,
            }
        except Exception:
            return {"requests": 0, "tokens": 0}


# Global instance
audit_logger = AuditLogger()
