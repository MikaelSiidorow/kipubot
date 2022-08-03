#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os

if not os.path.exists('data'):
    os.mkdir('data')

con = sqlite3.connect('data/.db')
cur = con.cursor()

try:
    cur.execute('''CREATE TABLE chat(
                    chat_id INTEGER PRIMARY KEY,
                    title TEXT,
                    admin INTEGER,
                    prev_winner INTEGER,
                    cur_winner INTEGER
                  )''')

    cur.execute('''CREATE TABLE user(
                    user_id INTEGER PRIMARY KEY,
                    username TEXT
                  )''')

    cur.execute('''CREATE TABLE in_chat(
                    user_id INTEGER REFERENCES users(user_id),
                    chat_id INTEGER REFERENCES chats(chat_id),
                    PRIMARY KEY (user_id, chat_id)
                  )''')

    cur.execute('''CREATE TABLE raffle(
                    chat_id INTEGER PRIMARY KEY REFERENCES chats(chat_id),
                    start_date TEXT CHECK (start_date IS datetime(start_date)),
                    end_date TEXT CHECK (end_date IS datetime(end_date)),
                    entry_fee INTEGER
                  )''')

    con.commit()
except sqlite3.OperationalError as e:
    print('Tables already setup!')

con.close()
