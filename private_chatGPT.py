from datetime import datetime, time
import time
import re
import sqlite3
import streamlit as st
from openai import OpenAI, OpenAIError
from os import path
# from streamlit_extras.stylable_container import stylable_container
from streamlit_option_menu import option_menu
from streamlit_js_eval import streamlit_js_eval

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
# Reset checkbox when changing thread
# Rename and Delete buttons (for threads)
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


def get_new_thread_title(old_title):
    numbers = re.compile(r'\((\d+)\)$')  # Matches a number between parenthesis at the end of the string
    match_old = numbers.search(old_title)
    if match_old:
        search = old_title[:match_old.start()]
    else:
        search = old_title
    existing = cursor.execute("SELECT title FROM threads WHERE title LIKE ?;", (search + '%', )).fetchall()
    if len(existing) == 0:
        return old_title
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


def change_title():
    new_title = st.session_state.new_title_text.strip()
    # st.write("You entered: ", new_title)
    # time.sleep(1)
    old_title = threads[current_thread_index][1].strip()
    if new_title != old_title:
        unique_new_title = get_new_thread_title(new_title)
        cursor.execute("UPDATE threads SET title = ?, last_use = ? WHERE thread_id = ?", (unique_new_title, datetime.now(), current_thread_id))
        conn.commit()
        # threads = cursor.execute("SELECT thread_id, title, messages FROM threads ORDER BY last_use DESC").fetchall()
        # thread_list = [t[1] for t in threads]
    else:
        st.write("Same name")


def delete_thread_confirmed():
    cursor.execute('DELETE FROM threads WHERE thread_id = ?;', (current_thread_id, ))
    # ToDo: Delete orphan messages from messages table.
    conn.commit()


st.header("Private chatGPT (GPT-4 Turbo)")
conn = get_conn_cursor()
cursor = conn.cursor()
threads = cursor.execute("SELECT thread_id, title, messages FROM threads ORDER BY last_use DESC").fetchall()
# last_thread = cursor.execute("SELECT MAX(thread_id) FROM threads ORDER BY thread_id DESC").fetchone()[0]

thread_list = [t[1] for t in threads]
with st.sidebar:
    selected = option_menu("Threads", thread_list, 
        icons=["chat-right"] * len(threads), default_index=0)

current_thread_index = thread_list.index(selected)
current_thread_id = threads[current_thread_index][0]
c1, c2, c3, c4 = st.columns([.82, .06, .06, .06])
with c2:
    if st.button(":floppy_disk:", help="Save as template"):
        pass
with c3:
    edit_title = st.button(":writing_hand:", help="Edit title")
with c4:
    delete_thread = st.button(":wastebasket:", help="Delete thread")
with c1:
    if edit_title:
        st.text_input("Edit", value=threads[current_thread_index][1], on_change=change_title, key="new_title_text")
    else:
        st.subheader(threads[current_thread_index][1])

if delete_thread:
    c1, c2, c3 = st.columns([.6, .2, .2])
    with c1:
        st.subheader(f"Confirm deletion of the thread {current_thread_id}?")
    with c2:
        st.button("Delete", on_click=delete_thread_confirmed, use_container_width=True)
    with c3:
        st.button("Cancel", use_container_width=True)

# st.markdown("""---""")
# current_datetime = datetime.now()
# st.write("Page refreshed at:", current_datetime.strftime("%A, %B %d, %Y %H:%M:%S"))

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
for i in range(len_messages):
    # if "check" + str(i) not in st.session_state:
    #     st.session_state["check" + str(i)] = True
    #     st.session_state["edit" + str(i)] = False

    id = id_list[i]
    if message_data[id][0] == "user":
        st.markdown("""---""")
    c1, c2 = st.columns([.8, .2])
    roles[i] =message_data[id][0]
    with c1:
        if message_data[id][0] == "assistant":
            show_message = st.session_state["check" + str(i - 1)]
            # st.write("assistant")
            st.checkbox(message_data[id][0], key="check" + str(i), value=show_message, disabled=True)
        else:
            show_message = st.checkbox(message_data[id][0], key="check" + str(i), value=True)
    if show_message:
        with c2:
            edit_message = st.toggle('Edit', key="edit" + str(i))
        if edit_message:
            texts[i] = st.text_area("content", label_visibility="hidden", key="content" + str(i), value=message_data[id][1])
        else:
            texts[i] = message_data[id][1]
            show_message = st.chat_message(message_data[id][0])
            show_message.write(message_data[id][1])

roles[len_messages] = "user"
texts[len_messages] = st.chat_input("What? When? Where? Why? Who? Whom? Whose? Which? How?")  # st.text_area("New prompt", key="content" + str(len_messages))

if texts[len_messages]:  # st.button("Submit", disabled = texts[len_messages] == ""):
    st.markdown("""---""")
    c1, c2 = st.columns([.8, .2])
    show_message = False
    with c1:
        if st.checkbox(roles[len_messages], key="check" + str(len_messages), value=True):
            show_message = True
            with c2:
                edit_message = st.toggle('Edit', key="edit" + str(len_messages))
    if show_message:
        if edit_message:
            texts[len_messages] = st.text_area("content", label_visibility="hidden", key="content" + str(i), value=texts[len_messages])
        else:
            show_message = st.chat_message(roles[len_messages])
            show_message.write(texts[len_messages])
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
    # st.write(f"Calling API with (same_thread={same_thread}):")
    new_message_list = []
    new_id_list = []
    for i in range(len_messages + 1):
        if texts[i]:
            # st.write(f'role: {roles[i]}')
            # st.write(f"content: {texts[i]}")
            new_message_list.append({"role": roles[i], "content": texts[i]})
            if i == len_messages or texts[i] != message_data[id_list[i]][1]: # New prompt or modified thread
                cursor.execute('INSERT INTO messages (role, content, created) VALUES (?, ?, ?);', (roles[i], texts[i], datetime.now()))
                new_id_list.append(cursor.lastrowid)
            else:
                new_id_list.append(id_list[i])
    # st.write(new_id_list)
    # st.write("Calling OpenAI API")

    client = get_client()

    try:
        # completion = client.chat.completions.create(
        #     model="gpt-4-turbo",
        #     messages=new_message_list
        # )

        # st.subheader("Answer")
        # if edit_message:
        #     edited_answer = st.text_area("content", label_visibility="hidden", key="content" + str(len_messages + 1), value=???)
        # else:
        c1, c2 = st.columns([.8, .2])
        show_message = False
        with c1:
            if st.checkbox("assistant", key="check" + str(len_messages+1), value=True):
                show_message = True
                with c2:
                    st.toggle('Edit', key="edit" + str(len_messages+1))  #, disabled=True)
        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model="gpt-4-turbo",  # st.session_state["openai_model"],
                messages=new_message_list,
                stream=True
            )
            answer = st.write_stream(stream)
        # answer = completion.choices[0].message.content
        cursor.execute('INSERT INTO messages (role, content, created) VALUES (?, ?, ?);', ("assistant", answer, datetime.now()))
        new_id_list.append(cursor.lastrowid)
        if same_thread:
            cursor.execute('UPDATE threads SET messages=?, last_use=? WHERE thread_id = ?;', (','.join(map(str, new_id_list)), datetime.now(), current_thread_id))
        else:
            cursor.execute('INSERT INTO threads (title, messages, created, last_use) VALUES (?, ?, ?, ?);', (get_new_thread_title(threads[current_thread_index][1]), ','.join(map(str, new_id_list)), datetime.now(), datetime.now()))
            for i in range(len_messages):
                del st.session_state["check" + str(i)]
                if "edit" + str(i) in st.session_state:
                    del st.session_state["edit" + str(i)]
            streamlit_js_eval(js_expressions="parent.window.location.reload()")
        # answer_message = st.chat_message("assistant")
        # answer_message.write(answer)
        # current_thread_index = save_thread

    except OpenAIError as e:
        # print(e.http_status)
        print(e.error)
    
    finally:
        conn.commit()
        