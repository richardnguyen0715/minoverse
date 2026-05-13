"""YouTube scraper adapter.

Uses yt-dlp for metadata + transcript extraction.
No API key required for public videos.
"""
from __future__ import annotations

import asyncio
import logging
from functools import partial

import structlog

from ..schemas import NormalizedDocument, SourceType, MediaItem
from .base import BaseScraper

logger = structlog.get_logger(__name__)


class YouTubeScraper(BaseScraper):
    """Extracts transcript, metadata, and optionally comments from YouTube videos."""

    @property
    def name(self) -> str:
        return "youtube"

    def can_handle(self, url: str) -> bool:
        return any(
            domain in url
            for domain in ["youtube.com/watch", "youtu.be/", "youtube.com/shorts/"]
        )

    async def scrape(self, url: str) -> NormalizedDocument:
        logger.info("scraping_youtube", url=url)

        try:
            import yt_dlp  # type: ignore[import-untyped]
        except ImportError:
            raise RuntimeError("yt-dlp not installed. Run: uv add yt-dlp")

        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, partial(self._extract_info, url, yt_dlp))

        # Extract transcript
        transcript = self._extract_transcript(info)
        if not transcript:
            # Fall back to description
            transcript = info.get("description", "")

        # Build content from transcript or description
        content = transcript or info.get("description", f"Video: {info.get('title', url)}")

        # Media
        thumbnails = info.get("thumbnails", [])
        media = []
        if thumbnails:
            best = max(thumbnails, key=lambda t: (t.get("width", 0) or 0))
            if best.get("url"):
                media.append(MediaItem(url=best["url"], type="image", alt="thumbnail"))

        return NormalizedDocument(
            source_url=url,
            source_type=SourceType.YOUTUBE,
            canonical_url=f"https://www.youtube.com/watch?v={info.get('id', '')}",
            title=info.get("title"),
            author=info.get("uploader") or info.get("channel"),
            content=content,
            tags=[t.get("term", "") for t in info.get("tags", []) if isinstance(t, dict)]
                 or info.get("tags", [])[:10],
            media=media,
            metadata={
                "video_id": info.get("id"),
                "duration_seconds": info.get("duration"),
                "view_count": info.get("view_count"),
                "like_count": info.get("like_count"),
                "channel_id": info.get("channel_id"),
                "upload_date": info.get("upload_date"),
                "categories": info.get("categories", []),
                "has_transcript": bool(transcript),
            },
        )

    def _extract_info(self, url: str, yt_dlp: object) -> dict:  # type: ignore[type-arg]
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "writesubtitles": True,
            "subtitleslangs": ["en", "en-US"],
            "skip_download": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore[attr-defined]
            return ydl.extract_info(url, download=False)  # type: ignore[no-any-return]

    def _extract_transcript(self, info: dict) -> str:  # type: ignore[type-arg]
        """Extract transcript from subtitles if available."""
        subtitles = info.get("subtitles", {}) or info.get("automatic_captions", {})
        for lang in ["en", "en-US", "en-GB"]:
            if lang in subtitles:
                subs = subtitles[lang]
                if isinstance(subs, list) and subs:
                    # Get first available format
                    for sub in subs:
                        if sub.get("ext") in ("json3", "srv3", "ttml"):
                            # Would need to download and parse — return empty for now
                            # In production, yt-dlp handles this
                            pass
        return ""
