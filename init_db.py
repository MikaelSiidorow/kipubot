#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg
from kipubot import get_con

CON = get_con()

try:
    CON.execute('''CREATE TABLE chat (
                    chat_id BIGINT PRIMARY KEY,
                    title VARCHAR(128),
                    admins BIGINT[],
                    prev_winners BIGINT[],
                    cur_winner BIGINT
                  )''')

    CON.execute('''CREATE TABLE chat_user (
                    user_id BIGINT PRIMARY KEY
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
                    entry_fee INTEGER,
                    dates TIMESTAMP[],
                    entries VARCHAR(128)[],
                    amounts INTEGER[]
                  )''')
except psycopg.errors.DuplicateTable as e:
    print('Tables already setup!')
    CON.rollback()
else:
    print('Setup tables!')
    CON.commit()
finally:
    CON.close()
