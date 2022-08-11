# CONSTANTS
EXCEL_MIME = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

STRINGS = {
    'moro_prompt': 'Join the raffles in %(chat_title)s by typing /moro or /hello!',
    'not_winner': 'You are not the winner in any chat! ❌',
    'choose_channel': 'Choose channel:',
    'chat_button': '💬 %(chat_title)s',
    'cancel_button': '❌ Cancel',
    'no_raffle': 'No raffle data found in %(chat_title)s!',
    'raffle_db_error': ('Error getting raffle data from database!\n\n' +
                        'Perhaps one is not setup yet for this chat? 🤔'),
    'no_entries': 'No raffle entries yet in %(chat_title)s!',
    'no_data': 'No data found for %(chat_title)s!',
    'moro': 'Registered %(username)s in %(chat_title)s!',
    'double_moro': 'You are already registered in %(chat_title)s!',
    'no_dm_warn': 'This command is not usable in private messages!',
    'cancelled': 'Cancelled! ❌',
    'unknown_error': 'Unknown error, please try again later! ❌',
    'invalid_file': 'Invalid Excel file! ❌\n\n/start for instructions',
    'new_raffle_button': '🆕 Create a new raffle!',
    'update_raffle_button': '🔄 Update existing raffle!',
    'update_or_new_raffle': ('Selected %(chat_title)s!\n' +
                             'Found existing raffle.\n' +
                             'Do you want update it or create a new one?'),
    'new_raffle_text': ('Selected %(chat_title)s! \n' +
                        'No existing raffle found. ' +
                        'Do you want to create a new one?'),
    'updated_raffle': 'Updated raffle data in %(chat_title)s! 🔄',
    'raffle_dates_prompt': ('Send the start and end date of the raffle!\n\n' +
                            'Format (start and end date on separate lines): \n' +
                            'YYYY-MM-DD HH:MM\n' +
                            'YYYY-MM-DD HH:MM\n\n' +
                            '/cancel to cancel'),
    'end_date_before_start': 'End date cannot be before start date! ❌',
    'invalid_date': 'Invalid date! ❌',
    'set_fee_button': '#️⃣ Set fee',
    'default_fee_button': '1️⃣ Use default (1€)',
    'finish_raffle_button': '✔️ Finish raffle',
    'default_fee_confirmation': 'Fee set to 1€!',
    'fee_confirmation': 'Fee set to %s€!',
    'raffle_fee_prompt': ('Send the entry fee to the raffle!\n\n' +
                          'Example inputs: \n' +
                          '0.50, 1.5, 2\n\n' +
                          '/cancel to cancel'),
    'invalid_fee': 'Invalid fee! ❌',
    'raffle_confirmation': 'New raffle setup in %(chat_title)s! ✔️',
    'raffle_created_chat': 'New raffle created by @%(username)s! ✔️',
    'raffle_updated_chat': 'Raffle updated by @%(username)s! ✔️',
    'timed_out': 'Timed out! 🕐',
    'start_prompt': ('Use the given commands or send me an Excel-file ' +
                     'from MobilePay if you\'re the host of a raffle!'),
    'invalid_winner_usage': 'Please use the format /winner @username',
    'forbidden_command': 'You are not allowed to use this command! ❌',
    'user_not_found': ('Error getting user!\n' +
                       'Perhaps they haven\'t /moro ed? 🤔'),
    'already_winner': 'You are already the winner!',
    'winner_confirmation': '%(username)s is the new winner!'
}
