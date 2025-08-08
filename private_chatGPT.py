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

st.header("Private chatGPT")

# DB connection
state.conn = db_get_connection()

# Sidebar with thread list

if "model_index" not in state:
    state["model_index"] = 0

available_models = [
    "gpt-5-nano/$0.05/0.4",
    "gpt-5-mini/$0.25/2",
    "gpt-5/$1.25/10",
    "gpt-4.1-nano/Fastest, most cost-effective 4.1 $0.1/0.4",
    "gpt-4.1-mini/$0.4/1.6",
    "gpt-4.1/Flagship GPT model for complex tasks $2/8",
    "o4-mini/Faster, more affordable reasoning model $1.1/4.4",
    "o3-mini/Our most powerful reasoning model (small) $1.1/4.4",
    "gpt-image-1/$5",
    "gpt-4o-mini-tts/$0.015 x minute",
    "gpt-4o-mini-transcribe/$0.003 x minute",
    "codex-mini-latest/$1.5/6",
    "o4-mini-deep-research/$2/8",
]

if "tier_index" not in state:
    state["tier_index"] = 0

available_tiers = [
    "flex",
    "priority",
    "default",
]

if "effort_index" not in state:
    state["effort_index"] = 0

available_efforts = [
    "minimal",
    "low",
    "medium",
    "high",
]

if "temperature" not in state:
    state["temperature"] = 1.0


def update_model_index():
    state["model_index"] = available_models.index(state.model)
    st.sidebar.write(f"changed to {state['model_index']}")


def update_tier_index():
    state["tier_index"] = available_tiers.index(state.tier)
    st.sidebar.write(f"changed to {state['tier_index']}")


def update_effort_index():
    state["effort_index"] = available_efforts.index(state.effort)
    st.sidebar.write(f"changed to {state['effort_index']}")


st.sidebar.radio(
    "Model",
    available_models,
    index=state.model_index,
    on_change=update_model_index,
    key="model",
)

st.sidebar.radio(
    "Processing Tier",
    available_tiers,
    index=state.tier_index,
    on_change=update_tier_index,
    key="tier",
)

st.sidebar.radio(
    "Reasoning Effort",
    available_efforts,
    index=state.effort_index,
    on_change=update_effort_index,
    key="effort",
)

state["temperature"] = st.sidebar.slider(
    "Temperature",
    min_value=0.0,
    value=state["temperature"],
    max_value=2.0,
    step=0.1,
    key="temperature_slider",
)

if st.sidebar.button("New empty thread", use_container_width=True):
    new_message_id = db_insert_message(
        "system",
        "You are a helpful assistant.",
        None,
        None,
        None,
        None,
        datetime.now(),
        state.conn,
    )
    db_insert_thread(
        get_new_thread_title("Example", state.conn),
        str(new_message_id),
        datetime.now(),
        datetime.now(),
        state.conn,
    )

threads = db_get_threads(state.conn)
thread_list = [t[1] for t in threads]
with st.sidebar:
    selected = option_menu(
        "Threads", thread_list, icons=["chat-right"] * len(threads), default_index=0
    )
current_thread_index = thread_list.index(selected)
state.current_thread_id = threads[current_thread_index][0]

# Thread title and commands
c1, c2, c3 = st.columns([0.88, 0.06, 0.06])
with c2:
    edit_title = st.button(":writing_hand:", help="Edit title")
with c3:
    delete_thread = st.button(":wastebasket:", help="Delete thread")
with c1:
    if edit_title:
        st.text_input(
            "Edit",
            value=threads[current_thread_index][1],
            on_change=change_title,
            args=(
                state.current_thread_id,
                threads[current_thread_index][1].strip(),
                None,
                state.conn,
            ),
            key="new_title_text",
        )
    else:
        st.subheader(threads[current_thread_index][1])

if delete_thread:
    c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
    with c1:
        st.subheader(f"Confirm deletion of the thread?")
    with c2:
        st.button(
            "Delete",
            on_click=db_delete_thread,
            args=(state.current_thread_id, state.conn),
            use_container_width=True,
        )
    with c3:
        st.button("Cancel", use_container_width=True)

# Messages of selected thread
id_list = [int(id) for id in threads[current_thread_index][2].split(",")]
messages = db_get_messages(
    id_list, state.conn
)  # message_id, role, content, model, effort, temperature, edited
message_data = dict()
for message in messages:
    message_data[message[0]] = [
        message[1],
        message[2],
        message[3],
        message[4],
        message[5],
        message[6],
    ]

len_messages = len(messages)
texts = [""] * (len_messages + 1)
roles = [""] * (len_messages + 1)
for i in range(len_messages):
    id = id_list[i]
    if message_data[id][0] == "user":
        st.markdown("---")
    c1, c2 = st.columns([0.8, 0.2])
    roles[i] = message_data[id][0]
    with c1:
        checkbox_title = roles[i]
        if roles[i] == "assistant":
            add_details = []
            if message_data[id][2] is not None:
                add_details.append(f"model={message_data[id][2]}")
            if message_data[id][3] is not None:
                add_details.append(f"effort={message_data[id][3]}")
            if message_data[id][4] is not None:
                add_details.append(f"temperature={message_data[id][4]:.1f}")
            if message_data[id][5]:
                add_details.append("edited")
            if add_details:
                checkbox_title += f" ({', '.join(add_details)})"
        show_message = st.checkbox(checkbox_title, key="check" + str(i), value=True)
    if show_message:
        with c2:
            edit_message = st.toggle("Edit", key="edit" + str(i))
        if edit_message:
            texts[i] = st.text_area(
                "content",
                label_visibility="hidden",
                key="content" + str(i),
                value=message_data[id][1],
            )
        else:
            texts[i] = message_data[id][1]
            show_message = st.chat_message(message_data[id][0])
            show_message.write(message_data[id][1])

# New prompt
roles[len_messages] = "user"
texts[len_messages] = st.chat_input(
    "What? When? Where? Why? Who? Whom? Whose? Which? How?"
)

# Call API and get answer
if texts[len_messages]:
    st.markdown("""---""")
    c1, c2 = st.columns([0.8, 0.2])
    with c1:
        st.checkbox(
            roles[len_messages],
            key="check" + str(len_messages),
            value=len(texts[len_messages].strip()) > 0,
        )
    with c2:
        edit_message = st.toggle("Edit", key="edit" + str(len_messages))
    show_message = st.chat_message(roles[len_messages])
    show_message.write(texts[len_messages])
    same_thread = True
    for i in range(len_messages):
        if texts[i] != message_data[id_list[i]][1] and not (
            i == 0 and len_messages == 1
        ):
            same_thread = False
            break
    new_message_list = []
    new_id_list = []
    for i in range(len_messages + 1):
        if texts[i].strip():
            new_message_list.append({"role": roles[i], "content": texts[i]})
            if i == len_messages:  # New prompt
                new_id_list.append(
                    db_insert_message(
                        roles[i], texts[i], None, None, None, None, datetime.now(), state.conn
                    )
                )
            elif texts[i] != message_data[id_list[i]][1]:  # Modified message
                new_id_list.append(
                    db_insert_message(  # role, content, model, effort, temperature, edited, created, conn
                        roles[i],
                        texts[i],
                        message_data[id_list[i]][2],
                        message_data[id_list[i]][3],
                        message_data[id_list[i]][4],
                        True,
                        datetime.now(),
                        state.conn,
                    )
                )
            else:
                new_id_list.append(id_list[i])

    client = get_client(state["tier"])
    c1, c2 = st.columns([0.8, 0.2])
    with c1:
        st.checkbox(
            f"assistant (model={state['model'].split('/')[0]}, effort={state['effort']}, temperature={state['temperature']:.1f})",
            key="check" + str(len_messages + 1),
            value=True,
        )
    with c2:
        st.toggle("Edit", key="edit" + str(len_messages + 1))
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=state["model"].split("/")[0],
            temperature=state["temperature"],
            service_tier=state["tier"],
            reasoning_effort=state["effort"],
            messages=new_message_list,
            stream=True,
        )
        answer = st.write_stream(stream)
    new_id_list.append(
        db_insert_message(
            "assistant",
            answer,
            state["model"].split("/")[0],
            state["effort"],
            state["temperature"],
            False,
            datetime.now(),
            state.conn,
        )
    )
    if same_thread:
        db_update_thread(
            ",".join(map(str, new_id_list)),
            datetime.now(),
            state.current_thread_id,
            state.conn,
        )
    else:
        change_title(
            state.current_thread_id, None, threads[current_thread_index][1], state.conn
        )
        db_insert_thread(
            threads[current_thread_index][1],
            ",".join(map(str, new_id_list)),
            datetime.now(),
            datetime.now(),
            state.conn,
        )
        for i in range(len_messages):
            del st.session_state["check" + str(i)]
            if "edit" + str(i) in st.session_state:
                del st.session_state["edit" + str(i)]
        streamlit_js_eval(js_expressions="parent.window.location.reload()")
