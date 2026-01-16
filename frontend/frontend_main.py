from .frontend_common import *
from .password_login_page import admin_login_modal, show_change_password
from .lab_schedule_page import render_lab_schedule
from .lab_holidays_page import render_lab_holidays
from .lab_tests_page import render_lab_tests
from .test_schedule_page import render_test_schedule
from .test_holidays_page import render_test_holidays
from .doctors_page import render_doctors
from .doctor_holidays_page import render_doctor_holidays
from .assign_test_doctor_page import render_test_doctor_assignments
from .create_booking_page import render_create_booking


# ---------------------------------
# ADMIN PANEL (updated)
# ---------------------------------
def render_admin_panel():
    if "admin_token" not in st.session_state:
        admin_login_modal()
        return

    section = st.sidebar.radio(
        "Admin Menu",
        [
            "Dashboard",
            "Lab Schedule",
            "Lab Holidays",
            "Lab Tests",
            "Test Schedule",
            "Test Holidays",           
            "Doctors",
            "Doctor Holidays",         
            "Test-Doctor Assignments", 
            "Bookings",                
            "Change Password",
            "Logout"
        ]
    )

    if section == "Dashboard":
        st.title("🧪 Lab Admin Panel")
        st.markdown(
            """
            Welcome to the **Lab Test Appointment Booking Admin Panel**!  

            Here, you have full control over your lab operations. You can:  
            - **Add or manage lab tests**  
            - **Edit lab schedules and timings**  
            - **Manage doctors and their holidays**  
            - **Assign tests to doctors**  
            - **View and create bookings**  

            Use the sidebar menu to navigate through different sections and manage your lab efficiently.  
            Keep everything organized and running smoothly from one place!  
            """
        )


    elif section == "Lab Schedule":
        render_lab_schedule()

    elif section == "Lab Holidays":
        render_lab_holidays()

    elif section == "Lab Tests":
        render_lab_tests()
    
    elif section == "Test Schedule":
        render_test_schedule()
    
    elif section == "Test Holidays":
        render_test_holidays()     # 👈 Render Test Holidays frontend

    elif section == "Doctors":
        render_doctors()           # 👈 Render Doctors frontend

    elif section == "Doctor Holidays":
        render_doctor_holidays()   # 👈 Render Doctor Holidays frontend

    elif section == "Test-Doctor Assignments":
        render_test_doctor_assignments()   # 👈 Render Test-Doctor Assignments frontend

    elif section == "Bookings":
        render_create_booking()    # 👈 NEW: Render Create Booking frontend

    elif section == "Change Password":
        show_change_password()

    elif section == "Logout":
        st.session_state.pop("admin_token", None)
        st.success("Logged out.")
        st.rerun()




# ---------------------------------
# MAIN
# ---------------------------------
def main():
    st.set_page_config(page_title="Lab Admin", page_icon="⚙️", layout="wide")

    # -------------------------
    # Sidebar Navigation
    # -------------------------
    page_option = st.sidebar.radio("Navigation", ["Chat", "Admin / Settings"])

    if page_option == "Chat":
        st.title("💬 Chat Page")
        st.info("Chat functionality will be implemented here.")

    elif page_option == "Admin / Settings":
        st.title("⚙️ Admin / Settings")
        render_admin_panel()


if __name__ == "__main__":
    main()