from datetime import datetime
import re
import sqlite3
import streamlit as st
from openai import OpenAI, OpenAIError
from os import path
# from streamlit_extras.stylable_container import stylable_container
from streamlit_option_menu import option_menu

# ToDo:
# Add threads table:
#   thread_id
#   title
#   last_use
#   message_ids LIST (TEXT with ','.join(map(str, messages)))
# Edit messages table:
#   message_id
#   role
#   content
# Add templates table:
#   template_id
# Reset checkbox when changing conversation
# Rename and Delete buttons (for conversations)
# Insert button
# Move up and Move down buttons
# Cached get_messages() function

@st.cache_resource
def get_client():
    return OpenAI()

@st.cache_resource
def get_conn_cursor():
    db_exist = path.isfile('chats.db')
    conn = sqlite3.connect('chats.db', check_same_thread=False)
    cursor = conn.cursor()
    if not db_exist:
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

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS templates (
                template_id INTEGER PRIMARY KEY,
                title TEXT,
                messages TEXT,
                created TIMESTAMP,
                last_use TIMESTAMP
            )
        ''')
        cursor.execute('INSERT INTO templates (title, messages, created, last_use) VALUES ("General", ?, ?, ?);', (str(first_messages[0][0]), datetime.now(), datetime.now()))

        conn.commit()
    return conn


def get_new_thread_name(old_name):
    numbers = re.compile(r'\((\d+)\)$')  # Matches a number between parenthesis at the end of the string
    match_old = numbers.search(old_name)
    if match_old:
        search = old_name[:match_old.start()]
    else:
        search = old_name
    existing = cursor.execute("SELECT title FROM threads WHERE title LIKE ?;", (search + '%', )).fetchall()
    if len(existing) == 0:
        return old_name
    else:
        matching_list = []
        for row in existing:
            match = numbers.search(row[0])
            if match:
                matching_list.append(int(match.group(1)))
        if matching_list:
            return f"{search.strip()} ({str(max(matching_list) + 1)})"
        else:
            return f"{search.strip()} (1)"


    

st.header("Private chatGPT (GPT-4 Turbo)")
conn = get_conn_cursor()
cursor = conn.cursor()
threads = cursor.execute("SELECT thread_id, title, messages FROM threads ORDER BY last_use DESC").fetchall()
# last_thread = cursor.execute("SELECT MAX(thread_id) FROM threads ORDER BY thread_id DESC").fetchone()[0]

thread_list = [t[1] for t in threads]
with st.sidebar:
    selected = option_menu("Conversations", thread_list, 
        icons=["chat-right"] * len(threads), default_index=0)

current_thread_index = thread_list.index(selected)
current_thread_id = threads[current_thread_index][0]
c1, c2, c3 = st.columns([.85, .075, .075])
with c1:
    st.subheader(threads[current_thread_index][1])
with c2:
    if st.button(":writing_hand:"):
        pass
with c3:
    if st.button(":wastebasket:"):
        pass
# st.markdown("""---""")

id_list = [int(id) for id in threads[current_thread_index][2].split(',')]
# st.write("id_list:", id_list)
messages = cursor.execute(f"""
    SELECT message_id, role, content
    FROM messages
    WHERE message_id IN ({','.join(["?"] * len(id_list))});""", (*id_list, )).fetchall()
message_data = dict()
for message in messages:
    message_data[message[0]] = [message[1], message[2]]

len_messages = len(messages)
texts = [""] * (len_messages + 1)
roles = [""] * (len_messages + 1)
for i in range(len(id_list)):
    id = id_list[i]
    # print(message)
    c1, c2 = st.columns([.8, .2])
    show_message = False
    with c1:
        if st.checkbox(message_data[id][0], key="check" + str(i), value=True):
            show_message = True
            roles[i] =message_data[id][0]
            with c2:
                edit_message = st.toggle('Edit', key="edit" + str(i))
    
    if show_message:
        if edit_message:
            texts[i] = st.text_area("content", label_visibility="hidden", key="content" + str(i), value=message_data[id][1])
        else:
            texts[i] = message_data[id][1]
            show_message = st.chat_message(message_data[id][0])
            show_message.write(message_data[id][1])
    st.markdown("""---""")


roles[len_messages] = "user"
texts[len_messages] = st.text_area("New prompt", key="content" + str(len_messages))

if st.button("Submit", disabled = texts[len_messages] == ""):
    same_thread = True
    for i in range(len_messages):
        # if not st.session_state["check" + str(i)]:
        #     same_thread = False
        #     break
        # st.write(f"Comparing {texts[i]} vs {message_data[id_list[i]][1]}")
        if texts[i] != message_data[id_list[i]][1]:
            same_thread = False
            break
    # if count < len_messages:
    #     save_thread = last_thread + 1
    # else:
    #     save_thread = current_thread
    st.write(f"Calling API with (same_thread={same_thread}):")
    new_message_list = []
    new_id_list = []
    for i in range(len_messages + 1):
        if texts[i]:
            st.write(f'role: {roles[i]}')
            st.write(f"content: {texts[i]}")
            new_message_list.append({"role": roles[i], "content": texts[i]})
            if i == len_messages or texts[i] != message_data[id_list[i]][1]: # New prompt or modified thread
                cursor.execute('INSERT INTO messages (role, content, created) VALUES (?, ?, ?);', (roles[i], texts[i], datetime.now()))
                new_id_list.append(cursor.lastrowid)
            else:
                new_id_list.append(id_list[i])
    st.write(new_id_list)
    st.write("Calling OpenAI API")

    client = get_client()

    try:
        completion = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=new_message_list
        )

        st.subheader("Answer")
        answer = completion.choices[0].message.content
        cursor.execute('INSERT INTO messages (role, content, created) VALUES (?, ?, ?);', ("assistant", answer, datetime.now()))
        new_id_list.append(cursor.lastrowid)
        if same_thread:
            cursor.execute('UPDATE threads SET messages=?, last_use=? WHERE thread_id = ?;', (','.join(map(str, new_id_list)), datetime.now(), current_thread_id))
        else:
            cursor.execute('INSERT INTO threads (title, messages, created, last_use) VALUES (?, ?, ?, ?);', (get_new_thread_name(threads[current_thread_index][1]), ','.join(map(str, new_id_list)), datetime.now(), datetime.now()))
        answer_message = st.chat_message("assistant")
        answer_message.write(answer)
        # current_thread_index = save_thread

    except OpenAIError as e:
        # print(e.http_status)
        print(e.error)
    
    finally:
        conn.commit()
        