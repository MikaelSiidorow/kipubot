import os
import sys
from typing import Optional
import psycopg
from dotenv import load_dotenv

load_dotenv()

# STORE DB CONNECTION
_CON: Optional[psycopg.Connection] = None

# ENV VARIABLES
BOT_TOKEN = os.getenv('BOT_TOKEN', default=None)
DATABASE_URL = os.getenv('DATABASE_URL', default=None)

if BOT_TOKEN is None:
    print('Bot token is not set!')
    sys.exit(1)

if DATABASE_URL is None:
    print('Database URL is not set!')
    sys.exit(1)


def get_con() -> psycopg.Connection:
    global _CON  # pylint: disable=global-statement

    if not _CON:
        _CON = psycopg.connect(DATABASE_URL)

    return _CON


def _init_db() -> None:
    print('Connecting to DB...')
    con = get_con()
    print('Connected!')
    print('Initializing database...')
    try:
        con.execute('''CREATE TABLE IF NOT EXISTS chat (
                        chat_id BIGINT PRIMARY KEY,
                        title VARCHAR(128),
                        admins BIGINT[],
                        prev_winners BIGINT[],
                        cur_winner BIGINT
                    )''')

        con.execute('''CREATE TABLE IF NOT EXISTS chat_user (
                        user_id BIGINT PRIMARY KEY
                    )''')

        con.execute('''CREATE TABLE IF NOT EXISTS in_chat (
                        user_id BIGINT REFERENCES chat_user(user_id),
                        chat_id BIGINT REFERENCES chat(chat_id),
                        PRIMARY KEY (user_id, chat_id)
                    )''')

        con.execute('''CREATE TABLE IF NOT EXISTS raffle (
                        chat_id BIGINT PRIMARY KEY REFERENCES chat(chat_id),
                        start_date TIMESTAMP,
                        end_date TIMESTAMP,
                        entry_fee INTEGER,
                        dates TIMESTAMP[],
                        entries VARCHAR(128)[],
                        amounts INTEGER[]
                    )''')
    except psycopg.errors.Error as e:
        print('Unknown error during database initialization:')
        print(e)
        con.rollback()
    else:
        print('Database succesfully initialized!')
        con.commit()


# INITIALIZE DB AND CREATE TABLES IF THEY DON'T EXIST
_init_db()

__all__ = (
    'get_con',
    'BOT_TOKEN',
    'DATABASE_URL',
)
