import sqlite3
import streamlit as st
from datetime import datetime
from os import path


@st.cache_resource
def db_get_connection():
    db_exist = path.isfile('chats.db')
    conn = sqlite3.connect('chats.db', check_same_thread=False)
    if not db_exist:
        db_setup(conn)
    return conn


def db_setup(conn):
    cursor = conn.cursor()
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY,
                role TEXT,
                content TEXT,
                created TIMESTAMP
            )
        ''')
    cursor.execute('INSERT INTO messages (role, content, created) VALUES ("system", "You are a helpful assistant.", ?);', (datetime.now(),))
    cursor.execute('INSERT INTO messages (role, content, created) VALUES ("user", "Who won the world series in 2020?", ?);', (datetime.now(),))
    cursor.execute('INSERT INTO messages (role, content, created) VALUES ("assistant", "The Los Angeles Dodgers won the World Series in 2020.", ?);', (datetime.now(),))
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS threads (
                thread_id INTEGER PRIMARY KEY,
                title TEXT,
                messages TEXT,
                created TIMESTAMP,
                last_use TIMESTAMP
            )
        ''')
    first_messages = cursor.execute("SELECT message_id FROM messages ORDER BY message_id LIMIT 3").fetchall()
    message_list = ','.join(map(str, [row[0] for row in first_messages]))
    cursor.execute('INSERT INTO threads (title, messages, created, last_use) VALUES ("Example", ?, ?, ?);', (message_list, datetime.now(), datetime.now()))
    conn.commit()


def db_get_threads(conn):
    cursor = conn.cursor()
    return cursor.execute("SELECT thread_id, title, messages FROM threads ORDER BY last_use DESC").fetchall()


def db_get_messages(id_list, conn):
    cursor = conn.cursor()
    return cursor.execute(f"""
        SELECT message_id, role, content
        FROM messages
        WHERE message_id IN ({','.join(["?"] * len(id_list))});""", (*id_list, )).fetchall()


def db_insert_message(role, content, created, conn):
    cursor = conn.cursor()
    cursor.execute('INSERT INTO messages (role, content, created) VALUES (?, ?, ?);', (role, content, created))
    conn.commit()
    return cursor.lastrowid


def db_update_thread(messages, last_use, thread_id, conn):
    cursor = conn.cursor()
    cursor.execute('UPDATE threads SET messages=?, last_use=? WHERE thread_id = ?;', (messages, last_use, thread_id))
    conn.commit()


def db_insert_thread(title, messages, created, last_use, conn):
    cursor = conn.cursor()
    cursor.execute('INSERT INTO threads (title, messages, created, last_use) VALUES (?, ?, ?, ?);', (title, messages, created, last_use))
    conn.commit()


def db_get_titles_like(search, conn):
    cursor = conn.cursor()
    return cursor.execute("SELECT title FROM threads WHERE title LIKE ?;", (search + '%', )).fetchall()


def db_update_title(title, last_use, thread_id, conn):
    cursor = conn.cursor()
    cursor.execute("UPDATE threads SET title = ?, last_use = ? WHERE thread_id = ?", (title, last_use, thread_id))
    conn.commit()


def db_delete_thread(thread_id, conn):
    cursor = conn.cursor()
    cursor.execute('DELETE FROM threads WHERE thread_id = ?;', (thread_id, ))
    # ToDo: Delete orphan messages from `messages` table.
    conn.commit()
