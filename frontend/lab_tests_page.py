from .frontend_common import *

# ---------------------------------
# LAB TESTS TABLE UI (FULL CRUD) WITH SEARCH & FILTER
# ---------------------------------
def render_lab_tests():
    st.subheader("🧪 Lab Tests Management")

    tests = api_get(f"{API_BASE}/lab/tests")
    if tests is None:
        st.error("Failed to fetch tests.")
        return

    with st.expander("➕ Add New Test"):
        new_test_name = st.text_input("Test Name", key="new_test_name")
        new_category = st.selectbox("Category", ["normal", "special"], key="new_test_category")
        new_price = st.number_input("Price", min_value=0.0, step=0.01, key="new_test_price")
        new_duration = st.text_input("Duration (e.g., 30 min)", key="new_test_duration")
        new_requires_booking = st.checkbox("Requires Booking", key="new_test_booking")
        new_requires_doctor = st.checkbox("Requires Doctor", key="new_test_doctor")

        if st.button("Add Test"):
            if not new_test_name:
                st.error("Please enter a test name.")
            else:
                payload = {
                    "test_name": new_test_name,
                    "category": new_category,
                    "price": new_price,
                    "duration": new_duration,
                    "requires_booking": 1 if new_requires_booking else 0,
                    "requires_doctor": 1 if new_requires_doctor else 0,
                }
                r = requests.post(f"{API_BASE}/lab/tests", json=payload, headers=auth_headers())
                if r.status_code == 200:
                    st.success("Test added successfully!")
                    st.rerun()
                else:
                    st.error(r.text)

    st.write("### Search & Filter")
    search_col, cat_col, booking_col, doctor_col = st.columns([3, 2, 2, 2])

    search_text = search_col.text_input("Search Test by Name")
    filter_category = cat_col.selectbox("Category", ["All", "normal", "special"])
    filter_booking = booking_col.selectbox("Requires Booking", ["All", "Yes", "No"])
    filter_doctor = doctor_col.selectbox("Requires Doctor", ["All", "Yes", "No"])

    filtered_tests = []
    for t in tests:
        if search_text and search_text.lower() not in t["test_name"].lower():
            continue
        if filter_category != "All" and t["category"] != filter_category:
            continue
        if filter_booking != "All":
            if filter_booking == "Yes" and not t["requires_booking"]:
                continue
            if filter_booking == "No" and t["requires_booking"]:
                continue
        if filter_doctor != "All":
            if filter_doctor == "Yes" and not t["requires_doctor"]:
                continue
            if filter_doctor == "No" and t["requires_doctor"]:
                continue
        filtered_tests.append(t)

    st.write("### Tests Table")
    header_cols = st.columns([3, 2, 2, 2, 2, 2, 2])
    header_cols[0].markdown("**Test Name**")
    header_cols[1].markdown("**Category**")
    header_cols[2].markdown("**Price**")
    header_cols[3].markdown("**Duration**")
    header_cols[4].markdown("**Booking**")
    header_cols[5].markdown("**Doctor**")
    header_cols[6].markdown("**Actions**")

    if not filtered_tests:
        st.info("No tests found.")
        return

    for t in filtered_tests:
        col1, col2, col3, col4, col5, col6, col7 = st.columns([3, 2, 2, 2, 2, 2, 2])
        col1.write(format_display(t["test_name"]))
        col2.write(format_display(t["category"]))
        col3.write(t["price"])
        col4.write(t["duration"])
        col5.write("✔️" if t["requires_booking"] else "❌")
        col6.write("✔️" if t["requires_doctor"] else "❌")

        edit_btn = col7.button("✏️ Edit", key=f"edit_test_{t['test_id']}")
        delete_btn = col7.button("🗑️ Delete", key=f"delete_test_{t['test_id']}")

        if edit_btn:
            st.session_state["edit_test"] = t
        if delete_btn:
            st.session_state["delete_test"] = t

        st.markdown('<hr style="margin:4px 0;">', unsafe_allow_html=True)

    if "delete_test" in st.session_state:
        item = st.session_state["delete_test"]
        st.warning(f"Are you sure you want to delete test '{format_display(item['test_name'])}'?")
        del_btn, cancel_btn = st.columns(2)
        if del_btn.button("Yes, Delete"):
            r = requests.delete(f"{API_BASE}/lab/tests/{item['test_id']}", headers=auth_headers())
            if r.status_code == 200:
                st.success("Deleted successfully!")
                del st.session_state["delete_test"]
                st.rerun()
            else:
                st.error(r.text)
        if cancel_btn.button("Cancel"):
            del st.session_state["delete_test"]
            st.rerun()

    if "edit_test" in st.session_state:
        item = st.session_state["edit_test"]
        st.write("---")
        st.subheader(f"✏️ Edit Test — {format_display(item['test_name'])}")

        new_name = st.text_input("Test Name", value=item["test_name"])
        new_category = st.selectbox("Category", ["normal", "special"], index=0 if item["category"]=="normal" else 1)
        new_price = st.number_input("Price", min_value=0.0, step=0.01, value=item["price"])
        new_duration = st.text_input("Duration (e.g., 30 min)", value=item["duration"])
        new_requires_booking = st.checkbox(
            "Requires Booking", 
            value=bool(item["requires_booking"]), 
            key=f"edit_test_booking_{item['test_id']}"
        )
        new_requires_doctor = st.checkbox(
            "Requires Doctor", 
            value=bool(item["requires_doctor"]), 
            key=f"edit_test_doctor_{item['test_id']}"
        )

        save_btn, cancel_btn = st.columns(2)
        if save_btn.button("💾 Save"):
            if not new_name:
                st.error("Test name cannot be empty.")
            else:
                payload = {
                    "test_name": new_name,
                    "category": new_category,
                    "price": new_price,
                    "duration": new_duration,
                    "requires_booking": 1 if new_requires_booking else 0,
                    "requires_doctor": 1 if new_requires_doctor else 0,
                }
                r = requests.put(f"{API_BASE}/lab/tests/{item['test_id']}", json=payload, headers=auth_headers())
                if r.status_code == 200:
                    st.success("Updated successfully!")
                    del st.session_state["edit_test"]
                    st.rerun()
                else:
                    st.error(r.text)
        if cancel_btn.button("Cancel"):
            del st.session_state["edit_test"]
            st.rerun()
