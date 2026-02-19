"""Postgres integration for historical GTM data queries."""

from __future__ import annotations

from typing import Any

import structlog
from sqlalchemy import text

from backend.config import Settings
from backend.db.session import AsyncSessionLocal
from backend.integrations.base import BaseIntegration

logger = structlog.get_logger(__name__)


class PostgresIntegration(BaseIntegration):
    """Direct Postgres queries for historical data and analytics."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)

    async def health_check(self) -> None:
        """Verify Postgres connectivity."""
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))

    async def query(self, sql: str, params: dict | None = None) -> list[dict[str, Any]]:
        """Execute a read-only SQL query and return results as dicts."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(text(sql), params or {})
            rows = result.fetchall()
            columns = list(result.keys())
            return [dict(zip(columns, row)) for row in rows]

    async def get_lead_source_breakdown(
        self,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return lead count grouped by source."""
        where_parts = []
        params: dict = {}
        if date_from:
            where_parts.append("created_at >= :date_from")
            params["date_from"] = date_from
        if date_to:
            where_parts.append("created_at <= :date_to")
            params["date_to"] = date_to

        where = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""
        sql = f"""
            SELECT lead_source, COUNT(*) AS lead_count,
                   SUM(CASE WHEN status = 'converted' THEN 1 ELSE 0 END) AS converted_count
            FROM leads
            {where}
            GROUP BY lead_source
            ORDER BY lead_count DESC
        """
        return await self.query(sql, params)

    async def get_historical_win_rates(
        self,
        months_back: int = 12,
    ) -> list[dict[str, Any]]:
        """Return monthly win rates from closed opportunities."""
        sql = """
            SELECT
                DATE_TRUNC('month', close_date) AS month,
                COUNT(*) AS total_deals,
                SUM(CASE WHEN outcome = 'won' THEN 1 ELSE 0 END) AS won_deals,
                ROUND(
                    SUM(CASE WHEN outcome = 'won' THEN 1 ELSE 0 END)::numeric
                    / NULLIF(COUNT(*), 0) * 100, 2
                ) AS win_rate_pct,
                SUM(CASE WHEN outcome = 'won' THEN amount ELSE 0 END) AS won_revenue
            FROM closed_deals
            WHERE close_date >= NOW() - (:months * INTERVAL '1 month')
            GROUP BY DATE_TRUNC('month', close_date)
            ORDER BY month ASC
        """
        return await self.query(sql, {"months": months_back})

    async def get_renewal_pipeline(
        self,
        days_ahead: int = 90,
    ) -> list[dict[str, Any]]:
        """Return upcoming contract renewals."""
        sql = """
            SELECT
                account_id, account_name, contract_value, renewal_date,
                health_score, csm_owner, contract_type
            FROM renewals
            WHERE renewal_date BETWEEN NOW() AND NOW() + (:days * INTERVAL '1 day')
            ORDER BY renewal_date ASC
        """
        return await self.query(sql, {"days": days_ahead})
