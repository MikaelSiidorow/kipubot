"""Database connection and queries for Kipubot."""

import logging
from contextlib import contextmanager, suppress

import psycopg.errors as pserrors
from pandas import Timestamp
from psycopg_pool import ConnectionPool

from kipubot import config
from kipubot.errors import AlreadyRegisteredError
from kipubot.utils import RaffleData

_pool = ConnectionPool(
    config.DATABASE_URL,
)

_logger = logging.getLogger(__name__)


@contextmanager
def logging_connection():
    """Log errors while connecting to the database."""
    try:
        _logger.info("Getting db connection...")
        with _pool.connection() as conn:
            yield conn
    except Exception:
        _logger.exception("Error while getting connection!")
    else:
        _logger.info("Connection to database successful!")
    finally:
        _logger.info("Freeing database connection...")


def init_db():
    """Initialize the database tables if they don't exist."""
    with logging_connection() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS chat (
                        chat_id BIGINT PRIMARY KEY,
                        title VARCHAR(128),
                        admins BIGINT[],
                        prev_winners BIGINT[],
                        cur_winner BIGINT
                    )"""
        )

        conn.execute(
            """CREATE TABLE IF NOT EXISTS chat_user (
                        user_id BIGINT PRIMARY KEY
                    )"""
        )

        conn.execute(
            """CREATE TABLE IF NOT EXISTS in_chat (
                        user_id BIGINT REFERENCES chat_user(user_id),
                        chat_id BIGINT REFERENCES chat(chat_id),
                        PRIMARY KEY (user_id, chat_id)
                    )"""
        )

        conn.execute(
            """CREATE TABLE IF NOT EXISTS raffle (
                        raffle_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        start_date TIMESTAMP,
                        end_date TIMESTAMP,
                        active BOOLEAN DEFAULT TRUE,
                        entry_fee INTEGER,
                        dates TIMESTAMP[],
                        entries VARCHAR(128)[],
                        amounts INTEGER[],
                        chat_id BIGINT REFERENCES chat(chat_id),
                        user_id BIGINT REFERENCES chat_user(user_id)

                    )"""
        )

        conn.execute(
            """CREATE INDEX IF NOT EXISTS raffle_chat_id_idx ON raffle (chat_id)"""
        )

        conn.execute(
            """CREATE UNIQUE INDEX IF NOT EXISTS raffle_chat_id_active
                ON raffle (chat_id) WHERE active = TRUE"""
        )


def get_registered_member_ids(chat_id: int) -> list[int]:
    """Get a list of all registered user IDs in a chat."""
    with logging_connection() as conn:
        return [
            row[0]
            for row in conn.execute(
                """SELECT chat_user.user_id
                FROM chat_user, in_chat
                WHERE chat_id = %s AND chat_user.user_id = in_chat.user_id""",
                (chat_id,),
            ).fetchall()
        ]


def get_admin_ids(chat_id: int) -> list[int]:
    """Get a list of all admin IDs in a chat."""
    with logging_connection() as conn:
        data = conn.execute(
            "SELECT admins FROM chat WHERE chat_id = %s", (chat_id,)
        ).fetchone()
        return data[0] if data else []


def get_prev_winner_ids(chat_id: int) -> list[int]:
    """Get a list of all previous winner IDs in a chat."""
    with logging_connection() as conn:
        data = conn.execute(
            "SELECT prev_winners FROM chat WHERE chat_id = %s", (chat_id,)
        ).fetchone()
        return data[0] if data else []


def get_winner_id(chat_id: int) -> int:
    """Get the current winner ID in a chat."""
    with logging_connection() as conn:
        data = conn.execute(
            "SELECT cur_winner FROM chat WHERE chat_id = %s", (chat_id,)
        ).fetchone()
        return data[0] if data else None


def get_chats_where_winner(user_id: int) -> list[tuple[int, str]]:
    """Get a list of all chats where a user is the current winner."""
    with logging_connection() as conn:
        return conn.execute(
            """SELECT c.chat_id, c.title
                FROM chat AS c, in_chat as i
                WHERE i.user_id = %(id)s
                    AND c.chat_id = i.chat_id
                    AND (c.cur_winner = %(id)s)""",
            {"id": user_id},
        ).fetchall()


def get_raffle_data(
    chat_id: int,
) -> tuple[
    str,
    Timestamp,
    Timestamp,
    bool,
    int,
    list[Timestamp],
    list[str],
    list[int],
    int,
    int,
]:
    """Get the raffle data for a chat.

    Returns
    -------
        Tuple of the raffle_id, chat_id, start date, end date,
        entry fee, dates, entries, and amounts.
    """
    with logging_connection() as conn:
        return conn.execute(
            """SELECT * FROM raffle WHERE chat_id = %s AND active = true""",
            [chat_id],
        ).fetchone()


def save_raffle_data(
    chat_id: int,
    user_id: int,
    raffle_data: RaffleData,
) -> None:
    """Save the raffle data for a chat."""
    start_date, end_date, entry_fee, df = raffle_data
    dates = df["date"].tolist()
    entries = df["name"].tolist()
    amounts = df["amount"].tolist()

    with logging_connection() as conn:
        conn.execute(
            """INSERT INTO raffle
                        (start_date, end_date, entry_fee,
                        dates, entries, amounts, chat_id, user_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                start_date,
                end_date,
                entry_fee,
                dates,
                entries,
                amounts,
                chat_id,
                user_id,
            ),
        )

        conn.commit()


def update_raffle_data(
    raffle_id: str,
    raffle_data: RaffleData,
) -> None:
    """Update the raffle data for a chat."""
    start_date, end_date, entry_fee, df = raffle_data
    dates = df["date"].tolist()
    entries = df["name"].tolist()
    amounts = df["amount"].tolist()

    with logging_connection() as conn:
        conn.execute(
            """UPDATE raffle
                SET start_date = %s,
                    end_date = %s,
                    entry_fee = %s,
                    dates = %s,
                    entries = %s,
                    amounts = %s
                WHERE raffle_id = %s""",
            (start_date, end_date, entry_fee, dates, entries, amounts, raffle_id),
        )

        conn.commit()


def close_raffle(
    chat_id: int,
) -> None:
    """Close a raffle."""
    with logging_connection() as conn:
        conn.execute(
            """UPDATE raffle
                SET active = false
                WHERE chat_id = %s AND active = true""",
            (chat_id,),
        )

        conn.commit()


def delete_raffle_data(chat_id: int):
    """Delete the raffle data for a chat."""
    with logging_connection() as conn:
        conn.execute("""DELETE FROM raffle where chat_id=%s""", (chat_id,))
        conn.commit()


def save_user_or_ignore(user_id: int) -> None:
    """Save a user to the database, or ignore if already exists."""
    with logging_connection() as conn:
        conn.execute(
            """INSERT INTO chat_user
                    VALUES (%s)
                    ON CONFLICT (user_id)
                    DO NOTHING""",
            (user_id,),
        )


def save_chat_or_ignore(chat_id: int, title: str, admin_ids: list[int]) -> None:
    """Save a chat to the database, or ignore if already exists."""
    with logging_connection() as conn:
        conn.execute(
            """INSERT INTO chat (chat_id, title, admins)
                                VALUES (%s, %s, %s)
                                ON CONFLICT (chat_id)
                                DO NOTHING""",
            (chat_id, title, admin_ids),
        )


def delete_chat(chat_id: int):
    """Delete a chat from the database."""
    with logging_connection() as conn:
        conn.execute("""DELETE FROM chat where chat_id=%s""", (chat_id,))
        conn.commit()


def register_user(chat_id: int, user_id: int) -> None:
    """Register a user in a chat."""
    save_user_or_ignore(user_id)

    with logging_connection() as conn:
        try:
            conn.execute(
                """INSERT INTO in_chat(user_id, chat_id)
                                VALUES (%s, %s)""",
                (user_id, chat_id),
            )
        except pserrors.UniqueViolation as e:
            conn.rollback()
            raise AlreadyRegisteredError from e
        else:
            conn.commit()


def register_user_or_ignore(chat_id: int, user_id: int) -> None:
    """Register a user in a chat, or ignore if already registered."""
    with suppress(AlreadyRegisteredError):
        register_user(chat_id, user_id)


def admin_cycle_winners(winner_id: int, chat_id: int) -> None:
    """Admin set current winner to a specific user.

    Move the previous winner to the list of previous winners.
    """
    with logging_connection() as conn:
        conn.execute(
            """UPDATE chat
                SET prev_winners = array_append(prev_winners, cur_winner),
                                    cur_winner=%s
                WHERE chat_id=%s""",
            (winner_id, chat_id),
        )
        conn.commit()


def replace_cur_winner(winner_id: int, chat_id: int) -> None:
    """Replace the current winner in a chat."""
    with logging_connection() as conn:
        conn.execute(
            """UPDATE chat
                                SET cur_winner=%s
                                WHERE chat_id=%s""",
            (winner_id, chat_id),
        )


def cycle_winners(user_id: int, winner_id: int, chat_id: int) -> None:
    """Set the current winner in a chat.

    Move the previous winner to the list of previous winners.
    """
    with logging_connection() as conn:
        conn.execute(
            """UPDATE chat
                                SET prev_winners=array_append(prev_winners, %s),
                                    cur_winner=%s'
                                WHERE chat_id=%s""",
            (user_id, winner_id, chat_id),
        )


if __name__ == "__main__":
    init_db()
