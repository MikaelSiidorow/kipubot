import os
import logging
import sqlite3
import sys
import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatMemberStatus, MessageEntityType
from telegram.ext import ApplicationBuilder, CommandHandler, \
    ContextTypes, MessageHandler, ChatMemberHandler
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


async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
            await context.bot.send_message(
                chat_id=chat_id,
                text=f'Registered {username} in {chat}!')
        except sqlite3.IntegrityError:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f'You are already registered in {chat}!'
            )
    except sqlite3.IntegrityError as e:
        print('SQLite Error: ' + str(e))

    con.commit()


async def download(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    file = await context.bot.get_file(update.message.document)

    with open('test.xlsx', 'wb') as f:
        await file.download(out=f)


async def graph(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    df = pd.read_excel('test.xlsx', usecols='A,D', header=None, names=[
                       'date', 'amount'], parse_dates=True)
    df.set_index('date', inplace=True)
    df = df.iloc[::-1]
    df['amount'] = df['amount'].cumsum()

    df['amount'].plot()

    plt.xlabel(None)
    plt.ylabel('Amount (€)')
    plt.savefig('test.png')

    with open('test.png', 'rb') as f:
        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=f)


async def bot_added(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # when bot is added to channel:
    # -> add the channel to a database
    # -> set the adder as the current winner of the channel
    # -> also set the adder as an admin (can update winner always)

    if update.my_chat_member.new_chat_member.status != ChatMemberStatus.LEFT:
        chat_id = update.effective_chat.id
        admin = update.effective_user.id

        try:
            cur.execute(f'''INSERT OR IGNORE INTO chats(chat_id, admin)
                      VALUES ({chat_id}, {admin})''')
            cur.execute(f'''INSERT OR IGNORE INTO users(user_id, username)
                      VALUES ({admin}, '{update.effective_user.username}')''')
            cur.execute(f'''INSERT OR IGNORE INTO in_chat(user_id, chat_id)
                      VALUES ({admin}, {chat_id})''')
            con.commit()
        except sqlite3.IntegrityError as e:
            print('SQLite Error: ' + str(e))

        # Kiitos pääsystä! -stigu
        await context.bot.send_sticker(
            chat_id=chat_id,
            sticker='CAACAgQAAxkBAAIBPmLicTHP2Xv8IcFzxHYocjLRFBvQAAI5AAMcLHsXd9jLHwYNcSEpBA')


async def winner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # only usable by admin, previous winner (in case of typos) and current winner
    # usage: /winner @username
    # -> set the winner to the given username

    ent = update.message.entities

    if len(ent) != 2 or ent[1].type != MessageEntityType.MENTION:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text='Please use the format /winner @username')

        return

    _winner = update.message.text.split(" ")[1]

    print('winner:' + str(update))


async def tester(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    print('all handler: ' + str(update))
    print()

# -- MAIN --
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler(['moro', 'hello'], hello))
    app.add_handler(MessageHandler(Document.MimeType(
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'), download))
    app.add_handler(CommandHandler('graph', graph))
    app.add_handler(ChatMemberHandler(bot_added, -1))
    app.add_handler(CommandHandler(
        'winner', winner, ~Filters.ChatType.PRIVATE))
    #app.add_handler(MessageHandler(Filters.ALL | Filters.Sticker.ALL, tester))

    app.run_polling()
