"""Unit tests for the markdown parsing pipeline.

These tests are pure — no DB, no filesystem writes, no network.
"""
import tempfile
from pathlib import Path

import pytest
from markdown_it import MarkdownIt

from src.ingestion.pipelines.markdown_parser import (
    _extract_headings,
    _extract_tags,
    _extract_wiki_links,
    parse_markdown_file,
)


def _make_temp_md(content: str) -> Path:
    """Helper: write content to a temp .md file and return its path."""
    tmp = tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w")
    tmp.write(content)
    tmp.close()
    return Path(tmp.name)


class TestParseMarkdownFile:
    def test_parses_frontmatter(self) -> None:
        path = _make_temp_md("---\ntitle: Test Note\ntags:\n  - rag\n---\n\n# Body")
        doc = parse_markdown_file(path)
        assert doc.frontmatter["title"] == "Test Note"

    def test_parses_body_separately_from_frontmatter(self) -> None:
        path = _make_temp_md("---\ntitle: X\n---\n\nHello world")
        doc = parse_markdown_file(path)
        assert "Hello world" in doc.body
        assert "title" not in doc.body

    def test_raises_on_missing_file(self) -> None:
        with pytest.raises(FileNotFoundError):
            parse_markdown_file(Path("/nonexistent/file.md"))

    def test_char_count_matches_body(self) -> None:
        body = "Hello world"
        path = _make_temp_md(f"---\ntitle: X\n---\n\n{body}")
        doc = parse_markdown_file(path)
        assert doc.char_count == len(doc.body)


class TestExtractWikiLinks:
    def test_extracts_simple_link(self) -> None:
        links = _extract_wiki_links("See [[RAG]] for details.")
        assert len(links) == 1
        assert links[0].target == "RAG"
        assert links[0].alias is None

    def test_extracts_aliased_link(self) -> None:
        links = _extract_wiki_links("Read [[Transformers|the paper]].")
        assert links[0].target == "Transformers"
        assert links[0].alias == "the paper"

    def test_deduplicates_links(self) -> None:
        links = _extract_wiki_links("[[RAG]] and [[RAG]] again.")
        assert len(links) == 1

    def test_multiple_links(self) -> None:
        links = _extract_wiki_links("[[A]] and [[B]] and [[C]]")
        assert len(links) == 3

    def test_empty_content(self) -> None:
        links = _extract_wiki_links("")
        assert links == []


class TestExtractHeadings:
    def test_extracts_h1(self) -> None:
        md = MarkdownIt()
        tokens = md.parse("# Attention Is All You Need")
        headings = _extract_headings(tokens)
        assert headings[0].level == 1
        assert headings[0].text == "Attention Is All You Need"

    def test_extracts_multiple_levels(self) -> None:
        md = MarkdownIt()
        tokens = md.parse("# H1\n## H2\n### H3")
        headings = _extract_headings(tokens)
        assert [h.level for h in headings] == [1, 2, 3]

    def test_slugifies_heading(self) -> None:
        md = MarkdownIt()
        tokens = md.parse("# Hello World!")
        headings = _extract_headings(tokens)
        assert headings[0].slug == "hello-world"


class TestExtractTags:
    def test_list_tags(self) -> None:
        tags = _extract_tags({"tags": ["RAG", "LLM", "Transformers"]})
        assert "rag" in tags
        assert "llm" in tags

    def test_string_tags(self) -> None:
        tags = _extract_tags({"tags": "rag llm"})
        assert "rag" in tags
        assert "llm" in tags

    def test_no_tags(self) -> None:
        tags = _extract_tags({})
        assert tags == []

    def test_deduplicates_tags(self) -> None:
        tags = _extract_tags({"tags": ["RAG", "rag", "Rag"]})
        assert len(tags) == 1
