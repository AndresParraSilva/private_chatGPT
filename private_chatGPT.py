import re
import streamlit as st
from datetime import datetime
from openai import OpenAIError
from os import path
from streamlit_js_eval import streamlit_js_eval
from streamlit_option_menu import option_menu

from db import *
from helpers import *


state = st.session_state

# ToDo:
# Add templates table and functionality

st.header("Private chatGPT (GPT-4 Turbo)")

# DB connection
state.conn = db_get_connection()

# Sidebar with thread list
if st.sidebar.button("New empty thread", use_container_width=True):
    new_message_id = db_insert_message("system", "You are a helpful assistant.", datetime.now(), state.conn)
    db_insert_thread(get_new_thread_title("Example", state.conn), str(new_message_id), datetime.now(), datetime.now(), state.conn)

threads = db_get_threads(state.conn)
thread_list = [t[1] for t in threads]
with st.sidebar:
    selected = option_menu("Threads", thread_list, icons=["chat-right"] * len(threads), default_index=0)
current_thread_index = thread_list.index(selected)
state.current_thread_id = threads[current_thread_index][0]

# Thread title and commands
c1, c2, c3 = st.columns([.88, .06, .06])
with c2:
    edit_title = st.button(":writing_hand:", help="Edit title")
with c3:
    delete_thread = st.button(":wastebasket:", help="Delete thread")
with c1:
    if edit_title:
        st.text_input("Edit", value=threads[current_thread_index][1], on_change=change_title, args=(state.current_thread_id, threads[current_thread_index][1].strip(), None, state.conn), key="new_title_text")
    else:
        st.subheader(threads[current_thread_index][1])

if delete_thread:
    c1, c2, c3 = st.columns([.6, .2, .2])
    with c1:
        st.subheader(f"Confirm deletion of the thread?")
    with c2:
        st.button("Delete", on_click=db_delete_thread, args=(state.current_thread_id, state.conn), use_container_width=True)
    with c3:
        st.button("Cancel", use_container_width=True)

# Messages of selected thread
id_list = [int(id) for id in threads[current_thread_index][2].split(',')]
messages = db_get_messages(id_list, state.conn)
message_data = dict()
for message in messages:
    message_data[message[0]] = [message[1], message[2]]

len_messages = len(messages)
texts = [""] * (len_messages + 1)
roles = [""] * (len_messages + 1)
for i in range(len_messages):
    id = id_list[i]
    if message_data[id][0] == "user":
        st.markdown("""---""")
    c1, c2 = st.columns([.8, .2])
    roles[i] =message_data[id][0]
    with c1:
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

# New prompt
roles[len_messages] = "user"
texts[len_messages] = st.chat_input("What? When? Where? Why? Who? Whom? Whose? Which? How?")

# Call API and get answer
if texts[len_messages]:
    st.markdown("""---""")
    c1, c2 = st.columns([.8, .2])
    with c1:
        st.checkbox(roles[len_messages], key="check" + str(len_messages), value=len(texts[len_messages].strip()) > 0)
    with c2:
        edit_message = st.toggle('Edit', key="edit" + str(len_messages))
    show_message = st.chat_message(roles[len_messages])
    show_message.write(texts[len_messages])
    same_thread = True
    for i in range(len_messages):
        if texts[i] != message_data[id_list[i]][1]:
            same_thread = False
            break
    new_message_list = []
    new_id_list = []
    for i in range(len_messages + 1):
        if texts[i].strip():
            new_message_list.append({"role": roles[i], "content": texts[i]})
            if i == len_messages or texts[i] != message_data[id_list[i]][1]: # New prompt or modified thread
                new_id_list.append(db_insert_message(roles[i], texts[i], datetime.now(), state.conn))
            else:
                new_id_list.append(id_list[i])

    client = get_client()
    c1, c2 = st.columns([.8, .2])
    with c1:
        st.checkbox("assistant", key="check" + str(len_messages+1), value=True)
    with c2:
        st.toggle('Edit', key="edit" + str(len_messages+1))
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model="gpt-4-turbo",  # ToDo: Variable model in st.session_state["model"],
            messages=new_message_list,
            stream=True
        )
        answer = st.write_stream(stream)
    new_id_list.append(db_insert_message("assistant", answer, datetime.now(), state.conn))
    if same_thread:
        db_update_thread(','.join(map(str, new_id_list)), datetime.now(), state.current_thread_id, state.conn)
    else:
        change_title(state.current_thread_id, None, threads[current_thread_index][1], state.conn)
        db_insert_thread(threads[current_thread_index][1], ','.join(map(str, new_id_list)), datetime.now(), datetime.now(), state.conn)
        for i in range(len_messages):
            del st.session_state["check" + str(i)]
            if "edit" + str(i) in st.session_state:
                del st.session_state["edit" + str(i)]
        streamlit_js_eval(js_expressions="parent.window.location.reload()")
