"""Generic web article scraper.

Uses trafilatura for content extraction (best-in-class readability extraction).
Falls back to BeautifulSoup if trafilatura fails.
"""
from __future__ import annotations

import re

import httpx
import structlog

from ..config import settings
from ..schemas import NormalizedDocument, SourceType
from .base import BaseScraper

logger = structlog.get_logger(__name__)

EXCLUDE_DOMAINS = {
    "youtube.com", "youtu.be",
    "github.com",
    "reddit.com",
    "twitter.com", "x.com",
}


class GenericScraper(BaseScraper):
    """Fallback scraper for generic web articles using trafilatura."""

    @property
    def name(self) -> str:
        return "generic"

    def can_handle(self, url: str) -> bool:
        # Handle anything not handled by more specific adapters
        return url.startswith("http")

    async def scrape(self, url: str) -> NormalizedDocument:
        logger.info("scraping_generic", url=url)

        headers = {
            "User-Agent": settings.SCRAPE_USER_AGENT
            if hasattr(settings, "SCRAPE_USER_AGENT")
            else "Mozilla/5.0 (compatible; MinoverseBot/1.0)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        async with httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
            headers=headers,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            html = response.text
            final_url = str(response.url)

        # Try trafilatura first (best quality)
        content, metadata = self._extract_trafilatura(html, url)

        # Fall back to BeautifulSoup if trafilatura gives nothing
        if not content or len(content) < 100:
            content, metadata = self._extract_bs4(html, url)

        source_type = self._detect_source_type(final_url)

        return NormalizedDocument(
            source_url=url,
            source_type=source_type,
            canonical_url=final_url if final_url != url else None,
            title=metadata.get("title"),
            author=metadata.get("author"),
            content=content,
            tags=metadata.get("tags", []),
            metadata={
                "hostname": metadata.get("hostname"),
                "description": metadata.get("description"),
                "image": metadata.get("image"),
                "word_count_raw": len(content.split()) if content else 0,
            },
        )

    def _extract_trafilatura(self, html: str, url: str) -> tuple[str, dict]:  # type: ignore[type-arg]
        try:
            import trafilatura  # type: ignore[import-untyped]
            from trafilatura.metadata import extract_metadata  # type: ignore[import-untyped]

            content = trafilatura.extract(
                html,
                url=url,
                include_comments=False,
                include_tables=True,
                no_fallback=False,
            ) or ""

            meta_obj = extract_metadata(html, default_url=url)
            metadata: dict = {}  # type: ignore[type-arg]
            if meta_obj:
                metadata = {
                    "title": meta_obj.title,
                    "author": meta_obj.author,
                    "hostname": meta_obj.hostname,
                    "description": meta_obj.description,
                    "image": meta_obj.image,
                    "tags": list(meta_obj.tags or []),
                }

            return content, metadata
        except Exception as e:
            logger.warning("trafilatura_failed", error=str(e))
            return "", {}

    def _extract_bs4(self, html: str, url: str) -> tuple[str, dict]:  # type: ignore[type-arg]
        try:
            from bs4 import BeautifulSoup  # type: ignore[import-untyped]

            soup = BeautifulSoup(html, "lxml")

            # Remove noise
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()

            title = ""
            title_tag = soup.find("title")
            if title_tag:
                title = title_tag.get_text(strip=True)

            # Try main content areas
            content = ""
            for selector in ["main", "article", '[role="main"]', ".post-content", ".entry-content", "#content"]:
                el = soup.select_one(selector)
                if el:
                    content = el.get_text(separator=" ", strip=True)
                    break

            if not content:
                body = soup.find("body")
                content = body.get_text(separator=" ", strip=True) if body else ""

            # Clean whitespace
            content = re.sub(r"\s+", " ", content).strip()

            return content, {"title": title}
        except Exception as e:
            logger.warning("bs4_extraction_failed", error=str(e))
            return "", {}

    def _detect_source_type(self, url: str) -> SourceType:
        if "medium.com" in url:
            return SourceType.MEDIUM
        if "reddit.com" in url:
            return SourceType.REDDIT
        if "news.ycombinator.com" in url:
            return SourceType.HACKERNEWS
        if url.endswith(".pdf"):
            return SourceType.PDF
        return SourceType.ARTICLE
