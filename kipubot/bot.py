#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram.ext import ApplicationBuilder, PicklePersistence
from kipubot import BOT_TOKEN
from kipubot.handlers import (start_handler, moro_handler, excel_file_handler,
                              bot_added_handler, winner_handler, graph_handler,
                              expected_value_handler, raffle_setup_handler, no_dm_handler,
                              error_handler)


def main() -> None:
    persistence = PicklePersistence(filepath='data/.pkl')
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .persistence(persistence)
        .arbitrary_callback_data(True)
        .build()
    )

    app.add_handler(start_handler)

    # added to channel
    app.add_handler(bot_added_handler)

    # base commands
    app.add_handler(moro_handler)
    app.add_handler(graph_handler)
    app.add_handler(winner_handler)
    app.add_handler(expected_value_handler)

    # warning about using a command in a private chat
    app.add_handler(no_dm_handler)

    # sending excel file in private chat
    app.add_handler(excel_file_handler)

    # start conversation after selecting channel from excel file
    app.add_handler(raffle_setup_handler)

    # add error handler
    app.add_error_handler(error_handler)

    app.run_polling()
