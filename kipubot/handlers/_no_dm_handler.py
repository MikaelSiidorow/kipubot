from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, filters

from kipubot.constants import STRINGS


async def chat_only(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return None
    await update.message.reply_text(STRINGS["no_dm_warn"])


no_dm_handler = CommandHandler(
    ["moro", "hello", "kuvaaja", "graph", "voittaja", "winner"],
    chat_only,
    filters.ChatType.PRIVATE,
)
