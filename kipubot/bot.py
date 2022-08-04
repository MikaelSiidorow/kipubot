#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
import psycopg
from scipy import stats
from config import BOT_TOKEN
from telegram import Update
from telegram.constants import MessageEntityType
from telegram.ext import (ApplicationBuilder, CommandHandler,
                          ContextTypes, PicklePersistence)
import telegram.ext.filters as Filters
from db import get_con
from handlers import (start_handler, moro_handler, excel_file_handler,
                      bot_added_handler, raffle_setup_handler)


# -- SETUP --
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

CON = get_con()

# -- FUNCTIONS --


async def graph(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title

    base_path = f'data/{chat_id}/'

    excel_path = base_path + 'data.xlsx'
    graph_path = base_path + 'graph.png'

    try:
        query_result = (
            CON.execute('SELECT * FROM raffle WHERE chat_id = %s', (chat_id,))
            .fetchone())

        if not query_result:
            await update.message.reply_text(f'No raffle data found in {chat_title}!')
            return

        _, start_str, end_str, _entry_fee = query_result

        start_date = pd.to_datetime(start_str)
        end_date = pd.to_datetime(end_str)
        _days = (end_date - start_date).days

        df = pd.read_excel(excel_path, usecols='A,D', header=None, names=[
            'date', 'amount'], parse_dates=True)

        df.drop(df[df['amount'] <= 0].index, inplace=True)
        df.drop(df[df['date'] > end_date].index, inplace=True)
        df.drop(df[df['date'] < start_date].index, inplace=True)

        df['datenum'] = pd.to_numeric(df['date']) // 1_000_000_000

        df.set_index('date', inplace=True)

        df = df.iloc[::-1]

        df['amount'] = df['amount'].cumsum()

        y = df['amount'].values
        x = df['datenum'].values

        if not df.size > 0:
            await update.message.reply_text(f'No raffle entries yet in {chat_title}!')
            return

        slope, intercept, _r, _p, sterr = stats.linregress(x, y)

        df['y_pred'] = slope * x + intercept

        n = len(x)
        t = stats.t.ppf(0.975, n-2)
        pi = t * sterr * np.sqrt(1 + 1/n +
                                 (x-x.mean())**2/sum((x-x.mean())**2))

        df['max_pred'] = df['y_pred'] + pi * 1e3
        df['min_pred'] = df['y_pred'] - pi * 1e3

        _fig, ax = plt.subplots()

        df['amount'].plot(ax=ax, style='xr')
        df['y_pred'].plot(ax=ax, color='orange')
        df['min_pred'].plot(ax=ax, style='--b')
        df['max_pred'].plot(ax=ax, style='--b')

        plt.xlim((pd.to_datetime(start_date), pd.to_datetime(end_date)))
        total = df['amount'].max()
        plt.title(f'{chat_title} -- Pool {total}€')
        plt.xlabel('Time')
        plt.ylabel('Pool (€)')
        # plt.xticks(np.linspace(start_date.toordinal(),
        #           end_date.toordinal(), days*6+1))
        # plt.ticklabel_format({},axis='x')
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m. %H:%M'))

        ax.grid(visible=True, which='minor',
                axis='both', linestyle='--', linewidth=1)
        # plt.tick_params(axis='x', which='both', length=0)
        # plt.tick_params(axis='y', which='both', length=0)
        # plt.setxticks(pd.to_datetime(start_date), pd.to_datetime(end_date))
        # plt.setyticks(np.arange(0, total, 100))
        ax.legend(['Data', 'Linear Fit', 'Confidence Intervals'])

        plt.savefig(graph_path)

        with open(graph_path, 'rb') as f:
            await update.message.reply_photo(photo=f)

    except psycopg.errors.Error as e:
        print(e)
        await update.message.reply_text('Error getting raffle data from database!\n\n' +
                                        'Perhaps one is not setup yet for this chat? 🤔')

    except FileNotFoundError:
        await update.message.reply_text(f'No data found for {chat_title}!')


async def winner(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    # only usable by admin, previous winner (in case of typos) and current winner
    # usage: /winner @username
    # -> set the winner to the given username

    ent = update.message.entities
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if len(ent) != 2 or ent[1].type != MessageEntityType.MENTION:
        await update.message.reply_text('Please use the format /winner @username')

    else:
        username = update.message.text.split(" ")[1][1:]

        try:
            is_admin = (
                CON.execute('''SELECT admin
                               FROM chat
                               WHERE admin = %s''',
                            (user_id,))
                .fetchone())
            is_winner = (
                CON.execute('''SELECT prev_winner
                               FROM chat
                               WHERE prev_winner = %(id)s OR
                                cur_winner = %(id)s''',
                            {'id': user_id})
                .fetchone())

            if not is_admin and not is_winner:
                await update.message.reply_text('You are not allowed to use this command!')
                return
            winner_id = (
                CON.execute(
                    '''SELECT chat_user.user_id, chat_user.username
                    FROM chat_user, in_chat
                    WHERE chat_id = %s
                        AND chat_user.user_id = in_chat.user_id
                        AND username = %s''',
                    (chat_id, username)).fetchone())
            if not winner_id:
                await update.message.reply_text('Error getting user!\n' +
                                                'Perhaps they haven\'t /moro ed? 🤔')
                return

            if winner_id[0] == user_id and not is_admin:
                await update.message.reply_text('You are already the winner!')
                return

            if is_admin:
                CON.execute('''UPDATE chat
                                SET prev_winner=cur_winner,
                                    cur_winner=%s
                                WHERE chat_id=%s''',
                            (winner_id[0], chat_id))
            else:
                CON.execute('''UPDATE chat
                                SET prev_winner=%s,
                                    cur_winner=%s'
                                WHERE chat_id=%s''',
                            (user_id, winner_id[0], chat_id))
        except psycopg.errors.Error as e:
            print(e)
            await update.message.reply_text('Error getting user!\n' +
                                            'Perhaps they haven\' /moro ed? 🤔')
            return
    CON.commit()
    await update.message.reply_text(f'{username} is the new winner!')


async def chat_only(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('This command is not usable in private messages!')


async def tester(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    print('all handler: ' + str(update))


# -- MAIN --
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
    app.add_handler(CommandHandler(
        ['kuvaaja', 'graph'], graph, ~Filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler(
        ['voittaja', 'winner'], winner, ~Filters.ChatType.PRIVATE))

    # warning about using a command in a private chat
    app.add_handler(CommandHandler(
        ['moro', 'hello', 'kuvaaja', 'graph', 'voittaja', 'winner'],
        chat_only, Filters.ChatType.PRIVATE))

    # sending excel file in private chat
    app.add_handler(excel_file_handler)

    # start conversation after selecting channel from excel file
    app.add_handler(raffle_setup_handler)

    # test handler for all messages
    # app.add_handler(MessageHandler(Filters.ALL | Filters.Sticker.ALL, tester))

    app.run_polling()


if __name__ == "__main__":
    main()
