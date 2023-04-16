from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from telegram.constants import MessageEntityType
import telegram.ext.filters as Filters
import psycopg.errors as PSErrors
from kipubot.constants import STRINGS
from kipubot.db import (
    admin_cycle_winners,
    cycle_winners,
    get_registered_member_ids,
    get_admin_ids,
    get_prev_winner_ids,
    get_winner_id,
    replace_cur_winner,
)
from kipubot.utils import get_chat_member_opt


async def winner(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    # only usable by admin, previous winner (in case of typos) and current winner
    # usage: /winner @username
    # -> set the winner to the given username

    ent = update.message.entities
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if len(ent) != 2 or ent[1].type != MessageEntityType.MENTION:
        await update.message.reply_text(STRINGS["invalid_winner_usage"])
        return

    username = update.message.text.split(" ")[1][1:]

    try:
        is_admin = user_id in get_admin_ids(chat_id)
        is_cur_winner = user_id == get_winner_id(chat_id)

        prev_winner_ids = get_prev_winner_ids(chat_id)
        is_prev_winner = prev_winner_ids and user_id == prev_winner_ids[-1]

        if not is_admin and not is_cur_winner and not is_prev_winner:
            await update.message.reply_text(STRINGS["forbidden_command"])
            return

        registered_member_ids = get_registered_member_ids(chat_id)
        registered_members = [
            await get_chat_member_opt(update.effective_chat, id)
            for id in registered_member_ids
        ]
        # drop None values
        registered_members = [m for m in registered_members if m]
        supposed_winner = [
            member for member in registered_members if member.user.username == username
        ]

        if not supposed_winner:
            await update.message.reply_text(STRINGS["user_not_found"])
            return

        winner_id = supposed_winner[0].user.id

        if winner_id == user_id and not is_admin:
            await update.message.reply_text(STRINGS["already_winner"])
            return

        # admin: moves current to prev and makes new current
        if is_admin:
            admin_cycle_winners(winner_id, chat_id)
        # prev_winner: replaces current winner directly (assumed typo)
        elif is_prev_winner:
            replace_cur_winner(winner_id, chat_id)
        # winner: moves themselves to prev and makes new current
        else:
            cycle_winners(user_id, winner_id, chat_id)
    except PSErrors.Error as e:
        print(e)
        await update.message.reply_text(STRINGS["user_not_found"])
        return

    await update.message.reply_text(
        STRINGS["winner_confirmation"] % {"username": username}
    )


winner_handler = CommandHandler(
    ["voittaja", "winner"], winner, ~Filters.ChatType.PRIVATE
)
