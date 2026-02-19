"""LangChain tools wrapping the Postgres integration."""

from __future__ import annotations

from typing import Any, Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from backend.integrations.postgres import PostgresIntegration


class GetLeadSourcesInput(BaseModel):
    date_from: Optional[str] = Field(default=None, description="Start date YYYY-MM-DD")
    date_to: Optional[str] = Field(default=None, description="End date YYYY-MM-DD")


class GetHistoricalWinRatesInput(BaseModel):
    months_back: int = Field(default=12, ge=1, le=36, description="Number of months to look back")


class GetRenewalPipelineInput(BaseModel):
    days_ahead: int = Field(default=90, ge=1, le=365, description="Look-ahead window in days")


def build_postgres_tools(client: PostgresIntegration) -> list:
    """Return list of LangChain tools bound to a PostgresIntegration instance."""

    @tool("get_lead_sources", args_schema=GetLeadSourcesInput)
    async def get_lead_sources(
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Get lead source breakdown from the database. Returns lead counts and conversion rates by source channel."""
        return await client.get_lead_source_breakdown(date_from=date_from, date_to=date_to)

    @tool("get_historical_win_rates", args_schema=GetHistoricalWinRatesInput)
    async def get_historical_win_rates(months_back: int = 12) -> list[dict[str, Any]]:
        """Get historical deal win rates by month. Returns win rate percentage and won revenue for forecasting baseline."""
        return await client.get_historical_win_rates(months_back=months_back)

    @tool("get_renewal_pipeline", args_schema=GetRenewalPipelineInput)
    async def get_renewal_pipeline(days_ahead: int = 90) -> list[dict[str, Any]]:
        """Get upcoming contract renewals within a look-ahead window. Returns account, contract value, health score, and renewal date."""
        return await client.get_renewal_pipeline(days_ahead=days_ahead)

    return [get_lead_sources, get_historical_win_rates, get_renewal_pipeline]
