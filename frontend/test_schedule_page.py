from .frontend_common import *

# ---------------------------------
# TEST SCHEDULE UI (WITH SEARCH & CRUD)
# ---------------------------------
def render_test_schedule():
    st.subheader("🗓️ Test Schedule")

    # -------------------
    # FETCH TESTS
    # -------------------
    tests = api_get(f"{API_BASE}/lab/tests")
    if not tests:
        st.info("No tests available.")
        return

    # -------------------
    # SEARCH TEST
    # -------------------
    st.write("### 🔍 Search Test")
    search_text = st.text_input("Search test by name")

    filtered_tests = [
        t for t in tests
        if search_text.lower() in t["test_name"].lower()
    ] if search_text else tests

    if not filtered_tests:
        st.warning("No matching tests found.")
        return

    # -------------------
    # SELECT TEST
    # -------------------
    test_map = {
        f"{format_display(t['test_name'])} ({format_display(t['category'])})": t["test_id"]
        for t in filtered_tests
    }
    selected_test_label = st.selectbox("Select Test", list(test_map.keys()))
    
    selected_test_id = test_map[selected_test_label]

    st.markdown("---")

    if st.session_state.get("show_all_test_schedules"):
        if st.button("⬅️ Back to Test Schedule"):
            st.session_state.pop("show_all_test_schedules", None)
            st.rerun()





    # -------------------
    # VIEW ALL TEST SCHEDULES
    # -------------------

    st.markdown("### 📋 View All Test Schedules")
    if st.button("👁️ See All Tests Schedule"):
        st.session_state["show_all_test_schedules"] = True

    if st.session_state.get("show_all_test_schedules"):
        all_schedules = api_get(f"{API_BASE}/lab/test-schedule")
        if not all_schedules:
            st.info("No test schedules found.")
            return

        search_col, day_col = st.columns([3, 2])
        search_test = search_col.text_input("Search by Test Name")
        filter_day = day_col.selectbox(
            "Filter by Day",
            ["All"] + list({s["day_name"] for s in all_schedules})
        )

        filtered = []
        for s in all_schedules:
            if search_test and search_test.lower() not in s["test_name"].lower():
                continue
            if filter_day != "All" and s["day_name"] != filter_day:
                continue
            filtered.append(s)

        st.write("### All Test Schedules")
        h = st.columns([3, 2, 2, 2, 1.5])
        h[0].markdown("**Test Name**")
        h[1].markdown("**Day**")
        h[2].markdown("**Opens**")
        h[3].markdown("**Closes**")
        h[4].markdown("**Closed**")

        if not filtered:
            st.warning("No matching schedules found.")
            return

        for s in filtered:
            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1.5])
            c1.write(format_display(s["test_name"]))
            c2.write(s["day_name"])
            c3.write(s["opens_at"] if not s["is_closed"] else "-")
            c4.write(s["closes_at"] if not s["is_closed"] else "-")
            c5.write("Yes" if s["is_closed"] else "No")
            st.markdown('<hr style="margin:4px 0;">', unsafe_allow_html=True)

        if st.button("❌ Close All Schedules View"):
            del st.session_state["show_all_test_schedules"]
            st.rerun()

    # -------------------
    # FETCH TEST SCHEDULE
    # -------------------
    schedules = api_get(f"{API_BASE}/lab/test-schedule/{selected_test_id}") or []

    # -------------------
    # ADD NEW DAY SCHEDULE
    # -------------------

    # -------------------
# ADD NEW DAY SCHEDULE
# -------------------
    with st.expander("➕ Add Test Day Schedule"):
        day = st.selectbox(
            "Day of Week",
            options=list(range(7)),
            format_func=lambda x: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][x]
        )

        closed_flag = st.checkbox("Closed", key="add_test_schedule_closed")

        if not closed_flag:
            open_time = st.text_input("Opens At (HH:MM)", key="add_test_schedule_open")
            close_time = st.text_input("Closes At (HH:MM)", key="add_test_schedule_close")
            window_minutes = st.number_input(
                "Window Size (minutes)", min_value=1, value=120, step=1, key="add_test_schedule_window"
            )
        else:
            open_time = "00:00"
            close_time = "00:00"
            window_minutes = 120  # default when closed

        if st.button("Add Schedule"):
            if not closed_flag and (not is_valid_time(open_time) or not is_valid_time(close_time)):
                st.error("Invalid time format (HH:MM)")
            else:
                payload = {
                    "test_id": selected_test_id,
                    "day_of_week": day,
                    "opens_at": open_time,
                    "closes_at": close_time,
                    "is_closed": 1 if closed_flag else 0,
                }
                # send window_minutes as query param to backend
                r = requests.post(
                    f"{API_BASE}/lab/test-schedule?window_minutes={window_minutes}",
                    json=payload,
                    headers=auth_headers()
                )
                if r.status_code == 200:
                    st.success("Test schedule added!")
                    st.rerun()
                else:
                    st.error(r.text)




    # with st.expander("➕ Add Test Day Schedule"):
    #     day = st.selectbox(
    #         "Day of Week",
    #         options=list(range(7)),
    #         format_func=lambda x: ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][x]
    #     )

    #     closed_flag = st.checkbox("Closed", key="add_test_schedule_closed")

    #     if not closed_flag:
    #         open_time = st.text_input("Opens At (HH:MM)", key="add_test_schedule_open")
    #         close_time = st.text_input("Closes At (HH:MM)", key="add_test_schedule_close")
    #     else:
    #         open_time = "00:00"
    #         close_time = "00:00"

    #     if st.button("Add Schedule"):
    #         if not closed_flag and (not is_valid_time(open_time) or not is_valid_time(close_time)):
    #             st.error("Invalid time format (HH:MM)")
    #         else:
    #             payload = {
    #                 "test_id": selected_test_id,
    #                 "day_of_week": day,
    #                 "opens_at": open_time,
    #                 "closes_at": close_time,
    #                 "is_closed": 1 if closed_flag else 0,
    #             }
    #             r = requests.post(
    #                 f"{API_BASE}/lab/test-schedule",
    #                 json=payload,
    #                 headers=auth_headers()
    #             )
    #             if r.status_code == 200:
    #                 st.success("Test schedule added!")
    #                 st.rerun()
    #             else:
    #                 st.error(r.text)

    # -------------------
    # TABLE HEADER
    # -------------------
    st.write("### Test Schedule Table")
    header = st.columns([2, 2, 2, 1.5, 1.5])
    header[0].markdown("**Day**")
    header[1].markdown("**Opens**")
    header[2].markdown("**Closes**")
    header[3].markdown("**Closed**")
    header[4].markdown("**Actions**")

    if not schedules:
        st.info("No schedule defined for this test.")
        # return

    for s in schedules:
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1.5, 1.5])
        col1.write(s["day_name"])
        col2.write(s["opens_at"] if not s["is_closed"] else "-")
        col3.write(s["closes_at"] if not s["is_closed"] else "-")
        col4.write("Yes" if s["is_closed"] else "No")

        edit_btn = col5.button("✏️ Edit", key=f"edit_test_sched_{s['schedule_id']}")
        del_btn = col5.button("🗑️ Delete", key=f"del_test_sched_{s['schedule_id']}")

        if edit_btn:
            st.session_state["edit_test_schedule"] = s
        if del_btn:
            st.session_state["delete_test_schedule"] = s

        st.markdown('<hr style="margin:4px 0;">', unsafe_allow_html=True)

    # -------------------
    # DELETE
    # -------------------
    if "delete_test_schedule" in st.session_state:
        item = st.session_state["delete_test_schedule"]
        st.warning("Delete this test schedule?")
        yes, no = st.columns(2)
        if yes.button("Yes, Delete"):
            r = requests.delete(
                f"{API_BASE}/lab/test-schedule/{item['schedule_id']}",
                headers=auth_headers()
            )
            if r.status_code == 200:
                st.success("Deleted successfully!")
                del st.session_state["delete_test_schedule"]
                st.rerun()
            else:
                st.error(r.text)
        if no.button("Cancel"):
            del st.session_state["delete_test_schedule"]
            st.rerun()

    # -------------------
    # EDIT
    # -------------------
    if "edit_test_schedule" in st.session_state:
        item = st.session_state["edit_test_schedule"]
        st.write("---")
        st.subheader(f"✏️ Edit — {item['day_name']}")

        closed_flag = st.checkbox(
            "Closed",
            value=bool(item["is_closed"]),
            key=f"edit_test_schedule_closed_{item['schedule_id']}"
        )

        if not closed_flag:
            new_open = st.text_input(
                "Opens At",
                value=item["opens_at"],
                key=f"edit_test_schedule_open_{item['schedule_id']}"
            )
            new_close = st.text_input(
                "Closes At",
                value=item["closes_at"],
                key=f"edit_test_schedule_close_{item['schedule_id']}"
            )
        else:
            new_open = "00:00"
            new_close = "00:00"

        save, cancel = st.columns(2)

        if save.button("💾 Save"):
            if not closed_flag and (not is_valid_time(new_open) or not is_valid_time(new_close)):
                st.error("Invalid time format")
            else:
                payload = {
                    "test_id": selected_test_id,
                    "day_of_week": item["day_of_week"],
                    "opens_at": new_open,
                    "closes_at": new_close,
                    "is_closed": 1 if closed_flag else 0,
                }
                r = requests.put(
                    f"{API_BASE}/lab/test-schedule/{item['schedule_id']}",
                    json=payload,
                    headers=auth_headers()
                )
                if r.status_code == 200:
                    st.success("Updated successfully!")
                    del st.session_state["edit_test_schedule"]
                    st.rerun()
                else:
                    st.error(r.text)

        if cancel.button("Cancel"):
            del st.session_state["edit_test_schedule"]
            st.rerun()






# # ---------------------------------
# # TEST SCHEDULE UI (WITH SEARCH & CRUD)
# # ---------------------------------
# def render_test_schedule():
#     st.subheader("🗓️ Test Schedule")

#     day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

#     # -------------------
#     # FETCH TESTS
#     # -------------------
#     tests = api_get(f"{API_BASE}/lab/tests")
#     if not tests:
#         st.info("No tests available.")
#         return

#     # -------------------
#     # SEARCH TEST
#     # -------------------
#     st.write("### 🔍 Search Test")
#     search_text = st.text_input("Search test by name")

#     filtered_tests = [
#         t for t in tests
#         if search_text.lower() in t["test_name"].lower()
#     ] if search_text else tests

#     if not filtered_tests:
#         st.warning("No matching tests found.")
#         return

#     # -------------------
#     # SELECT TEST
#     # -------------------
#     test_map = {f"{format_display(t['test_name'])} ({format_display(t['category'])})": t["test_id"] for t in filtered_tests}
#     selected_test_label = st.selectbox("Select Test", list(test_map.keys()))
#     selected_test_id = test_map[selected_test_label]

#     st.markdown("---")

#     # -------------------
#     # SEE ALL TEST SCHEDULES
#     # -------------------
#     st.markdown("### 📋 View All Test Schedules")
#     if st.button("👁️ See All Tests Schedule"):
#         st.session_state["show_all_test_schedules"] = True

#     if st.session_state.get("show_all_test_schedules"):
#         all_schedules = api_get(f"{API_BASE}/lab/test-schedule")
#         if not all_schedules:
#             st.info("No test schedules found.")
#             return

#         search_col, day_col = st.columns([3, 2])
#         search_test = search_col.text_input("Search by Test Name")
#         filter_day = day_col.selectbox(
#             "Filter by Day",
#             ["All"] + day_names
#         )

#         filtered = []
#         for s in all_schedules:
#             if search_test and search_test.lower() not in s["test_name"].lower():
#                 continue
#             if filter_day != "All" and day_names[s["day_of_week"]] != filter_day:
#                 continue
#             filtered.append(s)

#         st.write("### All Test Schedules")
#         h = st.columns([3, 2, 2, 2, 1.5])
#         h[0].markdown("**Test Name**")
#         h[1].markdown("**Day**")
#         h[2].markdown("**Opens**")
#         h[3].markdown("**Closes**")
#         h[4].markdown("**Closed**")

#         if not filtered:
#             st.warning("No matching schedules found.")
#             return

#         for s in filtered:
#             c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1.5])
#             c1.write(format_display(s["test_name"]))
#             c2.write(day_names[s["day_of_week"]])
#             c3.write(s["opens_at"] if not s["is_closed"] else "-")
#             c4.write(s["closes_at"] if not s["is_closed"] else "-")
#             c5.write("❌" if s["is_closed"] else "✔️")

#             st.markdown('<hr style="margin:4px 0;">', unsafe_allow_html=True)

#         if st.button("❌ Close All Schedules View"):
#             del st.session_state["show_all_test_schedules"]
#             st.rerun()

#     # -------------------
#     # FETCH TEST SCHEDULE
#     # -------------------
#     schedules = api_get(f"{API_BASE}/lab/test-schedule/{selected_test_id}") or []

#     # -------------------
#     # ADD NEW DAY SCHEDULE
#     # -------------------
#     with st.expander("➕ Add Test Day Schedule"):
#         day = st.selectbox("Day of Week", list(range(7)), format_func=lambda x: day_names[x])
#         closed_flag = st.checkbox("Closed", key="add_test_schedule_closed")

#         if not closed_flag:
#             open_time = st.text_input("Opens At (HH:MM)", key="add_test_schedule_open")
#             close_time = st.text_input("Closes At (HH:MM)", key="add_test_schedule_close")
#         else:
#             open_time = "00:00"
#             close_time = "00:00"

#         if st.button("Add Schedule"):
#             if not closed_flag and (not is_valid_time(open_time) or not is_valid_time(close_time)):
#                 st.error("Invalid time format (HH:MM)")
#             else:
#                 payload = {
#                     "test_id": selected_test_id,
#                     "day_of_week": day,
#                     "opens_at": open_time,
#                     "closes_at": close_time,
#                     "is_closed": 1 if closed_flag else 0,
#                 }
#                 r = requests.post(f"{API_BASE}/lab/test-schedule", json=payload, headers=auth_headers())
#                 if r.status_code == 200:
#                     st.success("Test schedule added!")
#                     st.rerun()
#                 else:
#                     st.error(r.text)

#     # -------------------
#     # TABLE HEADER
#     # -------------------
#     st.write("### Test Schedule Table")
#     header = st.columns([2, 2, 2, 1.5, 1.5])
#     header[0].markdown("**Day**")
#     header[1].markdown("**Opens**")
#     header[2].markdown("**Closes**")
#     header[3].markdown("**Closed**")
#     header[4].markdown("**Actions**")

#     if not schedules:
#         st.info("No schedule defined for this test.")
#         return

#     for s in schedules:
#         col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1.5, 1.5])
#         col1.write(day_names[s["day_of_week"]])
#         col2.write(s["opens_at"] if not s["is_closed"] else "-")
#         col3.write(s["closes_at"] if not s["is_closed"] else "-")
#         col4.write("❌" if s["is_closed"] else "✔️")

#         edit_btn = col5.button("✏️ Edit", key=f"edit_test_sched_{s['schedule_id']}")
#         del_btn = col5.button("🗑️ Delete", key=f"del_test_sched_{s['schedule_id']}")

#         if edit_btn:
#             st.session_state["edit_test_schedule"] = s
#         if del_btn:
#             st.session_state["delete_test_schedule"] = s

#         st.markdown('<hr style="margin:4px 0;">', unsafe_allow_html=True)

#     if "delete_test_schedule" in st.session_state:
#         item = st.session_state["delete_test_schedule"]
#         st.warning("Delete this test schedule?")
#         yes, no = st.columns(2)
#         if yes.button("Yes, Delete"):
#             r = requests.delete(f"{API_BASE}/lab/test-schedule/{item['schedule_id']}", headers=auth_headers())
#             if r.status_code == 200:
#                 st.success("Deleted successfully!")
#                 del st.session_state["delete_test_schedule"]
#                 st.rerun()
#             else:
#                 st.error(r.text)
#         if no.button("Cancel"):
#             del st.session_state["delete_test_schedule"]
#             st.rerun()

#     if "edit_test_schedule" in st.session_state:
#         item = st.session_state["edit_test_schedule"]
#         st.write("---")
#         st.subheader(f"✏️ Edit — {day_names[item['day_of_week']]}")

#         closed_flag = st.checkbox(
#             "Closed", 
#             value=bool(item["is_closed"]), 
#             key=f"edit_test_schedule_closed_{item['schedule_id']}"
#         )

#         if not closed_flag:
#             new_open = st.text_input(
#                 "Opens At", 
#                 value=item["opens_at"], 
#                 key=f"edit_test_schedule_open_{item['schedule_id']}"
#             )
#             new_close = st.text_input(
#                 "Closes At", 
#                 value=item["closes_at"], 
#                 key=f"edit_test_schedule_close_{item['schedule_id']}"
#             )
#         else:
#             new_open = "00:00"
#             new_close = "00:00"

#         save, cancel = st.columns(2)

#         if save.button("💾 Save"):
#             if not closed_flag and (not is_valid_time(new_open) or not is_valid_time(new_close)):
#                 st.error("Invalid time format")
#             else:
#                 payload = {
#                     "test_id": selected_test_id,
#                     "day_of_week": item["day_of_week"],
#                     "opens_at": new_open,
#                     "closes_at": new_close,
#                     "is_closed": 1 if closed_flag else 0,
#                 }
#                 r = requests.put(f"{API_BASE}/lab/test-schedule/{item['schedule_id']}", json=payload, headers=auth_headers())
#                 if r.status_code == 200:
#                     st.success("Updated successfully!")
#                     del st.session_state["edit_test_schedule"]
#                     st.rerun()
#                 else:
#                     st.error(r.text)
#         if cancel.button("Cancel"):
#             del st.session_state["edit_test_schedule"]
#             st.rerun()