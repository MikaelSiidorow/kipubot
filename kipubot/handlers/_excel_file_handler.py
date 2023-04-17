import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters

from kipubot.constants import EXCEL_MIME, STRINGS
from kipubot.db import get_chats_where_winner
from kipubot.utils import validate_excel


async def excel_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if (
        not update.effective_chat
        or not update.effective_user
        or not update.message
        or not update.message.document
    ):
        return ConversationHandler.END

    user_id = update.effective_user.id
    dm_id = update.effective_chat.id

    chats = get_chats_where_winner(user_id)

    if len(chats) == 0:
        await update.message.reply_text(STRINGS["not_winner"])
        return ConversationHandler.END

    doc = update.message.document
    file = await context.bot.get_file(doc)
    base_path = f"data/{dm_id}"
    excel_path = base_path + "/data.xlsx"

    if not os.path.exists(base_path):
        os.mkdir(base_path)

    await file.download_to_drive(excel_path)

    if not validate_excel(excel_path):
        await update.message.reply_text(STRINGS["invalid_file"])
        os.remove(excel_path)
        return ConversationHandler.END

    chat_buttons = []

    for chat_id, chat_title in chats:
        chat_buttons.append(
            InlineKeyboardButton(
                STRINGS["chat_button"] % {"chat_title": chat_title},
                callback_data=f"raffle:chat_selected:{chat_id}:{chat_title}",
            )
        )

    keyboard = [
        chat_buttons,
        [InlineKeyboardButton(STRINGS["cancel_button"], callback_data="raffle:cancel")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        STRINGS["choose_channel"], reply_markup=reply_markup
    )

    return ConversationHandler.END


excel_file_handler = MessageHandler(
    filters.Document.MimeType(EXCEL_MIME) & filters.ChatType.PRIVATE, excel_file
)
