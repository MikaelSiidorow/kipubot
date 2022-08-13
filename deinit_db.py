#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg
from kipubot import DATABASE_URL

CON = psycopg.connect(DATABASE_URL)

try:
    CON.execute('''DROP TABLE raffle''')

    CON.execute('''DROP TABLE in_chat''')

    CON.execute('''DROP TABLE chat_user''')

    CON.execute('''DROP TABLE chat''')
except psycopg.errors.UndefinedTable as e:
    print('Tables already removed!')
    CON.rollback()
else:
    print('Dropped all tables!')
    CON.commit()
finally:
    CON.close()
