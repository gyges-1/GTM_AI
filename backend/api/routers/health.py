"""Health check router."""

from __future__ import annotations

import asyncio
import time

from fastapi import APIRouter, Request

from backend.api.schemas import HealthResponse, IntegrationHealth
from backend.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health_check(request: Request) -> HealthResponse:
    """Return system health including all integration statuses."""
    integrations_map: dict = getattr(request.app.state, "integrations", {})

    checks: list[IntegrationHealth] = []

    async def check_one(name: str, client) -> IntegrationHealth:
        start = time.monotonic()
        try:
            await client.health_check()
            latency = (time.monotonic() - start) * 1000
            return IntegrationHealth(name=name, status="ok", latency_ms=round(latency, 2))
        except Exception as exc:
            latency = (time.monotonic() - start) * 1000
            return IntegrationHealth(
                name=name,
                status="error",
                latency_ms=round(latency, 2),
                error=str(exc)[:256],
            )

    tasks = [check_one(name, client) for name, client in integrations_map.items()]
    if tasks:
        checks = list(await asyncio.gather(*tasks))
    else:
        checks = []

    overall = "ok"
    if any(c.status == "error" for c in checks):
        overall = "degraded" if any(c.status == "ok" for c in checks) else "error"

    return HealthResponse(status=overall, integrations=checks)
