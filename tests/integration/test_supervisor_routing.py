"""Integration tests for supervisor routing logic (mocked LLM)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def test_agent_names_unique():
    """All agent names in the registry should be unique."""
    from backend.api.routers.agents import AGENT_REGISTRY
    names = [a.name for a in AGENT_REGISTRY]
    assert len(names) == len(set(names))


def test_agent_tool_names_in_registry():
    """Each agent should declare at least one tool."""
    from backend.api.routers.agents import AGENT_REGISTRY
    for agent in AGENT_REGISTRY:
        assert len(agent.tools) > 0, f"Agent {agent.name} has no tools"


def test_all_five_agents_registered():
    """All 5 specialised agents must be present."""
    from backend.api.routers.agents import AGENT_REGISTRY
    expected = {
        "demand_generation",
        "pipeline_management",
        "forecasting",
        "customer_success",
        "growth_intelligence",
    }
    registered = {a.name for a in AGENT_REGISTRY}
    assert expected == registered
