import psycopg.errors as PSErrors
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
import telegram.ext.filters as Filters
from db import get_con
from constants import STRINGS

CON = get_con()


async def hello(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    username = update.effective_user.username
    chat = update.effective_chat.title

    try:
        CON.execute('''INSERT INTO chat_user (user_id, username)
                        VALUES (%s, %s)
                        ON CONFLICT (user_id)
                        DO NOTHING''',
                    (user_id, username))

        try:
            CON.execute('''INSERT INTO in_chat(user_id, chat_id)
                            VALUES (%s, %s)''',
                        (user_id, chat_id))
            await update.message.reply_text(STRINGS['moro'] %
                                            {'username': username, 'chat_title': chat})
        except PSErrors.IntegrityError:
            await update.message.reply_text(STRINGS['double_moro'] % {'chat_title': chat})
    except PSErrors.IntegrityError as e:
        print('SQLite Error: ' + str(e))

    CON.commit()

moro_handler = CommandHandler(
    ['moro', 'hello'], hello, ~Filters.ChatType.PRIVATE)
