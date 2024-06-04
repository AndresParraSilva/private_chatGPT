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
    conn.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY,
                role TEXT,
                content TEXT,
                model TEXT,
                temperature FLOAT,
                edited BOOLEAN,
                created TIMESTAMP
            )
        ''')
    conn.execute('INSERT INTO messages (role, content, created, model, temperature, edited) VALUES ("system", "You are a helpful assistant.", NULL, NULL, NULL, ?);', (datetime.now(),))
    conn.execute('INSERT INTO messages (role, content, created, model, temperature, edited) VALUES ("user", "Who won the world series in 2020?", NULL, NULL, NULL, ?);', (datetime.now(),))
    conn.execute('INSERT INTO messages (role, content, created, model, temperature, edited) VALUES ("assistant", "The Los Angeles Dodgers won the World Series in 2020.", "gpt-4o", 1.0, FALSE, ?);', (datetime.now(),))
    conn.execute('''
            CREATE TABLE IF NOT EXISTS threads (
                thread_id INTEGER PRIMARY KEY,
                title TEXT,
                messages TEXT,
                created TIMESTAMP,
                last_use TIMESTAMP
            )
        ''')
    cursor = conn.cursor()
    first_messages = cursor.execute("SELECT message_id FROM messages ORDER BY message_id LIMIT 3").fetchall()
    message_list = ','.join(map(str, [row[0] for row in first_messages]))
    conn.execute('INSERT INTO threads (title, messages, created, last_use) VALUES ("Example", ?, ?, ?);', (message_list, datetime.now(), datetime.now()))
    conn.commit()


def db_get_threads(conn):
    cursor = conn.cursor()
    return cursor.execute("SELECT thread_id, title, messages FROM threads ORDER BY last_use DESC").fetchall()


def db_get_messages(id_list, conn):
    cursor = conn.cursor()
    return cursor.execute(f"""
        SELECT message_id, role, content, model, temperature, edited
        FROM messages
        WHERE message_id IN ({','.join(["?"] * len(id_list))})
        ORDER BY created;""", (*id_list, )).fetchall()


def db_insert_message(role, content, model, temperature, edited, created, conn):
    cursor = conn.cursor()
    cursor.execute('INSERT INTO messages (role, content, model, temperature, edited, created) VALUES (?, ?, ?, ?, ?, ?);', (role, content, model, temperature, edited, created))
    conn.commit()
    return cursor.lastrowid


def db_update_thread(messages, last_use, thread_id, conn):
    conn.execute('UPDATE threads SET messages=?, last_use=? WHERE thread_id = ?;', (messages, last_use, thread_id))
    conn.commit()


def db_insert_thread(title, messages, created, last_use, conn):
    conn.execute('INSERT INTO threads (title, messages, created, last_use) VALUES (?, ?, ?, ?);', (title, messages, created, last_use))
    conn.commit()


def db_get_titles_like(search, conn):
    cursor = conn.cursor()
    return cursor.execute("SELECT title FROM threads WHERE title LIKE ?;", (search + '%', )).fetchall()


def db_update_title(title, last_use, thread_id, conn):
    conn.execute("UPDATE threads SET title = ?, last_use = ? WHERE thread_id = ?", (title, last_use, thread_id))
    conn.commit()


def db_delete_thread(thread_id, conn):  
    conn.execute("""
        DELETE FROM messages
        WHERE message_id IN (
            SELECT m.message_id
            FROM messages m
                INNER JOIN threads t1 ON ',' || t1.messages || ',' LIKE '%,' || m.message_id || ',%'
                LEFT JOIN threads t2 ON t2.thread_id <> ? AND ',' || t2.messages || ',' LIKE '%,' || m.message_id || ',%'
            WHERE t1.thread_id = ?
                AND t2.thread_id IS NULL);""", (thread_id, thread_id))
    conn.execute('DELETE FROM threads WHERE thread_id = ?;', (thread_id, ))
    conn.commit()
