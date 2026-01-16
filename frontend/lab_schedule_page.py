from .frontend_common import *
# ---------------------------------
# LAB SCHEDULE TABLE UI
# ---------------------------------
def render_lab_schedule():
    st.subheader("📅 Weekly Lab Schedule")

    schedules = api_get(f"{API_BASE}/lab/schedule")
    if not schedules:
        st.info("No schedule found.")
        return

    # day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    st.write("### Schedule Table")

    # Header row
    header_cols = st.columns([2, 2, 2, 1.5, 1.5])
    header_cols[0].markdown("**Day**")
    header_cols[1].markdown("**Opens**")
    header_cols[2].markdown("**Closes**")
    header_cols[3].markdown("**Closed**")
    header_cols[4].markdown("**Action**")

    for s in schedules:
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1.5, 1.5])

        # col1.write(day_names[s["day_of_week"]])
        col1.write(s["day_of_week"])

        col2.write(s["opens_at"] if not s["is_closed"] else "-")
        col3.write(s["closes_at"] if not s["is_closed"] else "-")
        col4.write("Yes" if s["is_closed"] else "No")

        if col5.button("✏️ Edit", key=f"edit_{s['schedule_id']}"):
            st.session_state["edit_item"] = s

        st.markdown('<hr style="margin:4px 0;">', unsafe_allow_html=True)

    # POPUP EDIT WINDOW
    if "edit_item" in st.session_state:
        item = st.session_state["edit_item"]

        st.write("---")
        # st.subheader(f"✏️ Edit Schedule — {day_names[item['day_of_week']]}")
        st.subheader(f"✏️ Edit Schedule — {item['day_of_week']}")


        closed_flag = st.checkbox("Closed", value=bool(item["is_closed"]))
        st.caption("⏱ Time format: **HH:MM** (e.g., 08:30, 14:05)")

        if closed_flag:
            new_open = ""
            new_close = ""
            st.info("This day is marked as closed.")
        else:
            new_open = st.text_input("Opens At (HH:MM)", value=item["opens_at"] if item["opens_at"] else "")
            new_close = st.text_input("Closes At (HH:MM)", value=item["closes_at"] if item["closes_at"] else "")

        save_btn, cancel_btn = st.columns(2)

        if save_btn.button("💾 Save"):
            if not closed_flag:
                if not is_valid_time(new_open) or not is_valid_time(new_close):
                    st.error("❌ Invalid time format! Use HH:MM (e.g., 09:30, 14:45)")
                    return
            payload = {
                "day_of_week": item["day_of_week"],
                "opens_at": new_open if not closed_flag else None,
                "closes_at": new_close if not closed_flag else None,
                "is_closed": 1 if closed_flag else 0,
            }
            r = requests.put(
                f"{API_BASE}/lab/schedule/{item['schedule_id']}",
                json=payload,
                headers=auth_headers(),
            )
            if r.status_code == 200:
                st.success("Updated successfully!")
                del st.session_state["edit_item"]
                st.rerun()
            else:
                st.error(r.text)

        if cancel_btn.button("Cancel"):
            del st.session_state["edit_item"]
            st.rerun()