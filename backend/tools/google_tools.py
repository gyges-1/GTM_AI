"""LangChain tools wrapping the Google Docs integration."""

from __future__ import annotations

from typing import Any, Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from backend.integrations.google_docs import GoogleDocsClient


class GetDocumentInput(BaseModel):
    document_id: str = Field(..., description="Google Docs document ID from the URL")


class ListFilesInput(BaseModel):
    query: str = Field(default="", description="Search query to filter files by name")
    limit: int = Field(default=10, ge=1, le=50)


def build_google_tools(client: GoogleDocsClient) -> list:
    """Return list of LangChain tools bound to a GoogleDocsClient instance."""

    @tool("get_google_doc_report", args_schema=GetDocumentInput)
    async def get_google_doc_report(document_id: str) -> dict[str, Any]:
        """Retrieve the content of a Google Doc report. Returns title and full text content."""
        return await client.get_document(document_id)

    @tool("list_google_drive_files", args_schema=ListFilesInput)
    async def list_google_drive_files(
        query: str = "",
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """List Google Drive files matching a search query. Returns file names, IDs, and links."""
        return await client.list_files(query=query, limit=limit)

    return [get_google_doc_report, list_google_drive_files]
