from typing import Tuple, List, Optional
from pandas import Timestamp, DataFrame
import psycopg
import psycopg.errors as PSErrors
from kipubot.errors import AlreadyRegisteredError

# STORE DB CONNECTION
_CON: Optional[psycopg.Connection] = None


def _init_db(url: str) -> None:
    global _CON  # pylint: disable=global-statement

    if not _CON:
        print('Connecting to DB...')
        _CON = psycopg.connect(url)
        print('Connected!')

    print('Initializing database...')
    try:
        _CON.execute('''CREATE TABLE IF NOT EXISTS chat (
                        chat_id BIGINT PRIMARY KEY,
                        title VARCHAR(128),
                        admins BIGINT[],
                        prev_winners BIGINT[],
                        cur_winner BIGINT
                    )''')

        _CON.execute('''CREATE TABLE IF NOT EXISTS chat_user (
                        user_id BIGINT PRIMARY KEY
                    )''')

        _CON.execute('''CREATE TABLE IF NOT EXISTS in_chat (
                        user_id BIGINT REFERENCES chat_user(user_id),
                        chat_id BIGINT REFERENCES chat(chat_id),
                        PRIMARY KEY (user_id, chat_id)
                    )''')

        _CON.execute('''CREATE TABLE IF NOT EXISTS raffle (
                        chat_id BIGINT PRIMARY KEY REFERENCES chat(chat_id),
                        start_date TIMESTAMP,
                        end_date TIMESTAMP,
                        entry_fee INTEGER,
                        dates TIMESTAMP[],
                        entries VARCHAR(128)[],
                        amounts INTEGER[]
                    )''')
    except PSErrors.Error as e:
        print('Unknown error during database initialization:')
        print(e)
        _CON.rollback()
    else:
        print('Database succesfully initialized!')
        _CON.commit()


def get_registered_member_ids(chat_id: int) -> List[int]:
    return [row[0] for row in _CON.execute(
        '''SELECT chat_user.user_id
            FROM chat_user, in_chat
            WHERE chat_id = %s AND chat_user.user_id = in_chat.user_id''', (chat_id,)).fetchall()]


def get_admin_ids(chat_id: int) -> List[int]:
    return (_CON.execute(
        'SELECT admins FROM chat WHERE chat_id = %s', (chat_id,))
        .fetchone()[0])


def get_prev_winner_ids(chat_id: int) -> List[int]:
    return (_CON.execute(
        'SELECT prev_winners FROM chat WHERE chat_id = %s', (chat_id,))
        .fetchone()[0])


def get_winner_id(chat_id: int) -> int:
    return (_CON.execute(
        'SELECT cur_winner FROM chat WHERE chat_id = %s', (chat_id,))
        .fetchone()[0])


def get_chats_where_winner(user_id: int) -> List[Tuple[int, str]]:
    return _CON.execute(
        '''SELECT c.chat_id, c.title
            FROM chat AS c, in_chat as i
            WHERE i.user_id = %(id)s
                AND c.chat_id = i.chat_id
                AND (c.cur_winner = %(id)s)''',
        {'id': user_id}).fetchall()


def get_raffle_data(chat_id: int) -> Tuple[
        int, Timestamp, Timestamp, int,
        List[Timestamp], List[str], List[int]]:
    return _CON.execute(
        'SELECT * FROM raffle WHERE chat_id = %s', [chat_id]).fetchone()


def save_raffle_data(chat_id: int,
                     start_date: Timestamp,
                     end_date: Timestamp,
                     entry_fee: int,
                     df: DataFrame) -> None:

    dates = df['date'].tolist()
    entries = df['name'].tolist()
    amounts = df['amount'].tolist()

    _CON.execute('''INSERT INTO raffle
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (chat_id)
                    DO UPDATE SET 
                        start_date = EXCLUDED.start_date,
                        end_date = EXCLUDED.end_date,
                        entry_fee = EXCLUDED.entry_fee,
                        dates = EXCLUDED.dates,
                        entries = EXCLUDED.entries,
                        amounts = EXCLUDED.amounts''',
                 (chat_id, start_date, end_date, entry_fee, dates, entries, amounts))

    _CON.commit()


def save_user_or_ignore(user_id: int) -> None:
    _CON.execute('''INSERT INTO chat_user
                VALUES (%s)
                ON CONFLICT (user_id)
                DO NOTHING''',
                 (user_id,))

    _CON.commit()


def save_chat_or_ignore(chat_id: int, title: str, admin_ids: List[int]) -> None:
    _CON.execute('''INSERT INTO chat (chat_id, title, admins)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (chat_id)
                            DO NOTHING''',
                 (chat_id, title, admin_ids))
    _CON.commit()


def register_user(chat_id: int, user_id: int) -> None:

    save_user_or_ignore(user_id)

    try:
        _CON.execute('''INSERT INTO in_chat(user_id, chat_id)
                            VALUES (%s, %s)''',
                     (user_id, chat_id))
    except PSErrors.UniqueViolation as e:
        _CON.rollback()
        raise AlreadyRegisteredError from e
    else:
        _CON.commit()


def register_user_or_ignore(chat_id: int, user_id: int) -> None:
    try:
        register_user(chat_id, user_id)
    except AlreadyRegisteredError:
        pass


def admin_cycle_winners(winner_id: int, chat_id: int) -> None:
    _CON.execute('''UPDATE chat
                            SET prev_winners = array_append(prev_winners, cur_winner),
                                cur_winner=%s
                            WHERE chat_id=%s''',
                 (winner_id, chat_id))
    _CON.commit()


def replace_cur_winner(winner_id: int, chat_id: int) -> None:
    _CON.execute('''UPDATE chat
                            SET cur_winner=%s
                            WHERE chat_id=%s''',
                 (winner_id, chat_id))
    _CON.commit()


def cycle_winners(user_id: int, winner_id: int, chat_id: int) -> None:
    _CON.execute('''UPDATE chat
                            SET prev_winners=array_append(prev_winners, %s),
                                cur_winner=%s'
                            WHERE chat_id=%s''',
                 (user_id, winner_id, chat_id))
    _CON.commit()
