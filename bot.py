#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import sqlite3
import sys
from typing import Union
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from scipy import stats
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus, MessageEntityType
from telegram.ext import (ApplicationBuilder, CommandHandler,
                          ContextTypes, MessageHandler, ChatMemberHandler,
                          CallbackQueryHandler, ConversationHandler,
                          PicklePersistence)
from telegram.ext.filters import Document
import telegram.ext.filters as Filters
from telegram._files.document import Document as DocumentFile


# -- SETUP --
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN', default=None)
EXCEL_MIME = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

if BOT_TOKEN is None:
    print('Bot token not found')
    sys.exit(1)

print('Connecting to DB...')

con = sqlite3.connect('data/.db')
cur = con.cursor()

print('Connected!')

# -- FUNCTIONS --


async def start(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    with open('info.png', 'rb') as f:
        await update.message.reply_photo(
            caption='Use the given commands or send me an Excel-file ' +
                    'from MobilePay if you\'re the host of a raffle!', photo=f)


async def hello(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    username = update.effective_user.username
    chat = update.effective_chat.title

    try:
        cur.execute(f'''INSERT OR IGNORE INTO user(user_id, username)
                        VALUES ({user_id}, '{username}')''')

        try:
            cur.execute(f'''INSERT INTO in_chat(user_id, chat_id)
                            VALUES ({user_id}, {chat_id})''')
            await update.message.reply_text(f'Registered {username} in {chat}!')
        except sqlite3.IntegrityError:
            await update.message.reply_text(f'You are already registered in {chat}!')
    except sqlite3.IntegrityError as e:
        print('SQLite Error: ' + str(e))

    con.commit()


async def excel_file(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> Union[str, None]:
    user_id = update.effective_user.id

    query_result = (cur.execute(f'''SELECT c.chat_id, c.title
                        FROM chat AS c, in_chat AS i
                        WHERE i.user_id = {user_id} AND c.chat_id = i.chat_id
                            AND(c.cur_winner = {user_id} OR
                                c.prev_winner = {user_id} OR
                                c.admin = {user_id})''')
                    .fetchall())

    if len(query_result) == 0:
        await update.message.reply_text('You are not the winner in any chat! ❌')
        return ConversationHandler.END

    doc = update.message.document

    chat_buttons = []

    for chat_id, chat_title in query_result:
        chat_buttons.append(InlineKeyboardButton(
            '💬 ' + chat_title, callback_data=[chat_id, chat_title, doc]))

    keyboard = [
        chat_buttons,
        [InlineKeyboardButton('❌ Cancel', callback_data='cancel')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        'Choose channel:', reply_markup=reply_markup)


async def setup_raffle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Union[str, None]:
    query = update.callback_query
    # print('setup_raffle: ' + str(update))

    if query.data == 'cancel':
        await query.message.edit_text('Cancelled! ❌')
        context.user_data.clear()
        return ConversationHandler.END

    if (len(query.data) != 3 or not isinstance(query.data[0], int) or
            not isinstance(query.data[1], str) or
            not isinstance(query.data[2], DocumentFile)):
        await query.message.edit_text('Unknown error, please try again later! ❌')
        return ConversationHandler.END

    chat_id = query.data[0]
    chat_title = query.data[1]
    file = await context.bot.get_file(query.data[2])

    context.user_data['raffle_chat_id'] = chat_id
    context.user_data['raffle_chat_title'] = chat_title

    if not os.path.exists(f'data/{chat_id}'):
        os.mkdir(f'data/{chat_id}')

    with open(f'data/{chat_id}/data.xlsx', 'wb') as f:
        await file.download(out=f)

    raffle_data = (cur.execute(f'''SELECT *
                        FROM raffle
                        WHERE chat_id = {chat_id}''')
                   .fetchone())

    if raffle_data is not None:
        keyboard = [
            [InlineKeyboardButton(
                '🆕 Create a new raffle!', callback_data='raffle:new_raffle')],
            [InlineKeyboardButton(
                '🔄 Update existing raffle!', callback_data='raffle:use_existing')],
            [InlineKeyboardButton(
                '❌ Cancel!', callback_data='cancel')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.edit_text(f'Selected {chat_title}!\n' +
                                      'Found existing raffle.\n' +
                                      'Do you want update it or create a new one?')

        await query.message.edit_reply_markup(reply_markup)
    else:
        keyboard = [
            [InlineKeyboardButton(
                '🆕 Create a new raffle!', callback_data='raffle:new_raffle')],
            [InlineKeyboardButton(
                '❌ Cancel!', callback_data='cancel')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.edit_text(f'Selected {chat_title}! \n' +
                                      'No existing raffle found. ' +
                                      'Do you want to create a new one?')

        await query.message.edit_reply_markup(reply_markup)

    return 'ask_date'


async def ask_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Union[str, None]:
    query = update.callback_query
    # print('ask_date: ' + str(update))
    chat_title = context.user_data['raffle_chat_title']

    if query.data == 'cancel':
        await query.message.edit_text('Cancelled! ❌')
        context.user_data.clear()
        return ConversationHandler.END

    command = query.data.split(':')[1]

    if command == 'use_existing':
        await query.message.edit_text(f'Updated raffle data in {chat_title}! 🔄')
        context.user_data.clear()
        return ConversationHandler.END

    await query.message.edit_text('Send the start and end date of the raffle!\n\n' +
                                  'Format (start and end date on separate lines): \n' +
                                  'YYYY-MM-DD HH:MM\n' +
                                  'YYYY-MM-DD HH:MM\n\n' +
                                  '/cancel to cancel')

    return 'get_date'


async def invalid_date(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> Union[str, None]:
    # print('invalid_date: ' + str(update))

    await update.message.reply_text('Invalid date! ❌')

    return 'get_date'


async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    # print('get_date: ' + str(update))

    start_date, end_date = update.message.text.split("\n")

    context.user_data['raffle_start_date'] = start_date
    context.user_data['raffle_end_date'] = end_date

    keyboard = [
        [InlineKeyboardButton('#️⃣ Set fee', callback_data='fee:continue')],
        [InlineKeyboardButton('1️⃣ Use default (1€)',
                              callback_data='fee:default')],
        [InlineKeyboardButton('❌ Cancel', callback_data='cancel')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(f'Start date set to {start_date}!\n' +
                                    f'End date set to {end_date}!', reply_markup=reply_markup)

    return 'ask_fee'


async def ask_fee(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Union[str, None]:
    # print('ask_fee: ' + str(update))
    query = update.callback_query

    if query.data == 'cancel':
        await query.message.edit_text('Cancelled! ❌')
        context.user_data.clear()
        return ConversationHandler.END

    if query.data == 'fee:default':
        context.user_data['raffle_entry_fee'] = 100
        keyboard = [
            [InlineKeyboardButton('✔️ Finish raffle', callback_data='finish')],
            [InlineKeyboardButton('❌ Cancel', callback_data='cancel')]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.edit_text('Fee set to 1€!', reply_markup=reply_markup)

        return 'finish_setup'

    await query.message.edit_text('Send the entry fee to the raffle!\n\n' +
                                  'Example inputs: \n' +
                                  '0.50, 1.5, 2\n\n' +
                                  '/cancel to cancel')

    return 'get_fee'


async def invalid_fee(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> str:
    await update.message.reply_text('Invalid fee! ❌')

    # print('invalid_fee: ' + str(update))

    return 'get_fee'


async def get_fee(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    # print('get_fee: ' + str(update))

    fee = update.message.text
    context.user_data['raffle_entry_fee'] = int(float(fee) * 100)

    keyboard = [
        [InlineKeyboardButton('✔️ Finish raffle', callback_data='finish')],
        [InlineKeyboardButton('❌ Cancel', callback_data='cancel')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(f'Fee set to {fee}€!', reply_markup=reply_markup)

    return 'finish_setup'


async def finish_setup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Union[str, None]:
    # print('finish_setup: ' + str(update))
    query = update.callback_query

    if query.data == 'cancel':
        await query.message.edit_text('Cancelled! ❌')
        context.user_data.clear()
        return ConversationHandler.END

    chat_title = context.user_data['raffle_chat_title']
    chat_id = context.user_data['raffle_chat_id']
    start_date = context.user_data['raffle_start_date'] + ':00'
    end_date = context.user_data['raffle_end_date'] + ':00'
    entry_fee = context.user_data['raffle_entry_fee']
    # print(chat_id, start_date, end_date, entry_fee)

    cur.execute(f'''INSERT OR REPLACE INTO raffle(chat_id, start_date, end_date, entry_fee)
                    VALUES ({chat_id}, "{start_date}", "{end_date}", {entry_fee})''')
    con.commit()

    await query.message.edit_text(f'New raffle setup in {chat_title}! ✔️')

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()
    await update.message.reply_text('Cancelled! ❌')
    return ConversationHandler.END


async def timeout(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    # print('timeout: ' + str(update))
    query = update.callback_query
    await query.message.edit_text('Timed out! 🕐')


async def graph(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    # https://apmonitor.com/che263/index.php/Main/PythonRegressionStatistics
    # https://medium.com/python-data-analysis/linear-regression-on-time-series-data-like-stock-price-514a42d5ac8a
    # https://www.mathworks.com/help/stats/linearmodel.predict.html
    # https://stackoverflow.com/questions/27164114/show-confidence-limits-and-prediction-limits-in-scatter-plot
    # http://www.xavierdupre.fr/app/mlinsights/helpsphinx/notebooks/regression_confidence_interval.html
    # https://gist.github.com/riccardoscalco/5356167
    # https://pythonguides.com/scipy-confidence-interval/
    # https://www.graphpad.com/guides/prism/6/statistics/confidence_intervals2.htm

    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title

    base_path = f'data/{chat_id}/'

    excel_path = base_path + 'data.xlsx'
    graph_path = base_path + 'graph.png'

    try:
        query_result = (
            cur.execute(
                f'SELECT * FROM raffle WHERE chat_id = {chat_id}')
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

    except sqlite3.Error as e:
        print(e)
        await update.message.reply_text('Error getting raffle data from database!\n\n' +
                                        'Perhaps one is not setup yet for this chat? 🤔')

    except FileNotFoundError:
        await update.message.reply_text(f'No data found for {chat_title}!')


async def bot_added(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # when bot is added to channel:
    # -> add the channel to a database
    # -> set the adder as the current winner of the channel
    # -> also set the adder as an admin (can update winner always)

    if update.my_chat_member.new_chat_member.status != ChatMemberStatus.LEFT:
        chat_id = update.effective_chat.id
        title = update.effective_chat.title
        user_id = update.effective_user.id
        username = update.effective_user.username

        try:
            cur.execute(f'''INSERT OR IGNORE INTO chat(chat_id, title, admin)
                            VALUES ({chat_id}, "{title}", {user_id})''')
            cur.execute(f'''INSERT OR IGNORE INTO user(user_id, username)
                            VALUES ({user_id}, '{username}')''')
            cur.execute(f'''INSERT OR IGNORE INTO in_chat(user_id, chat_id)
                            VALUES ({user_id}, {chat_id})''')
            con.commit()
        except sqlite3.IntegrityError as e:
            print('SQLite Error: ' + str(e))

        # Kiitos pääsystä! -stigu
        await context.bot.send_sticker(
            chat_id=chat_id,
            sticker='CAACAgQAAxkBAAIBPmLicTHP2Xv8IcFzxHYocjLRFBvQAAI5AAMcLHsXd9jLHwYNcSEpBA')
        await update.message.reply_text(f'Join the raffles in {title} by typing /moro or /hello!')


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
                cur.execute(
                    f'''SELECT admin
                        FROM chat
                        WHERE admin = {user_id}''').fetchone())
            is_winner = (
                cur.execute(
                    f'''SELECT prev_winner
                        FROM chat
                        WHERE prev_winner = {user_id} OR
                                cur_winner = {user_id}''').fetchone())

            if not is_admin and not is_winner:
                await update.message.reply_text('You are not allowed to use this command!')
                return
            winner_id = (
                cur.execute(
                    '''SELECT user.user_id, user.username
                    FROM user, in_chat
                    WHERE chat_id = ?
                        AND user.user_id = in_chat.user_id
                        AND username = ?''',
                    (chat_id, username)).fetchone())
            if not winner_id:
                await update.message.reply_text('Error getting user!\n' +
                                                'Perhaps they haven\'t /moro ed? 🤔')
                return

            if winner_id[0] == user_id and not is_admin:
                await update.message.reply_text('You are already the winner!')
                return

            if is_admin:
                cur.execute(f'''UPDATE chat
                                SET prev_winner=cur_winner,
                                    cur_winner={winner_id[0]}
                                WHERE chat_id={chat_id}''')
            else:
                cur.execute(f'''UPDATE chat
                                SET prev_winner={user_id},
                                    cur_winner={winner_id[0]}'
                                WHERE chat_id={chat_id}''')
        except sqlite3.Error as e:
            print(e)
            await update.message.reply_text('Error getting user!\n' +
                                            'Perhaps they haven\' /moro ed? 🤔')
    con.commit()
    await update.message.reply_text(f'{username} is the new winner!')


async def chat_only(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('This command is not usable in private messages!')


async def tester(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    print('all handler: ' + str(update))


# -- MAIN --
def main() -> None:
    persistence = PicklePersistence(filepath='data/.pkl')
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .persistence(persistence)
        .arbitrary_callback_data(True)
        .build()
    )

    app.add_handler(CommandHandler('start', start))

    # added to channel
    app.add_handler(ChatMemberHandler(bot_added, -1))

    # base commands
    app.add_handler(CommandHandler(
        ['moro', 'hello'], hello, ~Filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler(
        ['kuvaaja', 'graph'], graph, ~Filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler(
        ['voittaja', 'winner'], winner, ~Filters.ChatType.PRIVATE))

    # warning about using a command in a private chat
    app.add_handler(CommandHandler(
        ['moro', 'hello', 'kuvaaja', 'graph', 'voittaja', 'winner'],
        chat_only, Filters.ChatType.PRIVATE))

    # YYYY-MM-DD HH:mm regex
    two_line_date_filter = Filters.Regex(
        r'^(\d{4})-(0[1-9]|1[0-2])-(0[1-9]|[1-2]\d|3[0-2])\s([0-1]\d|2[0-3]):([0-5]\d)\n' +
        r'(\d{4})-(0[1-9]|1[0-2])-(0[1-9]|[1-2]\d|3[0-2])\s([0-1]\d|2[0-3]):([0-5]\d)$')

    price_filter = Filters.Regex(r'^(([1-9]\d|[1-9])(.\d)?)|(0.[1-9]\d?)$')

    # sending excel file in private chat
    app.add_handler(MessageHandler(Document.MimeType(EXCEL_MIME) &
                                   Filters.ChatType.PRIVATE, excel_file))

    # start conversation after selecting channel from excel file
    app.add_handler(ConversationHandler(
        entry_points=[CallbackQueryHandler(setup_raffle)],
        states={
            'ask_date': [CallbackQueryHandler(ask_date)],
            'get_date': [
                MessageHandler(two_line_date_filter, get_date),
                MessageHandler(Filters.ALL & ~Filters.COMMAND, invalid_date),
                CommandHandler('cancel', cancel)
            ],
            'ask_fee': [CallbackQueryHandler(ask_fee)],
            'get_fee': [
                MessageHandler(price_filter, get_fee),
                MessageHandler(Filters.ALL & ~Filters.COMMAND, invalid_fee),
                CommandHandler('cancel', cancel)
            ],
            'finish_setup': [CallbackQueryHandler(finish_setup)],
            ConversationHandler.TIMEOUT: [CallbackQueryHandler(timeout)]
        },
        fallbacks=[CallbackQueryHandler(setup_raffle)],
        conversation_timeout=120
    ))

    # test handler for all messages
    # app.add_handler(MessageHandler(Filters.ALL | Filters.Sticker.ALL, tester))

    app.run_polling()


if __name__ == '__main__':
    main()
