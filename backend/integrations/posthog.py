"""PostHog analytics integration client (HTTP API)."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.config import Settings
from backend.integrations.base import BaseIntegration

logger = structlog.get_logger(__name__)


class PostHogClient(BaseIntegration):
    """
    PostHog integration using the HTTP API directly (not the Python SDK)
    since funnel/insight queries require the REST API.
    """

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
        self._http: httpx.AsyncClient | None = None

    def _get_http(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(
                base_url=self.settings.posthog_host,
                headers={
                    "Authorization": f"Bearer {self.settings.posthog_personal_api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._http

    async def health_check(self) -> None:
        """Verify PostHog connectivity."""
        client = self._get_http()
        resp = await client.get(f"/api/projects/{self.settings.posthog_project_id}/")
        resp.raise_for_status()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def get_funnel(
        self,
        funnel_id: int | None = None,
        date_from: str = "-30d",
        date_to: str = "today",
        steps: list[dict] | None = None,
    ) -> dict[str, Any]:
        """Retrieve funnel data for conversion analysis."""
        client = self._get_http()
        project_id = self.settings.posthog_project_id

        if funnel_id:
            resp = await client.get(f"/api/projects/{project_id}/insights/{funnel_id}/")
            resp.raise_for_status()
            return resp.json()

        # Run ad-hoc funnel query
        payload = {
            "insight": "FUNNELS",
            "date_from": date_from,
            "date_to": date_to,
            "funnel_viz_type": "steps",
            "events": steps or [
                {"id": "pageview", "name": "Page View", "order": 0},
                {"id": "signup", "name": "Sign Up", "order": 1},
                {"id": "activated", "name": "Activated", "order": 2},
            ],
        }
        resp = await client.post(f"/api/projects/{project_id}/insights/funnel/", json=payload)
        resp.raise_for_status()
        return resp.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def get_user_segments(self, cohort_id: int | None = None) -> list[dict[str, Any]]:
        """Retrieve cohorts / user segments."""
        client = self._get_http()
        project_id = self.settings.posthog_project_id

        if cohort_id:
            resp = await client.get(f"/api/projects/{project_id}/cohorts/{cohort_id}/")
            resp.raise_for_status()
            return [resp.json()]

        resp = await client.get(f"/api/projects/{project_id}/cohorts/")
        resp.raise_for_status()
        return resp.json().get("results", [])

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def get_engagement_metrics(
        self,
        date_from: str = "-30d",
        events: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get event trend data for engagement analysis."""
        client = self._get_http()
        project_id = self.settings.posthog_project_id

        event_list = events or ["pageview", "feature_used", "session_start"]
        payload = {
            "insight": "TRENDS",
            "date_from": date_from,
            "events": [{"id": e, "name": e} for e in event_list],
        }
        resp = await client.post(f"/api/projects/{project_id}/insights/trend/", json=payload)
        resp.raise_for_status()
        return resp.json()
