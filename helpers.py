import re
import streamlit as st
from datetime import datetime
from openai import OpenAI, OpenAIError

from db import *


def get_client():
    return OpenAI()


def get_new_thread_title(proposed_title, conn):
    numbers = re.compile(r'\((\d+)\)$')  # Matches a number between parenthesis at the end of the string
    match_old = numbers.search(proposed_title)
    if match_old:
        search = proposed_title[:match_old.start()]
    else:
        search = proposed_title
    existing = db_get_titles_like(search, conn)
    if len(existing) == 0 or proposed_title not in [t[0] for t in existing]:
        return proposed_title
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


def change_title(thread_id, old_title, new_title, conn):
    if not new_title:
        new_title = st.session_state.new_title_text.strip()  # Not used in unit tests
    if new_title != old_title:
        unique_new_title = get_new_thread_title(new_title, conn)
        db_update_title(unique_new_title, datetime.now(), thread_id, conn)
