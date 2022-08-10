from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
import telegram.ext.filters as Filters
import psycopg.errors as PSErrors
from errors import NoEntriesError, NoRaffleError
from utils import generate_expected
from constants import STRINGS


async def expected(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title
    graph_path = f'data/{chat_id}/expected.png'

    try:
        generate_expected(graph_path, chat_id, chat_title)

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

expected_value_handler = CommandHandler(
    ['odotusarvo', 'expected'], expected, ~Filters.ChatType.PRIVATE)
