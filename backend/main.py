"""FastAPI application entry point."""

from __future__ import annotations

import structlog
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import psycopg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from backend.api.routers import agents, chat, health, sessions
from backend.config import get_settings
from backend.db.session import async_engine
from backend.db.models import Base

logger = structlog.get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — initialise shared resources on startup."""
    logger.info("startup", env=settings.app_env)

    # ── Integrations ──────────────────────────────────────────────────────────
    from backend.integrations.hubspot import HubSpotClient
    from backend.integrations.salesforce import SalesforceClient
    from backend.integrations.google_docs import GoogleDocsClient
    from backend.integrations.posthog import PostHogClient
    from backend.integrations.postgres import PostgresIntegration

    integrations: dict = {}
    if settings.hubspot_configured:
        integrations["hubspot"] = HubSpotClient(settings)
    if settings.salesforce_configured:
        integrations["salesforce"] = SalesforceClient(settings)
    if settings.google_configured:
        integrations["google_docs"] = GoogleDocsClient(settings)
    if settings.posthog_configured:
        integrations["posthog"] = PostHogClient(settings)

    # Postgres integration always available (uses same DB)
    integrations["postgres"] = PostgresIntegration(settings)

    app.state.integrations = integrations

    # ── Postgres checkpointer (psycopg3 AsyncConnection) ─────────────────────
    aconn = await psycopg.AsyncConnection.connect(
        settings.postgres_dsn, autocommit=True
    )
    checkpointer = AsyncPostgresSaver(aconn)
    await checkpointer.setup()

    # ── Build supervisor graph ────────────────────────────────────────────────
    from backend.agents.supervisor import build_supervisor_graph

    app.state.graph = await build_supervisor_graph(checkpointer, integrations)
    app.state.pg_conn = aconn

    logger.info("startup_complete", integrations=list(integrations.keys()))

    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("shutdown")
    await aconn.close()
    await async_engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="GTM AI Agent System",
        description="LangGraph supervisor with 5 specialised Go-To-Market agents",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(sessions.router)
    app.include_router(agents.router)

    return app


app = create_app()
