import logging
import os
import sys

from dotenv import load_dotenv

import kipubot.db

load_dotenv()

# LOGGING CONFIG
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


# ENV VARIABLES
BOT_TOKEN = os.getenv("BOT_TOKEN", default=None)
DATABASE_URL = os.getenv("DATABASE_URL", default=None)
DEVELOPER_CHAT_ID = os.getenv("DEVELOPER_CHAT_ID", default=None)
MODE = os.getenv("MODE", default=None)
if BOT_TOKEN is None and MODE != "TEST":
    logging.error("Bot token is not set!")
    sys.exit(1)

if DATABASE_URL is None:
    logging.error("Database URL is not set!")
    sys.exit(1)

if DEVELOPER_CHAT_ID is None:
    logging.warning("Developer chat ID is not set!")


# INITIALIZE DB AND CREATE TABLES IF THEY DON'T EXIST
kipubot.db._init_db(DATABASE_URL)  # pylint: disable=protected-access

# CHECK/CREATE DATA DIRECTORY
if not os.path.exists("data"):
    logging.info("Creating ./data/ directory...")
    os.mkdir("data")

__all__ = ("BOT_TOKEN", "DATABASE_URL", "DEVELOPER_CHAT_ID")
