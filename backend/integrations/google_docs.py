"""Google Docs integration client."""

from __future__ import annotations

import json
from typing import Any

import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.config import Settings
from backend.integrations.base import BaseIntegration

logger = structlog.get_logger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/documents.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]


class GoogleDocsClient(BaseIntegration):
    """Provides read access to Google Docs and Drive."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
        self._creds = None
        self._docs_service = None
        self._drive_service = None

    def _get_credentials(self):
        if self._creds is None:
            from google.oauth2 import service_account

            sa_path = self.settings.google_service_account_json
            self._creds = service_account.Credentials.from_service_account_file(
                sa_path, scopes=SCOPES
            )
        return self._creds

    def _get_docs_service(self):
        if self._docs_service is None:
            from googleapiclient.discovery import build
            self._docs_service = build("docs", "v1", credentials=self._get_credentials())
        return self._docs_service

    def _get_drive_service(self):
        if self._drive_service is None:
            from googleapiclient.discovery import build
            self._drive_service = build("drive", "v3", credentials=self._get_credentials())
        return self._drive_service

    async def health_check(self) -> None:
        """Verify Google Docs connectivity."""
        import asyncio
        svc = self._get_drive_service()
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: svc.files().list(pageSize=1, fields="files(id,name)").execute(),
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def get_document(self, document_id: str) -> dict[str, Any]:
        """Retrieve a Google Doc and extract plain text content."""
        import asyncio

        svc = self._get_docs_service()
        loop = asyncio.get_event_loop()
        doc = await loop.run_in_executor(
            None,
            lambda: svc.documents().get(documentId=document_id).execute(),
        )
        return {"title": doc.get("title", ""), "content": self._extract_text(doc), "id": document_id}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def list_files(
        self,
        query: str = "",
        mime_type: str = "application/vnd.google-apps.document",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """List files in Google Drive matching a query."""
        import asyncio

        q_parts = [f"mimeType='{mime_type}'"]
        if query:
            q_parts.append(f"name contains '{query}'")
        q = " and ".join(q_parts)

        svc = self._get_drive_service()
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: svc.files()
            .list(q=q, pageSize=limit, fields="files(id,name,modifiedTime,webViewLink)")
            .execute(),
        )
        return result.get("files", [])

    @staticmethod
    def _extract_text(doc: dict) -> str:
        """Extract plain text from a Google Doc body."""
        texts: list[str] = []
        body = doc.get("body", {})
        for element in body.get("content", []):
            paragraph = element.get("paragraph")
            if not paragraph:
                continue
            for elem in paragraph.get("elements", []):
                text_run = elem.get("textRun")
                if text_run:
                    texts.append(text_run.get("content", ""))
        return "".join(texts)
