import os
from typing import Literal

import pandas as pd
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes, ConversationHandler

from kipubot.constants import STRINGS
from kipubot.errors import NoRaffleError
from kipubot.types import RaffleData
from kipubot.utils import (
    get_cur_time_hel,
    get_raffle_stats,
    int_price_to_str,
    is_float,
    is_int,
    read_excel_to_df,
    save_raffle,
    update_raffle,
)

# ==================
# = UTIL FUNCTIONS =
# ==================

# CLEAR FUNCTIONS
# ----------------


async def cancel_convo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not query or not query.message:
        return ConversationHandler.END
    await query.answer(STRINGS["cancelled"])
    await query.message.edit_text(STRINGS["cancelled"])
    if context.user_data:
        context.user_data.clear()
    return ConversationHandler.END


async def convo_error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not query or not query.message:
        return ConversationHandler.END
    await query.answer(STRINGS["unknown_error"])
    await query.message.edit_text(STRINGS["unknown_error"])
    if context.user_data:
        context.user_data.clear()
    return ConversationHandler.END


async def convo_timeout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if not query or not query.message:
        return ConversationHandler.END
    await query.answer(STRINGS["timed_out"])
    await query.message.edit_text(STRINGS["timed_out"])
    if context.user_data:
        context.user_data.clear()
    return ConversationHandler.END


# KEYBOARD COMPONENTS
# --------------------
RAFFLE_CHAT_SELECTED_DATA_LENGTH = 4
RAFFLE_DATE_UPDATE_DATA_LENGTH = 5
RAFFLE_FEE_UPDATE_DATA_LENGTH = 4


def raffle_keyboard(*, has_existing: bool = False) -> InlineKeyboardMarkup:
    if has_existing:
        keyboard = [
            [
                InlineKeyboardButton(
                    STRINGS["update_raffle_button"], callback_data="raffle:setup:old"
                )
            ],
            [
                InlineKeyboardButton(
                    STRINGS["cancel_button"], callback_data="raffle:cancel"
                )
            ],
        ]
        return InlineKeyboardMarkup(keyboard)

    keyboard = [
        [
            InlineKeyboardButton(
                STRINGS["new_raffle_button"], callback_data="raffle:setup:new"
            )
        ],
        [InlineKeyboardButton(STRINGS["cancel_button"], callback_data="raffle:cancel")],
    ]
    return InlineKeyboardMarkup(keyboard)


def date_keyboard(which: Literal["start", "end"]) -> InlineKeyboardMarkup:
    rough_controls = [
        InlineKeyboardButton("-1 d", callback_data=f"raffle:date:{which}:update:-24"),
        InlineKeyboardButton("-12 h", callback_data=f"raffle:date:{which}:update:-12"),
        InlineKeyboardButton("-6 h", callback_data=f"raffle:date:{which}:update:-6"),
        InlineKeyboardButton("+6 h", callback_data=f"raffle:date:{which}:update:+6"),
        InlineKeyboardButton("+12 h", callback_data=f"raffle:date:{which}:update:+12"),
        InlineKeyboardButton("+1 d", callback_data=f"raffle:date:{which}:update:+24"),
    ]

    smooth_controls = [
        InlineKeyboardButton("-1 h", callback_data=f"raffle:date:{which}:update:-1"),
        InlineKeyboardButton("-30 m", callback_data=f"raffle:date:{which}:update:-0.5"),
        InlineKeyboardButton(
            "-15 m", callback_data=f"raffle:date:{which}:update:-0.25"
        ),
        InlineKeyboardButton(
            "+15 m", callback_data=f"raffle:date:{which}:update:+0.25"
        ),
        InlineKeyboardButton("+30 m", callback_data=f"raffle:date:{which}:update:+0.5"),
        InlineKeyboardButton("+1 h", callback_data=f"raffle:date:{which}:update:+1"),
    ]

    keyboard = [
        rough_controls,
        smooth_controls,
        [
            InlineKeyboardButton(
                STRINGS["confirm_button"],
                callback_data=f"raffle:date:{which}:confirmed",
            )
        ],
        [InlineKeyboardButton(STRINGS["cancel_button"], callback_data="raffle:cancel")],
    ]

    return InlineKeyboardMarkup(keyboard)


def fee_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("-1", callback_data="raffle:fee:update:-100"),
            InlineKeyboardButton("-0.5", callback_data="raffle:fee:update:-50"),
            InlineKeyboardButton("+0.5", callback_data="raffle:fee:update:+50"),
            InlineKeyboardButton("+1", callback_data="raffle:fee:update:+100"),
        ],
        [
            InlineKeyboardButton(
                STRINGS["finish_raffle_button"], callback_data="raffle:fee:confirmed"
            )
        ],
        [InlineKeyboardButton(STRINGS["cancel_button"], callback_data="raffle:cancel")],
    ]

    return InlineKeyboardMarkup(keyboard)


# =================
# = MAIN HANDLERS =
# =================


async def setup_raffle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str | int:
    query = update.callback_query
    if not query or not query.message or not query.data or context.user_data is None:
        if query:
            await query.answer(STRINGS["unknown_error"])
        return ConversationHandler.END

    if query.data == "raffle:cancel":
        return await cancel_convo(update, context)

    if (
        query.data.startswith("raffle:chat_selected")
        and len(query.data.split(":")) == RAFFLE_CHAT_SELECTED_DATA_LENGTH
        and is_int(query.data.split(":")[2])
    ):
        args = query.data.split(":")

        chat_id = int(args[2])
        chat_title = args[3]

        # store selected chat in user_data
        context.user_data["raffle_chat_id"] = chat_id
        context.user_data["raffle_chat_title"] = chat_title

        try:
            get_raffle_stats(chat_id)

            msg = (
                STRINGS["raffle_setup_base"] + STRINGS["raffle_setup_update_or_new"]
            ) % {"chat_title": chat_title}

            await query.message.edit_text(
                msg, reply_markup=raffle_keyboard(has_existing=True)
            )

        except NoRaffleError:
            msg = (STRINGS["raffle_setup_base"] + STRINGS["raffle_setup_new"]) % {
                "chat_title": chat_title
            }

            await query.message.edit_text(msg, reply_markup=raffle_keyboard())

        return "raffle_setup_state:update_or_new"

    # If nothing matches, return error
    return await convo_error(update, context)


async def setup_start_date(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> str | int:
    query = update.callback_query
    if not query or not query.message or not query.data or not context.user_data:
        return ConversationHandler.END

    if query.data == "raffle:setup:new":
        context.user_data["raffle_start_date"] = get_cur_time_hel().floor(freq="15T")

    if (
        query.data.startswith("raffle:date:start:update")
        and len(query.data.split(":")) == RAFFLE_DATE_UPDATE_DATA_LENGTH
        and is_float(query.data.split(":")[4])
    ):
        diff = float(query.data.split(":")[4])
        old_date = context.user_data["raffle_start_date"]
        new_date = old_date + pd.Timedelta(diff, unit="h")  # type: ignore

        context.user_data["raffle_start_date"] = new_date

    if query.data == "raffle:setup:new" or query.data.startswith(
        "raffle:date:start:update"
    ):
        chat_title = context.user_data["raffle_chat_title"]
        start_date = context.user_data["raffle_start_date"]

        msg = (STRINGS["raffle_setup_base"] + STRINGS["raffle_setup_start_date"]) % {
            "chat_title": chat_title,
            "start_date": start_date,
        }

        await query.message.edit_text(msg, reply_markup=date_keyboard("start"))

        return "raffle_setup_state:start_date"

    return ConversationHandler.END


async def setup_end_date(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> str | int:
    query = update.callback_query
    if not query or not query.message or not query.data or not context.user_data:
        return ConversationHandler.END

    if query.data == "raffle:date:start:confirmed":
        context.user_data["raffle_end_date"] = context.user_data["raffle_start_date"]

    if (
        query.data.startswith("raffle:date:end:update")
        and len(query.data.split(":")) == RAFFLE_DATE_UPDATE_DATA_LENGTH
        and is_int(query.data.split(":")[4])
    ):
        diff = int(query.data.split(":")[4])
        old_date = context.user_data["raffle_end_date"]
        new_date = old_date + pd.Timedelta(diff, unit="h")

        context.user_data["raffle_end_date"] = new_date

    if query.data == "raffle:date:start:confirmed" or query.data.startswith(
        "raffle:date:end:update"
    ):
        chat_title = context.user_data["raffle_chat_title"]
        start_date = context.user_data["raffle_start_date"]
        end_date = context.user_data["raffle_end_date"]

        msg = (
            STRINGS["raffle_setup_base"]
            + STRINGS["raffle_setup_start_date"]
            + STRINGS["raffle_setup_end_date"]
        )

        if end_date < start_date:
            context.user_data["raffle_end_date"] = start_date
            end_date = start_date
            msg += STRINGS["end_date_before_start"]

        msg = msg % {
            "chat_title": chat_title,
            "start_date": start_date,
            "end_date": end_date,
        }

        if query.message.text != msg:
            await query.message.edit_text(msg, reply_markup=date_keyboard("end"))

        return "raffle_setup_state:end_date"

    return ConversationHandler.END


async def setup_fee(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str | int:
    query = update.callback_query
    if not query or not query.message or not query.data or not context.user_data:
        return ConversationHandler.END

    if query.data == "raffle:date:end:confirmed":
        context.user_data["raffle_fee"] = 100

    if (
        query.data.startswith("raffle:fee:update")
        and len(query.data.split(":")) == RAFFLE_FEE_UPDATE_DATA_LENGTH
        and is_int(query.data.split(":")[3])
    ):
        diff = int(query.data.split(":")[3])
        old_fee = context.user_data["raffle_fee"]
        new_fee = old_fee + diff

        context.user_data["raffle_fee"] = new_fee

    if query.data == "raffle:date:end:confirmed" or query.data.startswith(
        "raffle:fee:update"
    ):
        chat_title = context.user_data["raffle_chat_title"]
        start_date = context.user_data["raffle_start_date"]
        end_date = context.user_data["raffle_end_date"]
        fee = context.user_data["raffle_fee"]

        msg = (
            STRINGS["raffle_setup_base"]
            + STRINGS["raffle_setup_start_date"]
            + STRINGS["raffle_setup_end_date"]
            + STRINGS["raffle_setup_fee"]
        )

        if fee < 0:
            context.user_data["raffle_fee"] = 0
            msg += STRINGS["negative_fee"]

        msg = msg % {
            "chat_title": chat_title,
            "start_date": start_date,
            "end_date": end_date,
            "fee": int_price_to_str(fee),
        }

        if query.message.text != msg:
            await query.message.edit_text(msg, reply_markup=fee_keyboard())

        return "raffle_setup_state:fee"

    return ConversationHandler.END


async def finish_setup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | int:
    query = update.callback_query
    if (
        not query
        or not query.message
        or not query.data
        or not context.user_data
        or not update.effective_chat
        or not update.effective_user
    ):
        return ConversationHandler.END
    dm_id = update.effective_chat.id

    if query.data == "raffle:setup:old":
        chat_title = context.user_data["raffle_chat_title"]
        chat_id = context.user_data["raffle_chat_id"]
        dm_id = update.effective_chat.id

        raffle_id, (start_date, end_date, entry_fee) = get_raffle_stats(chat_id)
        excel_path = f"data/{dm_id}/data.xlsx"
        df = read_excel_to_df(excel_path, start_date, end_date)
        raffle_data = RaffleData(start_date, end_date, entry_fee, df)
        update_raffle(raffle_id, raffle_data)

        await query.message.edit_text(
            STRINGS["updated_raffle"] % {"chat_title": chat_title}
        )
        await context.bot.send_message(
            chat_id,
            STRINGS["raffle_updated_chat"]
            % {"username": update.effective_user.username},
        )
        # perform cleanup
        context.user_data.clear()
        os.remove(excel_path)

        return ConversationHandler.END

    if query.data == "raffle:fee:confirmed":
        chat_title = context.user_data["raffle_chat_title"]
        chat_id = context.user_data["raffle_chat_id"]
        user_id = update.effective_user.id
        start_date = context.user_data["raffle_start_date"]
        end_date = context.user_data["raffle_end_date"]
        fee = context.user_data["raffle_fee"]

        excel_path = f"data/{dm_id}/data.xlsx"
        df = read_excel_to_df(excel_path, start_date, end_date)
        raffle_data = RaffleData(start_date, end_date, fee, df)
        save_raffle(chat_id, user_id, raffle_data)

        msg = (
            STRINGS["raffle_setup_base"]
            + STRINGS["raffle_setup_start_date"]
            + STRINGS["raffle_setup_end_date"]
            + STRINGS["raffle_setup_fee"]
            + STRINGS["raffle_confirmation"]
        ) % {
            "chat_title": chat_title,
            "start_date": start_date,
            "end_date": end_date,
            "fee": int_price_to_str(fee),
        }

        await query.message.edit_text(msg)
        await query.answer()
        await context.bot.send_message(
            chat_id,
            STRINGS["raffle_created_chat"]
            % {"username": update.effective_user.username},
        )

        # perform cleanup
        context.user_data.clear()
        os.remove(excel_path)

        return ConversationHandler.END

    return ConversationHandler.END


raffle_setup_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(setup_raffle, pattern="^raffle:.*$")],
    states={
        "raffle_setup_state:update_or_new": [
            CallbackQueryHandler(setup_start_date, pattern="^raffle:setup:new$"),
            CallbackQueryHandler(finish_setup, pattern="^raffle:setup:old$"),
        ],
        "raffle_setup_state:start_date": [
            CallbackQueryHandler(
                setup_start_date, pattern="^raffle:date:start:update.*$"
            ),
            CallbackQueryHandler(
                setup_end_date, pattern="^raffle:date:start:confirmed$"
            ),
        ],
        "raffle_setup_state:end_date": [
            CallbackQueryHandler(setup_end_date, pattern="^raffle:date:end:update.*$"),
            CallbackQueryHandler(setup_fee, pattern="^raffle:date:end:confirmed$"),
        ],
        "raffle_setup_state:fee": [
            CallbackQueryHandler(setup_fee, pattern="^raffle:fee:update.*$"),
            CallbackQueryHandler(finish_setup, pattern="^raffle:fee:confirmed$"),
        ],
        ConversationHandler.TIMEOUT: [CallbackQueryHandler(convo_timeout)],
    },
    fallbacks=[CallbackQueryHandler(setup_raffle)],
    conversation_timeout=120,
    name="raffle_setup",
    persistent=True,
    per_message=True,
)
