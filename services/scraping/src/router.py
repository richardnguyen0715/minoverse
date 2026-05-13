"""Scraper router — selects the correct adapter for a URL."""
from __future__ import annotations

import structlog

from .adapters.base import BaseScraper
from .adapters.generic import GenericScraper
from .adapters.github import GitHubScraper
from .adapters.youtube import YouTubeScraper
from .schemas import NormalizedDocument

logger = structlog.get_logger(__name__)

# Priority-ordered list of scrapers
# First scraper whose can_handle() returns True is used
_SCRAPERS: list[BaseScraper] = [
    YouTubeScraper(),
    GitHubScraper(),
    GenericScraper(),  # Must be last — handles everything
]


def get_scraper(url: str) -> BaseScraper:
    """Return the best scraper for the URL."""
    for scraper in _SCRAPERS:
        if scraper.can_handle(url):
            logger.debug("scraper_selected", scraper=scraper.name, url=url)
            return scraper
    raise ValueError(f"No scraper found for URL: {url}")


async def scrape(url: str) -> NormalizedDocument:
    """Route URL to appropriate scraper and return normalized document."""
    scraper = get_scraper(url)
    return await scraper.scrape(url)
