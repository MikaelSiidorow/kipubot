import os
from typing import Union
import pandas as pd
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, MessageHandler,
    CallbackQueryHandler, CommandHandler, InvalidCallbackData)
import telegram.ext.filters as Filters
from kipubot.constants import STRINGS
from kipubot.utils import get_raffle, save_raffle, read_excel_to_df
from kipubot.errors import NoRaffleError


async def setup_raffle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Union[str, None]:
    query = update.callback_query
    if query.data == 'cancel':
        await query.message.edit_text(STRINGS['cancelled'])
        context.user_data.clear()
        return ConversationHandler.END

    if (isinstance(query.data, InvalidCallbackData) or
            len(query.data) != 2 or
            not isinstance(query.data[0], int) or
            not isinstance(query.data[1], str)):

        await query.message.edit_text(STRINGS['unknown_error'])
        return ConversationHandler.END

    chat_id = query.data[0]
    chat_title = query.data[1]

    context.user_data['raffle_chat_id'] = chat_id
    context.user_data['raffle_chat_title'] = chat_title

    try:
        get_raffle(chat_id)

        keyboard = [
            [InlineKeyboardButton(
                STRINGS['new_raffle_button'], callback_data='raffle:new_raffle')],
            [InlineKeyboardButton(
                STRINGS['update_raffle_button'], callback_data='raffle:use_existing')],
            [InlineKeyboardButton(
                STRINGS['cancel_button'],
                callback_data='cancel')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.edit_text(STRINGS['update_or_new_raffle'] % {'chat_title': chat_title})
        await query.message.edit_reply_markup(reply_markup)

    except NoRaffleError:
        keyboard = [
            [InlineKeyboardButton(
                STRINGS['new_raffle_button'], callback_data='raffle:new_raffle')],
            [InlineKeyboardButton(
                STRINGS['cancel_button'], callback_data='cancel')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.edit_text(STRINGS['new_raffle_text'] % {'chat_title': chat_title})
        await query.message.edit_reply_markup(reply_markup)

    return 'ask_date'


async def ask_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Union[str, None]:
    query = update.callback_query
    chat_title = context.user_data['raffle_chat_title']

    if query.data == 'cancel':
        await query.message.edit_text(STRINGS['cancelled'])
        context.user_data.clear()
        return ConversationHandler.END

    command = query.data.split(':')[1]

    if command == 'use_existing':
        chat_id = context.user_data['raffle_chat_id']
        dm_id = update.effective_chat.id

        start_date, end_date, entry_fee, _ = get_raffle(chat_id)
        excel_path = f'data/{dm_id}/data.xlsx'
        df = read_excel_to_df(excel_path, start_date, end_date)
        save_raffle(chat_id, start_date, end_date, entry_fee, df)

        await query.message.edit_text(STRINGS['updated_raffle'] % {'chat_title': chat_title})
        await context.bot.send_message(chat_id,
                                       STRINGS['raffle_updated_chat']
                                       % {'username': update.effective_user.username})
        # perform cleanup
        context.user_data.clear()
        os.remove(excel_path)

        return ConversationHandler.END

    await query.message.edit_text(STRINGS['raffle_dates_prompt'])

    return 'get_date'


async def invalid_date(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> Union[str, None]:
    await update.message.reply_text(STRINGS['invalid_date'])

    return 'get_date'


async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    start_date, end_date = update.message.text.split("\n")

    if not pd.Timestamp(end_date) > pd.Timestamp(start_date):
        await update.message.reply_text(STRINGS['end_date_before_start'])

        return 'get_date'

    context.user_data['raffle_start_date'] = start_date
    context.user_data['raffle_end_date'] = end_date

    keyboard = [
        [InlineKeyboardButton(STRINGS['set_fee_button'],
                              callback_data='fee:continue')],
        [InlineKeyboardButton(STRINGS['default_fee_button'],
                              callback_data='fee:default')],
        [InlineKeyboardButton(STRINGS['cancel_button'],
                              callback_data='cancel')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(f'Start date set to {start_date}!\n' +
                                    f'End date set to {end_date}!', reply_markup=reply_markup)

    return 'ask_fee'


async def ask_fee(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Union[str, None]:
    query = update.callback_query

    if query.data == 'cancel':
        await query.message.edit_text(STRINGS['cancelled'])
        context.user_data.clear()
        return ConversationHandler.END

    if query.data == 'fee:default':
        context.user_data['raffle_entry_fee'] = 100
        keyboard = [
            [InlineKeyboardButton(
                STRINGS['finish_raffle_button'], callback_data='finish')],
            [InlineKeyboardButton(STRINGS['cancel_button'],
                                  callback_data='cancel')]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.edit_text(
            STRINGS['default_fee_confirmation'],
            reply_markup=reply_markup)

        return 'finish_setup'

    await query.message.edit_text(STRINGS['raffle_fee_prompt'])

    return 'get_fee'


async def invalid_fee(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> str:
    await update.message.reply_text(STRINGS['invalid_fee'])

    return 'get_fee'


async def get_fee(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    fee = update.message.text
    context.user_data['raffle_entry_fee'] = int(float(fee) * 100)

    keyboard = [
        [InlineKeyboardButton(
            STRINGS['finish_raffle_button'], callback_data='finish')],
        [InlineKeyboardButton(STRINGS['cancel_button'],
                              callback_data='cancel')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(STRINGS['fee_confirmation'] % (fee), reply_markup=reply_markup)

    return 'finish_setup'


async def finish_setup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Union[str, None]:
    query = update.callback_query
    dm_id = update.effective_chat.id

    if query.data == 'cancel':
        await query.message.edit_text(STRINGS['cancelled'])
        context.user_data.clear()
        return ConversationHandler.END

    chat_title = context.user_data['raffle_chat_title']
    chat_id = context.user_data['raffle_chat_id']
    start_date = context.user_data['raffle_start_date'] + ':00'
    end_date = context.user_data['raffle_end_date'] + ':00'
    entry_fee = context.user_data['raffle_entry_fee']

    excel_path = f'data/{dm_id}/data.xlsx'
    df = read_excel_to_df(excel_path, start_date, end_date)
    save_raffle(chat_id, start_date, end_date, entry_fee, df)

    await query.message.edit_text(STRINGS['raffle_confirmation'] % {'chat_title': chat_title})
    await context.bot.send_message(chat_id, STRINGS['raffle_created_chat']
                                   % {'username': update.effective_user.username})

    # perform cleanup
    context.user_data.clear()
    os.remove(excel_path)

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()
    await update.message.reply_text(STRINGS['cancelled'])
    return ConversationHandler.END


async def timeout(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.message.edit_text(STRINGS['timed_out'])

# YYYY-MM-DD HH:mm regex
TWO_LINE_DATE_FILTER = Filters.Regex(
    r'^(\d{4})-(0[1-9]|1[0-2])-(0[1-9]|[1-2]\d|3[0-2])\s([0-1]\d|2[0-3]):([0-5]\d)\n' +
    r'(\d{4})-(0[1-9]|1[0-2])-(0[1-9]|[1-2]\d|3[0-2])\s([0-1]\d|2[0-3]):([0-5]\d)$')

PRICE_FILTER = Filters.Regex(r'^(([1-9]\d|[1-9])(.\d)?)|(0.[1-9]\d?)$')

raffle_setup_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(setup_raffle)],
    states={
        'ask_date': [CallbackQueryHandler(ask_date)],
        'get_date': [
            MessageHandler(TWO_LINE_DATE_FILTER, get_date),
            MessageHandler(Filters.ALL & ~Filters.COMMAND, invalid_date),
            CommandHandler('cancel', cancel)
        ],
        'ask_fee': [CallbackQueryHandler(ask_fee)],
        'get_fee': [
            MessageHandler(PRICE_FILTER, get_fee),
            MessageHandler(Filters.ALL & ~Filters.COMMAND, invalid_fee),
            CommandHandler('cancel', cancel)
        ],
        'finish_setup': [CallbackQueryHandler(finish_setup)],
        ConversationHandler.TIMEOUT: [CallbackQueryHandler(timeout)]
    },
    fallbacks=[CallbackQueryHandler(setup_raffle)],
    conversation_timeout=120
)
