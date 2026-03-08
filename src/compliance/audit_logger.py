import structlog
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import AuditLog

logger = structlog.get_logger()


@dataclass
class AuditLogEntry:
    """Data for creating an audit log entry."""

    provider: str
    model: str
    request_data: dict[str, Any]
    response_data: dict[str, Any] | None = None
    user_id: str | None = None
    pii_detected: list[dict] | None = None
    response_pii_detected: list[dict] | None = None
    tokens_input: int | None = None
    tokens_output: int | None = None
    latency_ms: int | None = None
    cost_usd: Decimal | None = None
    compliance_framework: str | None = None


class AuditLogger:
    """Immutable audit log writer."""

    async def log(self, entry: AuditLogEntry, session: AsyncSession) -> str:
        """Create an immutable audit log entry."""
        log_record = AuditLog(
            provider=entry.provider,
            model=entry.model,
            request_data=entry.request_data,
            response_data=entry.response_data,
            user_id=entry.user_id,
            pii_detected=entry.pii_detected or [],
            response_pii_detected=entry.response_pii_detected or [],
            tokens_input=entry.tokens_input,
            tokens_output=entry.tokens_output,
            latency_ms=entry.latency_ms,
            cost_usd=float(entry.cost_usd) if entry.cost_usd is not None else None,
            compliance_framework=entry.compliance_framework,
        )

        try:
            session.add(log_record)
            await session.commit()
            await session.refresh(log_record)

            log_id = str(log_record.id)
            logger.info(
                "audit_log_created",
                log_id=log_id,
                provider=entry.provider,
                model=entry.model,
            )
            return log_id

        except Exception as e:
            await session.rollback()
            logger.error("audit_log_failed", error=str(e))
            raise

    async def get_log(self, log_id: str, session: AsyncSession) -> dict | None:
        """Retrieve a single audit log entry."""
        try:
            result = await session.execute(
                select(AuditLog).where(AuditLog.id == log_id)
            )
            row = result.scalar_one_or_none()
            if row is None:
                return None
            return _row_to_dict(row)
        except Exception:
            return None

    async def query_logs(
        self,
        session: AsyncSession,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        user_id: str | None = None,
        model: str | None = None,
        limit: int = 50,
        page: int = 1,
    ) -> tuple[list[dict], int]:
        """Query audit logs with filtering and pagination."""
        limit = min(max(1, limit), 100)
        offset = (page - 1) * limit

        conditions = []
        if start_date:
            conditions.append(AuditLog.created_at >= start_date)
        if end_date:
            conditions.append(AuditLog.created_at <= end_date)
        if user_id:
            conditions.append(AuditLog.user_id == user_id)
        if model:
            conditions.append(AuditLog.model == model)

        try:
            count_query = select(func.count(AuditLog.id))
            if conditions:
                count_query = count_query.where(*conditions)
            count_result = await session.execute(count_query)
            total = count_result.scalar() or 0

            fetch_query = (
                select(
                    AuditLog.id, AuditLog.user_id, AuditLog.provider, AuditLog.model,
                    AuditLog.tokens_input, AuditLog.tokens_output, AuditLog.latency_ms,
                    AuditLog.cost_usd, AuditLog.pii_detected, AuditLog.compliance_framework,
                    AuditLog.created_at,
                )
                .order_by(AuditLog.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            if conditions:
                fetch_query = fetch_query.where(*conditions)
            result = await session.execute(fetch_query)
            logs = [
                {
                    "id": str(row.id),
                    "user_id": row.user_id,
                    "provider": row.provider,
                    "model": row.model,
                    "tokens_input": row.tokens_input,
                    "tokens_output": row.tokens_output,
                    "latency_ms": row.latency_ms,
                    "cost_usd": float(row.cost_usd) if row.cost_usd is not None else None,
                    "pii_detected": row.pii_detected or [],
                    "compliance_framework": row.compliance_framework,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
                for row in result
            ]
            return logs, total
        except Exception as e:
            logger.error("audit_log_query_failed", error=str(e))
            return [], 0

    async def get_usage_stats(
        self,
        start_date: datetime,
        end_date: datetime,
        session: AsyncSession,
    ) -> dict:
        """Get usage statistics over a time period."""
        try:
            result = await session.execute(
                select(
                    func.count(AuditLog.id).label("count"),
                    func.coalesce(func.sum(AuditLog.tokens_input), 0).label("tokens_in"),
                    func.coalesce(func.sum(AuditLog.tokens_output), 0).label("tokens_out"),
                )
                .where(
                    AuditLog.created_at >= start_date,
                    AuditLog.created_at <= end_date,
                )
            )
            row = result.one()
            return {
                "requests": row.count,
                "tokens": row.tokens_in + row.tokens_out,
            }
        except Exception:
            return {"requests": 0, "tokens": 0}


def _row_to_dict(row: AuditLog) -> dict:
    """Convert an AuditLog ORM instance to a dict."""
    return {
        "id": str(row.id),
        "user_id": row.user_id,
        "provider": row.provider,
        "model": row.model,
        "request_data": row.request_data,
        "response_data": row.response_data,
        "pii_detected": row.pii_detected or [],
        "response_pii_detected": row.response_pii_detected or [],
        "tokens_input": row.tokens_input,
        "tokens_output": row.tokens_output,
        "latency_ms": row.latency_ms,
        "cost_usd": float(row.cost_usd) if row.cost_usd is not None else None,
        "compliance_framework": row.compliance_framework,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


# Global instance
audit_logger = AuditLogger()
