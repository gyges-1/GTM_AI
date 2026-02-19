"""Base integration class."""

from __future__ import annotations

from abc import ABC, abstractmethod

from backend.config import Settings


class BaseIntegration(ABC):
    """All integration clients inherit from this."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = None

    @abstractmethod
    async def health_check(self) -> None:
        """Raise an exception if the integration is unreachable."""
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}>"
