"""Sessions management router."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy import delete, func, select

from backend.api.deps import DBSession
from backend.api.schemas import MessageSummary, SessionDetail, SessionSummary
from backend.db.models import ChatMessage, ChatSession

router = APIRouter(prefix="/api/v1", tags=["sessions"])


@router.get("/sessions", response_model=list[SessionSummary])
async def list_sessions(
    db: DBSession,
    user_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[SessionSummary]:
    """List chat sessions, optionally filtered by user_id."""
    stmt = (
        select(
            ChatSession,
            func.count(ChatMessage.id).label("message_count"),
        )
        .outerjoin(ChatMessage, ChatMessage.session_id == ChatSession.id)
        .where(ChatSession.is_active == True)  # noqa: E712
        .group_by(ChatSession.id)
        .order_by(ChatSession.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if user_id:
        stmt = stmt.where(ChatSession.user_id == user_id)

    rows = (await db.execute(stmt)).all()
    return [
        SessionSummary(
            thread_id=row.ChatSession.id,
            title=row.ChatSession.title,
            created_at=row.ChatSession.created_at,
            updated_at=row.ChatSession.updated_at,
            message_count=row.message_count,
        )
        for row in rows
    ]


@router.get("/sessions/{thread_id}", response_model=SessionDetail)
async def get_session(thread_id: str, db: DBSession) -> SessionDetail:
    """Get full session history including all messages."""
    session = await db.get(ChatSession, thread_id)
    if not session or not session.is_active:
        raise HTTPException(status_code=404, detail="Session not found")

    msg_rows = (
        await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == thread_id)
            .order_by(ChatMessage.created_at)
        )
    ).scalars().all()

    msg_count = len(msg_rows)
    messages = [
        MessageSummary(
            id=m.id,
            role=m.role,
            content=m.content,
            agent_name=m.agent_name,
            created_at=m.created_at,
        )
        for m in msg_rows
    ]

    return SessionDetail(
        thread_id=session.id,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=msg_count,
        messages=messages,
    )


@router.delete("/sessions/{thread_id}", status_code=204)
async def delete_session(thread_id: str, db: DBSession) -> None:
    """Soft-delete a session."""
    session = await db.get(ChatSession, thread_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.is_active = False
    await db.flush()
