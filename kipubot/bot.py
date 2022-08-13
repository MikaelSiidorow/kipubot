#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
from telegram.ext import ApplicationBuilder, PicklePersistence
from kipubot import BOT_TOKEN
from kipubot.handlers import (start_handler, moro_handler, excel_file_handler,
                              bot_added_handler, winner_handler, graph_handler,
                              expected_value_handler, raffle_setup_handler, no_dm_handler)


# -- SETUP --
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def main() -> None:
    if not os.path.exists('data'):
        #logging.info('No existing data...')
        os.mkdir('data')
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

    # test handler for all messages
    # app.add_handler(MessageHandler(Filters.ALL | Filters.Sticker.ALL, tester))

    app.run_polling()


if __name__ == "__main__":
    main()
