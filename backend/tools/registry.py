"""Tool registry — builds and indexes all tools from active integrations."""

from __future__ import annotations

from typing import Any

from langchain_core.tools import BaseTool

from backend.integrations.base import BaseIntegration


def build_tool_registry(integrations: dict[str, BaseIntegration]) -> dict[str, BaseTool]:
    """
    Given the active integrations dict, build all LangChain tools and
    return a name -> tool mapping.
    """
    all_tools: list[BaseTool] = []

    if "hubspot" in integrations:
        from backend.tools.hubspot_tools import build_hubspot_tools
        all_tools.extend(build_hubspot_tools(integrations["hubspot"]))

    if "salesforce" in integrations:
        from backend.tools.salesforce_tools import build_salesforce_tools
        all_tools.extend(build_salesforce_tools(integrations["salesforce"]))

    if "google_docs" in integrations:
        from backend.tools.google_tools import build_google_tools
        all_tools.extend(build_google_tools(integrations["google_docs"]))

    if "posthog" in integrations:
        from backend.tools.posthog_tools import build_posthog_tools
        all_tools.extend(build_posthog_tools(integrations["posthog"]))

    if "postgres" in integrations:
        from backend.tools.postgres_tools import build_postgres_tools
        all_tools.extend(build_postgres_tools(integrations["postgres"]))

    return {t.name: t for t in all_tools}


def get_tools_for_agent(
    tool_registry: dict[str, BaseTool],
    tool_names: list[str],
) -> list[BaseTool]:
    """Look up tools by name; silently skip missing tools (integration not configured)."""
    result = []
    for name in tool_names:
        if name in tool_registry:
            result.append(tool_registry[name])
    return result
