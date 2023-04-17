from enum import Enum

import psycopg.errors as pserrors
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, filters

from kipubot.constants import STRINGS
from kipubot.errors import NoEntriesError, NoRaffleError
from kipubot.utils import generate_expected, generate_graph


class GraphType(Enum):
    EXPECTED = "expected"
    GRAPH = "graph"


def get_graph_img(graph_type: GraphType) -> str:
    if graph_type == GraphType.EXPECTED:
        return "expected.png"

    return "graph.png"


async def graph(
    update: Update,
    _context: ContextTypes.DEFAULT_TYPE,
    graph_type: GraphType = GraphType.GRAPH,
) -> None:
    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title
    graph_path = f"data/{chat_id}/{get_graph_img(graph_type)}"

    try:
        if graph_type == GraphType.EXPECTED:
            generate_expected(graph_path, chat_id, chat_title)
        else:
            generate_graph(graph_path, chat_id, chat_title)

        with open(graph_path, "rb") as f:
            await update.message.reply_photo(photo=f)

    except NoRaffleError:
        await update.message.reply_text(
            STRINGS["no_raffle"] % {"chat_title": chat_title}
        )
    except NoEntriesError:
        await update.message.reply_text(
            STRINGS["no_entries"] % {"chat_title": chat_title}
        )
    except pserrors.Error as e:
        print(e)
        await update.message.reply_text(STRINGS["raffle_db_error"])
    except FileNotFoundError:
        await update.message.reply_text(STRINGS["no_data"] % {"chat_title": chat_title})


graph_handler = CommandHandler(["kuvaaja", "graph"], graph, ~filters.ChatType.PRIVATE)

expected_value_handler = CommandHandler(
    ["odotusarvo", "expected"],
    lambda u, c: graph(u, c, graph_type=GraphType.EXPECTED),
    ~filters.ChatType.PRIVATE,
)
