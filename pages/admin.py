import streamlit as st
import requests

st.title("Welcome to the Admin Page!")


st.header("Admin Dashboard")

admin_page = st.sidebar.selectbox(
    "Admin",
    [
        "Add Task",
        "Task Status",
        "Analytics"
    ]
)

if admin_page == "Add Task":

    st.header("Add Task")

    task_date = st.date_input("Task Date (YYYY-MM-DD)")

    question = st.text_input("Question Number ")

    submitted = st.button("Submit Task")

    if submitted:
        response = requests.post(
            "http://localhost:8000/tasks",
            params = {
                "task_date": task_date.isoformat(),
                "q_no": question
            }
        )

        if response.status_code == 200:
                st.success(f"Task submitted successfully! Task Date: {task_date}, Question Number: {question}")
        else:
                st.error("Failed. Please try again.")



