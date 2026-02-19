"""GTM Agent state definitions."""

from __future__ import annotations

import operator
from typing import Annotated, Literal, Optional

from langchain_core.messages import BaseMessage
from langgraph.graph import MessagesState
from pydantic import BaseModel, Field

AgentName = Literal[
    "demand_generation",
    "pipeline_management",
    "forecasting",
    "customer_success",
    "growth_intelligence",
]


class GTMContext(BaseModel):
    """Shared business context passed to all agents."""

    company_id: str | None = None
    pipeline_snapshot: dict | None = None
    churn_risk_accounts: list[str] = Field(default_factory=list)
    current_quarter: str | None = None
    fiscal_year: int | None = None
    metadata: dict = Field(default_factory=dict)


class GTMState(MessagesState):
    """
    Root state shared across the supervisor and all subgraph agents.

    MessagesState provides:
      - messages: Annotated[list[BaseMessage], add_messages]  (append-only)
    """

    # Routing
    next_agent: AgentName | None = None
    active_agent: AgentName | None = None

    # Accumulated results from all agents in a multi-step flow
    agent_outputs: Annotated[list[dict], operator.add] = []

    # Shared business context
    gtm_context: GTMContext = Field(default_factory=GTMContext)

    # Thread / trace identifiers
    thread_id: str | None = None
    langfuse_trace_id: str | None = None
