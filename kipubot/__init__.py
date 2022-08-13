import os
import sys
import psycopg
from dotenv import load_dotenv

load_dotenv()

# STORE DB CONNECTION
_CON = None

# ENV VARIABLES
BOT_TOKEN = os.getenv('BOT_TOKEN', default=None)
DATABASE_URL = os.getenv('DATABASE_URL', default=None)

if BOT_TOKEN is None:
    print('Bot token is not set!')
    sys.exit(1)

if DATABASE_URL is None:
    print('Database URL is not set!')
    sys.exit(1)


def get_con():
    global _CON  # pylint: disable=global-statement

    if not _CON:
        _CON = psycopg.connect(DATABASE_URL)

    return _CON


__all__ = (
    'get_con',
    'BOT_TOKEN',
    'DATABASE_URL',
)
