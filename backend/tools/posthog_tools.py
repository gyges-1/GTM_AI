"""LangChain tools wrapping the PostHog integration."""

from __future__ import annotations

from typing import Any, Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from backend.integrations.posthog import PostHogClient


class GetFunnelInput(BaseModel):
    funnel_id: Optional[int] = Field(default=None, description="Existing funnel/insight ID")
    date_from: str = Field(default="-30d", description="Start date e.g. '-30d' or '2025-01-01'")
    date_to: str = Field(default="today", description="End date e.g. 'today' or '2025-01-31'")


class GetEngagementInput(BaseModel):
    date_from: str = Field(default="-30d", description="Lookback period e.g. '-30d'")
    events: Optional[list[str]] = Field(
        default=None, description="Event names to include in the trend"
    )


class GetSegmentsInput(BaseModel):
    cohort_id: Optional[int] = Field(default=None, description="Specific cohort/segment ID")


def build_posthog_tools(client: PostHogClient) -> list:
    """Return list of LangChain tools bound to a PostHogClient instance."""

    @tool("get_posthog_funnel", args_schema=GetFunnelInput)
    async def get_posthog_funnel(
        funnel_id: Optional[int] = None,
        date_from: str = "-30d",
        date_to: str = "today",
    ) -> dict[str, Any]:
        """Retrieve PostHog funnel conversion data. Shows step-by-step conversion rates for user journeys."""
        return await client.get_funnel(funnel_id=funnel_id, date_from=date_from, date_to=date_to)

    @tool("get_posthog_engagement", args_schema=GetEngagementInput)
    async def get_posthog_engagement(
        date_from: str = "-30d",
        events: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Retrieve PostHog user engagement trends. Returns event frequency over time for customer health analysis."""
        return await client.get_engagement_metrics(date_from=date_from, events=events)

    @tool("get_posthog_segments", args_schema=GetSegmentsInput)
    async def get_posthog_segments(cohort_id: Optional[int] = None) -> list[dict[str, Any]]:
        """Retrieve PostHog user segments / cohorts. Returns cohort definitions and sizes for market analysis."""
        return await client.get_user_segments(cohort_id=cohort_id)

    return [get_posthog_funnel, get_posthog_engagement, get_posthog_segments]
