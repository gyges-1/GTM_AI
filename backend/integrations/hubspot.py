"""HubSpot CRM integration client."""

from __future__ import annotations

from typing import Any

import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.config import Settings
from backend.integrations.base import BaseIntegration

logger = structlog.get_logger(__name__)


class HubSpotClient(BaseIntegration):
    """Wraps hubspot-api-client for contacts, deals, and campaigns."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
        self._hs = None

    def _get_client(self):
        if self._hs is None:
            import hubspot
            self._hs = hubspot.Client.create(access_token=self.settings.hubspot_access_token)
        return self._hs

    async def health_check(self) -> None:
        """Verify HubSpot connectivity by fetching account details."""
        import asyncio
        client = self._get_client()
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: client.crm.contacts.basic_api.get_page(limit=1))

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def get_contacts(
        self,
        limit: int = 100,
        properties: list[str] | None = None,
        filter_groups: list[dict] | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve CRM contacts with optional property filtering."""
        import asyncio

        props = properties or ["firstname", "lastname", "email", "company", "hs_lead_status", "createdate"]
        client = self._get_client()

        def _fetch():
            if filter_groups:
                from hubspot.crm.contacts import PublicObjectSearchRequest
                req = PublicObjectSearchRequest(
                    filter_groups=filter_groups,
                    properties=props,
                    limit=limit,
                )
                resp = client.crm.contacts.search_api.do_search(public_object_search_request=req)
            else:
                resp = client.crm.contacts.basic_api.get_page(limit=limit, properties=props)
            return [c.to_dict() for c in resp.results]

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _fetch)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def get_deals(
        self,
        limit: int = 100,
        pipeline_id: str | None = None,
        stage: str | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve deals with optional pipeline/stage filtering."""
        import asyncio

        props = [
            "dealname", "amount", "dealstage", "pipeline",
            "closedate", "hubspot_owner_id", "hs_deal_stage_probability",
        ]
        client = self._get_client()

        def _fetch():
            filter_groups = []
            if pipeline_id:
                filter_groups.append({
                    "filters": [{"propertyName": "pipeline", "operator": "EQ", "value": pipeline_id}]
                })
            if stage:
                filter_groups.append({
                    "filters": [{"propertyName": "dealstage", "operator": "EQ", "value": stage}]
                })

            if filter_groups:
                from hubspot.crm.deals import PublicObjectSearchRequest
                req = PublicObjectSearchRequest(
                    filter_groups=filter_groups,
                    properties=props,
                    limit=limit,
                )
                resp = client.crm.deals.search_api.do_search(public_object_search_request=req)
            else:
                resp = client.crm.deals.basic_api.get_page(limit=limit, properties=props)
            return [d.to_dict() for d in resp.results]

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _fetch)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def get_contact_health_scores(self, limit: int = 100) -> list[dict[str, Any]]:
        """Retrieve contact health score data."""
        import asyncio

        props = [
            "email", "company", "hs_lead_status",
            "hs_email_open_rate", "hs_email_click_rate",
            "notes_last_contacted", "num_contacted_notes",
        ]
        client = self._get_client()

        def _fetch():
            resp = client.crm.contacts.basic_api.get_page(limit=limit, properties=props)
            return [c.to_dict() for c in resp.results]

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _fetch)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def get_campaign_metrics(self) -> list[dict[str, Any]]:
        """Retrieve email campaign performance metrics."""
        import asyncio

        client = self._get_client()

        def _fetch():
            try:
                resp = client.marketing.emails.statistics_api.get_all()
                return [e.to_dict() for e in resp.results] if hasattr(resp, "results") else []
            except Exception:
                return []

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _fetch)
