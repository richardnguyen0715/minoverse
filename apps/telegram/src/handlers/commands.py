"""Telegram command handlers."""
from __future__ import annotations

import structlog
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from ..middleware.auth import require_auth
from ..services.api_client import api
from ..utils.formatter import format_ingest_result, format_memory_results, format_research_results, escape_md

logger = structlog.get_logger(__name__)

# ── /start ────────────────────────────────────────────────────────────────────

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_auth(update, context):
        return
    if not update.message:
        return

    await update.message.reply_text(
        "🧠 *Minoverse AutoIngest Bot*\n\n"
        "I'm your autonomous research and knowledge assistant\\.\n\n"
        "*Commands:*\n"
        "📥 `/analyze <url>` — Analyze a URL\n"
        "🔬 `/research <topic>` — Deep research\n"
        "💾 `/memory <query>` — Search your knowledge base\n"
        "🕸️ `/graph <entity>` — Explore knowledge graph\n"
        "⚡ `/quick <url>` — Quick TLDR summary\n"
        "🔄 `/update <url>` — Re\\-analyze & update\n"
        "❓ `/help` — Show this message\n"
        "💊 `/status` — System health check",
        parse_mode=ParseMode.MARKDOWN_V2,
    )


# ── /analyze ──────────────────────────────────────────────────────────────────

async def analyze_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_auth(update, context):
        return
    if not update.message:
        return

    args = context.args or []
    if not args:
        await update.message.reply_text(
            "Usage: `/analyze <url>`\nExample: `/analyze https://github.com/openai/openai-python`",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    url = args[0]
    if not url.startswith("http"):
        await update.message.reply_text("⚠️ Please provide a valid URL starting with http(s)://")
        return

    # Determine mode from second arg
    mode = "technical"
    if len(args) > 1 and args[1] in ("quick", "technical", "research"):
        mode = args[1]

    status_msg = await update.message.reply_text(
        f"🔍 Analyzing...\n`{url[:60]}`",
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    try:
        # Stream events and update message
        last_step = ""
        result = None

        async for event in api.stream_ingest(url, mode=mode):
            event_type = event.get("type", "")
            if event_type == "scraping":
                last_step = "🕷️ Scraping content..."
            elif event_type == "extracting_entities":
                last_step = "🔬 Extracting entities..."
            elif event_type == "summarizing":
                last_step = "✍️ Generating summary..."
            elif event_type == "storing":
                last_step = "💾 Storing in knowledge base..."
            elif event_type == "completed":
                result = event.get("data", {})
            elif event_type == "error":
                await status_msg.edit_text(f"❌ Error: {event.get('message', 'Unknown error')}")
                return

            if last_step:
                try:
                    await status_msg.edit_text(
                        f"⏳ {last_step}\n`{url[:50]}`",
                        parse_mode=ParseMode.MARKDOWN_V2,
                    )
                except Exception:
                    pass

        if result:
            text = format_ingest_result(result, url, mode)
            await status_msg.edit_text(text, parse_mode=ParseMode.MARKDOWN_V2)
        else:
            # Fallback to non-streaming
            result = await api.ingest(url, mode=mode)
            text = format_ingest_result(result, url, mode)
            await status_msg.edit_text(text, parse_mode=ParseMode.MARKDOWN_V2)

    except Exception as e:
        logger.error("analyze_failed", url=url, error=str(e))
        await status_msg.edit_text(
            f"❌ Failed to analyze URL\\.\n\n`{escape_md(str(e)[:200])}`",
            parse_mode=ParseMode.MARKDOWN_V2,
        )


# ── /quick ────────────────────────────────────────────────────────────────────

async def quick_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_auth(update, context):
        return
    if not update.message:
        return

    args = context.args or []
    if not args:
        await update.message.reply_text("Usage: `/quick <url>`", parse_mode=ParseMode.MARKDOWN_V2)
        return

    url = args[0]
    status_msg = await update.message.reply_text("⚡ Getting quick summary...")

    try:
        result = await api.ingest(url, mode="quick")
        summary = result.get("summary") or "No summary available."
        title = result.get("title") or url

        text = (
            f"⚡ *Quick Summary*\n\n"
            f"*{escape_md(title[:100])}*\n\n"
            f"{escape_md(summary[:800])}\n\n"
            f"🔗 [Source]({url})"
        )
        await status_msg.edit_text(text, parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {escape_md(str(e)[:200])}", parse_mode=ParseMode.MARKDOWN_V2)


# ── /research ─────────────────────────────────────────────────────────────────

async def research_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_auth(update, context):
        return
    if not update.message:
        return

    args = context.args or []
    if not args:
        await update.message.reply_text(
            "Usage: `/research <topic>`\nExample: `/research RAG architectures 2024`",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    topic = " ".join(args)
    status_msg = await update.message.reply_text(
        f"🔬 Researching: *{escape_md(topic[:60])}*\\.\\.\\.",
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    try:
        result = await api.research(topic)
        text = format_research_results(result, topic)
        await status_msg.edit_text(text, parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        logger.error("research_failed", topic=topic, error=str(e))
        await status_msg.edit_text(
            f"❌ Research failed\\.\n`{escape_md(str(e)[:200])}`",
            parse_mode=ParseMode.MARKDOWN_V2,
        )


# ── /memory ───────────────────────────────────────────────────────────────────

async def memory_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_auth(update, context):
        return
    if not update.message:
        return

    args = context.args or []
    if not args:
        await update.message.reply_text(
            "Usage: `/memory <query>`\nExample: `/memory RAG vector databases`",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    query = " ".join(args)
    status_msg = await update.message.reply_text(
        f"💾 Searching memory: *{escape_md(query[:60])}*\\.\\.\\.",
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    try:
        result = await api.query_memory(query)
        text = format_memory_results(result, query)
        await status_msg.edit_text(text, parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        await status_msg.edit_text(
            f"❌ Memory query failed\\.\n`{escape_md(str(e)[:200])}`",
            parse_mode=ParseMode.MARKDOWN_V2,
        )


# ── /graph ────────────────────────────────────────────────────────────────────

async def graph_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_auth(update, context):
        return
    if not update.message:
        return

    args = context.args or []
    if not args:
        await update.message.reply_text(
            "Usage: `/graph <entity>`\nExample: `/graph LangChain`",
            parse_mode=ParseMode.MARKDOWN_V2,
        )
        return

    entity = " ".join(args)
    status_msg = await update.message.reply_text(
        f"🕸️ Loading graph for: *{escape_md(entity)}*\\.\\.\\.",
        parse_mode=ParseMode.MARKDOWN_V2,
    )

    try:
        result = await api.graph_context(entity)
        nodes = result.get("nodes", [])
        edges = result.get("edges", [])

        if not nodes:
            await status_msg.edit_text(f"⚠️ No graph data found for *{escape_md(entity)}*", parse_mode=ParseMode.MARKDOWN_V2)
            return

        lines = [f"🕸️ *Graph: {escape_md(entity)}*\n"]
        lines.append(f"*Nodes \\({len(nodes)}\\):*")
        for node in nodes[:10]:
            lines.append(f"  • {escape_md(node.get('name', ''))} `[{escape_md(node.get('type', ''))}]`")

        if edges:
            lines.append(f"\n*Edges \\({len(edges)}\\):*")
            node_map = {n["id"]: n["name"] for n in nodes}
            for edge in edges[:8]:
                src = escape_md(node_map.get(edge.get("source", ""), "?"))
                tgt = escape_md(node_map.get(edge.get("target", ""), "?"))
                rel = escape_md(edge.get("type", ""))
                lines.append(f"  {src} → `{rel}` → {tgt}")

        await status_msg.edit_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        await status_msg.edit_text(
            f"❌ Graph query failed\\.\n`{escape_md(str(e)[:200])}`",
            parse_mode=ParseMode.MARKDOWN_V2,
        )


# ── /status ───────────────────────────────────────────────────────────────────

async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_auth(update, context):
        return
    if not update.message:
        return

    try:
        health = await api.health()
        status = health.get("status", "unknown")
        icon = "✅" if status == "ok" else "⚠️" if status == "degraded" else "❌"
        version = health.get("version", "?")

        lines = [f"{icon} *System Status: {escape_md(status)}* \\(v{escape_md(version)}\\)\n"]
        for component, comp_status in health.get("components", {}).items():
            comp_icon = "✅" if comp_status == "ok" else "❌"
            lines.append(f"  {comp_icon} {escape_md(component)}: {escape_md(comp_status)}")

        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        await update.message.reply_text(
            f"❌ API unreachable\\.\n`{escape_md(str(e)[:200])}`",
            parse_mode=ParseMode.MARKDOWN_V2,
        )


# ── /help ─────────────────────────────────────────────────────────────────────

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await require_auth(update, context):
        return
    if not update.message:
        return

    await update.message.reply_text(
        "🧠 *Minoverse AutoIngest — Help*\n\n"
        "📥 `/analyze <url>` — Full analysis \\(scrape \\+ entities \\+ summary \\+ store\\)\n"
        "  Options: add `quick`, `technical`, or `research` as second arg\n\n"
        "⚡ `/quick <url>` — Quick TLDR summary only\n\n"
        "🔬 `/research <topic>` — Multi\\-source research report\n\n"
        "💾 `/memory <query>` — Search your long\\-term memory\n\n"
        "🕸️ `/graph <entity>` — Explore knowledge graph connections\n\n"
        "🔄 `/update <url>` — Re\\-analyze and update existing entry\n\n"
        "💊 `/status` — Check system health\n\n"
        "📋 `/help` — Show this message\n\n"
        "You can also just send a URL and I'll analyze it automatically\\.",
        parse_mode=ParseMode.MARKDOWN_V2,
    )


# ── URL message handler ───────────────────────────────────────────────────────

async def url_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle bare URL messages (no command)."""
    if not await require_auth(update, context):
        return
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    if text.startswith("http"):
        # Treat as /analyze
        context.args = [text]
        await analyze_handler(update, context)
