import os
from typing import Union
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler
import telegram.ext.filters as Filters
from db import get_con
from constants import EXCEL_MIME, STRINGS
from utils import get_chats_where_winner, validate_excel

CON = get_con()


async def excel_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Union[str, None]:
    user_id = update.effective_user.id
    dm_id = update.effective_chat.id

    chats = get_chats_where_winner(user_id)

    if len(chats) == 0:
        await update.message.reply_text(STRINGS['not_winner'])
        return ConversationHandler.END

    doc = update.message.document
    file = await context.bot.get_file(doc)
    base_path = f'data/{dm_id}'
    excel_path = base_path + '/data.xslx'

    if not os.path.exists(base_path):
        os.mkdir(base_path)

    with open(excel_path, 'wb') as f:
        await file.download(out=f)

    if not validate_excel(excel_path):
        await update.message.reply_text(STRINGS['invalid_file'])
        return

    chat_buttons = []

    for chat_id, chat_title in chats:
        chat_buttons.append(InlineKeyboardButton(
            STRINGS['chat_button'] % {'chat_title': chat_title},
            callback_data=[chat_id, chat_title]))

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
