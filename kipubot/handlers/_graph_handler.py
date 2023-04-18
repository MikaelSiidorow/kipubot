import logging
from pathlib import Path

import psycopg.errors as pserrors
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, filters

from kipubot.constants import STRINGS
from kipubot.errors import NoEntriesError, NoRaffleError
from kipubot.utils import generate_expected, generate_graph

GRAPH_TYPE = {
    "expected": "expected",
    "odotusarvo": "expected",
    "graph": "graph",
    "kuvaaja": "graph",
}

_logger = logging.getLogger(__name__)


def get_graph_img(graph_type: str) -> str:
    if graph_type == "expected":
        return "expected.png"

    return "graph.png"


async def graph(
    update: Update,
    _context: ContextTypes.DEFAULT_TYPE,
) -> None:
    if (
        not update.effective_chat
        or not update.effective_user
        or not update.message
        or not update.message.text
    ):
        return

    chat_id = update.effective_chat.id
    chat_title = (
        update.effective_chat.title if update.effective_chat.title else "untitled chat"
    )
    graph_type_text = update.message.text[1::]
    graph_type = GRAPH_TYPE[graph_type_text]
    graph_path = f"data/{chat_id}/{get_graph_img(graph_type)}"

    try:
        if graph_type == "expected":
            generate_expected(graph_path, chat_id, chat_title)
        else:
            generate_graph(graph_path, chat_id, chat_title)

        with Path(graph_path).open("rb") as f:
            await update.message.reply_photo(photo=f)

    except NoRaffleError:
        await update.message.reply_text(
            STRINGS["no_raffle"] % {"chat_title": chat_title},
        )
    except NoEntriesError:
        await update.message.reply_text(
            STRINGS["no_entries"] % {"chat_title": chat_title},
        )
    except pserrors.Error:
        _logger.exception("psycopg error")
        await update.message.reply_text(STRINGS["raffle_db_error"])
    except FileNotFoundError:
        await update.message.reply_text(STRINGS["no_data"] % {"chat_title": chat_title})


graph_handler = CommandHandler(
    ["kuvaaja", "graph", "odotusarvo", "expected"],
    graph,
    ~filters.ChatType.PRIVATE,
)
