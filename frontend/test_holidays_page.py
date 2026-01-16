from .frontend_common import *

# ---------------------------------
# TEST HOLIDAYS (STABLE + SAFE)
# ---------------------------------
# ---------------------------------
# TEST HOLIDAYS (DISPLAY-IMPROVED)
# ---------------------------------
def render_test_holidays():
    st.subheader("🧪 Test Holidays / Short Leaves")

    # -----------------------------
    # FETCH TESTS AND HOLIDAYS
    # -----------------------------
    tests = api_get(f"{API_BASE}/lab/tests")
    holidays = api_get(f"{API_BASE}/lab/test-holidays")

    if tests is None or holidays is None:
        st.error("Failed to load data")
        return

    # =============================
    # SEARCH / FILTER TESTS
    # =============================
    st.markdown("### 🔍 Search Tests")

    c1, c2 = st.columns([3, 2])
    search = c1.text_input("Test Name")
    category = c2.selectbox(
        "Category",
        ["All"] + sorted({t.get("category") for t in tests if t.get("category")})
    )

    filtered_tests = [
        t for t in tests
        if (not search or search.lower() in t["test_name"].lower())
        and (category == "All" or t.get("category") == category)
    ]

    # =============================
    # TESTS TABLE
    # =============================
    st.markdown("### 🧪 Tests")

    header = st.columns([3, 3, 2, 2])
    header[0].markdown("**Name**")
    header[1].markdown("**Category**")
    header[2].markdown("**Price**")
    header[3].markdown("**Action**")

    if not filtered_tests:
        st.info("No tests found")
        return

    for t in filtered_tests:
        c1, c2, c3, c4 = st.columns([3, 3, 2, 2])
        c1.write(t["test_name"])
        c2.write(t.get("category") or "-")
        c3.write(t.get("price") or "-")

        if c4.button("Select", key=f"select_{t['test_id']}"):
            st.session_state["selected_test"] = t
            st.session_state.pop("edit_holiday_id", None)
            st.session_state.pop("delete_holiday_id", None)
            st.rerun()

        st.markdown('<hr style="margin:3px 0;">', unsafe_allow_html=True)

    # =============================
    # NO TEST SELECTED → STOP
    # =============================
    if "selected_test" not in st.session_state:
        return

    test = st.session_state["selected_test"]
    st.markdown(f"## 📅 Holidays – {test['test_name']}")

    # =============================
    # ADD HOLIDAY
    # =============================
    with st.expander("➕ Add Holiday"):
        date = st.text_input("Date (YYYY-MM-DD)", key="add_date_test")
        full = st.checkbox("Full Day", key="add_full_test")

        if not full:
            open_t = st.text_input("Opens At (HH:MM)", key="add_open_test")
            close_t = st.text_input("Closes At (HH:MM)", key="add_close_test")
        else:
            open_t, close_t = "00:00", "00:00"

        if st.button("Add Holiday", key="add_btn_test"):
            payload = {
                "test_id": test["test_id"],
                "test_name": test["test_name"],
                "date": date,
                "opens_at": open_t,
                "closes_at": close_t,
                "is_closed": 1 if full else 0
            }

            r = requests.post(
                f"{API_BASE}/lab/test-holidays",
                json=payload,
                headers=auth_headers()
            )

            if r.status_code == 200:
                st.success("Holiday added")
                st.rerun()
            else:
                st.error(r.text)

    # =============================
    # HOLIDAYS TABLE
    # =============================
    test_holidays = [h for h in holidays if h["test_id"] == test["test_id"]]

    if not test_holidays:
        st.info("No holidays")
        return

    header = st.columns([3, 2, 2, 2, 2])
    header[0].markdown("**Date**")
    header[1].markdown("**Open**")
    header[2].markdown("**Close**")
    header[3].markdown("**Edit**")
    header[4].markdown("**Delete**")

    for hday in test_holidays:
        c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 2])
        c1.write(hday["date"])
        c2.write(hday["opens_at"] if not hday["is_closed"] else "-")
        c3.write(hday["closes_at"] if not hday["is_closed"] else "-")

        if c4.button("✏️", key=f"edit_{hday['test_holiday_id']}"):
            st.session_state["edit_holiday_id"] = hday["test_holiday_id"]

        if c5.button("🗑️", key=f"del_{hday['test_holiday_id']}"):
            st.session_state["delete_holiday_id"] = hday["test_holiday_id"]

        st.markdown('<hr style="margin:2px 0;">', unsafe_allow_html=True)

    # =============================
    # EDIT HOLIDAY
    # =============================
    if "edit_holiday_id" in st.session_state:
        item = next(
            (h for h in test_holidays if h["test_holiday_id"] == st.session_state["edit_holiday_id"]),
            None
        )
        if item is None:
            st.warning("Selected holiday not found.")
            st.session_state.pop("edit_holiday_id")
            st.stop()

        st.markdown("### ✏️ Edit Holiday")

        # Editable date
        date = st.text_input("Date (YYYY-MM-DD)", value=item["date"], key="edit_date")

        full = st.checkbox("Full Day", value=item["is_closed"], key="edit_full")
        if not full:
            open_t = st.text_input("Opens At", value=item["opens_at"], key="edit_open")
            close_t = st.text_input("Closes At", value=item["closes_at"], key="edit_close")
        else:
            open_t, close_t = "00:00", "00:00"

        if st.button("Save Changes"):
            payload = {
                "test_id": item["test_id"],
                "test_name": item["test_name"],
                "date": date,
                "opens_at": open_t,
                "closes_at": close_t,
                "is_closed": 1 if full else 0
            }

            r = requests.put(
                f"{API_BASE}/lab/test-holidays/{item['test_holiday_id']}",
                json=payload,
                headers=auth_headers()
            )

            if r.status_code == 200:
                st.success("Updated")
                st.session_state.pop("edit_holiday_id")
                st.rerun()
            else:
                st.error(r.text)

    # =============================
    # DELETE HOLIDAY
    # =============================
    if "delete_holiday_id" in st.session_state:
        hid = st.session_state["delete_holiday_id"]
        st.warning("Confirm delete?")

        c1, c2 = st.columns(2)
        if c1.button("Yes, Delete", key="yes_del_test"):
            r = requests.delete(
                f"{API_BASE}/lab/test-holidays/{hid}",
                headers=auth_headers()
            )

            if r.status_code == 200:
                st.success("Deleted")
                st.session_state.pop("delete_holiday_id")
                st.rerun()
            else:
                st.error(r.text)

        if c2.button("Cancel", key="no_del_test"):
            st.session_state.pop("delete_holiday_id")
            st.rerun()