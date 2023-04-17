# CONSTANTS
EXCEL_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

STRINGS = {
    "moro_prompt": "Join the raffles in %(chat_title)s by typing /moro or /hello!",
    "not_winner": "You are not the winner in any chat! ❌",
    "choose_channel": "Choose channel:",
    "chat_button": "💬 %(chat_title)s",
    "cancel_button": "❌ Cancel",
    "no_raffle": "No raffle data found in %(chat_title)s!",
    "raffle_db_error": (
        "Error getting raffle data from database!\n\n"
        "Perhaps one is not setup yet for this chat? 🤔"
    ),
    "no_entries": "No raffle entries yet in %(chat_title)s!",
    "no_data": "No data found for %(chat_title)s!",
    "moro": "Registered %(username)s in %(chat_title)s!",
    "double_moro": "You are already registered in %(chat_title)s!",
    "no_dm_warn": "This command is not usable in private messages!",
    "cancelled": "Cancelled! ❌",
    "unknown_error": "Unknown error, please try again later! ❌",
    "server_error": (
        "Server error, please try again later! ❌\n\n"
        "The administration has been contacted."
    ),
    "invalid_file": "Invalid Excel file! ❌\n\n/start for instructions",
    "new_raffle_button": "🆕 Create a new raffle!",
    "update_raffle_button": "🔄 Update existing raffle!",
    "raffle_setup_base": (
        "📝 Raffle setup for %(chat_title)s\n=============================\n\n"
    ),
    "raffle_setup_update_or_new": (
        "Found existing raffle.\nDo you want update it or create a new one?"
    ),
    "raffle_setup_new": "No existing raffle found.\nDo you want to create a new one?",
    "updated_raffle": "Updated raffle data in %(chat_title)s! 🔄",
    "raffle_setup_start_date": "Start date set to %(start_date)s!\n",
    "raffle_setup_end_date": "End date set to %(end_date)s!\n\n",
    "raffle_setup_fee": "Fee set to %(fee)s €!\n\n",
    "end_date_before_start": "End date cannot be before start date! ❌",
    "negative_fee": "Fee cannot be negative! ❌",
    "confirm_button": "✔️ Confirm",
    "finish_raffle_button": "✔️ Finish raffle",
    "raffle_confirmation": "Succesfully setup new raffle in %(chat_title)s! ✔️",
    "raffle_created_chat": "New raffle created by @%(username)s! ✔️",
    "raffle_updated_chat": "Raffle updated by @%(username)s! ✔️",
    "timed_out": "Timed out! 🕐",
    "start_prompt": (
        "Use the given commands or send me an Excel-file "
        "from MobilePay if you're the host of a raffle!"
    ),
    "invalid_winner_usage": "Please use the format /winner @username",
    "forbidden_command": "You are not allowed to use this command! ❌",
    "user_not_found": ("Error getting user!\nPerhaps they haven't /moro ed? 🤔"),
    "already_winner": "You are already the winner!",
    "winner_confirmation": "%(username)s is the new winner!",
}
