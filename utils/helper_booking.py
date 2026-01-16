from pydantic import BaseModel
import sqlite3
# from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import List, Dict

import re
from typing import Dict, Optional

from dotenv import load_dotenv

load_dotenv()

DB_PATH = "lab_system.db"  # adjust path


def _normalize(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    value = value.strip()
    if value.upper() == "NONE":
        return None
    return value

# -------------------------------
# Schema for LLM structured output
# -------------------------------
class TestBookingSchema(BaseModel):
    test_name: str       # exact test name from DB
    date_str: str        # YYYY-MM-DD
    patient_name: str    # extracted from user query
    patient_mobile: str  # extracted from user query



def get_test_info(user_query: str) -> Dict[str, str]:
    """
    Parse user query using LLM to extract exact test name, date,
    patient name, and mobile number, then fetch test_id from DB.
    """

    # -------------------------------
    # Step 1: Load test names from DB
    # -------------------------------
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT test_name FROM tests")
    tests = [row[0] for row in cursor.fetchall()]
    conn.close()

    # -------------------------------
    # Step 2: LLM structured parsing
    # -------------------------------
    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    # model = ChatOpenAI(model="gpt-3.5-turbo")
    structured_model = model.with_structured_output(TestBookingSchema)

    prompt = f"""
Valid lab tests:
{tests}

User query:
"{user_query}"

TASK:
1. Identify the correct test (fix typos).
2. Return EXACT test name from DB.
3. Extract date as YYYY-MM-DD.
4. Extract patient's full name.
5. Extract patient's mobile number (digits only).

If any field is missing, return NONE.
"""

    parsed = structured_model.invoke(prompt)

    test_name = _normalize(parsed.test_name)
    date_str = _normalize(parsed.date_str)
    patient_name = _normalize(parsed.patient_name)
    patient_mobile = _normalize(parsed.patient_mobile)

    if patient_mobile:
        patient_mobile = re.sub(r"\D", "", patient_mobile)

    print(
        f"[DEBUG] Parsed → test={test_name}, date={date_str}, "
        f"name={patient_name}, mobile={patient_mobile}"
    )

    # -------------------------------
    # Step 3: Resolve test_id
    # -------------------------------
    if not test_name:
        return {"error": "Test name not provided"}

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT test_id FROM tests WHERE test_name = ?",
        (test_name,)
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {"error": f"No test found in DB with name: {test_name}"}

    # -------------------------------
    # Step 4: Final structured result
    # -------------------------------
    return {
        "test_id": row[0],
        "test_name": test_name,
        "date_str": date_str,
        "patient_name": patient_name,
        "patient_mobile": patient_mobile,
    }

def parse_window_selection(user_input: str, windows: list) -> int:
    """
    Convert user input to a window index (1-based) dynamically.
    """
    user_input = user_input.lower()

    # Numeric input
    match = re.search(r"\b(\d+)\b", user_input)
    if match:
        idx = int(match.group(1))
        if 1 <= idx <= len(windows):
            return idx

    # Textual numbers
    text_map = {
        "first": 1, "second": 2, "third": 3, "fourth": 4,
        "fifth": 5, "sixth": 6, "seventh": 7, "eighth": 8
    }
    for word, idx in text_map.items():
        if word in user_input and idx <= len(windows):
            return idx

    # Match by time range
    for i, w in enumerate(windows):
        window_str = f"{w['window_start']} - {w['window_end']}".lower()
        if window_str in user_input:
            return i + 1

    raise ValueError("Window not recognized")











# # -------------------------------
# # Schema for LLM structured output
# # -------------------------------
# class SlotSelectionSchema(BaseModel):
#     slot_number: int  # 1-based index


# def parse_slot_selection(user_input: str, available_slots: List[Dict]) -> int:
#     """
#     Parse user's natural language input to select a slot from available slots.

#     Args:
#         user_input (str): User input like "slot 2" or "second window".
#         available_slots (List[Dict]): Output from get_available_slots()

#     Returns:
#         int: 1-based index of selected slot

#     Raises:
#         ValueError: if no valid slot can be parsed
#     """

#     # -------------------------------
#     # Step 1: Regex number extraction
#     # -------------------------------
#     match = re.search(r"\b(\d+)\b", user_input)
#     if match:
#         slot_no = int(match.group(1))
#         if 1 <= slot_no <= len(available_slots):
#             return slot_no

#     # -------------------------------
#     # Step 2: LLM fallback parsing
#     # -------------------------------
#     model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
#     structured_model = model.with_structured_output(SlotSelectionSchema)

#     slots_text = "\n".join(
#         [
#             f"{i+1}. {slot['window_start']} - {slot['window_end']}"
#             for i, slot in enumerate(available_slots)
#         ]
#     )

#     prompt = f"""
# Available slots:
# {slots_text}

# User input: "{user_input}"

# TASK:
# - Identify which slot the user selected.
# - Return ONLY the slot number (1-based).
# - If unclear, return 0.
# """

#     parsed = structured_model.invoke(prompt)
#     slot_number = parsed.slot_number

#     if not (1 <= slot_number <= len(available_slots)):
#         raise ValueError("Unable to determine selected slot")

#     return slot_number

