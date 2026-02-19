"""Unit tests for application configuration."""

import os
import pytest
from backend.config import Settings


def test_default_settings():
    """Settings should load with sensible defaults."""
    s = Settings(
        _env_file=None,  # don't load .env for unit tests
        anthropic_api_key="test-key",
        database_url="postgresql+psycopg://user:pass@localhost:5432/db",
        postgres_dsn="postgresql://user:pass@localhost:5432/db",
    )
    assert s.app_env == "development"
    assert s.supervisor_model == "claude-opus-4-6"
    assert s.subagent_model == "claude-haiku-4-5-20251001"
    assert not s.is_production


def test_production_flag():
    s = Settings(
        _env_file=None,
        app_env="production",
        database_url="postgresql+psycopg://u:p@localhost/db",
        postgres_dsn="postgresql://u:p@localhost/db",
    )
    assert s.is_production


def test_cors_origins_json_parse():
    s = Settings(
        _env_file=None,
        cors_origins='["http://localhost:3000","http://localhost:5173"]',
        database_url="postgresql+psycopg://u:p@localhost/db",
        postgres_dsn="postgresql://u:p@localhost/db",
    )
    assert "http://localhost:3000" in s.cors_origins
    assert "http://localhost:5173" in s.cors_origins


def test_integration_configured_flags():
    s = Settings(
        _env_file=None,
        hubspot_access_token="hs-token",
        sf_username="user",
        sf_password="pass",
        google_service_account_json="/path/to/sa.json",
        posthog_project_id="proj",
        posthog_personal_api_key="key",
        langfuse_public_key="lf-pk",
        langfuse_secret_key="lf-sk",
        database_url="postgresql+psycopg://u:p@localhost/db",
        postgres_dsn="postgresql://u:p@localhost/db",
    )
    assert s.hubspot_configured
    assert s.salesforce_configured
    assert s.google_configured
    assert s.posthog_configured
    assert s.langfuse_configured
