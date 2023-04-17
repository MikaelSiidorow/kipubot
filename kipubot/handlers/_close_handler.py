from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, filters

from kipubot.constants import STRINGS
from kipubot.db import (
    close_raffle,
    get_admin_ids,
    get_winner_id,
)


async def close(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_chat or not update.effective_user or not update.message:
        return None

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    is_admin = user_id in get_admin_ids(chat_id)
    is_cur_winner = user_id == get_winner_id(chat_id)

    if not is_admin and not is_cur_winner:
        await update.message.reply_text(STRINGS["forbidden_command"])
        return

    close_raffle(chat_id)

    await update.message.reply_text(
        STRINGS["close_confirmation"] % {"username": update.effective_user.username}
    )


close_handler = CommandHandler(["sulje", "close"], close, ~filters.ChatType.PRIVATE)
