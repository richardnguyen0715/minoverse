"""Pydantic schemas for markdown parsing pipeline outputs.

These are the data contracts between the parsing stage and all
downstream pipeline steps (ingestion, graph, tagging, embedding).
"""
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Heading:
    """A heading extracted from markdown AST.

    Attributes:
        level: Heading depth (1=H1, 2=H2, ..., 6=H6).
        text: Plain text content of the heading.
        slug: URL-safe lowercase slug of the heading text.
    """

    level: int
    text: str
    slug: str


@dataclass(frozen=True)
class WikiLinkRef:
    """A [[wiki link]] reference extracted from markdown.

    Attributes:
        target: The link target (text inside [[ ]]).
        alias: Optional display alias after | separator.
        raw: The original raw link text including [[ ]].
    """

    target: str
    alias: str | None
    raw: str


@dataclass
class ParsedDocument:
    """Complete parsed representation of a vault markdown file.

    This is the central data contract for the ingestion pipeline.
    All parsing results flow through this object.

    Invariants:
        - frontmatter is always a dict (empty if none present).
        - wiki_links contains only resolved [[target]] refs.
        - headings are in document order.
        - tags are deduplicated and lowercased.
    """

    source_path: Path
    frontmatter: dict[str, object] = field(default_factory=dict)
    body: str = ""
    raw_markdown: str = ""
    headings: list[Heading] = field(default_factory=list)
    wiki_links: list[WikiLinkRef] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    urls: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    char_count: int = 0
    word_count: int = 0
