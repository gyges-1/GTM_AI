"""FastAPI dependency injection helpers."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db


def get_graph(request: Request) -> CompiledStateGraph:
    """Retrieve the compiled LangGraph supervisor from app state."""
    return request.app.state.graph


GraphDep = Annotated[CompiledStateGraph, Depends(get_graph)]
DBSession = Annotated[AsyncSession, Depends(get_db)]
