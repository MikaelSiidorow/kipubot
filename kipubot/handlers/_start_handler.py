from telegram import Update
from telegram.ext import ContextTypes, CommandHandler


async def start(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    with open('kipubot/resources/info.png', 'rb') as f:
        await update.message.reply_photo(
            caption='Use the given commands or send me an Excel-file ' +
                    'from MobilePay if you\'re the host of a raffle!', photo=f)

start_handler = CommandHandler('start', start)
