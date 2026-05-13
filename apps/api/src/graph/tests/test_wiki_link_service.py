"""Unit tests for wiki link extraction logic (pure, no DB)."""
from src.ingestion.pipelines.markdown_parser import _extract_wiki_links


class TestWikiLinkExtraction:
    def test_no_links_returns_empty(self) -> None:
        links = _extract_wiki_links("No links here.")
        assert links == []

    def test_nested_brackets_ignored(self) -> None:
        links = _extract_wiki_links("[regular link](url)")
        assert links == []

    def test_link_with_heading_fragment(self) -> None:
        links = _extract_wiki_links("[[Note#Section]]")
        assert links[0].target == "Note#Section"
