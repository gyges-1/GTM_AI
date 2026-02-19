"""Chat router — HTTP POST + WebSocket streaming."""

from __future__ import annotations

import json
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from langchain_core.messages import HumanMessage

from backend.api.deps import DBSession, GraphDep
from backend.api.schemas import ChatRequest, ChatResponse, StreamChunk
from backend.db.models import ChatMessage, ChatSession
from backend.observability.langfuse import get_callback_handler

router = APIRouter(prefix="/api/v1", tags=["chat"])


def _ensure_thread_id(thread_id: str | None) -> str:
    return thread_id or str(uuid.uuid4())


async def _upsert_session(db: DBSession, thread_id: str, user_id: str | None) -> None:
    session = await db.get(ChatSession, thread_id)
    if not session:
        session = ChatSession(id=thread_id, user_id=user_id)
        db.add(session)
    await db.flush()


async def _save_messages(
    db: DBSession,
    thread_id: str,
    user_content: str,
    assistant_content: str,
    agent_name: str | None,
) -> None:
    db.add(ChatMessage(session_id=thread_id, role="user", content=user_content))
    db.add(
        ChatMessage(
            session_id=thread_id,
            role="assistant",
            content=assistant_content,
            agent_name=agent_name,
        )
    )
    await db.flush()


# ── HTTP endpoint ─────────────────────────────────────────────────────────────

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, graph: GraphDep, db: DBSession) -> ChatResponse:
    """Synchronous chat — runs the full graph and returns the final response."""
    thread_id = _ensure_thread_id(request.thread_id)
    await _upsert_session(db, thread_id, request.user_id)

    callbacks = []
    langfuse_handler = get_callback_handler(thread_id)
    if langfuse_handler:
        callbacks.append(langfuse_handler)

    config = {
        "configurable": {"thread_id": thread_id},
        "callbacks": callbacks,
    }

    try:
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=request.message)]},
            config=config,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    messages = result.get("messages", [])
    last_ai = next(
        (m for m in reversed(messages) if hasattr(m, "content") and m.type == "ai"),
        None,
    )
    response_text = last_ai.content if last_ai else "No response generated."
    active_agent = result.get("active_agent")

    await _save_messages(db, thread_id, request.message, response_text, active_agent)

    return ChatResponse(
        thread_id=thread_id,
        message=response_text,
        agent_name=active_agent,
    )


# ── WebSocket endpoint ────────────────────────────────────────────────────────

@router.websocket("/ws/chat/{thread_id}")
async def ws_chat(websocket: WebSocket, thread_id: str, graph: GraphDep) -> None:
    """Streaming chat via WebSocket using astream_events v2."""
    await websocket.accept()

    async def send_chunk(chunk: StreamChunk) -> None:
        await websocket.send_text(chunk.model_dump_json())

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
                message_text = payload.get("message", "")
            except json.JSONDecodeError:
                message_text = raw

            if not message_text.strip():
                continue

            callbacks = []
            langfuse_handler = get_callback_handler(thread_id)
            if langfuse_handler:
                callbacks.append(langfuse_handler)

            config = {
                "configurable": {"thread_id": thread_id},
                "callbacks": callbacks,
            }

            active_agent: str | None = None

            try:
                async for event in graph.astream_events(
                    {"messages": [HumanMessage(content=message_text)]},
                    config=config,
                    version="v2",
                ):
                    kind = event.get("event", "")
                    name = event.get("name", "")

                    if kind == "on_chain_start" and name in (
                        "demand_generation",
                        "pipeline_management",
                        "forecasting",
                        "customer_success",
                        "growth_intelligence",
                    ):
                        active_agent = name
                        await send_chunk(
                            StreamChunk(type="agent_switch", agent_name=name, thread_id=thread_id)
                        )

                    elif kind == "on_chat_model_stream":
                        data = event.get("data", {})
                        chunk_obj = data.get("chunk")
                        if chunk_obj and hasattr(chunk_obj, "content"):
                            content = chunk_obj.content
                            if isinstance(content, str) and content:
                                await send_chunk(
                                    StreamChunk(
                                        type="token",
                                        content=content,
                                        agent_name=active_agent,
                                        thread_id=thread_id,
                                    )
                                )
                            elif isinstance(content, list):
                                for block in content:
                                    if isinstance(block, dict) and block.get("type") == "text":
                                        text = block.get("text", "")
                                        if text:
                                            await send_chunk(
                                                StreamChunk(
                                                    type="token",
                                                    content=text,
                                                    agent_name=active_agent,
                                                    thread_id=thread_id,
                                                )
                                            )

                    elif kind == "on_tool_start":
                        data = event.get("data", {})
                        await send_chunk(
                            StreamChunk(
                                type="tool_call",
                                tool_name=name,
                                tool_input=data.get("input"),
                                agent_name=active_agent,
                                thread_id=thread_id,
                            )
                        )

                    elif kind == "on_tool_end":
                        data = event.get("data", {})
                        output = data.get("output", "")
                        await send_chunk(
                            StreamChunk(
                                type="tool_result",
                                tool_name=name,
                                tool_output=str(output)[:1024],
                                agent_name=active_agent,
                                thread_id=thread_id,
                            )
                        )

                await send_chunk(StreamChunk(type="done", thread_id=thread_id))

            except Exception as exc:
                await send_chunk(
                    StreamChunk(type="error", error=str(exc)[:512], thread_id=thread_id)
                )

    except WebSocketDisconnect:
        pass
