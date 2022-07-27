import os
import logging
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import datetime as dt
import scipy.stats as sp
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler
from telegram.ext.filters import Document

# -- SETUP --
logging.basicConfig(
  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
  level=logging.INFO
)

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN', default=None)

if (BOT_TOKEN == None):
  print('Bot token not found')
  exit(1)

# -- FUNCTIONS --
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

async def download(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  file = await context.bot.get_file(update.message.document)

  with open('test.xlsx', 'wb') as f:
    await file.download(out=f)

async def graph(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
  df = pd.read_excel('test.xlsx', usecols='A,D', header=None, names=['date', 'amount'], parse_dates=True)
  df.set_index('date', inplace=True)
  df = df.iloc[::-1]
  df['amount'] = df['amount'].cumsum()

  df['amount'].plot()

  plt.xlabel(None)
  plt.ylabel('Amount (€)')
  plt.savefig('test.png')
  
  with open('test.png', 'rb') as f:
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=f)

# -- MAIN --
if __name__ == '__main__':
  app = ApplicationBuilder().token(BOT_TOKEN).build()

  app.add_handler(CommandHandler('start', start))
  app.add_handler(MessageHandler(Document.MimeType('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'), download))
  app.add_handler(CommandHandler('graph', graph))

  app.run_polling()