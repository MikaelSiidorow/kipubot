"""Kipubot - A Telegram bot for graphing friday raffles."""

import logging
import os

from pydantic import BaseSettings

# LOGGING CONFIG
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


# ENV CONFIG
class Settings(BaseSettings):
    """Configuration for the bot."""

    BOT_TOKEN: str
    DATABASE_URL: str
    DEVELOPER_CHAT_ID: str | None = None

    class Config:
        """Environment variables to load from."""

        env_file = ".env"
        env_file_encoding = "utf-8"


config = Settings()


# CHECK/CREATE DATA DIRECTORY
if not os.path.exists("data"):
    logging.info("Creating ./data/ directory...")
    os.mkdir("data")

__all__ = ("config",)
