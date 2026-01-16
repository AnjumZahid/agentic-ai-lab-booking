# run.py
import uuid
import streamlit as st
from langgraph_mcp_backend import retrieve_all_threads

from frontend_chatpage import render_chat_page
from frontend.frontend_main import render_admin_panel

# -------------------------- Utilities --------------------------
def generate_thread_id():
    return uuid.uuid4()

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state["thread_id"] = thread_id
    add_thread(thread_id)
    st.session_state["message_history"] = []

def add_thread(thread_id):
    if "chat_threads" not in st.session_state:
        st.session_state["chat_threads"] = []
    if thread_id not in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].append(thread_id)

def load_conversation(thread_id):
    return st.session_state.get("message_history", [])

# ---------------------- Session Initialization ----------------------
if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = generate_thread_id()

if "chat_threads" not in st.session_state:
    try:
        st.session_state["chat_threads"] = retrieve_all_threads()
    except Exception:
        st.session_state["chat_threads"] = []

add_thread(st.session_state["thread_id"])

# --------------------------- Sidebar & Routing ---------------------------
st.sidebar.title("⚙️ Lab Management")
page = st.sidebar.radio("Go to", ["Chat", "Settings"])

# --------------------------- CHAT SIDEBAR ---------------------------
if page == "Chat":
    if st.sidebar.button("New Chat"):
        reset_chat()

    st.sidebar.header("My Conversations")

    for thread_id in st.session_state["chat_threads"][::-1]:
        if st.sidebar.button(str(thread_id)):
            st.session_state["thread_id"] = thread_id
            st.session_state["message_history"] = load_conversation(thread_id)

# --------------------------- PAGE ROUTING ---------------------------
if page == "Chat":
    render_chat_page()

elif page == "Settings":
    render_admin_panel()






# # run.py
# import uuid
# import streamlit as st
# from langgraph_mcp_backend import retrieve_all_threads

# from f_chatpage import render_chat_page
# # from f_settings import render_settings_page
# from admin_frontend import render_admin_panel

# # -------------------------- Utilities --------------------------
# def generate_thread_id():
#     return uuid.uuid4()

# def reset_chat():
#     thread_id = generate_thread_id()
#     st.session_state["thread_id"] = thread_id
#     add_thread(thread_id)
#     st.session_state["message_history"] = []

# def add_thread(thread_id):
#     if "chat_threads" not in st.session_state:
#         st.session_state["chat_threads"] = []
#     if thread_id not in st.session_state["chat_threads"]:
#         st.session_state["chat_threads"].append(thread_id)

# def load_conversation(thread_id):
#     # This function is intentionally simple — the chat_page handles actual chatbot streaming.
#     # Here we only provide a placeholder to keep session_state.message_history consistent.
#     # If you want to hydrate full message objects, you can call chatbot.get_state(...) from chat_page.
#     return st.session_state.get("message_history", [])

# # ---------------------- Session Initialization ----------------------
# if "message_history" not in st.session_state:
#     st.session_state["message_history"] = []

# if "thread_id" not in st.session_state:
#     st.session_state["thread_id"] = generate_thread_id()

# # retrieve_all_threads can be expensive; call once and store
# if "chat_threads" not in st.session_state:
#     try:
#         st.session_state["chat_threads"] = retrieve_all_threads()
#     except Exception:
#         # fallback to empty list if backend not available at startup
#         st.session_state["chat_threads"] = []

# add_thread(st.session_state["thread_id"])

# # --------------------------- Sidebar & Routing ---------------------------
# st.sidebar.title("LangGraph MCP Chatbot")
# page = st.sidebar.radio("Go to", ["Chat", "Settings"])

# if st.sidebar.button("New Chat"):
#     reset_chat()

# st.sidebar.header("My Conversations")
# # show threads in reverse order, clicking sets current thread and loads messages (if available)
# for thread_id in st.session_state["chat_threads"][::-1]:
#     if st.sidebar.button(str(thread_id)):
#         st.session_state["thread_id"] = thread_id
#         # attempt to load conversation (if you implement loading from chatbot state in chat_page)
#         st.session_state["message_history"] = load_conversation(thread_id)

# # Route to pages
# # reset admin login when switching pages if needed
# if page == "Chat":
#     render_chat_page()
    

# if page == "Settings":
#     render_admin_panel()

