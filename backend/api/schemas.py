"""Pydantic schemas for API requests and responses."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# ── Chat ─────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8192)
    thread_id: str | None = None
    user_id: str | None = None
    company_id: str | None = None


class ChatResponse(BaseModel):
    thread_id: str
    message: str
    agent_name: str | None = None
    tool_calls: list[dict[str, Any]] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ── Streaming ─────────────────────────────────────────────────────────────────

StreamChunkType = Literal["token", "agent_switch", "tool_call", "tool_result", "done", "error"]


class StreamChunk(BaseModel):
    type: StreamChunkType
    content: str | None = None
    agent_name: str | None = None
    tool_name: str | None = None
    tool_input: dict[str, Any] | None = None
    tool_output: str | None = None
    error: str | None = None
    thread_id: str | None = None


# ── Sessions ─────────────────────────────────────────────────────────────────

class SessionSummary(BaseModel):
    thread_id: str
    title: str | None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class SessionDetail(SessionSummary):
    messages: list[MessageSummary] = []


class MessageSummary(BaseModel):
    id: int
    role: str
    content: str
    agent_name: str | None
    created_at: datetime


# ── Agents ────────────────────────────────────────────────────────────────────

class AgentInfo(BaseModel):
    name: str
    description: str
    tools: list[str]
    model: str
    status: Literal["available", "degraded", "unavailable"] = "available"


# ── Health ────────────────────────────────────────────────────────────────────

class IntegrationHealth(BaseModel):
    name: str
    status: Literal["ok", "degraded", "error"]
    latency_ms: float | None = None
    error: str | None = None


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "error"]
    integrations: list[IntegrationHealth]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
