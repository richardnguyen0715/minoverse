"""Response formatter utilities for Telegram messages."""
from __future__ import annotations

import re


def escape_md(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2."""
    # Characters that must be escaped: _ * [ ] ( ) ~ ` > # + - = | { } . !
    special = r"_*[]()~`>#+-=|{}.!\\"
    return re.sub(r"([" + re.escape(special) + r"])", r"\\\1", text)


def format_ingest_result(result: dict, url: str, mode: str) -> str:  # type: ignore[type-arg]
    """Format an ingest result for Telegram display."""
    title = result.get("title") or url
    summary = result.get("summary") or "No summary generated."
    source_type = result.get("source_type", "generic")
    entities = result.get("entities", [])
    tags = result.get("tags", [])
    ms = result.get("processing_time_ms", 0)

    mode_icon = {"quick": "⚡", "technical": "🔧", "research": "🔬"}.get(mode, "📄")

    lines = [
        f"{mode_icon} *{escape_md(title[:100])}*",
        f"`{escape_md(source_type)}`\n",
        escape_md(summary[:800]),
    ]

    if tags:
        tag_str = "  ".join(f"`{escape_md(t)}`" for t in tags[:8])
        lines.append(f"\n🏷️ {tag_str}")

    if entities:
        ent_strs = [f"{escape_md(e.get('name', ''))} `[{escape_md(e.get('type', ''))}]`" for e in entities[:6]]
        lines.append(f"\n🔬 *Entities:* {', '.join(ent_strs)}")

    lines.append(f"\n🔗 [Source]({url})")
    lines.append(f"\n_{escape_md(f'Processed in {ms}ms')}_")

    return "\n".join(lines)


def format_research_results(result: dict, topic: str) -> str:  # type: ignore[type-arg]
    """Format research results for Telegram."""
    results = result.get("results", [])
    total = result.get("total", len(results))

    if not results:
        return f"🔬 *Research: {escape_md(topic)}*\n\n⚠️ No results found\\."

    lines = [f"🔬 *Research: {escape_md(topic[:60])}*\n", f"Found {total} results:\n"]

    for i, item in enumerate(results[:8], 1):
        title = item.get("title") or item.get("url", "Untitled")
        url = item.get("url", "")
        snippet = (item.get("snippet") or "")[:150]
        source = item.get("source", "web")
        source_icon = {"hackernews": "🔶", "github": "🐙", "reddit": "🔴"}.get(source, "🌐")

        lines.append(f"{i}\\. {source_icon} [{escape_md(title[:80])}]({url})")
        if snippet:
            lines.append(f"   _{escape_md(snippet)}_")
        lines.append("")

    return "\n".join(lines)


def format_memory_results(result: dict, query: str) -> str:  # type: ignore[type-arg]
    """Format memory query results for Telegram."""
    memories = result.get("memories", [])
    total = result.get("total", len(memories))

    if not memories:
        return f"💾 *Memory: {escape_md(query)}*\n\n⚠️ No memories found\\."

    lines = [f"💾 *Memory: {escape_md(query[:60])}*\n", f"Found {total} memories:\n"]

    for mem in memories[:5]:
        mem_type = mem.get("type", "?")
        content = mem.get("content", "")[:200]
        score = mem.get("importance_score")

        type_icon = {"episodic": "📖", "semantic": "💡", "procedural": "⚙️"}.get(mem_type, "💾")
        score_str = f" \\[{score:.2f}\\]" if score is not None else ""

        lines.append(f"{type_icon} `{escape_md(mem_type)}`{score_str}")
        lines.append(f"_{escape_md(content)}_\n")

    return "\n".join(lines)
