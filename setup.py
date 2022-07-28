import sqlite3

con = sqlite3.connect('data/.db')
cur = con.cursor()

try:
    cur.execute('''CREATE TABLE chats(
                    chat_id INTEGER PRIMARY KEY,
                    title TEXT,
                    admin INTEGER,
                    prev_winner INTEGER,
                    cur_winner INTEGER
                  )''')

    cur.execute('''CREATE TABLE users(
                    user_id INTEGER PRIMARY KEY,
                    username TEXT
                  )''')

    cur.execute('''CREATE TABLE in_chat(
                    user_id INTEGER REFERENCES users(user_id),
                    chat_id INTEGER REFERENCES chats(chat_id),
                    PRIMARY KEY (user_id, chat_id)
                  )''')
    con.commit()
except sqlite3.OperationalError as e:
    print('Tables already setup!')

con.close()
