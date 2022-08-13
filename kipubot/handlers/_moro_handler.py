from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
import telegram.ext.filters as Filters
from kipubot.constants import STRINGS
from kipubot.utils import register_user
from kipubot.errors import AlreadyRegisteredError


async def hello(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    username = update.effective_user.username
    chat = update.effective_chat.title

    try:
        register_user(chat_id, user_id)

    except AlreadyRegisteredError:
        await update.message.reply_text(STRINGS['double_moro'] %
                                        {'username': username, 'chat_title': chat})
    else:
        await update.message.reply_text(STRINGS['moro'] %
                                        {'username': username, 'chat_title': chat})

moro_handler = CommandHandler(
    ['moro', 'hello'], hello, ~Filters.ChatType.PRIVATE)
