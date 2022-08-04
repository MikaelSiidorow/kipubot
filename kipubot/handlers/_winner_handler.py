from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from telegram.constants import MessageEntityType
import telegram.ext.filters as Filters
import psycopg.errors as PSErrors
from db import get_con
from constants import STRINGS

CON = get_con()


async def winner(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    # only usable by admin, previous winner (in case of typos) and current winner
    # usage: /winner @username
    # -> set the winner to the given username

    ent = update.message.entities
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    if len(ent) != 2 or ent[1].type != MessageEntityType.MENTION:
        await update.message.reply_text(STRINGS['invalid_winner_usage'])
        return

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
            await update.message.reply_text(STRINGS['forbidden_command'])
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
            await update.message.reply_text(STRINGS['user_not_found'])
            return

        if winner_id[0] == user_id and not is_admin:
            await update.message.reply_text(STRINGS['already_winner'])
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
    except PSErrors.Error as e:
        print(e)
        await update.message.reply_text(STRINGS['user_not_found'])
        return

    CON.commit()
    await update.message.reply_text(STRINGS['winner_confirmation'] % {'username': username})

winner_handler = CommandHandler(
    ['voittaja', 'winner'], winner, ~Filters.ChatType.PRIVATE)
