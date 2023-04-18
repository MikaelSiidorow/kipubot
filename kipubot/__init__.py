"""Kipubot - A Telegram bot for graphing friday raffles."""

import logging
from pathlib import Path

from pydantic import BaseSettings

# LOGGING CONFIG
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
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


logging.info("Creating ./data/ directory... ")
Path("data").mkdir(exist_ok=True)

__all__ = ("config",)
