from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
import telegram.ext.filters as Filters
from constants import STRINGS


async def chat_only(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(STRINGS['no_dm_warn'])

no_dm_handler = CommandHandler(
    ['moro', 'hello', 'kuvaaja', 'graph', 'voittaja', 'winner'],
    chat_only, Filters.ChatType.PRIVATE)
