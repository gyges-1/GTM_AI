"""Agents info router."""

from __future__ import annotations

from fastapi import APIRouter

from backend.api.schemas import AgentInfo
from backend.config import get_settings

router = APIRouter(prefix="/api/v1", tags=["agents"])
settings = get_settings()

AGENT_REGISTRY: list[AgentInfo] = [
    AgentInfo(
        name="demand_generation",
        description="Manages lead generation, campaign performance, and top-of-funnel metrics.",
        tools=["get_hubspot_contacts", "get_campaign_metrics", "get_posthog_funnel", "get_lead_sources"],
        model=settings.subagent_model,
    ),
    AgentInfo(
        name="pipeline_management",
        description="Tracks deal stages, pipeline health, and sales velocity.",
        tools=["get_hubspot_deals", "get_salesforce_opportunities", "update_deal_stage"],
        model=settings.subagent_model,
    ),
    AgentInfo(
        name="forecasting",
        description="Generates revenue forecasts and close-date analysis.",
        tools=["get_sf_opportunities_by_close_date", "get_historical_win_rates", "calculate_forecast"],
        model=settings.subagent_model,
    ),
    AgentInfo(
        name="customer_success",
        description="Monitors customer health scores, churn risk, and renewal pipeline.",
        tools=["get_hubspot_health_scores", "get_posthog_engagement", "get_renewal_pipeline"],
        model=settings.subagent_model,
    ),
    AgentInfo(
        name="growth_intelligence",
        description="Analyses market segments, account expansion, and growth opportunities.",
        tools=["get_salesforce_accounts", "get_posthog_segments", "get_google_doc_report"],
        model=settings.subagent_model,
    ),
]


@router.get("/agents", response_model=list[AgentInfo])
async def list_agents() -> list[AgentInfo]:
    """List all available agents and their capabilities."""
    return AGENT_REGISTRY
