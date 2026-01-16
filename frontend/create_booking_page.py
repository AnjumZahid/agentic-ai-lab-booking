from .frontend_common import *



# ---------------------------------
# CREATE / UPDATE / DELETE BOOKING (DISPLAY-IMPROVED)
# ---------------------------------
def render_create_booking():
    st.subheader("📅 Create / Manage Bookings")

    tests = api_get(f"{API_BASE}/lab/tests")
    assignments = api_get(f"{API_BASE}/lab/test-doctor-assignments")

    if not tests or not assignments:
        st.error("Failed to load tests or assignments")
        return

    # =============================
    # Initialize state
    # =============================
    if "show_all_tests" not in st.session_state:
        st.session_state["show_all_tests"] = False
    if "show_booked_tests" not in st.session_state:
        st.session_state["show_booked_tests"] = False
    if "booking_search" not in st.session_state:
        st.session_state["booking_search"] = ""

    # =============================
    # Always visible button for booked tests
    # =============================
    if st.button("View All Booked Tests"):
        st.session_state["show_booked_tests"] = not st.session_state["show_booked_tests"]

    # =============================
    # Show already booked tests
    # =============================
    if st.session_state["show_booked_tests"]:
        bookings = api_get(f"{API_BASE}/lab/bookings") or []

        booking_search = st.text_input(
            "Filter Booked Tests by Patient or Test Name",
            key="booking_search"
        )

        filtered_bookings = bookings
        if booking_search:
            filtered_bookings = [
                b for b in bookings
                if booking_search.lower() in b.get("patient_name", "").lower()
                or booking_search.lower() in b.get("test_name", "").lower()
            ]

        if filtered_bookings:
            header = st.columns([3, 3, 2, 2, 2, 3])
            header[0].markdown("**Patient Name**")
            header[1].markdown("**Test Name**")
            header[2].markdown("**Doctor**")
            header[3].markdown("**Date**")
            header[4].markdown("**Time**")
            header[5].markdown("**Actions**")

            for b in filtered_bookings:
                c1, c2, c3, c4, c5, c6 = st.columns([3, 3, 2, 2, 2, 3])
                c1.write(format_display(b.get("patient_name", "-")))
                c2.write(format_display(b.get("test_name", "-")))   # ✅ use .get()
                c3.write(format_display(b.get("doctor_name", "-"))) # ✅ use .get()
                c4.write(b.get("booking_date", "-"))
                c5.write(b.get("booking_time", "-"))


                # -----------------------------
                # Actions: Update / Delete
                # -----------------------------
                if c6.button("Update", key=f"update_{b['booking_id']}"):
                    st.session_state["edit_booking"] = b
                    st.rerun()

                if c6.button("Delete", key=f"delete_{b['booking_id']}"):
                    r = requests.delete(f"{API_BASE}/lab/bookings/{b['booking_id']}", headers=auth_headers())
                    if r.status_code == 200:
                        st.success("Booking deleted successfully")
                        st.rerun()
                    else:
                        st.error(r.json().get("detail", "Failed to delete"))

        else:
            st.info("No booked tests to display.")

    st.markdown("---")

    # =============================
    # Search / Show Tests
    # =============================
    search_query = st.text_input("Search Test by Name", key="search_test_input")
    c1, c2 = st.columns([1, 1])
    if c1.button("Show All Tests"):
        st.session_state["show_all_tests"] = True
    if c2.button("Hide All Tests"):
        st.session_state["show_all_tests"] = False

    if search_query:
        filtered_tests = [t for t in tests if search_query.lower() in t["test_name"].lower()]
    elif st.session_state["show_all_tests"]:
        filtered_tests = tests
    else:
        filtered_tests = []

    if filtered_tests:
        header = st.columns([4, 2, 2])
        header[0].markdown("**Test Name**")
        header[1].markdown("**Price**")
        header[2].markdown("**Duration**")

        for t in filtered_tests:
            c1, c2, c3 = st.columns([4, 2, 2])
            c1.write(format_display(t["test_name"]))
            c2.write(f"{t.get('price', '-')}")
            c3.write(f"{t.get('duration', '-')}")
            if st.button("Select Test", key=f"select_test_{t['test_id']}"):
                st.session_state["selected_test"] = t
                st.rerun()
            st.markdown('<hr style="margin:2px 0;">', unsafe_allow_html=True)
    else:
        st.info("No tests to display.")

    # =============================
    # Check if editing booking
    # =============================
    if "edit_booking" in st.session_state:
        edit = st.session_state["edit_booking"]
        st.subheader("✏️ Update Booking")

        patient_name = st.text_input("Patient Name", value=edit["patient_name"])
        patient_mobile = st.text_input("Patient Mobile", value=edit["patient_mobile"])
        booking_date = st.date_input(
        "Booking Date",
        value=datetime.strptime(edit["booking_date"], "%Y-%m-%d").date()
)

        # Pre-select test
        test = next((t for t in tests if t["test_id"] == edit["test_id"]), None)
        st.markdown(f"**Test:** {format_display(test['test_name']) if test else '-'}")
        doctor_id = edit.get("doctor_id")
        doctor_name = edit.get("doctor_name")

        # Windows dropdown with available slots
        windows_with_slots = api_get(f"{API_BASE}/lab/available-slots/{test['test_id']}/{booking_date}") or []
        selected_window_label = f"{edit['window_start']} - {edit['window_end']} ({next((w['available_slots'] for w in windows_with_slots if w['window_id']==edit['window_id']), 0)} slots available)"
        selected_window = next((w for w in windows_with_slots if w['window_id']==edit['window_id']), None)

        if st.button("Save Changes"):
            payload = {
                "test_id": test["test_id"],
                "window_id": selected_window["window_id"],
                "doctor_id": doctor_id,
                "doctor_name": doctor_name,
                "patient_name": patient_name,
                "patient_mobile": patient_mobile,
                "booking_date": str(booking_date),
                "booking_time": selected_window["window_start"],
                "window_start": selected_window["window_start"],
                "window_end": selected_window["window_end"],
            }
            r = requests.put(f"{API_BASE}/lab/bookings/{edit['booking_id']}", json=payload, headers=auth_headers())
            if r.status_code == 200:
                st.success("Booking updated successfully")
                st.session_state.pop("edit_booking")
                st.rerun()
            else:
                st.error(r.json().get("detail", "Failed to update booking"))
        return  # Stop here if editing

    # =============================
    # Normal create booking flow
    # =============================
    if "selected_test" not in st.session_state:
        return

    test = st.session_state["selected_test"]

    # Assigned doctor
    assigned = next((a for a in assignments if a["test_id"] == test["test_id"]), None)
    doctor_id = assigned["doctor_id"] if assigned else None
    doctor_name = assigned["doctor_name"] if assigned else None
    st.markdown(f"**Assigned Doctor:** {format_display(doctor_name) if doctor_name else '-'}")

    # Patient details
    patient_name = st.text_input("Patient Name")
    patient_mobile = st.text_input("Patient Mobile")
    booking_date = st.date_input("Booking Date")

    # DYNAMIC WINDOWS DROPDOWN WITH AVAILABLE SLOTS
    if booking_date:
        windows_with_slots = api_get(
            f"{API_BASE}/lab/available-slots/{test['test_id']}/{booking_date}"
        ) or []

        if not windows_with_slots:
            st.warning("No available windows for this test on the selected date.")
            return

        # Only show windows with available slots > 0
        available_window_options = [
            f"{w['window_start']} - {w['window_end']} ({w['available_slots']} slots available)"
            for w in windows_with_slots if w['available_slots'] > 0
        ]

        if not available_window_options:
            st.warning("All windows are fully booked for this date.")
            return

        selected_window_label = st.selectbox("Select Window", available_window_options)
        selected_window = next(w for w in windows_with_slots if
                               f"{w['window_start']} - {w['window_end']} ({w['available_slots']} slots available)" == selected_window_label)
    else:
        st.info("Please select a booking date first to see available windows.")
        return

    # Submit Booking
    create_btn = st.button("Create Booking")
    success_box = st.empty()

    if st.session_state.get("booking_success"):
        success_box.success("Booking created successfully!")
        st.session_state.pop("selected_test", None)
        del st.session_state["booking_success"]

    if create_btn:
        if not patient_name or not patient_mobile:
            st.error("Patient name and mobile are required!")
            return

        payload = {
            "test_id": test["test_id"],
            "window_id": selected_window["window_id"],
            "doctor_id": doctor_id,
            "patient_name": patient_name,
            "patient_mobile": patient_mobile,
            "booking_date": str(booking_date),
            "booking_time": selected_window["window_start"],
            "window_start": selected_window["window_start"],
            "window_end": selected_window["window_end"],
        }

        r = requests.post(
            f"{API_BASE}/lab/bookings",
            json=payload,
            headers=auth_headers()
        )

        if r.status_code == 200 and "booking_id" in r.json():
            st.session_state["booking_success"] = True
            st.session_state["show_all_tests"] = False
            st.rerun()
        else:
            try:
                st.error(r.json().get("detail", "Booking failed"))
            except Exception:
                st.error("Booking failed")




# # ---------------------------------
# # CREATE NEW BOOKING (DISPLAY-IMPROVED)
# # ---------------------------------
# def render_create_booking():
#     st.subheader("📅 Create New Booking")

#     tests = api_get(f"{API_BASE}/lab/tests")
#     assignments = api_get(f"{API_BASE}/lab/test-doctor-assignments")

#     if not tests or not assignments:
#         st.error("Failed to load tests or assignments")
#         return

#     # =============================
#     # Initialize state
#     # =============================
#     if "show_all_tests" not in st.session_state:
#         st.session_state["show_all_tests"] = False
#     if "show_booked_tests" not in st.session_state:
#         st.session_state["show_booked_tests"] = False
#     if "booking_search" not in st.session_state:
#         st.session_state["booking_search"] = ""

#     # =============================
#     # Always visible button for booked tests
#     # =============================
#     if st.button("View All Booked Tests"):
#         st.session_state["show_booked_tests"] = not st.session_state["show_booked_tests"]

#     # =============================
#     # Show already booked tests
#     # =============================
#     if st.session_state["show_booked_tests"]:
#         bookings = api_get(f"{API_BASE}/lab/bookings") or []

#         booking_search = st.text_input(
#             "Filter Booked Tests by Patient or Test Name",
#             key="booking_search"
#         )

#         filtered_bookings = bookings
#         if booking_search:
#             filtered_bookings = [
#                 b for b in bookings
#                 if booking_search.lower() in b["patient_name"].lower()
#                 or booking_search.lower() in b["test_name"].lower()
#             ]

#         if filtered_bookings:
#             header = st.columns([3, 3, 2, 2, 2])
#             header[0].markdown("**Patient Name**")
#             header[1].markdown("**Test Name**")
#             header[2].markdown("**Doctor**")
#             header[3].markdown("**Date**")
#             header[4].markdown("**Time**")

#             for b in filtered_bookings:
#                 c1, c2, c3, c4, c5 = st.columns([3, 3, 2, 2, 2])
#                 c1.write(format_display(b["patient_name"]))
#                 c2.write(format_display(b["test_name"]))
#                 c3.write(format_display(b.get("doctor_name", "-")))
#                 c4.write(b["booking_date"])
#                 c5.write(b["booking_time"])
#                 st.markdown('<hr style="margin:2px 0;">', unsafe_allow_html=True)
#         else:
#             st.info("No booked tests to display.")

#     st.markdown("---")

#     # =============================
#     # Search Test
#     # =============================
#     search_query = st.text_input("Search Test by Name", key="search_test_input")

#     c1, c2 = st.columns([1, 1])
#     if c1.button("Show All Tests"):
#         st.session_state["show_all_tests"] = True
#     if c2.button("Hide All Tests"):
#         st.session_state["show_all_tests"] = False

#     if search_query:
#         filtered_tests = [t for t in tests if search_query.lower() in t["test_name"].lower()]
#     elif st.session_state["show_all_tests"]:
#         filtered_tests = tests
#     else:
#         filtered_tests = []

#     if filtered_tests:
#         header = st.columns([4, 2, 2])
#         header[0].markdown("**Test Name**")
#         header[1].markdown("**Price**")
#         header[2].markdown("**Duration**")

#         for t in filtered_tests:
#             c1, c2, c3 = st.columns([4, 2, 2])
#             c1.write(format_display(t["test_name"]))
#             c2.write(f"{t.get('price', '-')}")
#             c3.write(f"{t.get('duration', '-')}")
#             if st.button("Select Test", key=f"select_test_{t['test_id']}"):
#                 st.session_state["selected_test"] = t
#                 st.rerun()
#             st.markdown('<hr style="margin:2px 0;">', unsafe_allow_html=True)
#     else:
#         st.info("No tests to display.")

#     if "selected_test" not in st.session_state:
#         return

#     test = st.session_state["selected_test"]

#     # =============================
#     # Assigned doctor
#     # =============================
#     assigned = next((a for a in assignments if a["test_id"] == test["test_id"]), None)
#     doctor_id = assigned["doctor_id"] if assigned else None
#     doctor_name = assigned["doctor_name"] if assigned else None
#     st.markdown(f"**Assigned Doctor:** {format_display(doctor_name) if doctor_name else '-'}")

#     # =============================
#     # Patient details
#     # =============================
#     patient_name = st.text_input("Patient Name")
#     patient_mobile = st.text_input("Patient Mobile")
#     booking_date = st.date_input("Booking Date")

#     # =============================
#     # DYNAMIC WINDOWS DROPDOWN WITH AVAILABLE SLOTS
#     # =============================
#     if booking_date:
#         windows_with_slots = api_get(
#             f"{API_BASE}/lab/available-slots/{test['test_id']}/{booking_date}"
#         ) or []

#         if not windows_with_slots:
#             st.warning("No available windows for this test on the selected date.")
#             return

#         # Only show windows with available slots > 0
#         available_window_options = [
#             f"{w['window_start']} - {w['window_end']} ({w['available_slots']} slots available)"
#             for w in windows_with_slots if w['available_slots'] > 0
#         ]

#         if not available_window_options:
#             st.warning("All windows are fully booked for this date.")
#             return

#         selected_window_label = st.selectbox("Select Window", available_window_options)
#         selected_window = next(w for w in windows_with_slots if
#                                f"{w['window_start']} - {w['window_end']} ({w['available_slots']} slots available)" == selected_window_label)
#     else:
#         st.info("Please select a booking date first to see available windows.")
#         return

#     # =============================
#     # Submit Booking
#     # =============================
#     create_btn = st.button("Create Booking")

#     # 🔻 SUCCESS MESSAGE MUST STAY HERE (BOTTOM)
#     success_box = st.empty()

#     if st.session_state.get("booking_success"):
#         success_box.success("Booking created successfully!")
#         st.session_state.pop("selected_test", None)
#         del st.session_state["booking_success"]

#     if create_btn:
#         if not patient_name or not patient_mobile:
#             st.error("Patient name and mobile are required!")
#             return

#         payload = {
#             "test_id": test["test_id"],
#             "window_id": selected_window["window_id"],
#             "doctor_id": doctor_id,
#             "patient_name": patient_name,
#             "patient_mobile": patient_mobile,
#             "booking_date": str(booking_date),
#             "booking_time": selected_window["window_start"],
#             "window_start": selected_window["window_start"],
#             "window_end": selected_window["window_end"],
#         }

#         r = requests.post(
#             f"{API_BASE}/lab/bookings",
#             json=payload,
#             headers=auth_headers()
#         )

#         # ✅ SUCCESS ONLY IF BACKEND CONFIRMS INSERT
#         if r.status_code == 200 and "booking_id" in r.json():
#             st.session_state["booking_success"] = True
#             st.session_state["show_all_tests"] = False
#             st.rerun()
#         else:
#             try:
#                 st.error(r.json().get("detail", "Booking failed"))
#             except Exception:
#                 st.error("Booking failed")




# # ---------------------------------
# # CREATE NEW BOOKING (DISPLAY-IMPROVED)
# # ---------------------------------
# def render_create_booking():
#     st.subheader("📅 Create New Booking")

#     tests = api_get(f"{API_BASE}/lab/tests")
#     assignments = api_get(f"{API_BASE}/lab/test-doctor-assignments")

#     if not tests or not assignments:
#         st.error("Failed to load tests or assignments")
#         return

#     # =============================
#     # Initialize state
#     # =============================
#     if "show_all_tests" not in st.session_state:
#         st.session_state["show_all_tests"] = False
#     if "show_booked_tests" not in st.session_state:
#         st.session_state["show_booked_tests"] = False
#     if "booking_search" not in st.session_state:
#         st.session_state["booking_search"] = ""

#     # =============================
#     # Always visible button for booked tests
#     # =============================
#     if st.button("View All Booked Tests"):
#         st.session_state["show_booked_tests"] = not st.session_state["show_booked_tests"]

#     # =============================
#     # Show already booked tests
#     # =============================
#     if st.session_state["show_booked_tests"]:
#         bookings = api_get(f"{API_BASE}/lab/bookings") or []

#         booking_search = st.text_input(
#             "Filter Booked Tests by Patient or Test Name",
#             key="booking_search"
#         )

#         filtered_bookings = bookings
#         if booking_search:
#             filtered_bookings = [
#                 b for b in bookings
#                 if booking_search.lower() in b["patient_name"].lower()
#                 or booking_search.lower() in b["test_name"].lower()
#             ]

#         if filtered_bookings:
#             header = st.columns([3, 3, 2, 2, 2])
#             header[0].markdown("**Patient Name**")
#             header[1].markdown("**Test Name**")
#             header[2].markdown("**Doctor**")
#             header[3].markdown("**Date**")
#             header[4].markdown("**Time**")

#             for b in filtered_bookings:
#                 c1, c2, c3, c4, c5 = st.columns([3, 3, 2, 2, 2])
#                 c1.write(format_display(b["patient_name"]))
#                 c2.write(format_display(b["test_name"]))
#                 c3.write(format_display(b.get("doctor_name", "-")))
#                 c4.write(b["booking_date"])
#                 c5.write(b["booking_time"])
#                 st.markdown('<hr style="margin:2px 0;">', unsafe_allow_html=True)
#         else:
#             st.info("No booked tests to display.")

#     st.markdown("---")

#     # =============================
#     # Search Test
#     # =============================
#     search_query = st.text_input("Search Test by Name", key="search_test_input")

#     c1, c2 = st.columns([1, 1])
#     if c1.button("Show All Tests"):
#         st.session_state["show_all_tests"] = True
#     if c2.button("Hide All Tests"):
#         st.session_state["show_all_tests"] = False

#     if search_query:
#         filtered_tests = [t for t in tests if search_query.lower() in t["test_name"].lower()]
#     elif st.session_state["show_all_tests"]:
#         filtered_tests = tests
#     else:
#         filtered_tests = []

#     if filtered_tests:
#         header = st.columns([4, 2, 2])
#         header[0].markdown("**Test Name**")
#         header[1].markdown("**Price**")
#         header[2].markdown("**Duration**")

#         for t in filtered_tests:
#             c1, c2, c3 = st.columns([4, 2, 2])
#             c1.write(format_display(t["test_name"]))
#             c2.write(f"{t.get('price', '-')}") 
#             c3.write(f"{t.get('duration', '-')}") 
#             if st.button("Select Test", key=f"select_test_{t['test_id']}"):
#                 st.session_state["selected_test"] = t
#                 st.rerun()
#             st.markdown('<hr style="margin:2px 0;">', unsafe_allow_html=True)
#     else:
#         st.info("No tests to display.")

#     if "selected_test" not in st.session_state:
#         return

#     test = st.session_state["selected_test"]

#     # =============================
#     # Assigned doctor
#     # =============================
#     assigned = next((a for a in assignments if a["test_id"] == test["test_id"]), None)
#     doctor_id = assigned["doctor_id"] if assigned else None
#     doctor_name = assigned["doctor_name"] if assigned else None
#     st.markdown(f"**Assigned Doctor:** {format_display(doctor_name) if doctor_name else '-'}")

#     # =============================
#     # Patient details
#     # =============================
#     patient_name = st.text_input("Patient Name")
#     patient_mobile = st.text_input("Patient Mobile")
#     booking_date = st.date_input("Booking Date")

#     # -----------------------------
#     # CHECK AVAILABLE SLOTS
#     # -----------------------------
#     if st.button("Check Available Slots"):
#         if not booking_date:
#             st.error("Please select a booking date first")
#         else:
#             slots = api_get(f"{API_BASE}/lab/available-slots/{test['test_id']}/{booking_date}")
#             if slots:
#                 st.subheader("Available Slots by Window")
#                 for s in slots:
#                     st.write(f"{s['window_start']} - {s['window_end']}: {s['available_slots']} slots available")
#             else:
#                 st.info("No slots available for this test on the selected date.")





#     # =============================
#     # FETCH WINDOWS
#     # =============================
#     windows = api_get(f"{API_BASE}/lab/test-windows/{test['test_id']}") or []

#     if not windows:
#         st.warning("No available windows for this test.")
#         return

#     window_map = {
#         f"{w['window_start']} - {w['window_end']} ({w['max_tests']} slots)": w
#         for w in windows
#     }

#     selected_window_label = st.selectbox("Select Window", list(window_map.keys()))
#     selected_window = window_map[selected_window_label]

#     # =============================
#     # Submit Booking
#     # =============================
#     create_btn = st.button("Create Booking")

#     # 🔻 SUCCESS MESSAGE MUST STAY HERE (BOTTOM)
#     success_box = st.empty()

#     if st.session_state.get("booking_success"):
#         success_box.success("Booking created successfully!")
#         st.session_state.pop("selected_test", None)
#         del st.session_state["booking_success"]

#     if create_btn:
#         if not patient_name or not patient_mobile:
#             st.error("Patient name and mobile are required!")
#             return

#         payload = {
#             "test_id": test["test_id"],
#             "window_id": selected_window["window_id"],
#             "doctor_id": doctor_id,
#             "patient_name": patient_name,
#             "patient_mobile": patient_mobile,
#             "booking_date": str(booking_date),
#             "booking_time": selected_window["window_start"],
#             "window_start": selected_window["window_start"],
#             "window_end": selected_window["window_end"],
#         }

#         r = requests.post(
#             f"{API_BASE}/lab/bookings",
#             json=payload,
#             headers=auth_headers()
#         )

#         # ✅ SUCCESS ONLY IF BACKEND CONFIRMS INSERT
#         if r.status_code == 200 and "booking_id" in r.json():
#             st.session_state["booking_success"] = True
#             st.session_state["show_all_tests"] = False
#             st.rerun()
#         else:
#             try:
#                 st.error(r.json().get("detail", "Booking failed"))
#             except Exception:
#                 st.error("Booking failed")



# # ---------------------------------
# # CREATE NEW BOOKING (DISPLAY-IMPROVED)
# # ---------------------------------
# def render_create_booking():
#     st.subheader("📅 Create New Booking")

#     tests = api_get(f"{API_BASE}/lab/tests")
#     assignments = api_get(f"{API_BASE}/lab/test-doctor-assignments")

#     if not tests or not assignments:
#         st.error("Failed to load tests or assignments")
#         return

#     # =============================
#     # Initialize state
#     # =============================
#     if "show_all_tests" not in st.session_state:
#         st.session_state["show_all_tests"] = False
#     if "show_booked_tests" not in st.session_state:
#         st.session_state["show_booked_tests"] = False
#     if "booking_search" not in st.session_state:
#         st.session_state["booking_search"] = ""

#     # =============================
#     # Always visible button for booked tests
#     # =============================
#     if st.button("View All Booked Tests"):
#         st.session_state["show_booked_tests"] = not st.session_state["show_booked_tests"]

#     # =============================
#     # Show already booked tests
#     # =============================
#     if st.session_state["show_booked_tests"]:
#         bookings = api_get(f"{API_BASE}/lab/bookings") or []

#         booking_search = st.text_input(
#             "Filter Booked Tests by Patient or Test Name",
#             key="booking_search"
#         )

#         filtered_bookings = bookings
#         if booking_search:
#             filtered_bookings = [
#                 b for b in bookings
#                 if booking_search.lower() in b["patient_name"].lower()
#                 or booking_search.lower() in b["test_name"].lower()
#             ]

#         if filtered_bookings:
#             header = st.columns([3, 3, 2, 2, 2])
#             header[0].markdown("**Patient Name**")
#             header[1].markdown("**Test Name**")
#             header[2].markdown("**Doctor**")
#             header[3].markdown("**Date**")
#             header[4].markdown("**Time**")

#             for b in filtered_bookings:
#                 c1, c2, c3, c4, c5 = st.columns([3, 3, 2, 2, 2])
#                 c1.write(format_display(b["patient_name"]))
#                 c2.write(format_display(b["test_name"]))
#                 c3.write(format_display(b.get("doctor_name", "-")))
#                 c4.write(b["booking_date"])
#                 c5.write(b["booking_time"])
#                 st.markdown('<hr style="margin:2px 0;">', unsafe_allow_html=True)
#         else:
#             st.info("No booked tests to display.")

#     st.markdown("---")

#     # =============================
#     # Search Test
#     # =============================
#     search_query = st.text_input("Search Test by Name", key="search_test_input")

#     c1, c2 = st.columns([1, 1])
#     if c1.button("Show All Tests"):
#         st.session_state["show_all_tests"] = True
#     if c2.button("Hide All Tests"):
#         st.session_state["show_all_tests"] = False

#     if search_query:
#         filtered_tests = [t for t in tests if search_query.lower() in t["test_name"].lower()]
#     elif st.session_state["show_all_tests"]:
#         filtered_tests = tests
#     else:
#         filtered_tests = []

#     if filtered_tests:
#         header = st.columns([4, 2, 2])
#         header[0].markdown("**Test Name**")
#         header[1].markdown("**Price**")
#         header[2].markdown("**Duration**")

#         for t in filtered_tests:
#             c1, c2, c3 = st.columns([4, 2, 2])
#             c1.write(format_display(t["test_name"]))
#             c2.write(f"{t.get('price', '-')}") 
#             c3.write(f"{t.get('duration', '-')}") 
#             if st.button("Select Test", key=f"select_test_{t['test_id']}"):
#                 st.session_state["selected_test"] = t
#                 st.rerun()
#             st.markdown('<hr style="margin:2px 0;">', unsafe_allow_html=True)
#     else:
#         st.info("No tests to display.")

#     if "selected_test" not in st.session_state:
#         return

#     test = st.session_state["selected_test"]

#     # =============================
#     # Assigned doctor
#     # =============================
#     assigned = next((a for a in assignments if a["test_id"] == test["test_id"]), None)
#     doctor_id = assigned["doctor_id"] if assigned else None
#     doctor_name = assigned["doctor_name"] if assigned else None
#     st.markdown(f"**Assigned Doctor:** {format_display(doctor_name) if doctor_name else '-'}")

#     # =============================
#     # Patient details
#     # =============================
#     patient_name = st.text_input("Patient Name")
#     patient_mobile = st.text_input("Patient Mobile")
#     booking_date = st.date_input("Booking Date")

#     # =============================
#     # FETCH WINDOWS
#     # =============================
#     windows = api_get(f"{API_BASE}/lab/test-windows/{test['test_id']}") or []

#     if not windows:
#         st.warning("No available windows for this test.")
#         return

#     window_map = {
#         f"{w['window_start']} - {w['window_end']} ({w['max_tests']} slots)": w
#         for w in windows
#     }

#     selected_window_label = st.selectbox("Select Window", list(window_map.keys()))
#     selected_window = window_map[selected_window_label]

#     # =============================
#     # Submit Booking
#     # =============================
#     create_btn = st.button("Create Booking")

#     # 🔻 SUCCESS MESSAGE MUST STAY HERE (BOTTOM)
#     success_box = st.empty()

#     if st.session_state.get("booking_success"):
#         success_box.success("Booking created successfully!")
#         st.session_state.pop("selected_test", None)
#         del st.session_state["booking_success"]

#     if create_btn:
#         if not patient_name or not patient_mobile:
#             st.error("Patient name and mobile are required!")
#             return

#         payload = {
#             "test_id": test["test_id"],
#             "window_id": selected_window["window_id"],
#             "doctor_id": doctor_id,
#             "patient_name": patient_name,
#             "patient_mobile": patient_mobile,
#             "booking_date": str(booking_date),
#             "booking_time": selected_window["window_start"],
#             "window_start": selected_window["window_start"],
#             "window_end": selected_window["window_end"],
#         }

#         r = requests.post(
#             f"{API_BASE}/lab/bookings",
#             json=payload,
#             headers=auth_headers()
#         )

#         # ✅ SUCCESS ONLY IF BACKEND CONFIRMS INSERT
#         if r.status_code == 200 and "booking_id" in r.json():
#             st.session_state["booking_success"] = True
#             st.session_state["show_all_tests"] = False
#             st.rerun()
#         else:
#             try:
#                 st.error(r.json().get("detail", "Booking failed"))
#             except Exception:
#                 st.error("Booking failed")




# # ---------------------------------
# # CREATE NEW BOOKING (DISPLAY-IMPROVED)
# # ---------------------------------
# def render_create_booking():
#     st.subheader("📅 Create New Booking")

#     success_box = st.empty()

#     if st.session_state.get("booking_success"):
#         success_box.success("Booking created successfully!")
#         st.session_state.pop("selected_test", None)
#         del st.session_state["booking_success"]

    
#     tests = api_get(f"{API_BASE}/lab/tests")
#     assignments = api_get(f"{API_BASE}/lab/test-doctor-assignments")

#     if not tests or not assignments:
#         st.error("Failed to load tests or assignments")
#         return

#     # =============================
#     # Initialize state
#     # =============================
#     if "show_all_tests" not in st.session_state:
#         st.session_state["show_all_tests"] = False
#     if "show_booked_tests" not in st.session_state:
#         st.session_state["show_booked_tests"] = False
#     if "booking_search" not in st.session_state:
#         st.session_state["booking_search"] = ""

#     # =============================
#     # Always visible button for booked tests
#     # =============================
#     if st.button("View All Booked Tests"):
#         st.session_state["show_booked_tests"] = not st.session_state["show_booked_tests"]

#     # =============================
#     # Show already booked tests
#     # =============================
#     if st.session_state["show_booked_tests"]:
#         bookings = api_get(f"{API_BASE}/lab/bookings") or []

#         booking_search = st.text_input(
#             "Filter Booked Tests by Patient or Test Name", key="booking_search"
#         )

#         filtered_bookings = bookings
#         if booking_search:
#             filtered_bookings = [
#                 b for b in bookings
#                 if booking_search.lower() in b["patient_name"].lower()
#                 or booking_search.lower() in b["test_name"].lower()
#             ]

#         if filtered_bookings:
#             header = st.columns([3, 3, 2, 2, 2])
#             header[0].markdown("**Patient Name**")
#             header[1].markdown("**Test Name**")
#             header[2].markdown("**Doctor**")
#             header[3].markdown("**Date**")
#             header[4].markdown("**Time**")

#             for b in filtered_bookings:
#                 c1, c2, c3, c4, c5 = st.columns([3, 3, 2, 2, 2])
#                 c1.write(format_display(b["patient_name"]))
#                 c2.write(format_display(b["test_name"]))
#                 c3.write(format_display(b.get("doctor_name", "-")))
#                 c4.write(b["booking_date"])
#                 c5.write(b["booking_time"])
#                 st.markdown('<hr style="margin:2px 0;">', unsafe_allow_html=True)
#         else:
#             st.info("No booked tests to display.")

#     st.markdown("---")

#     # =============================
#     # Search Test
#     # =============================
#     search_query = st.text_input("Search Test by Name", key="search_test_input")

#     c1, c2 = st.columns([1, 1])
#     if c1.button("Show All Tests"):
#         st.session_state["show_all_tests"] = True
#     if c2.button("Hide All Tests"):
#         st.session_state["show_all_tests"] = False

#     if search_query:
#         filtered_tests = [t for t in tests if search_query.lower() in t["test_name"].lower()]
#     elif st.session_state["show_all_tests"]:
#         filtered_tests = tests
#     else:
#         filtered_tests = []

#     if filtered_tests:
#         header = st.columns([4, 2, 2])
#         header[0].markdown("**Test Name**")
#         header[1].markdown("**Price**")
#         header[2].markdown("**Duration**")

#         for t in filtered_tests:
#             c1, c2, c3 = st.columns([4, 2, 2])
#             c1.write(format_display(t["test_name"]))
#             c2.write(f"{t.get('price', '-')}")
#             c3.write(f"{t.get('duration', '-')}")
#             if st.button("Select Test", key=f"select_test_{t['test_id']}"):
#                 st.session_state["selected_test"] = t
#                 st.rerun()
#             st.markdown('<hr style="margin:2px 0;">', unsafe_allow_html=True)
#     else:
#         st.info("No tests to display.")

#     if "selected_test" not in st.session_state:
#         return

#     test = st.session_state["selected_test"]

#     # =============================
#     # Assigned doctor
#     # =============================
#     assigned = next((a for a in assignments if a["test_id"] == test["test_id"]), None)
#     doctor_id = assigned["doctor_id"] if assigned else None
#     doctor_name = assigned["doctor_name"] if assigned else None
#     st.markdown(f"**Assigned Doctor:** {format_display(doctor_name) if doctor_name else '-'}")

#     # =============================
#     # Patient details
#     # =============================
#     patient_name = st.text_input("Patient Name")
#     patient_mobile = st.text_input("Patient Mobile")
#     booking_date = st.date_input("Booking Date")

#     # =============================
#     # FETCH WINDOWS (NEW)
#     # =============================
#     windows = api_get(f"{API_BASE}/lab/test-windows/{test['test_id']}") or []

#     if not windows:
#         st.warning("No available windows for this test.")
#         return

#     window_map = {
#         f"{w['window_start']} - {w['window_end']} ({w['max_tests']} slots)": w
#         for w in windows
#     }

#     selected_window_label = st.selectbox("Select Window", list(window_map.keys()))
#     selected_window = window_map[selected_window_label]

#     # =============================
#     # Submit Booking
#     # =============================
    
#     if st.button("Create Booking"):
        
#         if not patient_name or not patient_mobile:
#             st.error("Patient name and mobile are required!")
#             return

#         payload = {
#             "test_id": test["test_id"],
#             "window_id": selected_window["window_id"],
#             "doctor_id": doctor_id,
#             "patient_name": patient_name,
#             "patient_mobile": patient_mobile,
#             "booking_date": str(booking_date),
#             "booking_time": selected_window["window_start"],
#             "window_start": selected_window["window_start"],
#             "window_end": selected_window["window_end"],
#         }

#         r = requests.post(
#             f"{API_BASE}/lab/bookings",
#             json=payload,
#             headers=auth_headers()
#         )

#         if r.status_code == 200:
#             st.session_state["booking_success"] = True
#             # st.session_state.pop("selected_test")
#             st.session_state["show_all_tests"] = False
#             st.rerun()
#         else:
#             st.error(r.text)




# def render_create_booking():
#     st.subheader("📅 Create New Booking")

#     tests = api_get(f"{API_BASE}/lab/tests")
#     assignments = api_get(f"{API_BASE}/lab/test-doctor-assignments")

#     if not tests or not assignments:
#         st.error("Failed to load tests or assignments")
#         return

#     # =============================
#     # Initialize state
#     # =============================
#     if "show_all_tests" not in st.session_state:
#         st.session_state["show_all_tests"] = False
#     if "show_booked_tests" not in st.session_state:
#         st.session_state["show_booked_tests"] = False
#     if "booking_search" not in st.session_state:
#         st.session_state["booking_search"] = ""

#     # =============================
#     # Always visible button for booked tests
#     # =============================
#     if st.button("View All Booked Tests"):
#         st.session_state["show_booked_tests"] = not st.session_state["show_booked_tests"]

#     # =============================
#     # Show already booked tests if toggled
#     # =============================
#     if st.session_state["show_booked_tests"]:
#         bookings = api_get(f"{API_BASE}/lab/bookings")
#         booking_search = st.text_input(
#             "Filter Booked Tests by Patient or Test Name", key="booking_search"
#         )

#         filtered_bookings = bookings
#         if booking_search:
#             filtered_bookings = [
#                 b for b in bookings
#                 if booking_search.lower() in b["patient_name"].lower()
#                 or booking_search.lower() in b["test_name"].lower()
#             ]

#         if filtered_bookings:
#             header = st.columns([3, 3, 2, 2, 2])
#             header[0].markdown("**Patient Name**")
#             header[1].markdown("**Test Name**")
#             header[2].markdown("**Doctor**")
#             header[3].markdown("**Date**")
#             header[4].markdown("**Time**")

#             for b in filtered_bookings:
#                 c1, c2, c3, c4, c5 = st.columns([3, 3, 2, 2, 2])
#                 c1.write(format_display(b["patient_name"]))
#                 c2.write(format_display(b["test_name"]))
#                 c3.write(format_display(b.get("doctor_name", "-")))
#                 c4.write(b["booking_date"])
#                 c5.write(b["booking_time"])
#                 st.markdown('<hr style="margin:2px 0;">', unsafe_allow_html=True)
#         else:
#             st.info("No booked tests to display.")

#     st.markdown("---")

#     # =============================
#     # Search input for creating new bookings
#     # =============================
#     search_query = st.text_input("Search Test by Name", key="search_test_input")

#     # =============================
#     # Show / Hide buttons for tests
#     # =============================
#     c1, c2 = st.columns([1, 1])
#     if c1.button("Show All Tests"):
#         st.session_state["show_all_tests"] = True
#     if c2.button("Hide All Tests"):
#         st.session_state["show_all_tests"] = False

#     # =============================
#     # Determine which tests to show for booking
#     # =============================
#     if search_query:
#         filtered_tests = [t for t in tests if search_query.lower() in t["test_name"].lower()]
#     elif st.session_state["show_all_tests"]:
#         filtered_tests = tests
#     else:
#         filtered_tests = []

#     # =============================
#     # Display tests with table style for booking
#     # =============================
#     if filtered_tests:
#         header = st.columns([4, 2, 2])
#         header[0].markdown("**Test Name**")
#         header[1].markdown("**Price**")
#         header[2].markdown("**Duration**")
#         for t in filtered_tests:
#             c1, c2, c3 = st.columns([4, 2, 2])
#             c1.write(format_display(t["test_name"]))
#             c2.write(f"{t.get('price', '-')}")
#             c3.write(f"{t.get('duration', '-')}")
#             if st.button("Select Test", key=f"select_test_{t['test_id']}"):
#                 st.session_state["selected_test"] = t
#                 st.rerun()
#             st.markdown('<hr style="margin:2px 0;">', unsafe_allow_html=True)
#     else:
#         st.info("No tests to display. Use search or click 'Show All Tests'.")

#     if "selected_test" not in st.session_state:
#         return

#     test = st.session_state["selected_test"]

#     # =============================
#     # Show assigned doctor
#     # =============================
#     assigned = next((a for a in assignments if a["test_id"] == test["test_id"]), None)
#     doctor_id = assigned["doctor_id"] if assigned else None
#     doctor_name = assigned["doctor_name"] if assigned else None
#     st.markdown(f"**Assigned Doctor:** {format_display(doctor_name) if doctor_name else '-'}")

#     # =============================
#     # Patient details
#     # =============================
#     patient_name = st.text_input("Patient Name")
#     patient_mobile = st.text_input("Patient Mobile")
#     booking_date = st.date_input("Booking Date")

#     # =============================
#     # Select window
#     # =============================
#     window = st.selectbox("Select Window", [1, 2, 3, 4])
#     window_map = {
#         1: ("08:00", "09:00"),
#         2: ("09:00", "10:00"),
#         3: ("10:00", "11:00"),
#         4: ("11:00", "12:00"),
#     }
#     window_start, window_end = window_map[window]
#     booking_time = window_start

#     # =============================
#     # Submit Booking
#     # =============================
#     if st.button("Create Booking"):
#         if not all([patient_name, patient_mobile]):
#             st.error("Patient name and mobile are required!")
#             return

#         payload = {
#             "test_id": test["test_id"],
#             "test_name": test["test_name"],
#             "doctor_id": doctor_id,
#             "doctor_name": doctor_name,
#             "patient_name": patient_name,
#             "patient_mobile": patient_mobile,
#             "booking_date": str(booking_date),
#             "booking_time": booking_time,
#             "window_start": window_start,
#             "window_end": window_end,
#             "price": test.get("price"),
#             "duration": test.get("duration"),
#             "notes": ""
#         }

#         r = requests.post(f"{API_BASE}/lab/bookings", json=payload, headers=auth_headers())
#         if r.status_code == 200:
#             st.success("Booking created successfully!")
#             st.session_state.pop("selected_test")
#             st.session_state["show_all_tests"] = False
#         else:
#             st.error(r.text)