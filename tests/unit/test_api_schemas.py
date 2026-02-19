"""Unit tests for API schemas."""

import pytest
from pydantic import ValidationError

from backend.api.schemas import (
    ChatRequest,
    ChatResponse,
    StreamChunk,
    HealthResponse,
    IntegrationHealth,
)


def test_chat_request_valid():
    req = ChatRequest(message="What's our pipeline coverage?")
    assert req.message == "What's our pipeline coverage?"
    assert req.thread_id is None


def test_chat_request_empty_message():
    with pytest.raises(ValidationError):
        ChatRequest(message="")


def test_stream_chunk_token():
    chunk = StreamChunk(type="token", content="Hello", agent_name="forecasting")
    assert chunk.type == "token"
    assert chunk.content == "Hello"
    data = chunk.model_dump_json()
    assert "token" in data


def test_stream_chunk_done():
    chunk = StreamChunk(type="done", thread_id="thread-123")
    assert chunk.type == "done"


def test_health_response_ok():
    resp = HealthResponse(
        status="ok",
        integrations=[
            IntegrationHealth(name="postgres", status="ok", latency_ms=2.5),
            IntegrationHealth(name="hubspot", status="ok", latency_ms=45.1),
        ],
    )
    assert resp.status == "ok"
    assert len(resp.integrations) == 2


def test_health_response_degraded():
    resp = HealthResponse(
        status="degraded",
        integrations=[
            IntegrationHealth(name="postgres", status="ok"),
            IntegrationHealth(name="hubspot", status="error", error="Connection refused"),
        ],
    )
    assert resp.status == "degraded"
    err_integration = next(i for i in resp.integrations if i.name == "hubspot")
    assert err_integration.error == "Connection refused"
