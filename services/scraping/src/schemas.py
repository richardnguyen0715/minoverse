"""Normalized document schema — canonical output of all scrapers."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    ARTICLE = "article"
    YOUTUBE = "youtube"
    GITHUB = "github"
    REDDIT = "reddit"
    HACKERNEWS = "hackernews"
    MEDIUM = "medium"
    TWITTER = "twitter"
    GENERIC = "generic"
    PDF = "pdf"


class MediaItem(BaseModel):
    url: str
    type: str  # image | video | audio
    alt: str | None = None


class Comment(BaseModel):
    author: str | None = None
    content: str
    score: int | None = None
    created_at: datetime | None = None
    replies: list["Comment"] = Field(default_factory=list)


class NormalizedDocument(BaseModel):
    """Canonical document output from all scrapers.

    All scrapers MUST return this schema.
    PostgreSQL is the source of truth — this goes into the contents table.
    """

    # Identity
    source_url: str
    source_type: SourceType
    canonical_url: str | None = None

    # Content
    title: str | None = None
    author: str | None = None
    content: str  # main text/transcript — always present
    summary: str | None = None  # pre-generated summary if available

    # Metadata
    published_at: datetime | None = None
    language: str | None = None
    tags: list[str] = Field(default_factory=list)

    # Rich content
    comments: list[Comment] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    media: list[MediaItem] = Field(default_factory=list)
    entities: list[dict[str, Any]] = Field(default_factory=list)

    # Source-specific metadata (flexible)
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Processing
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    scraper_version: str = "1.0.0"
    char_count: int = 0
    word_count: int = 0

    def model_post_init(self, __context: Any) -> None:
        if self.content:
            self.char_count = len(self.content)
            self.word_count = len(self.content.split())
