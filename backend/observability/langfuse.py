"""LangFuse observability — per-request callback handler factory."""

from __future__ import annotations

import structlog

from backend.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


def get_callback_handler(thread_id: str | None = None):
    """
    Create a fresh LangFuse CallbackHandler for the current request.

    Returns None if LangFuse is not configured, so callers can skip safely.
    """
    if not settings.langfuse_configured:
        return None

    try:
        from langfuse.callback import CallbackHandler

        handler = CallbackHandler(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
            session_id=thread_id,
            tags=["gtm-ai", settings.app_env],
        )
        return handler
    except ImportError:
        logger.warning("langfuse package not installed — observability disabled")
        return None
    except Exception as exc:
        logger.warning("langfuse_init_failed", error=str(exc))
        return None
