from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, ConversationHandler
from telegram.ext import filters as Filters
import psycopg.errors as PSErrors
from errors import NoEntriesError, NoRaffleError
from utils import generate_graph
from db import get_con
from constants import STRINGS

CON = get_con()


async def graph_helper(update: Update, graph_path, chat_id, chat_title) -> None:
    try:
        generate_graph(graph_path, chat_id, chat_title)

        with open(graph_path, 'rb') as f:
            await update.message.reply_photo(photo=f)
    except NoRaffleError:
        await update.message.reply_text(STRINGS['no_raffle'] % {'chat_title': chat_title})
    except NoEntriesError:
        await update.message.reply_text(STRINGS['no_entries'] % {'chat_title': chat_title})
    except PSErrors.Error as e:
        print(e)
        await update.message.reply_text(STRINGS['raffle_db_error'])
    except FileNotFoundError:
        await update.message.reply_text(STRINGS['no_data'] % {'chat_title': chat_title})


async def graph(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title
    graph_path = f'data/{chat_id}/graph.png'
    await graph_helper(update, graph_path, chat_id, chat_title)

graph_handler = CommandHandler(
    ['kuvaaja', 'graph'], graph, ~Filters.ChatType.PRIVATE)


async def graph_dm(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    query_result = CON.execute(
        f'SELECT R.chat_id,chat.title FROM in_chat AS C JOIN raffle as R ON C.chat_id=R.chat_id JOIN chat ON chat.chat_id=R.chat_id WHERE C.user_id={update.effective_user.id}').fetchall()
    print(query_result)
    chat_buttons = []
    for chat_id, chat_title in query_result:
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


async def dm_callback(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    print(query.data)

    return ConversationHandler.END
graph_handler_dm = CommandHandler(
    ['kuvaaja', 'graph'], graph_dm, Filters.ChatType.PRIVATE)
graph_handler_dm_cb = CallbackQueryHandler(dm_callback)
