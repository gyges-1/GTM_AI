"""LangChain tools wrapping the HubSpot integration."""

from __future__ import annotations

from typing import Any, Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from backend.integrations.hubspot import HubSpotClient


# ── Schema classes ────────────────────────────────────────────────────────────

class GetContactsInput(BaseModel):
    limit: int = Field(default=50, ge=1, le=100, description="Max number of contacts to return (HubSpot max: 100)")
    properties: Optional[list[str]] = Field(
        default=None, description="Contact properties to retrieve"
    )


class GetDealsInput(BaseModel):
    limit: int = Field(default=50, ge=1, le=100, description="Max deals to return (HubSpot max: 100)")
    pipeline_id: Optional[str] = Field(default=None, description="Filter by pipeline ID")
    stage: Optional[str] = Field(default=None, description="Filter by deal stage name")


class GetCampaignMetricsInput(BaseModel):
    pass  # no parameters needed


class GetHealthScoresInput(BaseModel):
    limit: int = Field(default=50, ge=1, le=100, description="Number of contacts to analyse (HubSpot max: 100)")


# ── Tool factories ────────────────────────────────────────────────────────────

def build_hubspot_tools(client: HubSpotClient) -> list:
    """Return list of LangChain tools bound to a HubSpotClient instance."""

    @tool("get_hubspot_contacts", args_schema=GetContactsInput)
    async def get_hubspot_contacts(limit: int = 50, properties: Optional[list[str]] = None) -> list[dict[str, Any]]:
        """Retrieve HubSpot CRM contacts. Returns a list of contact records with properties like email, company, lead status."""
        return await client.get_contacts(limit=limit, properties=properties)

    @tool("get_hubspot_deals", args_schema=GetDealsInput)
    async def get_hubspot_deals(
        limit: int = 50,
        pipeline_id: Optional[str] = None,
        stage: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Retrieve HubSpot deals. Optionally filter by pipeline or stage. Returns deal name, amount, stage, close date."""
        return await client.get_deals(limit=limit, pipeline_id=pipeline_id, stage=stage)

    @tool("get_campaign_metrics", args_schema=GetCampaignMetricsInput)
    async def get_campaign_metrics() -> list[dict[str, Any]]:
        """Retrieve HubSpot email campaign performance metrics including open rate, click rate, and conversions."""
        return await client.get_campaign_metrics()

    @tool("get_hubspot_health_scores", args_schema=GetHealthScoresInput)
    async def get_hubspot_health_scores(limit: int = 100) -> list[dict[str, Any]]:
        """Retrieve customer health scores from HubSpot contact engagement data."""
        return await client.get_contact_health_scores(limit=limit)

    return [get_hubspot_contacts, get_hubspot_deals, get_campaign_metrics, get_hubspot_health_scores]
