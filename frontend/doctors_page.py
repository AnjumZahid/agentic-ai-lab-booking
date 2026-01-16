from .frontend_common import *


# ---------------------------------
# DOCTORS MANAGEMENT UI
# ---------------------------------
def render_doctors():
    st.subheader("👨‍⚕️ Doctors Management")

    doctors = api_get(f"{API_BASE}/lab/doctors")
    if doctors is None:
        st.error("Failed to fetch doctors.")
        return

    # ADD NEW DOCTOR
    with st.expander("➕ Add New Doctor"):
        new_name = st.text_input("Doctor Name", key="new_doctor_name")
        new_spec = st.text_input("Specialization", key="new_doctor_spec")
        new_contact = st.text_input("Contact Info (optional)", key="new_doctor_contact")

        if st.button("Add Doctor"):
            if not new_name or not new_spec:
                st.error("Please enter name and specialization.")
            else:
                payload = {
                    "doctor_name": new_name,
                    "specialization": new_spec,
                    "contact_info": new_contact
                }
                r = requests.post(f"{API_BASE}/lab/doctors", json=payload, headers=auth_headers())
                if r.status_code == 200:
                    st.success("Doctor added successfully!")
                    st.rerun()
                else:
                    st.error(r.text)

    # SEARCH & FILTER
    st.write("### Search & Filter")
    search_col, spec_col = st.columns([3, 2])
    search_text = search_col.text_input("Search by Name")
    filter_spec = spec_col.selectbox(
        "Filter by Specialization",
        ["All"] + sorted(list({d["specialization"] for d in doctors}))
    )

    filtered_doctors = []
    for d in doctors:
        if search_text and search_text.lower() not in d["doctor_name"].lower():
            continue
        if filter_spec != "All" and d["specialization"] != filter_spec:
            continue
        filtered_doctors.append(d)

    st.write("### Doctors Table")
    header_cols = st.columns([3, 3, 3, 2])
    header_cols[0].markdown("**Doctor Name**")
    header_cols[1].markdown("**Specialization**")
    header_cols[2].markdown("**Contact Info**")
    header_cols[3].markdown("**Actions**")

    if not filtered_doctors:
        st.info("No doctors found.")
        return

    for d in filtered_doctors:
        col1, col2, col3, col4 = st.columns([3, 3, 3, 2])
        col1.write(format_display(d["doctor_name"]))
        col2.write(format_display(d["specialization"]))
        col3.write(d["contact_info"] if d["contact_info"] else "-")

        edit_btn = col4.button("✏️ Edit", key=f"edit_doctor_{d['doctor_id']}")
        delete_btn = col4.button("🗑️ Delete", key=f"delete_doctor_{d['doctor_id']}")

        if edit_btn:
            st.session_state["edit_doctor"] = d
        if delete_btn:
            st.session_state["delete_doctor"] = d

        st.markdown('<hr style="margin:4px 0;">', unsafe_allow_html=True)

    # DELETE CONFIRM
    if "delete_doctor" in st.session_state:
        item = st.session_state["delete_doctor"]
        st.warning(f"Are you sure you want to delete Dr. {format_display(item['doctor_name'])}?")
        yes, no = st.columns(2)
        if yes.button("Yes, Delete"):
            r = requests.delete(f"{API_BASE}/lab/doctors/{item['doctor_id']}", headers=auth_headers())
            if r.status_code == 200:
                st.success("Deleted successfully!")
                del st.session_state["delete_doctor"]
                st.rerun()
            else:
                st.error(r.text)
        if no.button("Cancel"):
            del st.session_state["delete_doctor"]
            st.rerun()

    # EDIT POPUP
    if "edit_doctor" in st.session_state:
        item = st.session_state["edit_doctor"]
        st.write("---")
        st.subheader(f"✏️ Edit Doctor — {format_display(item['doctor_name'])}")

        new_name = st.text_input("Doctor Name", value=item["doctor_name"])
        new_spec = st.text_input("Specialization", value=item["specialization"])
        new_contact = st.text_input("Contact Info", value=item["contact_info"] if item["contact_info"] else "")

        save_btn, cancel_btn = st.columns(2)
        if save_btn.button("💾 Save"):
            if not new_name or not new_spec:
                st.error("Name and specialization cannot be empty.")
            else:
                payload = {
                    "doctor_name": new_name,
                    "specialization": new_spec,
                    "contact_info": new_contact
                }
                r = requests.put(f"{API_BASE}/lab/doctors/{item['doctor_id']}", json=payload, headers=auth_headers())
                if r.status_code == 200:
                    st.success("Updated successfully!")
                    del st.session_state["edit_doctor"]
                    st.rerun()
                else:
                    st.error(r.text)
        if cancel_btn.button("Cancel"):
            del st.session_state["edit_doctor"]
            st.rerun()