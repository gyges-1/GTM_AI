"""LangChain tools wrapping the Salesforce integration."""

from __future__ import annotations

from typing import Any, Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from backend.integrations.salesforce import SalesforceClient


class GetOpportunitiesInput(BaseModel):
    stage: Optional[str] = Field(default=None, description="Filter by StageName e.g. 'Proposal/Price Quote'")
    close_date_after: Optional[str] = Field(default=None, description="ISO date string YYYY-MM-DD")
    close_date_before: Optional[str] = Field(default=None, description="ISO date string YYYY-MM-DD")
    limit: int = Field(default=100, ge=1, le=500)


class GetAccountsInput(BaseModel):
    segment: Optional[str] = Field(default=None, description="Account segment e.g. 'Enterprise', 'SMB'")
    limit: int = Field(default=100, ge=1, le=500)


class GetOpportunitiesByCloseDateInput(BaseModel):
    year: int = Field(..., description="Year e.g. 2025")
    quarter: Optional[int] = Field(default=None, ge=1, le=4, description="Fiscal quarter 1-4")
    month: Optional[int] = Field(default=None, ge=1, le=12, description="Month number 1-12")


def build_salesforce_tools(client: SalesforceClient) -> list:
    """Return list of LangChain tools bound to a SalesforceClient instance."""

    @tool("get_salesforce_opportunities", args_schema=GetOpportunitiesInput)
    async def get_salesforce_opportunities(
        stage: Optional[str] = None,
        close_date_after: Optional[str] = None,
        close_date_before: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Retrieve Salesforce opportunities. Filter by stage and/or close date range. Returns opportunity details including amount and probability."""
        return await client.get_opportunities(
            stage=stage,
            close_date_after=close_date_after,
            close_date_before=close_date_before,
            limit=limit,
        )

    @tool("get_salesforce_accounts", args_schema=GetAccountsInput)
    async def get_salesforce_accounts(
        segment: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Retrieve Salesforce accounts. Optionally filter by segment. Returns account name, industry, revenue, and size."""
        return await client.get_accounts(segment=segment, limit=limit)

    @tool("get_sf_opportunities_by_close_date", args_schema=GetOpportunitiesByCloseDateInput)
    async def get_sf_opportunities_by_close_date(
        year: int,
        quarter: Optional[int] = None,
        month: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """Get Salesforce opportunities closing in a specific year, quarter, or month. Essential for revenue forecasting."""
        return await client.get_opportunities_by_close_date(year=year, quarter=quarter, month=month)

    return [get_salesforce_opportunities, get_salesforce_accounts, get_sf_opportunities_by_close_date]
