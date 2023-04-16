from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from kipubot.constants import STRINGS


async def start(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    with open("kipubot/resources/info.png", "rb") as f:
        await update.message.reply_photo(caption=STRINGS["start_prompt"], photo=f)


start_handler = CommandHandler("start", start)
