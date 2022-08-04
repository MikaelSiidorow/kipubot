from telegram import Update
from telegram.ext import ContextTypes, ChatMemberHandler
from telegram.constants import ChatMemberStatus
import psycopg.errors as PSErrors
from db import get_con

CON = get_con()


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
            CON.execute('''INSERT INTO chat (chat_id, title, admin)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (chat_id)
                            DO NOTHING''',
                        (chat_id, title, user_id))
            CON.execute('''INSERT INTO chat_user (user_id, username)
                            VALUES (%s, %s)
                            ON CONFLICT (user_id)
                            DO NOTHING''',
                        (user_id, username))
            CON.execute('''INSERT INTO in_chat (user_id, chat_id)
                            VALUES (%s, %s)
                            ON CONFLICT (user_id, chat_id)
                            DO NOTHING''',
                        (user_id, chat_id))
            CON.commit()
        except PSErrors.IntegrityError as e:
            print('SQLite Error: ' + str(e))

        # Kiitos pääsystä! -stigu
        await context.bot.send_sticker(
            chat_id=chat_id,
            sticker='CAACAgQAAxkBAAIBPmLicTHP2Xv8IcFzxHYocjLRFBvQAAI5AAMcLHsXd9jLHwYNcSEpBA')
        await context.bot.send_message(
            chat_id=chat_id,
            text=f'Join the raffles in {title} by typing /moro or /hello!')

bot_added_handler = ChatMemberHandler(bot_added, -1)
