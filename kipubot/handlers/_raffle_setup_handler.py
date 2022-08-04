import os
from typing import Union
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, MessageHandler,
    CallbackQueryHandler, CommandHandler, InvalidCallbackData)
import telegram.ext.filters as Filters
from telegram._files.document import Document as DocumentFile
from db import get_con

CON = get_con()


async def setup_raffle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Union[str, None]:
    query = update.callback_query
    # print('setup_raffle: ' + str(update))

    if query.data == 'cancel':
        await query.message.edit_text('Cancelled! ❌')
        context.user_data.clear()
        return ConversationHandler.END

    if (isinstance(query.data, InvalidCallbackData) or
            len(query.data) != 3 or
            not isinstance(query.data[0], int) or
            not isinstance(query.data[1], str) or
            not isinstance(query.data[2], DocumentFile)):

        await query.message.edit_text('Unknown error, please try again later! ❌')
        return ConversationHandler.END

    chat_id = query.data[0]
    chat_title = query.data[1]
    file = await context.bot.get_file(query.data[2])

    context.user_data['raffle_chat_id'] = chat_id
    context.user_data['raffle_chat_title'] = chat_title

    if not os.path.exists(f'data/{chat_id}'):
        os.mkdir(f'data/{chat_id}')

    with open(f'data/{chat_id}/data.xlsx', 'wb') as f:
        await file.download(out=f)

    raffle_data = (CON.execute('''SELECT *
                        FROM raffle
                        WHERE chat_id = %s''',
                               (chat_id,))
                   .fetchone())

    if raffle_data is not None:
        keyboard = [
            [InlineKeyboardButton(
                '🆕 Create a new raffle!', callback_data='raffle:new_raffle')],
            [InlineKeyboardButton(
                '🔄 Update existing raffle!', callback_data='raffle:use_existing')],
            [InlineKeyboardButton(
                '❌ Cancel!', callback_data='cancel')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.edit_text(f'Selected {chat_title}!\n' +
                                      'Found existing raffle.\n' +
                                      'Do you want update it or create a new one?')

        await query.message.edit_reply_markup(reply_markup)
    else:
        keyboard = [
            [InlineKeyboardButton(
                '🆕 Create a new raffle!', callback_data='raffle:new_raffle')],
            [InlineKeyboardButton(
                '❌ Cancel!', callback_data='cancel')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.edit_text(f'Selected {chat_title}! \n' +
                                      'No existing raffle found. ' +
                                      'Do you want to create a new one?')

        await query.message.edit_reply_markup(reply_markup)

    return 'ask_date'


async def ask_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Union[str, None]:
    query = update.callback_query
    # print('ask_date: ' + str(update))
    chat_title = context.user_data['raffle_chat_title']

    if query.data == 'cancel':
        await query.message.edit_text('Cancelled! ❌')
        context.user_data.clear()
        return ConversationHandler.END

    command = query.data.split(':')[1]

    if command == 'use_existing':
        await query.message.edit_text(f'Updated raffle data in {chat_title}! 🔄')
        context.user_data.clear()
        return ConversationHandler.END

    await query.message.edit_text('Send the start and end date of the raffle!\n\n' +
                                  'Format (start and end date on separate lines): \n' +
                                  'YYYY-MM-DD HH:MM\n' +
                                  'YYYY-MM-DD HH:MM\n\n' +
                                  '/cancel to cancel')

    return 'get_date'


async def invalid_date(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> Union[str, None]:
    # print('invalid_date: ' + str(update))

    await update.message.reply_text('Invalid date! ❌')

    return 'get_date'


async def get_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    # print('get_date: ' + str(update))

    start_date, end_date = update.message.text.split("\n")

    context.user_data['raffle_start_date'] = start_date
    context.user_data['raffle_end_date'] = end_date

    keyboard = [
        [InlineKeyboardButton('#️⃣ Set fee', callback_data='fee:continue')],
        [InlineKeyboardButton('1️⃣ Use default (1€)',
                              callback_data='fee:default')],
        [InlineKeyboardButton('❌ Cancel', callback_data='cancel')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(f'Start date set to {start_date}!\n' +
                                    f'End date set to {end_date}!', reply_markup=reply_markup)

    return 'ask_fee'


async def ask_fee(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Union[str, None]:
    # print('ask_fee: ' + str(update))
    query = update.callback_query

    if query.data == 'cancel':
        await query.message.edit_text('Cancelled! ❌')
        context.user_data.clear()
        return ConversationHandler.END

    if query.data == 'fee:default':
        context.user_data['raffle_entry_fee'] = 100
        keyboard = [
            [InlineKeyboardButton('✔️ Finish raffle', callback_data='finish')],
            [InlineKeyboardButton('❌ Cancel', callback_data='cancel')]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.edit_text('Fee set to 1€!', reply_markup=reply_markup)

        return 'finish_setup'

    await query.message.edit_text('Send the entry fee to the raffle!\n\n' +
                                  'Example inputs: \n' +
                                  '0.50, 1.5, 2\n\n' +
                                  '/cancel to cancel')

    return 'get_fee'


async def invalid_fee(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> str:
    await update.message.reply_text('Invalid fee! ❌')

    # print('invalid_fee: ' + str(update))

    return 'get_fee'


async def get_fee(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    # print('get_fee: ' + str(update))

    fee = update.message.text
    context.user_data['raffle_entry_fee'] = int(float(fee) * 100)

    keyboard = [
        [InlineKeyboardButton('✔️ Finish raffle', callback_data='finish')],
        [InlineKeyboardButton('❌ Cancel', callback_data='cancel')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(f'Fee set to {fee}€!', reply_markup=reply_markup)

    return 'finish_setup'


async def finish_setup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Union[str, None]:
    # print('finish_setup: ' + str(update))
    query = update.callback_query

    if query.data == 'cancel':
        await query.message.edit_text('Cancelled! ❌')
        context.user_data.clear()
        return ConversationHandler.END

    chat_title = context.user_data['raffle_chat_title']
    chat_id = context.user_data['raffle_chat_id']
    start_date = context.user_data['raffle_start_date'] + ':00'
    end_date = context.user_data['raffle_end_date'] + ':00'
    entry_fee = context.user_data['raffle_entry_fee']
    # print(chat_id, start_date, end_date, entry_fee)

    CON.execute('''INSERT INTO raffle (chat_id, start_date, end_date, entry_fee)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (chat_id)
                    DO UPDATE SET 
                        start_date = EXCLUDED.start_date,
                        end_date = EXCLUDED.end_date,
                        entry_fee = EXCLUDED.entry_fee''',
                (chat_id, start_date, end_date, entry_fee))
    CON.commit()

    await query.message.edit_text(f'New raffle setup in {chat_title}! ✔️')

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()
    await update.message.reply_text('Cancelled! ❌')
    return ConversationHandler.END


async def timeout(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    # print('timeout: ' + str(update))
    query = update.callback_query
    await query.message.edit_text('Timed out! 🕐')

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
