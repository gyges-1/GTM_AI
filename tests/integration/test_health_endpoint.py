"""Integration tests for the health endpoint."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport

from backend.main import create_app


@pytest.fixture
def app_with_mocks():
    """Create app with mocked integrations (no real DB/APIs needed)."""
    app = create_app()

    mock_postgres = MagicMock()
    mock_postgres.health_check = AsyncMock(return_value=None)

    # Bypass lifespan for unit testing
    app.state.integrations = {"postgres": mock_postgres}

    return app


@pytest.mark.asyncio
async def test_health_endpoint_with_mock_integrations(app_with_mocks):
    transport = ASGITransport(app=app_with_mocks)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "integrations" in data
    assert "timestamp" in data
