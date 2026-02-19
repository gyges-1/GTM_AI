"""Supervisor graph builder using langgraph-supervisor."""

from __future__ import annotations

import structlog
from langchain_anthropic import ChatAnthropic
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph.state import CompiledStateGraph
from langgraph_supervisor import create_supervisor

from backend.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

SUPERVISOR_PROMPT = """You are the GTM AI Supervisor — an intelligent routing agent for a Go-To-Market operations system.

You coordinate a team of five specialised agents:

1. **demand_generation** — Lead generation, campaign metrics, top-of-funnel analysis, MQLs/SQLs
2. **pipeline_management** — Deal tracking, pipeline health, stage progression, sales velocity
3. **forecasting** — Revenue forecasting, close-date analysis, win rates, quota coverage
4. **customer_success** — Churn risk, health scores, renewal pipeline, NRR/GRR
5. **growth_intelligence** — Market segmentation, account expansion, PQLs, competitive analysis

Your job:
- Analyse the user's question and route it to the most appropriate specialist agent
- For complex questions spanning multiple domains, route to the primary domain first
- If the user asks about pipeline AND forecast, prefer forecasting (it's more specific)
- Synthesise multi-agent responses into a cohesive answer when needed

Routing guidelines:
- "pipeline coverage / pipeline health / deal stages" → pipeline_management
- "revenue forecast / quota / close date" → forecasting
- "leads / campaigns / MQL / funnel / top of funnel" → demand_generation
- "churn / renewal / health score / NRR" → customer_success
- "market segments / expansion / growth / accounts / ICP" → growth_intelligence

Always route to exactly one agent per turn unless the question clearly requires multiple perspectives."""


async def build_supervisor_graph(
    checkpointer: AsyncPostgresSaver,
    integrations: dict,
) -> CompiledStateGraph:
    """
    Build the compiled supervisor graph.

    One instance is created at startup and reused across all requests.
    Thread isolation is achieved via config["configurable"]["thread_id"].
    """
    from backend.tools.registry import build_tool_registry
    from backend.agents.demand_generation.agent import build_agent as build_demand
    from backend.agents.pipeline_management.agent import build_agent as build_pipeline
    from backend.agents.forecasting.agent import build_agent as build_forecast
    from backend.agents.customer_success.agent import build_agent as build_cs
    from backend.agents.growth_intelligence.agent import build_agent as build_growth

    # Build shared tool registry from active integrations
    tool_registry = build_tool_registry(integrations)
    logger.info("tool_registry_built", tools=list(tool_registry.keys()))

    # Build each subgraph agent
    demand_agent = build_demand(tool_registry)
    pipeline_agent = build_pipeline(tool_registry)
    forecast_agent = build_forecast(tool_registry)
    cs_agent = build_cs(tool_registry)
    growth_agent = build_growth(tool_registry)

    # Supervisor LLM (Opus 4.6)
    supervisor_llm = ChatAnthropic(
        model=settings.supervisor_model,
        api_key=settings.anthropic_api_key,
        temperature=0,
    )

    # Create supervisor with all subagents registered
    supervisor = create_supervisor(
        agents=[demand_agent, pipeline_agent, forecast_agent, cs_agent, growth_agent],
        model=supervisor_llm,
        prompt=SUPERVISOR_PROMPT,
    )

    # Compile with Postgres checkpointer for persistence
    compiled = supervisor.compile(checkpointer=checkpointer)

    logger.info("supervisor_graph_compiled")
    return compiled
