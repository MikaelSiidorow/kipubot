from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
import telegram.ext.filters as Filters


async def chat_only(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('This command is not usable in private messages!')

no_dm_handler = CommandHandler(
    ['moro', 'hello', 'kuvaaja', 'graph', 'voittaja', 'winner'],
    chat_only, Filters.ChatType.PRIVATE)
