"""Unit tests for tool registry."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from backend.tools.registry import build_tool_registry, get_tools_for_agent


def make_mock_integration():
    mock = MagicMock()
    mock.health_check = AsyncMock(return_value=None)
    return mock


def test_registry_empty_integrations():
    """Empty integrations dict produces empty registry."""
    registry = build_tool_registry({})
    assert registry == {}


def test_get_tools_for_agent_missing_tools():
    """Missing tool names are silently skipped."""
    registry = {"tool_a": MagicMock()}
    tools = get_tools_for_agent(registry, ["tool_a", "tool_b_missing"])
    assert len(tools) == 1


def test_get_tools_for_agent_all_present():
    tool_a = MagicMock()
    tool_a.name = "tool_a"
    tool_b = MagicMock()
    tool_b.name = "tool_b"
    registry = {"tool_a": tool_a, "tool_b": tool_b}

    tools = get_tools_for_agent(registry, ["tool_a", "tool_b"])
    assert len(tools) == 2
