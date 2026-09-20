import streamlit as st
import requests

st.title("Task")

login_tab, signup_tab = st.tabs(["Login", "Signup"])

with login_tab:
    st.header("LOGIN")

    with st.form("login_form"):

        name = st.text_input("Name")
        password = st.text_input("Password", type="password")
        role = st.selectbox("Role", ["Admin", "User"], key="login_role")

        submit = st.form_submit_button("Login")

    if submit:

        response = requests.post(
            "http://localhost:8000/login",
            data={
                "username": name,
                "password": password
            },
        )


        if response.status_code == 200:

            data = response.json()

            access_token = data.get("access_token")
            role = data["role"]
            
            st.session_state["access_token"] = access_token
            st.session_state["role"] = role
            st.session_state["logged_in"] = True
    
            st.success("Login successful!")

            if role == "Admin":
                st.switch_page("pages/admin.py")
            elif role == "User":
                st.switch_page("pages/user.py")
            else:
                st.error("Invalid role. Please contact the administrator.")

        else:
            st.error("Login failed")


    

with signup_tab:
    st.header("SIGNUP")

    with st.form("signup_form"):
        name = st.text_input("Name", key="signup_name")
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_password")
        role = st.selectbox("Role", ["Admin", "User"], key="signup_role")

        submit = st.form_submit_button("Signup")

    if submit:
        response = requests.post(
            "http://localhost:8000/signup",
            json={"username": name, "email": email, "password": password, "role": role},
        )

        if response.status_code == 200:
            st.success("Signup successful!")
        else:
            st.error("Signup failed. Please try again.")