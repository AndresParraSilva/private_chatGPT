import sqlite3
import streamlit as st
from openai import OpenAI, OpenAIError
from os import path
# from streamlit_extras.stylable_container import stylable_container
from streamlit_option_menu import option_menu

# ToDo:
# Add threads table:
#   thread_id
#   thread_title
#   last_use
#   message_ids LIST (TEXT with ','.join(map(str, messages)))
# Edit messages table:
#   message_id
#   role
#   content
# Add templates table:
#   template_id
#   
@st.cache_resource
def get_client():
    return OpenAI()

@st.cache_resource
def get_conn_cursor():
    db_exist = path.isfile('chats.db')
    conn = sqlite3.connect('chats.db', check_same_thread=False)
    cursor = conn.cursor()
    if not db_exist:
        last_thread = 0
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chats (
                id INTEGER PRIMARY KEY,
                thread INTEGER,
                role TEXT,
                content TEXT
            )
        ''')
        cursor.execute('INSERT INTO chats (thread, role, content) VALUES(0, "system", "You are a helpful assistant.");')
        cursor.execute('INSERT INTO chats (thread, role, content) VALUES(0, "user", "Who won the world series in 2020?");')
        cursor.execute('INSERT INTO chats (thread, role, content) VALUES(0, "assistant", "The Los Angeles Dodgers won the World Series in 2020.");')
        cursor.execute('INSERT INTO chats (thread, role, content) VALUES(0, "user", "Where was it played?");')
        conn.commit()
    return conn

st.header("Private chat (GPT-4 Turbo)")
conn = get_conn_cursor()
cursor = conn.cursor()
threads = cursor.execute("SELECT DISTINCT thread FROM chats ORDER BY thread DESC").fetchall()
# last_thread = cursor.execute("SELECT MAX(thread) AS max_thread FROM chats").fetchone()[0]
current_thread = last_thread = threads[0][0]

# def set_thread(t):
#     global current_thread
#     # st.write(f"Thread changed from {current_thread} to {t}")
#     current_thread = t

# for thread in threads:
#     c1, c2, c3 = st.sidebar.columns([.7, .15, .15])
#     with c1:
#         # if st.button(f"Thread {thread[0]}", type=("primary" if thread[0] == current_thread else "secondary"), key="thread" + str(thread[0]), use_container_width=True):
#         # if st.button(f"{':green[X ' if thread[0] == current_thread else ''}Thread {thread[0]}{']' if thread[0] == current_thread else ''}", key="thread" + str(thread[0]), use_container_width=True):
#         if st.checkbox(f"{':red[' if thread[0] == current_thread else ''}Thread {thread[0]}{']' if thread[0] == current_thread else ''}", key="thread" + str(thread[0])):
#             set_thread(thread[0])
#     with c2:
#         if st.button(":writing_hand:", key="edit_thread_name" + str(thread[0])):
#             pass
#     with c3:
#         if st.button(":wastebasket:", key="delete_thread" + str(thread[0])):
#             pass
thread_list = [t[0] for t in threads]
with st.sidebar:
    selected = option_menu("Conversations", thread_list, 
        icons=['eye'] * len(threads), menu_icon="cast", default_index=0)
# st.sidebar.selectbox("Thread", threads)
current_thread = threads[selected][0]

st.write(f"Current thread: {current_thread}")

messages = cursor.execute("""
    SELECT id, role, content
    FROM chats
    WHERE thread = ?
    ORDER BY id;""", (current_thread, )).fetchall()
# messages=[
#     {"role": "system", "content": "You are a helpful assistant."},
#     {"role": "user", "content": "Who won the world series in 2020?"},
#     {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
#     {"role": "user", "content": "Where was it played?"}
#     ]
len_messages = len(messages)
texts = [""] * (len_messages + 1)
roles = [""] * (len_messages + 1)
i = 0
count = 0
for message in messages:
    # print(message)
    c1, c2 = st.columns([.8, .2])
    show_message = False
    with c1:
        if st.checkbox(message[1], key="role" + str(i), value=True):
            show_message = True
            count += 1
            roles[i] = message[1]
            # with stylable_container(
            #     key="right_toggle",
            #     css_styles="""
            #         row-widget stCheckbox {
            #             margin-left: auto; 
            #             margin-right: 0;
            #         }
            #         """,
            #     ):
            with c2:
                edit_message = st.toggle('Edit', key="edit" + str(i))
    
    if show_message:
        if edit_message:
            texts[i] = st.text_area("", key="content" + str(i), value=message[2])
        else:
            texts[i] = message[2]
            show_message = st.chat_message(message[1])
            show_message.write(message[2])
    st.markdown("""---""")
    i += 1
# len_messages = i

# if st.checkbox("New prompt", key="role" + str(i), value=True):
roles[i] = "user"
texts[i] = st.text_area("New prompt", key="content" + str(i))

    # prompt = st.text_input("Prompt")

submit = st.button("Submit")

if submit:
    if count < len_messages:
        save_thread = last_thread + 1
    else:
        save_thread = current_thread
    st.write("Calling API with:")
    new_message_list = []
    for i in range(len_messages + 1):
        if texts[i]:
            st.write(f'role: {roles[i]}')
            st.write(f"content: {texts[i]}")
            new_message_list.append({"role": roles[i], "content": texts[i]})
            if count < len_messages or i == len_messages: # Modified thread or new prompt
                cursor.execute('INSERT INTO chats (thread, role, content) VALUES(?, ?, ?);', (save_thread, roles[i], texts[i]))

    st.write("Calling OpenAI API")

    client = get_client()

    try:
        completion = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=new_message_list
        )

        st.subheader("Answer")
        answer = completion.choices[0].message.content
        cursor.execute('INSERT INTO chats (thread, role, content) VALUES(?, ?, ?);', (save_thread, "assistant", answer))
        answer_message = st.chat_message("assistant")
        answer_message.write(answer)
        current_thread = save_thread

    except OpenAIError as e:
        # print(e.http_status)
        print(e.error)
    
    finally:
        conn.commit()
        