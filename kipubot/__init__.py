import os
import sys
from dotenv import load_dotenv
import kipubot.db

load_dotenv()


# ENV VARIABLES
BOT_TOKEN = os.getenv('BOT_TOKEN', default=None)
DATABASE_URL = os.getenv('DATABASE_URL', default=None)

if BOT_TOKEN is None:
    print('Bot token is not set!')
    sys.exit(1)

if DATABASE_URL is None:
    print('Database URL is not set!')
    sys.exit(1)


# INITIALIZE DB AND CREATE TABLES IF THEY DON'T EXIST
kipubot.db._init_db(DATABASE_URL)  # pylint: disable=protected-access

__all__ = (
    'BOT_TOKEN',
    'DATABASE_URL',
)
