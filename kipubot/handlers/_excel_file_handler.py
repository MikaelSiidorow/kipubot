from typing import Union
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler
import telegram.ext.filters as Filters
from db import get_con
from constants import EXCEL_MIME, STRINGS
from utils import get_chats_where_winner

CON = get_con()


async def excel_file(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> Union[str, None]:
    user_id = update.effective_user.id

    chats = get_chats_where_winner(user_id)

    if len(chats) == 0:
        await update.message.reply_text(STRINGS['not_winner'])
        return ConversationHandler.END

    doc = update.message.document

    chat_buttons = []

    for chat_id, chat_title in chats:
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
