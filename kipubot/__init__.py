import os
import sys
import logging
from dotenv import load_dotenv
import kipubot.db

load_dotenv()

# LOGGING CONFIG
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


# ENV VARIABLES
BOT_TOKEN = os.getenv('BOT_TOKEN', default=None)
DATABASE_URL = os.getenv('DATABASE_URL', default=None)

if BOT_TOKEN is None:
    logging.error('Bot token is not set!')
    sys.exit(1)

if DATABASE_URL is None:
    logging.error('Database URL is not set!')
    sys.exit(1)


# INITIALIZE DB AND CREATE TABLES IF THEY DON'T EXIST
kipubot.db._init_db(DATABASE_URL)  # pylint: disable=protected-access

# CHECK/CREATE DATA DIRECTORY
if not os.path.exists('data'):
    logging.info('Creating ./data/ directory...')
    os.mkdir('data')

__all__ = (
    'BOT_TOKEN',
    'DATABASE_URL',
)
