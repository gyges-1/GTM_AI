"""Growth Intelligence subgraph agent."""

from __future__ import annotations

from langchain_anthropic import ChatAnthropic
from langchain_core.tools import BaseTool
from langgraph.prebuilt import create_react_agent

from backend.agents.growth_intelligence.prompts import SYSTEM_PROMPT
from backend.config import get_settings

settings = get_settings()

TOOL_NAMES = [
    "get_salesforce_accounts",
    "get_posthog_segments",
    "get_google_doc_report",
    "list_google_drive_files",
]


def build_agent(tool_registry: dict[str, BaseTool]):
    """Build the growth intelligence ReAct agent."""
    from backend.tools.registry import get_tools_for_agent

    tools = get_tools_for_agent(tool_registry, TOOL_NAMES)

    llm = ChatAnthropic(
        model=settings.subagent_model,
        api_key=settings.anthropic_api_key,
        temperature=0,
    )

    return create_react_agent(
        model=llm,
        tools=tools,
        prompt=SYSTEM_PROMPT,
        name="growth_intelligence",
    )
