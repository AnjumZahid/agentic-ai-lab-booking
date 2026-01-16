# chat_page.py
import queue
import streamlit as st
from langgraph_mcp_backend import chatbot, submit_async_task
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage


def extract_ai_text(content):
    """
    Extract clean text from AIMessage.content (handles Gemini structured output)
    """
    if isinstance(content, list):
        return "".join(
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") == "text"
        )

    if isinstance(content, str):
        return content

    return ""


def render_chat_page():
    """
    Renders the chat interface. Expects session state keys:
      - message_history (list of dicts: {'role': 'user'|'assistant', 'content': str})
      - thread_id
    """
    st.header("💬 Chat with Lab Bot")
    st.subheader("➡ Ask questions")
    st.subheader("➡ Check appointment availability")
    st.subheader("➡ Book appointments for lab tests")

    



    # Render chat history
    for message in st.session_state.get("message_history", []):
        with st.chat_message(message["role"]):
            st.text(message["content"])

    user_input = st.chat_input("Type here")

    if not user_input:
        return

    # Append user message to session and show immediately
    st.session_state["message_history"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.text(user_input)

    CONFIG = {
        "configurable": {"thread_id": st.session_state.get("thread_id")},
        "metadata": {"thread_id": st.session_state.get("thread_id")},
        "run_name": "chat_turn",
    }

    # Assistant streaming block
    with st.chat_message("assistant"):
        status_holder = {"box": None}

        def ai_only_stream():
            event_queue: queue.Queue = queue.Queue()

            async def run_stream():
                try:
                    async for message_chunk, metadata in chatbot.astream(
                        {"messages": [HumanMessage(content=user_input)]},
                        config=CONFIG,
                        stream_mode="messages",
                    ):
                        event_queue.put((message_chunk, metadata))
                except Exception as exc:
                    event_queue.put(("error", exc))
                finally:
                    event_queue.put(None)

            submit_async_task(run_stream())

            while True:
                item = event_queue.get()
                if item is None:
                    break
                message_chunk, metadata = item
                if message_chunk == "error":
                    raise metadata

                # show a tool status box while a tool is used
                if isinstance(message_chunk, ToolMessage):
                    tool_name = getattr(message_chunk, "name", "tool")
                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(f"🔧 Using `{tool_name}` …", expanded=True)
                    else:
                        status_holder["box"].update(
                            label=f"🔧 Using `{tool_name}` …", state="running", expanded=True
                        )

                # stream only assistant tokens
                # if isinstance(message_chunk, AIMessage):
                #     yield message_chunk.content

                if isinstance(message_chunk, AIMessage):
                    clean_text = extract_ai_text(message_chunk.content)
                    if clean_text:
                        yield clean_text


        # run streaming generator and collect full assistant message
        try:
            ai_message = st.write_stream(ai_only_stream())
        except Exception as e:
            st.error(f"Error while streaming response: {e}")
            ai_message = f"Error: {e}"

        if status_holder["box"] is not None:
            status_holder["box"].update(label="✅ Tool finished", state="complete", expanded=False)

    # Save assistant message to session history
    st.session_state["message_history"].append({"role": "assistant", "content": ai_message})
