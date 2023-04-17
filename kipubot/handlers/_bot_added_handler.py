import psycopg.errors as pserrors
from telegram import Update
from telegram.constants import ChatMemberStatus
from telegram.ext import ChatMemberHandler, ContextTypes

from kipubot.constants import STRINGS
from kipubot.db import register_user_or_ignore, save_chat_or_ignore, save_user_or_ignore


async def bot_added(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # when bot is added to channel:
    # -> add the channel to a database
    # -> set the adder as the current winner of the channel
    # -> also set the adder as an admin (can update winner always)

    if update.my_chat_member.new_chat_member.status != ChatMemberStatus.LEFT:
        chat_id = update.effective_chat.id
        title = update.effective_chat.title
        user_id = update.effective_user.id
        admins = await update.effective_chat.get_administrators()
        admin_ids = list(set([admin.user.id for admin in admins] + [user_id]))

        try:
            save_chat_or_ignore(chat_id, title, admin_ids)
            save_user_or_ignore(user_id)
            register_user_or_ignore(chat_id, user_id)

        except pserrors.IntegrityError as e:
            print("SQLite Error: " + str(e))
            await context.bot.send_message(
                chat_id=chat_id, text=STRINGS["unknown_error"]
            )
        else:
            # Kiitos pääsystä! -stigu
            await context.bot.send_sticker(
                chat_id=chat_id,
                sticker="CAACAgQAAxkBAAIBPmLicTHP2Xv8IcFzxHYocjLRFBvQAAI5AAMcLHsXd9jLHwYNcSEpBA",
            )
            await context.bot.send_message(
                chat_id=chat_id, text=STRINGS["moro_prompt"] % {"chat_title": title}
            )


bot_added_handler = ChatMemberHandler(bot_added, -1)
