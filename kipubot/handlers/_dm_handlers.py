from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler
import telegram.ext.filters as Filters
from constants import STRINGS
from db import get_con
from ._graph_handlers import GraphType


CON = get_con()


async def ask_chat(update: Update, _context: ContextTypes.DEFAULT_TYPE,
                   graph_type: GraphType = None) -> None:
    query_result = CON.execute(
        f'SELECT R.chat_id,chat.title FROM in_chat AS C \
            JOIN raffle as R ON C.chat_id=R.chat_id JOIN\
            chat ON chat.chat_id=R.chat_id\
            WHERE C.user_id={update.effective_user.id}').fetchall()
    print(query_result)
    chat_buttons = []
    for chat_id, chat_title in query_result:
        chat_buttons.append(InlineKeyboardButton(
            STRINGS['chat_button'] % {'chat_title': chat_title},
            callback_data=[chat_id, chat_title, graph_type]))
    keyboard = [
        chat_buttons,
        [InlineKeyboardButton(STRINGS['cancel_button'],
                              callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        STRINGS['choose_channel'], reply_markup=reply_markup)

graph_handler_dm = CommandHandler(
    ['kuvaaja', 'graph'], lambda u, c: ask_chat(
        u, c, graph_type=GraphType.GRAPH),
    Filters.ChatType.PRIVATE)

expected_value_handler_dm = CommandHandler(
    ['odotusarvo', 'expected'],
    lambda u, c: ask_chat(u, c, graph_type=GraphType.EXPECTED),
    Filters.ChatType.PRIVATE)
