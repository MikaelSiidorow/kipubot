from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
import telegram.ext.filters as Filters
import psycopg.errors as PSErrors
from db import get_con
from errors import NoEntriesError, NoRaffleError
from utils import excel_to_graph

CON = get_con()


async def graph(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title

    base_path = f'data/{chat_id}/'

    excel_path = base_path + 'data.xlsx'
    graph_path = base_path + 'graph.png'

    try:
        excel_to_graph(excel_path, graph_path, chat_id, chat_title)

        with open(graph_path, 'rb') as f:
            await update.message.reply_photo(photo=f)

    except NoRaffleError:
        await update.message.reply_text(f'No raffle data found in {chat_title}!')
    except NoEntriesError:
        await update.message.reply_text(f'No raffle entries yet in {chat_title}!')
    except PSErrors.Error as e:
        print(e)
        await update.message.reply_text('Error getting raffle data from database!\n\n' +
                                        'Perhaps one is not setup yet for this chat? 🤔')
    except FileNotFoundError:
        await update.message.reply_text(f'No data found for {chat_title}!')

graph_handler = CommandHandler(
    ['kuvaaja', 'graph'], graph, ~Filters.ChatType.PRIVATE)
