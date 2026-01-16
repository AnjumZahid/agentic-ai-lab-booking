from .frontend_common import *


# ---------------------------------
# LAB HOLIDAYS TABLE UI (FULL CRUD)
# ---------------------------------
def render_lab_holidays():
    st.subheader("🎉 Lab Holidays / Half-Days")

    holidays = api_get(f"{API_BASE}/lab/holidays")
    if holidays is None:
        st.error("Failed to fetch holidays.")
        return

    with st.expander("➕ Add New Holiday"):
        new_date = st.text_input("Date (YYYY-MM-DD)", key="new_holiday_date")
        new_closed_flag = st.checkbox("Full Holiday", key="new_holiday_closed")
        new_remarks = st.text_input("Remarks", key="new_holiday_remarks")  # added remarks
        if not new_closed_flag:
            new_open = st.text_input("Opens At (HH:MM)", key="new_holiday_open")
            new_close = st.text_input("Closes At (HH:MM)", key="new_holiday_close")
        else:
            new_open = "00:00"
            new_close = "00:00"

        if st.button("Add Holiday"):
            if not new_date:
                st.error("Please enter a date.")
            elif not new_closed_flag and (not is_valid_time(new_open) or not is_valid_time(new_close)):
                st.error("❌ Invalid time format! Use HH:MM (e.g., 09:30, 14:45)")
            else:
                payload = {
                    "date": new_date,
                    "opens_at": new_open,
                    "closes_at": new_close,
                    "is_closed": 1 if new_closed_flag else 0,
                    "remarks": new_remarks  # added to payload
                }
                r = requests.post(f"{API_BASE}/lab/holidays", json=payload, headers=auth_headers())
                if r.status_code == 200:
                    st.success("Holiday added successfully!")
                    st.rerun()
                else:
                    st.error(r.text)

    st.write("### Holidays Table")
    header_cols = st.columns([2, 2, 2, 1.5, 1.5, 2])
    header_cols[0].markdown("**Date**")
    header_cols[1].markdown("**Opens**")
    header_cols[2].markdown("**Closes**")
    header_cols[3].markdown("**Closed**")
    header_cols[4].markdown("**Actions**")
    header_cols[5].markdown("**Remarks**")  # added column header

    if not holidays:
        st.info("No holidays found.")
        return

    for h in holidays:
        col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 1.5, 1.5, 2])
        col1.write(h["date"])
        col2.write(h["opens_at"] if not h["is_closed"] else "-")
        col3.write(h["closes_at"] if not h["is_closed"] else "-")
        col4.write("Yes" if h["is_closed"] else "No")
        col6.write(h.get("remarks", ""))  # display remarks

        edit_btn = col5.button("✏️ Edit", key=f"edit_holiday_{h['holiday_id']}")
        delete_btn = col5.button("🗑️ Delete", key=f"delete_holiday_{h['holiday_id']}")

        if edit_btn:
            st.session_state["edit_holiday"] = h
        if delete_btn:
            st.session_state["delete_holiday"] = h

    if "delete_holiday" in st.session_state:
        item = st.session_state["delete_holiday"]
        st.warning(f"Are you sure you want to delete holiday on {item['date']}?")
        del_btn, cancel_btn = st.columns(2)
        if del_btn.button("Yes, Delete"):
            r = requests.delete(f"{API_BASE}/lab/holidays/{item['holiday_id']}", headers=auth_headers())
            if r.status_code == 200:
                st.success("Deleted successfully!")
                del st.session_state["delete_holiday"]
                st.rerun()
            else:
                st.error(r.text)
        if cancel_btn.button("Cancel"):
            del st.session_state["delete_holiday"]
            st.rerun()

    if "edit_holiday" in st.session_state:
        item = st.session_state["edit_holiday"]
        st.write("---")
        st.subheader(f"✏️ Edit Holiday — {item['date']}")

        closed_flag = st.checkbox(
            "Full Holiday",
            value=bool(item["is_closed"]),
            key=f"edit_holiday_closed_{item['holiday_id']}"
        )
        st.caption("⏱ Time format: **HH:MM** (e.g., 08:30, 14:05)")
        edit_remarks = st.text_input("Remarks", value=item.get("remarks", ""), key=f"edit_holiday_remarks_{item['holiday_id']}")  # added input

        if not closed_flag:
            new_open = st.text_input("Opens At (HH:MM)", value=item["opens_at"] if item["opens_at"] else "")
            new_close = st.text_input("Closes At (HH:MM)", value=item["closes_at"] if item["closes_at"] else "")
        else:
            new_open = "00:00"
            new_close = "00:00"
            st.info("This day is marked as full holiday.")

        save_btn, cancel_btn = st.columns(2)
        if save_btn.button("💾 Save"):
            if not closed_flag and (not is_valid_time(new_open) or not is_valid_time(new_close)):
                st.error("❌ Invalid time format! Use HH:MM (e.g., 09:30, 14:45)")
                return
            payload = {
                "date": item["date"],
                "opens_at": new_open,
                "closes_at": new_close,
                "is_closed": 1 if closed_flag else 0,
                "remarks": edit_remarks  # added to payload
            }
            r = requests.put(f"{API_BASE}/lab/holidays/{item['holiday_id']}", json=payload, headers=auth_headers())
            if r.status_code == 200:
                st.success("Updated successfully!")
                del st.session_state["edit_holiday"]
                st.rerun()
            else:
                st.error(r.text)
        if cancel_btn.button("Cancel"):
            del st.session_state["edit_holiday"]
            st.rerun()