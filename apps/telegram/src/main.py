"""Minoverse Telegram Bot — main entry point."""
from __future__ import annotations

import asyncio
import logging

import structlog
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from .config import settings
from .handlers.commands import (
    analyze_handler,
    graph_handler,
    help_handler,
    memory_handler,
    quick_handler,
    research_handler,
    start_handler,
    status_handler,
    url_message_handler,
)

logger = structlog.get_logger(__name__)


def build_app():  # type: ignore[return]
    """Build and configure the Telegram bot application."""
    app = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("analyze", analyze_handler))
    app.add_handler(CommandHandler("quick", quick_handler))
    app.add_handler(CommandHandler("research", research_handler))
    app.add_handler(CommandHandler("memory", memory_handler))
    app.add_handler(CommandHandler("graph", graph_handler))
    app.add_handler(CommandHandler("update", analyze_handler))  # /update = re-analyze
    app.add_handler(CommandHandler("status", status_handler))

    # Handle bare URL messages
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.Regex(r"https?://"),
            url_message_handler,
        )
    )

    return app


def main() -> None:
    """Run the Telegram bot."""
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    )

    logger.info("telegram_bot_starting")
    app = build_app()

    if settings.TELEGRAM_WEBHOOK_URL:
        # Production: webhook mode
        logger.info("starting_webhook", url=settings.TELEGRAM_WEBHOOK_URL)
        app.run_webhook(
            listen="0.0.0.0",
            port=8443,
            url_path=settings.TELEGRAM_BOT_TOKEN,
            webhook_url=f"{settings.TELEGRAM_WEBHOOK_URL}/{settings.TELEGRAM_BOT_TOKEN}",
        )
    else:
        # Development: polling mode
        logger.info("starting_polling")
        app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
