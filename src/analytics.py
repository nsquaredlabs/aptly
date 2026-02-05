"""Analytics service for aggregating audit log data."""

import structlog
from collections import defaultdict
from datetime import datetime, timedelta

from src.supabase_client import supabase

logger = structlog.get_logger()


class AnalyticsService:
    """Aggregates audit log data into analytics views."""

    def _fetch_logs(self, customer_id: str, start_date: datetime, end_date: datetime) -> list[dict]:
        """Fetch all audit logs for a customer in the given date range."""
        try:
            result = (
                supabase.table("audit_logs")
                .select("*")
                .eq("customer_id", customer_id)
                .gte("created_at", start_date.isoformat())
                .lte("created_at", end_date.isoformat())
                .order("created_at")
                .execute()
            )
            return result.data or []
        except Exception as e:
            logger.error("analytics_fetch_failed", error=str(e))
            return []

    @staticmethod
    def _parse_timestamp(value: str) -> datetime:
        """Parse a created_at timestamp string."""
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    @staticmethod
    def _date_bucket(dt: datetime, granularity: str) -> str:
        """Bucket a datetime into a date string by granularity."""
        if granularity == "week":
            monday = dt - timedelta(days=dt.weekday())
            return monday.strftime("%Y-%m-%d")
        if granularity == "month":
            return dt.strftime("%Y-%m-01")
        return dt.strftime("%Y-%m-%d")

    async def get_usage_summary(
        self,
        customer_id: str,
        start_date: datetime,
        end_date: datetime,
        granularity: str = "day",
    ) -> dict:
        logs = self._fetch_logs(customer_id, start_date, end_date)
        buckets: dict[str, dict] = {}
        total_latency_sum = 0
        total_latency_count = 0
        total_cost = 0.0
        total_tokens = 0

        for log in logs:
            ti = log.get("tokens_input") or 0
            to = log.get("tokens_output") or 0
            cost = float(log.get("cost_usd") or 0)
            lat = log.get("latency_ms")

            total_tokens += ti + to
            total_cost += cost
            if lat is not None:
                total_latency_sum += lat
                total_latency_count += 1

            bucket_key = self._date_bucket(
                self._parse_timestamp(log["created_at"]), granularity
            )
            if bucket_key not in buckets:
                buckets[bucket_key] = {
                    "requests": 0, "tokens_input": 0, "tokens_output": 0,
                    "cost_usd": 0.0, "latency_sum": 0, "latency_count": 0,
                }
            b = buckets[bucket_key]
            b["requests"] += 1
            b["tokens_input"] += ti
            b["tokens_output"] += to
            b["cost_usd"] += cost
            if lat is not None:
                b["latency_sum"] += lat
                b["latency_count"] += 1

        time_series = [
            {
                "date": key,
                "requests": b["requests"],
                "tokens_input": b["tokens_input"],
                "tokens_output": b["tokens_output"],
                "cost_usd": round(b["cost_usd"], 2),
                "avg_latency_ms": b["latency_sum"] // b["latency_count"] if b["latency_count"] else 0,
            }
            for key, b in sorted(buckets.items())
        ]

        return {
            "summary": {
                "total_requests": len(logs),
                "total_tokens": total_tokens,
                "total_cost_usd": round(total_cost, 2),
                "avg_latency_ms": total_latency_sum // total_latency_count if total_latency_count else 0,
                "period_start": start_date.strftime("%Y-%m-%d"),
                "period_end": end_date.strftime("%Y-%m-%d"),
            },
            "time_series": time_series,
        }

    async def get_model_breakdown(
        self,
        customer_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        logs = self._fetch_logs(customer_id, start_date, end_date)
        total_requests = len(logs)
        models: dict[tuple[str, str], dict] = {}

        for log in logs:
            key = (log.get("model") or "unknown", log.get("provider") or "unknown")
            if key not in models:
                models[key] = {
                    "requests": 0, "tokens_input": 0, "tokens_output": 0,
                    "cost_usd": 0.0, "latency_sum": 0, "latency_count": 0,
                }
            m = models[key]
            m["requests"] += 1
            m["tokens_input"] += log.get("tokens_input") or 0
            m["tokens_output"] += log.get("tokens_output") or 0
            m["cost_usd"] += float(log.get("cost_usd") or 0)
            lat = log.get("latency_ms")
            if lat is not None:
                m["latency_sum"] += lat
                m["latency_count"] += 1

        model_list = [
            {
                "model": model,
                "provider": provider,
                "requests": m["requests"],
                "tokens_input": m["tokens_input"],
                "tokens_output": m["tokens_output"],
                "cost_usd": round(m["cost_usd"], 2),
                "avg_latency_ms": m["latency_sum"] // m["latency_count"] if m["latency_count"] else 0,
                "percentage_of_requests": round(m["requests"] / total_requests * 100, 1) if total_requests else 0.0,
            }
            for (model, provider), m in sorted(models.items(), key=lambda x: x[1]["requests"], reverse=True)
        ]

        return {
            "models": model_list,
            "period_start": start_date.strftime("%Y-%m-%d"),
            "period_end": end_date.strftime("%Y-%m-%d"),
        }

    async def get_user_breakdown(
        self,
        customer_id: str,
        start_date: datetime,
        end_date: datetime,
        limit: int = 50,
    ) -> dict:
        logs = self._fetch_logs(customer_id, start_date, end_date)
        users: dict[str, dict] = {}
        no_id = {"requests": 0, "tokens_input": 0, "tokens_output": 0, "cost_usd": 0.0}

        for log in logs:
            user_id = log.get("user_id")
            ti = log.get("tokens_input") or 0
            to = log.get("tokens_output") or 0
            cost = float(log.get("cost_usd") or 0)

            if not user_id:
                no_id["requests"] += 1
                no_id["tokens_input"] += ti
                no_id["tokens_output"] += to
                no_id["cost_usd"] += cost
                continue

            if user_id not in users:
                users[user_id] = {
                    "requests": 0, "tokens_input": 0, "tokens_output": 0,
                    "cost_usd": 0.0, "last_active": "",
                }
            u = users[user_id]
            u["requests"] += 1
            u["tokens_input"] += ti
            u["tokens_output"] += to
            u["cost_usd"] += cost
            if log["created_at"] > u["last_active"]:
                u["last_active"] = log["created_at"]

        top_users = sorted(users.items(), key=lambda x: x[1]["requests"], reverse=True)[:limit]

        return {
            "users": [
                {
                    "user_id": uid,
                    "requests": s["requests"],
                    "tokens_input": s["tokens_input"],
                    "tokens_output": s["tokens_output"],
                    "cost_usd": round(s["cost_usd"], 2),
                    "last_active": s["last_active"],
                }
                for uid, s in top_users
            ],
            "users_with_no_id": {
                "requests": no_id["requests"],
                "tokens_input": no_id["tokens_input"],
                "tokens_output": no_id["tokens_output"],
                "cost_usd": round(no_id["cost_usd"], 2),
            },
            "total_unique_users": len(users),
            "period_start": start_date.strftime("%Y-%m-%d"),
            "period_end": end_date.strftime("%Y-%m-%d"),
        }

    async def get_pii_stats(
        self,
        customer_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        logs = self._fetch_logs(customer_id, start_date, end_date)
        total = len(logs)
        input_pii_count = 0
        response_pii_count = 0
        entity_input: dict[str, int] = defaultdict(int)
        entity_response: dict[str, int] = defaultdict(int)
        day_buckets: dict[str, dict] = {}

        for log in logs:
            input_entities = log.get("pii_detected") or []
            response_entities = log.get("response_pii_detected") or []
            has_input = len(input_entities) > 0
            has_response = len(response_entities) > 0

            if has_input:
                input_pii_count += 1
            if has_response:
                response_pii_count += 1

            for e in input_entities:
                entity_input[e.get("type", "UNKNOWN")] += 1
            for e in response_entities:
                entity_response[e.get("type", "UNKNOWN")] += 1

            day = self._parse_timestamp(log["created_at"]).strftime("%Y-%m-%d")
            if day not in day_buckets:
                day_buckets[day] = {"total": 0, "with_pii": 0}
            day_buckets[day]["total"] += 1
            if has_input or has_response:
                day_buckets[day]["with_pii"] += 1

        all_types = sorted(set(entity_input) | set(entity_response))
        entity_types = sorted(
            [
                {
                    "type": t,
                    "input_count": entity_input.get(t, 0),
                    "response_count": entity_response.get(t, 0),
                    "total_count": entity_input.get(t, 0) + entity_response.get(t, 0),
                }
                for t in all_types
            ],
            key=lambda x: x["total_count"],
            reverse=True,
        )

        return {
            "summary": {
                "requests_with_input_pii": input_pii_count,
                "requests_with_response_pii": response_pii_count,
                "total_requests": total,
                "input_pii_rate": round(input_pii_count / total * 100, 1) if total else 0.0,
                "response_pii_rate": round(response_pii_count / total * 100, 1) if total else 0.0,
            },
            "entity_types": entity_types,
            "time_series": [
                {
                    "date": day,
                    "requests_with_pii": b["with_pii"],
                    "total_requests": b["total"],
                    "pii_rate": round(b["with_pii"] / b["total"] * 100, 1) if b["total"] else 0.0,
                }
                for day, b in sorted(day_buckets.items())
            ],
            "period_start": start_date.strftime("%Y-%m-%d"),
            "period_end": end_date.strftime("%Y-%m-%d"),
        }

    async def get_export_data(
        self,
        customer_id: str,
        start_date: datetime,
        end_date: datetime,
        include: list[str] | None = None,
    ) -> list[dict]:
        """Return per-day aggregated rows for CSV/JSON export."""
        if include is None:
            include = ["usage", "models", "users", "pii"]

        logs = self._fetch_logs(customer_id, start_date, end_date)
        days: dict[str, dict] = {}

        for log in logs:
            day = self._parse_timestamp(log["created_at"]).strftime("%Y-%m-%d")
            if day not in days:
                days[day] = {
                    "requests": 0, "tokens_input": 0, "tokens_output": 0,
                    "cost_usd": 0.0, "latency_sum": 0, "latency_count": 0,
                    "pii_count": 0, "model_counts": defaultdict(int),
                }
            d = days[day]
            d["requests"] += 1
            d["tokens_input"] += log.get("tokens_input") or 0
            d["tokens_output"] += log.get("tokens_output") or 0
            d["cost_usd"] += float(log.get("cost_usd") or 0)

            lat = log.get("latency_ms")
            if lat is not None:
                d["latency_sum"] += lat
                d["latency_count"] += 1

            input_pii = log.get("pii_detected") or []
            response_pii = log.get("response_pii_detected") or []
            if input_pii or response_pii:
                d["pii_count"] += 1

            d["model_counts"][log.get("model") or "unknown"] += 1

        rows = []
        for day in sorted(days):
            d = days[day]
            top_model = max(d["model_counts"], key=d["model_counts"].get) if d["model_counts"] else ""
            rows.append({
                "date": day,
                "requests": d["requests"],
                "tokens_input": d["tokens_input"],
                "tokens_output": d["tokens_output"],
                "cost_usd": round(d["cost_usd"], 2),
                "avg_latency_ms": d["latency_sum"] // d["latency_count"] if d["latency_count"] else 0,
                "pii_detected_count": d["pii_count"],
                "top_model": top_model,
            })

        return rows


# Global instance
analytics_service = AnalyticsService()
