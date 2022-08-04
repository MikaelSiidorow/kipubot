#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg
from kipubot.config import DATABASE_URL

CON = psycopg.connect(DATABASE_URL)

try:
    CON.execute('''CREATE TABLE chat (
                    chat_id BIGINT PRIMARY KEY,
                    title VARCHAR(128),
                    admin INTEGER,
                    prev_winner INTEGER,
                    cur_winner INTEGER
                  )''')

    CON.execute('''CREATE TABLE chat_user (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(32)
                  )''')

    CON.execute('''CREATE TABLE in_chat (
                    user_id BIGINT REFERENCES chat_user(user_id),
                    chat_id BIGINT REFERENCES chat(chat_id),
                    PRIMARY KEY (user_id, chat_id)
                  )''')

    CON.execute('''CREATE TABLE raffle (
                    chat_id BIGINT PRIMARY KEY REFERENCES chat(chat_id),
                    start_date TIMESTAMP,
                    end_date TIMESTAMP,
                    entry_fee INTEGER
                  )''')
except psycopg.errors.DuplicateTable as e:
    print('Tables already setup!')
    CON.rollback()
else:
    print('Setup tables!')
    CON.commit()
finally:
    CON.close()
