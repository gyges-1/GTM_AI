"""Unit tests for HubSpot tool wrappers."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from backend.tools.hubspot_tools import build_hubspot_tools


@pytest.fixture
def mock_hubspot_client():
    client = MagicMock()
    client.get_contacts = AsyncMock(return_value=[
        {"id": "1", "properties": {"email": "test@example.com", "company": "Acme Corp"}}
    ])
    client.get_deals = AsyncMock(return_value=[
        {"id": "d1", "properties": {"dealname": "Big Deal", "amount": "50000"}}
    ])
    client.get_campaign_metrics = AsyncMock(return_value=[])
    client.get_contact_health_scores = AsyncMock(return_value=[])
    return client


@pytest.mark.asyncio
async def test_get_hubspot_contacts(mock_hubspot_client):
    tools = build_hubspot_tools(mock_hubspot_client)
    contacts_tool = next(t for t in tools if t.name == "get_hubspot_contacts")

    result = await contacts_tool.ainvoke({"limit": 10})
    assert len(result) == 1
    mock_hubspot_client.get_contacts.assert_awaited_once_with(limit=10, properties=None)


@pytest.mark.asyncio
async def test_get_hubspot_deals(mock_hubspot_client):
    tools = build_hubspot_tools(mock_hubspot_client)
    deals_tool = next(t for t in tools if t.name == "get_hubspot_deals")

    result = await deals_tool.ainvoke({"limit": 5, "stage": "Proposal"})
    assert len(result) == 1
    mock_hubspot_client.get_deals.assert_awaited_once_with(limit=5, pipeline_id=None, stage="Proposal")


@pytest.mark.asyncio
async def test_get_campaign_metrics_no_args(mock_hubspot_client):
    tools = build_hubspot_tools(mock_hubspot_client)
    metrics_tool = next(t for t in tools if t.name == "get_campaign_metrics")

    result = await metrics_tool.ainvoke({})
    assert result == []
