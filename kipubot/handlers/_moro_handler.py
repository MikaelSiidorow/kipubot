import psycopg.errors as PSErrors
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
import telegram.ext.filters as Filters
from db import get_con
from constants import STRINGS
from utils import save_user_or_ignore

CON = get_con()


async def hello(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    username = update.effective_user.username
    chat = update.effective_chat.title

    save_user_or_ignore(user_id, username)

    try:
        CON.execute('''INSERT INTO in_chat(user_id, chat_id)
                        VALUES (%s, %s)''',
                    (user_id, chat_id))
        await update.message.reply_text(STRINGS['moro'] %
                                        {'username': username, 'chat_title': chat})
    except PSErrors.IntegrityError:
        await update.message.reply_text(STRINGS['double_moro'] % {'chat_title': chat})

    CON.commit()

moro_handler = CommandHandler(
    ['moro', 'hello'], hello, ~Filters.ChatType.PRIVATE)
