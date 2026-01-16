import sqlite3
import uuid
from datetime import datetime
from typing import Dict, Any, List
from fastapi import HTTPException
from fastmcp import FastMCP

from backend.crud_backend import (
    get_available_slots,
    create_booking_internal,
    Booking
)

from utils.helper_booking import get_test_info, parse_window_selection          # test + date + patient info parser
# from lab_info import ask_question

DB_PATH = "lab_system.db"

# -------------------------------------------------
# MCP SERVER
# -------------------------------------------------
mcp = FastMCP("LocalLabTools")

# -------------------------------------------------
# TOOL 1: CHECK AVAILABLE SLOTS (READ-ONLY)
# -------------------------------------------------

import uuid

BOOKING_CONTEXT = {}

@mcp.tool()
async def start_booking_tool(query: str) -> Dict[str, Any]:
    """Fetch windows and initialize booking context"""
    result = get_test_info(query)
    if "error" in result:
        return result

    test_id = result["test_id"]
    booking_date = result["date_str"]

    windows = get_available_slots(test_id, booking_date)
    if not windows:
        return {"status": "no_windows"}

    context_id = str(uuid.uuid4())

    BOOKING_CONTEXT[context_id] = {
        "test_id": test_id,
        "test_name": result["test_name"],
        "booking_date": booking_date,
        "windows": windows
    }

    return {
        "status": "awaiting_window_selection",
        "context_id": context_id,
        "windows": [
            {
                "window_no": i + 1,
                "time": f"{w['window_start']} - {w['window_end']}",
                "available": w["available_slots"]
            }
            for i, w in enumerate(windows)
        ]
    }


@mcp.tool()
async def create_booking_tool(
    context_id: str,
    window_selection: str,  # can be "win 2", "second", "8:00 - 10:00"
    patient_name: str,
    patient_mobile: str,
    confirm: bool = False
) -> Dict[str, Any]:
    """Finalize booking for selected window"""
    context = BOOKING_CONTEXT.get(context_id)
    if not context:
        return {"status": "error", "message": "Booking context expired"}

    windows = context["windows"]

    # Parse window dynamically
    try:
        window_no = parse_window_selection(window_selection, windows)
    except ValueError:
        return {"status": "error", "message": "Invalid window selection"}

    selected_window = windows[window_no - 1]

    if not confirm:
        return {
            "status": "awaiting_confirmation",
            "message": (
                f"Confirm booking:\n"
                f"• Test: {context['test_name']}\n"
                f"• Date: {context['booking_date']}\n"
                f"• Window: {selected_window['window_start']} - {selected_window['window_end']}\n"
                f"• Patient: {patient_name}"
            )
        }

    booking = Booking(
        test_id=context["test_id"],
        window_id=selected_window["window_id"],
        patient_name=patient_name,
        patient_mobile=patient_mobile,
        booking_date=datetime.strptime(context["booking_date"], "%Y-%m-%d").date(),
      )

    result = create_booking_internal(booking)

    BOOKING_CONTEXT.pop(context_id, None)  # cleanup

    return {
        "status": "success",
        "booking_id": result["booking_id"],
        "message": result["message"]
    }


# @mcp.tool()
# async def rag_retrieval_tool(query: str) -> Dict[str, Any]:
#     """
#     Retrieve relevant lab information for general user questions.

#     This tool is used only for general, non-booking queries about the lab
#     (e.g. lab timings, holidays, tests, doctors, services).
#     It does NOT handle appointments, dates, or slot availability.
#     """

#     retrieved_chunks = ask_question(query)

#     context_id = str(uuid.uuid4())
#     RAG_CONTEXT = {}
#     RAG_CONTEXT[context_id] = {
#         "query": query,
#         "chunks": retrieved_chunks
#     }

#     return {
#         "status": "success",
#         "context_id": context_id,
#         "chunks": retrieved_chunks
#     }


# ==============================
# Run MCP Server
# ==============================
def run_server():
    print("🚀 MCP Local Lab Server running on http://127.0.0.1:8005/mcp")
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8005)

if __name__ == "__main__":
    run_server()


