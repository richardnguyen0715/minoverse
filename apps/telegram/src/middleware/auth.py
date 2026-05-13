"""Auth middleware — enforces user allowlist."""
from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from ..config import settings
import structlog

logger = structlog.get_logger(__name__)


def is_authorized(user_id: int) -> bool:
    """Return True if the user is allowed to use the bot."""
    allowed = settings.allowed_user_ids
    if not allowed:
        return True  # No allowlist = open bot
    return user_id in allowed


async def require_auth(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check auth and send rejection message if unauthorized. Returns True if authorized."""
    if update.effective_user is None:
        return False

    user_id = update.effective_user.id
    if not is_authorized(user_id):
        logger.warning("unauthorized_access", user_id=user_id)
        if update.message:
            await update.message.reply_text(
                "⛔ You are not authorized to use this bot.\n"
                "Contact the administrator to request access."
            )
        return False

    return True
