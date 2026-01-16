
import streamlit as st
import requests
import re
from datetime import datetime

API_BASE = "http://127.0.0.1:8000"

# ---------------------------------
# AUTH HEADERS
# ---------------------------------
def auth_headers():
    token = st.session_state.get("admin_token")
    if not token:
        return {}
    return {"Authorization": f"Bearer " + token}


# ---------------------------------
# SIMPLE GET WRAPPER
# ---------------------------------
def api_get(url):
    try:
        r = requests.get(url, headers=auth_headers())
        if r.status_code == 200:
            return r.json()
        st.error(r.text)
    except Exception as e:
        st.error(str(e))
    return None


# ---------------------------------
# VALIDATE TIME FORMAT HH:MM
# ---------------------------------
def is_valid_time(value: str):
    if not value:
        return False
    return bool(re.match(r"^(?:[01]\d|2[0-3]):[0-5]\d$", value))

# ---------------------------------
# HELPER FUNCTION FOR DISPLAY
# ---------------------------------
def format_display(text: str) -> str:
    """
    Format DB-stored lowercase text for frontend display.
    - Converts names to Title Case
    - Keeps numbers, symbols, and non-English letters intact
    """
    if not isinstance(text, str):
        return text
    return " ".join([w.capitalize() if w.isalpha() else w for w in text.split()])