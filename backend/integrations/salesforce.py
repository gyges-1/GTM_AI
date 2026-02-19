"""Salesforce CRM integration client."""

from __future__ import annotations

from typing import Any

import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.config import Settings
from backend.integrations.base import BaseIntegration

logger = structlog.get_logger(__name__)


class SalesforceClient(BaseIntegration):
    """Wraps simple-salesforce for opportunities and accounts."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
        self._sf = None

    def _get_client(self):
        if self._sf is None:
            from simple_salesforce import Salesforce
            self._sf = Salesforce(
                username=self.settings.sf_username,
                password=self.settings.sf_password,
                security_token=self.settings.sf_security_token,
                domain=self.settings.sf_domain,
            )
        return self._sf

    async def health_check(self) -> None:
        """Verify Salesforce connectivity."""
        import asyncio
        sf = self._get_client()
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: sf.query("SELECT Id FROM Opportunity LIMIT 1"))

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def get_opportunities(
        self,
        stage: str | None = None,
        close_date_after: str | None = None,
        close_date_before: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """Query Salesforce opportunities with optional filters."""
        import asyncio

        conditions = ["IsClosed = false"]
        if stage:
            conditions.append(f"StageName = '{stage}'")
        if close_date_after:
            conditions.append(f"CloseDate >= {close_date_after}")
        if close_date_before:
            conditions.append(f"CloseDate <= {close_date_before}")

        where = " AND ".join(conditions)
        soql = (
            f"SELECT Id, Name, Amount, StageName, CloseDate, Probability, "
            f"AccountId, OwnerId, ForecastCategoryName "
            f"FROM Opportunity WHERE {where} LIMIT {limit}"
        )

        sf = self._get_client()
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: sf.query(soql))
        return result.get("records", [])

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def get_accounts(
        self,
        segment: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """Query Salesforce accounts."""
        import asyncio

        conditions = []
        if segment:
            conditions.append(f"Segment__c = '{segment}'")

        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
        soql = (
            f"SELECT Id, Name, Industry, AnnualRevenue, NumberOfEmployees, "
            f"Type, BillingCountry, OwnerId "
            f"FROM Account{where} LIMIT {limit}"
        )

        sf = self._get_client()
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: sf.query(soql))
        return result.get("records", [])

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def get_opportunities_by_close_date(
        self,
        year: int,
        quarter: int | None = None,
        month: int | None = None,
    ) -> list[dict[str, Any]]:
        """Get opportunities closing in a specific period."""
        import asyncio

        if quarter:
            q_months = {1: ("01", "03"), 2: ("04", "06"), 3: ("07", "09"), 4: ("10", "12")}
            start_m, end_m = q_months[quarter]
            date_filter = f"CloseDate >= {year}-{start_m}-01 AND CloseDate <= {year}-{end_m}-30"
        elif month:
            date_filter = f"CloseDate >= {year}-{month:02d}-01 AND CloseDate <= {year}-{month:02d}-28"
        else:
            date_filter = f"CloseDate >= {year}-01-01 AND CloseDate <= {year}-12-31"

        soql = (
            f"SELECT Id, Name, Amount, StageName, CloseDate, Probability, "
            f"ForecastCategoryName, AccountId "
            f"FROM Opportunity WHERE {date_filter} ORDER BY CloseDate ASC LIMIT 500"
        )

        sf = self._get_client()
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: sf.query(soql))
        return result.get("records", [])
