#!/usr/bin/env python3

"""Main kipubot file for running the bot."""

from telegram.ext import ApplicationBuilder, PicklePersistence

from kipubot import config
from kipubot.db import init_db
from kipubot.handlers import (
    bot_added_handler,
    error_handler,
    excel_file_handler,
    graph_handler,
    moro_handler,
    no_dm_handler,
    raffle_setup_handler,
    start_handler,
    winner_handler,
)


def main() -> None:
    """Run the bot with all handlers."""
    # INITIALIZE DB AND CREATE TABLES IF THEY DON'T EXIST
    init_db()
    persistence = PicklePersistence(filepath="data/.pkl")
    app = ApplicationBuilder().token(config.BOT_TOKEN).persistence(persistence).build()

    app.add_handler(start_handler)

    # added to channel
    app.add_handler(bot_added_handler)

    # base commands
    app.add_handler(moro_handler)
    app.add_handler(graph_handler)
    app.add_handler(winner_handler)

    # warning about using a command in a private chat
    app.add_handler(no_dm_handler)

    # sending excel file in private chat
    app.add_handler(excel_file_handler)

    # start conversation after selecting channel from excel file
    app.add_handler(raffle_setup_handler)

    # add error handler
    app.add_error_handler(error_handler)

    app.run_polling()
