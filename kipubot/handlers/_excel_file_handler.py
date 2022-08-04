from typing import Union
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler
import telegram.ext.filters as Filters
from db import get_con
from constants import EXCEL_MIME, STRINGS

CON = get_con()


async def excel_file(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> Union[str, None]:
    user_id = update.effective_user.id

    query_result = (CON.execute('''SELECT c.chat_id, c.title
                        FROM chat AS c, in_chat AS i
                        WHERE i.user_id = %(id)s AND c.chat_id = i.chat_id
                            AND(c.cur_winner = %(id)s OR
                                c.prev_winner = %(id)s OR
                                c.admin = %(id)s)''',
                                {'id': user_id})
                    .fetchall())

    if len(query_result) == 0:
        await update.message.reply_text(STRINGS['not_winner'])
        return ConversationHandler.END

    doc = update.message.document

    chat_buttons = []

    for chat_id, chat_title in query_result:
        chat_buttons.append(InlineKeyboardButton(
            STRINGS['chat_button'] % {'chat_title': chat_title},
            callback_data=[chat_id, chat_title, doc]))

    keyboard = [
        chat_buttons,
        [InlineKeyboardButton(STRINGS['cancel_button'],
                              callback_data='cancel')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        STRINGS['choose_channel'], reply_markup=reply_markup)

excel_file_handler = MessageHandler(Filters.Document.MimeType(EXCEL_MIME) &
                                    Filters.ChatType.PRIVATE, excel_file)
