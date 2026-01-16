from .frontend_common import *

# ---------------------------------
# TEST-DOCTOR ASSIGNMENTS (FRONTEND)
# ---------------------------------

# ---------------------------------
# TEST-DOCTOR ASSIGNMENTS (DISPLAY-IMPROVED)
# ---------------------------------
def render_test_doctor_assignments():
    st.subheader("🧪 Assign Tests to Doctors")

    # -----------------------------
    # FETCH DATA
    # -----------------------------
    doctors = api_get(f"{API_BASE}/lab/doctors")
    tests = api_get(f"{API_BASE}/lab/tests")
    assignments = api_get(f"{API_BASE}/lab/test-doctor-assignments")

    if doctors is None or tests is None or assignments is None:
        st.error("Failed to load data")
        return

    # =============================
    # STATE INIT
    # =============================
    if "show_assignments" not in st.session_state:
        st.session_state["show_assignments"] = False

    # =============================
    # TOGGLE BUTTON
    # =============================
    if st.button("📋 Show / Hide Assigned Tests"):
        st.session_state["show_assignments"] = not st.session_state["show_assignments"]

    # =============================
    # ASSIGNED TESTS TABLE
    # =============================
    st.markdown("### 🗂️ Assigned Tests")

    keyword = st.text_input(
        "Search assigned (doctor / specialization / test / category)",
        key="assigned_keyword"
    )

    def match_assignment(a, kw):
        kw = kw.lower()
        return (
            kw in a["doctor_name"].lower()
            or kw in (a.get("doctor_specialization") or "").lower()
            or kw in a["test_name"].lower()
            or kw in (a.get("test_category") or "").lower()
        )

    show_table = False
    if keyword:
        filtered_assignments = [a for a in assignments if match_assignment(a, keyword)]
        show_table = True
    elif st.session_state["show_assignments"]:
        filtered_assignments = assignments
        show_table = True
    else:
        filtered_assignments = []

    if show_table:
        if not filtered_assignments:
            st.info("No matching assigned tests")
        else:
            header = st.columns([3, 3, 3, 2])
            header[0].markdown("**Doctor Name**")
            header[1].markdown("**Test (Category)**")
            header[2].markdown("**Specialization**")
            header[3].markdown("**Action**")

            for a in filtered_assignments:
                c1, c2, c3, c4 = st.columns([3, 3, 3, 2])
                c1.write(a["doctor_name"])
                c2.write(f"{a['test_name']} ({a.get('test_category', '-')})")
                c3.write(a.get("doctor_specialization", "-"))
                if c4.button("🗑️", key=f"del_assignment_{a['assignment_id']}"):
                    st.session_state["delete_assignment_id"] = a["assignment_id"]
                st.markdown('<hr style="margin:2px 0;">', unsafe_allow_html=True)

    # =============================
    # DELETE CONFIRMATION
    # =============================
    if "delete_assignment_id" in st.session_state:
        del_id = st.session_state["delete_assignment_id"]
        st.warning("Confirm deletion of this assignment?")

        c1, c2 = st.columns(2)
        if c1.button("Yes, Delete", key="yes_del_assign"):
            r = requests.delete(
                f"{API_BASE}/lab/test-doctor-assignments/{del_id}",
                headers=auth_headers()
            )
            if r.status_code == 200:
                st.success("Deleted successfully")
                st.session_state.pop("delete_assignment_id")
                st.rerun()
            else:
                st.error(r.text)

        if c2.button("Cancel", key="no_del_assign"):
            st.session_state.pop("delete_assignment_id")
            st.rerun()

    st.markdown("---")

    # =============================
    # DOCTOR FILTER (NEW ASSIGN)
    # =============================
    st.markdown("### 🔍 Select Doctor")

    doc_name_filter = st.text_input("Doctor Name", key="search_doc")
    doc_spec_filter = st.selectbox(
        "Specialization",
        ["None", "All"] + sorted({d["specialization"] for d in doctors}),
        key="spec_filter"
    )

    filtered_doctors = []
    for d in doctors:
        if doc_spec_filter == "None" and not doc_name_filter:
            continue
        if doc_name_filter and doc_name_filter.lower() not in d["doctor_name"].lower():
            continue
        if doc_spec_filter not in ["None", "All"] and d["specialization"] != doc_spec_filter:
            continue
        filtered_doctors.append(d)

    for d in filtered_doctors:
        c1, c2, c3, c4 = st.columns([3, 3, 2, 2])
        c1.write(d["doctor_name"])
        c2.write(d["specialization"])
        c3.write(d.get("contact_info") or "-")
        if c4.button("Select Doctor", key=f"select_doc_{d['doctor_id']}"):
            st.session_state["selected_doctor_assignment"] = d
            st.rerun()
        st.markdown('<hr style="margin:2px 0;">', unsafe_allow_html=True)

    if "selected_doctor_assignment" not in st.session_state:
        st.info("Select a doctor to assign tests")
        return

    doctor = st.session_state["selected_doctor_assignment"]
    st.markdown(f"### Selected Doctor: {doctor['doctor_name']} ({doctor['specialization']})")

    # =============================
    # TEST FILTER
    # =============================
    st.markdown("### 🔍 Select Test")

    test_name_filter = st.text_input("Test Name", key="search_test")
    test_category_filter = st.selectbox(
        "Category",
        ["None", "All"] + sorted({t.get("category") for t in tests if t.get("category")}),
        key="test_category_filter"
    )

    filtered_tests = []
    for t in tests:
        if test_category_filter == "None" and not test_name_filter:
            continue
        if test_name_filter and test_name_filter.lower() not in t["test_name"].lower():
            continue
        if test_category_filter not in ["None", "All"] and t.get("category") != test_category_filter:
            continue
        filtered_tests.append(t)

    for t in filtered_tests:
        c1, c2, c3 = st.columns([4, 3, 2])
        c1.write(t["test_name"])
        c2.write(t.get("category") or "-")
        if c3.button("Select Test", key=f"select_test_{t['test_id']}"):
            st.session_state["selected_test_assignment"] = t
            st.rerun()
        st.markdown('<hr style="margin:2px 0;">', unsafe_allow_html=True)

    if "selected_test_assignment" not in st.session_state:
        st.info("Select a test to assign")
        return

    test = st.session_state["selected_test_assignment"]
    st.markdown(f"### Selected Test: {test['test_name']} ({test.get('category', '-')})")

    # =============================
    # ASSIGN
    # =============================
    if st.button("Assign Test to Doctor"):
        payload = {
            "doctor_id": doctor["doctor_id"],
            "test_id": test["test_id"]
        }
        r = requests.post(
            f"{API_BASE}/lab/test-doctor-assignments",
            json=payload,
            headers=auth_headers()
        )

        if r.status_code == 200:
            st.session_state["assignment_success_msg"] = f"✅ Test '{test['test_name']}' assigned to Dr. {doctor['doctor_name']} successfully!"
            st.session_state.pop("selected_test_assignment", None)
            st.session_state.pop("selected_doctor_assignment", None)
        else:
            st.error(r.text)

    # =============================
    # SHOW SUCCESS MESSAGE
    # =============================
    if "assignment_success_msg" in st.session_state:
        st.success(st.session_state.pop("assignment_success_msg"))