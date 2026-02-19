"""Application configuration via pydantic-settings."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ───────────────────────────────────────────────────────────────────
    app_env: str = "development"
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:5173"]

    # ── Anthropic ─────────────────────────────────────────────────────────────
    anthropic_api_key: str = ""

    # Model IDs
    supervisor_model: str = "claude-opus-4-6"
    subagent_model: str = "claude-haiku-4-5-20251001"

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = "postgresql+psycopg://gtm_user:gtm_password@localhost:5432/gtm_ai"
    postgres_dsn: str = "postgresql://gtm_user:gtm_password@localhost:5432/gtm_ai"
    db_pool_size: int = 10
    db_max_overflow: int = 20

    # ── HubSpot ───────────────────────────────────────────────────────────────
    hubspot_access_token: str = ""

    # ── Salesforce ────────────────────────────────────────────────────────────
    sf_username: str = ""
    sf_password: str = ""
    sf_security_token: str = ""
    sf_domain: str = "login"

    # ── Google ────────────────────────────────────────────────────────────────
    google_service_account_json: str = ""

    # ── PostHog ───────────────────────────────────────────────────────────────
    posthog_project_id: str = ""
    posthog_personal_api_key: str = ""
    posthog_host: str = "https://app.posthog.com"

    # ── LangFuse ──────────────────────────────────────────────────────────────
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [v]
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def hubspot_configured(self) -> bool:
        return bool(self.hubspot_access_token)

    @property
    def salesforce_configured(self) -> bool:
        return bool(self.sf_username and self.sf_password)

    @property
    def google_configured(self) -> bool:
        return bool(self.google_service_account_json)

    @property
    def posthog_configured(self) -> bool:
        return bool(self.posthog_project_id and self.posthog_personal_api_key)

    @property
    def langfuse_configured(self) -> bool:
        return bool(self.langfuse_public_key and self.langfuse_secret_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
