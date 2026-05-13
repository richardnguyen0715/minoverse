"""Base scraper adapter interface."""
from __future__ import annotations

from abc import ABC, abstractmethod

from .schemas import NormalizedDocument


class BaseScraper(ABC):
    """All scrapers must implement this interface.

    Each scraper handles a specific source type and returns a NormalizedDocument.
    """

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Return True if this scraper can handle the given URL."""
        ...

    @abstractmethod
    async def scrape(self, url: str) -> NormalizedDocument:
        """Scrape the URL and return a normalized document."""
        ...
