import os
import logging
import sqlite3
import sys
import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus, MessageEntityType
from telegram.ext import ApplicationBuilder, CommandHandler, \
    ContextTypes, MessageHandler, ChatMemberHandler, CallbackQueryHandler
from telegram.ext.filters import Document
import telegram.ext.filters as Filters

# -- SETUP --
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN', default=None)

if BOT_TOKEN is None:
    print('Bot token not found')
    sys.exit(1)

print('Connecting to DB...')

con = sqlite3.connect('data/.db')
cur = con.cursor()

print('Connected!')

# -- FUNCTIONS --


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="I'm a bot, please talk to me!")


async def hello(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    username = update.effective_user.username
    chat = update.effective_chat.title

    try:
        cur.execute(f'''INSERT OR IGNORE INTO users(user_id, username)
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


async def excel_file(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id

    query_result = \
        cur.execute(f'''SELECT c.chat_id, c.title
                        FROM chats AS c, in_chat AS i
                        WHERE i.user_id = {user_id} AND c.chat_id = i.chat_id''') \
        .fetchall()

    if len(query_result) == 0:
        await update.message.reply_text('You are not the winner in any chat!')

    else:
        doc = update.message.document

        chat_buttons = []

        for chat_id, chat_title in query_result:
            chat_buttons.append(InlineKeyboardButton(
                chat_title, callback_data=[chat_id, chat_title, doc]))

        keyboard = [
            chat_buttons,
            [InlineKeyboardButton('Cancel', callback_data='cancel_update')]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            'Choose channel:', reply_markup=reply_markup)


async def update_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    print(update)

    await query.answer()

    if query.data == 'cancel_update':
        await query.message.edit_text('Cancelled!')
    else:
        chat_id = query.data[0]
        chat_title = query.data[1]
        file = await context.bot.get_file(query.data[2])

        if not os.path.exists(f'data/{chat_id}'):
            os.mkdir(f'data/{chat_id}')

        with open(f'data/{chat_id}/data.xlsx', 'wb') as f:
            await file.download(out=f)

        await query.message.edit_text(f'Updated data in {chat_title}!')


async def graph(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    chat_title = update.effective_chat.title

    base_path = f'data/{chat_id}/'

    excel_path = base_path + 'data.xlsx'
    graph_path = base_path + 'graph.png'

    try:
        df = pd.read_excel(excel_path, usecols='A,D', header=None, names=[
            'date', 'amount'], parse_dates=True)
        df.set_index('date', inplace=True)
        df = df.iloc[::-1]
        df['amount'] = df['amount'].cumsum()

        df['amount'].plot()

        plt.title(f'{chat_title} stonks')
        plt.xlabel(None)
        plt.ylabel('Amount (€)')
        plt.savefig(graph_path)

        with open(graph_path, 'rb') as f:
            await update.message.reply_photo(photo=f)
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
            cur.execute(f'''INSERT OR IGNORE INTO chats(chat_id, title, admin)
                            VALUES ({chat_id}, "{title}", {user_id})''')
            cur.execute(f'''INSERT OR IGNORE INTO users(user_id, username)
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


async def winner(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    # only usable by admin, previous winner (in case of typos) and current winner
    # usage: /winner @username
    # -> set the winner to the given username

    ent = update.message.entities

    if len(ent) != 2 or ent[1].type != MessageEntityType.MENTION:
        await update.message.reply_text('Please use the format /winner @username')

        return

    _winner = update.message.text.split(" ")[1]

    print('winner:' + str(update))


async def tester(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    print('all handler: ' + str(update))
    print()

# -- MAIN --
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).arbitrary_callback_data(True).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler(['moro', 'hello'], hello))
    app.add_handler(MessageHandler(Document.MimeType(
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'), excel_file))
    app.add_handler(CallbackQueryHandler(update_chat))
    app.add_handler(CommandHandler(
        ['kuvaaja', 'graph'], graph, ~Filters.ChatType.PRIVATE))
    app.add_handler(ChatMemberHandler(bot_added, -1))
    app.add_handler(CommandHandler(
        ['voittaja', 'winner'], winner, ~Filters.ChatType.PRIVATE))
    app.add_handler(MessageHandler(Filters.ALL | Filters.Sticker.ALL, tester))

    app.run_polling()
