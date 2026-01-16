from .frontend_common import *


# ---------------------------------
# DOCTOR HOLIDAYS (DISPLAY-IMPROVED)
# ---------------------------------
def render_doctor_holidays():
    st.subheader("👨‍⚕️ Doctor Holidays / Short Leaves")

    doctors = api_get(f"{API_BASE}/lab/doctors")
    holidays = api_get(f"{API_BASE}/lab/doctor-holidays")

    if doctors is None or holidays is None:
        st.error("Failed to load data")
        return

    # =============================
    # SEARCH / FILTER DOCTORS
    # =============================
    st.markdown("### 🔍 Search Doctors")

    c1, c2 = st.columns([3, 2])
    search = c1.text_input("Doctor Name")
    spec = c2.selectbox(
        "Specialization",
        ["All"] + sorted({d["specialization"] for d in doctors})
    )

    filtered_doctors = [
        d for d in doctors
        if (not search or search.lower() in d["doctor_name"].lower())
        and (spec == "All" or d["specialization"] == spec)
    ]

    # =============================
    # DOCTORS TABLE
    # =============================
    st.markdown("### 👨‍⚕️ Doctors")

    header = st.columns([3, 3, 3, 2])
    header[0].markdown("**Name**")
    header[1].markdown("**Specialization**")
    header[2].markdown("**Contact**")
    header[3].markdown("**Action**")

    if not filtered_doctors:
        st.info("No doctors found")
        return

    for d in filtered_doctors:
        c1, c2, c3, c4 = st.columns([3, 3, 3, 2])
        c1.write(d["doctor_name"])
        c2.write(d["specialization"])
        c3.write(d.get("contact_info") or "-")

        if c4.button("Select", key=f"select_{d['doctor_id']}"):
            st.session_state["selected_doctor"] = d
            st.session_state.pop("edit_holiday_id", None)
            st.session_state.pop("delete_holiday_id", None)
            st.rerun()

        st.markdown('<hr style="margin:3px 0;">', unsafe_allow_html=True)

    # =============================
    # NO DOCTOR SELECTED → STOP
    # =============================
    if "selected_doctor" not in st.session_state:
        return

    doc = st.session_state["selected_doctor"]
    st.markdown(f"## 📅 Holidays – Dr. {doc['doctor_name']}")

    # =============================
    # ADD HOLIDAY
    # =============================
    with st.expander("➕ Add Holiday"):
        date = st.text_input("Date (YYYY-MM-DD)", key="add_date")
        full = st.checkbox("Full Day", key="add_full")

        if not full:
            open_t = st.text_input("Opens At (HH:MM)", key="add_open")
            close_t = st.text_input("Closes At (HH:MM)", key="add_close")
        else:
            open_t, close_t = "00:00", "00:00"

        if st.button("Add Holiday", key="add_btn"):
            payload = {
                "doctor_id": doc["doctor_id"],
                "doctor_name": doc["doctor_name"],
                "date": date,
                "opens_at": open_t,
                "closes_at": close_t,
                "is_closed": 1 if full else 0
            }

            r = requests.post(
                f"{API_BASE}/lab/doctor-holidays",
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
    doc_holidays = [
        h for h in holidays
        if h["doctor_id"] == doc["doctor_id"]
    ]

    if not doc_holidays:
        st.info("No holidays")
        return

    header = st.columns([3, 2, 2, 2, 2])
    header[0].markdown("**Date**")
    header[1].markdown("**Open**")
    header[2].markdown("**Close**")
    header[3].markdown("**Edit**")
    header[4].markdown("**Delete**")

    for hday in doc_holidays:
        c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 2])
        c1.write(hday["date"])
        c2.write(hday["opens_at"] if not hday["is_closed"] else "-")
        c3.write(hday["closes_at"] if not hday["is_closed"] else "-")

        if c4.button("✏️", key=f"edit_{hday['doctor_holiday_id']}"):
            st.session_state["edit_holiday_id"] = hday["doctor_holiday_id"]

        if c5.button("🗑️", key=f"del_{hday['doctor_holiday_id']}"):
            st.session_state["delete_holiday_id"] = hday["doctor_holiday_id"]

        st.markdown('<hr style="margin:2px 0;">', unsafe_allow_html=True)

    # =============================
    # EDIT HOLIDAY
    # =============================
    if "edit_holiday_id" in st.session_state:
        item = next(
            h for h in doc_holidays
            if h["doctor_holiday_id"] == st.session_state["edit_holiday_id"]
        )

        st.markdown("### ✏️ Edit Holiday")

        full = st.checkbox("Full Day", value=item["is_closed"], key="edit_full")
        if not full:
            open_t = st.text_input("Opens At", value=item["opens_at"], key="edit_open")
            close_t = st.text_input("Closes At", value=item["closes_at"], key="edit_close")
        else:
            open_t, close_t = "00:00", "00:00"

        if st.button("Save Changes"):
            payload = {
                "doctor_id": doc["doctor_id"],
                "doctor_name": doc["doctor_name"],
                "date": item["date"],
                "opens_at": open_t,
                "closes_at": close_t,
                "is_closed": 1 if full else 0
            }

            r = requests.put(
                f"{API_BASE}/lab/doctor-holidays/{item['doctor_holiday_id']}",
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
        if c1.button("Yes, Delete"):
            r = requests.delete(
                f"{API_BASE}/lab/doctor-holidays/{hid}",
                headers=auth_headers()
            )

            if r.status_code == 200:
                st.success("Deleted")
                st.session_state.pop("delete_holiday_id")
                st.rerun()
            else:
                st.error(r.text)

        if c2.button("Cancel"):
            st.session_state.pop("delete_holiday_id")
            st.rerun()
