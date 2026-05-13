"""Markdown parsing pipeline — converts vault files to ParsedDocument.

Uses markdown-it-py for AST-level parsing and python-frontmatter
for YAML frontmatter extraction. NEVER uses regex for markdown parsing.

Constraints:
    - This module is pure — no I/O side effects.
    - All functions are idempotent and stateless.
    - parse_markdown_file() is the single public entry point.
"""
import hashlib
import re
from pathlib import Path

import frontmatter
import structlog
from markdown_it import MarkdownIt
from markdown_it.token import Token

from src.ingestion.schemas.parsed_document import (
    Heading,
    ParsedDocument,
    WikiLinkRef,
)

logger = structlog.get_logger(__name__)

# Wiki link pattern: [[target]] or [[target|alias]]
# This is the only regex allowed — for the wiki link syntax which
# markdown-it-py does not natively handle.
_WIKI_LINK_RE = re.compile(r"\[\[([^\]\|]+)(?:\|([^\]]+))?\]\]")

# URL pattern for extracting bare URLs from inline tokens
_URL_RE = re.compile(r"https?://[^\s\)\"\']+")


def parse_markdown_file(file_path: Path) -> ParsedDocument:
    """Parse a vault markdown file into a structured ParsedDocument.

    This is the primary entry point for the ingestion pipeline's
    parsing stage. It combines frontmatter extraction with AST-level
    markdown analysis.

    Args:
        file_path: Absolute or relative path to the .md file.

    Returns:
        ParsedDocument: Fully populated parsed representation.

    Raises:
        FileNotFoundError: If the file does not exist on disk.
        MarkdownParseError: If the file content cannot be parsed.

    Side Effects:
        None — this function is pure and reads only.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Vault file not found: {file_path}")

    raw_markdown = file_path.read_text(encoding="utf-8")

    logger.debug("parsing_markdown_file", path=str(file_path))

    try:
        post = frontmatter.loads(raw_markdown)
    except Exception as exc:
        from src.core.exceptions import MarkdownParseError

        raise MarkdownParseError(
            f"Failed to parse frontmatter in {file_path}",
            context={"path": str(file_path), "error": str(exc)},
        ) from exc

    extracted_frontmatter: dict[str, object] = dict(post.metadata)
    body = post.content

    md = MarkdownIt()
    tokens = md.parse(body)

    headings = _extract_headings(tokens)
    wiki_links = _extract_wiki_links(body)
    tags = _extract_tags(extracted_frontmatter)
    urls = _extract_urls(tokens, body)
    aliases = _extract_aliases(extracted_frontmatter)

    return ParsedDocument(
        source_path=file_path,
        frontmatter=extracted_frontmatter,
        body=body,
        raw_markdown=raw_markdown,
        headings=headings,
        wiki_links=wiki_links,
        tags=tags,
        urls=urls,
        aliases=aliases,
        char_count=len(body),
        word_count=len(body.split()),
    )


def _extract_headings(tokens: list[Token]) -> list[Heading]:
    """Extract headings from a markdown-it token stream.

    Args:
        tokens: Top-level token list from markdown-it parse().

    Returns:
        list[Heading]: Headings in document order.
    """
    headings: list[Heading] = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token.type == "heading_open" and token.tag:
            level = int(token.tag[1])  # h1 → 1, h2 → 2, etc.
            if i + 1 < len(tokens) and tokens[i + 1].type == "inline":
                text = tokens[i + 1].content.strip()
                slug = _slugify(text)
                headings.append(Heading(level=level, text=text, slug=slug))
        i += 1
    return headings


def _extract_wiki_links(content: str) -> list[WikiLinkRef]:
    """Extract all [[wiki links]] from markdown content.

    This uses a targeted regex for the Obsidian wiki-link syntax,
    which markdown-it-py does not handle natively.

    Args:
        content: Raw markdown body text (post-frontmatter).

    Returns:
        list[WikiLinkRef]: Deduplicated wiki link references.
    """
    seen: set[str] = set()
    links: list[WikiLinkRef] = []

    for match in _WIKI_LINK_RE.finditer(content):
        target = match.group(1).strip()
        alias = match.group(2).strip() if match.group(2) else None
        raw = match.group(0)

        if target not in seen:
            seen.add(target)
            links.append(WikiLinkRef(target=target, alias=alias, raw=raw))

    return links


def _extract_tags(fm: dict[str, object]) -> list[str]:
    """Extract and normalize tags from frontmatter.

    Supports both list-style tags and space-separated string tags.

    Args:
        fm: Parsed frontmatter dict.

    Returns:
        list[str]: Deduplicated, lowercased tag slugs.
    """
    raw_tags = fm.get("tags", [])

    if isinstance(raw_tags, str):
        raw_tags = raw_tags.split()
    elif not isinstance(raw_tags, list):
        return []

    return list({str(tag).lower().strip() for tag in raw_tags if tag})


def _extract_urls(tokens: list[Token], content: str) -> list[str]:
    """Extract all HTTP/HTTPS URLs from markdown tokens and content.

    Args:
        tokens: Top-level token list from markdown-it parse().
        content: Raw markdown body for fallback bare URL detection.

    Returns:
        list[str]: Deduplicated URL strings.
    """
    urls: set[str] = set()

    def _walk(token_list: list[Token]) -> None:
        for token in token_list:
            if token.type == "link_open":
                href = token.attrGet("href") or ""
                if href.startswith(("http://", "https://")):
                    urls.add(href)
            if token.children:
                _walk(token.children)

    _walk(tokens)

    for match in _URL_RE.finditer(content):
        urls.add(match.group(0).rstrip(".,;)"))

    return list(urls)


def _extract_aliases(fm: dict[str, object]) -> list[str]:
    """Extract note aliases from frontmatter.

    Args:
        fm: Parsed frontmatter dict.

    Returns:
        list[str]: List of alias strings.
    """
    raw = fm.get("aliases", [])
    if isinstance(raw, str):
        return [raw.strip()] if raw.strip() else []
    if isinstance(raw, list):
        return [str(a).strip() for a in raw if a]
    return []


def _slugify(text: str) -> str:
    """Convert heading text to a URL-safe slug."""
    slug = text.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug.strip("-")


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file for change detection.

    Args:
        file_path: Path to the file.

    Returns:
        str: Hex-encoded SHA-256 digest.
    """
    hasher = hashlib.sha256()
    hasher.update(file_path.read_bytes())
    return hasher.hexdigest()
