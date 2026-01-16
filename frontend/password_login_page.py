from .frontend_common import *

# ---------------------------------
# LOGIN MODAL
# ---------------------------------
def admin_login_modal():
    st.subheader("🔐 Admin Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        r = requests.post(f"{API_BASE}/login", json={"username": username, "password": password})
        if r.status_code == 200:
            st.session_state["admin_token"] = r.json()["token"]
            st.success("Logged in!")
            st.rerun()
        else:
            st.error("Invalid username or password")

# ---------------------------------
# CHANGE PASSWORD
# ---------------------------------
def show_change_password():
    st.subheader("🔑 Change Password")

    old_pw = st.text_input("Old Password", type="password")
    new_pw = st.text_input("New Password", type="password")
    confirm_pw = st.text_input("Confirm New Password", type="password")

    if st.button("Update Password"):
        if new_pw != confirm_pw:
            st.error("Passwords do not match!")
            return

        r = requests.post(
            f"{API_BASE}/reset-password",
            json={"old_password": old_pw, "new_password": new_pw, "confirm_password": confirm_pw},
            headers=auth_headers()
        )

        if r.status_code == 200:
            st.success("Password updated! Please login again.")
            st.session_state.pop("admin_token", None)
            st.rerun()
        else:
            st.error(r.text)
